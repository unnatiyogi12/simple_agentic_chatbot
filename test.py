from agentic_checkpoint_backend import chatbot
from langchain_core.messages import BaseMessage, HumanMessage

CONFIG = {'configurable' : {'thread_id': 'thread-1'}}

# response = chatbot.invoke({'messages': [HumanMessage(content="Generate a blog about python programming")]}, config=CONFIG)
# print(response['messages'][-1].content)

for message_chunk, metada in chatbot.stream(
    {'messages': [HumanMessage(content="Generate a blog about python programming")]},
      config=CONFIG,
      stream_mode='messages'  
):
    if message_chunk.content:
        print(message_chunk.content, end = '', flush=True)
