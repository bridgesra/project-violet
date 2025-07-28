from Purple.Data_analysis.metrics import measure_mitre_distribution
from Style import colors
from Purple.Data_analysis.utils import Experiments
import matplotlib.pyplot as plt
from typing import List

def plot_mitre_data(experiments: Experiments, experiment_names: List[str]):
    mitre_dist_datas = [measure_mitre_distribution(sessions) for sessions,_,_ in experiments]

    for name in ["tactics", "techniques"]:
        plt.figure(figsize=(12, 6))
        for plot_data_name, title in zip(
            [
                f"session_cum_num_{name}",
                f"session_num_{name}",
            ],
            [
                f"Cumulative sum of unique {name}", 
                f"Number of unique {name} per session"
            ]
        ):
            for i, (mitre_dist_data, (_, _, reconfig_indices), exp_name) in enumerate(
                    zip(mitre_dist_datas, experiments, experiment_names)):
                plt.plot(
                    mitre_dist_data[plot_data_name],
                    marker="o",
                    markersize=2,
                    linestyle="-",
                    c=colors.scheme[i],
                    label=exp_name)
                plt.title(title)
                plt.xlabel("Session")
                plt.ylabel(f"Number of unique {name}")
                for index in reconfig_indices:
                    plt.axvline(index - 0.5, color=colors.scheme[i], linestyle="--", alpha=0.2)
                plt.ylim(bottom=0)
            plt.legend()
