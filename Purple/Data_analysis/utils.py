# %%
import os
from pathlib import Path
import numpy as np
from Utils.jsun import load_json

def extract_experiment(path, filter_empty_sessions, use_omni_sessions=False):
    configs = [name for name in os.listdir(path) if str(name).startswith("hp_config")]
    configs = sorted(
        configs,
        key=lambda fn: int(Path(fn).stem.split('_')[-1])
    )

    session_file_name = "omni_sessions.json" if use_omni_sessions else "sessions.json"
    sessions_list = [load_json(path / config / session_file_name) for config in configs if session_file_name in os.listdir(path / config)]

    if filter_empty_sessions:
        new_sessions_list = []
        for config_sessions in sessions_list:
            new_sessions_list.append([session for session in config_sessions if session["session"]])
        sessions_list = new_sessions_list

    reconfig_indices = np.cumsum([len(session) for session in sessions_list][:-1])
    combined_sessions = sum(sessions_list, [])

    return combined_sessions, sessions_list, reconfig_indices

# %%
