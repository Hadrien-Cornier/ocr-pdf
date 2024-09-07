# Setup Instructions

1. Create a virtual environment:
   ```
   python -m venv .venv
   ```

2. Activate the virtual environment:
   - On Windows:
     ```
     .venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```
     source .venv/bin/activate
     ```

3. Install the requirements:
   ```
   pip install -r requirements.txt
   ```

Make sure you have Python installed on your system before following these steps.


4. Prepare and process your PDF:
   a. Place your PDF files in the `in/` folder.
   b. Run the cropper script:
      ```
      python cropper.py
      ```
   c. Run the vertical scan OCR script:
      ```
      python vertical_scan_ocr.py
      ```

This process will first crop your PDF into individual pages, then perform vertical scanning OCR on the resulting images.

