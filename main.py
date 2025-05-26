# FastAPI
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# Agno
from agno.agent import RunResponse, Agent 
from agno.media import Image, File as AgnoUploadFile 
from agno.run.response import RunEvent 

from pydantic import BaseModel 
from typing import Dict, Optional, Any, Iterator, AsyncGenerator, List   
import json 
from io import BytesIO 
import re 

# Extract Agent 
from agents.extract_agent import task_classification_agent, document_upload_agent, document_search_team

# Tools 
from agents.tools.edit_form import edit_form 

from utils.prompt import convert_to_agno_message
from utils.types import ClientMessage, AgnoMessage

app = FastAPI()

# Add CORS middleware with more specific configuration 
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"],
    allow_credentials=True, 
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"], 
)

# Define agent names as constants
DOCUMENT_UPLOAD_AGENT = "Document Upload Agent"
DOCUMENT_SEARCH_AGENT = "Document Search Agent"

class ChatRequest(BaseModel): 
    message: str 
    conversation_id: Optional[str] = None 
    metadata: Optional[Dict[str, Any]] = None 

class Request(BaseModel): 
    messages: List[ClientMessage]

async def generate_stream(response_stream: Iterator[RunResponse], conversation_id=None, metadata=None): 
    """Generate a stream of responses from the agent."""
    response_stream = task_classification_agent.run(
        message, 
        conversation_id=conversation_id,  
        metadata=metadata,  
        stream=True
    )

    for chunk in response_stream: 
        if hasattr(chunk, 'content') and chunk.content: 
              # Format as SSE (Server-Sent Events)
            yield f"data: {json.dumps({'content': chunk.content})}\n\n" 

    yield f"data: {json.dumps({'content': '[DONE]'})}\n\n" 

@app.post("/agno/api/chat")
async def chat_with_agent(
    message: str = Form(...), 
    file: Optional[UploadFile] = File(None)
): 
    print("\n--- Received Data ---")
    print(f"User: {message}")

    try: 
        # Determine which agent will handle the task 
        response = task_classification_agent.run(message)
        print(f"Task relayed to: {response.content}")

        if file: 
            # Validate file size (e.g., 10MB limit)
            if file.size > 10 * 1024 * 1024:  # 10MB in bytes
                raise ValueError("File size exceeds 10MB limit")

            file_bytes = await file.read()  
            if (response.content == DOCUMENT_UPLOAD_AGENT):
                run_result = document_upload_agent.run(
                    message, 
                    images = [
                        Image(content=file_bytes)
                    ]
                )
                print(f"Document Upload Agent Response: {run_result.content}")
                return JSONResponse(
                    content={
                        "status": "OK", 
                        "agent_response": f"{run_result.content}", 
                    }
                )

            elif (response.content == DOCUMENT_SEARCH_AGENT):
                if (file.content_type != "application/pdf"):
                    raise ValueError(f"File must be a PDF for {DOCUMENT_SEARCH_AGENT}")
                
                print(f"Running: {DOCUMENT_SEARCH_AGENT}")
                run_result = document_search_team.run(
                    message, 
                    files = [
                        AgnoUploadFile(content=file_bytes)
                    ]
                )
                 
                search_agent_results = run_result.content

                # Parse the output from the search agent 
                dict_pattern = r'```python\s*({[\s\S]*?})\s*```' 
                dict_match = re.search(dict_pattern, search_agent_results)
                if not dict_match:
                    raise ValueError("No dictionary of search results found in the response")

                dict_str = dict_match.group(1)
                dict_str = dict_str.replace("'", '"')
                query_results = json.loads(dict_str)

                # Create a new BytesIO object with the file bytes
                file_stream = BytesIO(file_bytes)
                output_stream = await edit_form(file_stream, query_results) 

                return StreamingResponse(output_stream, media_type="application/pdf", headers={
                    "Content-Disposition": f"attachment; filename={file.filename}_filled.pdf"
                })
            
            else: 
                return JSONResponse(
                    content={
                        "status": "OK", 
                        "agent_response": f"{response.content}",
                        "information": f"Please clarify your request for the appropriate agent", 
                    }
                )
                
        else: 
            return JSONResponse(
                content={
                    "status": "OK", 
                    "agent_response": f"{response.content}",
                    "information": f"No file(s) were uploaded", 
                }
            )
        
    except ValueError as ve: 
        return JSONResponse(
            content={
                "status": "ERROR", 
                "message": f"Validation error: {str(ve)}"
            },
            status_code=400
        )
    
#     except Exception as e: 
#         return JSONResponse(
#             content={
#                 "status": "ERROR", 
#                 "message": f"Error processing request: {str(e)}"
#             },
#             status_code=500
#         )
    
def stream_response(message: List[AgnoMessage], protocol: str = 'data'): 
    # Get the streamed response from the agent 
    
    # Create a new Form Data instance (debugging)
    message_str = "What is your special skill"
    stream = task_classification_agent.run(
        message_str, 
        stream=True,        
    )

    # Stream Text Response 
    if protocol == 'text': 
        print("Text protocol")
    
    # Stream Data Response 
    elif protocol == 'data': 
        print("Data protocol") 

    for chunk in stream: 
            content = chunk.content
            if content: 
                yield "0:{text}\n".format(text=json.dumps(content))
 
@app.post("/agno/api/chat") 
async def handle_chat_data(request: Request): 
    messages = request.messages 

    # Convert the messages to be handled by the agno agents
    agno_message = convert_to_agno_message(messages) 

    response = StreamingResponse(stream_response(agno_message))  
    response.headers['x-vercel-ai-data-stream'] = 'v1' 
    return response 




