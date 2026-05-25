import os
from typing import Dict, List
from app.config import SANDBOX_DIR

def _safe_path(relative_path: str) -> str:
    """Resolve and validate that the path is strictly inside the sandbox directory."""
    # Strip any leading slashes or dot-dot segments
    cleaned_path = os.path.normpath(relative_path).lstrip(os.sep).lstrip("/")
    while cleaned_path.startswith(".."):
        cleaned_path = cleaned_path.split(os.sep, 1)[1] if os.sep in cleaned_path else ""
    
    full_path = os.path.normpath(os.path.join(SANDBOX_DIR, cleaned_path))
    if not full_path.startswith(os.path.normpath(SANDBOX_DIR)):
        raise ValueError(f"Path traversal detected: {relative_path} is out of sandbox")
    return full_path

def write_file_sandbox(relative_path: str, content: str) -> str:
    """Create or overwrite a file inside the sandbox. Returns status message."""
    try:
        full_path = _safe_path(relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote {relative_path}."
    except Exception as e:
        return f"Error writing file {relative_path}: {str(e)}"

def read_file_sandbox(relative_path: str) -> str:
    """Read file content inside the sandbox. Returns the content or error message."""
    try:
        full_path = _safe_path(relative_path)
        if not os.path.exists(full_path):
            return f"Error: File {relative_path} does not exist."
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file {relative_path}: {str(e)}"

def list_dir_sandbox() -> Dict[str, str]:
    """Recursively list all files and their relative paths inside the sandbox directory."""
    files_dict = {}
    for root, _, filenames in os.walk(SANDBOX_DIR):
        for name in filenames:
            full_path = os.path.join(root, name)
            rel_path = os.path.relpath(full_path, SANDBOX_DIR)
            # Avoid reading very large or binary files (like .venv or config caches)
            if not any(exclude in rel_path for exclude in [".venv", "__pycache__", ".git"]):
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        files_dict[rel_path] = f.read()
                except Exception:
                    pass
    return files_dict

def delete_file_sandbox(relative_path: str) -> str:
    """Delete a file inside the sandbox. Returns status message."""
    try:
        full_path = _safe_path(relative_path)
        if not os.path.exists(full_path):
            return f"Error: File {relative_path} does not exist."
        os.remove(full_path)
        return f"Successfully deleted {relative_path}."
    except Exception as e:
        return f"Error deleting file {relative_path}: {str(e)}"
