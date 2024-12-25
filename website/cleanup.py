import docker
import datetime
import time
import os
import shutil

def stop_and_remove_old_containers():
    client = docker.from_env()
    while True:
        containers = client.containers.list(all=True)
        one_hour_ago = datetime.datetime.now() - datetime.timedelta(hours=1)

        for container in containers:
            created_at = container.attrs['Created']
            created_at = datetime.datetime.strptime(created_at.split('.')[0], '%Y-%m-%dT%H:%M:%S')

            if created_at < one_hour_ago:
                print(f"Stopping and removing container: {container.name}")
                container.stop()
                container.remove()
        
        # Remove folders older than 1 hour in /home/tronmachine/Main
        main_dir = "/home/tronmachine/Main"
        for folder_name in os.listdir(main_dir):
            folder_path = os.path.join(main_dir, folder_name)
            if os.path.isdir(folder_path):
                folder_creation_time = datetime.datetime.fromtimestamp(os.path.getctime(folder_path))
                if folder_creation_time < one_hour_ago:
                    print(f"Removing folder: {folder_path}")
                    shutil.rmtree(folder_path)
        
        time.sleep(3600)  # Sleep for 1 hour before checking again

if __name__ == "__main__":
    stop_and_remove_old_containers()
