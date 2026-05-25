import uvicorn
import os
import sys

# Add the current directory to python path to resolve modules correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("[System] Starting CodeMachine FastAPI backend server on http://127.0.0.1:8000")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
