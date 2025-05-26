from pydantic import BaseModel 
from typing import Optional, List, Dict, Any 

class ClientAttachment(BaseModel): 
    name: str
    contentType: str 
    url: str 

class ToolInvocation(BaseModel): 
    toolCallId: str 
    toolName: str 
    args: dict 
    result: dict 

class ClientMessage(BaseModel): 
    role: str 
    content: str 
    experimental_attachments: Optional[List[ClientAttachment]] = None 
    toolInvocations: Optional[List[ToolInvocation]] = None 

class AgnoMessage(BaseModel): 
    role: str 
    content: List[Dict[str, Any]] 
 