from Purple.Data_analysis.metrics import measure_session_length
from Style import colors
from Purple.Data_analysis.utils import Experiments
from typing import List

import matplotlib.pyplot as plt

def plot_session_length(experiments: Experiments, experiment_names: List[str]):
    length_datas = [measure_session_length(sessions) for sessions, _, _ in experiments]

    plt.figure(figsize=(12, 6))
    for i, (length_data, (_, _, reconfig_indices), exp_name) in enumerate(
            zip(length_datas, experiments, experiment_names)):
        plt.plot(length_data["session_lengths"], color=colors.scheme[i], label=exp_name)
        plt.title("Session length per Session")
        plt.xlabel("Session")
        plt.ylabel("Session length")
        for index in reconfig_indices:
            plt.axvline(index - 0.5, color=colors.scheme[i], linestyle="--", alpha=0.2)
        plt.ylim(bottom=0)
    plt.legend()

