import os
import traceback
from dotenv import load_dotenv
load_dotenv()

print("VERTEX_KEY_API_KEY:", os.getenv("VERTEX_KEY_API_KEY"))
print("VERTEX_KEY_API_BASE:", os.getenv("VERTEX_KEY_API_BASE"))
print("VERTEX_KEY_MODEL_NAME:", os.getenv("VERTEX_KEY_MODEL_NAME"))
print("TAVILY_API_KEY:", os.getenv("TAVILY_API_KEY"))

print("\n--- Testing Vertex-Key Connection ---")
try:
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(
        model=os.getenv("VERTEX_KEY_MODEL_NAME", "gpt-4o"),
        openai_api_key=os.getenv("VERTEX_KEY_API_KEY"),
        openai_api_base=os.getenv("VERTEX_KEY_API_BASE"),
        temperature=0.2
    )
    res = llm.invoke("hello")
    print("Vertex-Key Success:", res)
except Exception as e:
    print("Vertex-Key Failed:")
    traceback.print_exc()

print("\n--- Testing Tavily Connection ---")
try:
    from langchain_tavily import TavilySearch
    tavily_tool = TavilySearch(max_results=1)
    res = tavily_tool.invoke("US GDP 2024")
    print("Tavily Success:", res)
except Exception as e:
    print("Tavily Failed:")
    traceback.print_exc()
