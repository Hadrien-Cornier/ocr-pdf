# OCR PDF Survey Response Extractor

This project is designed to extract manual survey responses from scanned PDF documents. It uses image processing techniques to identify and grade multiple-choice answers from questionnaires.

## Overview

The system processes scanned PDF surveys through the following steps:
1. PDF to image conversion
2. Image cropping and alignment
3. Detection of answer grids
4. Response extraction
5. Grading and result compilation

This automated approach allows for efficient processing of large volumes of paper-based surveys, converting them into digital data for analysis.

## Setup Instructions

1. Clone the repository:
   ```
   git clone https://github.com/Hadrien-Cornier/ocr-pdf.git
   cd ocr-pdf
   ```

2. Create and activate a virtual environment:

   For macOS and Linux:
   ```
   python -m venv .venv
   source .venv/bin/activate
   ```

   For Windows:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install the requirements:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Place your PDF files in the `data/input/` directory.

2. Run the pipeline:
   ```
   python src/run_pipeline.py
   ```

   This will execute the following steps:
   - Crop the PDFs (output in `data/cropped/`)
   - Align the images (output in `data/aligned/`)
   - Perform OCR and grade extraction (output in `data/output/`)

3. Check the results in the `data/output/` directory.

4. Debug images for each step can be found in the respective subdirectories of `data/debug/`.

## Configuration

Adjust the settings in `config/config.ini` to customize the pipeline behavior.

## Requirements

See `requirements.txt` for the list of Python packages required.
