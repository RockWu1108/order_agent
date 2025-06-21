from langgraph.graph import StateGraph, END
from graph.state import AgentState
from graph.nodes import (
    call_model,
    call_tool,
    human_input_node,
    provide_recommendations,
    create_order_form,
    schedule_summary_task,
    finish_node,
)
from .conditional_edges import (
    should_continue,
    route_to_recommendations,
    route_after_recommendations,
    route_after_form_creation
)

# --- Graph Definition ---
# This is where we wire up the nodes and edges to create the application logic.

builder = StateGraph(AgentState)

# 1. Define the Nodes
builder.add_node("agent", call_model)
builder.add_node("action", call_tool)
builder.add_node("human", human_input_node)
builder.add_node("recommend_restaurants", provide_recommendations)
builder.add_node("create_order_form", create_order_form)
builder.add_node("schedule_summary_task", schedule_summary_task)
builder.add_node("finish", finish_node)

# 2. Set the Entry Point
builder.set_entry_point("agent")

# 3. Define the Edges

# Conditional edge after the main agent decides the next step
builder.add_conditional_edges(
    "agent",
    should_continue,
    {
        "action": "action",
        "recommend": "recommend_restaurants", # New route to our custom recommendation node
        "human": "human",
        "end": END,
    },
)

# After a tool is called, go back to the main agent to process the results
builder.add_edge("action", "agent")

# After getting human input, go back to the agent
builder.add_edge("human", "agent")

# Conditional edge to decide what to do after providing recommendations
builder.add_conditional_edges(
    "recommend_restaurants",
    route_to_recommendations,
    {
        "get_menu": "agent",  # Go back to agent to find the menu
        "human": "human"      # Go back to human for clarification
    }
)

# After getting the menu and the user confirms, create the form
builder.add_conditional_edges(
    "agent", # This edge now comes from the main agent node
    route_after_recommendations,
    {
        "create_form": "create_order_form",
        "continue": "agent" # Default to continue conversation
    }
)

# After creating the form, schedule the background task
builder.add_conditional_edges(
    "create_order_form",
    route_after_form_creation,
    {
        "schedule_task": "schedule_summary_task",
        "end": "finish" # If form creation fails, end.
    }
)

# After scheduling, the process is finished for now.
builder.add_edge("schedule_summary_task", "finish")
