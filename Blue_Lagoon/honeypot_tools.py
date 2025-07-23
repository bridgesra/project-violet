import subprocess
import os

runid = os.environ.get("RUNID")
openai_key = os.environ.get("OPENAI_API_KEY")
together_key = os.environ.get("TOGETHER_AI_SECRET_KEY")
hp_model = os.environ.get("HP_MODEL")

def start_dockers():
    print("Starting Docker containers...")
    subprocess.run(["sudo", f"RUNID={runid}", f"OPENAI_API_KEY={openai_key}", f"TOGETHER_AI_SECRET_KEY={together_key}", f"HP_MODEL={hp_model}", "docker-compose","-f", f"docker-compose.yml", "-p", os.environ.get("RUNID"), "build"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", f"RUNID={runid}", f"OPENAI_API_KEY={openai_key}", f"TOGETHER_AI_SECRET_KEY={together_key}", f"HP_MODEL={hp_model}", "docker-compose", "-f", f"docker-compose.yml", "-p", os.environ.get("RUNID"), "up", "-d"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Docker containers started")


def stop_dockers():
    print("Stopping Docker containers...")
    subprocess.run(["sudo", f"RUNID={runid}", f"OPENAI_API_KEY={openai_key}", f"TOGETHER_AI_SECRET_KEY={together_key}", f"HP_MODEL={hp_model}", "docker-compose", "-f", f"docker-compose.yml", "-p", os.environ.get("RUNID"),"down"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Docker containers stopped")
    subprocess.run(["sudo", "docker", "image", "prune", "-f"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

