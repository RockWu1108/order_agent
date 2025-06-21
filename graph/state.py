from typing import TypedDict, Annotated, List, Union
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, ToolMessage
import operator


# --- Agent State Definition ---
# This class represents the memory of our agent. It's a dictionary that
# gets passed between nodes in the graph.

class AgentState(TypedDict):
    """
    Represents the state of the conversation and ordering process.
    """
    # Core conversation messages
    messages: Annotated[List[AnyMessage], operator.add]

    # Thread ID for multi-user conversations
    thread_id: str

    # --- Phase 1: Requirement Gathering ---
    location: str
    food_type: str
    budget: str
    title: str
    deadline: str
    notification_channels: dict  # e.g., {"line_token": "...", "emails": ["..."]}

    # --- Phase 2: Recommendation & Confirmation ---
    restaurants: list  # List of restaurant results from Google Maps
    selected_restaurant: str

    # --- Phase 3: Form Generation ---
    menu: str  # Can be a string of text pasted by the user
    form_url: str
    sheet_url: str  # URL for the Google Sheet where responses are stored
