# %%
import os
import sys
import numpy as np
from pathlib import Path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from Purple.Data_analysis.plots.heatmaps import plot_heatmaps
from Purple.Data_analysis.plots.session_length import plot_session_length
from Purple.Data_analysis.utils import extract_experiment, compute_confidence_interval
# Add parent directory to sys.path to allow imports from project root
import ipywidgets as widgets
from IPython.display import display
from Purple.Data_analysis import colors
import json
import matplotlib.pyplot as plt
from Purple.RagData.retrive_techniques import retrieve_unique_techniques
import editdistance

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

filter_empty_sessions = True
# %%

selected_experiments = list(experiment_selector.value)
if not selected_experiments:
    print("Nothing selected, exiting.")
    sys.exit(0)

paths = [logs_path / exp for exp in selected_experiments]

sessions_list_list = []
combined_sessions_list = []
reconfig_indices_list = []
total_sessions = 0
labeled_commands = 0
for path in paths:
    combined_sessions, sessions_list, reconfig_indices = extract_experiment(path, filter_empty_sessions)
    sessions_list_list.append(sessions_list)
    combined_sessions_list.append(combined_sessions)
    reconfig_indices_list.append(reconfig_indices)

    total_sessions += len(combined_sessions)
    labeled_commands += sum(len(session.get("full_session", [])) for session in combined_sessions)
print("total sessions:", total_sessions)
print("labeled commands:", labeled_commands)

# %% Tactic distribution
from Purple.Data_analysis.metrics import measure_tactic_sequences, measure_technique_sequences, measure_command_sequences
for i, combined_sessions in enumerate(combined_sessions_list):
    sequence_data = measure_tactic_sequences(combined_sessions)

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

# %% plot tactic distribution for all experiments with different colors in a single plot
plt.figure(figsize=(10, 5))

# Get all unique tactics across all experiments and sort by total count (descending)
all_tactics = sorted(full_tactic_distributions.keys(), key=lambda x: full_tactic_distributions[x], reverse=True)

# Set up bar positions
x_positions = np.arange(len(all_tactics))

# Initialize bottom array for stacking
bottom = np.zeros(len(all_tactics))

# Keep track of labels we've already added to legend
added_labels = set()

for i, tactic_distribution in enumerate(tactic_distributions):
    # Get counts for each tactic (0 if not present)
    counts = [tactic_distribution.get(tactic, 0) for tactic in all_tactics]
    
    # Plot stacked bars
    label = ""
    color = colors.scheme[i % len(colors.scheme)]
    if selected_experiments[i].startswith("EXPERIMENT_ATTACKER_"):
        label = "Attacker Experiments"
        color = colors.scheme[1]
    elif selected_experiments[i].startswith("EXPERIMENT_HP_"):
        label = "Honeypot Experiments"
        color = colors.scheme[0]
    elif selected_experiments[i].startswith("RECONFIG_EXPERIMENT_"):
        label = "Reconfiguration Experiment"
        color = colors.scheme[5]
    else:
        label = f'Experiment {selected_experiments[i]}'
    
    # Only include label if we haven't seen it before
    legend_label = label if label not in added_labels else ""
    if label not in added_labels:
        added_labels.add(label)
    
    plt.bar(x_positions, counts, 
            bottom=bottom,
            label=legend_label,
            color=color)
    
    # Update bottom for next stack
    bottom += counts

# Add percentage labels on top of each stack
total_counts = bottom
for i, (tactic, total_count) in enumerate(zip(all_tactics, total_counts)):
    if total_count > 0:  # Only show percentage if there's data
        percentage = (total_count / sum(total_counts)) * 100
        plt.text(i, total_count + max(total_counts) * 0, f'{percentage:.1f}%', 
                ha='center', va='bottom', fontsize=12, rotation=0)

plt.ylabel("Number of Sessions")
plt.ylim(0, 39000)
# plt.yscale('log')  # Use logarithmic scale for better visibility
plt.xticks(x_positions, all_tactics, rotation=45, ha='right')
plt.legend(loc='upper right', bbox_to_anchor=(0.98, 0.98), fontsize=12)
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

# %% Create LaTeX table for tactic distribution
# Create a dataframe with tactics as rows
tactic_totals = pd.Series(full_tactic_distributions)
tactic_total_sum = tactic_totals.sum()
tactic_percentages = (tactic_totals / tactic_total_sum * 100).round(1)

# Create dataframe with tactics as rows (not transposed)
tactic_summary_df = pd.DataFrame({
    'Total': tactic_totals,
    'Percentage': tactic_percentages
})

latex_tactic_table = tactic_summary_df.to_latex(
    float_format="%.1f",
    column_format='lrr',
    escape=False,
    caption="Tactic Distribution Totals and Percentages",
    label="tab:tactic_distribution",
    position='H'
)

# Save LaTeX table to file
with open(logs_path / "tactic_distribution.tex", 'w') as f:
    f.write(latex_tactic_table)

print("LaTeX table saved to tactic_distribution.tex")
print(latex_tactic_table)

# %% Honeypot deceptiveness
# table of model of HP/experiment, detection, no detection, session length befor discovery and average session length
hp_deceptiveness_data = []
for i, sessions_list in enumerate(combined_sessions_list):
    honeypot_model = selected_experiments[i]
    n_experiments = len(sessions_list)

    honeypot_detected = sum(1 for session in sessions_list if session.get("discovered_honeypot") == "yes")
    honeypot_not_detected = sum(1 for session in sessions_list if session.get("discovered_honeypot") == "no")
    print((honeypot_detected), (honeypot_not_detected), len(sessions_list))

    detected_percentage = honeypot_detected / n_experiments * 100
    not_detected_percentage = honeypot_not_detected / n_experiments * 100

    # Only include sessions where discovered_honeypot is not "unknown"
    filtered_sessions = [session for session in sessions_list if session.get("discovered_honeypot") != "unknown"]
    session_length_data = measure_session_length(filtered_sessions)
    average_session_length = session_length_data["mean"]

    sessions_before_discovery = [session for session in sessions_list if session.get("discovered_honeypot") == "yes"]
    if sessions_before_discovery:
        session_length_before_discovery = measure_session_length(sessions_before_discovery)
        average_session_length_before_discovery = session_length_before_discovery["mean"]
    else:
        average_session_length_before_discovery = 0

    sessions_without_discovery = [session for session in sessions_list if session.get("discovered_honeypot") == "no"]
    if sessions_without_discovery:
        session_length_without_discovery = measure_session_length(sessions_without_discovery)
        average_session_length_without_discovery = session_length_without_discovery["mean"]
    else:
        average_session_length_without_discovery = 0

    hp_deceptiveness_data.append({
        "Honeypot Model": honeypot_model,
        "Experiment": selected_experiments[i],
        "Detection Percentage": detected_percentage,
        "No Detection Percentage": not_detected_percentage,
        "Average Session Length": average_session_length,
        "Average Session Length Before Discovery": average_session_length_before_discovery,
        "Average Session Length Without Discovery": average_session_length_without_discovery
    })

hp_deceptiveness_df = pd.DataFrame(hp_deceptiveness_data)

hp_deceptiveness_df = hp_deceptiveness_df.round(2)

# Rename columns to be shorter and add % symbols where appropriate
hp_deceptiveness_df_latex = hp_deceptiveness_df.copy()
hp_deceptiveness_df_latex = hp_deceptiveness_df_latex.rename(columns={
    "Honeypot Model": "Model",
    "Detection Percentage": "Detected \\%",
    "No Detection Percentage": "Not Detected \\%", 
    "Average Session Length": "Avg Length",
    "Average Session Length Before Discovery": "Before Discovery",
    "Average Session Length Without Discovery": "Without Discovery"
})

# Drop the redundant 'Experiment' column and format the data
hp_deceptiveness_df_latex = hp_deceptiveness_df_latex.drop(columns=['Experiment'])

# Convert to CSV
hp_deceptiveness_df.to_csv(logs_path / "honeypot_deceptiveness.csv", index=False)

# Generate LaTeX table with custom formatting
latex_table = hp_deceptiveness_df_latex.to_latex(
    index=False, 
    float_format="%.1f",
    column_format='lrr|rrr',
    escape=False,
    caption="The table shows different honeypot models effectiveness in not being detected and their average session lengths.",
    label="tab:tab:hp-deceptiveness",
    position='H'
)

# Save LaTeX table to file
with open(logs_path / "honeypot_deceptiveness.tex", 'w') as f:
    f.write(latex_table)

print("LaTeX table saved to honeypot_deceptiveness.tex")
print(latex_table)

# %% Average session length over time (restart each configuration)
for k, sessions_list in enumerate(sessions_list_list):
    length_data = measure_session_length(combined_sessions_list[k])

    session_all_lengths = []    
    for session in sessions_list:
        if len(session) == 0:
            continue
        session_length_data = measure_session_length(session)
        session_all_lengths.append(session_length_data["session_lengths"])


    for j, session_lengths in enumerate(session_all_lengths):
        margins = []
        mus = []
        eps = 10
        eps = []

        for i in range(len(session_lengths)):
            if i < 2:  # Skip when we have less than 2 data points
                margins.append(0)
                mus.append(session_lengths[0] if i > 0 else 0)
                eps.append(0)
            else:
                moe = compute_confidence_interval(session_lengths[0:i], 0.05)
                margins.append(moe)
                mus.append(np.mean(session_lengths[0:i]))
                eps.append(0.4 * np.std(session_lengths[0:i], ddof=1))

        mus = np.array(mus)
        margins = np.array(margins)
        eps = np.array(eps)

        window_size = 5
        mask = (margins <= eps)
        values = np.array(range(len(mus)))

        plt.plot(values, mus, color=colors.scheme[k % len(colors.scheme)], label=f"{selected_experiments[k]}, Config {j+1}", alpha=0.7)
        plt.fill_between(values, mus - margins, mus + margins, color=colors.scheme[k % len(colors.scheme)], alpha=0.1)
        print(f"{selected_experiments[k]}, Config {j+1}: {mus[-1]:.2f} ± {margins[-1]:.2f}")

plt.ylim(-5, 100)
plt.xlim(0, 80)
plt.xlabel("Session Index")
plt.ylabel("Mean Session Length (number of commands)")
plt.title("Average Session Length Over Time")
plt.show()

# %% Average Levenshtein distance over time (restart each configuration)
for k, sessions_list in enumerate(sessions_list_list):
    combined_sessions = combined_sessions_list[k]
    
    for j, sessions in enumerate(sessions_list):
        sequence_data = measure_tactic_sequences(sessions)
        
        margins = []
        mus = []
        eps = []
        dists_list = []

        for i in range(1, len(sequence_data["indexed_sequences"])):
            # Calculate Levenshtein distances for all pairs up to index i
            current_dists = []
            for l in range(0, i):
                seq_i = sequence_data["indexed_sequences"][i]
                seq_l = sequence_data["indexed_sequences"][l]
                if seq_i and seq_l:
                    dist = editdistance.eval(seq_i, seq_l)
                    # Normalize by the maximum possible distance (length of longer sequence)
                    max_len = max(len(seq_i), len(seq_l))
                    normalized_dist = dist / max_len if max_len > 0 else 0
                    current_dists.append(normalized_dist)
                    dists_list.append(normalized_dist)
            
            if dists_list:
                eps.append(0.05 * np.std(dists_list, ddof=1) if len(dists_list) > 1 else 0)
                moe = compute_confidence_interval(np.array(dists_list), 0.05)
                margins.append(moe)
                mus.append(np.mean(dists_list))

        if mus:
            mus = np.array(mus)
            margins = np.array(margins)
            eps_threshold = eps[-1] if eps else 0
            window_size = 5
            mask = (margins <= eps_threshold) if len(margins) > window_size else np.ones(len(margins), dtype=bool)
            values = np.array(range(len(mus)))

            plt.plot(mus, color=colors.scheme[k % len(colors.scheme)], label=f"{selected_experiments[k]}, Config {j+1}", alpha=0.7)
            plt.fill_between(values, mus - margins, mus + margins, color=colors.scheme[k % len(colors.scheme)], alpha=0.1)
            print(f"{selected_experiments[k]}, Config {j+1}: {mus[-1]:.4f} ± {margins[-1]:.5f}")

plt.xlabel("Session Index")
plt.ylim(0, 1)
plt.xlim(0, 80)
plt.ylabel("Mean Levenshtein Distance")
plt.title("Average Levenshtein Distance Over Time")
plt.show()

# %% Average Levenshtein distance over time (no restart)
from collections import Counter
from utils import compute_confidence_interval
import editdistance
from Utils.jsun import load_json

for k, combined_sessions in enumerate(combined_sessions_list):
    sequence_data = measure_tactic_sequences(combined_sessions)

    dists = Counter()
    dists_list = []
    margins = []
    mus = []
    eps = 2
    eps = []

    for i in range(len(sequence_data["indexed_sequences"])):
        avg_list = []
        for j in range(0, i):
            seq_i = sequence_data["indexed_sequences"][i]
            seq_j = sequence_data["indexed_sequences"][j]
            if seq_i and seq_j:
                dist = editdistance.eval(seq_i, seq_j) / max(len(seq_i), len(seq_j))
                dists.update([dist])
                avg_list.append(dist)
        my_avg = np.mean(np.array(avg_list)) if avg_list else 0
        dists_list.append(my_avg)
        eps.append(0.1 * np.std(dists_list, ddof=1))
        moe = compute_confidence_interval(np.array(dists_list), 0.05)
        margins.append(moe)
        mus.append(np.mean(dists_list))
    mus = np.array(mus)
    margins = np.array(margins)
    eps = np.array(eps)[-1]
    window_size = 10
    mask = (margins < eps) & (np.array([False] * window_size + [True] * (len(mus) - window_size)))
    values = np.array(range(len(mus)))

    plt.plot(values, mus, color=colors.scheme[k], label=f"{selected_experiments[k]}", alpha=0.7)
    plt.fill_between(values, mus - margins, mus + margins, color=colors.scheme[k], alpha=0.1)

    # Add vertical bars for reconfig indices
    for reconfig_idx in reconfig_indices_list[k]:
        plt.axvline(x=reconfig_idx, color=colors.scheme[k], linestyle='--', alpha=0.5)
    
plt.xlabel("Sequence")
plt.ylabel("Mean Levenshtein Distance")
plt.xlim([0, len(mus) - 1])
plt.ylim([0, 1])
plt.legend()
plt.show()

# %% Average session length over time (no restart)
for k, combined_sessions in enumerate(combined_sessions_list):
    session_length_data = measure_session_length(combined_sessions)

    session_lengths = session_length_data["session_lengths"]
    margins = []
    mus = []
    eps = []

    for i in range(1, len(session_lengths) + 1):
        current_lengths = session_lengths[:i]
        eps.append(0.4 * np.std(current_lengths, ddof=1) if len(current_lengths) > 1 else 0)
        moe = compute_confidence_interval(current_lengths, 0.05)
        margins.append(moe)
        mus.append(np.mean(current_lengths))

    mus = np.array(mus)
    margins = np.array(margins)
    eps_threshold = eps[-1] if eps else 0
    window_size = 10
    mask = (margins < eps_threshold) & (np.array([False] * window_size + [True] * (len(mus) - window_size)))
    values = np.array(range(len(mus)))

    plt.plot(values, mus, color=colors.scheme[k], label=f"{selected_experiments[k]}", alpha=0.7)
    plt.fill_between(values, mus - margins, mus + margins, color=colors.scheme[k], alpha=0.1)

    # Add vertical bars for reconfig indices
    for reconfig_idx in reconfig_indices_list[k]:
        plt.axvline(x=reconfig_idx, color=colors.scheme[k], linestyle='--', alpha=0.5)

plt.xlabel("Session Index")
plt.ylabel("Mean Session Length (number of commands)")
plt.xlim([0, len(mus) - 1])
plt.ylim([0, 100])
plt.legend()
plt.title("Average Session Length Over Time (No Restart)")
plt.show()
# %% Tokens used per experiment

