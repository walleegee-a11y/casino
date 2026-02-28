#!/usr/local/bin/python3.12 -u

import os
import getpass
from datetime import datetime
import random
import string
import sys
from prettytable import PrettyTable
import subprocess

# Default file paths
pond_var = os.getenv('casino_pond')
#csh_file_path = os.path.join(pond_var, 'config_casino.csh') 
ws_hier_file_path = os.path.join(pond_var, 'ws_casino.hier')    
dk_hier_file_path = os.path.join(pond_var, 'dk_casino.hier')    
flow_default_file_path = os.path.join(pond_var, 'flow_casino.yaml')  
flow_manager_file_path = os.path.join(pond_var, 'fm_casino.py') 

## Function to parse config_casino.csh
#def parse_config_casino(file_path):
#    env_vars = {}
#    with open(file_path, 'r') as file:
#        for line in file:
#            if line.startswith("setenv"):
#                parts = line.split()
#                env_vars[parts[1]] = parts[2].strip('"')
#    return env_vars

# Function to generate a UNIQUE_ID in Python (mimicking the C shell `date +%s` and random string)
def generate_unique_id():
    timestamp = datetime.now().strftime("%s")
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    return f"{timestamp}_{random_str}"

# Function to navigate directories and choose options with context-specific questions
def choose_option(options, question):
    while True:
        # Print the question and flush the output to ensure it appears immediately
        print(question)
        sys.stdout.flush()
        
        # Create a PrettyTable object for the options
        table = PrettyTable()
        table.field_names = ["No.", "Option"]  # Column headers
        
        # Add options to the table with their respective numbers
        for i, option in enumerate(options):
            table.add_row([i + 1, option])
        
        # Left-align the "Option" column for better readability
        table.align["Option"] = "l"

        # Print the table and flush the output
        print(table)
        sys.stdout.flush()  # Ensure table is shown before input prompt
        
        # Print the input prompt on the same line and flush the output
        #print("\nEnter number: ", end="", flush=True)
        print("\nEnter number: ", flush=True)
        
        # Get user input
        choice = input().strip()  # Strip any extra spaces
        
        # Validate the input
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        
        # If invalid choice, show error and continue loop
        print("Invalid choice. Please try again.")
        sys.stdout.flush()  # Ensure error message is shown immediately

os.environ['PYTHONUNBUFFERED'] = '1'

# Parse the configuration file to get environment variables
#env_vars = parse_config_casino(csh_file_path)
env_vars = os.environ


# Change directory to prj_base
prj_base = env_vars.get("casino_prj_base")
if prj_base:
    os.chdir(prj_base)
    print(f"--> Going to {prj_base} : $prj_base\n")
else:
    print(" Error: prj_base is not set in the configuration file.")
    exit(1)


# Automatically determine the project name and workspace path
prj_name = env_vars['casino_prj_name']
username = getpass.getuser()  # Get the username using `getpass.getuser()`
user_workspace = f"works_{username}"

workspace_dir = os.path.join(prj_name, user_workspace)

# Check if the workspace directory exists
if not os.path.exists(workspace_dir):
    print(f"Error: Workspace directory {workspace_dir} does not exist.")
    exit(1)

# List all available top-level directories (Block Names like clk_gen, dgt_top_rdp180xp, img_proc)
top_dirs = [d for d in os.listdir(workspace_dir) if os.path.isdir(os.path.join(workspace_dir, d))]

# Allow the user to select a Block Name
chosen_top_dir = choose_option(top_dirs, "\nPlease choose a Block Name:")
chosen_top_dir_path = os.path.join(workspace_dir, chosen_top_dir)

# List all available specific workspace directories (without roles)
ws_dirs = [d for d in os.listdir(chosen_top_dir_path) if os.path.isdir(os.path.join(chosen_top_dir_path, d))]

# Allow the user to select the Specific Workspace (WS)
chosen_ws = choose_option(ws_dirs, "\nPlease choose a Workspace (WS):")
chosen_ws_path = os.path.join(chosen_top_dir_path, chosen_ws)

# Navigate to the 'runs' directory
runs_dir_path = os.path.join(chosen_ws_path, 'runs')
if not os.path.exists(runs_dir_path):
    print(f"Error: 'runs' directory does not exist in {chosen_ws_path}.")
    exit(1)

# List all available run directories (e.g., 000, 001, 002_run, 005_run)
run_dirs = [d for d in os.listdir(runs_dir_path) if os.path.isdir(os.path.join(runs_dir_path, d))]

# Allow the user to select a Run directory
chosen_run_dir = choose_option(run_dirs, "\nPlease choose a Run Directory:")
chosen_run_dir_path = os.path.join(runs_dir_path, chosen_run_dir)

# Ask the user if they want to go to the selected run directory
#change_dir = input(f"Do you want to go to the selected run directory '{chosen_run_dir_path}'? (y/n): ").strip().lower()
# Print the prompt first
print(f"Do you want to go to '{chosen_run_dir_path}'? (y/n): ")
# Then capture the user input
change_dir = input().strip().lower()

# If user selects 'y', change to the run directory
if change_dir == 'y':
    os.chdir(chosen_run_dir_path)
    print(f"Changed to directory: {chosen_run_dir_path}")
else:
    print(f"Continuing without changing directory.")

# Get the current working directory (pwd)
current_dir = os.getcwd()

# Get the current date and time in YYYY-MM-DD_HH:MM:SS format
current_date_time = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

# Generate the UNIQUE_ID using Python
#unique_id = generate_unique_id()
unique_id = os.environ.get('UNIQUE_ID') or generate_unique_id()

# Create the temporary file in /tmp using the Python-generated UNIQUE_ID
tmp_file = f"/tmp/tmp_wsnv_casino_{username}_{unique_id}.csh"

# Create the C shell script and include the UNIQUE_ID, works_'username' and environment variables
with open(tmp_file, 'w') as tmp_file_handle:
    tmp_file_handle.write("#! /bin/csh\n")
    tmp_file_handle.write(f"setenv UNIQUE_ID {unique_id}\n")
    tmp_file_handle.write(f"setenv {chosen_top_dir} \"{user_workspace} {chosen_ws} {chosen_run_dir} {current_date_time}\"\n")
    if change_dir == 'y':
        prj_base_path = os.path.join(env_vars['casino_prj_base'])
        full_run_dir_path = os.path.join(prj_base_path, chosen_run_dir_path)
        tmp_file_handle.write(f"cd {full_run_dir_path}\n")

# Make the temporary file executable
os.chmod(tmp_file, 0o755)


# Use subprocess to open gnome-terminal from PyQt5
if change_dir == 'y':
    try:
        # Set the terminal title
        terminal_title = f"{chosen_run_dir_path} - {current_date_time}"

        # Path to the config_casino.csh file
        config_casino_path = os.path.join(pond_var, 'config_casino.csh')

        # Ensure the file exists before proceeding
        if not os.path.exists(config_casino_path):
            print(f"Error: {config_casino_path} does not exist.")
            exit(1)

        # Run gnome-terminal using subprocess with a custom title
        subprocess.Popen([
            'gnome-terminal',
            '--title', terminal_title,
            '--', 'csh', '-c',
            f'source {config_casino_path}; cd {full_run_dir_path}; exec csh'
        ], env=os.environ)

        print(f"Opened gnome-terminal at {full_run_dir_path} with title '{terminal_title}' and sourced {config_casino_path}")
    except Exception as e:
        print(f"Failed to open gnome-terminal: {e}")

# Write or append to the file in the project directory with the new filename format
info_file_path = os.path.join(env_vars['casino_prj_base'], prj_name, "outfeeds", "___BLK_INFO___" ,f"{chosen_top_dir}.{chosen_ws}.ws.info")
os.makedirs(os.path.dirname(info_file_path), exist_ok=True)
with open(info_file_path, 'a') as info_file_handle:  # Open in append mode
    #info_file_handle.write(f"setenv {user_workspace} {chosen_top_dir}\n")  # Write works_{username}
    info_file_handle.write(f"setenv {chosen_top_dir} \"{user_workspace} {chosen_ws} {chosen_run_dir} {current_date_time}\"\n")

#print(f"\nFinal choice: \nProject = {prj_name}, \nBlock Name = {chosen_top_dir}, \nWorkspace = {chosen_ws}, \nRun Version = {chosen_run_dir}, \nDate and Time = {current_date_time}")

# Create a PrettyTable object
table = PrettyTable()

# Add columns to the table
table.field_names = ["Field", "Value"]
table.add_row(["Project", prj_name])
table.add_row(["Block Name", chosen_top_dir])
table.add_row(["Workspace", chosen_ws])
table.add_row(["Run Version", chosen_run_dir])
table.add_row(["Date and Time", current_date_time])
table.align["Field"] = "l"  # 'l' stands for left alignment
table.align["Value"] = "l"  # 'l' stands for left alignment
# Print the table
print("\nFinal choice:")
print(table)

print(f"\nFinal path: {chosen_run_dir_path}")
print(f"\nEnvironment variables written to {tmp_file} and appended to {info_file_path}, and both files are made executable.")
