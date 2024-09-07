import cv2
import numpy as np
import os
import json
import configparser

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

def rotate_image(image, angle):
    height, width = image.shape[:2]
    center = (width // 2, height // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, rotation_matrix, (width, height), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
    return rotated

def find_best_rotation(image, angle_range=20, step=0.5):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape
    kernel_height = height // 20
    kernel = np.ones((kernel_height, width)) / width
    kernel[kernel_height//2:] = -kernel[kernel_height//2:]

    max_response = float('-inf')
    best_angle = 0

    for angle in np.arange(-angle_range, angle_range + step, step):
        rotated = rotate_image(gray, angle)
        response = np.abs(cv2.filter2D(rotated, -1, kernel)).max()
        if response > max_response:
            max_response = response
            best_angle = angle

    return best_angle

def find_content_margins(image, threshold=30):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape
    
    def compute_gradient(column):
        return np.abs(np.diff(column.astype(np.float32)))
    
    left_margin = 0
    right_margin = width - 1
    
    for x in range(width // 2):
        left_gradient = compute_gradient(gray[:, x])
        right_gradient = compute_gradient(gray[:, width - 1 - x])
        
        if left_margin == 0 and np.max(left_gradient) > threshold:
            left_margin = x
        
        if right_margin == width - 1 and np.max(right_gradient) > threshold:
            right_margin = width - 1 - x
        
        if left_margin != 0 and right_margin != width - 1:
            break
    
    return left_margin, right_margin

def detect_horizontal_bands(image, left_margin, right_margin):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape
    content = gray[:, left_margin:right_margin]
    
    # Apply edge detection
    edges = cv2.Canny(content, 50, 150)
    
    # Sum the edge detection results horizontally
    edge_sum = np.sum(edges, axis=1)
    
    # Get threshold values from config
    threshold = config.getint('aligner', 'horizontal_band_threshold')
    min_gap = config.getint('aligner', 'min_band_gap')

    bands = [0]
    last_band = 0
    for y in range(1, height - 1):
        if edge_sum[y] > threshold * (right_margin - left_margin) and y - last_band >= min_gap:
            bands.append(y)
            last_band = y
    
    if bands[-1] != height - 1:
        bands.append(height - 1)
    
    return bands

def create_grade_bands(left_margin, right_margin, num_grades):
    content_width = right_margin - left_margin
    band_width = content_width // num_grades
    
    bands = [
        left_margin + i * band_width for i in range(num_grades + 1)
    ]
    
    return bands

def align_questionnaire(input_path, output_path, debug_path, bands_dict):
    image = cv2.imread(input_path)
    if image is None:
        print(f"Error: Failed to load image: {input_path}")
        return

    angle_range = config.getfloat('aligner', 'angle_range')
    angle_step = config.getfloat('aligner', 'angle_step')
    best_angle = find_best_rotation(image, angle_range, angle_step)
    print(f"Best rotation angle: {best_angle:.2f} degrees")

    rotated = rotate_image(image, best_angle)
    left_margin, right_margin = find_content_margins(rotated)
    
    num_grades = config.getint('aligner', 'num_grades')
    vertical_bands = create_grade_bands(left_margin, right_margin, num_grades)
    horizontal_bands = detect_horizontal_bands(rotated, left_margin, right_margin)
    
    # Create debug image
    debug_image = rotated.copy()
    for i, x in enumerate(vertical_bands):
        cv2.line(debug_image, (x, 0), (x, debug_image.shape[0]), (0, 255, 0), 2)
        if i < num_grades:
            cv2.putText(debug_image, str(i+1), (x + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    for i, y in enumerate(horizontal_bands):
        cv2.line(debug_image, (left_margin, y), (right_margin, y), (255, 0, 0), 2)
        cv2.putText(debug_image, str(i), (left_margin - 40, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    # Save aligned and debug images
    cv2.imwrite(output_path, rotated)
    cv2.imwrite(debug_path, debug_image)
    print(f"Aligned image saved: {output_path}")
    print(f"Debug image saved: {debug_path}")
    
    # Save band information
    bands_dict[os.path.basename(output_path)] = {
        'vertical': vertical_bands,
        'horizontal': horizontal_bands
    }

# Main execution
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_directory = os.path.join(script_dir, config.get('aligner', 'input_dir'))
    output_directory = os.path.join(script_dir, config.get('aligner', 'output_dir'))
    debug_directory = os.path.join(script_dir, config.get('aligner', 'debug_dir'))
    json_directory = os.path.join(script_dir, config.get('paths', 'json_dir'))

    print(f"Input directory: {input_directory}")
    print(f"Output directory: {output_directory}")
    print(f"Debug directory: {debug_directory}")

    # Ensure output directories exist
    os.makedirs(output_directory, exist_ok=True)
    os.makedirs(debug_directory, exist_ok=True)
    os.makedirs(json_directory, exist_ok=True)

    # Get all PNG files in the input directory
    png_files = [f for f in os.listdir(input_directory) if f.endswith('.png')]
    png_files.sort()

    bands_dict = {}

    if png_files:
        for filename in png_files:
            input_path = os.path.join(input_directory, filename)
            output_path = os.path.join(output_directory, f"aligned_{filename}")
            debug_path = os.path.join(debug_directory, f"debug_{filename}")
            align_questionnaire(input_path, output_path, debug_path, bands_dict)

        # Save bands to JSON file
        json_path = os.path.join(json_directory, 'detected_grade_bands.json')
        with open(json_path, 'w') as f:
            json.dump(bands_dict, f)
        print(f"Grade bands saved to: {json_path}")

        print(f"Alignment completed. {len(png_files)} images processed.")
    else:
        print("No PNG files found in the input directory.")