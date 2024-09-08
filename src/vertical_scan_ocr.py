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

# # Define grade bands
# GRADE_BANDS = [
#     (10, 26, 1),
#     (26, 39, 2),
#     (39, 50, 3),
#     (50, 60, 4),
# ]

def detect_ink_cells(image_path, cell_width=20, cell_height=20, threshold=200):
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Failed to load image: {image_path}")
        return None, None

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape
    ink_cells = []

    for y in range(0, height - cell_height, cell_height // 2):
        for x in range(0, width - cell_width, cell_width // 2):
            cell = gray[y:y+cell_height, x:x+cell_width]
            avg_value = np.mean(cell)
            if avg_value < threshold:
                ink_cells.append((x, y, cell_width, cell_height, 255 - avg_value))

    nms_cells = non_max_suppression(ink_cells)
    return nms_cells, image, width

def non_max_suppression(cells, overlap_threshold=0.3):
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

def calculate_grades(ink_cells, image_width):
    grades = []
    for cell in ink_cells:
        x, y, w, h, _ = cell
        centroid_x = x + w / 2
        centroid_y = y + h / 2
        grade_percentage = (centroid_x / image_width) * 100
        grade = next((g for low, high, g in GRADE_BANDS if low <= grade_percentage < high), None)
        grades.append((centroid_y, grade_percentage, grade))

    # Sort grades by y-coordinate (top to bottom)
    grades.sort(key=lambda x: x[0])

    return grades

def draw_ink_cells_and_bands(image, ink_cells, grades):
    height, width, _ = image.shape

    # Draw grade bands
    for low, high, grade in GRADE_BANDS:
        x1 = int(low * width / 100)
        x2 = int(high * width / 100)
        cv2.line(image, (x1, 0), (x1, height), (200, 200, 200), 1)
        cv2.putText(image, str(grade), (x1 + 5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 2)

    # Draw cells and grades
    for cell, (_, percentage, grade) in zip(ink_cells, grades):
        x, y, w, h, _ = map(int, cell)
        cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(image, f"{percentage:.1f}% (Grade: {grade})", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    return image

# Define directories
script_dir = os.path.dirname(os.path.abspath(__file__))
input_directory = os.path.join(script_dir, 'out')
debug_directory = os.path.join(script_dir, 'debug')

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
            ink_cells = filter_horizontal_cells(ink_cells)
            grades = calculate_grades(ink_cells, image_width)

            print(f"Grades for {filename}:")
            for i, (_, percentage, grade) in enumerate(grades, 1):
                print(f"  Question {i}: {percentage:.1f}% (Grade: {grade})")

            # Draw ink cells, grades, and bands on the image
            debug_image = draw_ink_cells_and_bands(original_image.copy(), ink_cells, grades)

            # Save the debug image
            debug_image_path = os.path.join(debug_directory, f"debug_{filename}")
            cv2.imwrite(debug_image_path, debug_image)
            print(f"Debug image saved: {debug_image_path}")

    print(f"Grade extraction completed. {len(png_files)} images processed.")
else:
    print("No PNG files found in the input directory.")