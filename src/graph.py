from langgraph.graph import StateGraph, START, END
from src.state import AgentOrgState
from src.agents import ceo_node, architect_node, coder_node, qa_node

# 1. Khởi tạo đồ thị với State Schema chung
builder = StateGraph(AgentOrgState)

# 2. Thêm các Node xử lý
builder.add_node("ceo", ceo_node)
builder.add_node("architect", architect_node)
builder.add_node("coder", coder_node)
builder.add_node("qa", qa_node)

# 3. Định nghĩa các Cạnh (Edges) cố định
builder.add_edge(START, "ceo")
builder.add_edge("ceo", "architect")
builder.add_edge("architect", "coder")
builder.add_edge("coder", "qa")

# 4. Định nghĩa hàm Router để quyết định bước tiếp theo từ QA Node
def should_continue(state: AgentOrgState):
    # Nếu đã vượt qua test kiểm thử hoặc vượt quá giới hạn lặp (5 lần) thì kết thúc
    if state.get("is_verified", False):
        print(f"\n[System Router] Mã nguồn đã đạt chuẩn chất lượng. Kết thúc quy trình phát triển.")
        return END
    
    iterations = state.get("iterations", 0)
    if iterations >= 5:
        print(f"\n[System Router] Đạt giới hạn số lần sửa lỗi tối đa (5 vòng lặp). Kết thúc quy trình.")
        return END
        
    print(f"\n[System Router] Code chưa vượt qua bài test. Quay lại bước lập trình (Coder Node).")
    return "coder"

# Thêm cạnh điều kiện cho QA Node
builder.add_conditional_edges(
    "qa",
    should_continue,
    {
        END: END,
        "coder": "coder"
    }
)

# 5. Compile đồ thị (sẽ được truyền checkpointer ở file main)
# Chúng ta export builder để main.py có thể compile kèm checkpointer
agent_org_graph = builder
