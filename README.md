
## Setup Instructions

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ocr-pdf.git
   cd ocr-pdf
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
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
