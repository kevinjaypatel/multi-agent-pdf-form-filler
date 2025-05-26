import base64 

from pydantic import BaseModel 
from typing import List, Optional 
from .types import ClientMessage, AgnoMessage


from agno.media import Image 

def convert_to_agno_message(messages: List[ClientMessage]) -> List[AgnoMessage]: 
    agno_messages = [] 
    print("Messages: ", messages) 

    for message in messages: 
        parts = [] 
        parts.append({
            'type': 'text', 
            'text': message.content
        })

        if message.experimental_attachments: 
            for attachment in message.experimental_attachments: 
                print("Attachment: ", attachment) 
                try:
                    if attachment.contentType.startswith('image'): 
                        # Handle base64 encoded image
                        if attachment.url.startswith('data:image'):
                            # Extract the base64 part after the comma
                            base64_data = attachment.url.split(',')[1]
                            image_bytes = base64.b64decode(base64_data)
                            
                            parts.append({
                                'type': 'image', 
                                'image': image_bytes
                            })
                    
                    elif attachment.contentType.startswith('application/pdf'): 
                        if attachment.url.startswith('data:application/pdf'): 
                            base64_data = attachment.url.split(",")[1]
                            pdf_bytes = base64.b64decode(base64_data)
                            parts.append({
                                'type': 'document', 
                                'document': pdf_bytes 
                            })
                except Exception as e:
                    print(f"Error processing attachment: {e}")
                    continue
        
        agno_messages.append(AgnoMessage(
            role=message.role, 
            content=parts
        ))
    
    return agno_messages 