import os 
import numpy as np 
import json
import re

from typing import Dict
from textwrap import dedent
from pathlib import Path 

from pypdf import PdfReader, PdfWriter 
from pypdf.constants import AnnotationDictionaryAttributes

from agno.agent import Agent  
from agno.models.openai import OpenAIChat

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


image_path = "input/data/image/w2_unfilled.jpg" 
# pdf_path = "agents/tools/input/data/pdf/fw2/fw2-pages-3.pdf"
# output_path = "agents/tools/output/pypdf"

output_path = "tools/output/pypdf"
pdf_path = "tools/input/data/pdf/fw2/fw2-pages-3.pdf"

# Mapping Agent as Tool 
mapping_agent = Agent(
    name="Document Mapping Agent", 
    description="You are an expert in mapping pdf field names to form values", 
    session_id="mapping_agent_session",
    model=OpenAIChat(
        id='gpt-4o',
        temperature=0.0  # Add temperature parameter (0.0 to 1.0)
    ), 
    instructions=dedent("""\
        You will receive the following inputs:
        - "pdf_field_names": An array of field objects parsed from an empty or partially filled form document 
        - "form_values": field names and values that need to be mapped to the pdf_field_names
        - "document_type": Indicates what type of document form is being processed (e.g., "W2 form, 1040 form, etc")
        
        1. Your task is to create a JSON object that correctly maps the field names from the pdf field names array to the values from the form_values object  
                        
        2. IMPORTANT: The field names in the JSON object that you create should be the EXACT key items from the field_objects array, not simplified or renamed versions.
        
        3. The final JSON object should contain as many key value pairs as there are values in the form_values object. In other words, 
        the size or number of key value pairs in the JSON object should be equal to the number of values provided in the form_values object 
                                       
        4. Compare both the pdf form names and form values, and determine which value from the form values list 
        should be mapped to the pdf field name from the pdf field names array, and vice versa.   
                        
        5. The core strucure of a field object can look like this: 
                        
        {
            "mapping_name": {
                "/T": "The partial name of the field", 
                "/FT": "The field type (Button, Text, Choice, or Signature)", 
                "/V": "The field's value, whose format varies depending on the field type."
            }                
        }

        6. IMPORTANT: Here is an example of the mapping output for a filled 2025 W2 Form. Pay attention to the field names, and example values that are assigned to them. 
        Only use this as reference for when you are filling out W2 forms. Do not use these same values to create the JSON mapping output.   
        {
            Field: f2_01[0]
            Value Definition: "Box A: Employee's Social Security Number"
            Example Value: "111-11-1111"
            --------------------------------------------------
            Field: f2_02[0]
            Value Definition: "Box B: Employer's Identification Number"
            Example Value: "38-0226974"
            --------------------------------------------------
            Field: f2_03[0]
            Value Definition: "Box C: Employer's Name, address, and ZIP code"
            Example Value: "West and Sons Inc 0324 Morgan Brook Port Shanstad KY 78445-9845"
            --------------------------------------------------
            Field: f2_04[0]
            Value Definition: "Box D: Control Number"
            Example Value: "5777864"
            --------------------------------------------------
            Field: f2_05[0]
            Value Definition: "Box E: Employee's first name and initial" 
            Example Value: "Diana"
            --------------------------------------------------
            Field: f2_06[0]
            Value Definition: "Employee's last name" 
            Example Value: "Reyes"
            --------------------------------------------------
            Field: f2_07[0]
            Value Definition: "Suffix"
            --------------------------------------------------
            Field: f2_08[0]
            Value Definition: "Box F: Employee's address and ZIP code"
            Example Value: "094 Harris Prairie, Susanville, ME 60154-1359"
            --------------------------------------------------
            Field: f2_09[0]
            Value Definition: "Box 1: Wages, tips, other compensation"
            Example Value: "126589.34"
            --------------------------------------------------
            Field: f2_10[0]
            Value Definition: "Box 2: Federal income tax withheld"
            Example Value: "43873.99"
            --------------------------------------------------
            Field: f2_11[0]
            Value Definition: "Box 3: Social security wages"
            Example Value: "122867.85"
            --------------------------------------------------
            Field: f2_12[0]
            Value Definition: "Box 4: Social security tax withheld" 
            Example Value: "9399.39"
            --------------------------------------------------
            Field: f2_13[0]
            Value Definition: "Box 5: Medicare wages and tips"
            Example Value: "114182.15"
            --------------------------------------------------
            Field: f2_14[0]
            Value Definition: "Box 6: Medicare tax withheld"
            Example Value: "3311.28"
            --------------------------------------------------
            Field: f2_15[0]
            Value Definition: "Box 7: Social security tips"
            Example Value: "122867.85"
            --------------------------------------------------
            Field: f2_16[0]
            Value Definition: "Box 8: Allocated tips" 
            Example Value: "114182.15"
            --------------------------------------------------
            Field: f2_17[0]
            Value Definition: "Box 9"
            Example Value: ""
            --------------------------------------------------
            Field: f2_18[0]
            Value Definition: "Box 10: Dependent care benefits" 
            Example Value: "219"
            --------------------------------------------------
            Field: f2_19[0]
            Value Definition: "Box 11: Nonqualified plans"
            Example Value: "158"
            --------------------------------------------------
            Field: f2_20[0]
            Value Definition: "Box 12a: value one"
            Example Value: "E"
            --------------------------------------------------
            Field: f2_21[0]
            Value Definition: "Box 12a: value two"
            Example Value: "9090"
            --------------------------------------------------
            Field: f2_22[0]
            Value Definition: "Box 12b: value one"
            Example Value: ""
            --------------------------------------------------
            Field: f2_23[0]
            Value Definition: "Box 12b: value two"
            Example Value: "459"
            --------------------------------------------------
            Field: f2_24[0]
            Value Definition: "Box 12c: value one"
            Example Value: "D"
            --------------------------------------------------
            Field: f2_25[0]
            Value Definition: "Box 12c: value two"
            Example Value: "275"
            --------------------------------------------------
            Field: f2_26[0]
            Value Definition: "Box 12d: value one"
            Example Value: "E"
            --------------------------------------------------
            Field: f2_27[0]
            Value Definition: "Box 12d: value two"
            Example Value: "688"
            --------------------------------------------------
            Field: topmostSubform[0].Copy1[0].Col_Right[0].Statutory_ReadOrder[0].c2_2[0]
            Value Definition: "Checked Box"
            Example Value: "/1"
            --------------------------------------------------
            Field: topmostSubform[0].Copy1[0].Col_Right[0].Retirement_ReadOrder[0].c2_3[0]
            Value: /Off
            --------------------------------------------------
            Field: topmostSubform[0].Copy1[0].Col_Right[0].c2_4[0]
            Value: /1
            --------------------------------------------------
            Field: topmostSubform[0].Copy1[0].Col_Right[0].f2_28[0]
            Value Definition: 
            Example Value: 
            --------------------------------------------------
            Field: f2_29[0]
            Value Definition: "State"
            Example Value: "HI" 
            --------------------------------------------------
            Field: f2_30[0]
            Value Definition: "Employer's state ID number"
            Example Value: "457 - 24 - 914"
            --------------------------------------------------
            Field: f2_31[0]
            Value Definition: "State"
            Example Value: "WI" 
            --------------------------------------------------
            Field: f2_32[0]
            Value Definition: "Employer's state ID number"
            Example Value: "386 - 31 - 922"
            --------------------------------------------------
            Field: f2_33[0]
            Value Definition: "State wages, tips, etc"
            Example Value: "68442.97"
            --------------------------------------------------
            Field: f2_34[0]
            Value Definition: "State wages, tips, etc"
            Example Value: 66147.7
            --------------------------------------------------
            Field: f2_35[0]
            Value Definition: "State income tax"             
            Example Value: 4761.03
            --------------------------------------------------
            Field: f2_36[0]
            Value Definition: "State income tax" 
            Example Value: 6996.33
            --------------------------------------------------
            Field: f2_37[0]
            Value Definition: Local wages, tips, etc 
            Example Value: 101209.95
            --------------------------------------------------
            Field: f2_38[0]
            Value Definition: Local wages, tips, etc
            Example Value: 125139.92
            --------------------------------------------------
            Field: f2_39[0]
            Value Definition: Local income tax 
            Example Value: 14120.87
            --------------------------------------------------
            Field: f2_40[0]
            Value Definition: Local income tax 
            Example Value: 23035.86
            --------------------------------------------------
            Field: f2_41[0]
            Value Definition: Locality name 
            Example Value: Cynthia
            --------------------------------------------------
            Field: f2_42[0]
            Value Definition: Locality name 
            Example Value: William 
        }

        7. IMPORTANT: You have to determine the mapping name for each field value. Do not hallucinate or make up values.  
        8. Make sure not to include comments in the JSON body. 
          
    """),
    tools=[], 
    # storage=storage,
    debug_mode=True,  # Add this to see detailed logs
)

def edit_form(new_values: Dict[str, str]) -> str:
    """
    Fill out a PDF form with the provided values.
    
    Args:
        new_values: A dictionary mapping field names to their values
        pdf_path: Optional path to the PDF file (uses default if not provided)
        
    Returns:
        str: Path to the filled out PDF
    """
        
    try:

        # Get absolute path to ensure we're looking in the right place
        abs_pdf_path = os.path.abspath(pdf_path)

        # print(f"Current working directory: {os.getcwd()}")
        # print(f"Attempting to open PDF at: {abs_pdf_path}")

        reader = PdfReader(abs_pdf_path) 
        if (reader is not None): 
            # Reads the form fields  
            print("Getting form mappings...")
            mappings = get_form_mappings(new_values) 
            print("Mappings received:", mappings is not None)
            
            if (mappings): 
                # Convert mappings to lists
                field_names = list(mappings.keys())
                field_values = list(mappings.values())
                
                # Write to the PDF form document  
                writer = PdfWriter() 
                writer.append(reader) 

                # Update form fields
                for i, field_name in enumerate(field_names):
                    writer.update_page_form_field_values(
                        writer.pages[0], 
                        {field_name: field_values[i]}, 
                        auto_regenerate=False,
                    )

                # output_dir = 'output/pypdf'
                os.makedirs(output_path, exist_ok=True)
                
                new_file_count = len(list(Path(output_path).glob('*.pdf'))) + 1
                new_file_name = f'filled-out-{new_file_count}.pdf'
                
                # print("New File Count: " + str(new_file_count))
                # print("New File Name: " + new_file_name)

                full_output_path = os.path.join(output_path, new_file_name)

                with open(full_output_path, "wb") as output_stream: 
                    writer.write(output_stream) 

                return f'The form has been filled out and saved to {full_output_path}'

            else: 
                return "No mappings were found"

        else: 
            return "No PDF file found"
        
    except Exception as e:
        return f"Error processing PDF: {str(e)}"

# Call the mapping agent to get the mapped output
def get_form_mappings(query_results: Dict[str, str]):
     
    field_objects = get_form_fields() 
        
     # Run agent and return the response as a variable
    response: RunResponse = mapping_agent.run(
        f"""
        I need to map form values to form fields.
        
        PDF Field Names: {json.dumps(field_objects)}
        Document metadata: 
        - Document type: W2 form 2025

        Form values: {json.dumps(query_results)}
        
        Please provide the mapping between these values and fields.
        """
    )

    response_content = response.content 

    # Extract just the JSON part using regex
    json_match = re.search(r'```json\s*({[\s\S]*?})\s*```', response_content)
    if json_match:
        json_str = json_match.group(1)
        response_dict = json.loads(json_str)
        return response_dict 
    else:
        return None 

def read_form_fields(pdf_path: str=pdf_path): 
    reader = PdfReader(pdf_path)
    fields = reader.get_fields()
    
    if not fields:
        return "No form fields found in the PDF."
    
    formatted_output = "PDF Form Fields:\n\n"
    
    for field_name, field_data in fields.items():
        # Extract the field value
        field_value = field_data.get('/V', '')
        
        # Format the output
        formatted_output += f"Field: {field_name}\n"
        formatted_output += f"Value: {field_value}\n"
        formatted_output += "-" * 50 + "\n"

    print(formatted_output)
    
def get_form_fields(): 
    reader = PdfReader(pdf_path)   
    fields = reader.get_form_text_fields() 

    return fields
     

def get_generic_form_data(): 
    reader = PdfReader(pdf_path)   
    fields = []
    for page in reader.pages:
        for annot in page.annotations:
            annot = annot.get_object()
            if annot[AnnotationDictionaryAttributes.Subtype] == "/Widget":
                fields.append(annot)
    
    return fields

def get_missing_fields(): 
    fields = get_form_fields()  
    
    missing_fields = []
    for field in fields: 
        if field == None: 
            missing_fields.append(field) 
    
    print("Missing Field: ", missing_fields)


if __name__ == "__main__":  
    # read_form_fields(pdf_path)

    form_field_mappings = {
      "topmostSubform[0].Copy1[0].BoxA_ReadOrder[0].f2_01[0]": "053-93-7915",
      "topmostSubform[0].Copy1[0].Col_Left[0].f2_02[0]": "38-0226974",
      "topmostSubform[0].Copy1[0].Col_Left[0].f2_03[0]": "West and Sons Inc, 0324 Morgan Brook, Port Shawnstad, KY 78445-9845",
      "topmostSubform[0].Copy1[0].Col_Left[0].f2_04[0]": "5777864",
      "topmostSubform[0].Copy1[0].Col_Left[0].FirstName_ReadOrder[0].f2_05[0]": "Diana",
      "topmostSubform[0].Copy1[0].Col_Left[0].LastName_ReadOrder[0].f2_06[0]": "Reyes",
      "topmostSubform[0].Copy1[0].Col_Left[0].f2_08[0]": "094 Harris Prairie, Susanville, ME 60154-1359",
      "topmostSubform[0].Copy1[0].Boxes15_ReadOrder[0].Box15_ReadOrder[0].f2_29[0]": "HI",
      "topmostSubform[0].Copy1[0].Boxes15_ReadOrder[0].f2_30[0]": "457-24-914",
      "topmostSubform[0].Copy1[0].Boxes15_ReadOrder[0].f2_31[0]": "WI",
      "topmostSubform[0].Copy1[0].Boxes15_ReadOrder[0].f2_32[0]": "386-31-922",
      "topmostSubform[0].Copy1[0].Box16_ReadOrder[0].f2_33[0]": "68,442.97",
      "topmostSubform[0].Copy1[0].Box16_ReadOrder[0].f2_34[0]": "66,147.70",
      "topmostSubform[0].Copy1[0].Box17_ReadOrder[0].f2_35[0]": "4,761.03",
      "topmostSubform[0].Copy1[0].Box17_ReadOrder[0].f2_36[0]": "6,996.33",
      "topmostSubform[0].Copy1[0].Box18_ReadOrder[0].f2_37[0]": "101,209.95",
      "topmostSubform[0].Copy1[0].Box18_ReadOrder[0].f2_38[0]": "125,139.92",
      "topmostSubform[0].Copy1[0].Box19_ReadOrder[0].f2_39[0]": "14,120.87",
      "topmostSubform[0].Copy1[0].Box19_ReadOrder[0].f2_40[0]": "23,035.86"
    }

    edit_form(form_field_mappings)


