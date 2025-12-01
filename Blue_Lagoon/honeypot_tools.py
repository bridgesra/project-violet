import subprocess
import os

runid = os.environ.get("RUNID")
openai_key = os.environ.get("OPENAI_API_KEY")
together_key = os.environ.get("TOGETHER_AI_SECRET_KEY")
hp_model = os.environ.get("HP_MODEL")

def start_dockers():
    print("Starting Docker containers...")
    
    # Create environment with all variables
    env = os.environ.copy()
    env.update({
        "RUNID": runid,
        "OPENAI_API_KEY": openai_key, 
        "TOGETHER_AI_SECRET_KEY": together_key,
        "HP_MODEL": hp_model
    })
    
    subprocess.run(
        ["docker", "compose", "-f", "docker-compose.yml", "-p", runid, "build"],
        check=True,
        env=env
    )
    subprocess.run(
        ["docker", "compose", "-f", "docker-compose.yml", "-p", runid, "up", "-d"],
        check=True,
        env=env
    )
    print("Docker containers started")

def stop_dockers():
    print("Stopping Docker containers...")
    
    env = os.environ.copy()
    env.update({
        "RUNID": runid,
        "OPENAI_API_KEY": openai_key,
        "TOGETHER_AI_SECRET_KEY": together_key, 
        "HP_MODEL": hp_model
    })
    
    subprocess.run(
        ["docker", "compose", "-f", "docker-compose.yml", "-p", runid, "down"],
        check=True,
        env=env
    )
    print("Docker containers stopped")
    
    subprocess.run(
        ["docker", "image", "prune", "-f"], 
        check=True, 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL
    )

# If you need to call these functions directly
if __name__ == "__main__":
    start_dockers()
    # or stop_dockers()