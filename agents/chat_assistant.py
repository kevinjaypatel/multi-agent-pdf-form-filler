from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.workflow.workflow import Workflow
from agno.utils.pprint import pprint_run_response

from textwrap import dedent
from typing import List, Optional

# Team of Agents 
from extract_agent import document_upload_agent, document_search_agent

# Storage 
# from extract_agent import storage

class ChatAssistantWorkflow(Workflow):
    """
    A workflow that coordinates a chat assistant with specialized agents.
    The chat assistant acts as the main interface and delegates tasks to other agents.
    """
    
    # Main chat assistant agent
    chat_assistant: Agent = Agent(
        name="HyperDocs.ai Chat Assistant",
        model=OpenAIChat(id="gpt-4o"),
        description="You are a helpful assistant that coordinates between different specialized agents for HyperDocs.ai",
        instructions=dedent("""\
            You are the main interface for users and coordinate between different specialized agents for HyperDocs.ai
                            
            HyperDocs.ai is a platform and service that enables users and developers to quickly fill out PDF forms 
            
            Your responsibilities:
            1. Understand user requests and determine which specialized agent can help
            2. Delegate tasks to the appropriate agent
            3. Collect and present responses from specialized agents
            4. Maintain context and conversation flow
            
            Available specialized agents:
            - Document Upload Agent: Handles document uploads and processing
            - Document Search Agent: Searches through uploaded documents to fill documents with missing information 
            
            When delegating tasks:
            1. Clearly explain the task to the specialized agent
            2. Specify the expected output format
            3. Provide any necessary context or additional information
            4. Collect and format the response for the user
        """),
        team=[],  # Will be populated with specialized agents
        read_chat_history=True,
        show_tool_calls=True,
        debug_mode=True,
        # storage=storage,
    )

    def __init__(self, specialized_agents: List[Agent]):
        """
        Initialize the workflow with specialized agents.
        
        Args:
            specialized_agents: List of specialized agents to coordinate
        """
        super().__init__()
        self.chat_assistant.team = specialized_agents

    def run_workflow(self, user_input: str) -> str:
        """
        Process user input through the chat assistant workflow.
        
        Args:
            user_input: The user's input message
            
        Returns:
            str: The response from the chat assistant
        """
        response = self.chat_assistant.run(user_input)
        return response.content
    

if __name__ == "__main__": 

    specialized_agents = [
        document_upload_agent, 
        document_search_agent
    ]

    workflow = ChatAssistantWorkflow(specialized_agents)

    user_input = "What are your special skills?" 
    response = workflow.run_workflow(user_input) 
    
    pprint_run_response(response, markdown=True)

