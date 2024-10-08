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

# Get directories from config
input_dir = config.get('ocr', 'input_dir')
output_dir = config.get('ocr', 'output_dir')
debug_dir = config.get('ocr', 'debug_dir')

# Get OCR parameters from config
cell_width = config.getint('ocr', 'cell_width')
cell_height = config.getint('ocr', 'cell_height')
ink_threshold = config.getint('ocr', 'ink_threshold')
overlap_threshold = config.getfloat('ocr', 'overlap_threshold')
questions_file = config.get('questions', 'file')
questions_path = os.path.join(project_root, "config", questions_file)
questions = json.load(open(questions_path))
number_of_questions = sum(len(section) for section in questions.values())
number_of_grades = config.getint('questions', 'number_of_grades')

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

def detect_ink_cells(image_path):
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Failed to load image: {image_path}")
        return None, None

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape
    ink_cells = []

    # Get the horizontal bands for this image
    filename = os.path.basename(image_path)
    image_bands = DETECTED_BANDS.get(filename, {})
    horizontal_bands = image_bands.get('horizontal', [])

    if not horizontal_bands:
        print(f"Warning: No horizontal bands found for {filename}")
        return None, None

    for y in horizontal_bands:
        for x in range(0, width - cell_width, cell_width // 2):
            cell = gray[y:y+cell_height, x:x+cell_width]
            avg_value = np.mean(cell)
            if avg_value < ink_threshold:
                ink_cells.append((x, y, cell_width, cell_height, 255 - avg_value))

    nms_cells = non_max_suppression(ink_cells, overlap_threshold, max_detections=number_of_questions)
    return nms_cells, image, width

def non_max_suppression(cells, overlap_threshold=0.3, max_detections=None):
    if len(cells) == 0:
        return []

    boxes = np.array(cells)
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 0] + boxes[:, 2]
    y2 = boxes[:, 1] + boxes[:, 3]
    scores = boxes[:, 4]

    order = scores.argsort()[::-1]
    keep = []

    while order.size > 0:
        i = order[0]
        keep.append(i)
        
        if max_detections is not None and len(keep) >= max_detections:
            break

        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0.0, xx2 - xx1 + 1)
        h = np.maximum(0.0, yy2 - yy1 + 1)
        inter = w * h

        ovr = inter / (boxes[i, 2] * boxes[i, 3] + boxes[order[1:], 2] * boxes[order[1:], 3] - inter)
        inds = np.where(ovr <= overlap_threshold)[0]
        order = order[inds + 1]

    return boxes[keep].tolist()

def filter_horizontal_cells(ink_cells, vertical_threshold=5):
    sorted_cells = sorted(ink_cells, key=lambda cell: (cell[1], -cell[0]))
    filtered_cells = []
    for i, cell in enumerate(sorted_cells):
        if i == 0 or abs(cell[1] - sorted_cells[i-1][1]) > vertical_threshold:
            filtered_cells.append(cell)
    return filtered_cells

def calculate_grades(ink_cells, image_width, vertical_bands):
    grades = []
    for cell in ink_cells:
        x, y, w, h, _ = cell
        centroid_x = x + w / 2
        centroid_y = y + h / 2
        
        # Use detected bands to determine the grade
        for i in range(len(vertical_bands) - 1):
            low = vertical_bands[i]
            high = vertical_bands[i+1]
            if low <= centroid_x < high:
                grade = i + 1
                grade_percentage = ((centroid_x - low) / (high - low)) * 100
                break
        else:
            grade = None
            grade_percentage = None

        grades.append((centroid_y, grade_percentage, grade))

    # Sort grades by y-coordinate (top to bottom)
    grades.sort(key=lambda x: x[0])

    return grades

def draw_ink_cells_and_bands(image, ink_cells, grades, vertical_bands):
    height, width, _ = image.shape

    # Draw grade bands
    for i, x in enumerate(vertical_bands):
        cv2.line(image, (x, 0), (x, height), (200, 200, 200), 1)
        if i < len(vertical_bands) - 1:
            cv2.putText(image, str(i+1), (x + 5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 2)

    # Draw cells and grades
    for cell, (_, percentage, grade) in zip(ink_cells, grades):
        x, y, w, h, _ = map(int, cell)
        cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
        if percentage is not None and grade is not None:
            cv2.putText(image, f"{percentage:.1f}% (Grade: {grade})", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    return image

# Main execution
if __name__ == "__main__":
    # Define directories using config
    input_directory = os.path.join(project_root, input_dir)
    debug_directory = os.path.join(project_root, debug_dir)

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
            ink_cells, original_image, image_width = detect_ink_cells(image_path)

            if ink_cells is not None and original_image is not None:
                # Get the detected bands for this specific image
                image_bands = DETECTED_BANDS.get(filename, {})
                vertical_bands = image_bands.get('vertical', [])
                if not vertical_bands:
                    print(f"Warning: No vertical bands found for {filename}")
                    continue

                ink_cells = filter_horizontal_cells(ink_cells)
                grades = calculate_grades(ink_cells, image_width, vertical_bands)

                print(f"Grades for {filename}:")
                for i, (_, percentage, grade) in enumerate(grades, 1):
                    if percentage is not None and grade is not None:
                        print(f"  Question {i}: {percentage:.1f}% (Grade: {grade})")
                    else:
                        print(f"  Question {i}: Unable to determine grade")

                # Draw ink cells, grades, and bands on the image
                debug_image = draw_ink_cells_and_bands(original_image.copy(), ink_cells, grades, vertical_bands)

                # Save the debug image
                debug_image_path = os.path.join(debug_directory, f"debug_{filename}")
                cv2.imwrite(debug_image_path, debug_image)
                print(f"Debug image saved: {debug_image_path}")

        print(f"Grade extraction completed. {len(png_files)} images processed.")
    else:
        print("No PNG files found in the input directory.")