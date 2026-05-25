from typing import Dict, List, TypedDict, Any
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    # Chat message log containing history of agent interactions
    messages: List[BaseMessage]
    
    # The high-level software architecture and implementation plan
    plan: str
    
    # Dict mapping relative file path -> file content
    files: Dict[str, str]
    
    # Output of test frameworks or compilation steps
    test_results: str
    
    # Accumulator of review feedback, linting issues or compiler errors
    errors: List[str]
    
    # The name of the node that generated the last message
    sender: str
    
    # Number of state machine loop iterations to prevent infinite looping
    iterations: int
    
    # The current sub-task target
    current_task: str
    
    # The dynamic API key passed from the client frontend
    api_key: str
