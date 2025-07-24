# %%
import os
import sys
import questionary
import numpy as np
from pathlib import Path

from Purple.Data_analysis.plots.heatmaps import plot_heatmaps
from Purple.Data_analysis.plots.session_length import plot_session_length
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

# %%
all_experiments = sorted(experiment_names)

# Create interactive widget for Jupyter notebook
experiment_selector = widgets.SelectMultiple(
    value=[],
    style={'description_width': 'initial'},
    options=all_experiments,
    description='Experiments:',
    disabled=False,
    layout=widgets.Layout(width='auto', height='200px'),
    rows=10
)

display(experiment_selector)

# To get selected values, use: experiment_selector.value

# %%
from Utils.jsun import load_json
import numpy as np
from Purple.Data_analysis.metrics import measure_session_length, measure_mitre_distribution, \
    measure_entropy_session_length, measure_entropy_techniques, measure_entropy_tactics

filter_empty_sessions = False
# %%

selected_experiments = list(experiment_selector.value)
if not selected_experiments:
    print("Nothing selected, exiting.")
    sys.exit(0)

paths = [logs_path / exp for exp in selected_experiments]
print(paths)

sessions_list_list = []
combined_sessions_list = []
reconfig_indices_list = []
for path in paths:
    combined_sessions, sessions_list, reconfig_indices = extract_experiment(path, filter_empty_sessions)
    sessions_list_list.append(sessions_list)
    combined_sessions_list.append(combined_sessions)
    reconfig_indices_list.append(reconfig_indices)

print(json.dumps(sessions_list_list, indent=2))

# %% Tactic distribution
full_tactic_distributions = {}
tactic_distributions = []
session_lengths = []

for i, sessions in enumerate(combined_sessions_list):
    mitre_dist_data = measure_mitre_distribution(sessions)
    tactics = list(mitre_dist_data["tactics"])
    print(mitre_dist_data["tactics"])

    # add to all fields in full_tactic_distributions with the number and tactic in tactics
    for tactic in tactics:
        if tactic not in full_tactic_distributions:
            full_tactic_distributions[tactic] = 0
        full_tactic_distributions[tactic] += mitre_dist_data["tactics"][tactic]

    tactic_distributions.append(mitre_dist_data["tactics"])
    session_lengths.append(measure_session_length(sessions))

# Sort by count in descending order
full_tactic_distributions = dict(sorted(full_tactic_distributions.items(), key=lambda x: x[1], reverse=True))
print(full_tactic_distributions)
print(tactic_distributions)
print(session_lengths)



# %% Plot tactic distribution
plt.figure(figsize=(10, 6))
plt.bar(full_tactic_distributions.keys(), full_tactic_distributions.values(), color=colors.blue)
plt.xlabel("Tactic")
plt.ylabel("Count")
plt.title("Tactic Distribution Across All Experiments")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

# %% plot tactic distribution for all experiments with different colors in a single plot
plt.figure(figsize=(12, 6))

# Get all unique tactics across all experiments and sort by total count (descending)
all_tactics = sorted(full_tactic_distributions.keys(), key=lambda x: full_tactic_distributions[x], reverse=True)

# Create a color map for different experiments
colors_list = ['blue', 'red', 'green', 'orange', 'purple', 'gold']
if len(tactic_distributions) > len(colors_list):
    colors_list = plt.cm.tab10(np.linspace(0, 1, len(tactic_distributions)))

# Set up bar positions
x_positions = np.arange(len(all_tactics))

# Initialize bottom array for stacking
bottom = np.zeros(len(all_tactics))

for i, tactic_distribution in enumerate(tactic_distributions):
    # Get counts for each tactic (0 if not present)
    counts = [tactic_distribution.get(tactic, 0) for tactic in all_tactics]
    
    # Plot stacked bars
    plt.bar(x_positions, counts, 
            bottom=bottom,
            label=f'Experiment {selected_experiments[i]}',
            color=colors_list[i % len(colors_list)])
    
    # Update bottom for next stack
    bottom += counts

plt.xlabel("Tactic")
plt.ylabel("Count")
plt.title("Tactic Distribution Across All Experiments (Stacked)")
plt.xticks(x_positions, all_tactics, rotation=45, ha='right')
plt.legend()
plt.tight_layout()
plt.show()

# %% table of tactic distribution
# should be experiment, sessionlength, and all tactics (%) as columns and a total one in the end
import numpy as np
import pandas as pd
tactic_distribution_df = pd.DataFrame(tactic_distributions)
for x in session_lengths:
    print(x['mean'])
tactic_distribution_df["session_length"] = [sl['mean'] for sl in session_lengths]
tactic_distribution_df["experiment"] = selected_experiments
tactic_distribution_df = tactic_distribution_df.set_index("experiment")
tactic_distribution_df = tactic_distribution_df.reindex(columns=["session_length"] + list(full_tactic_distributions.keys()) + ["total"])
tactic_distribution_df["total"] = tactic_distribution_df.sum(axis=1)
tactic_distribution_df = tactic_distribution_df.apply(lambda x: x / x["total"] * 100, axis=1)
tactic_distribution_df = tactic_distribution_df.round(2)
tactic_distribution_df = tactic_distribution_df.fillna(0)
tactic_distribution_df = tactic_distribution_df.fillna(0)

# create sum for session length and average for each tactic
tactic_distribution_df.loc["Total"] = tactic_distribution_df.sum(numeric_only=True)
tactic_distribution_df.loc["Total", "session_length"] = tactic_distribution_df["session_length"].mean()
tactic_distribution_df = tactic_distribution_df.round(2)
print(tactic_distribution_df)

tactic_distribution_df.to_csv(logs_path / "tactic_distribution.csv")

# %% Honeypot deceptiveness
# table of model of HP/experiment, detection, no detection, session length befor discovery and average session length


# %% Average session length over time (restart each configuration)

# %% Average Levenshtein distance over time (restart each configuration)

# %% Set of sequences over time
unique_session_list = []
unique_session_list_list = []
for i, comb_session in enumerate(combined_sessions_list):
    unique_session = set()
    _usll = []
    for session in comb_session:
        unique_session.add(session['tactics'])
        _usll.append(len(unique_session))
    unique_session_list.append(unique_session)
    unique_session_list_list.append(_usll)
print(unique_session_list)
print([len(sessions) for sessions in combined_sessions_list if sessions])
print([len(sessions) for sessions in unique_session_list])

for a in unique_session_list_list:
    print((a))

plt.figure(figsize=(12, 6))
for usl in unique_session_list_list:
    plt.plot(usl, marker='o', linestyle='-', alpha=0.5)


# %% Average Levenshtein distance over time (no restart)

# %% Tokens used per experiment

