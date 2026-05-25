import os
from langchain_core.messages import AIMessage
from app.state import AgentState
from app.agents.base import get_llm
from app.config import MODEL_TESTER
from app.tools.file_system import write_file_sandbox
from app.tools.terminal import execute_command

def run_tester(state: AgentState) -> AgentState:
    """
    Tester Node:
    1. Writes all virtual memory state files to the physical sandbox disk.
    2. Automatically identifies test files or the entry point.
    3. Runs pytest or python commands.
    4. Reports standard outputs, failures or passes back into the state.
    """
    print("[Agent] Tester is running...")
    
    # 1. Synchronize all virtual files to the actual sandbox disk
    if not state["files"]:
        state["test_results"] = "Error: No files to test."
        state["sender"] = "Tester"
        state["messages"].append(AIMessage(content="Tester found no files to execute."))
        return state
        
    for relative_path, file_content in state["files"].items():
        write_file_sandbox(relative_path, file_content, root_dir=state.get("code_folder"))
        
    # 2. Determine how to run tests
    # Scan for files containing test logic
    files_list = list(state["files"].keys())
    test_files = [f for f in files_list if f.startswith("test_") or "test_" in f or "_test" in f]
    
    test_cmd = ""
    if test_files:
        test_cmd = "pytest"
        print(f"[Tester] Detected test files: {test_files}. Running: {test_cmd}")
    else:
        # Fallback to running entrypoint files to check compilation/syntax
        entrypoints = [f for f in files_list if f in ["main.py", "app.py", "run.py"]]
        if entrypoints:
            test_cmd = f"python {entrypoints[0]}"
            print(f"[Tester] No test files found. Verifying execution of entrypoint: {test_cmd}")
        else:
            # Fallback to python compilation check for all py files
            py_files = [f for f in files_list if f.endswith(".py")]
            if py_files:
                test_cmd = f"python -m py_compile {' '.join(py_files)}"
                print(f"[Tester] Compiling python files: {test_cmd}")
            else:
                test_cmd = "echo 'No Python files found to test'"
                
    # 3. Execute the command in the sandbox env
    test_output = execute_command(test_cmd)
    
    # 4. Use LLM to analyze the execution output
    # Resolve dynamic model: per-agent override → group fallback → config default
    model_name = state.get("model_tester") or state.get("model_fast") or MODEL_TESTER
    llm = get_llm(model_name, state.get("api_key"))
    
    system_prompt = (
        "You are a Quality Assurance Engineer.\n"
        "Your task is to analyze the test execution outputs and determine if the codebase passed verification.\n\n"
        "CRITICAL RESPONSE FORMAT:\n"
        "- If all tests passed successfully with no errors, write `SUCCESS` and a brief summary.\n"
        "- If there are compile errors, test failures, or execution exceptions, write a detailed summary of the failing test cases or stack traces so the Developer can debug them.\n"
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Test Command executed: `{test_cmd}`\n\nExecution Output:\n{test_output}"}
    ]
    
    response = llm.invoke(messages)
    analysis = response.content
    
    state["test_results"] = test_output
    state["sender"] = "Tester"
    
    # If LLM flags it as a failure, or if pytest exited with errors, report it
    is_success = "SUCCESS" in analysis.upper() and "[STDERR]" not in test_output
    
    if is_success:
        state["messages"].append(AIMessage(content=f"Tester verification PASSED!\n\n{analysis}"))
        print("[Tester] Tests PASSED successfully!")
    else:
        # Test failed, we keep test results so Coder can debug
        state["messages"].append(AIMessage(content=f"Tester verification FAILED.\n\n{analysis}"))
        print("[Tester] Tests FAILED.")
        
    return state
