import subprocess

if __name__ == "__main__":
    scripts_to_run = ["data_preprocessing.py", "data_preprocessing_model.py"]

    for script_path in scripts_to_run:
        try:
            subprocess.run(["python", script_path], check=True)
            print(f"Script '{script_path}' executed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error executing script '{script_path}': {e}")
