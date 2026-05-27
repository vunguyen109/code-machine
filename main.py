import os
import time
from typing import Annotated
from dotenv import load_dotenv

# 1. Load các biến môi trường từ file .env
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL
from langchain_core.messages import HumanMessage

from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langgraph.checkpoint.postgres import PostgresSaver

# 2. Khởi tạo cấu hình LLM qua cổng Vertex-Key
# Sử dụng ChatOpenAI được định tuyến tới Vertex-Key API Base
llm = ChatOpenAI(
    model=os.getenv("VERTEX_KEY_MODEL_NAME", "gpt-4o"),
    openai_api_key=os.getenv("VERTEX_KEY_API_KEY"),
    openai_api_base=os.getenv("VERTEX_KEY_API_BASE"),
    temperature=0.2
)

# 3. Định nghĩa Tools cho các Agent
tavily_tool = TavilySearch(max_results=5)
repl = PythonREPL()

@tool
def python_repl_tool(
    code: Annotated[str, "The python code to execute to generate your chart."],
):
    """Use this to execute python code. If you want to see the output of a value,
    you should print it out with `print(...)`. This is visible to the user."""
    try:
        result = repl.run(code)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    result_str = f"Successfully executed:\n```python\n{code}\n```\nStdout: {result}"
    return (
        result_str + "\n\nIf you have completed all tasks, respond with FINAL ANSWER."
    )

# 4. Định nghĩa prompt builder cho các agent con
def make_system_prompt(suffix: str) -> str:
    return (
        "You are a helpful AI assistant, collaborating with other assistants."
        " Use the provided tools to progress towards answering the question."
        " If you are unable to fully answer, that's OK, another assistant with different tools "
        " will help where you left off. Execute what you can to make progress."
        " If you or any of the other assistants have the final answer or deliverable,"
        " prefix your response with FINAL ANSWER so the team knows to stop."
        f"\n{suffix}"
    )

# 5. Khởi tạo các Agent con (Sub-agents)
research_agent = create_react_agent(
    model=llm,
    tools=[tavily_tool],
    name="research_agent",
    prompt=make_system_prompt("You can only do research. You are working with a chart generator colleague.")
)

chart_agent = create_react_agent(
    model=llm,
    tools=[python_repl_tool],
    name="chart_agent",
    prompt=make_system_prompt("You can only generate charts by using python_repl_tool. You are working with a researcher colleague.")
)

# Các hàm toán học cơ bản làm công cụ cho Math Agent
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b

def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b

def divide(a: float, b: float) -> float:
    """Divide two numbers."""
    return a / b

math_agent = create_react_agent(
    model=llm,
    tools=[add, multiply, divide],
    prompt=(
        "You are a math agent.\n\n"
        "INSTRUCTIONS:\n"
        "- Assist ONLY with math-related tasks\n"
        "- After you're done with your tasks, respond to the supervisor directly\n"
        "- Respond ONLY with the results of your work, do NOT include ANY other text."
    ),
    name="math_agent",
)

# 6. Tạo supervisor workflow để quản lý và điều phối các agent con
workflow = create_supervisor(
    [research_agent, chart_agent, math_agent],
    name="supervisor",
    model=llm,
    prompt="""You are a team supervisor managing a research expert, a chart expert, and a math expert.
    For current events or finding data, use research_agent.
    For generating charts/visualizations or running python code, use chart_agent.
    For basic math operations (add, multiply, divide), use math_agent.
    """
)

# 7. Cấu hình kết nối PostgreSQL từ file .env
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres_secure_password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "agent_memory")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DB_URI = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}?sslmode=disable"

def main():
    print("--- Starting Multi-Agent System ---")
    try:
        # Sử dụng PostgresSaver làm checkpointer để quản lý bộ nhớ hội thoại persistent
        with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
            # Tạo các bảng cơ sở dữ liệu cần thiết nếu chúng chưa tồn tại
            checkpointer.setup()
            print("[INFO] Successfully connected and configured DB Checkpointer.")

            # Compile supervisor workflow với checkpointer
            supervisor_app = workflow.compile(checkpointer=checkpointer)

            # Cấu hình thread_id cho phiên làm việc hiện tại và recursion_limit (Guardrail ngắt an toàn)
            config = {
                "configurable": {
                    "thread_id": "land_data_crawl_session_001"
                },
                "recursion_limit": 20  # Tối đa 20 bước xử lý để tránh lặp vô hạn gây tốn chi phí
            }

            # Câu hỏi thử nghiệm
            query = "find US and New York state GDP in 2024. what % of US GDP was New York state?"
            print(f"\nQuery: {query}")
            print("=" * 60)

            # Khởi chạy luồng stream
            events = supervisor_app.stream(
                {"messages": [HumanMessage(content=query)]},
                config=config
            )

            # In kết quả luồng xử lý của từng agent
            for event in events:
                for agent_name, state in event.items():
                    print(f"\n[Active Agent: {agent_name}]")
                    if "messages" in state:
                        for message in state["messages"]:
                            message.pretty_print()
                    else:
                        print(state)
                    print("-" * 60)

    except Exception as e:
        print(f"\n[ERROR] Failed to run Agent: {e}")
        print("\n[TROUBLESHOOTING GUIDE]:")
        print("1. Ensure local PostgreSQL database is running via:")
        print("   docker-compose up -d")
        print("2. Make sure connection info in .env matches the running Postgres instance.")
        print("3. Check if port 5432 is conflicting.")

if __name__ == "__main__":
    main()
