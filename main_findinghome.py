import os
import sys

# Khắc phục triệt để lỗi UnicodeEncodeError trên Windows Terminal bằng cách buộc stdout/stderr dùng UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres import PostgresSaver
from src.config import get_db_uri
from src.graph import agent_org_graph
import src.tools

# 1. Định nghĩa thư mục làm việc mục tiêu
WORKSPACE_PATH = os.path.abspath("D:/project/FindingHome")
print(f"[INFO] Target Workspace: {WORKSPACE_PATH}")


DB_URI = get_db_uri()

def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', errors='replace').decode('ascii'))

def main():
    print("\n=======================================================")
    print("   RUNNING AGENTIC DEVELOPER ORG ON FINDINGHOME (E2E)")
    print("=======================================================\n")
    
    try:
        # Khởi chạy checkpointer lưu bộ nhớ
        with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
            checkpointer.setup()
            
            app = agent_org_graph.compile(checkpointer=checkpointer)
            
            # Cấu hình phiên chạy (thread_id riêng biệt cho FindingHome)
            config = {
                "configurable": {
                    "thread_id": "findinghome_sprint567_session_001",
                    "workspace_path": WORKSPACE_PATH
                },
                "recursion_limit": 150
            }
            
            # PROMPT YÊU CẦU DỌN DẸP FILE RÁC & HOÀN THÀNH SPRINT 4 (GEOCODING & GIS)
            query = """
            You are a senior frontend engineer. Build the production-ready frontend for FindingHome, a real-estate web app for Da Nang, Vietnam.

Product goal:
- Help first-time home buyers evaluate whether a listing is overpriced
- Search listings
- Filter by district, property type, price, and area
- View listing details
- Show valuation insight and similar listings
- Present district-level statistics

Current backend:
- FastAPI backend already exists
- API base URL: http://localhost:8000
- Endpoints:
  - GET /health
  - GET /api/listings
  - GET /api/listings/{id}
  - GET /api/listings/{id}/valuation
  - GET /api/listings/{id}/similar
  - GET /api/map/districts/stats
  - GET /api/stats/summary

Important constraints:
- There is currently no real frontend implementation yet
- Backend has placeholder support for static files, but api/static does not exist
- Build the frontend as a clean, separate app
- Do not create a fake backend

Tech stack:
- Next.js 14+ App Router
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Query
- Leaflet
- Zod

Required screens:
1. Home/Search page
- Header with FindingHome branding
- Filter area for district, property type, min/max price, min/max area
- Listing results grid
- Map showing listing positions
- Summary cards:
  - total listings
  - average price
  - average price per m2
  - district coverage

2. Listing detail page
- title, price, area, district, property type, source, description
- map location
- valuation panel:
  - estimated market price
  - difference vs asking price
  - percentage over/under market
  - confidence level
  - plain Vietnamese explanation
- similar listings section

3. Stats page or stats section
- district-level statistics
- listing count
- average price
- median price if available
- average area if available

UX direction:
- trustworthy, modern, data-rich
- clean and readable
- avoid generic purple SaaS styling
- make valuation insight prominent
- format VND currency and square meters clearly

Implementation requirements:
- Generate full folder structure
- package.json
- README.md
- API client layer
- TypeScript types for backend payloads
- reusable UI components
- pages/routes
- loading, empty, and error states
- use NEXT_PUBLIC_API_BASE_URL for API base URL
- strong typing throughout
- reusable components
- clean separation between API, hooks, UI, and utils

If response shapes are unclear:
- infer reasonable shapes from endpoint names
- isolate assumptions in a types/adapters layer
- avoid spreading fragile assumptions across the app

Nice to have:
- debounced filters
- URL-synced search params
- mobile-friendly filter UX
- map/list synchronization
- valuation color coding:
  - green = good deal
  - amber = fair
  - red = overpriced

Output:
- concise architecture summary
- full implementation code
- setup instructions
- assumptions about backend schemas

Write complete code, not pseudo-code.
            """
            
            print(f"Goal Prompt: {query[:300]}...\n" + "="*60)
            
            inputs = {
                "messages": [HumanMessage(content=query)],
                "prd": "",
                "architecture": "",
                "code_files": {},
                "test_results": "",
                "is_verified": False,
                "iterations": 0
            }
            
            # Quét mã nguồn hiện tại của FindingHome để làm ngữ cảnh ban đầu
            inputs["code_files"] = src.agents.scan_workspace_files(WORKSPACE_PATH)
            print(f"[INFO] Scanned {len(inputs['code_files'])} files from FindingHome.")
            
            events = app.stream(inputs, config=config)
            
            for event in events:
                for node_name, state in event.items():
                    print(f"\n[Finished Node: {node_name}]")
                    if node_name == "ceo":
                        print("--- PRD Preview ---")
                        safe_print(state["prd"][:400] + "...\n")
                    elif node_name == "architect":
                        print("--- Architecture Design Preview ---")
                        safe_print(state["architecture"][:400] + "...\n")
                    elif node_name == "coder":
                        print(f"Number of files in workspace: {len(state.get('code_files', {}))}")
                        print(f"Current Files: {list(state.get('code_files', {}).keys())}\n")
                    elif node_name == "qa":
                        print(f"Is Verified: {state['is_verified']}")
                        print("Test Results:")
                        safe_print(state['test_results'] + "\n")
                    print("-" * 60)
            
            final_state = app.get_state(config)
            print("\n=======================================================")
            if final_state.values.get("is_verified", False):
                print("SUCCESS: FindingHome Sprint 4 Completed and Verified!")
            else:
                print("FINISHED: Execution finished (but not verified or hit limit).")
            print("=======================================================")
            
    except Exception as e:
        print(f"\n[ERROR] Failed to run: {e}")

if __name__ == "__main__":
    main()
