from flask import Flask, render_template, request, redirect, url_for, send_from_directory,jsonify
import google.generativeai as genai
import json
import os
import subprocess
import threading
import socket
import hashlib
import os

# from flask_cors import CORS

# app = Flask(__name__)
# CORS(app)



def run_online(prompt):
    genai.configure(api_key='AIzaSyBFz5_rw43RviSZbWo8ieoi83NNTKKZOAQ')
    initial_content = f'''

You are tasked with developing a fully production-ready software application or program designed to run on my macOS. Follow these detailed instructions carefully to ensure the generated output is complete, error-free, and meets all requirements.

Key Requirements:
Backend Framework:

Use Flask for the back-end only if required.
If Flask is used, adhere to the following structure:
A separate folder named templates for HTML files.
User Interface:

Create a modern, accessible UI.
Containerization:

The application must run in a Docker container.
Include a Dockerfile. But do not provide necessary bash commands to build and run the container.
Dependencies:

Provide a requirements.txt file containing all necessary Python modules without specifying versions.
Compatibility:

All generated code must be fully compatible with macOS, including imports and bash commands.
Bash Commands:

Include a comprehensive list of bash commands for the same directory
Reliability:

The code must be production-ready, error-free, and adhere to best practices.
Output Structure:
Your output should be a JSON file containing the following:

File Names:

A list of all files to be created.
File Contents:

The complete code for each file, ensuring proper folder structure (e.g., templates folder for Flask apps).
Bash Commands:

A separate section with all required bash commands, including setup, dependency installation, and server startup (specific to macOS).
Additional Notes:
Double-check that the following are included if relevant:
A templates folder for HTML files if Flask is used.
Proper imports for macOS compatibility.
A Dockerfile.
Validate the output thoroughly to ensure no critical steps or files are missing.

Run the app on the following port: 5000
Now, generate the software based on this input:
{prompt}

'''
    response_schema = {
        "type": "object",
        "properties": {
            "files": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "code": {"type": "string"}
                    },
                    "required": ["name", "code"]
                }
            },
            "bash_scripts": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["files", "bash_scripts"]
    }
    
    model = genai.GenerativeModel('gemini-1.5-flash',
            generation_config={"response_mime_type": "application/json",
                                "response_schema": response_schema}
    )
    response = model.generate_content(initial_content)
    try:
        json_data = json.loads(response.text)
        with open('data.json', 'w') as json_file:
            json.dump(json_data, json_file, indent=4)
    except json.JSONDecodeError:
        print("Error: Unable to parse JSON from the response")
        return None

def create_files_from_json(json_file, new_folder):
    with open(json_file, 'r') as f:
        data = json.load(f)
        if not os.path.exists(new_folder):
            os.makedirs(new_folder)
        for file_data in data['files']:
            file_name = file_data['name']
            file_code = file_data['code']
            file_code = file_code.replace('\\n', '\n')
            full_path = os.path.join(new_folder, file_name)
            directory = os.path.dirname(full_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            with open(full_path, 'w') as file:
                file.write(file_code)
            print(f"Created file: {full_path}\n\n")
        bash_commands = data.get('bash_scripts', [])
        original_cwd = os.getcwd()
        error_message = ""
        combined_command = " && ".join(bash_commands)
        try:
            os.chdir(new_folder)
            print(f"Executed combined bash commands: {combined_command}\n\n")
            subprocess.run(combined_command, shell=True, check=True)
            print(f"Executed combined bash commands: {combined_command}\n\n")
        except subprocess.CalledProcessError as e:
            error_message += f"Error executing command '{combined_command}': {e.output}\n"
        finally:
            os.chdir(original_cwd)




###########################################################################################################



def generate_random_sha256():
    random_bytes = os.urandom(32)  # This generates cryptographically secure random bytes
    sha256_hash = hashlib.sha256(random_bytes)
    return sha256_hash.hexdigest()



# @app.route(f'/{GENERATED_FOLDER}/<path:path>')
# def serve_generated_files(path):
#     return send_from_directory(GENERATED_FOLDER, path)
# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/generate', methods=['POST'])
# def generate():
#     prompt = request.form.get('softwareDescription')
#     if prompt:
#         run_online(prompt)
#         create_files_from_json('data.json', GENERATED_FOLDER)
#         # Instead of redirecting to the generated files, return a JSON response
#         return jsonify({"status": "success", "redirect_url": "http://localhost:5012"})
#     return jsonify({"status": "error", "message": "No prompt provided"}), 400






if __name__ == '__main__':
    # app.run(debug=True, port=5001, host='0.0.0.0')
    prompt = input("Enter your prompt here: ")
    random_sha256 = generate_random_sha256()
    run_online(prompt)
    create_files_from_json('data.json',random_sha256)