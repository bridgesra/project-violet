from dotenv import load_dotenv
import os
import config
load_dotenv()
os.environ["HP_MODEL"] = config.llm_model_blue_lagoon
os.environ["RUN_ID"] = config.run_id

from pathlib import Path

from Sangria import attacker_prompt
from Sangria.sangria import run_single_attack
from Sangria.extraction import extract_session

from Reconfigurator.new_config_pipeline import generate_new_honeypot_config, get_honeypot_config, set_honeypot_config
from Reconfigurator.utils import acquire_config_lock, release_config_lock

from Blue_Lagoon.honeypot_tools import start_dockers, stop_dockers

from Utils.meta import create_experiment_folder, select_reconfigurator
from Utils.jsun import save_json_to_file, append_json_to_file


def main():
    base_path = create_experiment_folder(experiment_name=config.experiment_name)
    base_path = Path(base_path)

    honeypot_config = get_honeypot_config(id=config.llm_provider_hp, path="")

    lock_file = acquire_config_lock()
    set_honeypot_config(honeypot_config)

    config_counter = 1
    config_attack_counter = 0
    tokens_used_list = []

    BOLD   = "\033[1m"
    RESET  = "\033[0m"
    print(f"{BOLD}New Configuration: configuration {config_counter}{RESET}")

    reconfigurator = select_reconfigurator()
    reconfigurator.reset()

    if not config.simulate_command_line:
        start_dockers()
    release_config_lock(lock_file)

    config_path = base_path / f"hp_config_{config_counter}"
    full_logs_path = config_path / "full_logs"
    os.makedirs(full_logs_path, exist_ok=True)

    if not config.simulate_command_line:
        save_json_to_file(honeypot_config, config_path / f"honeypot_config.json")

    for _ in range(config.num_of_sessions):
        config_attack_counter += 1
        os.makedirs(config_path, exist_ok=True)
        print(f"{BOLD}Attack {config_attack_counter} / {config.num_of_sessions}, configuration {config_counter}{RESET}")

        logs_path = full_logs_path / f"attack_{config_attack_counter}.json"

        messages = [
            {'role': 'system', 'content': attacker_prompt.prompt},
            {"role": "user", "content": "What is your next move?"}
        ]

        logs, tokens_used = run_single_attack(messages, config.max_session_length, logs_path, config_attack_counter-1, config_counter)

        # extract session and add attack pattern to set
        session = extract_session(logs)
        reconfigurator.update(session)

        append_json_to_file(tokens_used, config_path / f"tokens_used.json", False)
        tokens_used_list.append(tokens_used)
        append_json_to_file(session, config_path / f"sessions.json", False)

        if reconfigurator.should_reconfigure():  
            print(f"{BOLD}Reconfiguring: Using {config.reconfig_method}.{RESET}")

            if not config.simulate_command_line:
                stop_dockers()

            honeypot_config = generate_new_honeypot_config(base_path)
            
            lock_file = acquire_config_lock()
            set_honeypot_config(honeypot_config)

            reconfigurator.reset()

            config_counter += 1
            config_attack_counter = 0

            config_path = base_path / f"hp_config_{config_counter}"
            full_logs_path = config_path / "full_logs"
            os.makedirs(full_logs_path, exist_ok=True)

            save_json_to_file(honeypot_config, config_path / f"honeypot_config.json")

            if not config.simulate_command_line:
                start_dockers()

            release_config_lock(lock_file)

        print("\n\n")
    stop_dockers()

if __name__ == "__main__":
    main()
