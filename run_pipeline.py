import os
import configparser
import subprocess

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

def run_step(script_name):
    print(f"Running {script_name}...")
    try:
        result = subprocess.run(['python', script_name], check=True, text=True, capture_output=True)
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}:")
        print(e.stdout)
        print("Error output:")
        print(e.stderr)
        raise
    print(f"{script_name} completed.\n")

def main():
    pipeline_steps = config.get('pipeline', 'steps').split(',')
    
    for step in pipeline_steps:
        if step == 'cropper':
            run_step('cropper.py')
        elif step == 'aligner':
            run_step('align_questionnaire.py')
        elif step == 'ocr':
            run_step('vertical_scan_ocr.py')
        else:
            print(f"Unknown step: {step}")

    print("Pipeline completed.")

if __name__ == "__main__":
    main()