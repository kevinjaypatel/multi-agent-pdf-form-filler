import os 
from PIL import Image, ImageDraw, ImageFont 

image_path = "input/data/image/w2_unfilled.jpg" 
new_values = {
  "new_values": {
    "Employee's Social Security Number": {"position": [40, 30], "new_value": "053-93-7915"},
    "Employer Identification Number (EIN)": {"position": [40, 60], "new_value": "38-0226974"},
    "Employer's Name": {"position": [40, 90], "new_value": "West and Sons Inc"},
    "Employer's Address": {"position": [40, 120], "new_value": "0324 Morgan Brook, Port Shawnstad, KY 78445-9845"},
    "Employee's First Name": {"position": [40, 150], "new_value": "Diana"},
    "Employee's Last Name": {"position": [200, 150], "new_value": "Reyes"},
    "Employee's Address": {"position": [40, 180], "new_value": "094 Harris Prairie, Susanville, ME 60154-1359"},
    "Wages, Tips, Other Compensation": {"position": [400, 30], "new_value": "$126,589.34"},
    "Federal Income Tax Withheld": {"position": [400, 60], "new_value": "$43,873.99"},
    "Social Security Wages": {"position": [400, 90], "new_value": "$122,867.85"},
    "Social Security Tax Withheld": {"position": [400, 120], "new_value": "$9,399.39"},
    "Medicare Wages and Tips": {"position": [400, 150], "new_value": "$122,867.85"},
    "Medicare Tax Withheld": {"position": [400, 180], "new_value": "$3,311.28"},
    "HI State Wages, Tips, etc.": {"position": [40, 240], "new_value": "$68,442.97"},
    "HI State Income Tax": {"position": [200, 240], "new_value": "$4,761.03"},
    "HI Local Wages, Tips, etc.": {"position": [400, 240], "new_value": "$101,209.95"},
    "HI Local Income Tax": {"position": [600, 240], "new_value": "$14,120.87"},
    "WI State Wages, Tips, etc.": {"position": [40, 270], "new_value": "$66,147.70"},
    "WI State Income Tax": {"position": [200, 270], "new_value": "$6,996.33"},
    "WI Local Wages, Tips, etc.": {"position": [400, 270], "new_value": "$125,139.92"},
    "WI Local Income Tax": {"position": [600, 270], "new_value": "$23,035.86"},
}
}

def edit_form(image_data: str, new_values: dict, font_size: int = 18) -> str:
    """
    Edit a form image and return it in a format displayable in chat.
    
    Args:
        image_data: File path to the image
        new_values: Dictionary with field positions and values to insert
        font_size: Font size for the text
    
    Returns:
        Markdown image string that can be displayed in chat
    """
    try:
        image = None 
        # Load the image
        if os.path.exists(image_data):
            print(f"Loading image from {image_data}")
            image = Image.open(image_data)
        else:
            return f"Error: Image file not found at {image_data}"
        
        draw = ImageDraw.Draw(image)

        # Load a monospaced font for better alignment
        font = ImageFont.load_default() 
        
        # Extract the actual values from the nested structure
        values_to_edit = new_values.get("new_values", new_values)
        
        for field, info in values_to_edit.items():
            position = tuple(info["position"])
            new_text = info['new_value'] 

            bbox = draw.textbbox(position, new_text, font=font)
            # print("Position: ", position)
            # print("Bbox: ", bbox)
            
            # Adjust position to center text in the field
            adjusted_x = bbox[0] + bbox[2] // 2
            adjusted_y = bbox[1] + bbox[3] // 2

            # Draw rectangle around the text area
            draw.rectangle(bbox, outline="red", width=1)
            
            # Draw the text
            draw.text(position, new_text, font=font, fill="black")
            
        print("Finished drawing text")

    except Exception as e:
        return f"Error: Could not process image: {e}"
    
    # Save the edited image
    updated_image_filename = "edited_form.jpg"
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    updated_image_path = os.path.join(output_dir, updated_image_filename)
    image.save(updated_image_path) 
    # Return a markdown image link that can be displayed in the agent's response
    # image_url = f"/static/edited_form.jpg"
    print(f"Edited tax form saved at {updated_image_path}")

if __name__ == "__main__":  
    edit_form(image_path, new_values) 