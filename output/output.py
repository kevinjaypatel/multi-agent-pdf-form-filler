from pydantic import BaseModel, Field 
from datetime import datetime

class DocumentMetadata(BaseModel): 
    source_document_type: str = Field(description="The type of document the user uploads")
    extracted_at: datetime = Field(description="The timestamp when the information was extracted")

class UserExtractedInfo(BaseModel): 
    id: int 
    source_document_type: str = Field(description="The type of document the user uploads")
    extracted_at: datetime = Field(description="The timestamp when the information was extracted")
    first_name: str = Field(description="The first name of the user")
    middle_name: str = Field(description="The middle name of the user")
    last_name: str = Field(description="The last name of the user")
    email: str = Field(description="The email of the user")
    phone_number: str = Field(description="The phone number of the user")
    address: str = Field(description="The address of the user")
    city: str = Field(description="The city of the user")
    state: str = Field(description="The state of the user")
    zip_code: str = Field(description="The zip code of the user")
    social_security_number: str = Field(description="The social security number of the user") 

class UserProfileDocument(BaseModel): 
    metadata: DocumentMetadata
    extracted_info: UserExtractedInfo 

