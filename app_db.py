from agentic_chatbot_db_backend import chatbot , get_all_threads
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import streamlit as st
import uuid 

# Generate a unique thread ID for each new conversation
def generate_thread_id():
    return str(uuid.uuid4())



# Add a new thread ID to the conversation list
def add_thread(thread_id):

    # Prevent the same thread from being added multiple times
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)

    

# Create a completely new chat conversation
def reset_chat():

    # Generate and assign a new thread ID
    st.session_state["thread_id"] = generate_thread_id()
    st.query_params["thread_id"] = st.session_state["thread_id"]

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

    # Return saved messages
    # Return an empty list if no messages are available
    return state.values.get("messages", [])


def format_messages(messages):
    formatted_messages = []

    for message in messages:
        if isinstance(message, HumanMessage):
            role = "user"
        elif isinstance(message, AIMessage):
            role = "assistant"
        else:
            continue

        formatted_messages.append({
            "role": role,
            "content": message.content
        })

    return formatted_messages


# Display the main application title
st.title("Agentic Chatbot with LangGraph")


# Create a list for storing all conversation thread IDs
if "chat_threads" not in st.session_state:
    threads = get_all_threads()

    if not isinstance(threads, list):
        threads = []

    st.session_state["chat_threads"] = threads


# Restore the thread from the URL after a page refresh. If no thread is
# specified, open the most recently saved conversation, or start a new one.
if "thread_id" not in st.session_state:
    thread_id = st.query_params.get("thread_id")
    if not thread_id:
        threads = st.session_state["chat_threads"]
        thread_id = threads[-1] if threads else generate_thread_id()

    st.session_state["thread_id"] = thread_id
    st.query_params["thread_id"] = thread_id
    st.session_state["message_history"] = format_messages(
        load_conversation(thread_id)
    )
elif "message_history" not in st.session_state:
    st.session_state["message_history"] = []


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


# Display all conversation threads in reverse order
# This shows the newest conversation first
for thread_id in st.session_state["chat_threads"][::-1]:

    # Create one sidebar button for every conversation
    if st.sidebar.button(
        str(thread_id),
        key=thread_id
    ):

        # Set the selected thread as the current thread
        st.session_state["thread_id"] = thread_id
        st.query_params["thread_id"] = thread_id
        st.session_state["message_history"] = format_messages(
            load_conversation(thread_id)
        )


        # Rerun the application to display the loaded messages
        st.rerun()


# ========================= Main chat interface =========================

# Display all messages from the currently selected conversation
for message in st.session_state["message_history"]:

    # Create either a user chat bubble or assistant chat bubble
    with st.chat_message(message["role"]):

        # Display the message content
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


    # Pass the current thread ID to LangGraph
    # LangGraph uses this ID to save and retrieve conversation memory
    CONFIG = {
        "configurable": {
            "thread_id": st.session_state["thread_id"]
        }
    }


    # Create the assistant chat-message container
    with st.chat_message("assistant"):

        # Stream the assistant response token by token
        ai_message = st.write_stream(

            # Return only the content of AI message chunks
            message_chunk.content

            # Stream messages from the LangGraph chatbot
            for message_chunk, metadata in chatbot.stream(
                {
                    # Send the latest user message to the chatbot
                    "messages": [
                        HumanMessage(content=user_input)
                    ]
                },

                # Use the current conversation thread
                config=CONFIG,

                # Stream individual message chunks
                stream_mode="messages"
            )

            # Display only AI messages
            # This prevents tool and user messages from appearing
            if isinstance(message_chunk, AIMessage)
        )


    # Save the complete assistant response in Streamlit session state
    st.session_state["message_history"].append({
        "role": "assistant",
        "content": ai_message
    })