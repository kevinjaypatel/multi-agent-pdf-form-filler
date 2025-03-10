from agno.agent import Agent 
from agno.playground import Playground, serve_playground_app
from agents.rag_agent import rag_agent
from agents.extract_agent import extraction_agent
from agno.models.openai import OpenAIChat

# Agent Team 
agent_team = Agent(
    name="PDF Document Agent Team",
    model=OpenAIChat(id="gpt-4o"),
    team=[rag_agent, extraction_agent], 
    instructions=[
        "First extract all user information from the documents", 
        "If you find required missing information, create a query  "
    ]
)

# Create the playground app with just the agents parameter
app = Playground(
    # agents=[extraction_agent, rag_agent],
    agents=[extraction_agent],

).get_app()


if __name__ == "__main__":
    
    # Start the playground
    serve_playground_app("playground:app", reload=True, host="0.0.0.0", port=8000)