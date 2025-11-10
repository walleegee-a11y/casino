#!/usr/local/bin/python3.12

import os
import subprocess
import shutil
import argparse
import sys
from prettytable import PrettyTable
import re

# Default file paths
pond_var = os.getenv('casino_pond')
csh_file_path =            os.path.join(pond_var, 'config_casino.csh')
ws_hier_file_path =        os.path.join(pond_var, 'ws_casino.hier')
dk_hier_file_path =        os.path.join(pond_var, 'dk_casino.hier')
flow_default_file_path =   os.path.join(pond_var, 'common_casino','flow' ,'flow_casino.yaml')
flow_manager_file_path =   os.path.join(pond_var, 'fm_casino.py')
globals_dir_path =         os.path.join(pond_var, 'globals')
common_dir_path        =   os.path.join(pond_var, 'common_casino')

common_dir_path = os.path.join(pond_var, 'common_casino')
def get_env_vars():
    """Source the config_casino.csh file and capture the environment variables."""
    command = f'env'
    try:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, executable='/bin/csh')
        env_vars = {}
        for line in proc.stdout:
            (key, _, value) = line.decode('utf-8').partition('=')
            env_vars[key.strip()] = value.strip()
        proc.communicate()
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, command)
        return env_vars
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to get env_vars: {e}")
        sys.exit(1)

def replace_placeholders_in_hier(ws_hier_file_path, env_vars):
    """Replace placeholders in ws_casino.hier based on the sourced environment variables."""
    try:
        with open(ws_hier_file_path, 'r') as file:
            content = file.read()

        content = content.replace('$prj', env_vars['casino_prj_name'])
        content = content.replace('$whoami', env_vars['casino_whoami'])
        content = content.replace('$top_name', env_vars['casino_top_name'])
        #content = content.replace('$role', env_vars['casino_role'])
        content = content.replace('$ws', env_vars['ws'])
        content = content.replace('$run_ver', env_vars['casino_run_ver'])

        return content.splitlines()
    except Exception as e:
        print(f"Error: Failed to replace placeholders in {ws_hier_file_path} with error: {e}")
        sys.exit(1)

def choose_top_name(env_vars):
    """Allow user to choose the top_name from the all_blks list."""
    all_blks = env_vars['casino_all_blks'].split()
    table = PrettyTable()
    table.field_names = ["Number", "Block Name"]
    table.align = "l"  # Align text to the left

    for i, blk in enumerate(all_blks, 1):
        table.add_row([i, blk])

    print("\nChoose the top_name by entering the corresponding number:")
    print(table)

    choice = -1
    while choice < 1 or choice > len(all_blks):
        try:
            choice = int(input("Enter the number corresponding to the block: "))
            if choice < 1 or choice > len(all_blks):
                print(f"Please enter a number between 1 and {len(all_blks)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    chosen_blk = all_blks[choice - 1]
    env_vars['casino_top_name'] = chosen_blk
    # Store chosen_blk in a global variable so other functions can access it
    global global_chosen_blk
    global_chosen_blk = chosen_blk
    print(f"Chosen top_name: {chosen_blk}")


def choose_role(env_vars):
    """Prompt the user to choose between 'pi' and 'pd' roles."""
    roles = ['pi', 'pd']
    table = PrettyTable()
    table.field_names = ["Number", "Role"]
    table.align = "l"  # Align text to the left

    for i, role in enumerate(roles, 1):
        table.add_row([i, role])

    print("\nChoose the role by entering the corresponding number:")
    print(table)

    choice = -1
    while choice < 1 or choice > len(roles):
        try:
            choice = int(input("Enter the number corresponding to the role: "))
            if choice < 1 or choice > len(roles):
                print(f"Please enter a number between 1 and {len(roles)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    chosen_role = roles[choice - 1]
    env_vars['casino_role'] = chosen_role
    print(f"Chosen role: {chosen_role}")


def filter_role_specific_lines(ws_hier_lines, role):
    """Filter out the lines specific to the chosen role (pi or pd) using regular expressions."""
    filtered_lines = []
    include_lines = True

    # Compile regular expressions for matching role-specific sections
    role_start_pattern = re.compile(rf"#\s*{role}\s*-\s*start")
    role_end_pattern = re.compile(rf"#\s*{role}\s*-\s*end")
    other_role_start_pattern = re.compile(r"#\s*\w+\s*-\s*start")
    other_role_end_pattern = re.compile(r"#\s*\w+\s*-\s*end")

    for line in ws_hier_lines:
        # Check for role-specific sections using regular expressions
        if role_start_pattern.search(line):
            include_lines = True
        elif role_end_pattern.search(line):
            include_lines = False
        elif other_role_start_pattern.search(line):
            include_lines = False
        elif other_role_end_pattern.search(line):
            include_lines = True

        # Add the line to filtered_lines only if it's part of the chosen role or outside of any role-specific section
        if include_lines:
            filtered_lines.append(line)

    return filtered_lines


def parse_ws_hier_lines(ws_hier_lines, env_vars):
    """Parse the lines of ws_casino.hier after placeholders have been replaced to create directories, handling $all_blks expansion."""
    try:
        dirs_to_create = []
        current_path = []
        previous_depth = -1
        #all_blks_list = env_vars['casino_all_blks'].split()  # Get the list of block names from the environment
        all_blks_list = env_vars['casino_all_blks'].split() + ["___BLK_INFO___"]  # Get the list of block names and add "___BLK_INFO___"

        for line in ws_hier_lines:
            line = line.rstrip()
            if line and not line.startswith('#'):
                stripped_line = line.lstrip().strip()
                depth = (len(line) - len(stripped_line)) // 4

                real_dir_name = stripped_line.split()[-1]

                if real_dir_name == "$all_blks":
                    # Expand each block name under $all_blks in `outfeeds`
                    for block_name in all_blks_list:
                        expanded_path = os.path.join(*current_path, block_name)
                        dirs_to_create.append((expanded_path, depth))
                else:
                    if depth > previous_depth:
                        current_path.append(real_dir_name)
                    elif depth == previous_depth:
                        current_path[-1] = real_dir_name
                    else:
                        current_path = current_path[:depth] + [real_dir_name]

                    previous_depth = depth
                    full_path = os.path.join(*current_path)
                    dirs_to_create.append((full_path, depth))

        return dirs_to_create
    except Exception as e:
        print(f"Error: Failed to parse ws_casino.hier lines with error: {e}")
        sys.exit(1)


def create_directory_structure(base_path, dirs_to_create, env_vars):
    """Create directories based on parsed ws_casino.hier lines, handling the special case for $all_blks."""
    for directory, depth in dirs_to_create:
        # Replace the placeholder $all_blks with actual block names if present in the directory path
        if "$all_blks" in directory:
            # Fetch all blocks from the environment variable and replace $all_blks in path
            for block in env_vars['casino_all_blks'].split():
                dir_with_block = directory.replace("$all_blks", block)
                full_path = os.path.join(base_path, dir_with_block)
                try:
                    if not os.path.exists(full_path):
                        os.makedirs(full_path, exist_ok=True)
                        print(f"Created directory for block: {full_path} (Depth {depth})")
                except Exception as e:
                    print(f"Error: Failed to create directory {full_path} with error: {e}")
                    sys.exit(1)
        else:
            # Create directory normally for all other paths
            full_path = os.path.join(base_path, directory)
            try:
                if not os.path.exists(full_path):
                    os.makedirs(full_path, exist_ok=True)
                    print(f"Created directory: {full_path} (Depth {depth})")
            except Exception as e:
                print(f"Error: Failed to create directory {full_path} with error: {e}")
                sys.exit(1)


def print_info_table(design_ver, dk_ver, tag):
    """Print a simple table with design_ver, dk_ver, and tag information."""
    print("+-------------+----------------+")
    print("|   Variable  |      Value     |")
    print("+-------------+----------------+")
    print(f"| design_ver  | {design_ver:<14} |")
    print(f"| dk_ver      | {dk_ver:<14} |")
    print(f"| tag         | {tag:<14} |")
    print("+-------------+----------------+")

def display_ws_info(ws):
    """Print the $ws information."""
    print(f"\nWorkspace (ws): {ws}")

def list_runs_directories(runs_path):
    """List all directories under the runs directory."""
    try:
        if os.path.exists(runs_path):
            run_dirs = [d for d in os.listdir(runs_path) if os.path.isdir(os.path.join(runs_path, d))]
            if run_dirs:
                print("\nExisting Runs Directories:")
                for run_dir in sorted(run_dirs):
                    print(f"- {run_dir}")
            else:
                print("No existing runs directories found.")
        else:
            print("Runs directory path does not exist yet.")
    except Exception as e:
        print(f"Error: Failed to list runs directories with error: {e}")
        sys.exit(1)

def list_runs_directories_after_creating(runs_path):
    """List all directories under the runs directory."""
    try:
        run_dirs = [d for d in os.listdir(runs_path) if os.path.isdir(os.path.join(runs_path, d))]
        if run_dirs:
            print("\nCurrent Runs Directories:")
            for run_dir in sorted(run_dirs):
                print(f"- {run_dir}")
        else:
            print("No existing runs directories found.")
    except Exception as e:
        print(f"Error: Failed to list runs directories after creating with error: {e}")
        sys.exit(1)

def copy_files_to_runs(ws_path):
    """
    Completely replace 'ws_path/common' with 'common_dir_path', overwriting existing files and directories.

    Args:
        ws_path (str): The workspace path where the 'common' directory resides.
    """
    # Convert ws_path to an absolute path
    ws_path = os.path.abspath(ws_path)
    src_common_dir = os.path.abspath(common_dir_path)
    common_dest_path = os.path.join(ws_path, 'common')

    try:
        # Remove the destination directory if it exists
        if os.path.exists(common_dest_path):
            shutil.rmtree(common_dest_path)

        # Copy the entire source directory to the destination
        shutil.copytree(src_common_dir, common_dest_path)
    except PermissionError as pe:
        sys.exit(1)
    except FileNotFoundError as fnfe:
        sys.exit(1)
    except Exception as e:
        sys.exit(1)


def copy_files_to_runs_local(ws_path, run_ver):
    """
    Completely replace 'ws_path/runs/run_ver/common' with 'common_dir_path', overwriting existing files and directories.

    Args:
        ws_path (str): The workspace path where the 'runs' directory resides.
        run_ver (str): The run version directory under 'runs'. This should include all necessary subdirectories.
    """
    # Convert ws_path to an absolute path
    ws_path = os.path.abspath(ws_path)

    # Do NOT convert run_ver to an absolute path; it should remain a relative path within 'runs'
    # Example of run_ver: 'rdp180xp/works_jeff.lee/row_drv/pi___rtl_3.0_dk_3.1_tag_2.0/FFN_fe00_te29_pv00'
    common_dest_path = os.path.join(ws_path, 'runs', run_ver, 'common')

    src_common_dir = os.path.abspath(common_dir_path)

    try:
        # Remove the destination directory if it exists
        if os.path.exists(common_dest_path):
            shutil.rmtree(common_dest_path)

        # Ensure the parent directories exist
        parent_dir = os.path.dirname(common_dest_path)
        os.makedirs(parent_dir, exist_ok=True)

        # Copy the entire source directory to the destination
        shutil.copytree(src_common_dir, common_dest_path)
    except PermissionError as pe:
        sys.exit(1)
    except FileNotFoundError as fnfe:
        sys.exit(1)
    except Exception as e:
        sys.exit(1)


def copy_csh_file_to_run_ver(dest_run_path):
    """
    Copy the config_casino.csh file (pointed by csh_file_path) to the given run version directory.

    Args:
        dest_run_path (str): The full path of the run version directory.
    """
    try:
        if os.path.exists(csh_file_path):
            shutil.copy(csh_file_path, dest_run_path)
            print(f"Copied {csh_file_path} to {dest_run_path}")
        else:
            print(f"Error: {csh_file_path} does not exist.")
    except Exception as e:
        print(f"Error: Failed to copy {csh_file_path} to {dest_run_path} with error: {e}")
        sys.exit(1)


def create_csh_script(run_ver, dest_path):
    """Create an executable C Shell script named :run_flow_mgr_${run_ver}.csh, replacing '/' in run_ver with '_'."""
    # Replace any '/' in run_ver with '_' to avoid directory issues in script filename
    sanitized_run_ver = run_ver.replace("/", "_")
    #script_name = f":run_flow_mgr_{sanitized_run_ver}.csh"
    script_name = f":run_flow_mgr.csh"
    script_path = os.path.join(dest_path, script_name)

    script_content = f"""#!/bin/csh -f

if (-e ./common/flow/flow_casino.yaml) then
    {pond_var}/fm_casino.py -flow ./common/flow/flow_casino.yaml -only $1 -terminal xterm
else
    {pond_var}/fm_casino.py -flow ../../common/flow/flow_casino.yaml -only $1 -terminal xterm
endif
"""
    try:
        with open(script_path, 'w') as script_file:
            script_file.write(script_content)
        os.chmod(script_path, 0o775)
        print(f"Created C Shell script: {script_path}")
    except Exception as e:
        print(f"Error: Failed to create script {script_path} with error: {e}")
        sys.exit(1)

def dump_env_and_copy_tool_env(run_stage_dir):
    """Dump environment variables to the given directory and copy tool env."""
    try:
        # Ensure the destination directory exists
        if not os.path.exists(run_stage_dir):
            os.makedirs(run_stage_dir)

        # Define the path for the environment dump file
        env_dump_path = os.path.join(run_stage_dir, 'env_vars.csh')

        # Check if config_casino.csh exists
        if not os.path.isfile(csh_file_path):
            QtWidgets.QMessageBox.critical(None, "Error", f"The file {csh_file_path} does not exist.")
            return

        # Step 1: Extract setenv variable names from config_casino.csh
        setenv_vars = set()
        setenv_pattern = re.compile(r'^\s*setenv\s+(\w+)\s+["\']?.*["\']?\s*$')

        with open(csh_file_path, 'r') as csh_file:
            for line in csh_file:
                match = setenv_pattern.match(line)
                if match:
                    var_name = match.group(1)
                    setenv_vars.add(var_name)

        if not setenv_vars:
            QtWidgets.QMessageBox.critical(None, "Error", f"No setenv variables found in {csh_file_path}.")
            return

        # Step 2: Filter current environment variables based on extracted names
        filtered_env = {}
        missing_vars = []
        for var in setenv_vars:
            if var in os.environ:
                filtered_env[var] = os.environ[var]
            else:
                missing_vars.append(var)

        if missing_vars:
            warning_message = f"The following setenv variables are not set in the current environment: {', '.join(missing_vars)}"
            QtWidgets.QMessageBox.warning(None, "Warning", warning_message)

        if not filtered_env:
            QtWidgets.QMessageBox.critical(None, "Error", "No matching environment variables found to dump.")
            return

        # Step 3: Dump the filtered environment variables to env_vars.csh
        with open(env_dump_path, 'w') as env_file:
            for key, value in filtered_env.items():
                if key == "top_name":
                    # Use the user-chosen value stored in global_chosen_blk
                    try:
                        chosen_value = global_chosen_blk
                    except NameError:
                        chosen_value = value
                    env_file.write(f'setenv top_name "{chosen_value}"\n')
                else:
                    # Escape double quotes in the value
                    escaped_value = value.replace('"', '\\"')
                    env_file.write(f'setenv {key} "{escaped_value}"\n')
        print(f"Dumping environment variables to {env_dump_path}")

        # Copy tools env file
        source_file = os.getenv('casino_all_tools_env')
        if source_file and os.path.exists(source_file):
            shutil.copy(source_file, run_stage_dir)
            print(f"File {source_file} copied to {run_stage_dir}")
        else:
            print(f"Error: Tool env file {source_file} not found.")
    except Exception as e:
        raise RuntimeError(f"Error during env dump and copy: {e}")


def process_stage_directories(base_path, dirs_to_create, env_vars, run_ver):
    """Process directories for dumping environment variables and copying the tools env."""
    stage_dirs = ['apr', 'pex', 'pv', 'psi', 'bump']  # Add more if needed

    for directory, depth in dirs_to_create:
        # Extract the last directory name (stage) from the path to check if it's a stage directory
        last_dir_name = os.path.basename(directory)

        # Ensure we're processing directories under runs/{run_ver} and it's one of the stage dirs
        if f"/runs/{run_ver}/" in directory and last_dir_name in stage_dirs:
            run_stage_dir = os.path.join(base_path, directory)
            print(f"Processing stage directory: {run_stage_dir}")  # Debug output
            try:
                dump_env_and_copy_tool_env(run_stage_dir)
            except Exception as e:
                print(f"Error during env dump and copy: {e}")
        else:
            print(f"Skipping directory: {directory}")  # Debugging skipped directories

def get_stage_directories(dirs_to_create, run_ver):
    """Dynamically collect the stage directories based on their depth in the hierarchy, excluding non-stage directories like 'common'."""
    stage_dirs = []
    excluded_dirs = {'common'}  # Add more non-stage directories to this set if needed

    for directory, depth in dirs_to_create:
        # Check if the directory is under runs/{run_ver}, at depth 6, and is not in the excluded directories
        if f"/runs/{run_ver}/" in directory and depth == 6:
            dir_name = os.path.basename(directory)
            if dir_name not in excluded_dirs:
                stage_dirs.append(dir_name)

    return stage_dirs

def process_stage_directories(base_path, dirs_to_create, env_vars, run_ver):
    """Process directories for dumping environment variables and copying the tools env."""
    # Dynamically collect stage directories
    stage_dirs = get_stage_directories(dirs_to_create, run_ver)
    print(f"Dynamically collected stage directories: {stage_dirs}")  # Debug output

    for directory, depth in dirs_to_create:
        # Extract the last directory name (stage) from the path to check if it's a stage directory
        last_dir_name = os.path.basename(directory)

        # Ensure we're processing directories under runs/{run_ver} and it's one of the dynamic stage dirs
        if f"/runs/{run_ver}/" in directory and last_dir_name in stage_dirs:
            run_stage_dir = os.path.join(base_path, directory)
            print(f"Processing stage directory: {run_stage_dir}")  # Debug output
            try:
                dump_env_and_copy_tool_env(run_stage_dir)
            except Exception as e:
                print(f"Error during env dump and copy: {e}")
        else:
            print(f"Skipping directory: {directory}")  # Debugging skipped directories


def notify_run_creation(run_path, run_version, tree_manager_history_service=None):
    """
    Notify that a run directory has been created.
    If called from casino_gui with history service, updates it directly.
    Otherwise, this is a no-op (for standalone execution).

    Args:
        run_path: Full path to the created run directory
        run_version: Run version identifier
        tree_manager_history_service: Optional DirectoryHistoryService instance from Tree Manager
    """
    if tree_manager_history_service is not None:
        try:
            from pathlib import Path
            from datetime import datetime

            # Add create_run operation to history service
            tree_manager_history_service.add_entry(
                path=Path(run_path),
                operation="create_run",
                details=f"Created run directory: {run_version}"
            )
            print(f"\n? Run creation added to Tree Manager history")
            print(f"  - Run: {run_version}")
            print(f"  - Path: {run_path}")
            print(f"  - Check Recent area in Tree Manager for the 'Run' button\n")
        except Exception as e:
            print(f"\n? Warning: Could not update Tree Manager history: {e}\n")

def write_casino_env_vars(env_vars, runs_path):
    """
    Write environment variables to config_casino.csh in organized sections:
    1) Workspace-specific vars,
    2) General casino scripts,
    3) Tools environment file path.
    Sections and ordering follow the master config template.

    Args:
        env_vars: Ordered dict of environment variables
        runs_path: Path to the runs directory
    """
    import os, sys
    try:
        output_file = os.path.join(runs_path, 'config_casino.csh')
        # Define sections and their keys in desired order
        workspace_keys = [
            'casino_prj_base', 'casino_prj_name', 'casino_design_ver',
            'casino_dk_ver', 'casino_tag', 'casino_is_top',
            'casino_top_name', 'casino_all_blks'
        ]
        general_keys = [k for k in env_vars if k.startswith('casino_') \
                        and k not in workspace_keys \
                        and k not in ('casino_all_tools_env',) \
                        and not k.endswith('_py')]
        script_keys = [k for k in env_vars if k.endswith('_py')]
        tools_env_key = 'casino_all_tools_env'

        # Open and write
        with open(output_file, 'w') as f:
            f.write("#! /bin/csh -f\n")
            f.write("##################################\n")
            f.write("# env   (casino - workspace)     #\n")
            f.write("##################################\n")
            for key in workspace_keys:
                if key in env_vars:
                    f.write(f"setenv {key} \"{env_vars[key]}\"\n")
            f.write("##################################\n")
            f.write("# env   (casino/general)         #\n")
            f.write("##################################\n")
            for key in general_keys:
                f.write(f"setenv {key} \"{env_vars[key]}\"\n")
            f.write("# utils\n")
            for key in script_keys:
                f.write(f"setenv {key} \"{env_vars[key]}\"\n")
            f.write("# tools env\n")
            if tools_env_key in env_vars:
                f.write(f"setenv {tools_env_key} \"{env_vars[tools_env_key]}\"\n")

        os.chmod(output_file, 0o755)
    except Exception as e:
        print(f"Error: Failed to write casino environment variables with error: {e}")
        sys.exit(1)


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Create workspace and copy flow control files.")
    parser.add_argument("-flow", type=str, default=flow_default_file_path, help=f"Specify the flow file to use. Default is '{flow_default_file_path}'.")
    args = parser.parse_args()

    # Source the C Shell script to extract environment variables
    env_vars = get_env_vars()

    # Get the current user (equivalent of whoami)
    env_vars['casino_whoami'] = subprocess.getoutput('whoami')

    # Choose the top_name from all_blks
    choose_top_name(env_vars)

    # Prompt user to choose a role and add it to $ws
    choose_role(env_vars)

    # Construct the $ws variable with role
    env_vars['ws'] = f"{env_vars['casino_role']}___{env_vars['casino_design_ver']}_{env_vars['casino_dk_ver']}_{env_vars['casino_tag']}"

    # Print info table for design_ver, dk_ver, and tag
    print_info_table(env_vars['casino_design_ver'], env_vars['casino_dk_ver'], env_vars['casino_tag'])

    # Display $ws information
    display_ws_info(env_vars['ws'])

    # Define the runs_path
    runs_path = os.path.join(env_vars['casino_prj_name'], f"works_{env_vars['casino_whoami']}", env_vars['casino_top_name'], env_vars['ws'], "runs")

    # List existing runs before asking for run_ver
    list_runs_directories(runs_path)

    # Prompt the user for the $run_ver name and ensure input is provided
    while True:
        print("\nEnter the run version ($run_ver):")
        run_ver = input().strip()
        if not run_ver:
            print("Run version cannot be empty. Please enter a valid run version.")
            continue

        # Check if the run directory already exists
        run_dir_path = os.path.join(runs_path, run_ver)
        if os.path.exists(run_dir_path):
            print(f"\nError: The run directory '{run_dir_path}' already exists. Please choose a different run version.")
        else:
            break

    env_vars['casino_run_ver'] = run_ver

    # Replace placeholders in ws_casino.hier content
    ws_hier_lines = replace_placeholders_in_hier(ws_hier_file_path, env_vars)
    ws_hier_lines = filter_role_specific_lines(ws_hier_lines, env_vars['casino_role'])

    # Parse the ws_casino.hier lines to get the list of directories to create
    dirs_to_create = parse_ws_hier_lines(ws_hier_lines, env_vars)

    # Create the directory structure based on the parsed ws_casino.hier lines, skipping existing ones
    base_path = '.'  # Assuming the base path is the current directory
    create_directory_structure(base_path, dirs_to_create, env_vars)

    # Copy fm_casino.py and the specified flow file to the runs directory under $ws
    ws_path = os.path.join(env_vars['casino_prj_name'], f"works_{env_vars['casino_whoami']}", env_vars['casino_top_name'], env_vars['ws'])
    copy_files_to_runs(ws_path)

    # Dynamically collect the stage directories
    stages = get_stage_directories(dirs_to_create, env_vars['casino_run_ver'])
    # Copy fm_casino.py and the specified flow file to the runs directory under $ws and stage-specific directories
    copy_files_to_runs_local(ws_path, env_vars['casino_run_ver'])

    # Process the directories to dump environment variables and copy tool env file
    process_stage_directories(base_path, dirs_to_create, env_vars, env_vars['casino_run_ver'])


    # Re Define the runs_path
    runs_path = os.path.join(env_vars['casino_prj_name'], f"works_{env_vars['casino_whoami']}", env_vars['casino_top_name'], env_vars['ws'], "runs", env_vars['casino_run_ver'])

    # Create the executable C Shell script in the runs directory
    create_csh_script(env_vars['casino_run_ver'], runs_path)


    # Copy the config_casino.csh file into the run version directory
    #copy_csh_file_to_run_ver(runs_path)

    # List directories after creating runs
    list_runs_directories_after_creating(runs_path)

    # Write casino environment variables to con_casino.csh file
    write_casino_env_vars(env_vars, runs_path)

    # ===== Add run creation to directory history =====
    print("\n" + "="*70)
    print("Recording run creation in directory history...")
    print("="*70)

    try:
        from pathlib import Path
        from history_utils import add_run_creation_history

        # Get full path to the created run directory
        full_run_path = Path(runs_path).absolute()

        # Project base should be prj_base + prj_name (e.g., /mnt/data/prjs/ANA6716)
        prj_base_dir = Path(env_vars.get('casino_prj_base', '.'))
        prj_name = env_vars['casino_prj_name']
        project_directory = prj_base_dir / prj_name

        # Add history entry for run creation
        success, message = add_run_creation_history(
            run_path=full_run_path,
            run_version=env_vars['casino_run_ver'],
            project_base=project_directory,
            project_name=prj_name
        )

        if success:
            print(f"? {message}")
            print(f"  - Run path: {full_run_path}")
            print(f"  - Run version: {env_vars['casino_run_ver']}")
            print(f"  - User: {env_vars['casino_whoami']}")
            print(f"  - This will appear as a 'Run' button in Tree Manager's Recent area")
        else:
            print(f"? Warning: {message}")

    except ImportError as e:
        print(f"? Warning: history_utils.py not found - skipping history update")
        print(f"  Error: {e}")
        print(f"  Note: History tracking is optional and won't affect run creation")
    except Exception as e:
        print(f"? Warning: Could not update directory history: {e}")
        print(f"  Note: This is non-fatal - run creation was successful")
        import traceback
        traceback.print_exc()

    print("="*70 + "\n")
    # ===== End history update =====

if __name__ == "__main__":
    main()

