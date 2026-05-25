from langchain_core.messages import AIMessage, HumanMessage
from app.state import AgentState
from app.agents.base import get_llm
from app.config import MODEL_ARCHITECT

def run_architect(state: AgentState) -> AgentState:
    """
    Architect Node: Analyzes requirements and drafts a comprehensive implementation plan,
    detailing the directory layout, design choices, and components.
    """
    print("[Agent] Architect is running...")
    
    # Resolve dynamic model: per-agent override → group fallback → config default
    model_name = state.get("model_architect") or state.get("model_complex") or MODEL_ARCHITECT
    llm = get_llm(model_name, state.get("api_key"))
    
    # Retrieve user request (usually the first message)
    user_prompt = ""
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            user_prompt = msg.content
            break
            
    system_prompt = (
        "You are an expert Software Architect and Tech Lead.\n"
        "Your task is to analyze the user prompt and design a robust, modular, and beautiful software architecture.\n\n"
        "Please provide an implementation plan in Markdown covering:\n"
        "1. Core design patterns and architectural decisions.\n"
        "2. Recommended folder and file structure inside the sandbox.\n"
        "3. Step-by-step development roadmap (which files to create/modify first).\n"
        "4. Testing strategy.\n\n"
        "Be extremely detailed, structured, and professional. Avoid vagueness."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"User request: {user_prompt}\n\nPlease draft the architecture design and implementation plan."}
    ]
    
    response = llm.invoke(messages)
    
    # Update the state
    state["plan"] = response.content
    state["sender"] = "Architect"
    state["messages"].append(AIMessage(content=f"Architect created the plan.\n\n{response.content}"))
    
    return state
