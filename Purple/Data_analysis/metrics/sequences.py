import editdistance
import numpy as np
from typing import Dict, List, Any, Literal, Set

def measure_tactic_sequences(sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
    return measure_sequences(sessions, "tactics")

def measure_technique_sequences(sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
    return measure_sequences(sessions, "techniques")

def measure_command_sequences(sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
    return measure_sequences(sessions, "command")

def measure_sequences(sessions: List[Dict[str, Any]],
        t_name: Literal["tactics", "techniques", "command"]) -> Dict[str, Any]:
    t_to_index: Dict[str, int] = {}
    sequences: List[List[str]] = []
    indexed_sequences: List[List[int]] = []
    min_distances: List[int] = []

    for session in sessions:
        seq = []
        for command in session.get("full_session", []):
            t = command.get(t_name, "")
            if t_name == "command":
                t = t.split(" ")[0]
            seq.append(t)
            if t not in t_to_index:
                t_to_index[t] = len(t_to_index)
        indexed_seq = [t_to_index[t] for t in seq]
        
        if len(indexed_sequences) > 0:
            if indexed_seq != "":
                min_distance = min([editdistance.eval(prev_seq, indexed_seq) 
                    for prev_seq in indexed_sequences])
                min_distances.append(min_distance)
            else:
                min_distances.append(min_distances[-1])
        else:
            min_distances.append(np.inf)

        sequences.append(seq)
        indexed_sequences.append(indexed_seq)

    results = {
        f"{t_name}": t_to_index,
        "min_distances": min_distances,
        "sequences": sequences,
        "indexed_sequences": indexed_sequences,
    }

    return results
