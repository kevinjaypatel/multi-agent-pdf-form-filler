from agno.playground import Playground, serve_playground_app
from agents.rag_agent import rag_agent

# Create the playground app with just the agents parameter
app = Playground(
    agents=[rag_agent],
).get_app()


if __name__ == "__main__":
    # Create upload directory if it doesn't exist
    import os
    os.makedirs("uploaded_pdfs", exist_ok=True)
    
    # Start the playground
    serve_playground_app("playground:app", reload=True, host="0.0.0.0", port=8000)