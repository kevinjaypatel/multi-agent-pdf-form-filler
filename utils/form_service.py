from typing import Dict
from agno.media import File as AgnoUploadFile
from agents.extract_agent import document_search_team
from agents.tools.edit_form import edit_form
import json
import re
import logging

# Configure logging
logger = logging.getLogger(__name__)

class FormFillingService:
    def __init__(self):
        self.document_search_team = document_search_team
        logger.info("FormFillingService initialized")

    async def process_form(self, message: str, file_content: bytes) -> dict:
        """
        Process a form by searching for information and filling it out.
        
        Args:
            message: The search query message
            file_content: The PDF file content as bytes
            
        Returns:
            dict: Response containing the filled PDF as base64
        """
        try:
            logger.info("Starting form processing")
            logger.debug(f"Message length: {len(message)}, File size: {len(file_content)} bytes")
            
            # Step 1: Search for form information
            logger.info("Searching for form information")
            search_result = await self._search_form_info(message, file_content)
            logger.debug(f"Search result length: {len(search_result)}")
            
            # Step 2: Parse search results
            logger.info("Parsing search results")
            query_results = self._parse_search_results(search_result)
            logger.debug(f"Parsed {len(query_results)} fields from search results")
            
            # Step 3: Fill out the form
            logger.info("Filling out form with parsed results")
            filled_pdf = await self._fill_form(file_content, query_results)
            logger.info("Form filling completed successfully")
            
            return {
                "data": filled_pdf,
                "mimeType": "application/pdf"
            }
            
        except ValueError as ve:
            logger.error(f"Form processing error: {str(ve)}")
            raise ValueError(f"Form processing error: {str(ve)}")
        except Exception as e:
            logger.error(f"Unexpected error during form processing: {str(e)}", exc_info=True)
            raise Exception(f"Unexpected error during form processing: {str(e)}")

    async def _search_form_info(self, message: str, file_content: bytes) -> str:
        """
        Search for form information using the document search team.
        
        Args:
            message: The search query message
            file_content: The PDF file content as bytes
            
        Returns:
            str: The search results
        """
        if not file_content:
            logger.error("No PDF file content provided")
            raise ValueError("No PDF file content provided")
            
        logger.debug("Running document search team")
        run_result = self.document_search_team.run(
            message,
            files=[AgnoUploadFile(content=file_content)],
        )
        logger.debug("Document search completed")
        return run_result.content

    def _parse_search_results(self, search_results: str) -> dict:
        """
        Parse the search results into a dictionary.
        
        Args:
            search_results: The raw search results string
            
        Returns:
            dict: The parsed query results
        """
        try:
            logger.debug("Parsing search results")
            dict_pattern = r'```python\s*({[\s\S]*?})\s*```'
            dict_match = re.search(dict_pattern, search_results)
            if not dict_match:
                logger.error("No dictionary found in search results")
                raise ValueError("No dictionary of search results found in the response")

            dict_str = dict_match.group(1)
            dict_str = dict_str.replace("'", '"')
            result = json.loads(dict_str)
            logger.debug(f"Successfully parsed {len(result)} fields")
            return result
            
        except ValueError as e:
            logger.error(f"Failed to parse search results: {str(e)}")
            raise ValueError(f"Failed to parse search results: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            raise ValueError(f"Invalid JSON in search results: {str(e)}")

    async def _fill_form(self, file_content: bytes, query_results: dict) -> str:
        """
        Fill out the form with the query results.
        
        Args:
            file_content: The PDF file content as bytes
            query_results: Dictionary of field names to values
            
        Returns:
            str: Base64 encoded string of the filled PDF
        """
        try:
            logger.debug(f"Filling form with {len(query_results)} fields")
            result = await edit_form(file_content, query_results)
            logger.debug("Form filled successfully")
            return result
        except Exception as e:
            logger.error(f"Failed to fill form: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to fill form: {str(e)}") 