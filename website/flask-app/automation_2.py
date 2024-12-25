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

    def create_container(self, container_name):
        """Create and run a container using existing Dockerfile"""
        try:
            # Build the image using the Dockerfile in the current directory
            image, _ = self.client.images.build(
                path=".",  # Uses Dockerfile from current directory
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
            proxy_pass http://{container_ip}:5000/;
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

def main():
    automation = DockerNginxAutomation()
    
    # Get container name from user
    container_name = input("Enter the name for the new container: ")
    
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

if __name__ == "__main__":
    main()