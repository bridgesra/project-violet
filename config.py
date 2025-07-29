from Red.model import LLMModel, ReconfigCriteria

experiment_name = ""

# Experiment settings
llm_model_sangria = LLMModel.GPT_4_1_MINI
llm_model_reconfig = LLMModel.GPT_4_1_MINI
reconfig_method: ReconfigCriteria = ReconfigCriteria.BASIC # NO_RECONFIG / BASIC / ENTROPY / T_TEST 
llm_provider = "openai" # openai / togetherai / static

# General settings
simulate_command_line = False

# Session settings
num_of_attacks = 400
max_session_length = 100

## Basic reconfiguration
ba_interval: int = 100

## Entropy reconfiguration
en_variable: str = "techniques"
en_window_size: int = 1
en_tolerance: float = 1e-2

## T-test reconfiguration
tt_variable: str = "tactic_sequences"
tt_tolerance: float = 0.003 # session_length: 0.008, tactics: 0.003
tt_confidence: float = 0.95
