#!/usr/bin/env python3
"""
Script to rename attack files in full_logs folder by incrementing attack numbers by 96.
Example: attack_1.json -> attack_97.json
"""

import os
import re
from pathlib import Path

def rename_attack_files(full_logs_path, increment):
    """
    Rename attack files by incrementing their numbers.
    
    Args:
        full_logs_path (str): Path to the full_logs directory
        increment (int): Number to add to each attack number (default: 96)
    """
    full_logs_dir = Path(full_logs_path)
    
    if not full_logs_dir.exists():
        print(f"Error: Directory {full_logs_path} does not exist")
        return
    
    if not full_logs_dir.is_dir():
        print(f"Error: {full_logs_path} is not a directory")
        return
    
    # Pattern to match attack_X.json files
    attack_pattern = re.compile(r'^attack_(\d+)\.json$')
    
    # Get all attack files and sort them by number (descending to avoid conflicts)
    attack_files = []
    for file in full_logs_dir.iterdir():
        if file.is_file():
            match = attack_pattern.match(file.name)
            if match:
                attack_num = int(match.group(1))
                attack_files.append((attack_num, file))
    
    # Sort by attack number in descending order to avoid naming conflicts
    attack_files.sort(key=lambda x: x[0], reverse=True)
    
    if not attack_files:
        print(f"No attack files found in {full_logs_path}")
        return
    
    print(f"Found {len(attack_files)} attack files to rename")
    print(f"Incrementing attack numbers by {increment}")
    
    # Rename files
    for attack_num, file_path in attack_files:
        new_attack_num = attack_num + increment
        new_filename = f"attack_{new_attack_num}.json"
        new_path = file_path.parent / new_filename
        
        try:
            file_path.rename(new_path)
            print(f"Renamed: {file_path.name} -> {new_filename}")
        except Exception as e:
            print(f"Error renaming {file_path.name}: {e}")

if __name__ == "__main__":
    # Default path - can be changed as needed
    default_path = "/home/defend/project-violet/logs/EXPERIMENT_2_NO_RECONFIG_GPT_4_1_CONT_2025-07-20T21_32_03/hp_config_1/full_logs"
    
    # You can also pass a different path as command line argument
    import sys
    if len(sys.argv) > 1:
        target_path = sys.argv[1]
    else:
        target_path = default_path
    
    print(f"Renaming attack files in: {target_path}")
    rename_attack_files(target_path, 96)
    print("Done!")
