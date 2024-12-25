import docker
import subprocess
from pathlib import Path
import time
import requests

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
        self.container_script = """
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

class CustomHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        response = f"Hello from Container {os.environ.get('CONTAINER_NUMBER', 'Unknown')}"
        self.wfile.write(response.encode())

httpd = HTTPServer(('0.0.0.0', 8000), CustomHandler)
print('Server running...')
httpd.serve_forever()
"""

    def create_python_container(self, container_number):
        """Create and run a Python HTTP server container"""
        container_name = f"python_http_{container_number}"
        
        # Create a temporary directory for the Python script
        script_path = Path(f"/tmp/{container_name}")
        script_path.mkdir(exist_ok=True)
        
        # Write the Python HTTP server script
        with open(script_path / "server.py", "w") as f:
            f.write(self.container_script)
        
        # Build and run the container
        dockerfile_content = """
FROM python:3.9-slim
WORKDIR /app
COPY server.py .
ENV CONTAINER_NUMBER={}
CMD ["python", "server.py"]
""".format(container_number)
        
        with open(script_path / "Dockerfile", "w") as f:
            f.write(dockerfile_content)
        
        # Build the image
        image, _ = self.client.images.build(
            path=str(script_path),
            tag=f"python_http_{container_number}"
        )
        
        # Run the container
        container = self.client.containers.run(
            image.id,
            name=container_name,
            detach=True
        )
        
        return container

    def get_container_ip(self, container):
        """Get container IP address"""
        container.reload()  # Refresh container info
        return container.attrs['NetworkSettings']['Networks']['bridge']['IPAddress']

    def update_nginx_config(self, containers):
        """Update Nginx configuration using container IPs"""
        # Generate location blocks using container IPs
        location_blocks = []
        for i, container in enumerate(containers, 1):
            container_ip = self.get_container_ip(container)
            location_blocks.append(f"""        location /container{i} {{
            proxy_pass http://{container_ip}:8000/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }}""")
        
        # Join all location blocks
        location_blocks_str = "\n".join(location_blocks)
        
        # Create the complete Nginx configuration with public IP
        nginx_config = self.base_nginx_config % (self.public_ip, location_blocks_str)
        
        # Write the configuration file
        with open("/etc/nginx/nginx.conf", "w") as f:
            f.write(nginx_config)
        
        # Reload Nginx
        subprocess.run(["nginx", "-s", "reload"])

    def create_containers(self, count):
        """Create specified number of containers and configure Nginx"""
        # Create containers
        containers = []
        for i in range(1, count + 1):
            container = self.create_python_container(i)
            containers.append(container)
            print(f"Created container {i}")
            
            # Wait for container to start
            time.sleep(2)
        
        # Update Nginx configuration with container IPs
        self.update_nginx_config(containers)
        print("Nginx configuration updated")
        
        return containers

def main():
    automation = DockerNginxAutomation()
    container_count = int(input("Enter the number of containers to create: "))
    containers = automation.create_containers(container_count)
    
    print("\nContainers created successfully!")
    print(f"You can access them from any computer at:")
    for i in range(1, container_count + 1):
        print(f"http://{automation.public_ip}/container{i}")
    
    print("\nContainer IPs:")
    for i, container in enumerate(containers, 1):
        ip = automation.get_container_ip(container)
        print(f"Container {i}: {ip}")

if __name__ == "__main__":
    main()