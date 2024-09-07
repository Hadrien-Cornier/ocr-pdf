import cv2
import numpy as np
import os
import json
import configparser

# Get the absolute path to the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (project root)
project_root = os.path.dirname(script_dir)
# Construct the path to the config file
config_path = os.path.join(project_root, 'config', 'config.ini')

# Load configuration
config = configparser.ConfigParser()
config.read(config_path)

# Load the detected grade bands
json_dir = config.get('paths', 'json_dir')
json_path = os.path.join(project_root, json_dir, 'detected_grade_bands.json')

try:
    with open(json_path, 'r') as f:
        DETECTED_BANDS = json.load(f)
except FileNotFoundError:
    print(f"Error: Could not find {json_path}")
    print("Make sure the aligner step has been run and produced the JSON file.")
    exit(1)

# Set the number of questions and grades
NUM_QUESTIONS = config.getint('aligner', 'num_questions')
NUM_GRADES = config.getint('aligner', 'num_grades')

def detect_ink_in_cell(image, cell_coords, threshold=200):
    x1, y1, x2, y2 = cell_coords
    cell = image[y1:y2, x1:x2]
    avg_value = np.mean(cell)
    return avg_value < threshold, 255 - avg_value

def grade_questionnaire(image_path, bands):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        print(f"Error: Failed to load image: {image_path}")
        return None

    vertical_bands = bands['vertical']
    horizontal_bands = bands['horizontal']

    if len(vertical_bands) - 1 != NUM_GRADES:
        print(f"Warning: Number of detected grade columns ({len(vertical_bands) - 1}) does not match expected ({NUM_GRADES})")

    expected_horizontal_bands = NUM_QUESTIONS * 2  # Top and bottom of each question
    if len(horizontal_bands) != expected_horizontal_bands:
        print(f"Warning: Number of detected horizontal bands ({len(horizontal_bands)}) does not match expected ({expected_horizontal_bands})")

    grades = []
    for i in range(0, min(len(horizontal_bands) - 1, expected_horizontal_bands - 1), 2):
        question_grades = []
        for j in range(len(vertical_bands) - 1):
            cell_coords = (vertical_bands[j], horizontal_bands[i],
                           vertical_bands[j+1], horizontal_bands[i+1])
            has_ink, ink_value = detect_ink_in_cell(image, cell_coords)
            if has_ink:
                question_grades.append((j + 1, ink_value))
        
        if question_grades:
            grades.append(max(question_grades, key=lambda x: x[1])[0])
        else:
            grades.append(None)  # No answer detected for this question

    return grades

def draw_debug_image(image_path, bands, grades):
    image = cv2.imread(image_path)
    vertical_bands = bands['vertical']
    horizontal_bands = bands['horizontal']

    # Draw vertical bands
    for i, x in enumerate(vertical_bands):
        cv2.line(image, (x, 0), (x, image.shape[0]), (0, 255, 0), 2)
        if i < NUM_GRADES:
            cv2.putText(image, str(i+1), (x + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # Draw horizontal bands
    for y in horizontal_bands:
        cv2.line(image, (0, y), (image.shape[1], y), (255, 0, 0), 2)

    # Draw grades
    for i, grade in enumerate(grades):
        if grade is not None:
            y = (horizontal_bands[i*2] + horizontal_bands[i*2+1]) // 2
            x = vertical_bands[grade - 1] + 10
            cv2.putText(image, f"Q{i+1}: {grade}", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    return image

# Define directories
input_directory = os.path.join(project_root, config.get('ocr', 'input_dir'))
debug_directory = os.path.join(project_root, config.get('ocr', 'debug_dir'))

print(f"Input directory: {input_directory}")
print(f"Debug directory: {debug_directory}")

# Ensure debug directory exists
os.makedirs(debug_directory, exist_ok=True)

# Get all PNG files in the input directory
png_files = [f for f in os.listdir(input_directory) if f.endswith('.png')]
png_files.sort()

if png_files:
    for filename in png_files:
        image_path = os.path.join(input_directory, filename)
        if filename not in DETECTED_BANDS:
            print(f"Warning: No band data found for {filename}")
            continue
        bands = DETECTED_BANDS[filename]
        
        grades = grade_questionnaire(image_path, bands)
        
        if grades is not None:
            print(f"Grades for {filename}:")
            for i, grade in enumerate(grades, 1):
                print(f"  Question {i}: {'Not answered' if grade is None else f'Grade {grade}'}")
            
            # Create debug image
            debug_image = draw_debug_image(image_path, bands, grades)
            
            # Save the debug image
            debug_image_path = os.path.join(debug_directory, f"debug_{filename}")
            cv2.imwrite(debug_image_path, debug_image)
            print(f"Debug image saved: {debug_image_path}")

    print(f"Grade extraction completed. {len(png_files)} images processed.")
else:
    print("No PNG files found in the input directory.")