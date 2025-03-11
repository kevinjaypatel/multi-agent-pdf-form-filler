from agno.agent import Agent, RunResponse 
from agno.playground.playground import Playground
from agno.models.openai import OpenAIChat
from textwrap import dedent
from agno.storage.agent.postgres import PostgresAgentStorage
from datetime import datetime
import json

# Import the shared knowledge base and extracted_info_kb
from knowledge.combined_knowledge import knowledge_base as extract_agent_knowledge_base

# Structured output 
from output.output import UserProfileDocument

db_url = "postgresql+psycopg://agno:agno@db/agno"
agent_model_id = "gpt-4o"

def find_required_information(document_path: str=None) -> str: 
    """
    Find the required user information from the document

    Args: 
        document_path (str): The path to the document to analyze. Defaults to None. 

    Returns: 
        str: JSON string of the users missing information. 
    """

    query = dedent("""\
        First, analyze the documents to identify what required information is missing.
        Structure the missing information in JSON format. 
        In your knowledge base, search the JSON knowledge base with table name "user_extracted_info" to find the users missing information.    
        If information cannot be found in the knowledge base, clearly indicate what information needs to be collected from the user.
        When you find information, note its source document and timestamp for verification.
        If you find conflicting information across documents, highlight the discrepancies and ask for clarification.     
        Format your response as a structured JSON object with the following fields:
        {
          "missing_information": {
            "field_name": "reason why it's missing or conflicting"
          },
          "found_information": {
            "field_name": {
              "value": "extracted value",
              "source": "document name",
              "timestamp": "extraction time"
            }
          },
          "conflicts": {
            "field_name": [
              {"value": "value1", "source": "doc1", "timestamp": "time1"},
              {"value": "value2", "source": "doc2", "timestamp": "time2"}
            ]
          }
        }
    """)

    response: RunResponse = extraction_agent.run(query) 
    
    try:
        # Try to parse the response as JSON
        extracted_data = json.loads(response)
    except json.JSONDecodeError:
        # If not JSON, use the raw text
        extracted_data = {"raw_extraction": response}
        
    return json.dumps(extracted_data, indent=2)

# Function to extract and store information
def extract_and_store():
    """
    Structure the user data in JSON and store it in the knowledge base
    
    Args:
        document_path: Optional path to a specific document to analyze
    
    Returns:
        Extracted information with metadata
    """
    # Create timestamp for this extraction
    timestamp = datetime.now().isoformat()
    
    # Extract information from the document
    query = dedent("""\
        Extract all user information from the documents in the knowledge base.
        Include names, addresses, phone numbers, email addresses, and any other relevant personal information. 
        Format your response as a structured JSON object.
    """)
    # Get response from the extraction agent
    response: RunResponse = extraction_agent.run(query)
    
    extracted_data = {}
    try:
        # Try to parse the response as JSON
        # This assumes the agent returns structured data
        extracted_data = json.loads(response)
    except json.JSONDecodeError:
        # If not JSON, use the raw text
        extracted_data = {"raw_extraction": response}
    
    # Add metadata
    metadata = {
        "timestamp": timestamp,
        "source": "uploaded_document",
        "extraction_method": agent_model_id,
        "confidence": "high",
        "version": "1.0"
    }
    
    # Combine data with metadata
    data_with_metadata = {
        "data": extracted_data,
        "metadata": metadata
    }
    
    # Convert to JSON string for storage
    json_data = json.dumps(data_with_metadata, indent=2)
    
    # Use the imported extracted_info_kb instead of creating a new one
    extract_agent_knowledge_base.load_text(
        text=json_data,
        metadata=metadata,
        upsert=True
    )
    
    print(f"Stored extracted information in knowledge base with metadata: {json.dumps(metadata)}")
    
    return response, metadata

# Create the extraction agent
extraction_agent = Agent(
    name="Extraction Agent",
    description="You are an expert document analyzer specialized in extracting and finding user information.",
    # instructions=[
    #     "Use the extract_and_store tool to extract user information from documents", 
    #     "Use the find_required_information tool to find the user's missing information from their documents",
    #     "When extracting information from the knowledge base, be thorough and identify all relevant user details",
    #     "When finding missing information, only check the knowledge base before indicating information is missing",
    #     "Always structure your responses as valid JSON objects",
    #     "Track metadata for all extracted information including source and timestamp",
    #     "When a user uploads a document, it will be automatically added to your knowledge base"
    # ], 
    instructions=[
        "You assist users with finding missing information from their documents. ",
        "If the user provides a set of documents and asks you to create a user profile from it, then analyze the documents thoroughly.",
        "Determine each document type, and parse all user information from the documents such as names, addresses, phone numbers, email addresses, and all other personal information.",
        "If there are multiple documents, merge the data and normalize it. Even flag inconsistencies or deduplicate entries.",
        "Structure all parsed data in JSON format, and add this data to your knowledge base.",
        # "If the user provides a form and asks you to find the missing information, then analyze the document thoroughly. "
        # "Determine what information is missing.",
        "However, when a user uploads an empty form that they wish to be auto-filled, search your knowledge base for the required missing information.",
        # "Search your knowledge base to find the missing information.", 
        "Format the retrieved data to match the form's required fields",
        "Generate natural language completions or confirmations for fields that need human-like context",
        "Prefer the knowledge base over your training data when finding missing information",
        "If you cannot find the missing information after searching your knowledge base, ask the user for the missing information.", 
        "Take the normalized profile data and generate the appropriate filled form, adapting the language to match the form’s requirements."
    ], 
    # tools=[extract_and_store, find_required_information],
    model=OpenAIChat(id=agent_model_id),
    knowledge=extract_agent_knowledge_base,             # Provides the agent with a knowledge base to search and update               
    search_knowledge=True,                # Adds a tool allowing the agent to search the knowledge base 
    update_knowledge=True,                # Adds a tool allowing the agent to update the knowledge base
    read_chat_history=True,
    # add_context_instructions=True, 
    # add_references=True,
    show_tool_calls=True, 
    markdown=True,
    debug_mode=True,
    # Store conversations in postgres
    storage=PostgresAgentStorage(
        table_name="extraction_agent_sessions",
        db_url="postgresql+psycopg://agno:agno@db/agno"
    ),
    # response_model=UserProfileDocument
)

app = Playground(agents=[extraction_agent]).get_app()

if __name__ == "__main__":
    extraction_agent.print_response(
        "Extract all user information from the documents in the knowledge base. Include names, addresses, phone numbers, email addresses, and any other relevant personal information. Organize the information by individual and add timestamps for each piece of information.", 
        stream=True
    )
    # serve_playground_app("upload_files:app", reload=True, host="0.0.0.0", port=8000)