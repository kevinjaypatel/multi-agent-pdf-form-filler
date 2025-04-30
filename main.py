from fastapi import FastAPI, Request 
from fastapi.responses import StreamingResponse 
from fastapi.middleware.cors import CORSMiddleware
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from pydantic import BaseModel 
from typing import Dict, Optional, Any, List 
import json 
# Extract Agent 
# from agents.extract_agent import extraction_agent 
from agents.extract_agent import document_upload_agent
import os
import httpx
from PIL import Image

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

async def download_image(url: str, save_dir: str = "agents/images") -> str:
    """Download an image from a URL and save it to a local file."""
    # Create directory if it doesn't exist
    os.makedirs(save_dir, exist_ok=True)
    
    # Generate a filename from the URL
    filename = url.split("/")[-1]
    filepath = os.path.join(save_dir, filename)
    
    # Download the image
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(response.content)
            return filepath
        else:
            print(f"Failed to download image from {url}: {response.status_code}")
            return None

async def extract_image_urls(body: dict) -> List[str]:
    """Extract image URLs from the request body."""
    image_urls = []
    
    # Check if coreMessages exists in the body
    if "coreMessages" in body:
        for message in body["coreMessages"]:
            if "content" in message and isinstance(message["content"], list):
                for content_item in message["content"]:
                    if content_item.get("type") == "image" and "image" in content_item:
                        image_urls.append(content_item["image"])
    
    return image_urls

async def generate_stream(message, conversation_id=None, metadata=None, image_paths=None): 
    """Generate a stream of responses from the agent."""
    # If we have image paths, prepare them for the vision model
    image_contents = []
    if image_paths:
        if metadata is None:
            metadata = {}
        metadata["image_paths"] = image_paths
        
        # Load images as base64 for the vision model
        for path in image_paths:
            try:
                with open(path, "rb") as img_file:
                    import base64
                    image_data = base64.b64encode(img_file.read()).decode('utf-8')
                    image_contents.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}"
                        }
                    })
            except Exception as e:
                print(f"Error loading image {path}: {e}")
    
    # Create a message that includes the original text and images
    messages = [
        {"role": "system", "content": "You are a helpful assistant that can analyze images and extract information for user profiles."},
        {"role": "user", "content": [{"type": "text", "text": message}] + image_contents}
    ]
    
    print(f"Sending message with {len(image_contents)} images to OpenAI...")
    
    # Use OpenAI's chat completion API directly for vision capabilities
    from openai import OpenAI
    client = OpenAI()
    
    # Stream the response
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        stream=True
    )
    
    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            yield f"data: {json.dumps({'content': content})}\n\n"
    
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
    conversation_id = body.get("conversation_id") or body.get("id")
    metadata = body.get("metadata", {})

    # Extract image URLs from the request body
    image_urls = await extract_image_urls(body)
    image_paths = []
    
    # Download images if there are any
    if image_urls:
        print(f"Found {len(image_urls)} images to download")
        for url in image_urls:
            try:
                image_path = await download_image(url)
                if image_path:
                    image_paths.append(image_path)
                    print(f"Downloaded image to {image_path}")
                    
                    # Verify the image exists and is readable
                    if os.path.exists(image_path):
                        try:
                            with Image.open(image_path) as img:
                                width, height = img.size
                                print(f"Image dimensions: {width}x{height}")
                        except Exception as e:
                            print(f"Warning: Downloaded image exists but cannot be opened: {e}")
                    else:
                        print(f"Warning: Downloaded image path doesn't exist: {image_path}")
            except Exception as e:
                print(f"Error downloading image from {url}: {e}")
    
    print(f"Received message: {message}")
    print(f"Processing with {len(image_paths)} images: {image_paths}")
    
    # Add image information to metadata
    if image_paths:
        metadata["has_images"] = True
        metadata["image_count"] = len(image_paths)
    
    return StreamingResponse(
        generate_stream(message, conversation_id, metadata, image_paths),  
        media_type="text/event-stream"
    )