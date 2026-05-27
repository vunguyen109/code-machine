import os
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from tenacity import retry, stop_after_attempt, wait_exponential

# Load env variables from root directory .env
load_dotenv()

class RobustChatOpenAI(ChatOpenAI):
    """Subclass của ChatOpenAI tự động tích hợp cơ chế Exponential Backoff Retry
    cho mọi cuộc gọi API thông qua tenacity để chống lỗi nghẽn hoặc timeout từ Gateway/Cloudflare (lỗi 524, 502, 429).
    """
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        reraise=True,
        before_sleep=lambda retry_state: sys.stdout.write(
            f"\n[LLM Warning] API invocation failed: {retry_state.outcome.exception()}. "
            f"Retrying in {retry_state.next_action.sleep:.1f}s... (Attempt {retry_state.attempt_number}/5)\n"
        )
    )
    def _generate(self, *args, **kwargs):
        return super()._generate(*args, **kwargs)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        reraise=True,
        before_sleep=lambda retry_state: sys.stdout.write(
            f"\n[LLM Warning] API invocation failed: {retry_state.outcome.exception()}. "
            f"Retrying in {retry_state.next_action.sleep:.1f}s... (Attempt {retry_state.attempt_number}/5)\n"
        )
    )
    def invoke(self, *args, **kwargs):
        return super().invoke(*args, **kwargs)

def get_dynamic_llm(model_name: str = None, api_key: str = None) -> RobustChatOpenAI:
    """Khởi tạo ChatOpenAI với Model Name và API Key tùy chỉnh, tự động fallback về .env."""
    final_model = model_name or os.getenv("VERTEX_KEY_MODEL_NAME", "gpt-4o")
    final_key = api_key or os.getenv("VERTEX_KEY_API_KEY")
    final_base = os.getenv("VERTEX_KEY_API_BASE", "https://vertex-key.com/api/v1")
    
    return RobustChatOpenAI(
        model=final_model,
        openai_api_key=final_key,
        openai_api_base=final_base,
        temperature=0.2
    )

def get_llm():
    # Sử dụng lớp RobustChatOpenAI thay thế để tự động khắc phục lỗi mạng/timeout
    return get_dynamic_llm()


def get_db_uri():
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres_secure_password")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "agent_memory")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    return f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}?sslmode=disable"

DEFAULT_WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "workspace"))

def get_workspace_path(config: RunnableConfig = None) -> str:
    """Lấy đường dẫn thư mục làm việc (workspace) từ RunnableConfig, fallback về biến môi trường hoặc mặc định."""
    if config and isinstance(config, dict):
        workspace_path = config.get("configurable", {}).get("workspace_path")
        if workspace_path:
            return os.path.abspath(workspace_path)
            
    env_path = os.getenv("TARGET_WORKSPACE_DIR")
    if env_path:
        return os.path.abspath(env_path)
        
    return DEFAULT_WORKSPACE_DIR

