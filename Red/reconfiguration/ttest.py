import numpy as np
from scipy.stats import t
from typing import List
from collections import Counter
from Red.reconfiguration.abstract import AbstractReconfigCriterion

def compute_confidence_interval(session_lengths: np.ndarray, alpha: float) -> float:
    print(session_lengths)
    s = session_lengths.std(ddof=1)
    n = session_lengths.shape[0]

    t_crit = t.ppf(1 - alpha/2, df=n - 1)
    moe = t_crit * (s / np.sqrt(n))

    return float(moe)

VARIABLES = ["session_length"]

def get_prob_dist(data: Counter) -> List[float]:
    total = sum(data.values())
    return [freq / total for freq in data.values()]

class TTestReconfigCriterion(AbstractReconfigCriterion):
    def __init__(self, variable: str, tolerance: float, 
            confidence_level: float, reset_every_reconfig: bool = False):
        assert variable in VARIABLES, f"Variable '{variable}' is not supported. Supported variables: {VARIABLES}"
        self.variable = variable
        self.tolerance = tolerance
        assert 0 < confidence_level < 1, f"Confidence level {self.confidence_level} is not in the range (0,1)"
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level
        super().__init__(reset_every_reconfig)

    def reset(self):
        self.session_lengths: List[int] = []
        self.moes: List[float] = []

    def update(self, session):
        match self.variable:
            case "session_length":
                self.session_lengths.append(session.get("session_length"))
        self.moes.append(
            compute_confidence_interval(
                np.array(self.session_lengths),
                self.alpha
            )
        )
        
    def should_reconfigure(self):
        return self.moes[-1] < self.tolerance