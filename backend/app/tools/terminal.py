import subprocess
import os
import sys
from app.config import SANDBOX_DIR, WORKSPACE_ROOT

def execute_command(command: str) -> str:
    """
    Execute a shell command inside the sandbox directory.
    Uses the project virtual environment (venv) to run python and pytest safely.
    """
    try:
        # Prepend our backend venv Scripts folder to the system PATH so that command invocation 
        # (e.g. 'python' or 'pytest') resolves to our custom environment packages.
        venv_scripts = os.path.join(WORKSPACE_ROOT, "backend", ".venv", "Scripts")
        
        env = os.environ.copy()
        if os.path.exists(venv_scripts):
            env["PATH"] = venv_scripts + os.pathsep + env.get("PATH", "")
            # Set virtualenv env var
            env["VIRTUAL_ENV"] = os.path.join(WORKSPACE_ROOT, "backend", ".venv")
            
        # Ensure Python outputs are printed unbuffered
        env["PYTHONUNBUFFERED"] = "1"
        
        # Execute inside the sandbox directory
        result = subprocess.run(
            command,
            shell=True,
            cwd=SANDBOX_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            timeout=60 # 60 seconds timeout to prevent hanging commands
        )
        
        output = []
        if result.stdout:
            output.append(result.stdout)
        if result.stderr:
            output.append("[STDERR]")
            output.append(result.stderr)
            
        if not output:
            return "Command executed successfully with no output."
            
        return "\n".join(output)
    except subprocess.TimeoutExpired:
        return f"Command execution timed out after 60 seconds: '{command}'"
    except Exception as e:
        return f"Error executing command: {str(e)}"
