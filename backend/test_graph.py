import os
import sys
from langchain_core.messages import HumanMessage

# Add current path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.graph import graph
from app.state import AgentState

def test_sync_graph():
    print("Initializing test state...")
    initial_state: AgentState = {
        "messages": [HumanMessage(content="Write a simple python script to add two numbers.")],
        "plan": "",
        "files": {},
        "test_results": "",
        "errors": [],
        "sender": "User",
        "iterations": 0,
        "current_task": "test",
        "api_key": "vai-test-key" # mock key
    }
    
    print("Running graph.stream() synchronously...")
    try:
        for event in graph.stream(initial_state):
            node_name = list(event.keys())[0]
            print(f"\n--- Node Completed: {node_name} ---")
            state = event[node_name]
            print(f"Plan: {state.get('plan')[:60] if state.get('plan') else 'None'}")
            print(f"Files written: {list(state.get('files', {}).keys())}")
    except Exception as e:
        import traceback
        print("\n--- ERROR OCCURRED ---")
        traceback.print_exc()

if __name__ == "__main__":
    test_sync_graph()
