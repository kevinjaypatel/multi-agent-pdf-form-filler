from agno.agent import Agent  
from agno.models.openai import OpenAIChat 
from agno.knowledge.pdf import PDFKnowledgeBase 
from tools.extract_pdf_tool import get_extracted_information  
from knowledge.combined_knowledge import knowledge_base 


agent = Agent(
    name="Extract Agent", 
    agent_id="extract-agent",
    model=OpenAIChat(id="gpt-4o"),
    description="You are an expert in extracting missing information from PDF documents",
    task="Determine the missing information from a PDF document",
    instructions=[
        "You are given a PDF document", 
        "Your job is to find the missing information from the PDF document",
        "Use the get_extracted_information tool to gather a dictionary of the missing information from the document",
        "If you are unsure about something, just say you don't know rather than making assumptions", 
    ], 
    # Use markdown to format your answers
    markdown=True,                  
    debug_mode=True, 
    show_tool_calls=True,
    tools=[get_extracted_information],
    knowledge_base=knowledge_base, 
    expected_output="A dictionary mapping all the missing information from the PDF document to the correct field in the form",
    prevent_hallucinations=True, 
)