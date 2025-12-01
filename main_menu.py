#!/usr/bin/env python3
"""
Interactive menu system for Project Violet.

Provides a user-friendly interface to:
1. Start new experiments with configurable parameters
2. Prepare experiment data (extract and combine sessions)
3. Run Purple analysis on existing logs
"""

import questionary
import subprocess
import sys
import re
import os
from pathlib import Path
from Sangria.model import LLMModel, ReconfigCriteria
from Sangria.extraction import extract_session, extract_everything_session
from Utils.jsun import load_json, save_json_to_file, append_json_to_file


def main():
    """Main entry point for the interactive menu."""
    print("\n" + "=" * 60)
    print(" " * 15 + "PROJECT VIOLET")
    print("=" * 60 + "\n")

    while True:
        choice = show_main_menu()

        if choice == "Start New Experiment":
            configure_experiment()
        elif choice == "Prepare Experiment Data":
            prepare_experiment_data()
        elif choice == "Run Purple Analysis":
            run_purple_analysis()
        elif choice == "Exit":
            print("\nGoodbye!")
            break


def show_main_menu():
    """Display main menu and return user choice."""
    return questionary.select(
        "What would you like to do?",
        choices=[
            "Start New Experiment",
            "Prepare Experiment Data",
            "Run Purple Analysis",
            "Exit"
        ],
        style=questionary.Style([
            ('question', 'bold'),
            ('pointer', 'fg:cyan bold'),
            ('highlighted', 'fg:cyan bold'),
        ])
    ).ask()


def configure_experiment():
    """Interactive experiment configuration flow."""
    print("\n" + "-" * 60)
    print("NEW EXPERIMENT CONFIGURATION")
    print("-" * 60 + "\n")

    config_data = {}

    # Step 1: Experiment name
    config_data['experiment_name'] = prompt_experiment_name()

    # Step 2: Run ID
    config_data['run_id'] = prompt_run_id()

    # Step 3: Model selections
    print("\n--- Model Selection ---")
    config_data['llm_model_sangria'] = prompt_model_selection("Sangria (Attacker)")
    config_data['llm_model_blue_lagoon'] = prompt_model_selection("Blue Lagoon (Honeypot)")
    config_data['llm_model_reconfig'] = prompt_model_selection("Reconfigurator")

    # Step 4: Honeypot provider
    config_data['llm_provider_hp'] = prompt_hp_provider()

    # Step 5: Reconfiguration method
    print("\n--- Reconfiguration Settings ---")
    reconfig_method, reconfig_params = prompt_reconfig_method()
    config_data['reconfig_method'] = reconfig_method
    config_data.update(reconfig_params)

    # Step 6: Session parameters
    print("\n--- Session Parameters ---")
    config_data['num_of_sessions'] = prompt_session_count()
    config_data['max_session_length'] = prompt_session_length()

    # Step 7: Additional options
    print("\n--- Additional Options ---")
    config_data['simulate_command_line'] = prompt_simulate_cli()
    config_data['provide_honeypot_credentials'] = prompt_provide_credentials()

    # Step 8: Confirmation
    if confirm_configuration(config_data):
        update_config_file(config_data)
        run_experiment()
    else:
        print("\nConfiguration cancelled. Returning to main menu...\n")


def prompt_experiment_name():
    """Prompt for experiment name."""
    return questionary.text(
        "Enter experiment name:",
        validate=lambda x: len(x.strip()) > 0 or "Experiment name cannot be empty"
    ).ask()


def prompt_run_id():
    """Prompt for run ID with validation."""
    return questionary.text(
        "Enter run ID (10-99, for parallel experiments):",
        default="10",
        validate=lambda x: (x.isdigit() and 10 <= int(x) <= 99) or "Run ID must be between 10 and 99"
    ).ask()


def prompt_model_selection(component_name):
    """Prompt for LLM model selection."""
    model_descriptions = {
        "GPT_4_1_NANO": "gpt-4.1-nano",
        "GPT_4_1": "gpt-4.1",
        "GPT_4_1_MINI": "gpt-4.1-mini (Recommended)",
        "O4_MINI": "o4-mini"
    }

    choices = [
        questionary.Choice(title=desc, value=model)
        for model, desc in model_descriptions.items()
    ]

    return questionary.select(
        f"Select model for {component_name}:",
        choices=choices
    ).ask()


def prompt_hp_provider():
    """Prompt for honeypot LLM provider."""
    provider_descriptions = {
        "openai": "OpenAI API",
        "togetherai": "TogetherAI API",
        "static": "Static responses (no LLM)"
    }

    choices = [
        questionary.Choice(title=desc, value=provider)
        for provider, desc in provider_descriptions.items()
    ]

    return questionary.select(
        "Select honeypot LLM provider:",
        choices=choices
    ).ask()


def prompt_reconfig_method():
    """Prompt for reconfiguration method and return (method, params)."""
    method_descriptions = {
        "NO_RECONFIG": "No reconfiguration (static honeypot)",
        "BASIC": "Basic - Reconfigure every N sessions",
        "ENTROPY": "Entropy - Entropy-based reconfiguration",
        "T_TEST": "T-Test - Statistical t-test based"
    }

    choices = [
        questionary.Choice(title=desc, value=method)
        for method, desc in method_descriptions.items()
    ]

    method = questionary.select(
        "Select reconfiguration method:",
        choices=choices
    ).ask()

    params = {}
    if method == "BASIC":
        params = prompt_basic_params()
    elif method == "ENTROPY":
        params = prompt_entropy_params()
    elif method == "T_TEST":
        params = prompt_ttest_params()

    return method, params


def prompt_basic_params():
    """Prompt for Basic reconfiguration parameters."""
    interval = questionary.text(
        "Reconfigure every N sessions:",
        default="100",
        validate=lambda x: (x.isdigit() and int(x) > 0) or "Must be a positive integer"
    ).ask()

    return {'ba_interval': int(interval)}


def prompt_entropy_params():
    """Prompt for Entropy reconfiguration parameters."""
    variable = questionary.select(
        "Variable to track:",
        choices=["techniques", "session_length"]
    ).ask()

    tolerance = questionary.text(
        "Entropy tolerance (0.0-1.0):",
        default="0.01",
        validate=lambda x: is_float(x) and 0.0 <= float(x) <= 1.0 or "Must be a float between 0.0 and 1.0"
    ).ask()

    window = questionary.text(
        "Window size:",
        default="1",
        validate=lambda x: (x.isdigit() and int(x) > 0) or "Must be a positive integer"
    ).ask()

    return {
        'en_variable': variable,
        'en_tolerance': float(tolerance),
        'en_window_size': int(window)
    }


def prompt_ttest_params():
    """Prompt for T-Test reconfiguration parameters."""
    variable = questionary.select(
        "Variable to track:",
        choices=["tactic_sequences", "session_length", "tactics"]
    ).ask()

    # Suggest different default tolerances based on variable
    default_tolerance = {
        "session_length": "0.008",
        "tactics": "0.003",
        "tactic_sequences": "0.003"
    }.get(variable, "0.003")

    tolerance = questionary.text(
        f"Tolerance for {variable}:",
        default=default_tolerance,
        validate=lambda x: is_float(x) and float(x) > 0 or "Must be a positive float"
    ).ask()

    confidence = questionary.text(
        "Confidence level (0.0-1.0):",
        default="0.95",
        validate=lambda x: is_float(x) and 0.0 < float(x) < 1.0 or "Must be between 0.0 and 1.0"
    ).ask()

    return {
        'tt_variable': variable,
        'tt_tolerance': float(tolerance),
        'tt_confidence': float(confidence)
    }


def prompt_session_count():
    """Prompt for number of sessions."""
    return int(questionary.text(
        "Number of sessions:",
        default="2",
        validate=lambda x: (x.isdigit() and int(x) > 0) or "Must be a positive integer"
    ).ask())


def prompt_session_length():
    """Prompt for maximum session length."""
    return int(questionary.text(
        "Maximum session length (turns):",
        default="20",
        validate=lambda x: (x.isdigit() and int(x) > 0) or "Must be a positive integer"
    ).ask())


def prompt_simulate_cli():
    """Prompt for simulate command line option."""
    return questionary.confirm(
        "Simulate command line outputs?",
        default=False
    ).ask()


def prompt_provide_credentials():
    """Prompt for providing honeypot credentials to attacker."""
    return questionary.confirm(
        "Provide target credentials to attacker? (Skips reconnaissance, saves tokens)",
        default=False
    ).ask()


def confirm_configuration(config_data):
    """Display configuration summary and ask for confirmation."""
    print("\n" + "=" * 60)
    print(" " * 15 + "CONFIGURATION SUMMARY")
    print("=" * 60)

    # Experiment details
    print("\nExperiment Details:")
    print(f"  Name                    : {config_data['experiment_name']}")
    print(f"  Run ID                  : {config_data['run_id']}")

    # Model configuration
    print("\nModel Configuration:")
    print(f"  Sangria (Attacker)      : {config_data['llm_model_sangria']}")
    print(f"  Blue Lagoon (Honeypot)  : {config_data['llm_model_blue_lagoon']}")
    print(f"  Reconfigurator          : {config_data['llm_model_reconfig']}")
    print(f"  Honeypot Provider       : {config_data['llm_provider_hp']}")

    # Reconfiguration
    print("\nReconfiguration:")
    print(f"  Method                  : {config_data['reconfig_method']}")
    if config_data['reconfig_method'] == 'BASIC':
        print(f"  Interval                : {config_data['ba_interval']} sessions")
    elif config_data['reconfig_method'] == 'ENTROPY':
        print(f"  Variable                : {config_data['en_variable']}")
        print(f"  Tolerance               : {config_data['en_tolerance']}")
        print(f"  Window Size             : {config_data['en_window_size']}")
    elif config_data['reconfig_method'] == 'T_TEST':
        print(f"  Variable                : {config_data['tt_variable']}")
        print(f"  Tolerance               : {config_data['tt_tolerance']}")
        print(f"  Confidence              : {config_data['tt_confidence']}")

    # Session parameters
    print("\nSession Parameters:")
    print(f"  Number of Sessions      : {config_data['num_of_sessions']}")
    print(f"  Max Session Length      : {config_data['max_session_length']} turns")

    # Additional options
    print("\nAdditional Options:")
    print(f"  Simulate CLI            : {config_data['simulate_command_line']}")
    print(f"  Provide Credentials     : {config_data['provide_honeypot_credentials']}")

    print("=" * 60 + "\n")

    return questionary.confirm(
        "Proceed with this configuration?",
        default=True
    ).ask()


def update_config_file(config_data):
    """Update config.py with new values."""
    config_path = Path(__file__).parent / "config.py"

    # Read current config
    with open(config_path, 'r') as f:
        content = f.read()

    # Map user selections to LLMModel enum values
    model_mapping = {
        "GPT_4_1_NANO": "LLMModel.GPT_4_1_NANO",
        "GPT_4_1": "LLMModel.GPT_4_1",
        "GPT_4_1_MINI": "LLMModel.GPT_4_1_MINI",
        "O4_MINI": "LLMModel.O4_MINI"
    }

    reconfig_mapping = {
        "NO_RECONFIG": "ReconfigCriteria.NO_RECONFIG",
        "BASIC": "ReconfigCriteria.BASIC",
        "ENTROPY": "ReconfigCriteria.ENTROPY",
        "T_TEST": "ReconfigCriteria.T_TEST"
    }

    # Update basic settings
    content = re.sub(
        r'experiment_name = ".*?"',
        f'experiment_name = "{config_data["experiment_name"]}"',
        content
    )
    content = re.sub(
        r'run_id = ".*?"',
        f'run_id = "{config_data["run_id"]}"',
        content
    )

    # Update model settings
    content = re.sub(
        r'llm_model_sangria = LLMModel\.\w+',
        f'llm_model_sangria = {model_mapping[config_data["llm_model_sangria"]]}',
        content
    )
    content = re.sub(
        r'llm_model_blue_lagoon = LLMModel\.\w+',
        f'llm_model_blue_lagoon = {model_mapping[config_data["llm_model_blue_lagoon"]]}',
        content
    )
    content = re.sub(
        r'llm_model_reconfig = LLMModel\.\w+',
        f'llm_model_reconfig = {model_mapping[config_data["llm_model_reconfig"]]}',
        content
    )

    # Update provider
    content = re.sub(
        r'llm_provider_hp = ".*?"',
        f'llm_provider_hp = "{config_data["llm_provider_hp"]}"',
        content
    )

    # Update reconfiguration method
    content = re.sub(
        r'reconfig_method: ReconfigCriteria = ReconfigCriteria\.\w+',
        f'reconfig_method: ReconfigCriteria = {reconfig_mapping[config_data["reconfig_method"]]}',
        content
    )

    # Update simulate_command_line
    content = re.sub(
        r'simulate_command_line = (True|False)',
        f'simulate_command_line = {config_data["simulate_command_line"]}',
        content
    )

    # Update provide_honeypot_credentials
    content = re.sub(
        r'provide_honeypot_credentials = (True|False)',
        f'provide_honeypot_credentials = {config_data["provide_honeypot_credentials"]}',
        content
    )

    # Update session settings
    content = re.sub(
        r'num_of_sessions = \d+',
        f'num_of_sessions = {config_data["num_of_sessions"]}',
        content
    )
    content = re.sub(
        r'max_session_length = \d+',
        f'max_session_length = {config_data["max_session_length"]}',
        content
    )

    # Update reconfiguration parameters
    if 'ba_interval' in config_data:
        content = re.sub(
            r'ba_interval: int = \d+',
            f'ba_interval: int = {config_data["ba_interval"]}',
            content
        )

    if 'en_variable' in config_data:
        content = re.sub(
            r'en_variable: str = ".*?"',
            f'en_variable: str = "{config_data["en_variable"]}"',
            content
        )
        content = re.sub(
            r'en_window_size: int = \d+',
            f'en_window_size: int = {config_data["en_window_size"]}',
            content
        )
        content = re.sub(
            r'en_tolerance: float = [\d.e\-+]+',
            f'en_tolerance: float = {config_data["en_tolerance"]}',
            content
        )

    if 'tt_variable' in config_data:
        content = re.sub(
            r'tt_variable: str = ".*?"',
            f'tt_variable: str = "{config_data["tt_variable"]}"',
            content
        )
        content = re.sub(
            r'tt_tolerance: float = [\d.e\-+]+',
            f'tt_tolerance: float = {config_data["tt_tolerance"]}',
            content
        )
        content = re.sub(
            r'tt_confidence: float = [\d.e\-+]+',
            f'tt_confidence: float = {config_data["tt_confidence"]}',
            content
        )

    # Write updated config
    with open(config_path, 'w') as f:
        f.write(content)

    print(f"\n✓ Configuration updated successfully in {config_path}\n")


def run_experiment():
    """Execute the experiment."""
    print("\n" + "=" * 60)
    print(" " * 15 + "STARTING EXPERIMENT")
    print("=" * 60 + "\n")

    proceed = questionary.confirm(
        "Ready to start the experiment?",
        default=True
    ).ask()

    if not proceed:
        print("\nExperiment cancelled. Returning to main menu...\n")
        return

    try:
        import main
        main.main()
    except Exception as e:
        print(f"\n❌ Error running experiment: {e}\n")
        import traceback
        traceback.print_exc()


def prepare_experiment_data():
    """Extract and combine session data from raw logs."""
    print("\n" + "=" * 60)
    print(" " * 10 + "PREPARE EXPERIMENT DATA")
    print("=" * 60 + "\n")

    print("This tool extracts sessions from raw experiment logs and")
    print("prepares them for analysis.\n")

    logs_path = Path(__file__).parent / "logs"

    if not logs_path.exists():
        print(f"❌ Logs directory not found at: {logs_path}\n")
        return

    all_experiments = sorted([d for d in os.listdir(logs_path) if (logs_path / d).is_dir()])

    if not all_experiments:
        print("❌ No experiments found in logs directory.\n")
        return

    # Ask extraction mode
    extract_omni = select_extraction_mode()

    # Select experiments
    selected_experiments = questionary.checkbox(
        "Select experiments to process:",
        choices=all_experiments
    ).ask()

    if not selected_experiments:
        print("\nNo experiments selected. Returning to main menu...\n")
        return

    # Confirm before processing
    print(f"\n📋 Will process {len(selected_experiments)} experiment(s)")
    print(f"   Extraction mode: {'All commands (omni)' if extract_omni else 'Honeypot commands only'}")

    proceed = questionary.confirm(
        "Proceed with data preparation?",
        default=True
    ).ask()

    if not proceed:
        print("\nCancelled. Returning to main menu...\n")
        return

    # Run extraction and combination
    run_extraction_process(logs_path, selected_experiments, extract_omni)
    run_combination_process(logs_path, selected_experiments, extract_omni)

    print("\n" + "=" * 60)
    print("✓ DATA PREPARATION COMPLETE")
    print("=" * 60)
    print("\nYou can now run Purple Analysis to visualize the data.\n")


def select_extraction_mode():
    """Ask user which extraction mode to use."""
    print("Choose extraction mode:\n")
    print("  • Honeypot commands only: Extract only commands that reached the honeypot")
    print("  • All commands (omni): Extract all attacker commands including reconnaissance\n")

    extract_omni = questionary.confirm(
        "Extract all commands (omni mode)?",
        default=False
    ).ask()

    return extract_omni


def safe_listdir(p: Path):
    """Return listdir if p exists and is a dir, else empty list."""
    return os.listdir(p) if p.exists() and p.is_dir() else []


def run_extraction_process(logs_path: Path, selected_experiments: list, extract_omni: bool):
    """Extract sessions from raw logs."""
    print("\n" + "-" * 60)
    print("STEP 1: EXTRACTING SESSIONS")
    print("-" * 60 + "\n")

    session_file_name = "omni_sessions.json" if extract_omni else "sessions.json"

    for experiment in selected_experiments:
        experiment_path = logs_path / experiment
        print(f">> Processing: {experiment}")

        configs = filter(lambda name: name.startswith("hp_config"), safe_listdir(experiment_path))
        sorted_configs = sorted(
            configs,
            key=lambda fn: int(Path(fn).stem.split('_')[-1])
        )

        if not sorted_configs:
            print(f"   ⚠ No hp_config directories found, skipping.\n")
            continue

        all_sessions = []
        all_sessions_path = experiment_path / session_file_name

        for config in sorted_configs:
            config_path = experiment_path / config
            full_logs_path = config_path / "full_logs"
            session_path = config_path / session_file_name

            if not full_logs_path.exists():
                print(f"   ⚠ {config}: No full_logs directory, skipping.")
                continue

            # Remove existing sessions file
            if session_path.exists():
                session_path.unlink()
                print(f"   • Removed existing: {config}/{session_file_name}")

            attack_files = safe_listdir(full_logs_path)
            sorted_attacks = sorted(
                [f for f in attack_files if f.endswith('.json')],
                key=lambda fn: int(Path(fn).stem.split('_')[-1]) if '_' in Path(fn).stem else 0
            )

            extracted_count = 0
            for attack in sorted_attacks:
                attack_path = full_logs_path / attack
                try:
                    logs = load_json(attack_path)
                    if extract_omni:
                        session = extract_everything_session(logs)
                    else:
                        session = extract_session(logs)
                    all_sessions.append(session)
                    append_json_to_file(session, session_path, False)
                    extracted_count += 1
                except Exception as e:
                    print(f"   ⚠ Error extracting {attack}: {e}")
                    continue

            print(f"   ✓ {config}: Extracted {extracted_count} sessions")

        # Save combined sessions at experiment level
        if all_sessions:
            save_json_to_file(all_sessions, all_sessions_path, False)
            print(f"   ✓ Created {session_file_name} ({len(all_sessions)} total sessions)\n")
        else:
            print(f"   ⚠ No sessions extracted\n")


def run_combination_process(logs_path: Path, selected_experiments: list, extract_omni: bool):
    """Combine sessions across hp_configs."""
    print("-" * 60)
    print("STEP 2: COMBINING SESSIONS")
    print("-" * 60 + "\n")

    for experiment in selected_experiments:
        experiment_path = logs_path / experiment
        print(f">> Processing: {experiment}")

        configs = filter(lambda name: name.startswith("hp_config"), safe_listdir(experiment_path))
        sorted_configs = sorted(
            configs,
            key=lambda fn: int(Path(fn).stem.split('_')[-1])
        )

        if not sorted_configs:
            print(f"   ⚠ No hp_config directories found, skipping.\n")
            continue

        # Combine regular sessions
        try:
            sessions_list = []
            for config in sorted_configs:
                session_file = experiment_path / config / "sessions.json"
                if session_file.exists():
                    sessions_list.append(load_json(session_file))

            if sessions_list:
                combined_sessions = sum(sessions_list, [])
                save_json_to_file(combined_sessions, experiment_path / "sessions.json")
                print(f"   ✓ Combined {len(combined_sessions)} regular sessions")
        except Exception as e:
            print(f"   ⚠ Error combining sessions: {e}")

        # Combine omni sessions if requested
        if extract_omni:
            try:
                omni_sessions_list = []
                for config in sorted_configs:
                    omni_file = experiment_path / config / "omni_sessions.json"
                    if omni_file.exists():
                        omni_sessions_list.append(load_json(omni_file))

                if omni_sessions_list:
                    combined_omni_sessions = sum(omni_sessions_list, [])
                    save_json_to_file(combined_omni_sessions, experiment_path / "omni_sessions.json")
                    print(f"   ✓ Combined {len(combined_omni_sessions)} omni sessions")
            except Exception as e:
                print(f"   ⚠ Error combining omni sessions: {e}")

        print()


def run_purple_analysis():
    """Launch Purple analysis tools with sub-menu."""
    print("\n" + "=" * 60)
    print(" " * 15 + "PURPLE ANALYSIS")
    print("=" * 60 + "\n")

    print("Purple Analysis provides multiple tools for analyzing your data:\n")
    print("  • HP Comparison: Compare session lengths across experiments")
    print("  • Meta Analysis: Analyze MITRE tactics, deceptiveness, patterns")
    print("  • Advanced Visualizations: Create custom plots and charts\n")

    # Check if sessions exist
    logs_path = Path(__file__).parent / "logs"
    if not check_sessions_exist(logs_path):
        print("⚠ No processed session data found.\n")
        print("Please run 'Prepare Experiment Data' first to extract")
        print("sessions from your experiment logs.\n")

        should_prepare = questionary.confirm(
            "Go to Prepare Experiment Data now?",
            default=True
        ).ask()

        if should_prepare:
            prepare_experiment_data()
        return

    # Show Purple analysis sub-menu
    while True:
        choice = show_purple_menu()

        if choice == "HP Comparison Analysis":
            run_hp_comparison()
        elif choice == "Meta Analysis":
            run_meta_analysis()
        elif choice == "Advanced Visualizations":
            run_advanced_viz()
        elif choice == "Run All Analyses":
            run_all_purple_analyses()
        elif choice == "Back to Main Menu":
            break


def show_purple_menu():
    """Display Purple analysis sub-menu."""
    return questionary.select(
        "Select analysis to run:",
        choices=[
            "HP Comparison Analysis",
            "Meta Analysis",
            "Advanced Visualizations",
            "Run All Analyses",
            "Back to Main Menu"
        ],
        style=questionary.Style([
            ('question', 'bold'),
            ('pointer', 'fg:cyan bold'),
            ('highlighted', 'fg:cyan bold'),
        ])
    ).ask()


def check_sessions_exist(logs_path: Path):
    """Check if any sessions.json files exist."""
    if not logs_path.exists():
        return False

    for exp_dir in logs_path.iterdir():
        if not exp_dir.is_dir():
            continue

        sessions_file = exp_dir / "sessions.json"
        omni_file = exp_dir / "omni_sessions.json"

        if sessions_file.exists() or omni_file.exists():
            return True

    return False


def run_hp_comparison():
    """Run HP comparison analysis."""
    print("\n" + "-" * 60)
    print("HP COMPARISON ANALYSIS")
    print("-" * 60 + "\n")

    hp_script = Path(__file__).parent / "Purple" / "Data_analysis" / "hp_comparison_cli.py"

    if not hp_script.exists():
        print(f"❌ HP comparison script not found at: {hp_script}\n")
        return

    try:
        subprocess.run([sys.executable, str(hp_script)])
    except Exception as e:
        print(f"\n❌ Error running HP comparison: {e}\n")

    print()


def run_meta_analysis():
    """Run meta analysis."""
    print("\n" + "-" * 60)
    print("META ANALYSIS")
    print("-" * 60 + "\n")

    meta_script = Path(__file__).parent / "Purple" / "Data_analysis" / "meta_analysis_cli.py"

    if not meta_script.exists():
        print(f"❌ Meta analysis script not found at: {meta_script}\n")
        return

    try:
        subprocess.run([sys.executable, str(meta_script)])
    except Exception as e:
        print(f"\n❌ Error running meta analysis: {e}\n")

    print()


def run_advanced_viz():
    """Run advanced visualization tool."""
    print("\n" + "-" * 60)
    print("ADVANCED VISUALIZATIONS")
    print("-" * 60 + "\n")

    viz_script = Path(__file__).parent / "Purple" / "Data_analysis" / "run_analysis.py"

    if not viz_script.exists():
        print(f"❌ Visualization script not found at: {viz_script}\n")
        return

    try:
        subprocess.run([sys.executable, str(viz_script)])
    except Exception as e:
        print(f"\n❌ Error running visualizations: {e}\n")

    print()


def run_all_purple_analyses():
    """Run all Purple analyses in sequence."""
    print("\n" + "=" * 60)
    print("RUNNING ALL PURPLE ANALYSES")
    print("=" * 60 + "\n")

    proceed = questionary.confirm(
        "This will run HP Comparison, Meta Analysis, and Visualizations in sequence. Continue?",
        default=True
    ).ask()

    if not proceed:
        print("\nCancelled.\n")
        return

    print("\n[1/3] Running HP Comparison...")
    run_hp_comparison()

    print("\n[2/3] Running Meta Analysis...")
    run_meta_analysis()

    print("\n[3/3] Running Advanced Visualizations...")
    run_advanced_viz()

    print("\n" + "=" * 60)
    print("✓ ALL ANALYSES COMPLETE")
    print("=" * 60 + "\n")


# Helper functions
def is_float(value):
    """Check if value can be converted to float."""
    try:
        float(value)
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
