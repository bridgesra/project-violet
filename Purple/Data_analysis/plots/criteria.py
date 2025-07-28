from Purple.Data_analysis.metrics import measure_tactic_sequences, measure_session_length
from Style import colors
from Purple.Data_analysis.utils import Experiments, compute_confidence_interval
import matplotlib.pyplot as plt
import editdistance
import numpy as np
from typing import List

def plot_criteria(
        experiments: Experiments,
        experiment_names: List[str],
        ld_alpha: float = 0.05,
        ld_eps: float = 0.2,
        sl_alpha: float = 0.05,
        sl_eps: float = 0.04,
        cutoff_criterion_reconfig: bool = False
        ):
    ld_datas = []
    sl_datas = []
    
    # collect data
    for _, config_sessions, _ in experiments:
        config_tactic_sequences = [
            measure_tactic_sequences(sessions)["indexed_sequences"]
            for sessions in config_sessions
        ]
        margins = []
        mus = []
        eps = []
        for tactic_sequences in config_tactic_sequences:
            dists_list = []
            for i in range(len(tactic_sequences)):
                for j in range(0, i):
                    seq_i = tactic_sequences[i]
                    seq_j = tactic_sequences[j]
                    if seq_i and seq_j:
                        dist = editdistance.eval(seq_i, seq_j)
                        dists_list.append(dist)
                eps.append(ld_eps * np.std(dists_list, ddof=1))
                moe = compute_confidence_interval(np.array(dists_list), ld_alpha)
                margins.append(moe)
                mus.append(np.mean(dists_list))
        mus = np.array(mus)
        margins = np.array(margins)
        eps = np.array(eps)[-1]

        ld_datas.append((mus, margins, eps))

        config_session_lengths = [
            measure_session_length(sessions)["session_lengths"]
            for sessions in config_sessions
        ]
        margins = []
        mus = []
        eps = []

        for session_lengths in config_session_lengths:
            for i in range(len(session_lengths)):
                moe = compute_confidence_interval(session_lengths[0:i], sl_alpha)
                margins.append(moe)
                mus.append(np.mean(session_lengths[0:i]))
                eps.append(sl_eps * np.std(session_lengths[0:i], ddof=1))

        mus = np.array(mus)
        margins = np.array(margins)
        eps = np.array(eps)

        sl_datas.append((mus, margins, eps))

    # plotting
    titles = ["levenshtein distance", "session length"]
    ylims = [(0, 100), (0, 100)]
    for datas, title, ylim in zip([ld_datas, sl_datas], titles, ylims):
        plt.figure(figsize=(8, 6))
        for i, ((mus, margins, eps), (_, _, reconfig_indices), exp_name) in enumerate(
                zip(datas, experiments, experiment_names)):
            mask = (margins < eps)

            modified_indices = [0] + list(reconfig_indices) + [len(mask)-1]
            criterion_indices = []

            new_mus = []
            new_margins = []
            new_criterion_indices = []

            for j in range(len(modified_indices)-1):
                start = modified_indices[j]
                end = modified_indices[j+1]
                for k in range(start, end+1):
                    if mask[k]:
                        criterion_indices.append(k)
                        new_mus.extend(list(mus[start:k+1]))
                        new_margins.extend(list(margins[start:k+1]))
                        new_criterion_indices.append(len(new_mus) - 1)
                        break
            
            if cutoff_criterion_reconfig:
                mus = np.array(new_mus)
                margins = np.array(new_margins)
                criterion_indices = new_criterion_indices

            lower = mus - margins
            upper = mus + margins
            values = np.arange(len(mus))

            plt.fill_between(values, lower, upper, alpha=0.2, color=colors.scheme[i])
            plt.title(title)
            plt.plot(values, mus, color=colors.scheme[i], label=exp_name)
            for index in criterion_indices:
                plt.axvline(values[index] + 0.5, color=colors.scheme[i], alpha=0.2, linestyle=":")
            if not cutoff_criterion_reconfig:
                for index in reconfig_indices:
                    plt.axvline(values[index] - 0.5, color=colors.scheme[i], alpha=0.2, linestyle="--")
            plt.xlabel("Sequence")
            plt.ylabel("Mean")
            plt.ylim(ylim)
        plt.legend()