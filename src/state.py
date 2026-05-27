from typing import Annotated, Sequence, TypedDict, Dict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentOrgState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    prd: str                 # Tài liệu mô tả yêu cầu sản phẩm
    architecture: str        # Thiết kế kiến trúc & danh sách file
    code_files: Dict[str, str] # Danh sách các file code {path: content}
    test_results: str        # Kết quả chạy test gần nhất
    is_verified: bool        # True nếu đã vượt qua toàn bộ unit test
    iterations: int          # Số lần lập trình & sửa lỗi (để giới hạn loop)
