# %%
from Red.model import LLMModel, ReconfigCriteria
from Red.attacker_prompts import AttackerPrompts

experiment_name = ""

# Experiment settings
llm_model_sangria = LLMModel.GPT_4_1_MINI
llm_model_config = LLMModel.GPT_4_1_MINI
attacker_prompt: str = AttackerPrompts.GENERAL
reconfig_method: ReconfigCriteria = ReconfigCriteria.NO_RECONFIG
llm_provider = "openai"

# General settings
simulate_command_line = False

# Session settings
num_of_attacks = 400
min_num_of_attacks_reconfig = 5
max_session_length = 100

# Reconfiguration settings 
reset_every_reconfig = True
## Basic reconfiguration
ba_interval: int = 1
## Mean increase reconfiguration
mi_variable: str = "techniques"
mi_tolerance: float = 0.5
mi_window_size: int = 5
mi_reset_techniques: bool = True
## Entropy reconfiguration
en_variable: str = "techniques"
en_window_size: int = 1
en_tolerance: float = 1e-2
## T-test reconfiguration
tt_variable: str = "tactic_sequences"
# tolerance session_length: 0.008
# tolerance levensthein: 0.003
tt_tolerance: float = 0.003
tt_confidence: float = 0.95

# Other
ISO_FORMAT = "%Y-%m-%dT%H_%M_%S"

# %%
