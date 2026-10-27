from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.sqlite import SqliteSaver
from dotenv import load_dotenv
from pathlib import Path
import sqlite3
load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    timeout=20,
    max_retries=2,
)

from langgraph.graph.message import add_messages

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def chat_node(state: ChatState):
    # take user querey from state
    messages = state['messages']
    # send to llm
    response = llm.invoke(messages)
    # response store state
    return {'messages': [response]}


database_path = Path(__file__).resolve().with_name("chatbot.db")
conn = sqlite3.connect(database=str(database_path), check_same_thread=False)
checkpoint = SqliteSaver(conn)

graph = StateGraph(ChatState)

# add node
graph.add_node('chat_node', chat_node)

# add_edge
graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

# execute the graph
chatbot = graph.compile(checkpointer=checkpoint)

def get_all_threads():
    all_threads = []

    for chpt in checkpoint.list(None):
        thread_id = chpt.config['configurable']['thread_id']
        if thread_id not in all_threads:
            all_threads.append(thread_id)

    # Checkpoints are listed newest first; keep the list oldest first so the
    # sidebar can continue displaying it in reverse chronological order.
    return list(reversed(all_threads))