from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    timeout=20,
    max_retries=0,
    max_output_tokens=128
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



checkpoint = MemorySaver()

graph = StateGraph(ChatState)

# add node
graph.add_node('chat_node', chat_node)

# add_edge
graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)


# execute the graph
chatbot = graph.compile(checkpointer=checkpoint)
