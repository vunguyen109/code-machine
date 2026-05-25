import os
from langchain_openai import ChatOpenAI
from app.config import VERTEX_KEY_API_BASE, VERTEX_KEY_API_KEY

def get_llm(model_name: str, api_key: str = None) -> ChatOpenAI:
    """
    Instantiate and return a ChatOpenAI client connected to the Vertex Key API.
    Resolves the api_key from dynamic state, falls back to the .env config.
    """
    # Use dynamically passed key or fallback to environment key
    key = api_key if api_key else VERTEX_KEY_API_KEY
    
    # Clean the key if it has quotes or whitespace
    if key:
        key = key.strip().strip("'").strip('"')
        
    if not key:
        raise ValueError(
            "Vertex Key API Key is missing. "
            "Please add `VERTEX_KEY_API_KEY=vai-xxxx` in your `backend/.env` file "
            "or enter it in the top settings panel of the Web Dashboard."
        )
        
    return ChatOpenAI(
        model=model_name,
        api_key=key,
        base_url=VERTEX_KEY_API_BASE,
        temperature=0.1,  # Low temperature for highly precise code generation
    )
