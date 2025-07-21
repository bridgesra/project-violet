from typing import Dict, List, Any, Set

def measure_sequences(sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
    tactics: Set[str] = set([])
    techniques: Set[str] = set([])
    tactic_sequences: List[List[str]] = []
    technique_sequences: List[List[str]] = []

    for session in sessions:
        tactic_seq = []
        technique_seq = []

        for command in session.get("full_session", []):
            tactic = command.get("tactic", "")
            technique = command.get("technique", "")
            tactics.add(tactic)
            techniques.add(technique)
            tactic_seq.append(tactic)
            technique_seq.append(technique)

        tactic_sequences.append(tactic_seq)
        technique_sequences.append(technique_seq)

    tactic_to_index = {tactic:index for index, tactic in enumerate(tactics)}
    technique_to_index = {technique:index for index, technique in enumerate(techniques)}

    indexed_tactic_sequence = [
        "".join([str(tactic_to_index[tactic]) for tactic in tactic_seq])
        for tactic_seq in tactic_sequences
    ]
    indexed_technique_sequence = [
        "".join([str(technique_to_index[technique]) for technique in technique_seq])
        for technique_seq in technique_sequences
    ]

    results = {
        "tactics": tactic_to_index,
        "techniques": technique_to_index,
        "tactic_sequences": tactic_sequences,
        "technique_sequences": technique_sequences,
        "indexed_tactic_sequences": indexed_tactic_sequence,
        "indexed_technique_sequences": indexed_technique_sequence
    }

    return results