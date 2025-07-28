from enum import Enum

class LLMModel(str, Enum):
    """Enumeration LLM models."""
    GPT_4_1_NANO = "gpt-4.1-nano"
    GPT_4_1 = "gpt-4.1"
    GPT_4 = "gpt-4"
    GPT_4_1_MINI = "gpt-4.1-mini"
    O4_MINI = "o4-mini"

class ReconfigCriteria(str, Enum):
    NO_RECONFIG = "no_reconfig"
    BASIC = "basic"
    ENTROPY = "entropy"
    T_TEST = "t_test"
