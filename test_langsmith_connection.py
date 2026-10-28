import os
from dotenv import load_dotenv
from langsmith import Client

# 1. Load .env file
load_dotenv()

# Print loaded configurations for confirmation
print("--- Checking Environment Variables ---")
print("Endpoint:", os.getenv("LANGSMITH_ENDPOINT"))
# print("API_key:", os.getenv("LANGSMITH_API_KEY"))
print("Project:", os.getenv("LANGSMITH_PROJECT"))
# print("Workspace ID loaded:", bool(os.getenv("LANGCHAIN_WORKSPACE_ID") or os.getenv("LANGSMITH_WORKSPACE_ID")))
print("--------------------------------------\n")

# 2. Test LangSmith API Connection
try:
    # Initialize LangSmith Client
    client = Client()
    
    # Try fetching projects to verify credentials
    projects = list(client.list_projects(limit=1))
    
    print(" SUCCESS: Connected to LangSmith successfully!")
    print(f" Connected Project: {os.getenv('LANGSMITH_PROJECT', 'default')}")
    
except Exception as e:
    print(" FAILED: Connection Error")
    print(f"Error Details: {e}")