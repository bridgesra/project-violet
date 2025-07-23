import re
import numpy as np
import uuid
from datetime import datetime, timezone
from pathlib import Path
import os


def extract_json(text):
    """
    Extract a JSON object from a string using regex. Returns the JSON string or the original text if not found.
    """
    match = re.search(r'({[\s\S]+})', text)
    return match.group(1) if match else text.strip()

def cosine_similarity(a, b):
    """
    Compute the cosine similarity between two vectors a and b.
    """
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def clean_and_finalize_config(config):
    """
    Clean up and finalize the generated config: remove schema/title, assign a new UUID, timestamp, and fix service fields.
    """
    config.pop("$schema", None)
    config.pop("title", None)
    config["id"] = str(uuid.uuid4())
    config["timestamp"] = datetime.now(timezone.utc).isoformat()
    for service in config.get("services", []):
        service.pop("id", None)
        if service.get("protocol") in ["http", "ssh"]:
            if "plugin" not in service:
                service["plugin"] = None
        else:
            service.pop("plugin", None)
    return config
    


def acquire_config_lock():
    """
    Acquire an exclusive lock for honeypot configuration operations.
    Returns the lock file object.
    """
    target_dir = Path(__file__).resolve().parent.resolve().parent / "Blue_Lagoon" / "configurations" / "services"
    target_dir.mkdir(parents=True, exist_ok=True)
    lock_file_path = target_dir / ".config_lock"
    lock_file = open(lock_file_path, "w")
    if os.name == "posix":
        import fcntl
        print("acquiring lock")
        fcntl.lockf(lock_file.fileno(), fcntl.LOCK_EX)
        print("lock acquired")
    return lock_file


def release_config_lock(lock_file):
    """
    Release the configuration lock and close the lock file.
    
    Args:
        lock_file: The lock file object to release
        context: Optional context string for logging
    """
    if os.name == "posix":
        import fcntl
        print("releasing lock")
        fcntl.lockf(lock_file.fileno(), fcntl.LOCK_UN)
        print("lock released")
    lock_file.close()

