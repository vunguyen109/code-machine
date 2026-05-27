import os
import shutil
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres import PostgresSaver
from src.config import get_db_uri
from src.graph import agent_org_graph
from src.tools import WORKSPACE_DIR

# Database connection string from configurations
DB_URI = get_db_uri()

def clean_workspace():
    # Làm sạch thư mục workspace trước khi chạy mới để tránh rác từ các phiên cũ
    if os.path.exists(WORKSPACE_DIR):
        print(f"[INFO] Cleaning workspace directory: {WORKSPACE_DIR}")
        try:
            shutil.rmtree(WORKSPACE_DIR)
        except Exception as e:
            print(f"[WARNING] Failed to clean workspace: {e}")
    os.makedirs(WORKSPACE_DIR)

def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', errors='replace').decode('ascii'))

def main():
    clean_workspace()
    
    print("\n=======================================================")
    print("      RUNNING AGENTIC DEVELOPER ORGANIZATION (E2E)")
    print("=======================================================\n")
    
    try:
        # Sử dụng PostgresSaver làm checkpointer để quản lý bộ nhớ của tổ chức tác nhân
        with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
            # Tạo các bảng cơ sở dữ liệu nếu chưa có
            checkpointer.setup()
            print("[INFO] Connected to PostgreSQL checkpoints DB.")
            
            # Compile Graph kèm checkpointer
            app = agent_org_graph.compile(checkpointer=checkpointer)
            
            # Cấu hình thread_id và recursion limit của luồng chạy
            config = {
                "configurable": {"thread_id": "auto_dev_session_002"},
                "recursion_limit": 150 # Cho phép chạy nhiều vòng lặp sửa lỗi
            }
            
            # Yêu cầu phát triển phần mềm đơn giản để kiểm thử luồng
            query = "Write a python script that calculates factorials and Fibonacci numbers. Ensure it has a CLI, and write unit tests to verify both."
            print(f"Goal: {query}")
            print("="*60)
            
            inputs = {
                "messages": [HumanMessage(content=query)],
                "prd": "",
                "architecture": "",
                "code_files": {},
                "test_results": "",
                "is_verified": False,
                "iterations": 0
            }
            
            # Khởi chạy luồng chạy Graph
            events = app.stream(inputs, config=config)
            
            for event in events:
                for node_name, state in event.items():
                    print(f"\n[Finished Node: {node_name}]")
                    if node_name == "ceo":
                        print("--- PRD Content Preview ---")
                        safe_print(state["prd"][:500] + "...\n")
                    elif node_name == "architect":
                        print("--- Architecture Design Preview ---")
                        safe_print(state["architecture"][:500] + "...\n")
                    elif node_name == "coder":
                        print(f"Number of code files written: {len(state.get('code_files', {}))}")
                        print(f"Files: {list(state.get('code_files', {}).keys())}\n")
                    elif node_name == "qa":
                        print(f"Is Verified: {state['is_verified']}")
                        print("Test Results:")
                        safe_print(state['test_results'] + "\n")
                    print("-" * 60)
            
            # Lấy trạng thái cuối cùng
            final_state = app.get_state(config)
            print("\n=======================================================")
            if final_state.values.get("is_verified", False):
                print("SUCCESS: Code developed, tested, and verified successfully by QA!")
            else:
                print("FINISHED: Agent execution completed (but code was not verified or hit limit).")
            print("=======================================================")
            
    except Exception as e:
        print(f"\n[ERROR] Failed to run Agentic Org: {e}")
        print("\n[TROUBLESHOOTING]:")
        print("1. Make sure your local PostgreSQL database is running via:")
        print("   docker-compose up -d")
        print("2. Ensure that connection info in your .env file matches the running Postgres instance.")

if __name__ == "__main__":
    main()
