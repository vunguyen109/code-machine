import os
import subprocess
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from src.config import get_workspace_path, DEFAULT_WORKSPACE_DIR

WORKSPACE_DIR = DEFAULT_WORKSPACE_DIR

def ensure_workspace_exists(workspace_dir: str):
    os.makedirs(workspace_dir, exist_ok=True)

@tool
def write_workspace_file(relative_path: str, content: str, config: RunnableConfig) -> str:
    """Ghi nội dung vào một file nằm trong thư mục workspace cách ly.
    relative_path: Đường dẫn tương đối từ workspace (ví dụ: 'app.py' hoặc 'tests/test_app.py')
    content: Nội dung mã nguồn ghi vào file.
    """
    try:
        workspace_dir = get_workspace_path(config)
        ensure_workspace_exists(workspace_dir)
        # Ngăn chặn path traversal ra ngoài workspace
        safe_path = os.path.abspath(os.path.join(workspace_dir, relative_path))
        if not safe_path.startswith(workspace_dir):
            return f"Error: Path {relative_path} is outside of the workspace directory."
        
        # Tạo thư mục cha nếu chưa có
        parent_dir = os.path.dirname(safe_path)
        os.makedirs(parent_dir, exist_ok=True)
            
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return f"Successfully wrote {relative_path}"
    except Exception as e:
        return f"Error writing file {relative_path}: {str(e)}"

@tool
def read_workspace_file(relative_path: str, config: RunnableConfig) -> str:
    """Đọc nội dung một file trong workspace.
    relative_path: Đường dẫn tương đối từ workspace.
    """
    try:
        workspace_dir = get_workspace_path(config)
        ensure_workspace_exists(workspace_dir)
        safe_path = os.path.abspath(os.path.join(workspace_dir, relative_path))
        if not safe_path.startswith(workspace_dir):
            return f"Error: Path {relative_path} is outside of the workspace directory."
            
        if not os.path.exists(safe_path):
            return f"Error: File {relative_path} does not exist."
            
        with open(safe_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file {relative_path}: {str(e)}"

@tool
def run_workspace_tests(test_command: str, config: RunnableConfig) -> str:
    """Chạy lệnh kiểm thử hoặc chạy code bên trong thư mục workspace cách ly và nhận kết quả.
    test_command: Lệnh chạy kiểm thử (ví dụ: 'pytest' hoặc 'python -m unittest discover' hoặc 'python test_app.py')
    """
    workspace_dir = get_workspace_path(config)
    ensure_workspace_exists(workspace_dir)
    print(f"\n[Tool: run_workspace_tests] Running command: {test_command} in {workspace_dir}...")
    try:
        # Chạy lệnh trong thư mục workspace
        result = subprocess.run(
            test_command,
            shell=True,
            cwd=workspace_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30 # Tránh treo lệnh vô hạn
        )
        output = f"Stdout:\n{result.stdout}\n\nStderr:\n{result.stderr}"
        if result.returncode == 0:
            return f"Tests PASSED successfully!\n\n{output}"
        else:
            return f"Tests FAILED (Exit Code {result.returncode}):\n\n{output}"
    except subprocess.TimeoutExpired:
        return "Error: Test execution timed out (30s)."
    except Exception as e:
        return f"Error during test execution: {str(e)}"

@tool
def delete_workspace_file(relative_path: str, config: RunnableConfig) -> str:
    """Xóa một file trong thư mục workspace.
    relative_path: Đường dẫn tương đối từ workspace (ví dụ: 'calculator.py').
    """
    workspace_dir = get_workspace_path(config)
    ensure_workspace_exists(workspace_dir)
    safe_path = os.path.abspath(os.path.join(workspace_dir, relative_path))
    if not safe_path.startswith(workspace_dir):
        return f"Error: Path {relative_path} is outside of the workspace directory."
    if not os.path.exists(safe_path):
        return f"Error: File {relative_path} does not exist."
    try:
        os.remove(safe_path)
        return f"Successfully deleted {relative_path}"
    except Exception as e:
        return f"Error deleting file: {str(e)}"

