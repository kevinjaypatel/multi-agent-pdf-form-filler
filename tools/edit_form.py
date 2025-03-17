import os 
from PIL import Image, ImageDraw, ImageFont 

image_path = "data/w2_unfilled.jpg" 
new_values = {
  "new_values": {
    "Employee's Social Security Number": {"position": [70, 30], "new_value": "053-93-7915"},
    "Employer Identification Number (EIN)": {"position": [70, 70], "new_value": "38-0226974"},
    "Employer's Name, Address, and ZIP Code": {"position": [70, 110], "new_value": "West and Sons Inc, 0324 Morgan Brook, Port Shawnstad, KY 78445-9845"},
    "Employee's First Name and Initial, Last Name, Suffix": {"position": [70, 210], "new_value": "Diana Reyes"},
    "Employee's Address and ZIP Code": {"position": [70, 250], "new_value": "094 Harris Prairie, Susanville, ME 60154-1359"},
    "Wages, Tips, Other Compensation": {"position": [390, 30], "new_value": "126589.34"},
    "Federal Income Tax Withheld": {"position": [390, 70], "new_value": "43873.99"},
    "Social Security Wages": {"position": [390, 110], "new_value": "122867.85"},
    "Social Security Tax Withheld": {"position": [390, 150], "new_value": "9399.39"},
    "Medicare Wages and Tips": {"position": [390, 190], "new_value": "122867.85"},
    "Medicare Tax Withheld": {"position": [390, 230], "new_value": "3311.28"},
    "Social Security Tips": {"position": [390, 270], "new_value": "0.00"},
    "Allocated Tips": {"position": [390, 310], "new_value": "0.00"},
    "State Wages, Tips, etc. (HI)": {"position": [70, 450], "new_value": "68442.97"},
    "State Income Tax (HI)": {"position": [230, 450], "new_value": "4761.03"},
    "State Wages, Tips, etc. (WI)": {"position": [230, 450], "new_value": "66147.7"},
    "State Income Tax (WI)": {"position": [390, 450], "new_value": "6996.33"},
    "Local Wages, Tips, etc. (HI)": {"position": [230, 450], "new_value": "101209.95"},
    "Local Income Tax (HI)": {"position": [390, 450], "new_value": "14120.87"},
    "Local Wages, Tips, etc. (WI)": {"position": [390, 450], "new_value": "125139.92"},
    "Local Income Tax (WI)": {"position": [550, 450], "new_value": "23035.86"}
}
}

def edit_form(image_path: str, new_values: dict, font_size: int = 18) -> str: 
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image) 

    font = ImageFont.load_default()  

    # Extract the actual values from the nested structure
    values_to_edit = new_values.get("new_values", new_values)
    
    for field, info in values_to_edit.items(): 
        position = tuple(info["position"])

        # Erase old text (draw a white box over the field)
        # draw.rectangle([position, (position[0] + 200, position[1] + 40)], fill="white")

        # Insert new text
        draw.text(position, info["new_value"], font=font, fill="black")

    # Save the edited image
    updated_image_filename = "edited_form.jpg"
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    updated_image_path = os.path.join(output_dir, updated_image_filename)
    image.save(updated_image_path) 
    
    # Return a markdown image link that can be displayed in the agent's response
    # image_url = f"/static/edited_form.jpg"
    print(f"Edited tax form saved at {updated_image_path}")
    # return f"![Edited Form]({image_url})"

if __name__ == "__main__":  
    edit_form(image_path, new_values) 