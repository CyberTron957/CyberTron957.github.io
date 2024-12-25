import os
import subprocess

def create_container(image_name):
    # Run the container and get its ID
    container_id = subprocess.check_output(
        ["docker", "run", "-d", image_name]
    ).strip().decode('utf-8')
    return container_id

def get_container_ip(container_id):
    # Inspect container to get its IP address
    container_ip = subprocess.check_output(
        ["docker", "inspect", "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", container_id]
    ).strip().decode('utf-8')
    return container_ip

def create_nginx_config(subdomain, container_ip, container_port):
    config_file = f"/opt/homebrew/etc/nginx/conf.d/{subdomain}.conf"
    config_content = f"""
    server {{
        listen 80;
        server_name {subdomain};

        location / {{
            proxy_pass http://{container_ip}:{container_port};
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }}
    }}
    """
    with open(config_file, 'w') as f:
        f.write(config_content)

    # Reload NGINX to apply the configuration
    subprocess.run(["nginx", "-s", "reload"])

# Main Workflow
image_name = "user1_app"
subdomain = "localhost/hellobro"
container_port = 8000  # The app's port inside the container

# Create container and fetch details
container_id = create_container(image_name)
container_ip = get_container_ip(container_id)
print(container_ip)
# Map subdomain to container
#create_nginx_config(subdomain, container_ip, container_port)
print(f"Subdomain {subdomain} is now mapped to {container_ip}:{container_port}")
