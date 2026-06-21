import os
from dotenv import load_dotenv
from smolagents import (
    OpenAIServerModel,
    MCPClient,
    CodeAgent,
    DuckDuckGoSearchTool,
    ToolCallingAgent,
    tool,
    PromptTemplates,
    PlanningPromptTemplate,
    ManagedAgentPromptTemplate,
    FinalAnswerPromptTemplate,
)

# Load environment variables from the .env file (if present)
load_dotenv()

# Access environment variables as if they came from the actual environment
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')