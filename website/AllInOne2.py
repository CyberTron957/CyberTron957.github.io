import docker
import subprocess
from pathlib import Path
import time
import requests
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import json
import os
import threading
import hashlib
from flask_cors import CORS

# Utility Functions
def run_online(prompt,name):
    genai.configure(api_key='AIzaSyBFz5_rw43RviSZbWo8ieoi83NNTKKZOAQ')
    # port = get_free_port()
    initial_content = f'''

You are tasked with developing a fully production-ready software application or program designed to run on my ubuntu server. Follow these detailed instructions carefully to ensure the generated output is complete, error-free, and meets all requirements.

Key Requirements:
Backend Framework:

Use Flask for the back-end and adhere to the following structure:
A separate folder named templates for HTML files.
User Interface:

Create a modern, accessible UI.
Dependencies:

Provide a requirements.txt file containing all necessary Python modules without specifying versions.
Compatibility:

All generated code must be fully compatible with ubuntu server, including imports and bash commands.

Reliability:

The code must be production-ready, error-free, and adhere to best practices.
Output Structure:
Your output should be a JSON file containing the following:

File Names:

A list of all files to be created.
File Contents:

The complete code for each file, ensuring proper folder structure (e.g., templates folder for Flask apps).
Containerization:

Include a Dockerfile. But do NOT provide necessary bash commands to build and run the container.
Bash Commands:

A separate section with all required bash commands.

Additional Notes:
Double-check that the following are included if relevant:
A templates folder for HTML files if Flask is used.
Proper imports for Ubuntu compatibility.
A Dockerfile without necessary bash commands to build and run the container.
Do not forget to add --host=0.0.0.0 to the flask run command.
Validate the output thoroughly to ensure no critical steps or files are missing.

Run the app on the following port: 5100
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
        with open(f'{name}.json', 'w') as json_file:
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
        filtered_commands = [cmd for cmd in bash_commands if 'docker' not in cmd]
        combined_command = " && ".join(filtered_commands)
        try:
            os.chdir(new_folder)
            if combined_command:
                subprocess.run(combined_command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error executing command '{combined_command}': {e}")
        finally:
            os.chdir(original_cwd)

def generate_random_sha256():
    random_bytes = os.urandom(32)
    sha256_hash = hashlib.sha256(random_bytes)
    return sha256_hash.hexdigest()

# DockerNginxAutomation Class
class DockerNginxAutomation:
    def __init__(self):
        self.client = docker.from_env()
        self.public_ip = requests.get('https://api.ipify.org').text
        self.base_nginx_config = """
events {
    worker_connections 1024;
}
http {
    server_names_hash_bucket_size 64;
    server {
        listen 80;
        server_name %s;
        location / {
            allow all;
        }
        %s
    }
}
"""

    def create_container(self, container_name):
        try:
            image, _ = self.client.images.build(
                path=f"{container_name}",
                tag=f"custom_{container_name}"
            )
            container = self.client.containers.run(
                image.id,
                name=container_name,
                detach=True
            )
            print(f"Container '{container_name}' created successfully")
            return container
        except (docker.errors.BuildError, docker.errors.APIError) as e:
            print(f"Error creating container: {e}")
            return None

    def get_container_ip(self, container):
        container.reload()
        return container.attrs['NetworkSettings']['Networks']['bridge']['IPAddress']

    def update_nginx_config(self, container, container_name):
        container_ip = self.get_container_ip(container)
        location_block = f"""
        location /{container_name} {{
            proxy_pass http://{container_ip}:5100/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            rewrite ^/{container_name}(/.*)$ $1 break;
            rewrite ^/{container_name}$ / break;
        }}"""
        nginx_config = self.base_nginx_config % (self.public_ip, location_block)
        with open("/etc/nginx/nginx.conf", "w") as f:
            f.write(nginx_config)
        subprocess.run(["nginx", "-s", "reload"])
        print("Nginx configuration updated")

# Flask App Configuration


app = Flask(__name__)
CORS(app)

container_status = {}


def process_container(prompt, random_sha256):
    try:
        container_status[random_sha256] = {"status": "in_progress", "redirect_url": None}
        print("Running online")
        run_online(prompt, random_sha256)
        print("Creating files")
        create_files_from_json(f'{random_sha256}.json', random_sha256)
        automation = DockerNginxAutomation()
        print("Creating Container")
        container_name = random_sha256
        container = automation.create_container(container_name)
        if container:
            time.sleep(2)
            automation.update_nginx_config(container, container_name)
            print("\nContainer created successfully!")
            redirect_url = f"http://{automation.public_ip}/{container_name}"
            container_status[random_sha256] = {"status": "complete", "redirect_url": redirect_url}
        else:
            container_status[random_sha256] = {"status": "failed", "redirect_url": None}
    except Exception as e:
        print(f"Error in container creation: {e}")
        container_status[random_sha256] = {"status": "failed", "redirect_url": None}

@app.route('/generate', methods=['POST'])
def generate():
    prompt = request.form.get('userInput')
    if prompt:
        random_sha256 = generate_random_sha256()
        container_status[random_sha256] = {"status": "queued", "redirect_url": None}
        threading.Thread(target=process_container, args=(prompt, random_sha256), daemon=True).start()
        return jsonify({"status": "success", "message": "Container creation started", "task_id": random_sha256})
    return jsonify({"status": "error", "message": "No prompt provided"}), 400

@app.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    status = container_status.get(task_id, {"status": "unknown", "redirect_url": None})
    return jsonify(status)


if __name__ == "__main__":
    app.run(debug=True, port=5001, host='0.0.0.0', threaded=True)
