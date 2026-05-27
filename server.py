import os
import json
import uuid
import time
import asyncio
import threading
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver

from src.graph import agent_org_graph
from src.agents import scan_workspace_files
from src.config import get_db_uri, DEFAULT_WORKSPACE_DIR

app = FastAPI(title="LangGraph SDLC Agentic Dashboard")

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_URI = get_db_uri()

class RunRequest(BaseModel):
    vertex_key: Optional[str] = None
    workspace_path: Optional[str] = None
    prompt: str
    active_agents: List[str]
    agents_config: Dict[str, Dict[str, str]]

@app.post("/api/run")
async def run_workflow(req: RunRequest):
    workspace_path = req.workspace_path or DEFAULT_WORKSPACE_DIR
    workspace_path = os.path.abspath(workspace_path)
    
    try:
        os.makedirs(workspace_path, exist_ok=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Không thể tạo hoặc truy cập thư mục: {str(e)}")
        
    return StreamingResponse(
        event_generator(
            prompt=req.prompt,
            vertex_key=req.vertex_key,
            workspace_path=workspace_path,
            active_agents=req.active_agents,
            agents_config=req.agents_config
        ),
        media_type="text/event-stream"
    )

async def run_graph_stream(compiled_app, prompt, vertex_key, workspace_path, active_agents, agents_config):
    inputs = {
        "messages": [HumanMessage(content=prompt)],
        "prd": "",
        "architecture": "",
        "code_files": {},
        "test_results": "",
        "is_verified": False,
        "iterations": 0
    }
    
    # Quét trước tệp trong workspace làm ngữ cảnh đầu vào
    try:
        inputs["code_files"] = scan_workspace_files(workspace_path)
    except Exception as e:
        print(f"Error scanning workspace: {e}")
        
    config = {
        "configurable": {
            "thread_id": f"web_session_{uuid.uuid4().hex[:8]}",
            "vertex_key": vertex_key,
            "workspace_path": workspace_path,
            "active_agents": active_agents,
            "agents_config": agents_config
        },
        "recursion_limit": 100
    }
    
    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()
    
    def producer():
        try:
            for event in compiled_app.stream(inputs, config=config):
                loop.call_soon_threadsafe(queue.put_nowait, event)
            loop.call_soon_threadsafe(queue.put_nowait, "DONE")
        except Exception as e:
            loop.call_soon_threadsafe(queue.put_nowait, f"ERROR: {str(e)}")

    # Khởi chạy luồng stream của LangGraph trong Thread riêng biệt
    thread = threading.Thread(target=producer)
    thread.start()
    
    yield f"data: {json.dumps({'event': 'start', 'message': 'Bắt đầu khởi chạy hệ thống tác tử LangGraph...'})}\n\n"
    
    while True:
        item = await queue.get()
        if item == "DONE":
            break
        if isinstance(item, str) and item.startswith("ERROR:"):
            yield f"data: {json.dumps({'event': 'error', 'message': item[6:]})}\n\n"
            break
            
        node_name = list(item.keys())[0]
        node_state = item[node_name]
        
        payload = {
            "event": "node_complete",
            "node": node_name,
            "prd": node_state.get("prd", ""),
            "architecture": node_state.get("architecture", ""),
            "is_verified": node_state.get("is_verified", False),
            "test_results": node_state.get("test_results", ""),
            "iterations": node_state.get("iterations", 0),
            "files": list(node_state.get("code_files", {}).keys()) if "code_files" in node_state else []
        }
        yield f"data: {json.dumps(payload)}\n\n"
        
    yield f"data: {json.dumps({'event': 'end', 'message': 'Tất cả các tác tử đã hoàn thành quy trình!'})}\n\n"

async def event_generator(prompt: str, vertex_key: str, workspace_path: str, active_agents: List[str], agents_config: Dict[str, Dict[str, str]]):
    # Thử kết nối lưu checkpoint bằng PostgreSQL trước
    try:
        with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
            checkpointer.setup()
            compiled_app = agent_org_graph.compile(checkpointer=checkpointer)
            async for data in run_graph_stream(compiled_app, prompt, vertex_key, workspace_path, active_agents, agents_config):
                yield data
    except Exception as e:
        print(f"[WARNING] PostgreSQL connection failed: {e}. Falling back to MemorySaver.")
        # Fallback về MemorySaver lưu trong RAM
        checkpointer = MemorySaver()
        compiled_app = agent_org_graph.compile(checkpointer=checkpointer)
        async for data in run_graph_stream(compiled_app, prompt, vertex_key, workspace_path, active_agents, agents_config):
            yield data

@app.get("/api/file")
async def get_file_content(path: str, workspace_path: Optional[str] = None):
    target_workspace = workspace_path or DEFAULT_WORKSPACE_DIR
    target_workspace = os.path.abspath(target_workspace)
    
    safe_path = os.path.abspath(os.path.join(target_workspace, path))
    if not safe_path.startswith(target_workspace):
        raise HTTPException(status_code=400, detail="Đường dẫn file nằm ngoài thư mục workspace.")
        
    if not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="Không tìm thấy file yêu cầu.")
        
    try:
        with open(safe_path, "r", encoding="utf-8") as f:
            return {"content": f.read()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Không thể đọc file: {str(e)}")

# Phục vụ giao diện tĩnh từ thư mục /static
os.makedirs("static", exist_ok=True)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Sử dụng "server:app" để hỗ trợ reload khi file code thay đổi
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
