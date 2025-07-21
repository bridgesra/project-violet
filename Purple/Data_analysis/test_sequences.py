#%%

import os
import sys
import numpy as np
from pathlib import Path
# Add parent directory to sys.path to allow imports from project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)
import ipywidgets as widgets
from IPython.display import display
from Style import colors
import json
import pprint
import matplotlib.pyplot as plt
from Purple.RagData.retrive_techniques import retrieve_unique_techniques

logs_path = Path(__file__).resolve().parent.parent.parent / "logs"
experiment_names = os.listdir(logs_path)[::-1]

dropdown = widgets.Dropdown(
    options=experiment_names,
    description="Pick an experiment to analyze:",
)

display(dropdown)

#%%

selected_experiment = dropdown.value
filter_empty_sessions = False
use_omni_sessions = False
print(f"Analyzing experiment {selected_experiment}")

from Utils.jsun import load_json
import numpy as np
from Purple.Data_analysis.metrics import measure_session_length, measure_mitre_distribution, \
    measure_entropy_session_length, measure_entropy_techniques, measure_entropy_tactics, \
    measure_sequences

path = logs_path / selected_experiment
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
print(f"Reconfig indices: {reconfig_indices}")
print(f"Number of sessions: {len(combined_sessions)}")

length_data = measure_session_length(combined_sessions)
mitre_dist_data = measure_mitre_distribution(combined_sessions)
session_mitre_dist_data = [measure_mitre_distribution(session) for session in sessions_list]

entropy_tactics_data = measure_entropy_tactics(combined_sessions)
session_entropy_tactics_data = [measure_entropy_tactics(session) for session in sessions_list]

entropy_techniques_data = measure_entropy_techniques(combined_sessions)
session_entropy_techniques_data = [measure_entropy_techniques(session) for session in sessions_list]

entropy_session_length_data = measure_entropy_session_length(combined_sessions)
session_entropy_session_length_data = [measure_entropy_session_length(session) for session in sessions_list]


# %%
import Levenshtein
from itertools import combinations
sequence_data = measure_sequences(combined_sessions)
print(sequence_data["indexed_tactic_sequences"])
distances = []
for i, j in combinations(
        sequence_data["indexed_tactic_sequences"],
        2
    ):
    distances.append(Levenshtein.distance(i,j))

plt.plot(sorted(distances, reverse=True))

# %%
