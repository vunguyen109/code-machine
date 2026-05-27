import os
import glob
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langchain_core.runnables import RunnableConfig
from src.config import get_llm, get_workspace_path, get_dynamic_llm
from src.state import AgentOrgState
from src.tools import write_workspace_file, read_workspace_file, run_workspace_tests, delete_workspace_file, WORKSPACE_DIR

llm = get_llm()

def get_node_llm(node_name: str, config: RunnableConfig = None):
    vertex_key = None
    model_name = None
    if config and isinstance(config, dict):
        configurable = config.get("configurable", {})
        vertex_key = configurable.get("vertex_key")
        agents_config = configurable.get("agents_config", {})
        if node_name in agents_config:
            model_name = agents_config[node_name].get("model")
    return get_dynamic_llm(model_name=model_name, api_key=vertex_key)


# Helper function quét toàn bộ file trong workspace để cập nhật state.code_files
def scan_workspace_files(workspace_dir: str = None) -> dict:
    if workspace_dir is None:
        workspace_dir = get_workspace_path(None)
    files_dict = {}
    if not os.path.exists(workspace_dir):
        return files_dict
    
    # Lấy toàn bộ file ngoại trừ các file tạm hoặc thư mục pycache
    for filepath in glob.glob(os.path.join(workspace_dir, "**", "*"), recursive=True):
        if os.path.isfile(filepath):
            # Lấy đường dẫn tương đối làm key
            rel_path = os.path.relpath(filepath, workspace_dir)
            # Bỏ qua thư mục hệ thống/thư viện
            if any(part in rel_path.split(os.sep) for part in [".pytest_cache", "__pycache__", ".git", "venv", ".venv", ".agent"]):

                continue
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    files_dict[rel_path] = f.read()
            except Exception:
                pass
    return files_dict

# 2. Định nghĩa các Graph Node (Hàm xử lý của đồ thị)

def ceo_node(state: AgentOrgState, config: RunnableConfig = None) -> dict:
    # Kiểm tra xem agent có được kích hoạt không
    if config and isinstance(config, dict):
        active_agents = config.get("configurable", {}).get("active_agents")
        if active_agents is not None and "ceo" not in active_agents:
            print("\n>>> [CEO Node] Bypassed (Disabled by User).")
            user_query = state["messages"][-1].content
            fallback_prd = state.get("prd") or f"Tài liệu yêu cầu sản phẩm (PRD) bị bỏ qua. Hãy làm theo yêu cầu trực tiếp của người dùng: {user_query}"
            return {"prd": fallback_prd}
            
    print("\n>>> [CEO Node] Analyzing requirements & writing PRD...")
    user_query = state["messages"][-1].content
    
    # Trích xuất nội dung các file tài liệu markdown hiện có để cung cấp ngữ cảnh trực tiếp
    docs_context = ""
    for path, content in state.get("code_files", {}).items():
        if path.endswith(".md"):
            docs_context += f"\nFile: {path}\nContent:\n{content}\n==================\n"
    
    prompt = f"""Bạn là CEO kiêm Product Manager của công ty công nghệ.
    
    Dưới đây là các tài liệu hiện có trong dự án (nếu có):
    {docs_context}
    
    Hãy phân tích yêu cầu phần mềm của người dùng dưới đây cùng với các tài liệu dự án trên để viết một tài liệu PRD (Product Requirements Document) hoàn chỉnh bằng tiếng Việt hoặc tiếng Anh.
    Tài liệu PRD phải bao gồm:
    1. Mục tiêu sản phẩm (Product Goals)
    2. Các tính năng cốt lõi (Core Features)
    3. Bộ quy tắc nghiệp vụ (Business Rules)
    4. Gợi ý các ca kiểm thử cần thực hiện (Test Cases)

    Yêu cầu của người dùng:
    "{user_query}"
    """
    
    node_llm = get_node_llm("ceo", config)
    response = node_llm.invoke([SystemMessage(content=prompt)])
    prd_content = response.content
    print("[CEO Node] Completed writing PRD.")
    return {
        "prd": prd_content,
        "messages": [response]
    }


def architect_node(state: AgentOrgState, config: RunnableConfig = None) -> dict:
    # Kiểm tra xem agent có được kích hoạt không
    if config and isinstance(config, dict):
        active_agents = config.get("configurable", {}).get("active_agents")
        if active_agents is not None and "architect" not in active_agents:
            print("\n>>> [Architect Node] Bypassed (Disabled by User).")
            fallback_arch = state.get("architecture") or "Bản thiết kế kiến trúc bị bỏ qua. Hãy lập trình trực tiếp theo PRD."
            return {"architecture": fallback_arch}

    print("\n>>> [Architect Node] Designing system architecture...")
    prd = state["prd"]
    
    docs_context = ""
    for path, content in state.get("code_files", {}).items():
        if path.endswith(".md"):
            docs_context += f"\nFile: {path}\nContent:\n{content}\n==================\n"
    
    prompt = f"""Bạn là Software Architect của công ty công nghệ.
    
    Dưới đây là các tài liệu hiện có trong dự án (nếu có):
    {docs_context}
    
    Hãy đọc tài liệu PRD dưới đây cùng với tài liệu dự án trên và thiết kế cấu trúc file/kiến trúc cho dự án.
    Hãy chỉ định:
    1. Danh sách các file cần tạo/chỉnh sửa trong thư mục `workspace/` (ví dụ: `pipeline/geocoder.py`, `tests/test_geocoding.py`).
    2. Chi tiết cấu trúc dữ liệu, các class và hàm cần được định nghĩa.
    3. Hướng dẫn kiểm thử cho QA (dùng pytest hoặc python unittest).

    Tài liệu PRD:
    {prd}
    """
    
    node_llm = get_node_llm("architect", config)
    response = node_llm.invoke([SystemMessage(content=prompt)])
    architecture_content = response.content
    print("[Architect Node] Completed architectural design.")
    return {
        "architecture": architecture_content,
        "messages": [response]
    }


def coder_node(state: AgentOrgState, config: RunnableConfig = None) -> dict:
    # Coder là node cốt lõi không nên bị bypass, nhưng vẫn hỗ trợ nếu có yêu cầu
    if config and isinstance(config, dict):
        active_agents = config.get("configurable", {}).get("active_agents")
        if active_agents is not None and "coder" not in active_agents:
            print("\n>>> [Coder Node] Bypassed (Disabled by User).")
            return {"iterations": state.get("iterations", 0) + 1}

    print(f"\n>>> [Coder Node] Coding (Iteration #{state.get('iterations', 0) + 1})...")
    prd = state["prd"]
    arch = state["architecture"]
    test_results = state.get("test_results", "Chưa có kết quả test trước đó.")
    
    instruction = f"""Bạn là Senior Software Engineer.
    Nhiệm vụ của bạn là lập trình phần mềm dựa trên PRD và bản thiết kế kiến trúc hệ thống.
    
    Tài liệu PRD:
    {prd}
    
    Thiết kế Kiến trúc:
    {arch}
    
    Kết quả chạy thử nghiệm kiểm thử gần nhất:
    {test_results}
    
    YÊU CẦU:
    1. Sử dụng công cụ `write_workspace_file` để viết hoặc cập nhật mã nguồn (ví dụ: 'app.py') trong thư mục workspace.
    2. Đọc mã nguồn hiện có bằng `read_workspace_file` nếu cần chỉnh sửa.
    3. Nếu có kết quả chạy thử nghiệm thất bại (Failed) ở trên, hãy phân tích lỗi (ví dụ: SyntaxError, AssertionError) và cập nhật các file code để sửa triệt để lỗi.
    4. Trả lời chi tiết những gì bạn đã làm sau khi hoàn thành.
    """
    
    # Khởi tạo Coder React Agent động với LLM tùy chỉnh
    node_llm = get_node_llm("coder", config)
    coder_react_agent = create_react_agent(
        model=node_llm,
        tools=[write_workspace_file, read_workspace_file, delete_workspace_file],
        name="coder_agent"
    )
    
    # Chạy Coder React Agent
    res = coder_react_agent.invoke({"messages": [HumanMessage(content=instruction)]}, config=config)
    
    # Quét workspace để đồng bộ hóa mã nguồn hiện tại vào state
    workspace_dir = get_workspace_path(config)
    updated_files = scan_workspace_files(workspace_dir)
    
    return {
        "code_files": updated_files,
        "iterations": state.get("iterations", 0) + 1,
        "messages": res["messages"]
    }

def qa_node(state: AgentOrgState, config: RunnableConfig = None) -> dict:
    # Kiểm tra xem agent có được kích hoạt không
    if config and isinstance(config, dict):
        active_agents = config.get("configurable", {}).get("active_agents")
        if active_agents is not None and "qa" not in active_agents:
            print("\n>>> [QA Node] Bypassed (Disabled by User).")
            return {
                "is_verified": True,
                "test_results": "Bỏ qua bước kiểm thử QA.",
                "code_files": state["code_files"]
            }

    print("\n>>> [QA Node] Setting up unit tests & running test suite...")
    prd = state["prd"]
    code_files = state["code_files"]
    
    instruction = f"""Bạn là QA Engineer của công ty công nghệ.
    Nhiệm vụ của bạn là viết và chạy các bài unit test tự động để xác định mã nguồn của Coder có đáp ứng đúng PRD hay không.
    
    Tài liệu PRD:
    {prd}
    
    Mã nguồn hiện tại trong workspace:
    {code_files}
    
    YÊU CẦU:
    1. Viết mã nguồn kiểm thử vào file tương ứng (ví dụ: 'test_app.py') sử dụng thư viện `unittest` hoặc `pytest` trong Python.
    2. Lưu file test bằng `write_workspace_file`.
    3. Chạy các bài test sử dụng công cụ `run_workspace_tests` (ví dụ chạy lệnh 'pytest' hoặc 'python -m unittest test_app.py').
    4. Kiểm tra kỹ đầu ra của `run_workspace_tests`. Nếu có lỗi (AssertionError, ImportError, v.v.), hãy báo cáo chi tiết nguyên nhân lỗi.
    5. Đừng chỉ dừng lại ở việc tạo file test, bạn BẮT BUỘC phải chạy công cụ `run_workspace_tests` ít nhất 1 lần để xác minh kết quả.
    """
    
    # Khởi tạo QA React Agent động với LLM tùy chỉnh
    node_llm = get_node_llm("qa", config)
    qa_react_agent = create_react_agent(
        model=node_llm,
        tools=[write_workspace_file, read_workspace_file, run_workspace_tests, delete_workspace_file],
        name="qa_agent"
    )
    
    # Chạy QA React Agent
    res = qa_react_agent.invoke({"messages": [HumanMessage(content=instruction)]}, config=config)
    
    # Quét lại workspace để cập nhật bất kỳ file test nào QA viết
    workspace_dir = get_workspace_path(config)
    updated_files = scan_workspace_files(workspace_dir)
    
    # Xác định xem bài test chạy thành công hay thất bại dựa trên phản hồi của tool chạy test
    # Chúng ta tìm tin nhắn cuối cùng của agent hoặc tin nhắn tool run_workspace_tests gần nhất
    test_output = ""
    is_verified = False
    
    for msg in reversed(res["messages"]):
        if msg.type == "tool" and msg.name == "run_workspace_tests":
            test_output = msg.content
            break
            
    if "Tests PASSED" in test_output:
        is_verified = True
        print("[QA Node] Success! All test cases PASSED successfully.")
    else:
        print("[QA Node] Test failures detected! Sending feedback back to Coder.")
        if not test_output:
            test_output = "QA Agent đã không chạy công cụ run_workspace_tests thành công hoặc không ghi nhận kết quả."
            
    return {
        "test_results": test_output,
        "is_verified": is_verified,
        "code_files": updated_files,
        "messages": res["messages"]
    }
