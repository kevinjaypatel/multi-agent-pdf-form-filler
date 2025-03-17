import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import json
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PolygonFormFiller:
    """
    A class for filling forms using polygon-based field identification.
    This is more accurate than coordinate-based approaches, as it can handle
    irregular shapes and provides better text placement.
    """
    
    def __init__(self, default_font_path=None, default_font_size=12, debug=False):
        """
        Initialize the form filler with default settings.
        
        Args:
            default_font_path: Path to default font to use for text insertion
            default_font_size: Default font size to use
            debug: Whether to save debug images showing polygon boundaries
        """
        self.default_font_path = default_font_path or "/path/to/default/font.ttf"
        self.default_font_size = default_font_size
        self.debug = debug
        
        # Verify default font exists
        if not os.path.exists(self.default_font_path):
            logger.warning(f"Default font not found at {self.default_font_path}, system will attempt to use fallback fonts")
        
    def edit_form(self, image_path, new_values, output_path=None):
        """
        Fill a form with the provided values using polygon-based field targeting.
        
        Args:
            image_path: Path to the form image
            new_values: Dictionary with field names and their values + polygons
            output_path: Where to save the filled form (defaults to adding "_filled" suffix)
            
        Returns:
            Path to the filled form
        """
        logger.info(f"Processing form: {image_path}")
        
        # Validate inputs
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Form image not found: {image_path}")
        
        if not new_values:
            logger.warning("No values provided to fill in the form")
            return image_path
        
        # Set output path if not provided
        if output_path is None:
            file_name, file_ext = os.path.splitext(image_path)
            output_path = f"{file_name}_filled{file_ext}"
        
        # Open the image using PIL (handles various formats better than OpenCV for saving)
        try:
            form_image = Image.open(image_path)
            draw = ImageDraw.Draw(form_image)
            
            # Create a debug image if needed
            if self.debug:
                debug_image = form_image.copy()
                debug_draw = ImageDraw.Draw(debug_image)
            
            # Process each field
            for field_name, field_data in new_values.items():
                self._fill_field(form_image, draw, field_name, field_data)
                
                # Draw polygon on debug image
                if self.debug and 'polygon' in field_data:
                    self._draw_debug_polygon(debug_draw, field_data['polygon'], field_name)
            
            # Save the result
            form_image.save(output_path)
            logger.info(f"Filled form saved to: {output_path}")
            
            # Save debug image if needed
            if self.debug:
                debug_path = f"{os.path.splitext(output_path)[0]}_debug{os.path.splitext(output_path)[1]}"
                debug_image.save(debug_path)
                logger.info(f"Debug visualization saved to: {debug_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error filling form: {str(e)}")
            raise
    
    def _fill_field(self, image, draw, field_name, field_data):
        """Fill a single field in the form."""
        # Extract field information
        new_value = field_data.get('new_value', '')
        
        # Skip empty values
        if not new_value:
            logger.warning(f"Empty value for field '{field_name}', skipping")
            return
        
        # Handle different field identification methods
        if 'polygon' in field_data:
            self._fill_polygon_field(image, draw, field_name, field_data)
        elif 'position' in field_data:
            # Backward compatibility with coordinate-based approach
            logger.info(f"Using legacy coordinate method for field '{field_name}'")
            self._fill_coordinate_field(image, draw, field_name, field_data)
        else:
            logger.warning(f"No valid positioning data for field '{field_name}', skipping")
    
    def _fill_polygon_field(self, image, draw, field_name, field_data):
        """Fill a field identified by a polygon boundary."""
        try:
            # Extract polygon and value
            polygon = field_data.get('polygon', [])
            new_value = field_data.get('new_value', '')
            
            # Validate polygon has at least 3 points
            if len(polygon) < 3:
                logger.warning(f"Polygon for '{field_name}' has fewer than 3 points, skipping")
                return
            
            # Calculate the bounding box of the polygon
            xs = [p[0] for p in polygon]
            ys = [p[1] for p in polygon]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            
            # Calculate width and height
            width = max_x - min_x
            height = max_y - min_y
            
            # Calculate polygon centroid for text placement
            centroid_x = sum(xs) / len(polygon)
            centroid_y = sum(ys) / len(polygon)
            
            # Get or calculate font size based on field size
            font_size = field_data.get('font_size', self._estimate_font_size(width, height, new_value))
            
            # Load font
            font_path = field_data.get('font_path', self.default_font_path)
            try:
                font = ImageFont.truetype(font_path, font_size)
            except Exception as e:
                logger.warning(f"Could not load font {font_path}: {str(e)}. Using default font.")
                font = ImageFont.load_default()
            
            # Calculate text size to center it properly
            text_bbox = draw.textbbox((0, 0), new_value, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Calculate text position (centered in polygon)
            text_x = centroid_x - (text_width / 2)
            text_y = centroid_y - (text_height / 2)
            
            # Special handling for checkboxes
            if 'checkbox' in field_name.lower() or field_data.get('field_type') == 'checkbox':
                self._handle_checkbox(draw, polygon, new_value)
            else:
                # Draw the text
                draw.text((text_x, text_y), new_value, font=font, fill='black')
                
            logger.info(f"Filled field '{field_name}' with value '{new_value}' using polygon method")
            
        except Exception as e:
            logger.error(f"Error filling polygon field '{field_name}': {str(e)}")
    
    def _fill_coordinate_field(self, image, draw, field_name, field_data):
        """Legacy method to fill a field identified by coordinates (for backward compatibility)."""
        try:
            # Extract position and value
            position = field_data.get('position', [0, 0])
            new_value = field_data.get('new_value', '')
            
            # Get or calculate font size
            font_size = field_data.get('font_size', self.default_font_size)
            
            # Load font
            font_path = field_data.get('font_path', self.default_font_path)
            try:
                font = ImageFont.truetype(font_path, font_size)
            except Exception as e:
                logger.warning(f"Could not load font {font_path}: {str(e)}. Using default font.")
                font = ImageFont.load_default()
            
            # Draw the text
            draw.text((position[0], position[1]), new_value, font=font, fill='black')
            logger.info(f"Filled field '{field_name}' with value '{new_value}' using coordinate method")
            
        except Exception as e:
            logger.error(f"Error filling coordinate field '{field_name}': {str(e)}")
    
    def _handle_checkbox(self, draw, polygon, value):
        """Handle checkbox fields differently - fill with X or check mark if true."""
        # Determine if checkbox should be checked
        check_it = str(value).lower() in ['true', 'yes', 'y', '1', 'checked', 'selected', 'x']
        
        if check_it:
            # Calculate the bounding box
            xs = [p[0] for p in polygon]
            ys = [p[1] for p in polygon]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            
            # Draw an X in the checkbox
            draw.line([(min_x, min_y), (max_x, max_y)], fill='black', width=2)
            draw.line([(max_x, min_y), (min_x, max_y)], fill='black', width=2)
    
    def _estimate_font_size(self, width, height, text):
        """Estimate an appropriate font size based on field dimensions and text length."""
        # Simple heuristic: try to fit text in the field
        field_area = width * height
        text_length = len(text)
        
        # Base calculation on field size and text length
        if text_length <= 0:
            return self.default_font_size
            
        # Adjust based on field width and character count
        estimated_size = int(min(width / text_length * 1.5, height * 0.7))
        
        # Clamp to reasonable range
        return max(8, min(estimated_size, 36))
    
    def _draw_debug_polygon(self, draw, polygon, field_name):
        """Draw the polygon boundary for debugging purposes."""
        # Draw polygon outline
        draw.polygon(polygon, outline='red')
        
        # Calculate centroid for label
        centroid_x = sum(p[0] for p in polygon) / len(polygon)
        centroid_y = sum(p[1] for p in polygon) / len(polygon)
        
        # Draw field name
        draw.text((centroid_x, centroid_y), field_name, fill='blue')

# Command-line interface for the tool
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Fill a form using polygon-based field identification')
    parser.add_argument('image_path', help='Path to the form image')
    parser.add_argument('json_path', help='Path to JSON file with field values and polygons')
    parser.add_argument('--output', '-o', help='Output path for filled form')
    parser.add_argument('--font', '-f', help='Path to font file')
    parser.add_argument('--size', '-s', type=int, help='Default font size')
    parser.add_argument('--debug', '-d', action='store_true', help='Save debug image with polygon boundaries')
    
    args = parser.parse_args()
    
    # Load the JSON data
    with open(args.json_path, 'r') as f:
        new_values = json.load(f)
    
    # Create the form filler
    filler = PolygonFormFiller(
        default_font_path=args.font,
        default_font_size=args.size or 12,
        debug=args.debug
    )
    
    # Fill the form
    filled_form_path = filler.edit_form(args.image_path, new_values, args.output)
    print(f"Form filled and saved to: {filled_form_path}")
