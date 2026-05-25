import os
from typing import Dict, Optional
from app.config import SANDBOX_DIR, WORKSPACE_ROOT


def _resolve_root_dir(root_dir: Optional[str]) -> str:
    """Resolve a safe root directory inside the workspace or sandbox."""
    if not root_dir:
        return SANDBOX_DIR

    normalized = os.path.normpath(root_dir)
    if os.path.isabs(normalized):
        root_path = normalized
    else:
        root_path = os.path.normpath(os.path.join(WORKSPACE_ROOT, normalized))

    if not root_path.startswith(os.path.normpath(WORKSPACE_ROOT)):
        raise ValueError(f"Invalid root directory. Only workspace subfolders are allowed: {root_dir}")

    if not os.path.exists(root_path):
        os.makedirs(root_path, exist_ok=True)

    return root_path


def _safe_path(relative_path: str, root_dir: Optional[str] = None) -> str:
    """Resolve and validate that the path is strictly inside the resolved root directory."""
    root_path = _resolve_root_dir(root_dir)
    cleaned_path = os.path.normpath(relative_path).lstrip(os.sep).lstrip("/")
    while cleaned_path.startswith(".."):
        cleaned_path = cleaned_path.split(os.sep, 1)[1] if os.sep in cleaned_path else ""

    full_path = os.path.normpath(os.path.join(root_path, cleaned_path))
    if not full_path.startswith(os.path.normpath(root_path)):
        raise ValueError(f"Path traversal detected: {relative_path} is out of root directory")
    return full_path


def write_file_sandbox(relative_path: str, content: str, root_dir: Optional[str] = None) -> str:
    """Create or overwrite a file inside the selected workspace folder."""
    try:
        full_path = _safe_path(relative_path, root_dir)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote {relative_path}."
    except Exception as e:
        return f"Error writing file {relative_path}: {str(e)}"


def read_file_sandbox(relative_path: str, root_dir: Optional[str] = None) -> str:
    """Read file content inside the selected workspace folder. Returns the content or error message."""
    try:
        full_path = _safe_path(relative_path, root_dir)
        if not os.path.exists(full_path):
            return f"Error: File {relative_path} does not exist."
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file {relative_path}: {str(e)}"


def list_dir_sandbox(root_dir: Optional[str] = None) -> Dict[str, str]:
    """Recursively list all files and their relative paths inside the selected workspace folder."""
    root_path = _resolve_root_dir(root_dir)
    files_dict = {}
    for root, _, filenames in os.walk(root_path):
        for name in filenames:
            full_path = os.path.join(root, name)
            rel_path = os.path.relpath(full_path, root_path)
            if not any(exclude in rel_path for exclude in [".venv", "__pycache__", ".git"]):
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        files_dict[rel_path] = f.read()
                except Exception:
                    pass
    return files_dict


def delete_file_sandbox(relative_path: str, root_dir: Optional[str] = None) -> str:
    """Delete a file inside the selected workspace folder. Returns status message."""
    try:
        full_path = _safe_path(relative_path, root_dir)
        if not os.path.exists(full_path):
            return f"Error: File {relative_path} does not exist."
        os.remove(full_path)
        return f"Successfully deleted {relative_path}."
    except Exception as e:
        return f"Error deleting file {relative_path}: {str(e)}"
