import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, AIMessage

# Import LangGraph and state definition
from app.graph import graph
from app.state import AgentState
from app.tools.file_system import list_dir_sandbox

app = FastAPI(title="LangChain Multi-Agent CodeMachine Gateway")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok", "message": "CodeMachine backend gateway is running"}

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
            api_key = request.get("api_key", "")
            
            if not prompt:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": "Empty prompt provided."
                }))
                continue
                
            print(f"[WebSocket] Triggering workflow for prompt: '{prompt[:40]}...'")
            
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
                "api_key": api_key
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
                    
                    # Package and stream updated state to client
                    await websocket.send_text(json.dumps({
                        "type": "node_complete",
                        "node": node_name,
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
                final_disk_files = list_dir_sandbox()
                
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
