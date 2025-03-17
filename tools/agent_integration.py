import os
import json
from polygon_form_filler import PolygonFormFiller

class FormFillingAgent:
    """
    Integration class that connects the AI agent with the polygon-based form filling system.
    This class handles the conversion of AI agent outputs to the format expected by the form filler.
    """
    
    def __init__(self, knowledge_base_path="knowledge_base.json", font_path=None, debug=False):
        """
        Initialize the agent integration.
        
        Args:
            knowledge_base_path: Path to the knowledge base JSON file
            font_path: Path to the font file to use for form filling
            debug: Whether to enable debug mode
        """
        self.knowledge_base_path = knowledge_base_path
        self.form_filler = PolygonFormFiller(
            default_font_path=font_path,
            debug=debug
        )
        self.knowledge_base = self._load_knowledge_base()
    
    def _load_knowledge_base(self):
        """Load the knowledge base from disk, or create a new one if it doesn't exist."""
        if os.path.exists(self.knowledge_base_path):
            try:
                with open(self.knowledge_base_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Error loading knowledge base, creating a new one")
                return self._create_empty_knowledge_base()
        else:
            return self._create_empty_knowledge_base()
    
    def _create_empty_knowledge_base(self):
        """Create an empty knowledge base structure."""
        return {
            "entities": {
                "primary_user": {
                    "personal": {},
                    "contact": {},
                    "financial": {},
                    "professional": {},
                    "medical": {},
                    "relationships": {},
                    "identification": {}
                },
                "related_entities": []
            },
            "documents": [],
            "audit_trail": [],
            "system_metadata": {
                "last_updated": None,
                "completeness_score": 0,
                "information_gaps": []
            }
        }
    
    def _save_knowledge_base(self):
        """Save the knowledge base to disk."""
        with open(self.knowledge_base_path, 'w') as f:
            json.dump(self.knowledge_base, f, indent=2)
    
    def add_document_to_knowledge_base(self, document_data, document_type, document_metadata=None):
        """
        Add extracted document data to the knowledge base.
        
        Args:
            document_data: The extracted information from the document
            document_type: Type of document (ID, tax form, etc.)
            document_metadata: Additional metadata about the document
            
        Returns:
            Success message
        """
        # Create document entry
        document_entry = {
            "type": document_type,
            "date": document_metadata.get("date") if document_metadata else None,
            "issuer": document_metadata.get("issuer") if document_metadata else None,
            "extracted_fields": document_data,
            "confidence_metrics": document_metadata.get("confidence_metrics") if document_metadata else {},
            "processing_metadata": document_metadata
        }
        
        # Add to documents list
        self.knowledge_base["documents"].append(document_entry)
        
        # Update primary user information
        primary_user = self.knowledge_base["entities"]["primary_user"]
        
        # Categorize and merge information
        for field_name, field_data in document_data.items():
            # Simple categorization logic - can be made more sophisticated
            category = self._categorize_field(field_name)
            
            # Add to appropriate category
            if category:
                primary_user[category][field_name] = {
                    "value": field_data.get("value") if isinstance(field_data, dict) else field_data,
                    "source": f"document_{len(self.knowledge_base['documents']) - 1}",
                    "confidence": field_data.get("confidence", 5) if isinstance(field_data, dict) else 5,
                    "timestamp": document_metadata.get("date") if document_metadata else None
                }
        
        # Update metadata
        self.knowledge_base["system_metadata"]["last_updated"] = document_metadata.get("date") if document_metadata else None
        
        # Save updated knowledge base
        self._save_knowledge_base()
        
        return f"Document added to knowledge base. Knowledge base now contains {len(self.knowledge_base['documents'])} documents."
    
    def _categorize_field(self, field_name):
        """
        Simple categorization of fields based on name.
        Can be made more sophisticated with ML-based approaches.
        """
        field_name_lower = field_name.lower()
        
        # Personal information
        if any(term in field_name_lower for term in ["name", "birth", "gender", "marital", "ssn", "social security"]):
            return "personal"
            
        # Contact information
        if any(term in field_name_lower for term in ["address", "phone", "email", "city", "state", "zip", "postal"]):
            return "contact"
            
        # Financial information
        if any(term in field_name_lower for term in ["income", "expense", "salary", "bank", "account", "tax", "investment"]):
            return "financial"
            
        # Professional information
        if any(term in field_name_lower for term in ["employer", "job", "occupation", "employment", "education", "degree"]):
            return "professional"
            
        # Medical information
        if any(term in field_name_lower for term in ["health", "insurance", "medical", "doctor", "condition", "medication"]):
            return "medical"
            
        # Identification
        if any(term in field_name_lower for term in ["passport", "license", "id", "identification"]):
            return "identification"
            
        # Default to personal if no match
        return "personal"
    
    def fill_form(self, form_image_path, agent_output, output_path=None):
        """
        Process the agent's output and fill the form.
        
        Args:
            form_image_path: Path to the form image to fill
            agent_output: The structured output from the AI agent
            output_path: Where to save the filled form
            
        Returns:
            Path to the filled form
        """
        # Process agent output to extract new_values
        new_values = self._process_agent_output(agent_output)
        
        # Fill the form
        return self.form_filler.edit_form(form_image_path, new_values, output_path)
    
    def _process_agent_output(self, agent_output):
        """
        Process the output from the AI agent to extract the values to be filled.
        Handles both the old coordinate-based format and the new polygon-based format.
        
        Args:
            agent_output: The structured output from the AI agent
            
        Returns:
            Processed new_values dictionary ready for the form filler
        """
        # If agent_output is already a dict with new_values, extract it
        if isinstance(agent_output, dict) and "new_values" in agent_output:
            agent_output = agent_output["new_values"]
        
        # If it's a string (JSON), parse it
        if isinstance(agent_output, str):
            try:
                agent_output = json.loads(agent_output)
                if "new_values" in agent_output:
                    agent_output = agent_output["new_values"]
            except json.JSONDecodeError:
                raise ValueError("Agent output is not valid JSON")
        
        processed_values = {}
        
        # Process each field
        for field_name, field_data in agent_output.items():
            # Handle different formats
            if isinstance(field_data, dict):
                # Check if this is in the new polygon-based format
                if "polygon" in field_data or "identification" in field_data:
                    # New format handling
                    if "identification" in field_data:
                        # Extract from complex nested structure
                        new_entry = {
                            "new_value": field_data.get("value", {}).get("formatted_value", 
                                        field_data.get("value", {}).get("raw_value", "")),
                        }
                        
                        # Get polygon from positioning if available
                        if "positioning" in field_data and "boundary_polygon" in field_data["positioning"]:
                            new_entry["polygon"] = field_data["positioning"]["boundary_polygon"]
                        elif "positioning" in field_data and "primary_coordinates" in field_data["positioning"]:
                            # Fall back to coordinates if polygon not available
                            coords = field_data["positioning"]["primary_coordinates"]
                            new_entry["position"] = coords
                        
                        processed_values[field_name] = new_entry
                    else:
                        # Simpler nested structure
                        processed_values[field_name] = {
                            "polygon": field_data.get("polygon", []),
                            "new_value": field_data.get("new_value", "")
                        }
                else:
                    # Old coordinate-based format
                    processed_values[field_name] = {
                        "position": field_data.get("position", [0, 0]),
                        "new_value": field_data.get("new_value", "")
                    }
            else:
                # Direct value assignment - not recommended but handled for completeness
                processed_values[field_name] = {
                    "position": [0, 0],  # Default position
                    "new_value": str(field_data)
                }
        
        return processed_values
    
    def get_knowledge_for_field(self, field_name, field_context=None):
        """
        Look up information in the knowledge base for a specific field.
        
        Args:
            field_name: The name of the field to look up
            field_context: Additional context about the field (section, type, etc.)
            
        Returns:
            The value if found, None otherwise
        """
        # First try exact match in all categories
        primary_user = self.knowledge_base["entities"]["primary_user"]
        for category, fields in primary_user.items():
            if field_name in fields:
                return fields[field_name].get("value", None)
        
        # If not found, try fuzzy matching based on field name
        field_name_lower = field_name.lower()
        best_match = None
        best_match_score = 0
        
        for category, fields in primary_user.items():
            for existing_field, data in fields.items():
                # Simple matching score based on word overlap
                existing_lower = existing_field.lower()
                words1 = set(field_name_lower.split())
                words2 = set(existing_lower.split())
                common_words = words1.intersection(words2)
                
                if common_words:
                    score = len(common_words) / max(len(words1), len(words2))
                    if score > best_match_score and score > 0.3:  # Threshold for match
                        best_match = data.get("value", None)
                        best_match_score = score
        
        return best_match

# Example usage
if __name__ == "__main__":
    # Sample usage
    agent = FormFillingAgent(debug=True)
    
    # Example of adding a document to the knowledge base
    sample_document_data = {
        "Full Name": "John Smith",
        "Date of Birth": "01/15/1980",
        "Social Security Number": "123-45-6789",
        "Address": "123 Main St, Anytown, CA 12345",
        "Phone Number": "(555) 123-4567",
        "Email": "john.smith@example.com",
        "Annual Income": "$75,000"
    }
    
    agent.add_document_to_knowledge_base(sample_document_data, "ID Document")

     # Example of agent output for form filling
    agent_output = {
        "Full Name": {
            "polygon": [[100, 100], [300, 100], [300, 130], [100, 130]],
            "new_value": "John Smith"
        },
        "Phone Number": {
            "polygon": [[100, 150], [300, 150], [300, 180], [100, 180]],
            "new_value": "(555) 123-4567"
        }
    }
    
    # Fill a form (this would be an actual form image path)
    # agent.fill_form("path/to/empty_form.jpg", agent_output, "path/to/filled_form.jpg")

