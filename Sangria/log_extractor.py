import subprocess
import datetime
import json
import os

last_checked = datetime.datetime.now(datetime.UTC).isoformat()
def get_new_hp_logs():
    """
    Fetch new logs from the Beelzebub container since the last check.
    Returns a list of parsed JSON objects or raw logs if parsing fails.
    """
    global last_checked
    process = subprocess.Popen(
        ["docker", "logs", f"{os.getenv('RUNID')}-blue_lagoon-1", "--since", last_checked],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    last_checked = datetime.datetime.now(datetime.UTC).isoformat()

    log_output = process.stdout.read().strip()
    if log_output:
        logs = []
        log_lines = log_output.strip().split('\n')

        for line in log_lines:
            line = line.strip()
            if not line:
                continue

            try:
                # Try to parse line as JSON
                parsed = json.loads(line)
                logs.append(parsed)
            except json.JSONDecodeError:
                # Skip non-JSON lines (ASCII art, banners, etc.)
                continue

        return logs  # Always returns a list

    return []  # Always returns a list 
