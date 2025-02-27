from agno.playground import Playground, serve_playground_app
from agent import rag_agent

# Create the playground app
app = Playground(
    agents=[rag_agent],
    # Enable file upload in the playground
    enable_file_upload=True,
    # Specify allowed file types
    allowed_file_types=[".pdf"],
).get_app()


if __name__ == "__main__":
    # Create upload directory if it doesn't exist
    import os
    os.makedirs("uploaded_pdfs", exist_ok=True)
    
    # Start the playground
    serve_playground_app("app:app", reload=True)