import docker
import subprocess
from pathlib import Path
import time
import requests
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
import google.generativeai as genai
import json
import os
import threading
import socket
import hashlib
from flask_cors import CORS



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
        error_message = ""
        filtered_commands = [cmd for cmd in bash_commands if 'docker' not in cmd]
        combined_command = " && ".join(filtered_commands)
        try:
            os.chdir(new_folder)
            if combined_command:  # Only run if there are commands to execute
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




class DockerNginxAutomation:
    def __init__(self):
        self.client = docker.from_env()
        # Get public IP of the Azure VM
        self.public_ip = requests.get('https://api.ipify.org').text
        self.base_nginx_config = """
events {
    worker_connections 1024;
}

http {
    server_names_hash_bucket_size 64;
    
    server {
        listen 80;
        listen [::]:80;
        server_name %s;  # Will be replaced with public IP

        # Enable access from any IP
        location / {
            allow all;
        }

        %s
    }
}
"""

    def create_container(self, container_name):
        """Create and run a container using existing Dockerfile"""
        try:
            # Build the image using the Dockerfile in the current directory
            image, _ = self.client.images.build(
                path=f"{container_name}",  # Uses Dockerfile from current directory
                tag=f"custom_{container_name}"
            )
            
            # Run the container
            container = self.client.containers.run(
                image.id,
                name=container_name,
                detach=True
            )
            
            print(f"Container '{container_name}' created successfully")
            return container
            
        except docker.errors.BuildError as e:
            print(f"Error building image: {e}")
            return None
        except docker.errors.APIError as e:
            print(f"Error creating container: {e}")
            return None

    def get_container_ip(self, container):
        """Get container IP address"""
        container.reload()  # Refresh container info
        return container.attrs['NetworkSettings']['Networks']['bridge']['IPAddress']

    def update_nginx_config(self, container, container_name):
        """Update Nginx configuration for the new container"""
        container_ip = self.get_container_ip(container)
        
        # Generate location block for the container with container name in the path
        location_block = f"""        location /{container_name} {{
            proxy_pass http://{container_ip}:5100/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Remove the container name prefix from the URI
            rewrite ^/{container_name}(/.*)$ $1 break;
            rewrite ^/{container_name}$ / break;
        }}"""
        
        # Create the complete Nginx configuration
        nginx_config = self.base_nginx_config % (self.public_ip, location_block)
        
        # Write the configuration file
        with open("/etc/nginx/nginx.conf", "w") as f:
            f.write(nginx_config)
        
        # Reload Nginx
        subprocess.run(["nginx", "-s", "reload"])
        print("Nginx configuration updated")


app = Flask(__name__)
CORS(app)

@app.route('/generate', methods=['POST'])
def generate():
    prompt = request.form.get('userInput')
    if prompt:
        random_sha256 = generate_random_sha256()
        print("Running online")
        run_online(prompt, random_sha256)
        print("Creating files")
        create_files_from_json(f'{random_sha256}.json', random_sha256)
        print("Creted Files")
        automation = DockerNginxAutomation()
        print("Creating Contianer")
        # Get container name from user
        container_name = random_sha256
        
        # Create the container
        container = automation.create_container(container_name)
        
        if container:
            # Wait briefly for container to start
            time.sleep(2)
            
            # Update Nginx configuration with container name
            automation.update_nginx_config(container, container_name)
            
            # Print access information
            print("\nContainer created successfully!")
            print(f"Container IP: {automation.get_container_ip(container)}")
            print(f"You can access it from any computer at: http://{automation.public_ip}/{container_name}")
        else:
            print("Failed to create container. Please check if the Dockerfile exists in the current directory.")
        return jsonify({"status": "success", "redirect_url": f"http://{automation.public_ip}/{random_sha256}"})
    return jsonify({"status": "error", "message": "No prompt provided"}), 400

if __name__ == "__main__":
    app.run(debug=True, port=5001, host='0.0.0.0',threaded=True)