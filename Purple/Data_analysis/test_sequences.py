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
    measure_tactic_sequences, measure_technique_sequences, measure_command_sequences

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
sequence_data = measure_tactic_sequences(combined_sessions)

# %%
sequence_data = measure_tactic_sequences(combined_sessions)
plt.plot(sequence_data["min_distances"])
plt.show()

# %%
import editdistance
from collections import Counter
from itertools import combinations

print(sequence_data["indexed_sequences"])
print(len([seq for seq in sequence_data["indexed_sequences"] if seq]))
distances = []
for i, j in combinations(
        [seq for seq in sequence_data["indexed_sequences"] if seq],
        2
    ):
    distances.append(editdistance.eval(i,j))
distances = np.array(distances)
freq = Counter(distances)

import numpy as np
from scipy.stats import t

def compute_confidence_interval(session_lengths: np.ndarray, alpha: float) -> float:
    s = session_lengths.std(ddof=1)
    n = session_lengths.shape[0]

    t_crit = t.ppf(1 - alpha/2, df=n - 1)
    moe = t_crit * (s / np.sqrt(n))

    return float(moe)

# prepare data for plotting
x = sorted(freq.keys())
y = [freq[d] for d in x]

# plot
plt.bar(x, y, align='center', width=0.8)
plt.axvline(np.mean(distances), color="k")
plt.xlabel('Levenshtein distance')
plt.ylabel('Count')
plt.title('Distribution of Pairwise Sequence Distances')
plt.show()

mean_dist = np.mean(distances)
moe = compute_confidence_interval(distances, 0.05)


# %%
from collections import Counter
dists = Counter()
dists_list = []
margins = []
mus = []
import editdistance
eps = 2
eps = []

for i in range(len(sequence_data["indexed_sequences"])):
    for j in range(0, i):
        seq_i = sequence_data["indexed_sequences"][i]
        seq_j = sequence_data["indexed_sequences"][j]
        if seq_i and seq_j:
            dist = editdistance.eval(seq_i, seq_j)
            dists.update([dist])
            dists_list.append(dist)
    eps.append(0.003 * np.var(dists_list))
    moe = compute_confidence_interval(np.array(dists_list), 0.05)
    margins.append(moe)
    mus.append(np.mean(dists_list))
mus = np.array(mus)
margins = np.array(margins)
eps = np.array(eps)[-1]
window_size = 10
mask = (margins < eps) & (np.array([False] * window_size + [True] * (len(mus) - window_size)))
values = np.array(range(len(mus)))

plt.errorbar(values, mus, margins)
plt.scatter(values[mask], mus[mask], color="red")
plt.xlabel("Sequence")
plt.ylabel("Mean")
plt.show()

# %%

pprint.pprint(sequence_data)
# %%

session_all_lengths = [measure_session_length(session)["session_lengths"] for session in sessions_list]
n = len(combined_sessions) // 2
fake_sessions_list = [combined_sessions[i:i + n] for i in range(0, len(combined_sessions), n)]
session_all_lengths = [measure_session_length(session)["session_lengths"] for session in fake_sessions_list]
margins = []
mus = []
eps = 10
eps = []

for session_lengths in session_all_lengths:
    print(session_lengths)
    for i in range(len(session_lengths)):
        moe = compute_confidence_interval(session_lengths[0:i], 0.05)
        margins.append(moe)
        mus.append(np.mean(session_lengths[0:i]))
        eps.append(0.003 * np.var(session_lengths[0:i]))

mus = np.array(mus)
margins = np.array(margins)
eps = np.array(eps)

window_size = 5
eps = 10
mask = (margins <= eps)
values = np.array(range(len(mus)))

plt.ylim(-5, 100)
plt.errorbar(values, mus, margins)
plt.scatter(values[mask], mus[mask], color="red")
plt.xlabel("Sequence")
plt.ylabel("Mean")
plt.scatter(values, length_data["session_lengths"], color="orange", s=1)
plt.show()
print(mus * mask)

# %%
