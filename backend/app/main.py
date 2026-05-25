import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, AIMessage

# Import LangGraph and state definition
from app.graph import graph
from app.state import AgentState
from app.tools.file_system import list_dir_sandbox, read_file_sandbox, write_file_sandbox

app = FastAPI(title="LangChain Multi-Agent CodeMachine Gateway")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pydantic import BaseModel
from app.agents.base import get_llm

class TestConnectionRequest(BaseModel):
    api_key: str
    model: str

@app.get("/api/health")
def health():
    return {"status": "ok", "message": "CodeMachine backend gateway is running"}

@app.post("/api/test-connection")
async def test_connection(request: TestConnectionRequest):
    """
    Ping the Vertex Key API with a lightweight mock request
    to verify that the provided API key and model are active and valid.
    """
    try:
        # Resolve LLM using our helper
        llm = get_llm(request.model, request.api_key)
        
        # Execute lightweight ping in a thread pool to avoid blocking the async event loop
        await asyncio.to_thread(
            llm.invoke,
            [{"role": "user", "content": "Say 'ping' only"}],
        )
        return {"status": "success", "message": "Kết nối đến Vertex Key API thành công!"}
    except Exception as e:
        error_msg = str(e)
        if "AuthenticationError" in error_msg or "401" in error_msg:
            error_msg = "API Key không hợp lệ hoặc hết hạn."
        elif "404" in error_msg:
            error_msg = f"Model '{request.model}' không được hỗ trợ hoặc sai chính tả."
        return {"status": "error", "message": f"Kiểm thử kết nối thất bại: {error_msg}"}

class SaveFileRequest(BaseModel):
    relative_path: str
    content: str
    code_folder: str | None = None

@app.post("/api/save-file")
async def save_file(request: SaveFileRequest):
    """Save a file inside the chosen folder."""
    if not request.relative_path:
        return {"status": "error", "message": "Đường dẫn file không được để trống."}

    result = write_file_sandbox(request.relative_path, request.content, root_dir=request.code_folder)
    if result.startswith("Error"):
        return {"status": "error", "message": result}

    return {"status": "success", "message": result}

class ListFilesRequest(BaseModel):
    code_folder: str | None = None

@app.post("/api/list-files")
async def list_files(request: ListFilesRequest):
    """List files inside the chosen folder."""
    try:
        files = list_dir_sandbox(request.code_folder)
        return {"status": "success", "files": list(files.keys())}
    except Exception as e:
        return {"status": "error", "message": str(e)}

class ReadFileRequest(BaseModel):
    relative_path: str
    code_folder: str | None = None

@app.post("/api/read-file")
async def read_file(request: ReadFileRequest):
    """Read a file from the chosen folder."""
    if not request.relative_path:
        return {"status": "error", "message": "Đường dẫn file không được để trống."}

    content = read_file_sandbox(request.relative_path, root_dir=request.code_folder)
    if content.startswith("Error"):
        return {"status": "error", "message": content}
    return {"status": "success", "content": content}

@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[WebSocket] Client connected.")
    
    try:
        while True:
            # Receive task trigger from frontend
            data = await websocket.receive_text()
            request = json.loads(data)
            
            prompt = request.get("prompt", "")
            api_key = request.get("api_key", "").strip()
            # Selected sandbox subfolder for code generation and file editing
            code_folder = request.get("code_folder", "")
            # Group shortcuts (fallback if per-agent models not provided)
            model_complex = request.get("model_complex", "aws/claude-sonnet-4-6")
            model_fast = request.get("model_fast", "aws/claude-haiku-4-5")
            # Per-agent model overrides (highest priority)
            model_architect = request.get("model_architect", "")
            model_coder = request.get("model_coder", "")
            model_reviewer = request.get("model_reviewer", "")
            model_tester = request.get("model_tester", "")
            
            if not prompt:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": "Nội dung yêu cầu trống. Vui lòng mô tả yêu cầu ứng dụng của bạn."
                }))
                continue
                
            # Pre-validate API Key to prevent silent crashes during agent graph runs
            if not api_key or not api_key.startswith("vai-"):
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": "API Key không hợp lệ. Vui lòng nhập Vertex API Key bắt đầu bằng 'vai-' trong ô cấu hình phía trên bên phải trước khi nhấn Bắt đầu!"
                }))
                continue
                
            print(f"[WebSocket] Triggering workflow | architect={model_architect or model_complex} | coder={model_coder or model_complex} | reviewer={model_reviewer or model_fast} | tester={model_tester or model_fast} | prompt='{prompt[:40]}...'")
            
            # 1. Initialize LangGraph State
            initial_state: AgentState = {
                "messages": [HumanMessage(content=prompt)],
                "plan": "",
                "files": {},
                "test_results": "",
                "errors": [],
                "sender": "User",
                "iterations": 0,
                "current_task": prompt,
                "api_key": api_key,
                "model_complex": model_complex,
                "model_fast": model_fast,
                "model_architect": model_architect,
                "model_coder": model_coder,
                "model_reviewer": model_reviewer,
                "model_tester": model_tester,
                "code_folder": code_folder or ""
            }
            
            # Send initial state acknowledgment
            await websocket.send_text(json.dumps({
                "type": "status",
                "node": "idle",
                "status": "Starting workflow...",
                "state": {
                    "plan": "",
                    "files": {},
                    "iterations": 0,
                    "errors": []
                }
            }))
            
            # 2. Run LangGraph asynchronously and stream node transitions
            try:
                async for event in graph.astream(initial_state):
                    # event represents the node that completed
                    node_name = list(event.keys())[0]
                    node_state = event[node_name]
                    
                    # Extract the latest message from that node
                    latest_msg = ""
                    if node_state.get("messages"):
                        latest_msg = node_state["messages"][-1].content
                    
                    print(f"[WebSocket] Node finished: {node_name}")
                    
                    # Package and stream updated state to client with agent-level logging
                    await websocket.send_text(json.dumps({
                        "type": "agent_log",
                        "node": node_name,
                        "level": "info",
                        "message": latest_msg,
                        "state": {
                            "plan": node_state.get("plan", ""),
                            "files": node_state.get("files", {}),
                            "iterations": node_state.get("iterations", 0),
                            "errors": node_state.get("errors", []),
                            "test_results": node_state.get("test_results", "")
                        }
                    }))
                    
                    # Give UI breathing room
                    await asyncio.sleep(0.5)
                    
                # 3. Workflow complete!
                print("[WebSocket] Workflow completed successfully.")
                
                # Fetch final sandbox files written on physical disk just in case
                final_disk_files = list_dir_sandbox(code_folder or None)
                
                await websocket.send_text(json.dumps({
                    "type": "workflow_complete",
                    "status": "System successfully generated, reviewed and verified the codebase!",
                    "files": final_disk_files
                }))
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"[WebSocket] Workflow error: {str(e)}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": f"Workflow execution error: {str(e)}"
                }))
                
    except WebSocketDisconnect:
        print("[WebSocket] Client disconnected.")
    except Exception as e:
        print(f"[WebSocket] Connection error: {str(e)}")
