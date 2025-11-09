#!/usr/local/bin/python3.12

import yaml
import os
import argparse
import subprocess
import time
import glob
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from enum import Enum

import shutil
import readline
import rlcompleter
readline.parse_and_bind("tab: complete")
import sys
import signal
import psutil
from prettytable import PrettyTable

# Import argcomplete and a file completer for bash auto-completion
import argcomplete
from argcomplete.completers import FilesCompleter

class TerminalType(Enum):
    XTERM = "xterm"
    GNOME_TERMINAL = "gnome-terminal"

def detect_available_terminals():
    """Detect which terminal emulators are available on the system"""
    available = []

    # Check for xterm
    if shutil.which("xterm"):
        available.append(TerminalType.XTERM)

    # Check for gnome-terminal
    if shutil.which("gnome-terminal"):
        available.append(TerminalType.GNOME_TERMINAL)

    return available

def get_default_terminal():
    """Get the default terminal based on desktop environment and availability"""
    available = detect_available_terminals()

    if not available:
        return None

    # Check desktop environment
    desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()

    # Prefer gnome-terminal for GNOME environments
    if 'gnome' in desktop and TerminalType.GNOME_TERMINAL in available:
        return TerminalType.GNOME_TERMINAL

    # Default order of preference
    preference_order = [TerminalType.GNOME_TERMINAL, TerminalType.XTERM]

    for terminal in preference_order:
        if terminal in available:
            return terminal

    return available[0]

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Task Execution Script with Dependencies")
parser.add_argument('-start', type=str, help="Specify the start task")
parser.add_argument('-end', type=str, help="Specify the end task")
parser.add_argument('-force', action='store_true', help="Force execution of tasks even if they are marked as completed")
parser.add_argument(
    '-flow',
    type=str,
    help="Specify the YAML file defining the task flow (e.g., flow.yaml)",
    default="./common/flow/flow_casino.yaml"
).completer = FilesCompleter()
parser.add_argument('-only', type=str, help="Run only the specified task")
parser.add_argument('-max_workers', type=int, default=4, help="Maximum number of concurrent tasks")
parser.add_argument('-max_retries', type=int, default=3, help="Maximum number of retries for a task")
parser.add_argument('-monitor', action='store_true', help="Launch task monitor in terminal window")
parser.add_argument(
    '-terminal',
    type=str,
    choices=['xterm', 'gnome-terminal', 'auto'],
    default='auto',
    help="Choose terminal emulator (auto, xterm, gnome-terminal)"
)
parser.add_argument('-y', action='store_true', help="Automatically proceed with execution without confirmation prompt")
parser.add_argument('-singleTerm', action='store_true', help="Execute all tasks sequentially in a single terminal window instead of separate terminals. Useful for debugging or when you want to see all task output in one place.")
parser.add_argument('--interactive', action='store_true', help="Enable interactive mode for single terminal execution. Allows real-time output and user input for interactive tasks, including tool shells (vim, htop, etc.). Only works with -singleTerm.")

# Enable argcomplete auto-completion (for bash/zsh)
argcomplete.autocomplete(parser)

# Proceed to parse arguments
args = parser.parse_args()

# If no arguments are provided, display options and exit
if len(sys.argv) == 1:
    available_terminals = detect_available_terminals()
    terminal_list = ", ".join([t.value for t in available_terminals])

    print(f"""
Options:
    -start       : Set the start task
    -end         : Set the end task
    -only        : Set the subtasks only
    -force       : Force tasks ignoring status completed
    -flow        : Set flow_casino.yaml (default: ./common/flow/flow_casino.yaml)
    -max_workers a: Set max workers
    -monitor     : Launch task monitor in terminal window
    -terminal    : Choose terminal (auto, xterm, gnome-terminal)
                   Available terminals: {terminal_list}
    -y           : Automatically proceed with execution without confirmation prompt
    """)
    sys.exit(1)

# Determine terminal type to use
if args.terminal == 'auto':
    selected_terminal = get_default_terminal()
elif args.terminal == 'xterm':
    selected_terminal = TerminalType.XTERM if TerminalType.XTERM in detect_available_terminals() else None
elif args.terminal == 'gnome-terminal':
    selected_terminal = TerminalType.GNOME_TERMINAL if TerminalType.GNOME_TERMINAL in detect_available_terminals() else None

if selected_terminal is None:
    available = detect_available_terminals()
    if available:
        print(f"Warning: Requested terminal '{args.terminal}' not available. Using {available[0].value}")
        selected_terminal = available[0]
    else:
        print("Error: No supported terminal emulator found (xterm or gnome-terminal)")
        sys.exit(1)

print(f"Using terminal: {selected_terminal.value}")

if not args.flow:
    print("Warning: 'flow' is not provided. Please provide a flow YAML file.")
    sys.exit(1)

if args.only and (args.start or args.end):
    raise ValueError("The -only option cannot be used together with -start or -end.")

if args.interactive and not args.singleTerm:
    raise ValueError("The --interactive option can only be used with -singleTerm.")

# Auto-enable interactive mode when singleTerm is used
if args.singleTerm and not args.interactive:
    print("Auto-enabling --interactive mode for -singleTerm execution")
    args.interactive = True

# Determine the filename suffix based on the arguments
if args.only:
    filename_suffix = args.only
elif args.start or args.end:
    start_suffix = args.start if args.start else "start"
    end_suffix = args.end if args.end else "end"
    filename_suffix = f"{start_suffix}_to_{end_suffix}"
else:
    filename_suffix = "full_run"

# Create runs_history directory if it doesn't exist
RUNS_HISTORY_DIR = 'flow_log'
Path(RUNS_HISTORY_DIR).mkdir(exist_ok=True)

# Global variables
interrupted = False
current_process = None
monitor_process = None
execution_id = str(int(time.time()))  # Unique execution ID

# File paths for keeping track of tasks and runtimes - EXECUTION-SPECIFIC
COMPLETED_TASKS_FILE = os.path.join(RUNS_HISTORY_DIR, f'completed_tasks___{filename_suffix}_{execution_id}.yaml')
RUNTIME_HISTORY_FILE = os.path.join(RUNS_HISTORY_DIR, f'runtime_history___{filename_suffix}.yaml')

# Load the YAML file that defines the task flow
if not os.path.exists(args.flow):
    raise FileNotFoundError(f"The specified flow file {args.flow} does not exist.")

with open(args.flow, 'r') as file:
    data = yaml.safe_load(file)

def validate_flow_yaml(data):
    """Validate flow YAML for common issues"""
    errors = []
    task_names = set()
    all_task_names = [task.get('name') for task in data.get('tasks', []) if task.get('name')]

    for task in data.get('tasks', []):
        name = task.get('name')
        if not name:
            errors.append("Task found without name")
            continue

        if name in task_names:
            errors.append(f"Duplicate task name: {name}")
        task_names.add(name)

        # Check for self-dependencies
        deps = task.get('dependencies', [])
        if name in deps:
            errors.append(f"Task '{name}' has circular self-dependency")

        # Validate dependencies exist
        for dep in deps:
            if dep not in all_task_names:
                errors.append(f"Task '{name}' depends on non-existent task '{dep}'")

        # Check dependencies_or if they exist
        deps_or = task.get('dependencies_or', [])
        for dep in deps_or:
            if dep not in all_task_names:
                errors.append(f"Task '{name}' has OR dependency on non-existent task '{dep}'")

    return errors

# Validate flow before processing
validation_errors = validate_flow_yaml(data)
if validation_errors:
    print("Flow validation errors found:")
    for error in validation_errors:
        print(f"  - {error}")
    print("Please fix these errors before running.")
    sys.exit(1)

# Get run_ver variable from current directory (customize as needed)
current_dir = os.getcwd()
path_components = current_dir.strip(os.sep).split(os.sep)
run_ver_components = path_components[-4:]
run_dir = path_components[-1]
run_ver = os.sep.join(run_ver_components)

# Replace $run_ver variable in commands
for task in data['tasks']:
    if 'command' in task:
        task['command'] = task['command'].replace('$run_ver', run_ver)

# Load the list of completed tasks from the YAML file
completed_tasks = []
if os.path.exists(COMPLETED_TASKS_FILE):
    try:
        with open(COMPLETED_TASKS_FILE, 'r') as file:
            completed_tasks = yaml.safe_load(file) or []
    except (yaml.YAMLError, ValueError) as e:
        print(f"Warning: {COMPLETED_TASKS_FILE} is empty or malformed. Starting with an empty list of completed tasks.")
        completed_tasks = []
else:
    print(f"Warning: {COMPLETED_TASKS_FILE} does not exist. Starting with an empty list of completed tasks.")

# If force flag is set, clear all completed tasks to start fresh
if args.force:
    print("Force flag set - clearing completed tasks for fresh execution")
    completed_tasks = []
    # Clear the completed tasks file
    with open(COMPLETED_TASKS_FILE, 'w') as f:
        f.write("[]")

# Only keep tasks that were successful
completed_tasks = [task for task in completed_tasks if task['status'] == "Success"]

def display_completed_tasks(tasks):
    if not tasks:
        print("No completed tasks found.")
        return

    print("\nCompleted Tasks:")
    print(f"{'No.':<3} {'Task Name':<20} {'Start Time':<22} {'End Time':<22} {'Runtime':<20} {'Status':<10}")
    print("-" * 120)
    for idx, task in enumerate(tasks):
        print(f"{idx + 1:<3} {task['name']:<20} {task['start_time']:<22} {task['end_time']:<22} {task['runtime']:<20} {task.get('status', 'Unknown'):<10}")
    print("-" * 120)

def display_previous_runs_summary():
    """Display the most recent previous run's task details and return completion status"""
    pattern = os.path.join(RUNS_HISTORY_DIR, f'completed_tasks___{filename_suffix}_*.yaml')
    previous_files = glob.glob(pattern)

    if not previous_files:
        print("No previous runs found for this task range.")
        return False  # No previous run = proceed

    most_recent_file = max(previous_files, key=os.path.getmtime)

    try:
        filename = os.path.basename(most_recent_file)
        exec_id = filename.split('_')[-1].replace('.yaml', '')

        with open(most_recent_file, 'r') as f:
            content = f.read().strip()
            if not content:
                print("Most recent run file is empty.")
                return False

        tasks_data = yaml.safe_load(content) or []
        if not isinstance(tasks_data, list):
            print("Invalid format in most recent run file.")
            return False

        file_time = datetime.fromtimestamp(os.path.getmtime(most_recent_file))
        print(f"\nMost Recent Run (Execution ID: {exec_id}):")
        print(f"Run Time: {file_time.strftime('%Y/%m/%d %H:%M:%S')}")
        print(f"{'No.':<3} {'Task Name':<20} {'Start Time':<22} {'End Time':<22} {'Runtime':<20} {'Status':<12}")
        print("-" * 120)

        for idx, task in enumerate(tasks_data):
            if task.get('name'):
                print(f"{idx + 1:<3} {task.get('name', ''):<20} {task.get('start_time', 'N/A'):<22} {task.get('end_time', 'N/A'):<22} {task.get('runtime', 'N/A'):<20} {task.get('status', 'Unknown'):<12}")

        print("-" * 120)

        total_tasks = len([t for t in tasks_data if t.get('name')])
        success_count = len([t for t in tasks_data if t.get('status') == 'Success'])
        failed_count = len([t for t in tasks_data if t.get('status') in ['Failed', 'Interrupted', 'Timeout']])
        not_executed = len([t for t in tasks_data if t.get('status') == 'Not Executed'])

        print(f"Summary: {total_tasks} total, {success_count} success, {failed_count} failed/interrupted, {not_executed} not executed")

        previous_run_completed = (success_count == total_tasks and failed_count == 0 and not_executed == 0)

        if previous_run_completed:
            print(f"? Previous run completed successfully - all {total_tasks} tasks finished with Success status")
        else:
            print(f"? Previous run incomplete - {failed_count} failed/interrupted, {not_executed} not executed")

        return previous_run_completed

    except Exception as e:
        print(f"Error reading most recent run: {e}")
        return False

display_completed_tasks(completed_tasks)
previous_run_successful = display_previous_runs_summary()

def format_runtime(seconds):
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{int(days):02}:{int(hours):02}:{int(minutes):02}:{int(secs):02}"

def format_completed_tasks(tasks):
    """Format completed tasks for YAML output"""
    formatted_tasks = []
    for task in tasks:
        formatted_tasks.append(
            f"- name:       {task['name']}\n"
            f"  start_time: {task['start_time']}\n"
            f"  end_time:   {task['end_time']}\n"
            f"  runtime:    {task['runtime']}\n"
            f"  status:     {task['status']}"
        )
    return "\n".join(formatted_tasks)

def write_completed_tasks_file():
    """Write completed tasks to file for real-time monitoring"""
    formatted_completed_tasks = format_completed_tasks(completed_tasks)
    with open(COMPLETED_TASKS_FILE, 'w') as file:
        file.write(formatted_completed_tasks)

def get_current_time():
    return time.strftime("%Y/%m/%d %H:%M:%S")

def calculate_time_difference(start_time_str, end_time_str):
    start_time = time.strptime(start_time_str, "%Y/%m/%d %H:%M:%S")
    end_time = time.strptime(end_time_str, "%Y/%m/%d %H:%M:%S")
    return time.mktime(end_time) - time.mktime(start_time)

def cleanup_temp_files():
    """Clean up temporary files created during execution"""
    patterns = [
        "/tmp/task_*.csh",
        "/tmp/task_status_*.txt",
        "/tmp/task_pid_*.txt"
    ]

    for pattern in patterns:
        try:
            files = glob.glob(pattern)
            for file in files:
                # Only clean files from this execution
                if execution_id in file:
                    os.remove(file)
        except Exception as e:
            print(f"Cleanup warning: {e}")

def handle_interruption(signum, frame):
    global interrupted, current_process, monitor_process
    interrupted = True
    print(f"\nReceived signal {signum}. Cleaning up and stopping execution...")

    # Clean up temp files
    cleanup_temp_files()

    if current_process is not None:
        current_process.terminate()

    if monitor_process:
        print("Task monitor will continue running. You can close it manually when done.")
        print("Monitor PID:", monitor_process.pid)

signal.signal(signal.SIGTERM, handle_interruption)
signal.signal(signal.SIGHUP, handle_interruption)
signal.signal(signal.SIGINT, handle_interruption)

def create_terminal_command(terminal_type, title, command_args, **kwargs):
    """Create terminal command based on terminal type"""

    if terminal_type == TerminalType.XTERM:
        cmd = ['xterm', '-title', title]

        # Add xterm-specific options
        if kwargs.get('bg'):
            cmd.extend(['-bg', kwargs['bg']])
        if kwargs.get('fg'):
            cmd.extend(['-fg', kwargs['fg']])
        if kwargs.get('geometry'):
            cmd.extend(['-geometry', kwargs['geometry']])
        if kwargs.get('hold', True):
            cmd.append('-hold')

        cmd.append('-e')
        cmd.extend(command_args)
        return cmd


    elif terminal_type == TerminalType.GNOME_TERMINAL:
        # Get current group name to preserve gid inheritance
        import grp
        current_gid = os.getgid()
        try:
            group_name = grp.getgrgid(current_gid).gr_name
        except:
            group_name = None

        cmd = ['gnome-terminal', '--wait', '--title', title]

        # Add gnome-terminal specific options
        if kwargs.get('geometry'):
            cmd.extend(['--geometry', kwargs['geometry']])
        if kwargs.get('working_directory'):
            cmd.extend(['--working-directory', kwargs['working_directory']])

        # Handle colors for gnome-terminal using escape sequences
        bg_color = kwargs.get('bg')
        fg_color = kwargs.get('fg')

        if bg_color or fg_color:
            # Convert color names to hex if needed
            color_map = {
                'black': '#000000',
                'blue': '#0000FF',
                'green': '#00FF00',
                'red': '#FF0000',
                'yellow': '#FFFF00',
                'cyan': '#00FFFF',
                'magenta': '#FF00FF',
                'white': '#FFFFFF',
                'gray': '#808080',
                'grey': '#808080'
            }

            bg_hex = color_map.get(bg_color, bg_color) if bg_color else None
            fg_hex = color_map.get(fg_color, fg_color) if fg_color else None

            # Create a wrapper script that sets colors then runs the command
            color_script = f"""#!/usr/bin/csh
# Set terminal colors using escape sequences
"""
            if bg_hex:
                color_script += f'printf "\\033]11;{bg_hex}\\007"\n'  # Set background
            if fg_hex:
                color_script += f'printf "\\033]10;{fg_hex}\\007"\n'  # Set foreground

            color_script += f"""
# Execute the actual command
exec {' '.join(command_args)}
"""

            # Write the color script to a temporary file
            import tempfile

            script_fd, script_path = tempfile.mkstemp(suffix='.csh', prefix='casino_color_')
            try:
                with os.fdopen(script_fd, 'w') as f:
                    f.write(color_script)
                os.chmod(script_path, 0o755)

                # Wrap with sg to preserve gid if group_name is available
                if group_name:
                    cmd.extend(['--', 'sg', group_name, '-c', f'csh {script_path}'])
                else:
                    cmd.extend(['--', 'csh', script_path])
                return cmd

            except Exception as e:
                print(f"Error creating color script: {e}")
                # Fallback to normal command without colors
                if group_name:
                    cmd.extend(['--', 'sg', group_name, '-c', ' '.join(command_args)])
                else:
                    cmd.append('--')
                    cmd.extend(command_args)
                return cmd
        else:
            # No colors specified, use normal command wrapped with sg to preserve gid
            if group_name:
                cmd.extend(['--', 'sg', group_name, '-c', ' '.join(command_args)])
            else:
                cmd.append('--')
                cmd.extend(command_args)
            return cmd

    else:
        raise ValueError(f"Unsupported terminal type: {terminal_type}")

def launch_task_monitor():
    """Launch the task monitor in a terminal window"""
    try:
        # Get the path to the task_monitor.py script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        monitor_script = os.path.join(script_dir, 'task_monitor.py')

        if not os.path.exists(monitor_script):
            print(f"Error: task_monitor.py not found at {monitor_script}")
            return None

        # Verify that required files exist
        print(f"Verifying monitor file paths:")
        print(f"  Flow file: {args.flow} - {'Exists' if os.path.exists(args.flow) else 'Missing'}")
        print(f"  Completed tasks file: {COMPLETED_TASKS_FILE} - {'Exists' if os.path.exists(COMPLETED_TASKS_FILE) else 'Missing'}")
        print(f"  Runtime history file: {RUNTIME_HISTORY_FILE} - {'Exists' if os.path.exists(RUNTIME_HISTORY_FILE) else 'Missing'}")

        # Create empty files if they don't exist
        if not os.path.exists(COMPLETED_TASKS_FILE):
            print(f"Creating empty completed tasks file: {COMPLETED_TASKS_FILE}")
            with open(COMPLETED_TASKS_FILE, 'w') as f:
                f.write("[]")

        if not os.path.exists(RUNTIME_HISTORY_FILE):
            print(f"Creating empty runtime history file: {RUNTIME_HISTORY_FILE}")
            with open(RUNTIME_HISTORY_FILE, 'w') as f:
                f.write("")

        # Create monitor title with execution context
        monitor_title = f"Task Monitor @ {run_dir}"
        if args.only:
            monitor_title += f" [ONLY: {args.only}]"
        elif args.start or args.end:
            start_part = args.start if args.start else "start"
            end_part = args.end if args.end else "end"
            monitor_title += f" [{start_part} to {end_part}]"
        else:
            monitor_title += " [FULL RUN]"

        # Prepare monitor command arguments - USE EXECUTION-SPECIFIC FILE
        monitor_cmd_args = [
            'python3.12', monitor_script,
            '--flow', args.flow,
            '--completed', COMPLETED_TASKS_FILE,  # Now execution-specific
            '--runtime', RUNTIME_HISTORY_FILE,
            '--execution-id', execution_id
        ]

        # Add execution range parameters if specified
        if args.start:
            monitor_cmd_args.extend(['--start', args.start])
        if args.end:
            monitor_cmd_args.extend(['--end', args.end])
        if args.only:
            monitor_cmd_args.extend(['--only', args.only])
        if args.force:
            monitor_cmd_args.extend(['--force', '--clear-on-start'])
        if args.singleTerm:
            monitor_cmd_args.extend(['--singleTerm'])
        if args.interactive:
            monitor_cmd_args.extend(['--interactive'])

        # Create terminal command based on selected terminal type
        terminal_cmd = create_terminal_command(
            selected_terminal,
            monitor_title,
            monitor_cmd_args,
            bg='black',
            fg='darkgray',
            geometry='120x45',
            hold=True,
            working_directory=current_dir
        )

        print(f"Launching task monitor in {selected_terminal.value} window...")
        print(f"Execution ID: {execution_id}")

        monitor_process = subprocess.Popen(
            terminal_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ.copy()
        )

        print(f"Task monitor launched with PID: {monitor_process.pid}")

        # Wait a moment to see if it starts successfully
        time.sleep(2)

        if monitor_process.poll() is not None:
            stdout, stderr = monitor_process.communicate()
            print(f"Monitor process exited immediately")
            print(f"Return code: {monitor_process.returncode}")
            if stdout:
                print(f"stdout: {stdout.decode()}")
            if stderr:
                print(f"stderr: {stderr.decode()}")
            return None

        return monitor_process

    except Exception as e:
        print(f"Error launching task monitor: {e}")
        return None

def save_completed_task_immediately(task_runtime_info):
    """Save completed task immediately for real-time monitoring"""
    try:
        # Load existing completed tasks
        existing_tasks = []
        if os.path.exists(COMPLETED_TASKS_FILE):
            try:
                with open(COMPLETED_TASKS_FILE, 'r') as f:
                    content = f.read().strip()
                    if content:
                        existing_tasks = yaml.safe_load(content) or []
            except:
                existing_tasks = []

        # Add new task
        existing_tasks.append(task_runtime_info)

        # Save immediately
        formatted_tasks = []
        for task in existing_tasks:
            formatted_tasks.append(
                f"- name:       {task['name']}\n"
                f"  start_time: {task['start_time']}\n"
                f"  end_time:   {task['end_time']}\n"
                f"  runtime:    {task['runtime']}\n"
                f"  status:     {task['status']}"
            )

        with open(COMPLETED_TASKS_FILE, 'w') as f:
            f.write("\n".join(formatted_tasks))

        # Force filesystem sync
        os.sync()

    except Exception as e:
        print(f"Warning: Could not save task completion immediately: {e}")

def monitor_process_and_status(self, process, status_file, pid_file, task_name, max_wait_time=864000):
    """
    Enhanced monitoring that detects both normal completion AND accidental terminal closure
    """
    wait_start = time.time()
    last_status = None
    task_completed = False

    print(f"Monitoring task completion for {task_name} - checking both process and status...")

    while not interrupted and not task_completed:
        # Check timeout
        if time.time() - wait_start > max_wait_time:
            print(f"Task {task_name} exceeded maximum wait time, terminating...")
            self.cleanup_task_processes(process, pid_file, task_name)
            return "Timeout"

        # PRIMARY: Check status file for normal completion
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r') as f:
                    status_content = f.read().strip()

                    if status_content != last_status:
                        if status_content == "RUNNING":
                            print(f"Task {task_name} is running...")
                        elif status_content.startswith('SUCCESS'):
                            print(f"Task {task_name} completed successfully")
                            return "Success"
                        elif status_content.startswith('FAILED'):
                            print(f"Task {task_name} failed")
                            return "Failed"
                        elif status_content == "INTERRUPTED":
                            print(f"Task {task_name} was interrupted")
                            return "Interrupted"
                        last_status = status_content

            except Exception as e:
                print(f"Warning: Could not read status file {status_file}: {e}")

        # SECONDARY: Check if terminal process died unexpectedly
        terminal_dead = False
        if process.poll() is not None:
            # Terminal process has exited - this could be normal or accidental
            terminal_dead = True

        # TERTIARY: Check if actual command process is still running
        command_processes_running = self.check_command_processes_running(pid_file, task_name)

        # DECISION LOGIC:
        if terminal_dead and not command_processes_running:
            # Terminal died AND no command processes running
            if not os.path.exists(status_file) or last_status == "RUNNING":
                # No completion status written = accidental closure
                print(f"DETECTED: Terminal for {task_name} closed without proper completion status")
                print(f"This appears to be an accidental terminal closure - marking as INTERRUPTED")
                return "Interrupted"
            # else: Normal completion, status file shows final state

        elif terminal_dead and command_processes_running:
            # Terminal died but command still running = definite zombie situation
            print(f"DETECTED: Terminal for {task_name} closed but command processes still running")
            print(f"Cleaning up zombie processes for task: {task_name}")
            self.cleanup_task_processes(process, pid_file, task_name)
            return "Interrupted"

        # Continue monitoring
        time.sleep(2)

    return "Interrupted" if interrupted else "Unknown"

def check_command_processes_running(self, pid_file, task_name):
    """
    Check if the actual command processes are still running
    """
    try:
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())

            # Check if PID exists and get process info
            if psutil.pid_exists(pid):
                try:
                    proc = psutil.Process(pid)

                    # Check if it's our process (not reused PID)
                    cmdline = ' '.join(proc.cmdline())
                    if task_name in cmdline or 'task_' in cmdline:
                        # Get all child processes too
                        children = proc.children(recursive=True)
                        all_processes = [proc] + children

                        # Check if any are still running
                        running_processes = []
                        for p in all_processes:
                            try:
                                if p.is_running() and p.status() != psutil.STATUS_ZOMBIE:
                                    running_processes.append(p)
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue

                        if running_processes:
                            print(f"Found {len(running_processes)} processes still running for task {task_name}")
                            return True

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Process no longer exists or access denied
                    pass

    except Exception as e:
        print(f"Error checking command processes for {task_name}: {e}")

    return False

def cleanup_task_processes(self, terminal_process, pid_file, task_name):
    """
    Clean up both terminal and command processes
    """
    print(f"Cleaning up processes for task: {task_name}")

    # 1. Terminate terminal process if still running
    if terminal_process and terminal_process.poll() is None:
        try:
            terminal_process.terminate()
            time.sleep(2)
            if terminal_process.poll() is None:
                terminal_process.kill()
                print(f"Force killed terminal process for {task_name}")
        except Exception as e:
            print(f"Error terminating terminal process: {e}")

    # 2. Clean up command processes using PID file
    try:
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())

            if psutil.pid_exists(pid):
                try:
                    proc = psutil.Process(pid)

                    # Get all children first
                    children = proc.children(recursive=True)

                    # Terminate children first
                    for child in children:
                        try:
                            print(f"Terminating child process {child.pid} for task {task_name}")
                            child.terminate()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                    # Wait for children to exit
                    gone, alive = psutil.wait_procs(children, timeout=5)

                    # Force kill any remaining children
                    for child in alive:
                        try:
                            print(f"Force killing child process {child.pid} for task {task_name}")
                            child.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                    # Finally terminate the main process
                    print(f"Terminating main process {pid} for task {task_name}")
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        print(f"Force killing main process {pid} for task {task_name}")
                        proc.kill()

                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    print(f"Process {pid} already gone or access denied: {e}")

    except Exception as e:
        print(f"Error during process cleanup for {task_name}: {e}")

########
# Modified execute_task function

def execute_task(task):
    """Execute a task with process tree monitoring for accidental terminal closure detection"""
    global interrupted
    start_time = time.time()
    start_time_str = get_current_time()

    # Check for interruption before starting
    if interrupted:
        print(f"Task '{task['name']}' skipped due to interruption.")
        return start_time_str, start_time_str, "00:00:00:00", "Interrupted"

    if 'command' not in task or not task['command']:
        print(f"Skipping task '{task['name']}' as it has no command.")
        return start_time_str, start_time_str, "00:00:00:00", "Skipped"

    # Create unique task identifier
    task_id = f"{task['name']}_{execution_id}_{int(start_time)}"
    status_file = f"/tmp/task_status_{task_id}.txt"
    pid_file = f"/tmp/task_pid_{task_id}.txt"

    print(f"Executing {task['name']} at {start_time_str} with command: {task['command']}")
    status = "Success"
    table = PrettyTable()
    table.field_names = ["Output/Error Type", "Message"]

    try:
        # Check for interruption before creating script
        if interrupted:
            print(f"Task '{task['name']}' interrupted before script creation.")
            return start_time_str, get_current_time(), "00:00:00:01", "Interrupted"

        # Create enhanced C shell script with status tracking
        auto_flag = "1" if args.y else "0"
        script_content = f"""#!/usr/bin/csh
# Write PID for monitoring
echo $$ > {pid_file}

# Write start status
echo "RUNNING" > {status_file}
sync

# Display task information
echo "==============================================="
echo "CASINO FLOW MANAGER - TASK EXECUTION"
echo "Task: {task['name']}"
echo "Command: {task['command']}"
echo "==============================================="
echo "NOTE: This terminal will remain open for interactive tasks."
echo "The flow manager will wait for task completion status."
echo "To complete this task, ensure your command finishes properly."
echo "==============================================="
echo ""

# Set up signal handlers for proper cleanup (csh style)
onintr cleanup
goto start_execution

cleanup:
    echo "INTERRUPTED" > {status_file}
    sync
    echo "Task interrupted by user"
    exit 1

start_execution:
# Execute the actual command
echo "Starting task execution..."
{task['command']}
set exit_code = $status

# Write completion status with sync
if ($exit_code == 0) then
    echo "SUCCESS" > {status_file}
    sync
    echo ""
    echo "==============================================="
    echo "TASK COMPLETED SUCCESSFULLY"
    echo "Task: {task['name']}"
    echo "Exit Code: $exit_code"
    echo "You can now close this terminal window."
    echo "==============================================="
else
    echo "FAILED:$exit_code" > {status_file}
    sync
    echo ""
    echo "==============================================="
    echo "TASK FAILED"
    echo "Task: {task['name']}"
    echo "Exit Code: $exit_code"
    echo "Please check the error above."
    echo "==============================================="
endif

# Keep terminal open for review
echo "Press Enter to close this terminal..."
# Don't wait for input in auto mode or if task failed
if ({auto_flag} || $exit_code != 0) then
    echo "Auto-closing due to automation mode or failure..."
    sleep 2
else
    # Wait for user to press Enter before closing
    #set input = $<
endif

exit $exit_code
"""

        script_path = f"/tmp/task_{task_id}.csh"
        with open(script_path, 'w') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)

        # Check for interruption before launching
        if interrupted:
            print(f"Task '{task['name']}' interrupted before launch.")
            os.remove(script_path)
            return start_time_str, get_current_time(), "00:00:00:01", "Interrupted"

        # Create terminal command for task execution
        task_title = f"Task: {task['name']} [{task_id}] @ {run_dir}"
        task_cmd_args = ['/usr/bin/csh', script_path]

        terminal_cmd = create_terminal_command(
            selected_terminal,
            task_title,
            task_cmd_args,
            bg='gray' if selected_terminal == TerminalType.XTERM else None,
            fg='black' if selected_terminal == TerminalType.XTERM else None,
            working_directory=current_dir
        )

        # Create terminal command for task execution
        task_title = f"Task: {task['name']} [{task_id}] @ {run_dir}"
        task_cmd_args = ['/usr/bin/csh', script_path]

        # Determine colors based on task name for gnome-terminal
        if selected_terminal == TerminalType.XTERM:
            bg_color = 'gray'
            fg_color = 'black'
        elif selected_terminal == TerminalType.GNOME_TERMINAL:
            # Set colors based on task type
            task_name_lower = task['name'].lower()
            if 'manual' in task_name_lower:
                bg_color, fg_color = '#1B1619', '#D8DEE9'  # Default dark
            else:
                #bg_color, fg_color = '#1a472a', '#90EE90'  # Dark/Light green
                #bg_color, fg_color = '#2d1b69', '#87CEEB'  # Dark blue/Sky blue
                #bg_color, fg_color = '#8b0000', '#FFB6C1'  # Dark red/Light pink
                bg_color, fg_color = '#4a2c2a', '#DEB887'  # Dark brown/Burlywood
                #bg_color, fg_color = '#2f1b69', '#DDA0DD'  # Dark purple/Plum

        else:
            bg_color, fg_color = '#2E3440', '#D8DEE9'  # Default dark

        terminal_cmd = create_terminal_command(
            selected_terminal,
            task_title,
            task_cmd_args,
            bg=bg_color,
            fg=fg_color,
            working_directory=current_dir
        )

        process = subprocess.Popen(terminal_cmd, env=os.environ.copy())
        global current_process
        current_process = process

        # Use Option 1: Process tree monitoring
        status = monitor_with_process_tree_csh(
            process, status_file, pid_file, task['name'], max_wait_time=864000
        )

        current_process = None

        # Handle specific status cases
        if status == "Success":
            print(f"CONFIRMED: Task {task['name']} completed successfully - proceeding to next task")
        elif status == "Failed":
            print(f"CONFIRMED: Task {task['name']} failed - execution will stop")
        elif status == "Interrupted":
            print(f"CONFIRMED: Task {task['name']} was interrupted - execution will stop")
            interrupted = True
        elif status == "Timeout":
            print(f"CONFIRMED: Task {task['name']} timed out - execution will stop")
            table.add_row(["Timeout", f"Task exceeded maximum execution time"])
        else:
            print(f"UNCERTAIN: Task {task['name']} status unclear: {status}")
            status = "Failed"

        # Cleanup temp files
        for temp_file in [script_path, status_file, pid_file]:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass

    except KeyboardInterrupt:
        print(f"KeyboardInterrupt caught during task '{task['name']}' execution")
        interrupted = True
        status = "Interrupted"
        # Clean up temp files
        for temp_file in [script_path, status_file, pid_file]:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass

    except Exception as e:
        table.add_row(["Exception", f"An exception occurred while executing task {task['name']}: {e}"])
        status = "Failed"

    if table._rows:
        print(table)

    end_time = time.time()
    end_time_str = get_current_time()
    elapsed_time = end_time - start_time
    runtime = format_runtime(elapsed_time)

    print(f"Task {task['name']} completed at {end_time_str} in {runtime}. Status: {status}")

    # Save task completion immediately for real-time monitoring
    task_runtime_info = {
        "name": task['name'],
        "start_time": start_time_str,
        "end_time": end_time_str,
        "runtime": runtime,
        "status": status
    }
    save_completed_task_immediately(task_runtime_info)

    # If interrupted, make sure the global flag is set
    if status == "Interrupted":
        interrupted = True

    return start_time_str, end_time_str, runtime, status

def monitor_with_process_tree_csh(process, status_file, pid_file, task_name, max_wait_time=864000):
    """Monitor both status file and csh process health with FAST terminal death detection"""
    global interrupted
    wait_start = time.time()
    last_status = None
    last_process_check = time.time()
    last_terminal_check = time.time()
    terminal_closed_warned = False  # Track if we've already warned about terminal closure

    # BALANCED: Check process health every 5 minutes for stale status detection
    process_check_interval = 300  # 5 minutes for deep process checks

    # Terminal death detection: Check every 10 seconds (MUCH faster)
    terminal_check_interval = 10  # 10 seconds for terminal process checks

    # Grace period for stale status file (only for deep process checks)
    status_file_grace_period = 600  # 10 minutes without status update
    last_status_update = time.time()

    print(f"Monitoring task completion for {task_name} - checking status file + terminal + process health...")

    while not interrupted:
        current_time = time.time()

        # Check timeout
        if current_time - wait_start > max_wait_time:
            print(f"Task {task_name} exceeded maximum wait time, terminating...")
            cleanup_orphaned_processes(pid_file, task_name)
            return "Timeout"

        # PRIMARY: Check status file for completion (highest priority)
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r') as f:
                    status_content = f.read().strip()

                    if status_content != last_status:
                        if status_content == "RUNNING":
                            print(f"Task {task_name} is running...")
                            last_status_update = current_time  # Update timestamp
                        elif status_content.startswith('SUCCESS'):
                            print(f"Task {task_name} completed successfully")
                            return "Success"
                        elif status_content.startswith('FAILED'):
                            print(f"Task {task_name} failed")
                            return "Failed"
                        elif status_content == "INTERRUPTED":
                            print(f"Task {task_name} was interrupted")
                            return "Interrupted"
                        last_status = status_content

            except Exception as e:
                print(f"Warning: Could not read status file {status_file}: {e}")

        # NEW: FAST terminal process death detection (every 10 seconds)
        # This catches accidental "X" clicks on terminal window QUICKLY
        if current_time - last_terminal_check > terminal_check_interval:
            if detect_terminal_closed_fast(process, task_name):
                # Double-check: Is the actual task process still running?
                if not check_task_process_alive(pid_file, task_name):
                    # Task is dead - print final message and exit
                    if not terminal_closed_warned:
                        print(f"WARNING: Terminal window for {task_name} was closed and task process is dead - marking as INTERRUPTED")
                    else:
                        print(f"CONFIRMED: Task process is now dead - marking as INTERRUPTED")
                    cleanup_orphaned_processes(pid_file, task_name)
                    return "Interrupted"
                else:
                    # Terminal closed but task still running - warn only ONCE
                    if not terminal_closed_warned:
                        print(f"WARNING: Terminal window for {task_name} was closed (task still running in background - monitoring...)")
                        terminal_closed_warned = True
                    # Continue monitoring silently

            last_terminal_check = current_time

        # SECONDARY: Deep process health check (every 5 minutes, only if status stale)
        if current_time - last_process_check > process_check_interval:
            # Only perform aggressive checks if status file is stale
            if current_time - last_status_update > status_file_grace_period:
                print(f"Status file hasn't been updated for {int(current_time - last_status_update)}s - checking process health...")
                if detect_accidental_closure_csh_relaxed(pid_file, task_name):
                    print(f"DETECTED: Accidental terminal closure for {task_name}")
                    cleanup_orphaned_processes(pid_file, task_name)
                    return "Interrupted"
            last_process_check = current_time

        time.sleep(2)  # Check status file every 2 seconds

    return "Interrupted" if interrupted else "Unknown"


def detect_terminal_closed_fast(terminal_process, task_name):
    """
    FAST detection: Check if terminal window process has died
    This detects when user clicks "X" on terminal window within 10 seconds
    """
    try:
        # Check if terminal process is still running
        if terminal_process and terminal_process.poll() is not None:
            # Terminal process has exited
            return True
        return False
    except Exception as e:
        print(f"Error checking terminal for {task_name}: {e}")
        return False

def check_task_process_alive(pid_file, task_name):
    """
    Check if the actual csh task process is still alive
    Returns True if process is alive, False if dead
    """
    try:
        if not os.path.exists(pid_file):
            return False

        with open(pid_file, 'r') as f:
            csh_pid = int(f.read().strip())

        if not psutil.pid_exists(csh_pid):
            return False

        try:
            proc = psutil.Process(csh_pid)
            # Check if process is not zombie
            if proc.status() == psutil.STATUS_ZOMBIE:
                return False
            # Process exists and is not zombie
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    except Exception as e:
        print(f"Error checking task process for {task_name}: {e}")
        return False

def detect_accidental_closure_csh_relaxed(pid_file, task_name):
    """
    RELAXED version - only detect OBVIOUS cases of accidental closure
    Removes false-positive checks like terminal association and parent PID
    """
    try:
        if not os.path.exists(pid_file):
            print(f"PID file missing for {task_name} - likely accidental closure")
            return True

        with open(pid_file, 'r') as f:
            csh_pid = int(f.read().strip())

        if not psutil.pid_exists(csh_pid):
            print(f"Csh process {csh_pid} no longer exists for {task_name} - accidental closure detected")
            return True

        proc = psutil.Process(csh_pid)

        # CRITICAL FIX: Only check for zombie status - remove terminal and parent checks
        if proc.status() == psutil.STATUS_ZOMBIE:
            print(f"Csh process {csh_pid} is zombie for {task_name} - accidental closure detected")
            return True

        # REMOVED: Terminal association check (causes false positives with EDA tools)
        # REMOVED: Parent PID check (processes can legitimately be reparented)

    except (ValueError, FileNotFoundError, PermissionError) as e:
        print(f"Error checking csh process for {task_name}: {e} - assuming accidental closure")
        return True
    except Exception as e:
        print(f"Unexpected error checking csh process for {task_name}: {e}")
        return False  # Don't assume closure for unexpected errors

    return False  # Process looks healthy

def cleanup_orphaned_processes(pid_file, task_name):
    """Clean up orphaned processes after accidental terminal closure"""
    print(f"Cleaning up orphaned processes for task: {task_name}")

    try:
        if not os.path.exists(pid_file):
            print(f"No PID file found for {task_name}, cannot clean up processes")
            return

        with open(pid_file, 'r') as f:
            csh_pid = int(f.read().strip())

        if not psutil.pid_exists(csh_pid):
            print(f"Main csh process {csh_pid} already gone for {task_name}")
            return

        proc = psutil.Process(csh_pid)

        # Get all child processes first
        try:
            children = proc.children(recursive=True)
            print(f"Found {len(children)} child processes for {task_name}")

            # Terminate children first
            for child in children:
                try:
                    print(f"Terminating child process {child.pid} ({child.name()}) for task {task_name}")
                    child.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # Wait for children to exit
            if children:
                gone, alive = psutil.wait_procs(children, timeout=5)
                print(f"Terminated {len(gone)} child processes, {len(alive)} still alive")

                # Force kill any remaining children
                for child in alive:
                    try:
                        print(f"Force killing child process {child.pid} for task {task_name}")
                        child.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            print(f"Could not get children for process {csh_pid}")

        # Finally terminate the main csh process
        try:
            print(f"Terminating main csh process {csh_pid} for task {task_name}")
            proc.terminate()
            try:
                proc.wait(timeout=5)
                print(f"Main csh process {csh_pid} terminated gracefully")
            except psutil.TimeoutExpired:
                print(f"Force killing main csh process {csh_pid} for task {task_name}")
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            print(f"Main csh process {csh_pid} already gone")

    except Exception as e:
        print(f"Error during process cleanup for {task_name}: {e}")

    print(f"Process cleanup completed for task: {task_name}")

def display_previous_runs_summary():
    """Display the most recent previous run's task details with improved empty run detection"""
    pattern = os.path.join(RUNS_HISTORY_DIR, f'completed_tasks___{filename_suffix}_*.yaml')
    previous_files = glob.glob(pattern)

    if not previous_files:
        print("No previous runs found for this task range.")
        return False  # No previous run = proceed

    most_recent_file = max(previous_files, key=os.path.getmtime)

    try:
        filename = os.path.basename(most_recent_file)
        exec_id = filename.split('_')[-1].replace('.yaml', '')

        with open(most_recent_file, 'r') as f:
            content = f.read().strip()

        if not content:
            print("Most recent run file exists but is empty - no tasks were executed.")
            return False  # Empty file = not successful

        tasks_data = yaml.safe_load(content) or []
        if not isinstance(tasks_data, list) or len(tasks_data) == 0:
            print("Most recent run file exists but contains no task data.")
            return False  # No tasks = not successful

        file_time = datetime.fromtimestamp(os.path.getmtime(most_recent_file))
        print(f"\nMost Recent Run (Execution ID: {exec_id}):")
        print(f"Run Time: {file_time.strftime('%Y/%m/%d %H:%M:%S')}")
        print(f"{'No.':<3} {'Task Name':<20} {'Start Time':<22} {'End Time':<22} {'Runtime':<20} {'Status':<12}")
        print("-" * 120)

        for idx, task in enumerate(tasks_data):
            if task.get('name'):
                print(f"{idx + 1:<3} {task.get('name', ''):<20} {task.get('start_time', 'N/A'):<22} {task.get('end_time', 'N/A'):<22} {task.get('runtime', 'N/A'):<20} {task.get('status', 'Unknown'):<12}")

        print("-" * 120)

        total_tasks = len([t for t in tasks_data if t.get('name')])
        success_count = len([t for t in tasks_data if t.get('status') == 'Success'])
        failed_count = len([t for t in tasks_data if t.get('status') in ['Failed', 'Interrupted', 'Timeout']])
        not_executed = len([t for t in tasks_data if t.get('status') == 'Not Executed'])

        print(f"Summary: {total_tasks} total, {success_count} success, {failed_count} failed/interrupted, {not_executed} not executed")

        # Fixed logic: only successful if we have tasks AND all succeeded
        previous_run_completed = (total_tasks > 0 and success_count == total_tasks and failed_count == 0 and not_executed == 0)

        if previous_run_completed:
            print(f"? Previous run completed successfully - all {total_tasks} tasks finished with Success status")
        else:
            if total_tasks == 0:
                print("? Previous run had no tasks executed")
            else:
                print(f"? Previous run incomplete - {failed_count} failed/interrupted, {not_executed} not executed")

        return previous_run_completed

    except Exception as e:
        print(f"Error reading most recent run: {e}")
        return False

########


def monitor_process_and_status(process, status_file, pid_file, task_name, max_wait_time=864000):
    """
    Enhanced monitoring that detects both normal completion AND accidental terminal closure
    """
    global interrupted
    wait_start = time.time()
    last_status = None
    task_completed = False

    print(f"Monitoring task completion for {task_name} - checking both process and status...")

    while not interrupted and not task_completed:
        # Check timeout
        if time.time() - wait_start > max_wait_time:
            print(f"Task {task_name} exceeded maximum wait time, terminating...")
            cleanup_task_processes(process, pid_file, task_name)
            return "Timeout"

        # PRIMARY: Check status file for normal completion
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r') as f:
                    status_content = f.read().strip()

                    if status_content != last_status:
                        if status_content == "RUNNING":
                            print(f"Task {task_name} is running...")
                        elif status_content.startswith('SUCCESS'):
                            print(f"Task {task_name} completed successfully")
                            return "Success"
                        elif status_content.startswith('FAILED'):
                            print(f"Task {task_name} failed")
                            return "Failed"
                        elif status_content == "INTERRUPTED":
                            print(f"Task {task_name} was interrupted")
                            return "Interrupted"
                        last_status = status_content

            except Exception as e:
                print(f"Warning: Could not read status file {status_file}: {e}")

        # SECONDARY: Check if terminal process died unexpectedly
        terminal_dead = False
        if process.poll() is not None:
            # Terminal process has exited - this could be normal or accidental
            terminal_dead = True

        # TERTIARY: Check if actual command process is still running
        command_processes_running = check_command_processes_running(pid_file, task_name)

        # DECISION LOGIC:
        if terminal_dead and not command_processes_running:
            # Terminal died AND no command processes running
            if not os.path.exists(status_file) or last_status == "RUNNING":
                # No completion status written = accidental closure
                print(f"DETECTED: Terminal for {task_name} closed without proper completion status")
                print(f"This appears to be an accidental terminal closure - marking as INTERRUPTED")
                return "Interrupted"
            # else: Normal completion, status file shows final state

        elif terminal_dead and command_processes_running:
            # Terminal died but command still running = definite zombie situation
            print(f"DETECTED: Terminal for {task_name} closed but command processes still running")
            print(f"Cleaning up zombie processes for task: {task_name}")
            cleanup_task_processes(process, pid_file, task_name)
            return "Interrupted"

        # Continue monitoring
        time.sleep(2)

    return "Interrupted" if interrupted else "Unknown"

def check_command_processes_running(pid_file, task_name):
    """
    Check if the actual command processes are still running
    """
    try:
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())

            # Check if PID exists and get process info
            if psutil.pid_exists(pid):
                try:
                    proc = psutil.Process(pid)

                    # Check if it's our process (not reused PID)
                    cmdline = ' '.join(proc.cmdline())
                    if task_name in cmdline or 'task_' in cmdline:
                        # Get all child processes too
                        children = proc.children(recursive=True)
                        all_processes = [proc] + children

                        # Check if any are still running
                        running_processes = []
                        for p in all_processes:
                            try:
                                if p.is_running() and p.status() != psutil.STATUS_ZOMBIE:
                                    running_processes.append(p)
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue

                        if running_processes:
                            print(f"Found {len(running_processes)} processes still running for task {task_name}")
                            for rp in running_processes:
                                try:
                                    print(f"  - PID {rp.pid}: {' '.join(rp.cmdline()[:3])}")
                                except:
                                    print(f"  - PID {rp.pid}: <cannot read cmdline>")
                            return True

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Process no longer exists or access denied
                    pass

    except Exception as e:
        print(f"Error checking command processes for {task_name}: {e}")

    return False

def cleanup_task_processes(terminal_process, pid_file, task_name):
    """
    Clean up both terminal and command processes
    """
    print(f"Cleaning up processes for task: {task_name}")

    # 1. Terminate terminal process if still running
    if terminal_process and terminal_process.poll() is None:
        try:
            print(f"Terminating terminal process for {task_name}")
            terminal_process.terminate()
            time.sleep(2)
            if terminal_process.poll() is None:
                terminal_process.kill()
                print(f"Force killed terminal process for {task_name}")
        except Exception as e:
            print(f"Error terminating terminal process: {e}")

    # 2. Clean up command processes using PID file
    try:
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())

            if psutil.pid_exists(pid):
                try:
                    proc = psutil.Process(pid)

                    # Get all children first
                    children = proc.children(recursive=True)

                    # Terminate children first
                    for child in children:
                        try:
                            print(f"Terminating child process {child.pid} for task {task_name}")
                            child.terminate()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                    # Wait for children to exit
                    if children:
                        gone, alive = psutil.wait_procs(children, timeout=5)

                        # Force kill any remaining children
                        for child in alive:
                            try:
                                print(f"Force killing child process {child.pid} for task {task_name}")
                                child.kill()
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                pass

                    # Finally terminate the main process
                    print(f"Terminating main process {pid} for task {task_name}")
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        print(f"Force killing main process {pid} for task {task_name}")
                        proc.kill()

                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    print(f"Process {pid} already gone or access denied: {e}")

    except Exception as e:
        print(f"Error during process cleanup for {task_name}: {e}")

    print(f"Process cleanup completed for task: {task_name}")

def execute_task_single_terminal(task):
    """Execute a task in single terminal mode (sequential execution)"""
    global interrupted
    start_time = time.time()
    start_time_str = get_current_time()

    # Check for interruption before starting
    if interrupted:
        print(f"Task '{task['name']}' skipped due to interruption.")
        return start_time_str, start_time_str, "00:00:00:00", "Interrupted"

    if 'command' not in task or not task['command']:
        print(f"Skipping task '{task['name']}' as it has no command.")
        return start_time_str, start_time_str, "00:00:00:00", "Skipped"

    # Create unique task identifier
    task_id = f"{task['name']}_{execution_id}_{int(start_time)}"
    status_file = f"/tmp/task_status_{task_id}.txt"
    pid_file = f"/tmp/task_pid_{task_id}.txt"

    print(f"Executing {task['name']} at {start_time_str} with command: {task['command']}")
    status = "Success"

    try:
        # Check for interruption before creating script
        if interrupted:
            print(f"Task '{task['name']}' interrupted before script creation.")
            return start_time_str, get_current_time(), "00:00:00:01", "Interrupted"

        # Create enhanced C shell script with status tracking for single terminal
        auto_flag = "1" if args.y else "0"
        script_content = f"""#!/usr/bin/csh
# Write PID for monitoring
echo $$ > {pid_file}

# Write start status
echo "RUNNING" > {status_file}
sync

# Display task information
echo "==============================================="
echo "CASINO FLOW MANAGER - TASK EXECUTION (SINGLE TERMINAL)"
echo "Task: {task['name']}"
echo "Command: {task['command']}"
echo "==============================================="
echo "NOTE: This is single terminal mode - tasks run sequentially."
echo "The flow manager will wait for task completion status."
echo "==============================================="

# Execute the actual command
{task['command']}
set exit_code = $status

# Write completion status
if ($exit_code == 0) then
    echo "SUCCESS" > {status_file}
    echo "Task '{task['name']}' completed successfully."
else
    echo "FAILED:$exit_code" > {status_file}
    echo "Task '{task['name']}' failed with exit code: $exit_code"
endif

sync
exit $exit_code
"""

        script_path = f"/tmp/task_{task_id}.csh"
        with open(script_path, 'w') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)

        # Check for interruption before launching
        if interrupted:
            print(f"Task '{task['name']}' interrupted before launch.")
            os.remove(script_path)
            return start_time_str, get_current_time(), "00:00:00:01", "Interrupted"

        # Execute directly with csh (no xterm wrapper for single terminal mode)
        if args.interactive:
            # Interactive mode: inherit stdin/stdout/stderr for real-time interaction
            process = subprocess.Popen(
                ['/usr/bin/csh', script_path],
                env=os.environ.copy()
            )
        else:
            # Non-interactive mode: capture output for monitoring
            process = subprocess.Popen(
                ['/usr/bin/csh', script_path],
                env=os.environ.copy(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

        global current_process
        current_process = process

        # Monitor the process and status file
        max_wait_time = 864000  # 1 hour maximum wait
        wait_start = time.time()

        if args.interactive:
            # Interactive mode: simply wait for process completion
            print(f"Interactive mode: Task '{task['name']}' is running. You can interact with it directly.")

            # Check if the command might launch an interactive tool
            command_lower = task['command'].lower()
            interactive_tools = ['vim', 'nano', 'emacs', 'htop', 'top', 'less', 'more', 'man', 'bash', 'sh', 'csh', 'tcsh']
            detected_tool = None
            for tool in interactive_tools:
                if tool in command_lower:
                    detected_tool = tool
                    break

            print("=" * 60)
            if detected_tool:
                print(f"DETECTED INTERACTIVE TOOL: {detected_tool.upper()}")
                if detected_tool in ['vim', 'nano', 'emacs']:
                    print("- Text editor detected - Use standard editor commands to exit")
                    if detected_tool == 'vim':
                        print("  Vim: Press Esc, then type :q (or :wq to save)")
                    elif detected_tool == 'nano':
                        print("  Nano: Press Ctrl+X to exit")
                    elif detected_tool == 'emacs':
                        print("  Emacs: Press Ctrl+X, then Ctrl+C to exit")
                elif detected_tool in ['htop', 'top']:
                    print("- System monitor detected - Press 'q' to quit")
                elif detected_tool in ['less', 'more', 'man']:
                    print("- Pager detected - Press 'q' to quit")
                elif detected_tool in ['bash', 'sh', 'csh', 'tcsh']:
                    print("- Shell detected - Type 'exit' or press Ctrl+D to quit")
            else:
                print("IMPORTANT: If the task opens a tool shell or interactive interface:")
                print("- For text editors (vim, nano): Use :q or Ctrl+X to exit")
                print("- For system tools (htop, top): Press 'q' to quit")
                print("- For interactive GUIs: Close the window or use the exit option")
                print("- For command shells: Type 'exit' or press Ctrl+D")
                print("- For any tool: Press Ctrl+C to force exit if needed")
            print("=" * 60)
            print("Press Ctrl+C in this terminal to interrupt the entire task if needed.")
            try:
                process.wait()
            except KeyboardInterrupt:
                print(f"\nInterrupting task '{task['name']}'...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                os.remove(script_path)
                return start_time_str, get_current_time(), "00:00:00:01", "Interrupted"
        else:
            # Non-interactive mode: monitor with status file checking
            while process.poll() is None and not interrupted:
                # Check if we've been waiting too long
                if time.time() - wait_start > max_wait_time:
                    print(f"Task '{task['name']}' timed out after {max_wait_time} seconds.")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    os.remove(script_path)
                    return start_time_str, get_current_time(), "00:00:00:01", "Timeout"

                # Check status file for completion
                if os.path.exists(status_file):
                    try:
                        with open(status_file, 'r') as f:
                            status_content = f.read().strip()
                        if status_content.startswith("SUCCESS"):
                            break
                        elif status_content.startswith("FAILED"):
                            break
                    except Exception:
                        pass

                time.sleep(1)

        # Get final status
        final_status = "Success"
        if interrupted:
            final_status = "Interrupted"
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        elif process.returncode is not None:
            if process.returncode != 0:
                final_status = f"Failed (exit code: {process.returncode})"
        else:
            # Check status file for final status
            if os.path.exists(status_file):
                try:
                    with open(status_file, 'r') as f:
                        status_content = f.read().strip()
                    if status_content.startswith("FAILED"):
                        final_status = f"Failed ({status_content})"
                except Exception:
                    pass

        # Clean up
        try:
            os.remove(script_path)
            if os.path.exists(status_file):
                os.remove(status_file)
            if os.path.exists(pid_file):
                os.remove(pid_file)
        except Exception:
            pass

        end_time = time.time()
        end_time_str = get_current_time()
        runtime = end_time - start_time
        runtime_str = format_runtime(runtime)

        # Display output for non-interactive mode
        if not args.interactive and hasattr(process, 'stdout') and process.stdout:
            try:
                stdout_output = process.stdout.read()
                if stdout_output:
                    print("=== TASK OUTPUT ===")
                    print(stdout_output)
                    print("=== END OUTPUT ===")
            except Exception:
                pass

        print(f"Task '{task['name']}' completed with status: {final_status}")
        print(f"Runtime: {runtime_str}")

        return start_time_str, end_time_str, runtime_str, final_status

    except Exception as e:
        print(f"Error executing task '{task['name']}': {e}")
        end_time = time.time()
        end_time_str = get_current_time()
        runtime = end_time - start_time
        runtime_str = format_runtime(runtime)
        return start_time_str, end_time_str, runtime_str, f"Error: {str(e)}"

def execute_task_single_terminal_with_retries(task, max_retries=3):
    """Execute task in single terminal mode with retries, but stop immediately on interruption"""
    global interrupted

    # Check for interruption before starting
    if interrupted:
        return get_current_time(), get_current_time(), "00:00:00:01", "Interrupted"

    retries = 0
    while retries < max_retries:
        # Check for interruption before each retry
        if interrupted:
            print(f"Task '{task['name']}' execution stopped due to interruption")
            return get_current_time(), get_current_time(), "00:00:00:01", "Interrupted"

        start_time, end_time, runtime, status = execute_task_single_terminal(task)

        if status == "Success":
            return start_time, end_time, runtime, status

        # Don't retry interrupted tasks, timeouts, or when globally interrupted
        if status in ["Interrupted", "Timeout"] or interrupted:
            print(f"Task '{task['name']}' was {status.lower()} - not retrying")
            return start_time, end_time, runtime, status

        retries += 1
        if retries < max_retries:
            print(f"Retrying task '{task['name']}' ({retries}/{max_retries})...")

    print(f"Task '{task['name']}' failed after {max_retries} retries.")
    return start_time, end_time, runtime, "Failed"

def execute_task_with_retries(task, max_retries=3):
    """Execute task with retries, but stop immediately on interruption"""
    global interrupted

    # Check for interruption before starting
    if interrupted:
        return get_current_time(), get_current_time(), "00:00:00:01", "Interrupted"

    retries = 0
    while retries < max_retries:
        # Check for interruption before each retry
        if interrupted:
            print(f"Task '{task['name']}' execution stopped due to interruption")
            return get_current_time(), get_current_time(), "00:00:00:01", "Interrupted"

        start_time, end_time, runtime, status = execute_task(task)

        if status == "Success":
            return start_time, end_time, runtime, status

        # Don't retry interrupted tasks, timeouts, or when globally interrupted
        if status in ["Interrupted", "Timeout"] or interrupted:
            print(f"Task '{task['name']}' was {status.lower()} - not retrying")
            return start_time, end_time, runtime, status

        retries += 1
        if retries < max_retries:
            print(f"Retrying task '{task['name']}' ({retries}/{max_retries})...")

    print(f"Task '{task['name']}' failed after {max_retries} retries.")
    return start_time, end_time, runtime, "Failed"

def assign_task_numbers(execution_order):
    task_numbers = {}
    current_no = 1
    previous_task_info = None

    for idx, task_name in enumerate(execution_order):
        dependencies = task_dependencies.get(task_name, [])
        priority = task_priorities.get(task_name, 0)
        current_task_info = (set(dependencies), priority)

        if previous_task_info is None or current_task_info != previous_task_info:
            current_no = idx + 1

        task_numbers[task_name] = current_no
        previous_task_info = current_task_info

    return task_numbers

def execute_tasks_single_terminal(task_graph, execution_order):
    """Execute all tasks sequentially in single terminal mode"""
    global interrupted
    runtimes = []
    completed_task_names = set(t['name'] for t in completed_tasks)

    # Check for interruption before starting
    if interrupted:
        print("Execution was interrupted before starting tasks.")
        return runtimes

    print("=" * 70)
    print("CASINO FLOW MANAGER - SINGLE TERMINAL MODE")
    print("=" * 70)
    print("All tasks will be executed sequentially in this terminal.")
    print("Each task will run to completion before the next one starts.")
    if args.interactive:
        print("INTERACTIVE MODE: Tasks will run with real-time output and user input.")
        print("You can interact with each task as it runs, including tool shells and GUIs.")
        print("Useful for tasks that open editors, system tools, or interactive interfaces.")
    else:
        print("NON-INTERACTIVE MODE: Task output will be captured and displayed after completion.")
    print("=" * 70)

    # For single task execution (-only option)
    if args.only:
        task_name = execution_order[0]
        current_task = next(task for task in expanded_tasks if task['name'] == task_name)
        if task_name in completed_task_names and not args.force:
            print(f"Skipping task '{task_name}' as it is already completed.")
            return runtimes

        # Check for interruption before executing
        if interrupted:
            print("Execution was interrupted before starting task.")
            return runtimes

        # Execute the single task directly
        start_time, end_time, task_runtime, status = execute_task_single_terminal_with_retries(
            current_task,
            max_retries=args.max_retries
        )

        runtime_info = {
            "name": task_name,
            "start_time": start_time,
            "end_time": end_time,
            "runtime": task_runtime,
            "status": status
        }
        runtimes.append(runtime_info)

        # Write completed tasks file for real-time monitoring
        write_completed_tasks_file()

        # If task was interrupted, mark remaining tasks as not executed
        if status == "Interrupted" or interrupted:
            print("Task execution was interrupted.")

        return runtimes

    # Sequential execution for multiple tasks
    for task_name in execution_order:
        # Check for interruption before each task
        if interrupted:
            print("Execution was interrupted.")
            break

        # Skip if already completed and not forcing
        if task_name in completed_task_names and not args.force:
            print(f"Skipping task '{task_name}' as it is already completed.")
            continue

        # Find the task
        current_task = next(task for task in expanded_tasks if task['name'] == task_name)

        print(f"\n{'='*50}")
        print(f"Starting Task: {task_name}")
        print(f"{'='*50}")

        # Execute the task
        start_time, end_time, task_runtime, status = execute_task_single_terminal_with_retries(
            current_task,
            max_retries=args.max_retries
        )

        runtime_info = {
            "name": task_name,
            "start_time": start_time,
            "end_time": end_time,
            "runtime": task_runtime,
            "status": status
        }
        runtimes.append(runtime_info)

        # Write completed tasks file for real-time monitoring
        write_completed_tasks_file()

        print(f"Task '{task_name}' completed with status: {status}")
        print(f"Runtime: {task_runtime}")

        # If task failed and we're not forcing, we might want to stop
        if status not in ["Success", "Interrupted"] and not args.force:
            print(f"Task '{task_name}' failed. Consider using -force to continue with remaining tasks.")
            # Continue with next task instead of stopping

        # If task was interrupted, stop execution
        if status == "Interrupted" or interrupted:
            print("Task execution was interrupted. Stopping execution.")
            break

    return runtimes

def execute_tasks_with_constraints(task_graph, execution_order):
    global interrupted
    runtimes = []
    completed_task_names = set(t['name'] for t in completed_tasks)

    # Check for interruption before starting
    if interrupted:
        print("Execution was interrupted before starting tasks.")
        return runtimes

    # For single task execution (-only option)
    if args.only:
        task_name = execution_order[0]
        current_task = next(task for task in expanded_tasks if task['name'] == task_name)
        if task_name in completed_task_names and not args.force:
            print(f"Skipping task '{task_name}' as it is already completed.")
            return runtimes

        # Check for interruption before executing
        if interrupted:
            print("Execution was interrupted before starting task.")
            return runtimes

        # Execute the single task directly
        start_time, end_time, task_runtime, status = execute_task_with_retries(
            current_task,
            max_retries=args.max_retries
        )

        runtime_info = {
            "name": task_name,
            "start_time": start_time,
            "end_time": end_time,
            "runtime": task_runtime,
            "status": status
        }
        runtimes.append(runtime_info)

        # If task was interrupted, mark remaining tasks as not executed
        if status == "Interrupted" or interrupted:
            print("Task execution was interrupted.")

        return runtimes

    # Sequential execution for dependency-based tasks (no parallel execution)
    summary_table = PrettyTable()
    summary_table.field_names = ["Task Name", "Start Time", "End Time", "Runtime", "Status"]
    summary_table.align = "l"

    try:
        for task_name in execution_order:
            # Check for interruption before each task
            if interrupted:
                print(f"Execution interrupted before starting task '{task_name}'")
                # Mark all remaining tasks as "Not Executed"
                for remaining_task in execution_order:
                    if remaining_task not in [r['name'] for r in runtimes]:
                        runtimes.append({
                            "name": remaining_task,
                            "start_time": "N/A",
                            "end_time": "N/A",
                            "runtime": "N/A",
                            "status": "Not Executed"
                        })
                        summary_table.add_row([remaining_task, "N/A", "N/A", "N/A", "Not Executed"])
                break

            current_task = next(task for task in expanded_tasks if task['name'] == task_name)

            if task_name in completed_task_names and not args.force:
                print(f"Skipping task '{task_name}' as it is already completed.")
                runtimes.append({
                    "name": task_name,
                    "start_time": "N/A",
                    "end_time": "N/A",
                    "runtime": "N/A",
                    "status": "Skipped"
                })
                summary_table.add_row([task_name, "N/A", "N/A", "N/A", "Skipped"])
                continue

            # Execute task
            start_time, end_time, task_runtime, status = execute_task_with_retries(
                current_task,
                max_retries=args.max_retries
            )

            runtimes.append({
                "name": task_name,
                "start_time": start_time,
                "end_time": end_time,
                "runtime": task_runtime,
                "status": status
            })
            summary_table.add_row([task_name, start_time, end_time, task_runtime, status])

            # Check if task failed, was interrupted, or if global interruption occurred
            if status in ["Failed", "Interrupted", "Timeout"] or interrupted:
                print(f"Execution stopped due to {status.lower() if not interrupted else 'interruption'} in task: {task_name}")

                # Add remaining tasks as "Not Executed"
                for remaining_task in execution_order:
                    if remaining_task not in [r['name'] for r in runtimes]:
                        runtimes.append({
                            "name": remaining_task,
                            "start_time": "N/A",
                            "end_time": "N/A",
                            "runtime": "N/A",
                            "status": "Not Executed"
                        })
                        summary_table.add_row([remaining_task, "N/A", "N/A", "N/A", "Not Executed"])
                break

    except KeyboardInterrupt:
        print("KeyboardInterrupt caught in execution loop")
        interrupted = True
        # Mark any remaining tasks as not executed
        for remaining_task in execution_order:
            if remaining_task not in [r['name'] for r in runtimes]:
                runtimes.append({
                    "name": remaining_task,
                    "start_time": "N/A",
                    "end_time": "N/A",
                    "runtime": "N/A",
                    "status": "Not Executed"
                })
                summary_table.add_row([remaining_task, "N/A", "N/A", "N/A", "Not Executed"])

    except Exception as e:
        print(f"Execution interrupted. Error: {e}")

    print("\nExecution Summary:")
    print(summary_table)
    return runtimes

def build_graph_and_in_degree(tasks):
    task_graph = defaultdict(list)
    in_degree = defaultdict(int)
    task_priorities = {}
    task_dependencies = {}
    task_dependencies_or = {}

    task_dict = {task['name']: task for task in tasks}

    def process_task(task_name, parent=None):
        task = task_dict[task_name]
        task_priorities[task_name] = task.get('priority', 0)
        dependencies = task.get('dependencies', [])
        dependencies_or = task.get('dependencies_or', [])
        subtasks = task.get('subtasks', [])

        task_dependencies[task_name] = dependencies
        task_dependencies_or[task_name] = dependencies_or

        if parent:
            task_graph[parent].append(task_name)
            in_degree[task_name] += 1

        for dep in dependencies:
            if dep not in task_dict:
                raise ValueError(f"Dependency '{dep}' of task '{task_name}' not found.")
            task_graph[dep].append(task_name)
            in_degree[task_name] += 1
            if dep not in in_degree:
                process_task(dep)

        for dep_or in dependencies_or:
            if dep_or not in task_dict:
                raise ValueError(f"OR Dependency '{dep_or}' of task '{task_name}' not found.")
            if dep_or not in in_degree:
                process_task(dep_or)

        for subtask_name in subtasks:
            if subtask_name not in task_dict:
                raise ValueError(f"Subtask '{subtask_name}' of task '{task_name}' not found.")
            process_task(subtask_name, parent=task_name)

        if task_name not in in_degree:
            in_degree[task_name] = in_degree.get(task_name, 0)

    for task_name in task_dict:
        if task_name not in in_degree:
            process_task(task_name)

    return task_graph, in_degree, task_priorities, task_dependencies, task_dependencies_or

def expand_subtasks(tasks):
    expanded_tasks = []
    task_dict = {task['name']: task for task in tasks}
    seen = set()

    def add_task(task_name):
        if task_name in seen:
            return
        task = task_dict.get(task_name)
        if not task:
            raise ValueError(f"Task '{task_name}' not found.")
        seen.add(task_name)
        if 'subtasks' in task:
            for subtask_name in task['subtasks']:
                add_task(subtask_name)
        expanded_tasks.append(task)

    for task in tasks:
        add_task(task['name'])

    return expanded_tasks

expanded_tasks = expand_subtasks(data['tasks'])
all_tasks = [task['name'] for task in expanded_tasks]

def get_execution_range(tasks, start_task, end_task):
    if start_task and start_task not in tasks:
        raise ValueError(f"Start task '{start_task}' is not in the list of tasks.")
    if end_task and end_task not in tasks:
        raise ValueError(f"End task '{end_task}' is not in the list of tasks.")

    execution_range = []
    if start_task and end_task:
        start_index = tasks.index(start_task)
        end_index = tasks.index(end_task) + 1
        execution_range = tasks[start_index:end_index]
    else:
        execution_range = tasks

    return execution_range

execution_range = get_execution_range(all_tasks, args.start, args.end)
task_graph, in_degree, task_priorities, task_dependencies, task_dependencies_or = build_graph_and_in_degree(expanded_tasks)
filtered_tasks = [task for task in expanded_tasks if task['name'] in execution_range]

if not args.force:
    for task in completed_tasks:
        if task['name'] in in_degree:
            del in_degree[task['name']]
            for dependent in task_graph[task['name']]:
                in_degree[dependent] -= 1

def calculate_execution_order(task_graph, in_degree, task_dependencies, task_dependencies_or):
    execution_order = []
    ready_queue = deque([task for task in in_degree if in_degree[task] == 0])
    waiting_or_dependencies = {}

    for task in in_degree:
        if task_dependencies_or.get(task):
            waiting_or_dependencies[task] = set(task_dependencies_or[task])

    while ready_queue or waiting_or_dependencies:
        while ready_queue:
            current_task = ready_queue.popleft()
            execution_order.append(current_task)
            for dependent in task_graph.get(current_task, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    ready_queue.append(dependent)
            for task, dependencies in list(waiting_or_dependencies.items()):
                if current_task in dependencies:
                    dependencies.remove(current_task)
                    execution_order.append(task)
                    del waiting_or_dependencies[task]
                    for dependent in task_graph.get(task, []):
                        in_degree[dependent] -= 1
                        if in_degree[dependent] == 0:
                            ready_queue.append(dependent)
        if waiting_or_dependencies:
            task, dependencies = waiting_or_dependencies.popitem()
            execution_order.append(task)
            for dependent in task_graph.get(task, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    ready_queue.append(dependent)

    seen = set()
    execution_order = [x for x in execution_order if not (x in seen or seen.add(x))]
    execution_order = [task for task in execution_order if task in [t['name'] for t in filtered_tasks]]
    execution_order.sort(key=lambda t: task_priorities.get(t, 0))
    return execution_order

execution_order = calculate_execution_order(task_graph, in_degree, task_dependencies, task_dependencies_or)

if args.only:
    selected_task = next((t for t in data['tasks'] if t['name'] == args.only), None)
    if selected_task is None:
        raise ValueError(f"Task '{args.only}' not found in the list of tasks.")
    execution_order = []
    def collect_subtasks(task):
        if 'subtasks' in task:
            for subtask_name in task['subtasks']:
                subtask = next((t for t in expanded_tasks if t['name'] == subtask_name), None)
                if subtask:
                    collect_subtasks(subtask)
        else:
            execution_order.append(task['name'])
    collect_subtasks(selected_task)

if not execution_order:
    print("No tasks to execute.")
    exit(0)

execution_table = PrettyTable()
execution_table.field_names = ["No.", "Task", "Dependencies", "Dependencies_or", "Priority"]
execution_table.align["No."] = "l"
execution_table.align["Task"] = "l"
execution_table.align["Dependencies"] = "l"
execution_table.align["Dependencies_or"] = "l"
execution_table.align["Priority"] = "l"

current_no = 1
previous_task_info = None

for idx, task in enumerate(execution_order):
    dependencies = ", ".join(task_dependencies.get(task, []))
    dependencies_or = ", ".join(task_dependencies_or.get(task, []))
    priority = task_priorities.get(task, 'N/A')
    current_task_info = (dependencies, dependencies_or, priority)
    if previous_task_info is None or current_task_info != previous_task_info:
        current_no = idx + 1
    previous_task_info = current_task_info
    execution_table.add_row([current_no, task, dependencies, dependencies_or, priority])

print("\nExecution Order:")
print(execution_table)

# Launch task monitor if requested
if args.monitor:
    monitor_process = launch_task_monitor()
    if monitor_process:
        print(f"Task monitor is running in {selected_terminal.value}. You can monitor progress in the separate terminal window.")
        print("The monitor will automatically update every 2 seconds.")
        print("The monitor will stay open until you manually close it.")
        print()

# Main execution flow with intelligent go/no-go decision based on previous run
if not args.y:  # Only use intelligent decision if -y flag is not set
    # Decision logic based on previous run status
    if previous_run_successful:
        print(f"\n{'='*70}")
        print("INTELLIGENT DECISION: Previous run completed successfully.")
        print("All tasks in the previous execution finished with Success status.")
        print("RECOMMENDATION: Skip execution to avoid redundant work.")
        print(f"{'='*70}")
        print("\nOptions:")
        print("  'y' - Force proceed all tasks (like -force option)")
        print("  'n' - Exit (follow recommendation)")
        print("  Any other key - Abort")
        print("\nChoice (y/n/other): ", end="", flush=True)
    else:
        print(f"\n{'='*70}")
        print("INTELLIGENT DECISION: Previous run was incomplete or failed.")
        print("Some tasks failed, were interrupted, or were not executed.")
        print("RECOMMENDATION: Proceed to complete missing work.")
        print(f"{'='*70}")
        print("\nOptions:")
        print("  'y' - Proceed all tasks (like -force option)")
        print("  'n' - Exit")
        print("  's' - Smart proceed from failed task only")
        print("  Any other key - Abort")
        print("\nChoice (y/n/s/other): ", end="", flush=True)

    try:
        user_input = input().strip().lower()
        #print("-" * 70)

        if user_input == 'y':
            # Force proceed with all tasks
            print("Force proceeding with all tasks (ignoring previous completions).")
            args.force = True  # Set force flag dynamically
        elif user_input == 'n':
            print("Execution skipped.")
            if monitor_process:
                print("Task monitor will continue running. You can close it manually when done.")
                print("Monitor PID:", monitor_process.pid)
            exit(0)
        elif user_input == 's' and not previous_run_successful:
            # Smart proceed - load successful tasks from previous run
            print("Smart proceeding from failed task (loading previous successes).")
            try:
                # Load previous successful tasks into current completed_tasks
                pattern = os.path.join(RUNS_HISTORY_DIR, f'completed_tasks___{filename_suffix}_*.yaml')
                previous_files = glob.glob(pattern)
                if previous_files:
                    most_recent_file = max(previous_files, key=os.path.getmtime)
                    with open(most_recent_file, 'r') as f:
                        content = f.read().strip()
                        if content:
                            previous_tasks = yaml.safe_load(content) or []
                            # Only load successfully completed tasks
                            successful_tasks = [t for t in previous_tasks if t.get('status') == 'Success']
                            completed_tasks.extend(successful_tasks)
                            print(f"Loaded {len(successful_tasks)} successful tasks from previous run.")
            except Exception as e:
                print(f"Warning: Could not load previous successful tasks: {e}")
        else:
            print("Execution aborted by user.")
            if monitor_process:
                print("Task monitor will continue running. You can close it manually when done.")
                print("Monitor PID:", monitor_process.pid)
            exit(0)

    except KeyboardInterrupt:
        print("\nExecution aborted by user (Ctrl+C).")
        interrupted = True
        if monitor_process:
            print("Task monitor will continue running. You can close it manually when done.")
            print("Monitor PID:", monitor_process.pid)
        exit(0)
else:
    print("Auto-proceeding with execution (-y flag set)")
    print("-" * 70)

# Check for interruption before starting task execution
if interrupted:
    print("Execution was interrupted before starting.")
    if monitor_process:
        print("Task monitor will continue running. You can close it manually when done.")
        print("Monitor PID:", monitor_process.pid)
    exit(0)

print("Starting task execution...")
if args.singleTerm:
    print("Using single terminal mode - tasks will run sequentially in this terminal.")
    runtimes = execute_tasks_single_terminal(task_graph, execution_order)
else:
    print("Using multi-terminal mode - each task will run in its own terminal window.")
    runtimes = execute_tasks_with_constraints(task_graph, execution_order)

# Check if execution was interrupted
if interrupted:
    print("\nExecution was interrupted.")
    print("Some tasks may not have completed.")
else:
    print("\nTask execution completed normally.")

completed_tasks = [task for task in completed_tasks if task['name'] not in [r['name'] for r in runtimes]]
completed_tasks.extend(runtimes)

write_completed_tasks_file()

def append_to_runtime_history(runtimes, runtime_history_file):
    header = (
        "Task Name            Start (YY/MM/DD HH:MM:SS)      End (YY/MM/DD HH:MM:SS)        Runtime (DD:HH:MM:SS) Status\n"
        "-------------------------------------------------------------------------------------------------------------------------\n"
    )
    lines = []
    execution_order_line = "Execution order : " + ", ".join(execution_order[:]) + "\n"
    lines.append(execution_order_line)
    lines.append("-" * 120 + "\n")
    for runtime in runtimes:
        line = (
            f"{runtime['name']:<20} {runtime['start_time']:<30} {runtime['end_time']:<30} {runtime['runtime']:<20} {runtime['status']:<10}\n"
        )
        lines.append(line)
    with open(runtime_history_file, 'a') as file:
        if os.stat(runtime_history_file).st_size == 0:
            file.write(header)
        file.writelines(lines)
        file.write("-" * 120 + "\n")

if runtimes:
    overall_start_time = min(task['start_time'] for task in runtimes if task['start_time'] != "N/A")
    overall_end_time = max(task['end_time'] for task in runtimes if task['end_time'] != "N/A")
    overall_runtime_seconds = calculate_time_difference(overall_start_time, overall_end_time)
    overall_runtime = format_runtime(overall_runtime_seconds)
    runtimes.append({
        "name": "Total",
        "start_time": overall_start_time,
        "end_time": overall_end_time,
        "runtime": overall_runtime,
        "status": ""
    })

    print("\nTask Start/End Times and Runtimes:")
    print(f"{'Task Name':<20} {'Start (YY/MM/DD HH:MM:SS)':<30} {'End (YY/MM/DD HH:MM:SS)':<30} {'Runtime (DD:HH:MM:SS)':<20} {'Status':<10}")
    print("-" * 120)
    for runtime in runtimes:
        print(f"{runtime['name']:<20} {runtime['start_time']:<30} {runtime['end_time']:<30} {runtime['runtime']:<20} {runtime['status']:<10}")
    print("-" * 120)
    append_to_runtime_history(runtimes, RUNTIME_HISTORY_FILE)
else:
    print("No tasks were executed.")

# Cleanup monitor process if it was launched
if monitor_process:
    print("\nTask execution completed.")
    print(f"Task monitor will continue running in {selected_terminal.value}. You can close it manually when done.")
    print("Monitor PID:", monitor_process.pid)
    print("To close the monitor: Press Ctrl+C in the monitor window or close the terminal window.")
