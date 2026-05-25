import re
from typing import Dict
from langchain_core.messages import AIMessage
from app.state import AgentState
from app.agents.base import get_llm
from app.config import MODEL_CODER

def parse_file_tags(text: str) -> Dict[str, str]:
    """
    Parse tags in format:
    <write_file path="relative/path/to/file.ext">
    file content
    </write_file>
    
    Returns a dictionary of relative_path -> content
    """
    # Regex to find all write_file blocks
    pattern = re.compile(r'<write_file\s+path=["\']([^"\']+)["\']\s*>(.*?)</write_file>', re.DOTALL)
    matches = pattern.findall(text)
    
    files = {}
    for path, content in matches:
        # Strip leading/trailing newlines that are artifacts of formatting
        if content.startswith("\n"):
            content = content[1:]
        if content.endswith("\n"):
            content = content[:-1]
        files[path] = content
        
    return files

def run_coder(state: AgentState) -> AgentState:
    """
    Coder Node: Generates, updates, or debugs code files inside the workspace sandbox 
    based on the Architect plan, review logs, and test results.
    """
    print("[Agent] Coder is running...")
    
    # Resolve dynamic model: per-agent override → group fallback → config default
    model_name = state.get("model_coder") or state.get("model_complex") or MODEL_CODER
    llm = get_llm(model_name, state.get("api_key"))
    
    # Formulate context for the LLM
    plan = state.get("plan", "No plan drafted yet.")
    
    # Format existing files for LLM context
    existing_files_str = ""
    if state["files"]:
        existing_files_str = "\n--- Existing Files in Workspace ---\n"
        for path, content in state["files"].items():
            existing_files_str += f"\nFile: `{path}`\n```\n{content}\n```\n"
    else:
        existing_files_str = "\nWorkspace is currently empty. No files created yet."
        
    # Format errors/reviews/test results
    review_feedback = ""
    if state.get("errors"):
        review_feedback = "\n--- CODE REVIEW FEEDBACK ---\nPlease address the following issues:\n"
        for err in state["errors"]:
            review_feedback += f"- {err}\n"
            
    test_feedback = ""
    if state.get("test_results"):
        test_feedback = f"\n--- TEST EXECUTION FAILURES ---\n{state['test_results']}\n"
        
    system_prompt = (
        "You are an elite, senior software developer. You produce clean, optimized, and complete code.\n"
        "Your task is to write and modify the files required for this software project based on the Architect's plan, "
        "addressing any review comments or failing test outputs.\n\n"
        "CRITICAL INSTRUCTIONS ON OUTPUT FORMAT:\n"
        "To write or modify a file, you MUST wrap it inside `<write_file path=\"file_path\">` and `</write_file>` tags.\n"
        "You can write multiple files in a single response.\n"
        "Example:\n"
        "<write_file path=\"src/utils.py\">\n"
        "def add(a, b):\n"
        "    return a + b\n"
        "</write_file>\n\n"
        "Always write COMPLETE files. Do not use placeholders or write partial files like `// rest of code here`.\n"
        "Make sure to also write unit tests (e.g. pytest or unittest) for your code so the Tester can run them."
    )
    
    user_prompt = (
        f"--- ARCHITECT PLAN ---\n{plan}\n"
        f"{existing_files_str}\n"
        f"{review_feedback}\n"
        f"{test_feedback}\n"
        "Please implement or edit the files according to the plan and fix all issues. Output the modified/new files using the `<write_file path=\"...\">` tag format."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    response = llm.invoke(messages)
    content = response.content
    
    # Parse the files written by Coder
    new_files = parse_file_tags(content)
    
    # Update state's files
    if new_files:
        print(f"[Coder] Wrote {len(new_files)} files: {list(new_files.keys())}")
        for path, code in new_files.items():
            state["files"][path] = code
    else:
        print("[Coder] Warning: No file changes parsed from Coder's response.")
        
    # Append AIMessage
    state["sender"] = "Coder"
    state["messages"].append(AIMessage(content=f"Coder generated/updated codebase files.\n\n{content}"))
    
    # Clear errors and test results since new code was written (to trigger fresh review/test)
    state["errors"] = []
    state["test_results"] = ""
    
    return state
