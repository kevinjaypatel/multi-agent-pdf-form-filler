import json 
import httpx 

def get_extracted_information(pdf_url: str) -> dict: 
    """
    Call the PDF api for getting a dictionary of the extracted information from the PDF document 
    """