from fastapi import FastAPI, Request 
from fastapi.responses import StreamingResponse 
from fastapi.middleware.cors import CORSMiddleware
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from pydantic import BaseModel 
from typing import Dict, Optional, Any 
import json 
# Extract Agent 
from agents.extract_agent import extraction_agent 

# Vercel AI SDK  
# from ai import StreamingResponse as VercelStreamingResponse 

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

class ChatRequest(BaseModel): 
    message: str 
    conversation_id: Optional[str] = None 
    metadata: Optional[Dict[str, Any]] = None 

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    description="You are a helpful assistant.",
    markdown=True,

)

async def generate_stream(message, conversation_id=None, metadata=None): 
    """Generate a stream of responses from the agent."""
    response_stream = extraction_agent.run(
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

@app.get("/ask")
async def ask(query: str):
    response = extraction_agent.run(query)
    return {"response": response.content}


@app.post("/agno/api/chat")
async def chat_with_agent(request: Request): 
    body = await request.json() 
    print(f"Received body: {body}") 

    message = body.get('message') 
    # message = messages[-1]['content'] if messages else "" 
    
    conversation_id = body.get("conversation_id") or body.get("id")
    metadata = body.get("metadata") 

    print(f"Received message: {message}")
    return StreamingResponse(
        # generate_stream(message, conversation_id, metadata),
        generate_stream(message),  
        media_type="text/event-stream"
    )