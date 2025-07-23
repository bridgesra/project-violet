import subprocess
import os

def start_dockers():
    print("Starting Docker containers...")
    subprocess.run(["sudo", f"RUNID={os.environ.get("RUNID")}", f"OPENAI_API_KEY={os.environ.get("OPENAI_API_KEY")}", f"TOGETHER_AI_SECRET_KEY={os.environ.get("TOGETHER_AI_SECRET_KEY")}", f"HP_MODEL={os.environ.get("HP_MODEL")}", "docker-compose","-f", f"docker-compose.yml", "-p", os.environ.get("RUNID"), "build"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", f"RUNID={os.environ.get("RUNID")}", f"OPENAI_API_KEY={os.environ.get("OPENAI_API_KEY")}", f"TOGETHER_AI_SECRET_KEY={os.environ.get("TOGETHER_AI_SECRET_KEY")}", f"HP_MODEL={os.environ.get("HP_MODEL")}", "docker-compose", "-f", f"docker-compose.yml", "-p", os.environ.get("RUNID"), "up", "-d"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Docker containers started")


def stop_dockers():
    print("Stopping Docker containers...")
    subprocess.run(["sudo", f"RUNID={os.environ.get("RUNID")}", f"OPENAI_API_KEY={os.environ.get("OPENAI_API_KEY")}", f"TOGETHER_AI_SECRET_KEY={os.environ.get("TOGETHER_AI_SECRET_KEY")}", f"HP_MODEL={os.environ.get("HP_MODEL")}", "docker-compose", "-f", f"docker-compose.yml", "-p", os.environ.get("RUNID"),"down"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Docker containers stopped")
    subprocess.run(["sudo", "docker", "image", "prune", "-f"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

