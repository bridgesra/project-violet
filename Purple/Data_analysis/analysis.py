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
from Purple.Data_analysis.utils import extract_experiment

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
    measure_entropy_session_length, measure_entropy_techniques, measure_entropy_tactics


path = logs_path / selected_experiment

combined_sessions, sessions_list, reconfig_indices = extract_experiment(path, filter_empty_sessions, use_omni_sessions)

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



#%% Plotting cumulative attack of unique techniqes vs sessions

from Purple.Data_analysis.plots import plot_mitre_data, plot_session_length, plot_heatmaps

plot_mitre_data(combined_sessions, reconfig_indices)
plot_session_length(combined_sessions, reconfig_indices)
plot_heatmaps(combined_sessions, reconfig_indices)

# %%
from matplotlib.ticker import MultipleLocator, FuncFormatter

tactics = list(mitre_dist_data["tactics"].keys())
import matplotlib
colors_tab20 = plt.get_cmap("tab10").colors + plt.get_cmap("tab20b").colors 
heatmap = np.hstack([
    mitre_dist_data["tactics_heatmap"]
])
plt.plot(heatmap.T)
plt.figure(figsize=(12,7))
bottom = np.zeros(heatmap.shape[1])
for tactic, row, color in zip(tactics, heatmap, colors_tab20):
    plt.bar(range(len(row)), row, bottom=bottom, label=tactic,
        color=color, width=1, edgecolor=colors.black, linewidth=0.5)
    bottom += row
plt.xlabel("Session")
plt.ylabel("Session length")
ax = plt.gca()

ax.xaxis.set_major_formatter(
    FuncFormatter(lambda x, pos: f"{int(x+6)}" if ((x + 0.5)%10 == 0) else "")
)

ax.yaxis.set_major_formatter(
    FuncFormatter(lambda x, pos: f"{int(x)}" if (x % 10 == 0) else "")
)

ax.tick_params(
    axis='x',          # x‐axis
    which='both',      # both major and minor
    bottom=True,       # ticks on bottom
    top=False,         # no ticks on top
    labelbottom=True, # no labels
    length=3 ,         # length of the tick‐marks

)
ax.tick_params(
    axis='y',          # y‐axis
    which='both',
    left=True,
    right=False,
    labelleft=True,
    length=3
)
ax.xaxis.set_major_locator(MultipleLocator(1, 0.5))
ax.yaxis.set_major_locator(MultipleLocator(1))
#ax.yaxis.set_minor_locator(MultipleLocator(0.5))





plt.legend(fontsize="small")
plt.show()

# %% Tokens vs session
configs = [name for name in os.listdir(path) if str(name).startswith("hp_config")]
tokens_list = [load_json(path / config / "tokens_used.json") for config in configs]
token_reconfig_indices= np.cumsum([len(tokens) for tokens in tokens_list][:-1])
combined_tokens = sum(tokens_list, [])

prompt_tokens = [tokens["prompt_tokens"] for tokens in combined_tokens]
cached_tokens = [tokens["cached_tokens"] for tokens in combined_tokens]
completion_tokens = [tokens["completion_tokens"] for tokens in combined_tokens]

plt.figure(figsize=(12, 6))
plt.bar(range(len(prompt_tokens)), prompt_tokens,label="prompt tokens")
# plt.bar(range(len(cached_tokens)), prompt_tokens,label="cached tokens")
plt.bar(range(len(completion_tokens)), completion_tokens, label="completion tokens")
plt.title("Tokens per Session")
plt.xlabel("Session")
plt.ylabel("Session length")

for index in token_reconfig_indices:
    plt.axvline(index - 0.5, color=colors.black, linestyle="--", alpha=0.2)

# plt.grid()
plt.ylim(bottom=0)
plt.legend()
plt.show()
# test


# %%

# your data
tactics = list(mitre_dist_data["tactics"].keys())
values  = list(mitre_dist_data["tactics"].values())

plt.figure(figsize=(10, 5))
bars = plt.bar(range(len(tactics)), values)
plt.xticks(range(len(tactics)), tactics, rotation=70)

# add value labels on top of each bar
for bar in bars:
    height = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width()/2,  # x position: center of the bar
        height,                           # y position: top of the bar
        f'{height}',                      # label text
        ha='center',                      # horizontal alignment
        va='bottom'                       # vertical alignment
    )

plt.tight_layout()
plt.show()


# %%

# Simple moving average
def moving_average(x, w):
    return np.convolve(x, np.ones(w), 'valid') / w

eps = 5e-3
window_size = 2
smoothed = moving_average(entropy_techniques_data["entropies"], window_size)
diffs = np.abs(np.diff(smoothed, prepend=np.ones((window_size,)) * np.inf))

# %%
