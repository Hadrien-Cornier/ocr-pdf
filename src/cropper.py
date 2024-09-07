from PIL import Image
import os
from pdf2image import convert_from_path
import configparser
import cv2
import numpy as np

# Get the absolute path to the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (project root)
project_root = os.path.dirname(script_dir)
# Construct the path to the config file
config_path = os.path.join(project_root, 'config', 'config.ini')

# Load configuration
config = configparser.ConfigParser()
config.read(config_path)

# Define the directories
input_directory = os.path.join(project_root, config.get('cropper', 'input_dir'))
output_directory = os.path.join(project_root, config.get('cropper', 'output_dir'))
debug_directory = os.path.join(project_root, config.get('cropper', 'debug_dir'))

# Define the rectangle size
rect_width = config.getint('cropper', 'rect_width')
rect_height = config.getint('cropper', 'rect_height')

# Ensure the output and debug directories exist
os.makedirs(output_directory, exist_ok=True)
os.makedirs(debug_directory, exist_ok=True)

def convert_pdf_to_png(pdf_path, output_directory):
    pages = convert_from_path(pdf_path)
    png_paths = []
    for i, page in enumerate(pages):
        png_path = os.path.join(output_directory, f'page_{i+1}.png')
        page.save(png_path, 'PNG')
        png_paths.append(png_path)
    return png_paths

def crop_image(input_path, output_path, debug_path, rect_width, rect_height):
    with Image.open(input_path) as img:
        width, height = img.size
        
        # Calculate the dimensions for the rectangle
        rect_width = min(rect_width, width)  # Ensure rect_width doesn't exceed image width
        rect_height = min(rect_height, height)  # Ensure rect_height doesn't exceed image height
        
        left = width - rect_width  # Align to right border
        bottom = (height + rect_height) // 2  # Center vertically
        right = width
        top = bottom - rect_height

        # Crop the image
        cropped_img = img.crop((left, top, right, bottom))
        
        # Save the cropped image
        cropped_img.save(output_path)

        # Create debug image
        debug_img = cv2.imread(input_path)
        cv2.rectangle(debug_img, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.imwrite(debug_path, debug_img)

# Get all PDF files in the input directory
pdf_files = [f for f in os.listdir(input_directory) if f.endswith('.pdf')]

# Sort the files to ensure consistent numbering
pdf_files.sort()

# Iterate over each PDF in the input directory
for i, filename in enumerate(pdf_files, start=1):
    # Construct full input path
    input_path = os.path.join(input_directory, filename)
    
    # Convert PDF to PNG
    png_paths = convert_pdf_to_png(input_path, output_directory)
    
    # Crop each converted PNG
    for j, png_path in enumerate(png_paths, start=1):
        output_filename = f'questionnaire_{i}_page_{j}.png'
        output_path = os.path.join(output_directory, output_filename)
        debug_filename = f'debug_questionnaire_{i}_page_{j}.png'
        debug_path = os.path.join(debug_directory, debug_filename)
        
        # Crop the image
        crop_image(png_path, output_path, debug_path, rect_width, rect_height)
        
        # Remove the temporary full-page PNG
        os.remove(png_path)

print(f"Conversion and cropping completed. {len(pdf_files)} PDFs processed.")