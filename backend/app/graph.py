from langgraph.graph import StateGraph, START, END
from app.state import AgentState
from app.agents.architect import run_architect
from app.agents.coder import run_coder
from app.agents.reviewer import run_reviewer
from app.agents.tester import run_tester

def increment_iterations(state: AgentState) -> AgentState:
    """Helper node to increment iteration counter and track loops."""
    state["iterations"] = state.get("iterations", 0) + 1
    print(f"\n--- Starting Development Iteration {state['iterations']}/10 ---")
    return state

def route_after_reviewer(state: AgentState):
    """
    Decide whether to route to Tester (if approved) 
    or back to Coder (if there are review errors).
    """
    if state.get("iterations", 0) >= 10:
        print("[Router] Maximum iterations (10) reached. Terminating process.")
        return "end"
        
    if state.get("errors"):
        print("[Router] Review failed. Routing back to Coder.")
        return "coder"
        
    print("[Router] Review APPROVED. Routing to Tester.")
    return "tester"

def route_after_tester(state: AgentState):
    """
    Decide whether to finish (if tests pass) 
    or route back to Coder (if tests fail).
    """
    if state.get("iterations", 0) >= 10:
        print("[Router] Maximum iterations (10) reached. Terminating process.")
        return "end"
        
    last_msg = state["messages"][-1].content if state["messages"] else ""
    if "PASSED" in last_msg:
        print("[Router] All verifications passed! Workflow completed.")
        return "end"
        
    print("[Router] Tester reported failures. Routing back to Coder for debugging.")
    return "coder"

# Define LangGraph State Machine
builder = StateGraph(AgentState)

# Add Nodes
builder.add_node("architect", run_architect)
builder.add_node("coder_setup", increment_iterations)
builder.add_node("coder", run_coder)
builder.add_node("reviewer", run_reviewer)
builder.add_node("tester", run_tester)

# Build Edges
builder.add_edge(START, "architect")
builder.add_edge("architect", "coder_setup")
builder.add_edge("coder_setup", "coder")
builder.add_edge("coder", "reviewer")

# Conditional Router Edges
builder.add_conditional_edges(
    "reviewer",
    route_after_reviewer,
    {
        "coder": "coder_setup",
        "tester": "tester",
        "end": END
    }
)

builder.add_conditional_edges(
    "tester",
    route_after_tester,
    {
        "coder": "coder_setup",
        "end": END
    }
)

# Compile Workflow Graph
graph = builder.compile()
print("[System] LangGraph Workflow compiled successfully.")
