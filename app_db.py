from dotenv import load_dotenv
from pathlib import Path
import os

# --- FORCE LANGSMITH TRACING CONFIGURATION ---
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path, override=True)

# Force both modern and legacy configurations so the SDK catches them regardless of version
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGSMITH_PROJECT"] = "agentic_chatbot"
os.environ["LANGCHAIN_PROJECT"] = "agentic_chatbot"

if os.getenv("LANGSMITH_API_KEY") and not os.getenv("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
elif os.getenv("LANGCHAIN_API_KEY") and not os.getenv("LANGSMITH_API_KEY"):
    os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")

print("File path:", env_path)
print("File exists:", env_path.exists())
print("LANGSMITH_API_KEY loaded:", bool(os.getenv("LANGSMITH_API_KEY")))
print("LANGSMITH_PROJECT:", os.getenv("LANGSMITH_PROJECT"))
# ---------------------------------------------

from agentic_chatbot_db_backend import chatbot, get_all_threads
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import streamlit as st
import uuid 

# Add a new thread ID to the conversation list
def add_thread(thread_id):
    # Prevent the same thread from being added multiple times
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)

def generate_thread_id():
    return str(uuid.uuid4())


# Create a completely new chat conversation
def reset_chat():
    # Generate and assign a new thread ID
    st.session_state["thread_id"] = generate_thread_id()

    # Clear the current chat messages from the UI
    st.session_state["message_history"] = []

    # Add the new thread to the conversation list
    add_thread(st.session_state["thread_id"])


# Load a previous conversation from the LangGraph checkpointer
def load_conversation(thread_id):
    # Get the saved state for the selected thread
    state = chatbot.get_state(
        config={
            "configurable": {
                "thread_id": thread_id
            }
        }
    )
    # Return saved messages or an empty list if none are available
    return state.values.get("messages", [])


# Display the main application title
st.title("Agentic Chatbot with LangGraph")


# Create message_history when the app runs for the first time
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []


# Create a thread ID when the app runs for the first time
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()


# Create a list for storing all conversation thread IDs
if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = get_all_threads()


# Add the current thread to the conversation list
add_thread(st.session_state["thread_id"])


# ========================= Sidebar threading feature =========================

# Display the sidebar title
st.sidebar.title("My Conversations")


# Create a button for starting a new conversation
if st.sidebar.button("New Chat"):
    # Reset the current chat and create a new thread
    reset_chat()
    # Rerun the Streamlit app to update the interface
    st.rerun()


# Display all conversation threads in reverse order (newest first)
for thread_id in st.session_state["chat_threads"][::-1]:
    # Create one sidebar button for every conversation
    if st.sidebar.button(str(thread_id), key=thread_id):
        # Set the selected thread as the current thread
        st.session_state["thread_id"] = thread_id

        # Load the messages saved under the selected thread
        messages = load_conversation(thread_id)
        temp_messages = []

        # Loop through all saved messages
        for message in messages:
            if isinstance(message, HumanMessage):
                role = "user"
            elif isinstance(message, AIMessage):
                role = "assistant"
            else:
                continue

            temp_messages.append({
                "role": role,
                "content": message.content
            })

        # Replace the current UI history with the selected conversation
        st.session_state["message_history"] = temp_messages
        st.rerun()


# ========================= Main chat interface =========================

# Display all messages from the currently selected conversation
for message in st.session_state["message_history"]:
    with st.chat_message(message["role"]):
        st.text(message["content"])


# Create the chat input box
user_input = st.chat_input("Type here")


# Run this block after the user submits a message
if user_input:
    # Save the user's message in Streamlit session state
    st.session_state["message_history"].append({
        "role": "user",
        "content": user_input
    })

    # Display the user's message in the chat interface
    with st.chat_message("user"):
        st.text(user_input)

    # Pass the current thread ID and configuration to LangGraph
    CONFIG = {
        "configurable": {"thread_id": st.session_state["thread_id"]},
        "metadata": {
            "thread_id": st.session_state["thread_id"]
        },
        "run_name": "chat_trace",
    }

    # Create the assistant chat-message container
    with st.chat_message("assistant"):
        # Stream the assistant response token by token
        from langsmith import tracing_v2_enabled

        with tracing_v2_enabled(project_name="agentic_chatbot"):
            ai_message = st.write_stream(
                message_chunk.content
                for message_chunk, metadata in chatbot.stream(
                    {
                        "messages": [
                            HumanMessage(content=user_input)
                        ]
                    },
                    config=CONFIG,
                    stream_mode="messages"
                )
                if isinstance(message_chunk, AIMessage)
            )



    # Save the complete assistant response in Streamlit session state
    st.session_state["message_history"].append({
        "role": "assistant",
        "content": ai_message
    })