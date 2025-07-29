import os
import sys
from pathlib import Path
import questionary
import matplotlib.pyplot as plt

# Add parent directory to sys.path to allow imports from project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from Purple.Data_analysis.utils import extract_experiment
from Purple.Data_analysis.plots import (
    plot_mitre_data,
    plot_session_length,
    plot_criteria,
    plot_entropy
)

logs_path = Path(__file__).resolve().parent.parent.parent / "logs"
filter_empty_sessions = False
use_omni_sessions = False

def main():
    all_experiments = sorted(os.listdir(logs_path), reverse=False)
    if not all_experiments:
        print("No experiments found under", logs_path)
        sys.exit(1)

    selected_experiments = questionary.checkbox(
        "Select experiments to analyze:",
        choices=all_experiments
    ).ask()

    if not selected_experiments:
        print("No experiments selected, exiting.")
        sys.exit(0)

    experiments = [
        extract_experiment(
            logs_path / exp_name,
            filter_empty_sessions,
            use_omni_sessions
        ) for exp_name in selected_experiments
    ]

    def prepare_plot_criteria(exps, exp_names):
        cutoff_experiments = questionary.checkbox(
            "Select experiments to apply cutoff option:",
            choices=exp_names
        ).ask()
        cutoff_list = [name in cutoff_experiments for name in exp_names]
        plot_criteria(exps, exp_names, cutoff_list)

    plot_options = {
        'Session Length': plot_session_length,
        'MITRE Distribution': plot_mitre_data,
        'Entropy': plot_entropy,
        'Criteria': prepare_plot_criteria,
    }

    chosen_plots = questionary.checkbox(
        "Select plots to generate:",
        choices=list(plot_options.keys())
    ).ask()

    if not chosen_plots:
        print("No plots selected, exiting.")
        sys.exit(0)

    for plot_name in chosen_plots:
        plot_func = plot_options[plot_name]
        plot_func(experiments, selected_experiments)
        plt.show()

if __name__ == "__main__":
    main()
