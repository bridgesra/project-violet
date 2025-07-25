# %%
from Red.model import LLMModel, ReconfigCriteria

experiment_name = ""

# Experiment settings
llm_model_sangria = LLMModel.GPT_4_1_MINI
llm_model_config = LLMModel.GPT_4_1_MINI
reconfig_method: ReconfigCriteria = ReconfigCriteria.BASIC # NO_RECONFIG / T_TEST / BASIC
llm_provider = "openai" # openai / togetherai / static

# General settings
simulate_command_line = False

# Session settings
num_of_attacks = 400
min_num_of_attacks_reconfig = 1
max_session_length = 1

# Reconfiguration settings 
reset_every_reconfig = True
## Basic reconfiguration
ba_interval: int = 1
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
