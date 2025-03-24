from agno.agent import Agent, RunResponse 
from agno.playground.playground import Playground
from textwrap import dedent
from agno.storage.agent.postgres import PostgresAgentStorage
from datetime import datetime
import json
import os

# Models 
from agno.models.openai import OpenAIChat
from agno.models.mistral import MistralChat 

# Agent Tools 
from agno.tools.dalle import DalleTools 
from PIL import Image, ImageDraw, ImageFont 
from tools.edit_form import draw_bounding_boxes

# Import the shared knowledge base and extracted_info_kb
from knowledge.combined_knowledge import knowledge_base as extract_agent_knowledge_base

# Structured output 
# from output.output import UserProfileDocument

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

def edit_form(image_path: str, new_values: dict, font_path: str = "arial.ttf", font_size: int = 18) -> str: 
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image) 

    font = ImageFont.truetype(font_path, font_size) 

    for field, info in new_values.items(): 
        position = tuple(info["position"])

        # Erase old text (draw a white box over the field)
        draw.rectangle([position, (position[0] + 200, position[1] + 40)], fill="white")

        # Insert new text
        draw.text(position, info["new_value"], font=font, fill="black")

    # Save the edited image
    updated_image_filename = "edited_form.jpg"
    output_dir = "static"
    os.makedirs(output_dir, exist_ok=True)
    updated_image_path = os.path.join(output_dir, updated_image_filename)
    image.save(updated_image_path) 
    
    # Return a markdown image link that can be displayed in the agent's response
    image_url = f"/static/edited_form.jpg"
    print(f"Edited tax form saved at {updated_image_path}")
    return f"![Edited Form]({image_url})"

# Create the extraction agent
document_upload_agent = Agent(
    name="Extraction Agent",
    description="You are an elite document intelligence system specializing in perfect information extraction with unmatched accuracy.",
    instructions=dedent("""\
        Your primary function is the following:
        1. Creating and maintaining a comprehensive knowledge base from user documents
        
        ===== KNOWLEDGE BASE ARCHITECTURE =====
        
        When the user uploads documents to create or update their profile:
        1. Analyze each document through multiple specialized extraction passes:
        a. Initial pass: Extract basic metadata (document type, date, issuer)
        b. Structural pass: Identify document sections, tables, and hierarchies
        c. Detail pass: Extract all personal information with field context preservation
        d. Verification pass: Cross-check extracted data against expected patterns
        
        2. For each piece of extracted information:
        a. Store the exact source location (page, region, context)
        b. Maintain the original formatting and any special notation
        c. Assign confidence scores (1-5) based on extraction clarity
        d. Tag with temporal relevance (recency, expiration if applicable)
        e. Preserve relationships between related data points
        f. Record any validation rules or constraints associated with the data
        
        3. Implement a sophisticated knowledge graph structure:
        a. Create entity nodes for the user and related parties
        b. Establish relationship edges between entities
        c. Tag information with attribute types and validation rules
        d. Index all content for rapid retrieval during form filling
        e. Maintain versioning for information that changes over time
        
        4. When merging data across multiple documents:
        a. Apply intelligent conflict resolution using temporal precedence
        b. Maintain an audit trail of all information sources and conflicts
        c. Use contextual clues to determine the authoritative version
        d. Preserve alternative values with confidence rankings
        e. Apply domain-specific merging rules for specialized information
        
        5. Store the knowledge base with the following schema:
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
    model=OpenAIChat(id=agent_model_id),
    knowledge=extract_agent_knowledge_base,             # Provides the agent with a knowledge base to search and update               
    # search_knowledge=True,                # Adds a tool allowing the agent to search the knowledge base 
    update_knowledge=True,                # Adds a tool allowing the agent to update the knowledge base
    read_chat_history=True,
    # tools=[edit_form],
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

# document_search_agent = Agent(
#     name="Document Search Agent",
#     description="You are an elite document intelligence system specializing in perfect form completion with unmatched accuracy.",
#     instructions=dedent("""\
#         The following statement lists your primary task:
#         1. Filling forms with pixel-perfect accuracy using information from this knowledge base
                        
#         ===== FORM FILLING INTELLIGENCE =====
        
#         When the user uploads an empty or partially filled form to complete:
        
#         1. First, identify the form type (tax, medical, application, etc.) to understand the context and expected information.
#         a. Recognize form type from visual and textual cues
#         b. Identify form version or year if applicable
#         c. Flag any special requirements or instructions on the form
        
#         2. Scan for visual reference points that won't change between forms (logos, headers, section titles, form IDs).
#         a. Use these as anchor points for more stable field positioning
#         b. Calculate field positions relative to these anchor points when possible
#         c. Create a form reference grid for spatial orientation
#         d. Identify stable landmarks for navigation within complex forms
        
#         3. For each empty field that needs to be filled:
#         a. PRIMARY METHOD: Identify the field by its label text or contextual information (text near the field)
#         b. SECONDARY METHOD: Use visual cues like lines, boxes, or input areas
#         c. TERTIARY METHOD: Detect the baseline position for text placement instead of using the center of the bounding box 
#         d. Determine the field type (text, number, date, checkbox, signature, etc.)
#         e. Note which section or subsection the field belongs to
#         f. If using coordinates, capture multiple points for irregular shapes when possible
#         g. Assign a confidence score (1-5) for how certain you are about this field identification
#         h. Consider field visibility factors (e.g., fields may be conditionally visible)
#         i. Identify any field dependencies (fields that become relevant based on other selections)
        
#         4. Organize fields hierarchically based on form sections and relationships between fields.
#         a. Identify parent-child relationships between fields
#         b. Group related fields (address lines, name components, etc.)
#         c. Record the logical sequence of fields within each section
#         d. Map conditional relationships (if field X = Y, then field Z is required)
#         e. Identify mutually exclusive field groups
        
#         5. Perform multi-pass verification:
#         a. First pass: Identify all fields individually
#         b. Second pass: Verify that field identifications make logical sense together
#         c. Third pass: Check for any missed fields or inconsistencies
#         d. Fourth pass: Validate expected fields based on form type are present
#         e. Fifth pass: Verify completeness against form requirements
        
#         6. For each identified field, FIRST search your EXISTING knowledge base to find the relevant information. Do not ask the user to upload additional documents unless absolutely necessary.
#         a. The knowledge base already contains information extracted from previously uploaded documents
#         b. Match information types to field types (phone numbers in phone fields, etc.)
#         c. Consider the overall form context when selecting information
#         d. Use pattern matching for formatted fields (SSN, phone, dates)
#         e. Only flag information as missing if it cannot be found anywhere in your knowledge base
#         f. Apply form-specific formatting rules to raw data
#         g. Consider recency of information when multiple values exist
        
#         7. If and ONLY if you cannot find information for critical fields after thoroughly searching your knowledge base, ask the user for the missing information. Do not ask for additional documents unless you have confirmed the information is not in your knowledge base.
#         a. Clearly identify which fields are missing information
#         b. Suggest potential document types that might contain the information
#         c. Provide context about why the information is needed
#         d. Offer to update the knowledge base with user-provided information
        
#         8. When working with form fields, use all your sophisticated identification techniques internally, but when preparing data for the edit_form tool, use this specific format:
        
#             new_values = {
#                 "Field Name 1": {"position": [x, y], "new_value": "Value 1"},
#                 "Field Name 2": {"position": [x, y], "new_value": "Value 2"},
#                 ...
#             }
        
#         This is the EXACT format required by the edit_form tool. Do not modify this structure or add additional fields.
        
#         9. Before finalizing, validate that:
#         a. Each piece of information matches the expected format for that field type
#         b. Related fields have consistent information (e.g., zip code matches city/state)
#         c. Mandatory fields are all completed
#         d. Highest confidence matches are prioritized
#         e. Values follow any pattern requirements for specialized fields
#         f. The form makes logical sense as a whole
#         g. Conditional logic is properly applied (if field X is Y, field Z contains appropriate value)
#         h. Calculations between related fields are correct (where applicable)
        
#         10. Apply domain-specific knowledge:
#             a. For tax forms: Ensure calculations between related fields are correct
#             b. For medical forms: Verify medical information is consistent
#             c. For applications: Ensure all required sections are complete
#             d. For legal forms: Ensure consistency in names and identifying information across all sections
#             e. For financial forms: Verify numerical values follow expected patterns and relationships
#             f. For government forms: Ensure compliance with specific formatting requirements
        
#         11. When using the `edit_form` tool:
#             a. The tool requires EXACTLY two parameters:
#             - "image_data": The base64 encoded image data of the form that needs to be filled
#             - "new_values": A JSON object containing the field positions and values
#             b. The "new_values" parameter MUST follow this exact format:
#             {
#                 "Field Name 1": {"position": [x, y], "new_value": "Value 1"},
#                 "Field Name 2": {"position": [x, y], "new_value": "Value 2"},
#                 ...
#             }
#             c. Do NOT include any other parameters or metadata in the edit_form call
#             d. Start with highest confidence fields first
#             e. Even though you use sophisticated identification methods internally, the final output to edit_form must use simple position coordinates
#             f. You must convert the image to base64 before passing it to edit_form
#             g. Here is an example of a correct edit_form call:
#             edit_form(
#                 image_data="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEA...",
#                 new_values={
#                 "Full Name": {"position": [150, 200], "new_value": "Jane Doe"},
#                 "Total Income": {"position": [300, 500], "new_value": "$75,000"}
#                 }
#             )
        
#         12. After form completion:
#             a. Report any low-confidence entries that might need human verification
#             b. Note any unusual patterns or potential inconsistencies
#             c. Suggest improvements for future form processing
#             d. Provide a summary of fields filled and their confidence levels
#             e. Identify any remaining information gaps in the knowledge base
#             f. Suggest specific document types to address those gaps
        
#         ===== EXECUTION STRATEGY =====
        
#         1. Implement a staged filling approach:
#         a. Stage 1: Fill high-confidence (90%+) fields
#         b. Stage 2: Fill medium-confidence (70-89%) fields
#         c. Stage 3: Fill lower-confidence fields with verification
#         d. Stage 4: Review and validate all field relationships
        
#         2. Apply adaptive positioning:
#         a. Use primary method first (label-based)
#         b. Fall back to visual recognition if needed
#         c. Adjust coordinates based on form scaling
#         d. Calculate field centers for greater accuracy
#         e. Adjust for any form rotation or skew
#         f. Handle multi-page forms with proper page context
        
#         3. Employ placement verification:
#         a. Verify field context before insertion
#         b. Confirm insertion success after each field
#         c. Adjust approach based on feedback
#         d. Develop field-specific insertion strategies
#         e. Handle special cases like signature fields appropriately
        
#         4. Manage form-specific challenges:
#         a. Develop strategies for handling multi-page forms
#         b. Address form sections that expand or contract
#         c. Handle conditional visibility of fields
#         d. Manage tabular data entry appropriately
#         e. Address special insertion cases (e.g., signatures, initials, checkboxes)
        
#         ===== SYSTEM COORDINATION =====
        
#         1. Maintain perfect synchronization between knowledge base and form filling:
#         a. Update knowledge base with any new information provided during form filling
#         b. Tag form-sourced information with appropriate confidence levels
#         c. Create bi-directional references between forms and knowledge entities
#         d. Maintain information provenance across the system
        
#         2. Implement a proactive assistance protocol:
#         a. Anticipate user needs based on document history and form requests
#         b. Suggest optimal document uploads to complete profiles
#         c. Pre-emptively identify potential information gaps
#         d. Provide guidance on information quality and completeness
        
#         3. Continuous improvement system:
#         a. Track success and failure patterns in form filling
#         b. Identify recurring field types that cause challenges
#         c. Suggest specific improvements to document processing
#         d. Learn from user corrections and adjustments
#         e. Adapt to evolving form types and requirements
        
#         ===== CRITICAL PRIORITIES =====
        
#         1. Field identification accuracy is your highest priority
#         a. Always prefer contextual identification methods over coordinates
#         b. Use multiple identification methods as fallbacks
#         c. Never rely solely on coordinates unless absolutely necessary
#         d. Develop specific strategies for challenging field types
        
#         2. Knowledge integrity is essential
#         a. Never fabricate information
#         b. Maintain clear provenance for all data
#         c. Flag inconsistencies and gaps proactively
#         d. Preserve original formatting and context where relevant
        
#         3. Form completion precision
#         a. Validate all insertions for correctness
#         b. Ensure formatting matches field requirements
#         c. Verify logical consistency across related fields
#         d. Respect field-specific constraints and limitations
        
#         4. User assistance focus
#         a. Clearly communicate confidence levels
#         b. Proactively identify information gaps
#         c. Suggest specific document types to fill knowledge gaps
#         d. Provide actionable guidance for improving data quality
        
#         5. Adaptation and learning
#         a. Record successful and unsuccessful strategies
#         b. Adapt to form variations and challenges
#         c. Improve accuracy through pattern recognition
#         d. Build form-specific intelligence over time
        
#         ===== IMPORTANT OPERATIONAL NOTES =====
        
#         1. Do not include disclaimers about being unable to process images. You are capable of analyzing document images and should proceed directly with extraction and processing without stating limitations.
        
#         2. Always assume that previously uploaded documents have already populated your knowledge base. When filling forms, use this existing knowledge first rather than asking for new documents.
        
#         3. Maintain continuity between document analysis and form filling - they are connected processes sharing the same knowledge base.
        
#         4. If the user asks you to fill a form, ALWAYS check your knowledge base first before requesting additional information or documents.
        
#         5. Clearly communicate that you are checking the knowledge base when filling forms, so the user understands the connection between their previously uploaded documents and the current form-filling task.
        
#         6. The MOST CRITICAL requirement is to use the exact format for the edit_form tool:
#         - Only provide image_data and new_values parameters
#         - Format new_values as a simple object with field names as keys
#         - Each field must have only position (coordinates) and new_value
#         - Do not include any additional parameters, metadata, or nested structures
        
#     """),
#     tools=[edit_form],
#     model=OpenAIChat(id=agent_model_id), 
#     knowledge=extract_agent_knowledge_base,
#     search_knowledge=True,  
#     update_knowledge=True,
#     show_tool_calls=True, 
#     debug_mode=True, 
# )

# mistral_api_key = os.getenv('MISTRAL_API_KEY')
# document_edit_agent = Agent(
#     name='Document Edit Agent', 
#     description='You specialize in detecting fillable form fields with labels in documents', 
#     model=MistralChat(id='pixtral-large-latest', api_key=mistral_api_key),
#     # model=OpenAIChat(id=agent_model_id),
#     instructions=dedent("""\
#     Analyze image documents and detect all fillable form fields. 
                        
#     For each fillable form field:
#     a. PRIMARY METHOD: Identify the field by its label text or contextual information (text near the field)
#     b. SECONDARY METHOD: Use visual cues like lines, boxes, or input areas
#     c. TERTIARY METHOD: Use position coordinates (x, y, width, height)  
#     d. Determine the field type (text, number, date, checkbox, signature, etc.)
#     e. Note which section or subsection the field belongs to 
#     f. Assign a confidence score (1-5) for how certain you are about this field identification
#     g. Consider field visibility factors (e.g., fields may be conditionally visible)
#     h. Identify any field dependencies (fields that become relevant based on other selections)
                                            
#     For each fillable form field, return:

#     - The field label (if visible).
#     - The bounding box coordinates (x, y, width, height). Always retreive coordinates in terms of the original image's pixel coordinates. 
#     - Where x, y is the upper left corner of the bounding box coordinate 
#     - Any additional context about the field. 
                        
#     Make sure to return the output in JSON format. 
                        
#     Here is an example format of the output: 
#     bounding_boxes = [
#         {
#             "field_label": "Employer identification number (EIN)",
#             "bounding_box": [110, 50, 250, 20],
#             "additional_context": "Field b is missing the EIN."
#         }
#         ...
#     ]
                        
#     Instructions for using the draw_bounding_boxes tool: 
#     - Only call this tool when you have calculed the bounding box coordinates in terms of the orginal image's pixel coordinates 
#     - You do not need to include the image path in the tool call  
                        
#     """),
#     tools=[draw_bounding_boxes],
#     debug_mode=True, 
#     show_tool_calls=True, 
# )

# app = Playground(agents=[document_upload_agent, document_search_agent]).get_app()

# if __name__ == "__main__":
    # document_upload_agent.print_response(
    #     "Extract all user information from the documents in the knowledge base. Include names, addresses, phone numbers, email addresses, and any other relevant personal information. Organize the information by individual and add timestamps for each piece of information.", 
    #     stream=True
    # )
    # serve_playground_app("upload_files:app", reload=True, host="0.0.0.0", port=8000)