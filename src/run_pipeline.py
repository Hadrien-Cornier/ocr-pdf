import os
import configparser
import subprocess

# Get the absolute path to the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (project root)
project_root = os.path.dirname(script_dir)
# Construct the path to the config file
config_path = os.path.join(project_root, 'config', 'config.ini')

# Load configuration
config = configparser.ConfigParser()
config.read(config_path)

def run_step(script_name):
    print(f"Running {script_name}...")
    try:
        script_path = os.path.join(script_dir, script_name)
        result = subprocess.run(['python', script_path], check=True, text=True, capture_output=True)
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