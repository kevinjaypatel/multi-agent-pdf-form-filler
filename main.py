# FastAPI
from fastapi import FastAPI, UploadFile, Form  
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
import base64
import logging

# Extract Agent 
from agents.extract_agent import task_classification_agent, document_upload_agent, document_search_team

# Tools 
from agents.tools.edit_form import edit_form 

from utils.prompt import convert_to_agno_message
from utils.types import ClientMessage, AgnoMessage
from utils.form_service import FormFillingService

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

# Initialize the service
form_filling_service = FormFillingService()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel): 
    message: str 
    conversation_id: Optional[str] = None 
    metadata: Optional[Dict[str, Any]] = None 

class Request(BaseModel): 
    messages: List[ClientMessage]
                    
def parse_message_content(message: List[AgnoMessage]) -> tuple[str, list[Image], list[AgnoUploadFile]]:
    """
    Parse the message content to extract text, images, and files.
    
    Args:
        message: List of AgnoMessage objects
        
    Returns:
        tuple containing:
        - message_str: The text content of the message
        - images: List of Image objects
        - files: List of AgnoUploadFile objects
    """
    last_message = message[-1]
    message_str = ""
    images = []
    files = []
    
    for part in last_message.content:
        if part['type'] == 'text':
            message_str += part['text']
        elif part['type'] == 'image':
            images.append(Image(content=part['image']))
        elif part['type'] == 'document':
            files.append(AgnoUploadFile(content=part['document']))
            
    return message_str, images, files

async def stream_response(message: List[AgnoMessage], protocol: str = 'data'): 
    try:
        logger.info("Starting stream response processing")
        
        # Parse message content
        message_str, images, files = parse_message_content(message)
        logger.info(f"Parsed message content - Text length: {len(message_str)}, Images: {len(images)}, Files: {len(files)}")
        
        # If no files or images, just stream the task classification response
        if not files and not images:
            logger.info("No files or images found, using task classification agent")
            run_response: Iterator[RunResponse] = task_classification_agent.run(
                message_str,
                stream=True,
            )
            for chunk in run_response:
                if chunk.content:
                    yield "0:{text}\n".format(text=json.dumps(chunk.content))
            return

        # Determine which agent will handle the task
        logger.info("Determining agent type for task")
        run_response: RunResponse = task_classification_agent.run(
            message_str,
        )
        logger.info(f"Run response: {run_response}")
        
        # Get the first response to determine which agent to use
        agent_type = run_response.content
        if not agent_type:
            logger.warning("No agent type determined, defaulting to general chat")
        logger.info(f"Selected agent type: {agent_type}")

        # Handle document search case
        if agent_type == DOCUMENT_SEARCH_AGENT:
            if not files:
                logger.error(f"No PDF file provided for {DOCUMENT_SEARCH_AGENT}")
                raise ValueError(f"No PDF file provided for {DOCUMENT_SEARCH_AGENT}")
            
            logger.info("Processing form with document search agent")
            result = await form_filling_service.process_form(message_str, files[0].content)
            logger.info("Form processing completed successfully")
            logger.info(f"Result: {result}")
            yield "k:{file_part}\n".format(file_part=json.dumps(result))

        # Handle document upload case
        elif agent_type == DOCUMENT_UPLOAD_AGENT or agent_type == 'Upload Agent':
            if not images:
                logger.error(f"No image file provided for {DOCUMENT_UPLOAD_AGENT}")
                raise ValueError(f"No image file provided for {DOCUMENT_UPLOAD_AGENT}")
            
            logger.info("Processing with document upload agent")
            run_result: Iterator[RunResponse] = document_upload_agent.run(
                message_str,
                images=images,
                stream=True
            )
            
            for chunk in run_result:
                if chunk.content:
                    yield "0:{text}\n".format(text=json.dumps(chunk.content))

        # Handle general chat case
        else:
            logger.info("Using general chat response")
            for chunk in run_response:
                if chunk.content:
                    yield "0:{text}\n".format(text=json.dumps(chunk.content))

    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        yield "0:{text}\n".format(text=json.dumps({
            "error": f"Validation error: {str(ve)}",
            "status": "ERROR"
        }))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        yield "0:{text}\n".format(text=json.dumps({
            "error": f"Error processing request: {str(e)}",
            "status": "ERROR"
        }))

@app.post("/agno/api/chat") 
async def handle_chat_data(request: Request): 
    messages = request.messages 

    # Convert the messages to be handled by the agno agents
    agno_message = convert_to_agno_message(messages) 

    response = StreamingResponse(stream_response(agno_message))  
    response.headers['x-vercel-ai-data-stream'] = 'v1' 
    return response 




