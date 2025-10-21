#!/usr/local/bin/python3.12

import os
import subprocess
import shutil
import sys
import re
import tempfile
import copy
import logging
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QSplitter, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QListWidget,
    QLineEdit, QPushButton, QSpinBox, QGroupBox,
    QScrollArea, QGridLayout
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt


prj_base = os.getenv('casino_prj_base')
print(f"Going to {prj_base} : $prj_base\n")

if prj_base:
    os.chdir(prj_base)

# ----------------------------
# Logging Configuration
# ----------------------------
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("teco_casino.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger()

# ----------------------------
# Default File Paths
# ----------------------------
pond_var = os.getenv('casino_pond')
if pond_var is None:
    logger.critical("'casino_pond' environment variable is not set.")
    sys.exit(1)

prj_name = os.getenv('casino_prj_name')

csh_file_path = os.path.join(pond_var, 'config_casino.csh')
ws_hier_file_path = os.path.join(pond_var, 'ws_casino.hier')
dk_hier_file_path = os.path.join(pond_var, 'dk_casino.hier')
flow_default_file_path = os.path.join(pond_var, 'common_casino/flow/flow_casino.yaml')
flow_manager_file_path = os.path.join(pond_var, 'fm_casino.py')
common_dir_path = os.path.join(pond_var, 'common_casino')
dmsa_option_file_path = os.path.join(pond_var, 'common_casino', 'user_define', f'{prj_name}_ovars.tcl')

# ----------------------------
# Define Colors
# ----------------------------
OLIVE = "#778a35"
SAGE_GREEN = "#d1e2c4"
PEWTER = "#ebebe8"
OLIVE_GREEN = "#31352e"
IVORY = "#EBECE0"
WHITE = "#F7F8F8"
DARK_BLUE = "#051537"
CHILI_PEPPER = "#BC3110"
BURNT_SIENNA = "#BE6310"
BLUE_GROTTO =  "#43B0F1"

# ----------------------------
# Define CheckableComboBox
# ----------------------------
class CheckableComboBox(QComboBox):
    def __init__(self, parent=None):
        super(CheckableComboBox, self).__init__(parent)
        self.setModel(QStandardItemModel(self))
        self.view().pressed.connect(self.handle_item_pressed)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setPlaceholderText('Select options')
        self.checked_items = []

    def addItems(self, items):
        for item in items:
            self.addItem(item)

    def addItem(self, text):
        item = QStandardItem(text)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        item.setData(Qt.Unchecked, Qt.CheckStateRole)
        self.model().appendRow(item)

    def handle_item_pressed(self, index):
        item = self.model().itemFromIndex(index)
        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
            if item.text() in self.checked_items:
                self.checked_items.remove(item.text())
        else:
            item.setCheckState(Qt.Checked)
            if item.text() not in self.checked_items:
                self.checked_items.append(item.text())
        self.update_display()

    def update_display(self):
        if self.checked_items:
            display_text = ', '.join(self.checked_items)
        else:
            display_text = 'Select options'
        self.lineEdit().setText(display_text)

    def checkedItemsList(self):
        return self.checked_items

    def setCheckedItems(self, items):
        """Set multiple items as checked."""
        self.checked_items = []
        normalized_items = [item.strip().lower() for item in items]
        for i in range(self.count()):
            item = self.model().item(i)
            item_text_normalized = item.text().strip().lower()
            if item_text_normalized in normalized_items:
                item.setCheckState(Qt.Checked)
                # Use the original case from the item
                self.checked_items.append(item.text())
            else:
                item.setCheckState(Qt.Unchecked)
        self.update_display()

# ----------------------------
# Helper Functions
# ----------------------------

def get_env_vars(config_script_path):
    """Source the config_casino.csh file and capture the environment variables."""
    command = f'source {config_script_path} >& /dev/null && env'
    try:
        logger.debug(f"Executing command to source config: {command}")
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, executable='/bin/csh')
        env_vars = {}
        for line in proc.stdout:
            (key, _, value) = line.decode('utf-8').partition('=')
            env_vars[key.strip()] = value.strip()
        proc.communicate()
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, command)
        logger.info("Successfully sourced config and captured environment variables.")
        return env_vars
    except subprocess.CalledProcessError as e:
        logger.critical(f"Failed to get environment variables: {e}")
        sys.exit(1)

def replace_placeholders_in_hier(ws_hier_file_path, env_vars):
    """Replace placeholders in ws_casino.hier based on the sourced environment variables."""
    try:
        with open(ws_hier_file_path, 'r') as file:
            content = file.read()

        placeholders = {
            '$prj': env_vars.get('prj_name', ''),
            '$whoami': env_vars.get('whoami', ''),
            '$top_name': env_vars.get('top_name', ''),
            '$ws': env_vars.get('ws', ''),
            '$run_ver': env_vars.get('run_ver', '')
        }

        for placeholder, value in placeholders.items():
            content = content.replace(placeholder, value)
            logger.debug(f"Replaced {placeholder} with {value}.")

        return content.splitlines()
    except Exception as e:
        logger.critical(f"Failed to replace placeholders in {ws_hier_file_path}: {e}")
        sys.exit(1)

def filter_role_specific_lines(ws_hier_lines, role):
    """Filter out the lines specific to the chosen role (pi or pd) using regular expressions."""
    filtered_lines = []
    include_lines = True

    # Compile regular expressions for matching role-specific sections
    role_start_pattern = re.compile(rf"#\s*{role}\s*-\s*start", re.IGNORECASE)
    role_end_pattern = re.compile(rf"#\s*{role}\s*-\s*end", re.IGNORECASE)
    other_role_pattern = re.compile(r"#\s*(\w+)\s*-\s*(start|end)", re.IGNORECASE)

    for line in ws_hier_lines:
        # Check for role-specific sections using regular expressions
        match = other_role_pattern.search(line)
        if match:
            matched_role, section = match.groups()
            if matched_role.lower() == role.lower():
                if section.lower() == 'start':
                    include_lines = True
                    logger.debug(f"Entering {role} - start section.")
                elif section.lower() == 'end':
                    include_lines = False
                    logger.debug(f"Exiting {role} - end section.")
            else:
                if section.lower() == 'start':
                    include_lines = False
                    logger.debug(f"Entering other role ({matched_role}) - start section.")
                elif section.lower() == 'end':
                    include_lines = True
                    logger.debug(f"Exiting other role ({matched_role}) - end section.")
        else:
            # Add the line to filtered_lines only if it's part of the chosen role or outside of any role-specific section
            if include_lines:
                filtered_lines.append(line)

    logger.debug(f"Filtered {len(filtered_lines)} lines for role '{role}'.")
    return filtered_lines

def parse_ws_hier_lines(ws_hier_lines, env_vars):
    """Parse the lines of ws_casino.hier after placeholders have been replaced to create directories, handling $all_blks expansion."""
    try:
        dirs_to_create = []
        current_path = []
        previous_depth = -1
        all_blks = env_vars.get('casino_all_blks', '')
        all_blks_list = all_blks.split() + ["___BLK_INFO___"]  # Get the list of block names and add "___BLK_INFO___"

        for line in ws_hier_lines:
            line = line.rstrip()
            if line and not line.startswith('#'):
                stripped_line = line.lstrip().strip()
                depth = (len(line) - len(stripped_line)) // 4

                real_dir_name = stripped_line.split()[-1]

                if real_dir_name == "$all_blks":
                    # Expand each block name under $all_blks
                    for block_name in all_blks_list:
                        expanded_path = os.path.join(*current_path, block_name)
                        dirs_to_create.append((expanded_path, depth))
                        logger.debug(f"Expanded $all_blks to: {expanded_path} (Depth {depth})")
                else:
                    if depth > previous_depth:
                        current_path.append(real_dir_name)
                    elif depth == previous_depth:
                        if current_path:
                            current_path[-1] = real_dir_name
                        else:
                            current_path = [real_dir_name]
                    else:
                        current_path = current_path[:depth] + [real_dir_name]

                    previous_depth = depth
                    full_path = os.path.join(*current_path)
                    dirs_to_create.append((full_path, depth))
                    logger.debug(f"Parsed directory: {full_path} (Depth {depth})")

        logger.info(f"Total directories to create: {len(dirs_to_create)}")
        return dirs_to_create
    except Exception as e:
        logger.critical(f"Failed to parse ws_casino.hier lines: {e}")
        sys.exit(1)

def create_directory_structure(base_path, dirs_to_create, env_vars):
    """Create directories based on parsed ws_casino.hier lines, handling the special case for $all_blks."""
    for directory, depth in dirs_to_create:
        # Replace the placeholder $all_blks with actual block names if present in the directory path
        if "$all_blks" in directory:
            # Fetch all blocks from the environment variable and replace $all_blks in path
            for block in env_vars.get('casino_all_blks', '').split():
                dir_with_block = directory.replace("$all_blks", block)
                full_path = os.path.join(base_path, dir_with_block)
                if os.path.exists(full_path):
                    logger.info(f"Directory already exists for block: {full_path} (Depth {depth})")
                    continue  # Skip to the next iteration
                try:
                    os.makedirs(full_path)
                    logger.info(f"Created directory for block: {full_path} (Depth {depth})")
                except Exception as e:
                    logger.error(f"Failed to create directory {full_path}: {e}")
                    sys.exit(1)
        else:
            # Create directory normally for all other paths
            full_path = os.path.join(base_path, directory)
            if os.path.exists(full_path):
                logger.info(f"Directory already exists: {full_path} (Depth {depth})")
                continue  # Skip to the next iteration
            try:
                os.makedirs(full_path)
                logger.info(f"Created directory: {full_path} (Depth {depth})")
            except Exception as e:
                logger.error(f"Failed to create directory {full_path}: {e}")
                sys.exit(1)

def display_ws_info(ws):
    """Print the $ws information."""
    logger.info(f"Workspace (ws): {ws}")

def list_runs_directories_after_creating(runs_path):
    """List all directories under the runs directory."""
    try:
        run_dirs = [d for d in os.listdir(runs_path) if os.path.isdir(os.path.join(runs_path, d))]
        if run_dirs:
            logger.info("\nCurrent Runs Directories:")
            for run_dir in sorted(run_dirs):
                logger.info(f"- {run_dir}")
        else:
            logger.warning("No existing runs directories found.")
    except Exception as e:
        logger.error(f"Failed to list runs directories after creating: {e}")
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

    logger.debug(f"Source common directory (absolute): {src_common_dir}")
    logger.debug(f"Destination common directory (absolute): {common_dest_path}")

    try:
        # Remove the destination directory if it exists
        if os.path.exists(common_dest_path):
            shutil.rmtree(common_dest_path)
            logger.debug(f"Removed existing directory: {common_dest_path}")

        # Copy the entire source directory to the destination
        shutil.copytree(src_common_dir, common_dest_path)
        logger.info(f"Successfully replaced '{common_dest_path}' with '{src_common_dir}'")
    except PermissionError as pe:
        logger.error(f"Permission denied while copying from '{src_common_dir}' to '{common_dest_path}': {pe}")
        sys.exit(1)
    except FileNotFoundError as fnfe:
        logger.error(f"File or directory not found: {fnfe}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to copy contents from '{src_common_dir}' to '{common_dest_path}': {e}")
        logger.exception("Exception details:")
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

    logger.debug(f"Source common directory (absolute): {src_common_dir}")
    logger.debug(f"Destination local common directory (absolute): {common_dest_path}")

    try:
        # Remove the destination directory if it exists
        if os.path.exists(common_dest_path):
            shutil.rmtree(common_dest_path)
            logger.debug(f"Removed existing directory: {common_dest_path}")

        # Ensure the parent directories exist
        parent_dir = os.path.dirname(common_dest_path)
        os.makedirs(parent_dir, exist_ok=True)
        logger.debug(f"Ensured parent directories exist: {parent_dir}")

        # Copy the entire source directory to the destination
        shutil.copytree(src_common_dir, common_dest_path)
        logger.info(f"Successfully replaced '{common_dest_path}' with '{src_common_dir}'")
    except PermissionError as pe:
        logger.error(f"Permission denied while copying from '{src_common_dir}' to '{common_dest_path}': {pe}")
        sys.exit(1)
    except FileNotFoundError as fnfe:
        logger.error(f"File or directory not found: {fnfe}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to copy contents from '{src_common_dir}' to '{common_dest_path}': {e}")
        logger.exception("Exception details:")
        sys.exit(1)

def create_csh_script(run_ver, dest_path, outfeed_partner_dir, prj_base, pond_var):
    """
    Create an executable C Shell script named wait_n_run_flow_mgr_${run_ver}.csh,
    replacing '/' in run_ver with '_', and waiting for export.finish.
    Overwrites the existing file if it already exists.
    
    Args:
        run_ver (str): The run version string (e.g., 'FFN_fe00_te00_pv00').
        dest_path (str): The destination directory where the script will be created.
        outfeed_partner_dir (str): The partner's outfeed directory path.
        prj_base (str): The base project directory path.
        pond_var (str): The pond variable path.
    """
    try:
        # Replace any '/' in run_ver with '_' to avoid issues in script filename
        sanitized_run_ver = run_ver.replace("/", "_")
        script_name = f":wait_n_run_flow_mgr_{sanitized_run_ver}.csh"
        script_path = os.path.join(dest_path, script_name)

        # Ensure the destination directory exists
        os.makedirs(dest_path, exist_ok=True)

        # If the script already exists, delete it
        if os.path.exists(script_path):
            try:
                os.remove(script_path)
                logger.info(f"Deleted existing script: {script_path}")
            except PermissionError:
                logger.error(f"Permission denied: Cannot delete existing script {script_path}.")
                sys.exit(1)
            except Exception as e:
                logger.error(f"Failed to delete existing script {script_path}: {e}")
                sys.exit(1)

        # Build the script content with the wait loop for export.finish
        script_content = f"""#!/bin/csh -f

# Wait until partner's export.finish file exists
set retry_count = 0
set max_retries = 60   # Maximum wait time in minutes (can be adjusted as needed)
while (! -e {prj_base}/{outfeed_partner_dir}/export.finish && $retry_count < $max_retries)
    @ retry_line = $retry_count + 1
    echo "$retry_line/$max_retries Waiting for {prj_base}/{outfeed_partner_dir}/export.finish in partner's outfeed directory..."
    sleep 10  # Wait for 10 seconds before checking again
    @ retry_count++
end

# If the file was not found after max retries, exit with an error
if (! -e {prj_base}/{outfeed_partner_dir}/export.finish) then
    echo "Error: Required file {prj_base}/{outfeed_partner_dir}/export.finish not found in partner's outfeed directory after waiting."
    exit 1
endif

if (-e ./common/flow/flow_casino.yaml) then
    yes | {pond_var}/fm_casino.py -force -only $1 -flow ./common/flow/flow_casino.yaml
else
    yes | {pond_var}/fm_casino.py -force -only $1 -flow ../../common/flow/flow_casino.yaml
endif
"""

        # Create the new script file, overwriting if necessary
        with open(script_path, 'w') as script_file:
            script_file.write(script_content)

        # Set executable permissions on the script file
        os.chmod(script_path, 0o775)

        logger.info(f"Created C Shell script: {script_path}")

    except Exception as e:
        logger.error(f"Failed to create script {script_path}: {e}")
        sys.exit(1)

def dump_env_and_copy_tool_env(run_stage_dir, all_tools_env):
    """Dump environment variables to the given directory and copy tool env, overwriting existing files."""
    try:
        # Ensure the destination directory exists
        os.makedirs(run_stage_dir, exist_ok=True)
        logger.info(f"Ensured directory for environment dump exists: {run_stage_dir}")

        # Define the path for the environment dump file
        env_dump_path = os.path.join(run_stage_dir, 'env_vars.csh')

        # Dump current environment variables into the file, overwriting if it exists
        with open(env_dump_path, 'w') as env_file:
            for key, value in os.environ.items():
                env_file.write(f'setenv {key} "{value}"\n')
        # Set permissions for the generated file
        os.chmod(env_dump_path, 0o775)
        logger.info(f"Dumped environment variables to {env_dump_path} with chmod 775")

        # Copy tools env file, overwriting if it exists
        if all_tools_env and os.path.exists(all_tools_env):
            dest_file = os.path.join(run_stage_dir, os.path.basename(all_tools_env))
            shutil.copyfile(all_tools_env, dest_file)
            # Set permissions for the copied file
            os.chmod(dest_file, 0o775)
            logger.info(f"Copied tools env file {all_tools_env} to {dest_file} with chmod 775")
        else:
            logger.error(f"Tool env file {all_tools_env} not found.")
    except Exception as e:
        logger.error(f"Error during environment dump and tool env copy: {e}")
        sys.exit(1)

def get_stage_directories(dirs_to_create, run_ver, role):
    """Collect stage directories based on their depth in the hierarchy and role-specific hierarchy."""
    stage_dirs = []
    excluded_dirs = {'common'}  # Add more non-stage directories to this set if needed

    for directory, depth in dirs_to_create:
        # Check if the directory is under runs/{run_ver}, at depth 6, and is not in the excluded directories
        if f"/runs/{run_ver}/" in directory and depth == 6:
            dir_name = os.path.basename(directory)
            if dir_name not in excluded_dirs:
                stage_dirs.append(dir_name)
                logger.debug(f"Identified stage directory: {dir_name}")
    logger.debug(f"Total stage directories collected for role '{role}': {len(stage_dirs)}")
    return stage_dirs

def process_stage_directories(base_path, dirs_to_create, env_vars, run_ver):
    """Process directories for dumping environment variables and copying tool env file."""
    # Collect stage directories
    stage_dirs = get_stage_directories(dirs_to_create, run_ver, env_vars['current_role'])
    logger.debug(f"Dynamically collected stage directories for role '{env_vars['current_role']}': {stage_dirs}")

    all_tools_env = env_vars.get('casino_all_tools_env', None)
    if all_tools_env is None:
        logger.critical("'all_tools_env' environment variable is not set.")
        sys.exit(1)

    for directory, depth in dirs_to_create:
        # Extract the last directory name (stage) from the path to check if it's a stage directory
        last_dir_name = os.path.basename(directory)

        # Ensure we're processing directories under runs/{run_ver} and it's one of the dynamic stage dirs
        if f"/runs/{run_ver}/" in directory and last_dir_name in stage_dirs:
            run_stage_dir = os.path.join(base_path, directory)
            logger.debug(f"Processing stage directory: {run_stage_dir}")
            try:
                # Dump environment variables and copy tool environment files
                dump_env_and_copy_tool_env(run_stage_dir, all_tools_env)

                # Ensure all generated files in the directory have chmod 775
                for root, dirs, files in os.walk(run_stage_dir):
                    for file_name in files:
                        file_path = os.path.join(root, file_name)
                        os.chmod(file_path, 0o775)
                        logger.debug(f"Set permissions 775 for file: {file_path}")

            except Exception as e:
                logger.error(f"Error processing stage directory {run_stage_dir}: {e}")

def get_partner_run_ver(run_ver, role, purpose='processing'):
    """
    Adjust the timing ECO number based on the role ('pi' or 'pd') 
    and return the partner run version.

    Args:
        run_ver (str): The current run version string (e.g., 'FFN_fe00_te02_pv00').
        role (str): The current role ('pi' or 'pd').
        purpose (str): The purpose of the adjustment ('processing' or 'linking').

    Returns:
        str: The partner's run version string.
    """
    # Split the run_ver by underscores
    parts = run_ver.split('_')
    te_part = parts[-2]  # e.g., 'te02'
    try:
        te_number = int(te_part[2:])
    except ValueError:
        logger.critical(f"Invalid te_number format in run_ver '{run_ver}'. Expected 'teXX'.")
        sys.exit(1)

    if role == 'pi':
        if purpose == 'processing' or purpose == 'linking':
            # For 'pi', partner 'pd' run_ver has te_number +1
            partner_te_number = te_number + 1
    elif role == 'pd':
        if purpose == 'processing' or purpose == 'linking':
            # For 'pd', partner 'pi' run_ver remains the same
            partner_te_number = te_number
    else:
        logger.critical(f"Unrecognized role '{role}'. Must be 'pi' or 'pd'.")
        sys.exit(1)

    # Update the te part
    new_te_part = f"te{partner_te_number:02}"
    parts[-2] = new_te_part
    partner_run_ver = '_'.join(parts)

    logger.debug(f"Generated partner run_ver '{partner_run_ver}' for role '{role}' and purpose '{purpose}'.")
    return partner_run_ver

def increment_te_number_in_run_ver(run_ver):
    """
    Increment the te number in the run_ver by 1.
    """
    parts = run_ver.split('_')
    te_part = parts[-2]  # e.g., 'te02'
    te_number = int(te_part[2:])
    te_number += 1
    new_te_part = f"te{te_number:02}"  # Format as two digits
    parts[-2] = new_te_part
    new_run_ver = '_'.join(parts)
    logger.debug(f"Incremented run_ver from '{run_ver}' to '{new_run_ver}'.")
    return new_run_ver

def decrement_te_number_in_run_ver(run_ver):
    try:
        parts = run_ver.split('_')
        te_part = parts[-2]  # e.g., 'te02'
        te_number = int(te_part[2:])
        if te_number <= 0:
            #raise ValueError(f"Cannot decrement te number below 0. Current te number: {te_number}")
            te_number = 0
        te_number -= 1
        new_te_part = f"te{te_number:02}"  # Format as two digits
        parts[-2] = new_te_part
        new_run_ver = '_'.join(parts)
        logger.debug(f"Decremented run_ver from '{run_ver}' to '{new_run_ver}'.")
        return new_run_ver
    except IndexError:
        raise ValueError(f"run_ver '{run_ver}' does not have enough parts to decrement te number.")

def create_symbolic_links_for_iteration(iteration_run_info):
    """
    Create symbolic links between partner's stage directories for a single iteration.

    Args:
        iteration_run_info (dict): Dictionary containing run information for roles 'pi' and 'pd'.
    """
    logger.info("\nCreating symbolic links to partner's stage directories...")
    for role in ['pi', 'pd']:
        role_info = iteration_run_info.get(role, {})
        partner_role = 'pi' if role == 'pd' else 'pd'
        partner_info = iteration_run_info.get(partner_role, {})

        if not role_info or not partner_info:
            logger.warning(f"Missing role information for '{role}' or '{partner_role}'. Skipping symbolic link creation.")
            continue

        # Get the partner's run_ver for symbolic links
        partner_run_ver_for_links = partner_info['run_ver']

        create_symbolic_links(
            role_info['ws_path'],
            role_info['run_ver'],
            partner_info['ws_path'],
            partner_run_ver_for_links,
            partner_info['stages']
        )

def create_symbolic_links_for_iteration(all_run_info):
    """
    Create symbolic links between partner's stage directories for each iteration.

    Args:
        all_run_info (list): List of dictionaries containing run information for each iteration.
    """
    logger.info("\nCreating symbolic links to partner's stage directories...")
    for iteration_index, iteration_info in enumerate(all_run_info, start=1):
        logger.info(f"--- Processing Iteration {iteration_index} ---")
        for role in ['pi', 'pd']:
            role_info = iteration_info.get(role, {})
            if not role_info:
                logger.warning(f"No run information found for role '{role}' in iteration {iteration_index}. Skipping.")
                continue

            partner_role = 'pd' if role == 'pi' else 'pi'
            partner_info = iteration_info.get(partner_role, {})
            if not partner_info:
                logger.warning(f"No run information found for partner role '{partner_role}' in iteration {iteration_index}. Skipping.")
                continue

            # Fetch partner's run_ver
            partner_run_ver_for_links = partner_info.get('run_ver', '')
            if not partner_run_ver_for_links:
                logger.warning(f"Partner run_ver is missing for role '{partner_role}' in iteration {iteration_index}. Skipping.")
                continue

            # Fetch workspace paths
            role_ws_path = role_info.get('ws_path', '')
            partner_ws_path = partner_info.get('ws_path', '')
            role_run_ver = role_info.get('run_ver', '')

            # Validate workspace paths and run versions
            if not role_ws_path or not partner_ws_path:
                logger.warning(f"Workspace paths are incomplete for roles '{role}' or '{partner_role}' in iteration {iteration_index}. Skipping.")
                continue

            if not role_run_ver:
                logger.warning(f"Run version is missing for role '{role}' in iteration {iteration_index}. Skipping.")
                continue

            # Fetch partner stages
            partner_stages = partner_info.get('stages', [])
            if not partner_stages:
                logger.warning(f"No stages found for partner role '{partner_role}' in iteration {iteration_index}. Skipping.")
                continue

            # Create symbolic links
            create_symbolic_links(
                role_ws_path=role_ws_path,
                role_run_ver=role_run_ver,
                partner_ws_path=partner_ws_path,
                partner_run_ver=partner_run_ver_for_links,
                partner_stages=partner_stages
            )


def create_symbolic_links(role_ws_path, role_run_ver, partner_ws_path, partner_run_ver, partner_stages):
    """
    Create symbolic links for each partner's stages directories (excluding 'common') in each run_dir.

    Args:
        role_ws_path (str): Workspace path for the current role.
        role_run_ver (str): Run version for the current role.
        partner_ws_path (str): Workspace path for the partner role.
        partner_run_ver (str): Run version for the partner role.
        partner_stages (list): List of stages in the partner run directory.
    """
    role_run_path = os.path.join(role_ws_path, 'runs', role_run_ver)
    partner_run_path = os.path.join(partner_ws_path, 'runs', partner_run_ver)

    logger.info(f"Creating symbolic links from partner '{partner_run_path}' stages to role '{role_run_path}' run directory.")

    for stage in partner_stages:
        role_stage_path = os.path.join(role_run_path, stage)
        partner_stage_path = os.path.join(partner_run_path, stage)

        # Ensure partner_stage_path exists
        if not os.path.exists(partner_stage_path):
            logger.warning(f"Partner stage directory '{partner_stage_path}' does not exist. Skipping symbolic link creation.")
            continue

        # Create symbolic link only if it doesn't already exist
        if not os.path.exists(role_stage_path):
            try:
                # Create a relative symbolic link
                relative_partner_stage_path = os.path.relpath(partner_stage_path, os.path.dirname(role_stage_path))
                os.symlink(relative_partner_stage_path, role_stage_path)
                logger.info(f"Created symbolic link: {role_stage_path} -> {partner_stage_path}")
            except Exception as e:
                logger.error(f"Failed to create symbolic link {role_stage_path} -> {partner_stage_path}: {e}")
        else:
            logger.warning(f"Symbolic link or directory '{role_stage_path}' already exists. Skipping.")


def parse_dmsa_option_file(dmsa_option_file_path):
    """
    Parse the dmsa_option_file and extract variable names, types, default values, and options.
    Returns a dictionary with variable names as keys and a dictionary of 
    {'type': type_info, 'default': default_value, 'options': options_list} as values.
    """
    variables = {}
    try:
        with open(dmsa_option_file_path, 'r') as file:
            lines = file.readlines()

        # Preprocess lines to handle line continuations
        processed_lines = []
        continuation = False
        current_line = ''
        for line in lines:
            stripped = line.strip()
            if stripped.endswith('\\'):
                # Remove the backslash and continue
                current_line += stripped[:-1] + ' '
                continuation = True
            else:
                if continuation:
                    current_line += stripped
                    processed_lines.append(current_line)
                    current_line = ''
                    continuation = False
                else:
                    processed_lines.append(stripped)

        # Parse each processed line
        for line in processed_lines:
            # Skip empty lines and comments
            if not line or line.startswith(';') or line.startswith('#'):
                continue

            # Match lines starting with 'set ovars(dmsa,teco,...)'
            match = re.match(r'set\s+ovars\(dmsa,teco,([^)]+)\)\s+(.*?)\s*(?:;#(.*))?$', line)
            if match:
                var_name = match.group(1).strip()
                default_value = match.group(2).strip()
                comment = match.group(3).strip() if match.group(3) else ''

                # Extract type from comment
                var_type = 'string'  # Default type
                options = []

                type_match = re.search(r'(boolean|float|string|list)', comment, re.IGNORECASE)
                if type_match:
                    var_type = type_match.group(1).lower()

                # Extract options from comment within '<...>'
                options_match = re.search(r'<([^>]*)>', comment)
                if options_match:
                    options_str = options_match.group(1)
                    # Split options by '|' and remove any formatting like '**'
                    options = [opt.strip('* ').strip() for opt in options_str.split('|') if opt.strip()]
                else:
                    # If no '<...>' in comment but it's a list type, use default items as options
                    if var_type == 'list':
                        # Split the default value by spaces to get list items
                        options = default_value.split()

                # Clean up default value by removing surrounding quotes or brackets
                if default_value.startswith('"') and default_value.endswith('"'):
                    default_value = default_value[1:-1]
                elif default_value.startswith('[') and default_value.endswith(']'):
                    default_value = default_value[1:-1].strip()

                # For list types, split default_value into a list
                if var_type == 'list':
                    default_items = default_value.split()
                    default_value = default_items
                else:
                    default_value = default_value

                variables[var_name] = {
                    'type': var_type,
                    'default': default_value,
                    'options': options
                }
                logger.debug(f"Parsed variable: {var_name} | Type: {var_type} | Default: {default_value} | Options: {options}")

        logger.info(f"Total variables parsed from dmsa_option_file: {len(variables)}")
        return variables

    except FileNotFoundError:
        logger.critical(f"File '{dmsa_option_file_path}' not found.")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Error parsing dmsa_option_file: {e}")
        sys.exit(1)

def launch_gnome_terminal(run_dir, run_ver, role):
    """Launch a GNOME terminal in the given run_dir, execute the command using csh, and set the title."""
    title = f"teco @ {run_ver} : {role}"
    try:
        subprocess.Popen([
            'gnome-terminal', '--title', title, '--', 'csh', '-c', 
            f'cd "{run_dir}"; ./:wait_n_run_flow_mgr*.csh teco_{role}; exec csh'
        ])
        logger.info(f"Launched GNOME terminal in {run_dir} with title '{title}'")
    except Exception as e:
        logger.error(f"Failed to launch GNOME terminal in {run_dir}: {e}")

def launch_terminals(all_run_info):
    logger.info("\nLaunching GNOME terminals in each run directory...")
    launched_dirs = set()
    for iteration_info in all_run_info:
        for role, info in iteration_info.items():
            run_dir = os.path.join(info['ws_path'], 'runs', info['run_ver'])
            if run_dir not in launched_dirs:
                launch_gnome_terminal(run_dir, info['run_ver'], role)
                launched_dirs.add(run_dir)
            else:
                logger.debug(f"Skipping duplicate terminal launch for {run_dir}")


# ----------------------------
# GUI Application Class
# ----------------------------
class TecoCasinoGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('TECO Casino Setup')
        self.setGeometry(100, 100, 1200, 800)  # Increased width for better split view

        # Set the font to QFont("Terminus", 12)
        fixed_font12 = QtGui.QFont("Terminus", 12)
        self.setFont(fixed_font12)

        # Retrieve environment variables
        self.env_vars = get_env_vars(csh_file_path)
        self.env_vars['whoami'] = subprocess.getoutput('whoami')

        # Parse dmsa variables
        self.dmsa_variables = parse_dmsa_option_file(dmsa_option_file_path)

        # Initialize UI
        self.initUI()

    def initUI(self):

        fixed_font12 = QtGui.QFont("Terminus", 12)
        self.setFont(fixed_font12)

        # Create main splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left Pane Widget
        left_widget = QWidget()
        left_layout = QVBoxLayout()

        # Top Name Selection
        self.top_name_combo = QtWidgets.QComboBox()
        all_blks = self.env_vars.get('casino_all_blks', '').split()
        self.top_name_combo.addItems(all_blks)
        left_layout.addWidget(QLabel('Select Top Name:'))
        left_layout.addWidget(self.top_name_combo)

        # Role Selection
        self.role_combo = QtWidgets.QComboBox()
        self.role_combo.addItems(['pi', 'pd'])
        whoami_text = f"<span style='color:blue;'>{self.env_vars['whoami']}</span>"
        left_layout.addWidget(QLabel(f"Select Role: {whoami_text}"))
        left_layout.addWidget(self.role_combo)

        # Partner ID Selection
        self.partner_id_combo = QtWidgets.QComboBox()
        partner_ids = self.get_partner_ids()
        self.partner_id_combo.addItems(partner_ids)
        
        # Create the partner label
        self.partner_label = QLabel()
        left_layout.addWidget(self.partner_label)
        left_layout.addWidget(self.partner_id_combo)
        
        # Connect the role change signal to a method
        self.role_combo.currentIndexChanged.connect(self.update_partner_label)
        
        # Initialize the label once
        self.update_partner_label()

        # Run Version Selection
        left_layout.addWidget(QLabel('Select Existing Run Version or Enter New One:'))

        # Use QVBoxLayout instead of QHBoxLayout to stack widgets vertically
        run_ver_layout = QVBoxLayout()

        # Existing runs (current user)
        self.run_ver_list = QListWidget()
        run_ver_layout.addWidget(QLabel("Current User/Role Runs:"))
        run_ver_layout.addWidget(self.run_ver_list)
        
        # Partner runs
        self.partner_run_ver_list = QListWidget()
        run_ver_layout.addWidget(QLabel("Partner User/Role Runs:"))
        run_ver_layout.addWidget(self.partner_run_ver_list)
        
        # Now that both lists are defined, you can safely update them
        self.update_run_ver_list()
        self.update_partner_run_ver_list()

        # New Run Version Entry
        self.run_ver_edit = QLineEdit()
        self.run_ver_edit.setText('PI-PD-fe00_te00_pv00')  # Set default text
        # Optionally, you can keep or remove the placeholder text
        # self.run_ver_edit.setPlaceholderText('Enter new run version (FFN_fe00_te00_pv00)')
        run_ver_layout.addWidget(self.run_ver_edit)

        # Add the vertical run_ver_layout to the left_layout
        left_layout.addLayout(run_ver_layout)

        # Timing ECO Number Adjustment
        te_layout = QHBoxLayout()
        self.te_label = QLabel('te Number:')
        self.te_value_label = QLabel('00')
        self.plus_button = QPushButton('+')
        self.minus_button = QPushButton('-')
        te_layout.addWidget(self.te_label)
        te_layout.addWidget(self.te_value_label)
        te_layout.addWidget(self.plus_button)
        te_layout.addWidget(self.minus_button)
        left_layout.addLayout(te_layout)

        # Iteration Number Input
        iteration_layout = QHBoxLayout()
        self.iteration_label = QLabel('Iteration Number:')
        self.iteration_spinbox = QSpinBox()
        self.iteration_spinbox.setMinimum(0)  # Changed from 1 to 0
        self.iteration_spinbox.setValue(1)
        iteration_layout.addWidget(self.iteration_label)
        iteration_layout.addWidget(self.iteration_spinbox)
        left_layout.addLayout(iteration_layout)

        # Connect signal for iteration changes
        self.iteration_spinbox.valueChanged.connect(self.update_purposes_per_iteration)

        # Submit Button
        self.submit_button = QPushButton('Submit')
        self.submit_button.setStyleSheet(f"background-color: {BLUE_GROTTO}; color: black;")
        self.submit_button.setFont(fixed_font12)
        left_layout.addWidget(self.submit_button)
        self.submit_button.clicked.connect(self.submit)

        # Set left layout
        left_widget.setLayout(left_layout)

        # Right Pane Widget (Iteration Purposes)
        right_widget = QWidget()
        right_layout = QVBoxLayout()

        # Scroll Area for Iteration Purposes
        self.purposes_scroll_area = QScrollArea()
        self.purposes_scroll_widget = QWidget()
        self.purposes_layout = QVBoxLayout()
        self.purposes_scroll_widget.setLayout(self.purposes_layout)
        self.purposes_scroll_area.setWidget(self.purposes_scroll_widget)
        self.purposes_scroll_area.setWidgetResizable(True)
        right_layout.addWidget(QLabel('Iteration Purposes:'))
        right_layout.addWidget(self.purposes_scroll_area)

        # Set right layout
        right_widget.setLayout(right_layout)

        # Add widgets to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        # Set initial sizes (optional)
        splitter.setSizes([400, 800])

        # Set splitter as central widget
        self.setCentralWidget(splitter)

        # Connect other signals
        self.role_combo.currentIndexChanged.connect(self.update_te_number)
        self.top_name_combo.currentIndexChanged.connect(self.update_run_ver_list)
        self.role_combo.currentIndexChanged.connect(self.update_run_ver_list)
        self.run_ver_edit.textChanged.connect(self.update_te_number)
        self.run_ver_list.itemSelectionChanged.connect(self.update_run_ver_from_list)
        self.plus_button.clicked.connect(self.increment_te_number)
        self.minus_button.clicked.connect(self.decrement_te_number)

        # Initialize purpose selection widgets
        self.iteration_purpose_widgets = []
        self.iteration_purpose_data = []
        self.update_purposes_per_iteration()

    def update_partner_label(self):
        current_role = self.role_combo.currentText()
        partner_role = 'pd' if current_role == 'pi' else 'pi'
        self.partner_label.setText(f"Select Partner ID: {partner_role}")

    def update_purposes_per_iteration(self):
        # Clear existing purpose selection widgets
        for widget in self.iteration_purpose_widgets:
            self.purposes_layout.removeWidget(widget)
            widget.deleteLater()
        self.iteration_purpose_widgets.clear()
        self.iteration_purpose_data = []
    
        iteration_number = self.iteration_spinbox.value()
    
        # If iteration_number is 0, we still want to show at least one set of purposes.
        if iteration_number == 0:
            iteration_number = 1  # Treat iteration_number=0 as if it were 1
    
        for i in range(iteration_number):
            group_box = QGroupBox(f"Iteration {i+1} Purposes")
            group_layout = QVBoxLayout()
    
            # Purpose Inputs
            purpose_inputs = {}
            inputs_layout = QGridLayout()
            row = 0
    
            for var_name, var_definitions in self.dmsa_variables.items():
                var_type = var_definitions['type']
                all_options = var_definitions.get('options', [])
                all_defaults = var_definitions['default']
    
                # If it's a list type without options, use defaults as options
                if var_type == 'list' and not all_options:
                    all_options = all_defaults if isinstance(all_defaults, list) else [all_defaults]
    
                display_var_name = var_name
    
                if var_type == 'boolean':
                    label = QLabel(display_var_name)
                    checkbox = QtWidgets.QCheckBox()
                    # If any default is '1', checkbox is checked
                    checkbox.setChecked(any(default == '1' for default in (all_defaults if isinstance(all_defaults, list) else [all_defaults])))
                    purpose_inputs[var_name] = checkbox
                    inputs_layout.addWidget(label, row, 0)
                    inputs_layout.addWidget(checkbox, row, 1)
                    row += 1
    
                elif var_type == 'float':
                    label = QLabel(display_var_name)
                    line_edit = QLineEdit()
                    line_edit.setValidator(QtGui.QDoubleValidator())  # Allow double numbers
                    # Set the first default value if available
                    if all_defaults:
                        if isinstance(all_defaults, list):
                            line_edit.setText(str(all_defaults[0]))
                        else:
                            line_edit.setText(str(all_defaults))
                    purpose_inputs[var_name] = line_edit
                    inputs_layout.addWidget(label, row, 0)
                    inputs_layout.addWidget(line_edit, row, 1)
                    row += 1
    
                elif var_type == 'list' and all_options:
                    label = QLabel(display_var_name)
                    combo_box = CheckableComboBox()
                    combo_box.addItems(all_options)
                    if isinstance(all_defaults, list):
                        defaults = all_defaults
                    else:
                        defaults = [all_defaults]
                    combo_box.setCheckedItems(defaults)
                    purpose_inputs[var_name] = combo_box
                    inputs_layout.addWidget(label, row, 0)
                    inputs_layout.addWidget(combo_box, row, 1)
                    row += 1
    
                elif var_type == 'string' and all_options:
                    label = QLabel(display_var_name)
                    combo_box = QComboBox()
                    combo_box.addItems(all_options)
                    # Set default selection if it matches one of the options
                    if all_defaults:
                        default_text = all_defaults[0] if isinstance(all_defaults, list) else all_defaults
                        if default_text in all_options:
                            combo_box.setCurrentText(default_text)
                    purpose_inputs[var_name] = combo_box
                    inputs_layout.addWidget(label, row, 0)
                    inputs_layout.addWidget(combo_box, row, 1)
                    row += 1
    
                elif var_type == 'list':
                    # Free text input for list
                    label = QLabel(display_var_name)
                    line_edit = QLineEdit()
                    if all_defaults:
                        if isinstance(all_defaults, list):
                            line_edit.setText(' '.join(map(str, all_defaults)))
                        else:
                            line_edit.setText(str(all_defaults))
                    purpose_inputs[var_name] = line_edit
                    inputs_layout.addWidget(label, row, 0)
                    inputs_layout.addWidget(line_edit, row, 1)
                    row += 1
    
                else:  # string or others without options
                    label = QLabel(display_var_name)
                    line_edit = QLineEdit()
                    if all_defaults:
                        if isinstance(all_defaults, list):
                            line_edit.setText(' '.join(map(str, all_defaults)))
                        else:
                            line_edit.setText(str(all_defaults))
                    purpose_inputs[var_name] = line_edit
                    inputs_layout.addWidget(label, row, 0)
                    inputs_layout.addWidget(line_edit, row, 1)
                    row += 1
    
            group_layout.addLayout(inputs_layout)
            group_box.setLayout(group_layout)
            self.purposes_layout.addWidget(group_box)
            self.iteration_purpose_widgets.append(group_box)
            self.iteration_purpose_data.append(purpose_inputs)


    def submit(self):
        # Determine run_ver
        run_ver = self.run_ver_edit.text().strip()
        selected_items = self.run_ver_list.selectedItems()
        if run_ver:
            # Validate run_ver format
            pattern = r".+-.+-fe\d{2}_te\d{2}_pv\d{2}$"
            if not re.fullmatch(pattern, run_ver):
                QMessageBox.warning(self, 'Input Error', 'Run version does not match the required pattern (*-*-fe**_te**_pv**).')
                logger.warning("Run version input does not match the required pattern.")
                return
        elif selected_items and selected_items[0].text() != 'No existing runs':
            run_ver = selected_items[0].text()
            # Update run_ver_edit with selected run_ver
            self.run_ver_edit.setText(run_ver)
            logger.info(f"Selected existing run_ver: {run_ver}")
        else:
            QMessageBox.warning(self, 'Input Error', 'Please select an existing run version or enter a new one.')
            logger.warning("No run_ver provided by user.")
            return

        # Get the iteration number
        iteration_number = self.iteration_spinbox.value()
        logger.info(f"Number of iterations: {iteration_number}")

        # Collect purposes for each iteration
        iterations_purposes = []
        if iteration_number == 0:
            iterations_purposes.append({})  # Empty purposes for iteration 0
        else:
            for i in range(len(self.iteration_purpose_data)):
                purpose_inputs = self.iteration_purpose_data[i]
                purposes = {}
                for var_key, widget in purpose_inputs.items():
                    var_info = self.dmsa_variables.get(var_key, {})
                    var_type = var_info.get('type', 'string')
                    if var_type == 'boolean':
                        purposes[var_key] = '1' if widget.isChecked() else '0'
                    elif var_type == 'float':
                        value = widget.text().strip()
                        purposes[var_key] = value if value else ''
                    elif var_type == 'list' and var_info.get('options', []):
                        purposes[var_key] = widget.checkedItemsList()
                    elif var_type == 'string' and var_info.get('options', []):
                        purposes[var_key] = widget.currentText()
                    elif var_type == 'list':
                        value = widget.text().strip()
                        if value:
                            items = [item.strip() for item in re.split(r'[\s,]+', value)]
                            purposes[var_key] = items
                        else:
                            purposes[var_key] = []
                    else:  # string
                        value = widget.text().strip()
                        purposes[var_key] = value
                iterations_purposes.append(purposes)
                logger.debug(f"Collected purposes for iteration {i+1}: {purposes}")

        # Proceed with the rest of the script logic...
        self.env_vars['top_name'] = self.top_name_combo.currentText()
        self.env_vars['role'] = self.role_combo.currentText()
        self.env_vars['partner_role'] = 'pd' if self.env_vars['role'] == 'pi' else 'pi'
        self.env_vars['partner_id'] = self.partner_id_combo.currentText()
        self.env_vars['run_ver'] = run_ver

        logger.info(f"Selected Top Name: {self.env_vars['top_name']}")
        logger.info(f"Selected Role: {self.env_vars['role']}")
        logger.info(f"Selected Partner Role: {self.env_vars['partner_role']}")
        logger.info(f"Selected Partner ID: {self.env_vars['partner_id']}")
        logger.info(f"Selected Run Version: {self.env_vars['run_ver']}")

        # Proceed with the main logic
        main_logic(self.env_vars, run_ver, self.env_vars['partner_id'], iteration_number, iterations_purposes)

        QMessageBox.information(self, 'Success', 'Setup completed successfully.')
        logger.info("Setup completed successfully.")
        self.close()


    def submit(self):
        # Determine run_ver
        run_ver = self.run_ver_edit.text().strip()
        selected_items = self.run_ver_list.selectedItems()
        if run_ver:
            # Validate run_ver format
            pattern = r".+-.+-fe\d{2}_te\d{2}_pv\d{2}$"
            if not re.fullmatch(pattern, run_ver):
                QMessageBox.warning(self, 'Input Error', 'Run version does not match the required pattern (*-*-fe**_te**_pv**).')
                logger.warning("Run version input does not match the required pattern.")
                return
        elif selected_items and selected_items[0].text() != 'No existing runs':
            run_ver = selected_items[0].text()
            # Update run_ver_edit with selected run_ver
            self.run_ver_edit.setText(run_ver)
            logger.info(f"Selected existing run_ver: {run_ver}")
        else:
            QMessageBox.warning(self, 'Input Error', 'Please select an existing run version or enter a new one.')
            logger.warning("No run_ver provided by user.")
            return
    
        # Get the iteration number
        iteration_number = self.iteration_spinbox.value()
        logger.info(f"Number of iterations: {iteration_number}")
    
        # If iteration_number is 0, we still want to process one iteration of purposes.
        effective_iterations = max(iteration_number, 1)
    
        # Collect purposes for each iteration
        iterations_purposes = []
        for i in range(effective_iterations):
            if i < len(self.iteration_purpose_data):
                purpose_inputs = self.iteration_purpose_data[i]
                purposes = {}
                for var_key, widget in purpose_inputs.items():
                    var_info = self.dmsa_variables.get(var_key, {})
                    var_type = var_info.get('type', 'string')
    
                    if var_type == 'boolean':
                        purposes[var_key] = '1' if widget.isChecked() else '0'
                    elif var_type == 'float':
                        value = widget.text().strip()
                        purposes[var_key] = value if value else ''
                    elif var_type == 'list' and var_info.get('options', []):
                        # Multiple selectable options
                        purposes[var_key] = widget.checkedItemsList()
                    elif var_type == 'string' and var_info.get('options', []):
                        # Single selectable option
                        purposes[var_key] = widget.currentText()
                    elif var_type == 'list':
                        # Free-text list
                        value = widget.text().strip()
                        if value:
                            items = [item.strip() for item in re.split(r'[\s,]+', value)]
                            purposes[var_key] = items
                        else:
                            purposes[var_key] = []
                    else:  # string
                        value = widget.text().strip()
                        purposes[var_key] = value
                iterations_purposes.append(purposes)
                logger.debug(f"Collected purposes for iteration {i+1}: {purposes}")
            else:
                # If no purpose data exists for this iteration, append an empty dictionary
                iterations_purposes.append({})
                logger.debug(f"No purpose data for iteration {i+1}, appending empty dict.")
    
        # Update environment variables from GUI selections
        self.env_vars['top_name'] = self.top_name_combo.currentText()
        self.env_vars['role'] = self.role_combo.currentText()
        self.env_vars['partner_role'] = 'pd' if self.env_vars['role'] == 'pi' else 'pi'
        self.env_vars['partner_id'] = self.partner_id_combo.currentText()
        self.env_vars['run_ver'] = run_ver
    
        logger.info(f"Selected Top Name: {self.env_vars['top_name']}")
        logger.info(f"Selected Role: {self.env_vars['role']}")
        logger.info(f"Selected Partner Role: {self.env_vars['partner_role']}")
        logger.info(f"Selected Partner ID: {self.env_vars['partner_id']}")
        logger.info(f"Selected Run Version: {self.env_vars['run_ver']}")
    
        # Proceed with the main logic
        main_logic(self.env_vars, run_ver, self.env_vars['partner_id'], iteration_number, iterations_purposes)
    
        QMessageBox.information(self, 'Success', 'Setup completed successfully.')
        logger.info("Setup completed successfully.")
        self.close()


    def get_partner_ids(self):
        works_dir = self.env_vars.get('casino_prj_name', '')
        # List directories matching works_*
        try:
            all_dirs = os.listdir(works_dir)
            works_dirs = [d for d in all_dirs if os.path.isdir(os.path.join(works_dir, d)) and d.startswith('works_')]
            if not works_dirs:
                QMessageBox.critical(self, 'Error', 'No works_* directories found in the project directory.')
                logger.critical("No works_* directories found in the project directory.")
                sys.exit(1)
            # Extract partner IDs (usernames), including the current user
            partner_ids = [d[len('works_'):] for d in works_dirs]
            logger.debug(f"Found partner IDs: {partner_ids}")
            return partner_ids
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"Failed to list works_* directories with error: {e}")
            logger.critical(f"Failed to list works_* directories: {e}")
            sys.exit(1)

    def get_existing_runs(self):
        # Get necessary variables
        top_name = self.top_name_combo.currentText()
        role = self.role_combo.currentText()
        design_ver = self.env_vars.get('casino_design_ver', '')
        dk_ver = self.env_vars.get('casino_dk_ver', '')
        tag = self.env_vars.get('casino_tag', '')
        whoami = self.env_vars.get('whoami', '')
        self.env_vars['partner_id'] = self.partner_id_combo.currentText()
        partner_id = self.env_vars.get('partner_id', '')

        # Determine partner role
        partner_role = 'pd' if role == 'pi' else 'pi'

        # Construct the ws (workspace) names for both current and partner roles
        ws_current = f"{role}___{design_ver}_{dk_ver}_{tag}"
        ws_partner = f"{partner_role}___{design_ver}_{dk_ver}_{tag}"

        prj_name = self.env_vars.get('casino_prj_name', '')

        # Construct paths for both current user and partner user runs directories
        runs_path_user = os.path.join(prj_name, f"works_{whoami}", top_name, ws_current, "runs")
        runs_path_partner = os.path.join(prj_name, f"works_{partner_id}", top_name, ws_partner, "runs")

        user_run_dirs = []
        partner_run_dirs = []

        # Check user workspace runs
        if os.path.exists(runs_path_user):
            user_run_dirs = [d for d in os.listdir(runs_path_user) if os.path.isdir(os.path.join(runs_path_user, d))]
        else:
            logger.warning(f"Runs path {runs_path_user} does not exist for current user/role.")

        # Check partner workspace runs
        if os.path.exists(runs_path_partner):
            partner_run_dirs = [d for d in os.listdir(runs_path_partner) if os.path.isdir(os.path.join(runs_path_partner, d))]
        else:
            logger.warning(f"Runs path {runs_path_partner} does not exist for partner user/role.")

        user_run_dirs = sorted(user_run_dirs)
        partner_run_dirs = sorted(partner_run_dirs)

        logger.debug(f"User runs found: {user_run_dirs}")
        logger.debug(f"Partner runs found: {partner_run_dirs}")

        return user_run_dirs, partner_run_dirs

    def get_existing_runs_duplicate(self):
        """This is a duplicate function in the original code, which should be removed."""
        # Remove or comment out this function to avoid duplication
        pass  # Placeholder

    def update_run_ver_list(self):
        self.run_ver_list.clear()
        user_run_dirs, _ = self.get_existing_runs()

        if user_run_dirs:
            self.run_ver_list.addItems(user_run_dirs)
            logger.debug("Updated run_ver_list with user's runs.")
        else:
            self.run_ver_list.addItem('No existing runs')
            logger.debug("No existing user runs found.")

        # Update the partner list as well
        self.update_partner_run_ver_list()

    def update_partner_run_ver_list(self):
        self.partner_run_ver_list.clear()
        _, partner_run_dirs = self.get_existing_runs()

        if partner_run_dirs:
            self.partner_run_ver_list.addItems(partner_run_dirs)
            logger.debug("Updated partner_run_ver_list with partner's runs.")
        else:
            self.partner_run_ver_list.addItem('No partner runs')
            logger.debug("No partner runs found.")

    def update_te_number(self):
        run_ver = self.run_ver_edit.text().strip()
        if run_ver:
            te_number = self.extract_te_number(run_ver)
            self.te_value_label.setText(f"{te_number:02}")
            logger.debug(f"Updated te_number label to: {te_number:02}")
        else:
            self.te_value_label.setText("00")
            logger.debug("Cleared te_number label.")

    def update_run_ver_from_list(self):
        selected_items = self.run_ver_list.selectedItems()
        if selected_items and selected_items[0].text() != 'No existing runs':
            run_ver = selected_items[0].text()
            self.run_ver_edit.setText(run_ver)
            # Extract and update the te number
            te_number = self.extract_te_number(run_ver)
            self.te_value_label.setText(f"{te_number:02}")
            logger.info(f"Selected run_ver from list: {run_ver}")
        else:
            self.run_ver_edit.clear()
            self.te_value_label.setText("00")
            logger.debug("Cleared run_ver_edit and te_number label due to no selection.")

    def extract_te_number(self, run_ver):
        # Extract the te number from run_ver
        #pattern = r".*_fe\d{2}_te(\d{2})_pv\d{2}$"
        pattern = r".+-.+-fe\d{2}_te(\d{2})_pv\d{2}$"
        match = re.match(pattern, run_ver)
        if match:
            te_num = int(match.group(1))
            logger.debug(f"Extracted te_number: {te_num} from run_ver: {run_ver}")
            return te_num
        else:
            logger.warning(f"Run_ver '{run_ver}' does not match the expected pattern.")
            return 0

    def increment_te_number(self):
        te_number = int(self.te_value_label.text())
        te_number += 1
        self.te_value_label.setText(f"{te_number:02}")
        self.update_run_ver_te_number(te_number)
        logger.debug(f"Incremented te_number to: {te_number:02}")

    def decrement_te_number(self):
        te_number = int(self.te_value_label.text())
        if te_number > 0:
            te_number -= 1
            self.te_value_label.setText(f"{te_number:02}")
            self.update_run_ver_te_number(te_number)
            logger.debug(f"Decremented te_number to: {te_number:02}")
        else:
            logger.warning("Attempted to decrement te_number below 0.")

    def update_run_ver_te_number(self, te_number):
        """
        Update the te number in the current run_ver dynamically in the GUI.
        """
        # Determine the base run_ver
        selected_items = self.run_ver_list.selectedItems()
        if selected_items and selected_items[0].text() != 'No existing runs':
            base_run_ver = selected_items[0].text()
        elif self.run_ver_edit.text():
            base_run_ver = self.run_ver_edit.text().strip()
        else:
            base_run_ver = ''

        if base_run_ver:
            logger.debug(f"Original base_run_ver: {base_run_ver}")

            # Regular expression to match the expected format
            pattern = r"^(.*?-.*?-fe\d{2})_te\d{2}_pv\d{2}$"
            match = re.match(pattern, base_run_ver)
            if match:
                logger.debug(f"Regex match successful. Groups: {match.groups()}")

                # Reconstruct run_ver with updated te number
                prefix = match.group(1)  # Capture the part before '_teXX_pvXX'
                new_te_part = f"te{te_number:02}"  # Format the new te number
                new_run_ver = f"{prefix}_{new_te_part}_pv00"

                # Update the input field with the new run_ver
                self.run_ver_edit.setText(new_run_ver)
                logger.debug(f"Updated run_ver to: {new_run_ver}")
            else:
                # Log a warning if the regex fails
                logger.warning(f"Run_ver format mismatch. Cannot update te number: {base_run_ver}")
        else:
            logger.debug("No base run_ver to update with te_number.")

def generate_and_move_purpose_files(runs_path, stages, purposes):
    # If purposes are empty, skip generating purpose files
    #if not purposes:
        #logger.info("No purposes provided. Skipping generation of purpose files.")
        #return


    # Proceed with generation even if no purposes
    #logger.info("No purposes provided, but proceeding with file generation as requested.")

    # Generate and move sta_pt_teco files
    fname_sta_pt_teco = 'sta_pt_teco'
    logger.info(f"Generating files with fname='{fname_sta_pt_teco}' for sta_pt.")
    sta_pt_teco_csh_path, sta_pt_teco_tcl_path = generate_teco_purpose_casino_file(purposes, runs_path, fname_sta_pt_teco)
    sta_pt_dir = os.path.join(runs_path, 'sta_pt')
    if os.path.exists(sta_pt_dir):
        try:
            # Move the .csh file
            moved_csh_path = shutil.move(sta_pt_teco_csh_path, sta_pt_dir)
            logger.info(f"Successfully moved {fname_sta_pt_teco}.csh to {sta_pt_dir}")

            # Change mode to 775
            os.chmod(moved_csh_path, 0o775)

            # Move the .tcl file
            moved_tcl_path = shutil.move(sta_pt_teco_tcl_path, sta_pt_dir)
            logger.info(f"Successfully moved {fname_sta_pt_teco}.tcl to {sta_pt_dir}")

            # Change mode to 775
            os.chmod(moved_tcl_path, 0o775)

        except Exception as e:
            logger.error(f"Failed to move or change permissions of {fname_sta_pt_teco} files to {sta_pt_dir}: {e}")
    else:
        logger.warning(f"Directory {sta_pt_dir} does not exist. Skipping moving {fname_sta_pt_teco} files.")

    # Generate and move dmsa_teco files
    fname_dmsa_teco = 'dmsa_teco'
    dmsa_dir = os.path.join(runs_path, 'sta_pt', 'dmsa')
    if os.path.exists(dmsa_dir):
        logger.info(f"Generating files with fname='{fname_dmsa_teco}' for sta_pt/dmsa.")
        dmsa_teco_csh_path, dmsa_teco_tcl_path = generate_teco_purpose_casino_file(purposes, runs_path, fname_dmsa_teco)
        try:
            # Move the .csh file
            moved_csh_path = shutil.move(dmsa_teco_csh_path, dmsa_dir)
            logger.info(f"Successfully moved {fname_dmsa_teco}.csh to {dmsa_dir}")

            # Change mode to 775
            os.chmod(moved_csh_path, 0o775)

            # Move the .tcl file
            moved_tcl_path = shutil.move(dmsa_teco_tcl_path, dmsa_dir)
            logger.info(f"Successfully moved {fname_dmsa_teco}.tcl to {dmsa_dir}")

            # Change mode to 775
            os.chmod(moved_tcl_path, 0o775)

        except Exception as e:
            logger.error(f"Failed to move or change permissions of {fname_dmsa_teco} files to {dmsa_dir}: {e}")
    else:
        logger.warning(f"Directory {dmsa_dir} does not exist. Skipping moving {fname_dmsa_teco} files.")


import shutil
import os
import logging

# Ensure logger is configured
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_and_move_purpose_files(runs_path, stages, purposes):
    # If purposes are empty, skip generating purpose files
    # if not purposes:
        # logger.info("No purposes provided. Skipping generation of purpose files.")
        # return

    # Proceed with generation even if no purposes
    logger.info("No purposes provided, but proceeding with file generation as requested.")

    # Generate and move sta_pt_teco files
    fname_sta_pt_teco = 'sta_pt_teco'
    logger.info(f"Generating files with fname='{fname_sta_pt_teco}' for sta_pt.")
    sta_pt_teco_csh_path, sta_pt_teco_tcl_path = generate_teco_purpose_casino_file(purposes, runs_path, fname_sta_pt_teco)
    sta_pt_dir = os.path.join(runs_path, 'sta_pt')
    
    if os.path.exists(sta_pt_dir):
        try:
            # Define destination paths
            dest_csh_path = os.path.join(sta_pt_dir, f"{fname_sta_pt_teco}.csh")
            dest_tcl_path = os.path.join(sta_pt_dir, f"{fname_sta_pt_teco}.tcl")
            
            # Force move the .csh file
            if os.path.exists(dest_csh_path):
                logger.info(f"Destination file {dest_csh_path} exists. Removing it to allow overwrite.")
                os.remove(dest_csh_path)
            shutil.move(sta_pt_teco_csh_path, sta_pt_dir)
            logger.info(f"Successfully moved {fname_sta_pt_teco}.csh to {sta_pt_dir}")
            
            # Change mode to 775 for the moved .csh file
            os.chmod(dest_csh_path, 0o775)
            logger.info(f"Set permissions to 775 for {dest_csh_path}")
    
            # Force move the .tcl file
            if os.path.exists(dest_tcl_path):
                logger.info(f"Destination file {dest_tcl_path} exists. Removing it to allow overwrite.")
                os.remove(dest_tcl_path)
            shutil.move(sta_pt_teco_tcl_path, sta_pt_dir)
            logger.info(f"Successfully moved {fname_sta_pt_teco}.tcl to {sta_pt_dir}")
            
            # Change mode to 775 for the moved .tcl file
            os.chmod(dest_tcl_path, 0o775)
            logger.info(f"Set permissions to 775 for {dest_tcl_path}")
    
        except Exception as e:
            logger.error(f"Failed to move or change permissions of {fname_sta_pt_teco} files to {sta_pt_dir}: {e}")
    else:
        logger.warning(f"Directory {sta_pt_dir} does not exist. Skipping moving {fname_sta_pt_teco} files.")

    # Generate and move dmsa_teco files
    fname_dmsa_teco = 'dmsa_teco'
    dmsa_dir = os.path.join(runs_path, 'sta_pt', 'dmsa')
    
    if os.path.exists(dmsa_dir):
        logger.info(f"Generating files with fname='{fname_dmsa_teco}' for sta_pt/dmsa.")
        dmsa_teco_csh_path, dmsa_teco_tcl_path = generate_teco_purpose_casino_file(purposes, runs_path, fname_dmsa_teco)
        try:
            # Define destination paths
            dest_dmsa_csh_path = os.path.join(dmsa_dir, f"{fname_dmsa_teco}.csh")
            dest_dmsa_tcl_path = os.path.join(dmsa_dir, f"{fname_dmsa_teco}.tcl")
            
            # Force move the .csh file
            if os.path.exists(dest_dmsa_csh_path):
                logger.info(f"Destination file {dest_dmsa_csh_path} exists. Removing it to allow overwrite.")
                os.remove(dest_dmsa_csh_path)
            shutil.move(dmsa_teco_csh_path, dmsa_dir)
            logger.info(f"Successfully moved {fname_dmsa_teco}.csh to {dmsa_dir}")
            
            # Change mode to 775 for the moved .csh file
            os.chmod(dest_dmsa_csh_path, 0o775)
            logger.info(f"Set permissions to 775 for {dest_dmsa_csh_path}")
    
            # Force move the .tcl file
            if os.path.exists(dest_dmsa_tcl_path):
                logger.info(f"Destination file {dest_dmsa_tcl_path} exists. Removing it to allow overwrite.")
                os.remove(dest_dmsa_tcl_path)
            shutil.move(dmsa_teco_tcl_path, dmsa_dir)
            logger.info(f"Successfully moved {fname_dmsa_teco}.tcl to {dmsa_dir}")
            
            # Change mode to 775 for the moved .tcl file
            os.chmod(dest_dmsa_tcl_path, 0o775)
            logger.info(f"Set permissions to 775 for {dest_dmsa_tcl_path}")
    
        except Exception as e:
            logger.error(f"Failed to move or change permissions of {fname_dmsa_teco} files to {dmsa_dir}: {e}")
    else:
        logger.warning(f"Directory {dmsa_dir} does not exist. Skipping moving {fname_dmsa_teco} files.")


def generate_teco_purpose_casino_file(purposes, output_path, fname):
    try:
        # Ensure the output path exists
        os.makedirs(output_path, exist_ok=True)

        csh_file_name = f"{fname}.csh"
        tcl_file_name = f"{fname}.tcl"

        csh_file_path = os.path.join(output_path, csh_file_name)
        tcl_file_path = os.path.join(output_path, tcl_file_name)

        if 'dmsa_teco' in fname:
            ovars_section = 'dmsa'
        elif 'sta_pt_teco' in fname:
            ovars_section = 'sta_pt'
        else:
            ovars_section = 'dmsa'  # default

        with tempfile.NamedTemporaryFile('w', dir=output_path, delete=False) as csh_temp_file, \
             tempfile.NamedTemporaryFile('w', dir=output_path, delete=False) as tcl_temp_file:

            if not purposes:
                # Write placeholder lines if no purposes are provided
                csh_temp_file.write("# No purposes defined.\n")
                tcl_temp_file.write("# No purposes defined.\n")
            else:
                # Write out environment variables and TCL lines
                for var_name, value in purposes.items():
                    if isinstance(value, list):
                        list_str = ' '.join(value)
                        csh_temp_file.write(f'setenv {var_name}_teco "{list_str}"\n')
                        tcl_temp_file.write(f'set ovars({ovars_section},teco,{var_name}) [list {" ".join(value)}]\n')
                    else:
                        csh_temp_file.write(f'setenv {var_name}_teco "{value}"\n')
                        tcl_temp_file.write(f'set ovars({ovars_section},teco,{var_name}) "{value}"\n')

            csh_temp_name = csh_temp_file.name
            tcl_temp_name = tcl_temp_file.name

        os.chmod(csh_temp_name, 0o775)
        os.chmod(tcl_temp_name, 0o775)

        shutil.move(csh_temp_name, csh_file_path)
        shutil.move(tcl_temp_name, tcl_file_path)

        os.chmod(csh_file_path, 0o775)
        os.chmod(tcl_file_path, 0o775)

        logger.info(f"Generated {csh_file_name} at {csh_file_path}")
        logger.info(f"Generated {tcl_file_name} at {tcl_file_path}")

        return csh_file_path, tcl_file_path

    except Exception as e:
        logger.error(f"Failed to generate teco_purpose_casino files: {e}")
        sys.exit(1)


def main_logic(env_vars, initial_run_ver, partner_id, iteration_number, iterations_purposes):
    """
    Orchestrates the setup and management of project directories, run versions, and related configurations
    for the TECO Casino system.

    Args:
        env_vars (dict): Environment variables required for setup.
        initial_run_ver (str): The initial run version string.
        partner_id (str): Identifier for the partner.
        iteration_number (int): Number of iterations to perform.
        iterations_purposes (list): List of dictionaries containing purposes for each iteration.

    Returns:
        None
    """

    base_path = os.getcwd()
    logger.debug(f"Project base directory: {base_path}")

    # Initialize a list to store run information for all iterations
    all_run_info = []

    # Determine the starting role ('pi' or 'pd') from environment variables
    starting_role = env_vars.get('role', 'pi')  # Default to 'pi' if not set
    other_role = 'pd' if starting_role == 'pi' else 'pi'

    # Set initial run versions based on starting_role
    if starting_role == 'pi':
        pi_run_ver = initial_run_ver
        pd_run_ver = increment_te_number_in_run_ver(pi_run_ver)
    else:  # starting_role == 'pd'
        pd_run_ver = initial_run_ver
        pi_run_ver = pd_run_ver

    # ----------------------------
    # Handle Iterations
    # ----------------------------
    for iteration in range(iteration_number + 1):  # Include iteration_number as the last iteration
        logger.info(f"\n--- Iteration {iteration} ---")
        iteration_run_info = {}
        #current_iteration_purposes = iterations_purposes[iteration] if iteration < len(iterations_purposes) else {}
## scott : to make itertion number sync between iteration number and actual iteration_purpose : iteration --> iteration-1
        current_iteration_purposes = iterations_purposes[iteration-1]

        # Determine role_order based on iteration index
        if iteration == 0:
            # Special case: Only process starting_role in iteration 0
            role_order = [starting_role]
        else:
            if iteration % 2 == 1:
                # Odd iterations: [starting_role, other_role]
                role_order = [starting_role, other_role]
            else:
                # Even iterations: [other_role, starting_role]
                role_order = [other_role, starting_role]

        logger.debug(f"Iteration {iteration} role order: {role_order}")

        for role in role_order:
            # Copy env_vars so we don't mutate the original
            role_env_vars = copy.deepcopy(env_vars)
            role_env_vars['current_role'] = role

            # Determine user_id based on the role
            # - If the current role is the starting_role, use the 'whoami' (current user) as user_id
            # - If the current role is the other_role, use 'partner_id'
            if role == starting_role:
                user_id = role_env_vars.get('whoami', '')
            else:
                user_id = role_env_vars.get('partner_id', '')

            # Update whoami to reflect the user_id for directory creation
            role_env_vars['whoami'] = user_id

            # Define the workspace (ws)
            role_env_vars['ws'] = f"{role}___{role_env_vars.get('design_ver', '')}_" \
                                  f"{role_env_vars.get('dk_ver', '')}_" \
                                  f"{role_env_vars.get('tag', '')}"

            display_ws_info(role_env_vars['ws'])

            # Set run_ver for the role
            role_run_ver = pi_run_ver if role == 'pi' else pd_run_ver
            role_env_vars['run_ver'] = role_run_ver

            # Replace placeholders in ws_casino.hier and filter role-specific lines
            ws_hier_lines = replace_placeholders_in_hier(ws_hier_file_path, role_env_vars)
            ws_hier_lines = filter_role_specific_lines(ws_hier_lines, role)

            # Parse the ws_casino.hier lines to get the list of directories to create
            dirs_to_create = parse_ws_hier_lines(ws_hier_lines, role_env_vars)

            # Create the directory structure based on the parsed ws_casino.hier lines
            create_directory_structure(base_path, dirs_to_create, role_env_vars)

            # Define the workspace path using the selected user_id
            ws_path = os.path.join(
                role_env_vars.get('prj_name', ''),
                f"works_{user_id}",
                role_env_vars.get('top_name', ''),
                role_env_vars['ws']
            )

            copy_files_to_runs(ws_path)

            # Collect stage directories
            stages = get_stage_directories(dirs_to_create, role_env_vars['run_ver'], role)
            logger.info(f"Stages for role '{role}': {stages}")

            # Copy files to runs local
            copy_files_to_runs_local(ws_path, role_env_vars['run_ver'])

            # Process stage directories (e.g., dumping env vars, copying tool env)
            process_stage_directories(base_path, dirs_to_create, role_env_vars, role_env_vars['run_ver'])

            # Generate and move purpose files based on current iteration's purposes
            generate_and_move_purpose_files(
                os.path.join(ws_path, "runs", role_env_vars['run_ver']),
                stages,
                current_iteration_purposes
            )

            # Define partner's outfeed directory based on role
            if role == 'pi':
                wait_outfeed_dir = pi_run_ver
            else:  # role == 'pd'
                wait_outfeed_dir = decrement_te_number_in_run_ver(pi_run_ver)

            partner_role = 'pd' if role == 'pi' else 'pi'
            partner_ws = f"{partner_role}___{role_env_vars.get('design_ver', '')}_" \
                         f"{role_env_vars.get('dk_ver', '')}_" \
                         f"{role_env_vars.get('tag', '')}"
            outfeed_partner_dir = os.path.join(
                role_env_vars.get('prj_name', ''),
                'outfeeds',
                role_env_vars.get('top_name', ''),
                partner_ws,
                wait_outfeed_dir
            )

            # Create C Shell script for the role
            create_csh_script(
                role_run_ver,
                os.path.join(ws_path, "runs", role_env_vars['run_ver']),
                outfeed_partner_dir,
                base_path,
                pond_var
            )

            # Store run info for terminal launch
            iteration_run_info[role] = {
                'ws_path': ws_path,
                'run_ver': role_env_vars['run_ver'],
                'stages': stages,
                'user_id': user_id,
            }

        all_run_info.append(iteration_run_info)

        # Update run_ver for next iteration based on role order
        if iteration >= 1:
            if role_order[0] == 'pi':
                pi_run_ver = increment_te_number_in_run_ver(pi_run_ver)
                pd_run_ver = increment_te_number_in_run_ver(pd_run_ver)
            else:
                pd_run_ver = increment_te_number_in_run_ver(pd_run_ver)
                pi_run_ver = increment_te_number_in_run_ver(pi_run_ver)


    # ----------------------------
    # Post-Setup Operations
    # ----------------------------
    # After all iterations, create symbolic links between partner's stage directories
    create_symbolic_links_for_iteration(all_run_info)

    # Launch GNOME terminals in each run directory to execute scripts
    launch_terminals(all_run_info)


# ----------------------------
# Main Function
# ----------------------------
def main():
    app = QApplication(sys.argv)
    gui = TecoCasinoGUI()
    gui.show()
    sys.exit(app.exec_())

# ----------------------------
# Entry Point
# ----------------------------
if __name__ == "__main__":
    main()

