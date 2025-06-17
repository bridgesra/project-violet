# %%
from Red.model import LLMModel

llm_model_sangria = LLMModel.GPT_4O_MINI
llm_model_config = LLMModel.GPT_4_1_NANO
simulate_command_line = True
save_logs = True
save_configuration = True
print_output = True

attacks_per_configuration = 10
n_configurations = 10

# %%
if simulate_command_line:
    save_logs = False
    
# %%
