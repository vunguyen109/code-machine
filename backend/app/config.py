import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Vertex Key API settings
VERTEX_KEY_API_BASE = os.getenv("VERTEX_KEY_API_BASE", "https://vertex-key.com/v1")
VERTEX_KEY_API_KEY = os.getenv("VERTEX_KEY_API_KEY", "")

# Default Models
MODEL_ARCHITECT = os.getenv("MODEL_ARCHITECT", "aws/claude-sonnet-4-6")
MODEL_CODER = os.getenv("MODEL_CODER", "aws/claude-sonnet-4-6")
MODEL_REVIEWER = os.getenv("MODEL_REVIEWER", "aws/claude-haiku-4-5")
MODEL_TESTER = os.getenv("MODEL_TESTER", "aws/qwen3-codex")

# Sandbox folder inside workspace where files are created/tested
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SANDBOX_DIR = os.path.join(WORKSPACE_ROOT, "sandbox")

# Create sandbox dir if not exists
os.makedirs(SANDBOX_DIR, exist_ok=True)
