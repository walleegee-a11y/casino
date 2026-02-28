#! /usr/local/bin/python3.12 -u

import os
import re
import subprocess
import time
import sys
from prettytable import PrettyTable
import colorama
from colorama import Fore, Style
import time

# Function to parse the configuration file and extract environment variables
def parse_config(file_path):
    env_vars = {}
    with open(file_path, 'r') as file:
        for line in file:
            # Look for lines that start with 'setenv'
            match = re.match(r'setenv\s+(\w+)\s+"?([^"\s]+)"?', line)
            if match:
                var_name = match.group(1)
                var_value = match.group(2)
                # Resolve any environment variable references within the value
                var_value = re.sub(r'\$(\w+)', lambda m: env_vars.get(m.group(1), m.group(0)), var_value)
                env_vars[var_name] = var_value
    return env_vars

# Function to display the selected setenv variables in a table format using PrettyTable
def display_selected_env_vars(env_vars, selected_vars):
    table = PrettyTable()
    table.field_names = ["Variable", "Value"]

    for var_name in selected_vars:
        if var_name in env_vars:
            table.add_row([var_name, env_vars[var_name]])

    # Set alignment to left for all columns
    table.align = "l"

    print(table)
    #print("\nCheck project base path & dk version carefully.")

# Function to display help for casino_dk_mgr script using PrettyTable
def display_casino_dk_mgr_help():
    table = PrettyTable()
    table.title = "casino_dk_mgr Help"
    table.field_names = ["Option", "Description"]

    #table.add_row(["-config", "Path to config_casino.csh (default)"])
    table.add_row(["-init_git", "Initialize and commit to Git"])
    table.add_row(["-create_ver", "Flag to create db_ver (no value is required)"])
    table.add_row(["-link_set", "ver.make describing design, mem, pdk, std, io, ip, and misc"])
    table.add_row(["-link_ver", "Version name for linking"])

    # Set alignment to left for all columns
    table.align = "l"

    print(table)

# Function to display help for casino_flow_mgr script using PrettyTable
def display_casino_flow_mgr_help():
    table = PrettyTable()
    table.title = "casino_flow_mgr Help"
    table.field_names = ["Option", "Description"]

    table.add_row(["-start", "Set the start task"])
    table.add_row(["-end", "Set the end task"])
    table.add_row(["-only", "Set the subtasks only"])
    table.add_row(["-force", "Force tasks ignoring status completed"])
    table.add_row(["-flow", "Set flow_casino.yaml"])
    table.add_row(["-singleTerm", "Execute in a single terminal"])
    table.add_row(["--interactive", "To handle interactive tasks"])
    #table.add_row(["-run_ver", "Set the run ver directory under the 'runs' directory"])
    #table.add_row(["-stage", "Set the stage in the run ver directory"])

    # Set alignment to left for all columns
    table.align = "l"

    print(table)

# Function to animate text by printing it character by character
def animate_text(text, delay=0.05):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

# Function to display available options and a quit option in a table format using PrettyTable with animation
def display_options(scripts):
    table = PrettyTable()
    table.title = "CASINO Managers"
    table.field_names = ["No.", "Manager"]

    # Populate the table with script options
    for idx, (key, _) in enumerate(scripts.items(), start=1):
        table.add_row([idx, key])

    # Add a "Quit" option at the end
    table.add_row([len(scripts) + 1, "Quit"])

    # Set alignment to left for all columns
    table.align = "l"

    # Display the table with animation for the title text
    animate_text(" Welcome, which lever are you going to pull?", delay=0.005)

    # Display the table of options after the lever animation
    print(table)

# Function to select a script or quit
def select_script(scripts):
    while True:
        display_options(scripts)
        print(f" Enter the number of the manager: ")
        choice = input().strip()
        if choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= len(scripts):
                selected_key = list(scripts.keys())[choice - 1]
                return selected_key
            elif choice == len(scripts) + 1:  # If user chooses the Quit option
                print("\n Exiting the CASINO. Goodbye!\n")
                sys.exit(0)
        else:
            print(f" Invalid selection: {choice}. Please enter a valid number.")

# Function to execute the selected script and display output in real-time
def execute_script(scripts, selected_key, initial_dir):
    while True:
        if selected_key:
            script_path = scripts[selected_key]

            # Check if dk_mgr or flow_mgr is selected and show help
            if selected_key == 'casino_dk_mgr':
                display_casino_dk_mgr_help()
            elif selected_key == 'casino_flow_mgr':
                display_casino_flow_mgr_help()
                os.chdir(initial_dir)  # Change back to the initial directory for flow_mgr

            if selected_key in ['casino_dk_mgr', 'casino_flow_mgr']:
                command = ""
                while not command:  # Keep asking until the user provides input
                    print(f" Enter the command/options to execute {selected_key}.py: ")
                    command = input().strip()
                    if not command:
                        print(" Command cannot be empty. Please provide a valid command or option.")
            else:
                command = ""

            command_args = command.split()  # Split the command into arguments
            full_command = [script_path] + command_args  # Build the full command as a list
            print(f" Executing: {' '.join(full_command)} ...")
            #print("-" * 80)
            # Use subprocess.Popen to execute the command and stream output in real-time
            process = subprocess.Popen(full_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8', errors='replace')

            # Stream the output to the console as it is produced
            while True:
                output = process.stdout.read(1)
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output, end='', flush=True)

            # Wait for the process to complete
            process.wait()

            if process.returncode != 0:
                #print(f"Error executing the script.")
                print("Do you want to retry? (yes/no): ")
                retry = input().strip().lower()
                if retry in ['yes', 'y']:
                    continue  # Retry the command
                else:
                    print(" Exiting...")
                    break  # Exit the loop and finish execution
            else:
                break  # Successful execution, exit the loop
        else:
            print(" No valid script selected. Exiting.")
            break

if __name__ == "__main__":

    initial_dir = os.getcwd()  # Store the initial directory

    # Initialize colorama for Windows support
    colorama.init(autoreset=True)

    # ASCII art
    ascii_art = [
        "\n   .d$$$$b.        d$$$$      $$     $$$$$$$ $$$b    $$$  .d$$$$$b.  ",
        "  d$$P  Y$$b      d$$$$$  .d$$$$$b.    $$$   $$$$b   $$$ d$$P\" \"Y$$b ",
        "  $$$    $$$     d$$P$$$ d$$P $$\"$$b   $$$   $$$$$b  $$$ $$$     $$$ ",
        "  $$$           d$$P $$$ Y$$b.$$       $$$   $$$Y$$b $$$ $$$     $$$ ",
        "  $$$          d$$P  $$$  \"Y$$$$$b.    $$$   $$$ Y$$b$$$ $$$     $$$ ",
        "  $$$    $$$  d$$P   $$$      $$\"$$b   $$$   $$$  Y$$$$$ $$$     $$$ ",
        "  Y$$b  d$$P d$$$$$$$$$$ Y$$b $$.$$P   $$$   $$$   Y$$$$ Y$$b. .d$$P ",
        "   \"Y$$$$P\" d$$P     $$$  \"Y$$$$$P\"  $$$$$$$ $$$    Y$$$  \"Y$$$$$P\"  ",
        "                              $$                                    "
    ]

    # Print the ASCII art in light green
    for line in ascii_art:
        print(Fore.LIGHTGREEN_EX + line)

    pond_base = os.getenv('casino_pond')
    #config_file_path = os.path.join(pond_base, 'config_casino.csh')

    # Source the configuration file to set environment variables
    #subprocess.run(f"source {config_file_path}", shell=True, executable="/bin/csh")

    # Parse the config file to get the environment variables
    #env_vars = parse_config(config_file_path)
    env_vars = os.environ

    # Define the specific variables to display
    selected_vars = ["casino_prj_name", "casino_design_ver", "casino_dk_ver", "casino_tag", "casino_prj_base", "casino_casino_pond"]

    # Display the selected setenv variables
    #print("\nSelected setenv variables from config_casino.csh:\n")
    display_selected_env_vars(env_vars, selected_vars)

    # Change directory to prj_base
    prj_base = env_vars.get("casino_prj_base")
    if prj_base:
        os.chdir(prj_base)
        #print("-" * 80)
        print(f" Going to {prj_base} : $prj_base\n")
        #print("-" * 80)
    else:
        print(" Error: prj_base is not set in the configuration file.")
        exit(1)

    # Extract Python script paths from the parsed environment variables
    scripts = {
        key.replace('_py', ''): value
        for key, value in env_vars.items()
        if key.endswith('_py')
    }

    if scripts:
        selected_script = select_script(scripts)
        execute_script(scripts, selected_script, initial_dir)
    else:
        print(" No Python scripts found in the configuration file.")

