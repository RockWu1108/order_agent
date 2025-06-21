import os
import uuid
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import HumanMessage
from graph.graph import builder
import json

app = Flask(__name__)
CORS(app)

# --- Configuration ---
# It's recommended to load these from environment variables or a secure config file
# For demonstration, we are using os.environ.get
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS',
                                                              'path/to/your/credentials.json')
os.environ['LINE_CHANNEL_ACCESS_TOKEN'] = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_LINE_CHANNEL_ACCESS_TOKEN')

# --- LangGraph Setup ---
memory = SqliteSaver.from_conn_string(":memory:")
graph = builder.compile(checkpointer=memory)


# --- Helper Functions ---
def _is_json(s):
    try:
        json.loads(s)
        return True
    except (ValueError, TypeError):
        return False


# --- API Routes ---
@app.route('/')
def index():
    return "Welcome to the Smart Food Ordering Agent API!"


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Main endpoint for interacting with the agent.
    Handles conversation state and streams responses.
    """
    data = request.json
    human_input = data.get("message")
    thread_id = data.get("thread_id")

    # --- Conversation Management ---
    # If no thread_id is provided, start a new conversation
    if not thread_id:
        thread_id = str(uuid.uuid4())

    # Configuration for the graph invocation
    config = {"configurable": {"thread_id": thread_id}}

    # Prepare the input for the graph
    inputs = {"messages": [HumanMessage(content=human_input)]}

    def event_stream():
        """
        Streams the agent's response back to the client.
        This allows for real-time updates in the UI.
        """
        try:
            # The stream method returns an iterator of events
            for event in graph.stream(inputs, config, stream_mode="values"):
                # The event is the full state of the graph after each step
                last_message = event["messages"][-1]

                # Check if the last message has content and send it
                if last_message and last_message.content:
                    # Check if the content is a JSON string (for structured data)
                    if isinstance(last_message.content, str) and _is_json(last_message.content):
                        # If it's JSON, send it as a structured data event
                        yield f"data: {last_message.content}\n\n"
                    else:
                        # Otherwise, wrap it in a standard message JSON object
                        response_data = {
                            "type": "message",
                            "content": last_message.content
                        }
                        yield f"data: {json.dumps(response_data)}\n\n"

            # Send a final event to indicate the end of the stream
            end_event = {"type": "end", "thread_id": thread_id}
            yield f"data: {json.dumps(end_event)}\n\n"

        except Exception as e:
            print(f"Error during stream: {e}")
            error_event = {"type": "error", "content": str(e)}
            yield f"data: {json.dumps(error_event)}\n\n"

    # Return the streaming response
    return Response(event_stream(), mimetype='text/event-stream')


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    # It's recommended to run Flask with a production-ready WSGI server like Gunicorn
    app.run(host='0.0.0.0', port=5000, debug=True)

