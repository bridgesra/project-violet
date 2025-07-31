# project-violet

## Overview

Project Violet is an automated cybersecurity research platform that simulates realistic attack scenarios against configurable honeypots to generate labeled datasets for improving defensive capabilities. The system uses AI-powered red team attacks, adaptive blue team defenses, and the Beelzebub honeypot to create a continuous feedback loop for cybersecurity improvement.

## Prerequisites

 - Docker
 - docker-compose
 - python (3.11.2+)
 - python dependencies (listed in requirements.txt)
 - .env file in top directory with api keys:
```
OPENAI_API_KEY="{your-openai-api-key}"
TOGETHER_AI_SECRET_KEY="{your-togetherai_api_key}"
```
## Running the code easy

All experiment settings will be set in config.py prior to running.

Then simply run the experiment with

```bash
python main.py
```

The [main.py](main.py) file orchestrates the entire attack simulation cycle, running multiple configurations and collecting comprehensive attack data.

## Configuration

### Main Configuration (`config.py`):

```python
experiment_name = "" # Name for the experiment, leave empty for timestamp.
run_id = "10" # 10 - 99, If multiple experiments are run in parallel, each need unique run_id.

# Experiment settings
llm_model_sangria = LLMModel.GPT_4_1_MINI                  # GPT_4_1, GPT_4_1_MINI, O4_MINI, GPT_4_1_NANO
llm_model_blue_lagoon = LLMModel.GPT_4_1_MINI
llm_model_reconfig = LLMModel.GPT_4_1_MINI
llm_provider_hp = "openai"                                 # openai / togetherai / static
reconfig_method: ReconfigCriteria = ReconfigCriteria.BASIC # NO_RECONFIG / BASIC / ENTROPY / T_TEST 

# Simulate HP for testing purposes
simulate_command_line = False

# Session settings
num_of_sessions = 400
max_session_length = 100

# Reconfiguration criteria settings
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

```

## Output Structure

The system generates organized output in the `logs/` directory:

```
logs/
├── [EXPERIMENT_NAME]/               # Experiment directories
│   ├── metadata.json               # Experiment metadata
│   ├── sessions.json               # All sessions summary
│   └── hp_config_[N]/              # Individual honeypot configurations
│       ├── honeypot_config.json    # Honeypot configuration used
│       ├── sessions.json           # Sessions for this config
│       ├── tokens_used.json        # Token usage tracking
│       └── full_logs/              # Individual attack logs
│           └── attack_[N].json     # Complete attack interaction logs
```


## Structure of code

The codebase is organized into four main components:

### ❤️ Sangria (Attacker)

* **Sangria**: AI-powered attack orchestration system
* **Tool Integration**: Automated execution of attack commands

### 💙 Blue_Lagoon (Honeypot) [Link](https://github.com/mariocandela/beelzebub)

* **Service Simulation**: Realistic vulnerable service emulation
* **Interaction Logging**: Comprehensive attack interaction capture
* **Configuration**: Iterative service modification capabilities

### ⚙️ Reconfigurator 

* **Configuration Pipeline**: Dynamic honeypot reconfiguration based on previous configurations and attack patterns
* **RAG System**: Using a RAG to retrieve vulnerabilities from NVD

### 💜 Purple

* **Data Analysis**: Analysis tools to analyze logs.


