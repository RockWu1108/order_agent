from graph.state import AgentState
from langchain_core.messages import AIMessage
import json


# --- Conditional Edge Functions ---
# These functions direct the flow of the graph based on the current state.

def should_continue(state: AgentState) -> str:
    """
    Decides the next step after the main LLM call.
    """
    last_message = state["messages"][-1]

    # If the model explicitly decides to end, terminate.
    if "FINISH" in last_message.content:
        return "end"

    # If the model has generated tool calls, execute them.
    if last_message.tool_calls:
        # Here we add logic to intercept specific tool calls and route them
        # to our custom nodes instead of the generic 'action' node.
        if last_message.tool_calls[0]['name'] == 'search_google_maps':
            return "recommend"
        return "action"

    # Otherwise, the model is asking for more input or just responding.
    return "human"


def route_to_recommendations(state: AgentState) -> str:
    """
    Decides where to go after providing restaurant recommendations.
    """
    # This node is not strictly needed if the main agent handles the logic,
    # but it can be useful for more complex routing.
    # For now, we assume the user will reply and the main agent will
    # decide the next step.
    return "get_menu"


def route_after_recommendations(state: AgentState) -> str:
    """
    After the user has selected a restaurant and the agent has menu info,
    decide whether to proceed with form creation.
    """
    if state.get("menu") and state.get("selected_restaurant"):
        return "create_form"
    return "continue"


def route_after_form_creation(state: AgentState) -> str:
    """
    After attempting to create a Google Form, decide whether to schedule
    the summary task.
    """
    # Check if a form_url was successfully added to the state.
    if state.get("form_url"):
        return "schedule_task"
    else:
        # If form creation failed, we end the flow.
        # The create_order_form node should have already added an error message.
        return "end"
