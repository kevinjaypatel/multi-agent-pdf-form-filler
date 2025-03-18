from agno.agent import Agent, RunResponse 
from typing import Iterator 
from agno.workflow import Workflow 
from agno.models.openai import OpenAIChat  
from textwrap import dedent 
# from knowledge.combined_knowledge import knowledge_base as image_document_editor_knowledge_base
from pydantic import BaseModel, Field 
from agno.playground import Playground, serve_playground_app

class UserActionClassification(BaseModel): 
    upload_documents: bool = Field(..., description="True if the user wants to upload documents, or if the knowledge base needs to be updated")
    fill_out_form: bool = Field(..., description="True if the user needs a form filled out")

def classify_user_action(user_request: str) -> UserActionClassification:
    print(user_request) 
     

class ImageDocumentEditor(Workflow): 
    classification_agent: Agent = Agent(
        model=OpenAIChat("o3-mini"),
        name="Classification Agent", 
        description="You are a helpful assistant", 
        instructions=dedent("""\
        Your goal is the help the user understand how to use the Document Editor Tool. 
                            
        This is how the document editor works: 
        1. Initially, the user uploads a batch of documents (phone bills, w2 forms, resumes, etc)
        The documents can be any type (e.g. pdf, jpg, png, etc)
        2. Next, the user uploads a form that they want filled out (e.g. a job application, a resume, a 1040 tax form, etc)
        The image document editor fills out the form. 
                            
        Helpful tips for the user: 
        - Upload documents relative to the form that needs to be filled for the most accurate results   
                            

        Finally, your job is to classify the users request.  
        1. Determine if the user wants to upload documents, or is requesting a form to be filled out.     
        Currently we only fill one form at a time, make sure to let the user know this.  
        """), 
        response_model=UserActionClassification, 
        structured_outputs=True, 
        stream=True, 
    )

    image_document_uploader: Agent = Agent( 
        model=OpenAIChat("gpt-4o"),
        name="Image Document Uploader", 
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
        # knowledge=image_document_editor_knowledge_base,
        update_knowledge=True,  
    )

    image_document_editor: Agent = Agent(
        model=OpenAIChat("gpt-4o"), 
        name="Image Document Editor", 
        instructions=[], 
        search_knowledge=True, 
        update_knowledge=True, 
    )

    def run(self, user_request: str) -> Iterator[RunResponse]: 

        # Step 1: Classify the user's request 
        response: RunResponse = self.classification_agent.run(user_request) 
        print(response.content)
        # if request.upload_documents: 
        #     # yield self.image_document_uploader.run(user_request)
        #     pass 
        # else: 
        #     # yield self.image_document_editor.run(user_request) 
        #     pass 

workflow = ImageDocumentEditor() 
classification_agent = workflow.classification_agent 

app = Playground(agents=[classification_agent]).get_app() 

if __name__ == "__main__": 
    serve_playground_app('image_document_editor:app', reload=True, host="0.0.0.0", port=8000) 



    




