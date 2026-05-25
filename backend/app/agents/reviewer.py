import re
from langchain_core.messages import AIMessage
from app.state import AgentState
from app.agents.base import get_llm
from app.config import MODEL_REVIEWER

def run_reviewer(state: AgentState) -> AgentState:
    """
    Reviewer Node: Audits generated files for syntax correctness, code standards,
    architectural alignment, and security flaws.
    """
    print("[Agent] Reviewer is running...")
    
    llm = get_llm(MODEL_REVIEWER, state.get("api_key"))
    
    # Format current codebase files
    files_str = ""
    if state["files"]:
        for path, content in state["files"].items():
            files_str += f"\nFile: `{path}`\n```\n{content}\n```\n"
    else:
        files_str = "No files created in workspace."
        
    system_prompt = (
        "You are an elite Code Reviewer, Security Engineer, and QA Expert.\n"
        "Your task is to analyze the files currently under development and review them for:\n"
        "1. Correctness and logic bugs.\n"
        "2. Code quality, organization, clean-code practices, and design patterns.\n"
        "3. Security vulnerabilities and secure data handling.\n"
        "4. Syntax errors, missing imports, or undefined variables.\n\n"
        "CRITICAL RESPONSE FORMAT:\n"
        "- If the codebase is correct, complete, and ready for execution/testing, write `APPROVED` in your response.\n"
        "- If there are issues, write a list of specific, actionable review comments using bullet points starting with `- `.\n"
        "Do not write both. Only approve if it's 100% ready."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Please review the current codebase:\n{files_str}"}
    ]
    
    response = llm.invoke(messages)
    content = response.content
    
    # Check if approved
    is_approved = "APPROVED" in content.upper() and not re.search(r'^-\s+', content, re.MULTILINE)
    
    state["sender"] = "Reviewer"
    state["messages"].append(AIMessage(content=f"Reviewer analyzed the codebase.\n\n{content}"))
    
    if is_approved:
        print("[Reviewer] Codebase APPROVED!")
        state["errors"] = []
    else:
        # Extract bulleted items as errors
        errors = re.findall(r'^-\s*(.*)', content, re.MULTILINE)
        if not errors:
            # Fallback if no bullet points but not APPROVED
            errors = [content]
        print(f"[Reviewer] Found {len(errors)} issues.")
        state["errors"] = errors
        
    return state
