import os
from typing import Annotated
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL
from langchain_tavily import TavilySearch
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

# Setup environment variables
def _set_if_undefined(key: str, value: str):
    if not os.environ.get(key):
        os.environ[key] = value

# Fill in your API keys here or set them in your environment
_set_if_undefined("GEMINI_API_KEY", "")
_set_if_undefined("TAVILY_API_KEY", "")

# Initialize LLM using Gemini
# You can also use ChatOpenAI if you prefer
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

# Initialize Tavily search tool
tavily_tool = TavilySearch(max_results=5)

# Initialize Python REPL for running code
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

# Define prompt builder
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

# Create agents
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

# Math functions
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

# Create supervisor workflow
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

# Compile the workflow
supervisor = workflow.compile()

if __name__ == "__main__":
    # Test message
    query = "find US and New York state GDP in 2024. what % of US GDP was New York state?"
    print(f"Query: {query}\n" + "="*40)
    
    messages = [HumanMessage(content=query)]
    
    events = supervisor.stream(
        {"messages": messages},
        {"recursion_limit": 150},
    )
    
    for event in events:
        for agent_name, state in event.items():
            print(f"\n[Agent: {agent_name}]")
            if "messages" in state:
                for message in state["messages"]:
                    message.pretty_print()
            else:
                print(state)
            print("-" * 40)
