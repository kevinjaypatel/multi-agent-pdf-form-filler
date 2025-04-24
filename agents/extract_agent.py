from agno.agent import Agent, RunResponse 
from agno.playground.playground import Playground
from agno.utils.pprint import pprint_run_response
from agno.team.team import Team 

from textwrap import dedent
from agno.storage.postgres import PostgresStorage
from datetime import datetime
import json
import re

# Models 
from agno.models.openai import OpenAIChat

# Knowledge Base 
from agents.knowledge.combined_knowledge import knowledge_base as extract_agent_knowledge_base

# Tools 
from agents.tools.edit_form import edit_form

db_url = "postgresql+psycopg://agno:agno@db/agno"
agent_model_id = "gpt-4o"

# storage = PostgresStorage(
#         table_name="extraction_agent_sessions",
#         db_url=db_url
# )

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

    response: RunResponse = document_upload_agent.run(query) 
    
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
    response: RunResponse = document_upload_agent.run(query)
    
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

# Document Upload Agent 
document_upload_agent = Agent(
    name="Document Upload Agent",
    session_id="pdf_document_uploading_session",
    role="You support creating user profiles", 
    description="You are an expert in analyzing and extracting user information from documents",
    instructions=dedent("""\
        When the user uploads a document:
        1. Analyze each document through multiple specialized extraction passes:
        a. Initial pass: Extract basic metadata (document type, date, issuer)
        b. Structural pass: Identify document sections, tables, and hierarchies
        c. Detail pass: Extract all personal information with field context preservation
        d. Verification pass: Cross-check extracted data against expected patterns
        
        2. For each piece of extracted information:
        a. Maintain the original formatting 
        b. Tag with temporal relevance (recency, expiration if applicable)
        c. Preserve relationships between related data points
        
        3. When merging data across multiple documents:
        a. Maintain an audit trail of all information sources and conflicts
        b. Use contextual clues to determine the authoritative version
        c. Preserve alternative values with confidence rankings
        d. Apply domain-specific merging rules for specialized information
        
        4. IMPORTANT: After extracting information, ALWAYS use the `add_to_knowledge` tool to store the extracted data.
           You MUST call this tool explicitly with the extracted information.
           
        5. The `add_to_knowledge` tool requires a JSON object with the following schema:
            {
                "entities": {
                    "primary_user": {
                        "personal": {/* personal information */},
                        "contact": {/* contact details */},
                        "financial": {/* financial information */},
                        "professional": {/* work information */},
                        "medical": {/* health information */},
                        "relationships": {/* family/dependents */},
                        "identification": {/* ID numbers, licenses, etc. */}
                    },
                    "related_entities": [
                        {/* spouse, dependents, beneficiaries */}
                    ]
                },
                "documents": [
                    {
                        "type": "document_type",
                        "date": "issue_date",
                        "issuer": "document_issuer",
                        "extracted_fields": {/* all extracted fields */},
                        "confidence_metrics": {/* confidence scores */},
                        "processing_metadata": {/* extraction record */}
                    }
                ],
                "audit_trail": [
                    {/* record of all updates and conflicts */}
                ],
                "system_metadata": {
                    "last_updated": "timestamp",
                    "completeness_score": "0-100",
                    "information_gaps": [/* missing critical information */]
                }
            }
    """),
    model=OpenAIChat(
        id='gpt-4o',
        temperature=0.0
    ),
    # tool_choice="required",
    knowledge=extract_agent_knowledge_base,             # Provides the agent with a knowledge base to search and update               
    update_knowledge=True,                              # Adds a tool allowing the agent to update the knowledge base
    read_chat_history=True,
    show_tool_calls=True, 
    markdown=True,
    debug_mode=True,
    # storage=storage
)

# Document Search Agent 
document_search_agent = Agent(
    name="Document Search Agent",
    session_id="pdf_document_searching_session",
    role="You support finding missing information from documents",
    description="You are an expert in analyzing documents and finding missing information from them",
    instructions=dedent("""\    
        1. Extract and parse all missing information from the document 
        2. Use the `search_knowledge` tool to find the missing information. 
        Make sure to use the correct parameters when calling this tool.                 

        3. Important: Fields can be organised hierarchically, where one field can be placed under another.  
                        
        4. If you are analyzing a W2-form, make sure to structure the output in alphanumeric order based on the partial field name. 
        Remember that some fields are grouped together. 
                        
        For example, Box 15 in a W2-form is grouped with other fields. 

        5. You MUST return a Python dictionary with string keys and string values. Do not include comments in the output. 
        The dictionary should look like this:
        {
            "field_name_box_a": "new value", 
            "field_name_box_f": "new value", 
            "field_name_box_1": "new value",
            "field_name_box_15": "new value", 
            "field_name_box_20": "new value", 
        } 
        
        6. Remember not to include any comments in the dictionary output
        7. Each key in the dictionary should be a field name, and each value should be the corresponding value to fill in.
        Make sure all values are strings.                        
    """),
    # tool_choice="required",
    tools=[],
    model=OpenAIChat(
        id='gpt-4o', 
        temperature=0.0
    ), 
    knowledge=extract_agent_knowledge_base,
    search_knowledge=True,  
    update_knowledge=True,
    show_tool_calls=True, 
    debug_mode=True, 
    # storage=storage, 
    read_chat_history=True,
)

document_search_team = Team(
    name='Document Search Team', 
    mode='route', 
    model=OpenAIChat(
        id='gpt-4o', 
        temperature=0.0
    ),  
    members=[
        document_search_agent, 
    ], 
    show_tool_calls=True, 
    markdown=False, 
    instructions=[
        "Your job is to search the knowledge base for the missing information.",
        "You MUST return a Python dictionary with string keys and string values.",
    ],
    show_members_responses=True
)

task_classification_agent = Team(
    name='Task Classification Agent', 
    # agent_id='document_agent_team', 
    mode='route', 
    model=OpenAIChat(
        id='gpt-4o', 
        temperature=0.0
    ),
    members=[
        document_upload_agent,
        document_search_agent, 
    ], 
    show_tool_calls=True, 
    markdown=False, 
    instructions=[
        "Your job is to assess user queries and determine the best agent to handle the task.",
        "Either say, 'Document Upload Agent', or 'Document Search Agent' nothing else. Don't route tasks to the agents.",
        "Remember, your job is to determine the best agent to do the task, you don't have to route the task to any particular agent, or provide any other information.",  
        "If the user asks for a task that cannot be supported with one of the agents, respond with: ",
        "'I can only achieve the following document tasks: Document Upload, or Document Search (for documents that need to be filled). Please clarify your request'",
        "Always assess the users input before determining what agent can handle the task.",
        "For unsupported requests, respond with the above message.",  
    ],
    show_members_responses=True
)

if __name__ == "__main__":
    
    # Search Agent Output  
    query_results = {    
        "employee_social_security_number_box_a": "218-67-7264",
        "employer_identification_number_box_b": "26-7978697",
        "employer_name_address_zip_code_box_c": "Robinson, Clark and Mason PLC",
        "employee_first_name_initial_box_e": "April Prince",
        "employee_address_zip_code_box_f": "31126 Parsons Turnpike Apt. 170, East Shaun, IN 99674-9051"
    }

    result = edit_form(query_results) 
    print(result)
