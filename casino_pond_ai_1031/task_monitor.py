#!/usr/local/bin/python3.12

import yaml
import os
import argparse
import time
import psutil
import glob
import shutil
import sys
from io import StringIO
from datetime import datetime
from prettytable import PrettyTable
from pathlib import Path
from enum import Enum
from typing import Dict, List, Optional, Any

class TerminalType(Enum):
    XTERM = "xterm"
    GNOME_TERMINAL = "gnome-terminal"

def detect_current_terminal():
    """Detect which terminal we're running in"""
    # Check TERM environment variable and parent process
    term_env = os.environ.get('TERM', '').lower()

    # Check parent process name
    try:
        parent_pid = os.getppid()
        parent = psutil.Process(parent_pid)
        parent_name = parent.name().lower()

        if 'gnome-terminal' in parent_name:
            return TerminalType.GNOME_TERMINAL
        elif 'xterm' in parent_name:
            return TerminalType.XTERM
    except:
        pass

    # Fallback to environment variables
    if 'gnome' in term_env:
        return TerminalType.GNOME_TERMINAL
    elif 'xterm' in term_env:
        return TerminalType.XTERM

    return None

def setup_terminal_colors(terminal_type: Optional[TerminalType]):
    """Setup terminal colors based on terminal type"""
    if terminal_type == TerminalType.GNOME_TERMINAL:
        # ANSI color codes for gnome-terminal
        return {
            'reset': '\033[0m',
            'bold': '\033[1m',
            'dim': '\033[2m',
            'green': '\033[32m',
            'red': '\033[31m',
            'yellow': '\033[33m',
            'blue': '\033[34m',
            'cyan': '\033[36m',
            'white': '\033[37m',
            'bg_black': '\033[40m',
            'bg_green': '\033[42m',
            'bg_red': '\033[41m'
        }
    else:
        # Default/xterm colors - more conservative
        return {
            'reset': '\033[0m',
            'bold': '\033[1m',
            'dim': '\033[2m',
            'green': '\033[32m',
            'red': '\033[31m',
            'yellow': '\033[33m',
            'blue': '\033[34m',
            'cyan': '\033[36m',
            'white': '\033[37m',
            'bg_black': '',
            'bg_green': '',
            'bg_red': ''
        }

def clear_screen_and_home():
    """Move cursor to home position without clearing (reduces flicker)"""
    # Just move cursor to home - don't clear
    # Content will be overwritten by new output
    sys.stdout.write('\033[H')
    sys.stdout.flush()

def clear_screen():
    """Clear the terminal screen gracefully without blinking"""
    # Use ANSI escape sequences to move cursor and clear screen
    # Build everything in a buffer first, then write all at once
    buffer = []
    buffer.append('\033[?25l')  # Hide cursor
    buffer.append('\033[2J')     # Clear entire screen
    buffer.append('\033[H')      # Move cursor to home (1,1)
    sys.stdout.write(''.join(buffer))
    sys.stdout.flush()

def show_cursor():
    """Show the terminal cursor"""
    sys.stdout.write('\033[?25h')
    sys.stdout.flush()

def hide_cursor():
    """Hide the terminal cursor"""
    sys.stdout.write('\033[?25l')
    sys.stdout.flush()

class DisplayBuffer:
    """Buffer for collecting output before displaying all at once"""
    def __init__(self):
        self.lines = []

    def add(self, text=''):
        """Add a line to the buffer"""
        self.lines.append(str(text))

    def flush_to_screen(self):
        """Write all buffered content to screen at once"""
        # Move to home and write everything at once
        output = '\033[H' + '\n'.join(self.lines)
        # Pad with empty lines to clear any leftover content from previous display
        output += '\n' * 10  # Extra blank lines to clear old content
        sys.stdout.write(output)
        sys.stdout.flush()
        self.lines = []

def format_runtime(seconds: float) -> str:
    """Format runtime in DD:HH:MM:SS format"""
    if seconds is None or seconds == 0:
        return "00:00:00:00"

    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{days:02d}:{hours:02d}:{minutes:02d}:{secs:02d}"

def get_current_time() -> str:
    """Get current time in YYYY/MM/DD HH:MM:SS format"""
    return datetime.now().strftime("%Y/%m/%d %H:%M:%S")

def calculate_runtime(start_time_str: str, end_time_str: Optional[str] = None) -> float:
    """Calculate runtime between start and end time"""
    if not start_time_str:
        return 0

    try:
        start_time = datetime.strptime(start_time_str, "%Y/%m/%d %H:%M:%S")
        if end_time_str:
            end_time = datetime.strptime(end_time_str, "%Y/%m/%d %H:%M:%S")
        else:
            end_time = datetime.now()

        return (end_time - start_time).total_seconds()
    except:
        return 0

def load_flow_tasks(flow_file: str) -> List[Dict[str, Any]]:
    """Load task definitions from flow file"""
    try:
        with open(flow_file, 'r') as f:
            data = yaml.safe_load(f)
            return data.get('tasks', [])
    except Exception as e:
        print(f"Error loading flow file: {e}")
        return []

def load_completed_tasks(completed_file: str, execution_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load completed tasks from file - execution-specific filtering"""
    if not os.path.exists(completed_file):
        print(f"DEBUG: Completed file does not exist: {completed_file}")
        return []

    try:
        with open(completed_file, 'r') as f:
            content = f.read().strip()
            if not content:
                print(f"DEBUG: Completed file is empty: {completed_file}")
                return []

        #print(f"DEBUG: Raw file content:\n{content}\n" + "="*50)

        # Handle both YAML list format and individual task format
        loaded_data = yaml.safe_load(content)
        #print(f"DEBUG: YAML parsed data: {loaded_data}")

        if loaded_data is None:
            return []
        elif isinstance(loaded_data, list):
            all_tasks = loaded_data
        else:
            # Single task format - convert to list
            all_tasks = [loaded_data]

        #print(f"DEBUG: All tasks before filtering: {all_tasks}")

        # CRITICAL FIX: If execution_id provided, only return tasks that have a matching execution_id field
        # OR tasks that are associated with our current session (very recent + in our memory)
        if execution_id:
            execution_specific_tasks = []

            for task in all_tasks:
                print(f"DEBUG: Processing task {task.get('name')} with status '{task.get('status')}'")

                # Check if task has execution_id metadata (new approach)
                task_exec_id = task.get('execution_id')
                if task_exec_id == execution_id:
                    execution_specific_tasks.append(task)
                    continue

                # Fallback: VERY strict time filtering - only last 5 minutes for backward compatibility
                if not task.get('end_time'):
                    continue

                try:
                    task_end_time = datetime.strptime(task['end_time'], "%Y/%m/%d %H:%M:%S")
                    task_timestamp = task_end_time.timestamp()
                    current_time = time.time()

                    # MUCH stricter: only 5 minutes instead of 10, and only if no execution_id in task
                    if not task_exec_id and (current_time - task_timestamp < 300):  # 5 minutes
                        execution_specific_tasks.append(task)
                        print(f"DEBUG: Task {task.get('name')} included via time filter")
                except Exception as e:
                    print(f"DEBUG: Error parsing time for task {task.get('name')}: {e}")
                    continue

            print(f"DEBUG: Final execution-specific tasks: {execution_specific_tasks}")
            return execution_specific_tasks

        return all_tasks
    except Exception as e:
        print(f"DEBUG: Error loading completed tasks: {e}")
        return []

def detect_running_tasks(flow_tasks: List[Dict], execution_id: Optional[str] = None) -> Dict[str, Dict]:
    """Detect currently running tasks using PID files - execution-specific only"""
    running_tasks = {}

    # Only detect tasks for THIS execution ID - prevents cross-execution interference
    if not execution_id:
        return running_tasks

    try:
        for task in flow_tasks:
            task_name = task['name']

            # ONLY search for PID files with matching execution ID
            pid_patterns = [f"/tmp/task_pid_{task_name}_{execution_id}_*.txt"]

            for pattern in pid_patterns:
                pid_files = glob.glob(pattern)
                pid_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

                for pid_file in pid_files:
                    try:
                        if os.path.exists(pid_file):
                            # Check if file is very recent (within last 10 seconds) for faster detection
                            file_age = time.time() - os.path.getmtime(pid_file)

                            with open(pid_file, 'r') as f:
                                pid_str = f.read().strip()

                            if pid_str.isdigit():
                                pid = int(pid_str)

                                if psutil.pid_exists(pid):
                                    try:
                                        proc = psutil.Process(pid)
                                        proc_status = proc.status()

                                        # Use file creation time for very recent tasks
                                        if file_age < 10:
                                            start_time = datetime.fromtimestamp(os.path.getmtime(pid_file))
                                        else:
                                            start_time = datetime.fromtimestamp(proc.create_time())

                                        running_tasks[task_name] = {
                                            'pid': pid,
                                            'start_time': start_time.strftime("%Y/%m/%d %H:%M:%S"),
                                            'status': 'running',
                                            'file_age': file_age
                                        }
                                        break  # Found running instance
                                    except psutil.NoSuchProcess:
                                        # Clean up stale PID file
                                        try:
                                            os.remove(pid_file)
                                        except:
                                            pass
                                else:
                                    # Clean up stale PID file
                                    try:
                                        os.remove(pid_file)
                                    except:
                                        pass
                    except Exception as e:
                        continue

                if task_name in running_tasks:
                    break  # Found in this pattern, no need to try others

    except Exception as e:
        pass

    return running_tasks

def filter_tasks_by_range(tasks: List[Dict], start_task: Optional[str],
                         end_task: Optional[str], only_task: Optional[str]) -> List[Dict]:
    """Filter tasks based on execution range"""
    if only_task:
        return [task for task in tasks if task['name'] == only_task]

    if not start_task and not end_task:
        return tasks

    task_names = [task['name'] for task in tasks]

    if start_task and start_task not in task_names:
        return tasks
    if end_task and end_task not in task_names:
        return tasks

    if start_task and end_task:
        start_idx = task_names.index(start_task)
        end_idx = task_names.index(end_task) + 1
        return tasks[start_idx:end_idx]

    return tasks

def create_status_display(status: str, colors: Dict[str, str]) -> str:
    """Create colored status display"""
    status_lower = status.lower()

    # DEBUG: Show what status is being processed
    #print(f"DEBUG STATUS: Processing status='{status}' (lower='{status_lower}')")

    if 'running' in status_lower or 'run' in status_lower:
        return f"{colors['cyan']}{colors['bold']}[RUN]{colors['reset']} {colors['cyan']}running{colors['reset']}"
    elif 'interrupt' in status_lower or 'stop' in status_lower:
        return f"{colors['red']}{colors['bold']}[STOP]{colors['reset']} {colors['red']}interrupted{colors['reset']}"
    elif 'success' in status_lower or 'completed' in status_lower or 'done' in status_lower:
        return f"{colors['green']}{colors['bold']}[DONE]{colors['reset']} {colors['green']}completed{colors['reset']}"
    elif 'fail' in status_lower or 'error' in status_lower:
        return f"{colors['red']}{colors['bold']}[FAIL]{colors['reset']} {colors['red']}failed{colors['reset']}"
    elif 'timeout' in status_lower or 'time' in status_lower:
        return f"{colors['red']}{colors['bold']}[TIME]{colors['reset']} {colors['red']}timeout{colors['reset']}"
    elif 'skip' in status_lower:
        return f"{colors['dim']}[SKIP]{colors['reset']} {colors['dim']}skipped{colors['reset']}"
    elif 'wait' in status_lower:
        return f"{colors['white']}[WAIT]{colors['reset']} waiting"
    elif 'not executed' in status_lower:
        return f"{colors['dim']}[----]{colors['reset']} {colors['dim']}not executed{colors['reset']}"
    else:
        return f"[????] {status}"

def create_progress_bar(success_count: int, failed_count: int, running_count: int,
                       total_tasks: int, colors: Dict[str, str], width: int = 50) -> str:
    """Create a colored progress bar"""
    if total_tasks == 0:
        return f"[{'-' * width}] 0.0%"

    processed = success_count + failed_count + running_count
    progress = processed / total_tasks * 100

    success_width = int(success_count / total_tasks * width)
    failed_width = int(failed_count / total_tasks * width)
    running_width = int(running_count / total_tasks * width)
    remaining_width = width - success_width - failed_width - running_width

    bar_parts = []
    if success_width > 0:
        bar_parts.append(f"{colors['green']}{'=' * success_width}{colors['reset']}")
    if failed_width > 0:
        bar_parts.append(f"{colors['red']}{'X' * failed_width}{colors['reset']}")
    if running_width > 0:
        bar_parts.append(f"{colors['cyan']}{'~' * running_width}{colors['reset']}")
    if remaining_width > 0:
        bar_parts.append('-' * remaining_width)

    bar = ''.join(bar_parts)
    return f"[{bar}] {progress:.1f}%"

def print_header(colors: Dict[str, str], terminal_type: Optional[TerminalType],
                execution_id: Optional[str], monitor_session_id: Optional[str] = None):
    """Print the monitor header with styling"""
    # Get current directory information
    current_dir = os.getcwd()
    path_components = current_dir.strip(os.sep).split(os.sep)
    run_ver_components = path_components[-4:]
    run_dir = path_components[-1]
    run_ver = os.sep.join(run_ver_components)

    print(f"{colors['bold']}{colors['cyan']}{'=' * 80}{colors['reset']}")
    print(f"{colors['bold']}{colors['white']}CASINO FLOW MANAGER - TASK MONITOR{colors['reset']}")
    print(f"{colors['bold']}{colors['yellow']}Run Directory: {run_dir}{colors['reset']}")
    print(f"{colors['dim']}Full Path: {current_dir}{colors['reset']}")
    print(f"{colors['dim']}Run Version: {run_ver}{colors['reset']}")
    if terminal_type:
        print(f"{colors['dim']}Terminal: {terminal_type.value}{colors['reset']}")
    if execution_id:
        print(f"{colors['bold']}{colors['green']}Execution ID: {execution_id}{colors['reset']}")
    if monitor_session_id:
        print(f"{colors['dim']}Monitor Session: {monitor_session_id}{colors['reset']}")
    print(f"{colors['dim']}Last Updated: {get_current_time()}{colors['reset']}")
    print(f"{colors['bold']}{colors['cyan']}{'=' * 80}{colors['reset']}")
    print(f"{colors['dim']}Press Ctrl+C to exit{colors['reset']}")
    print()

def main():
    parser = argparse.ArgumentParser(description="Enhanced Real-time Task Monitor")
    parser.add_argument('--flow', required=True, help="Flow YAML file")
    parser.add_argument('--completed', required=True, help="Completed tasks file")
    parser.add_argument('--runtime', required=True, help="Runtime history file")
    parser.add_argument('--start', help="Start task")
    parser.add_argument('--end', help="End task")
    parser.add_argument('--only', help="Only task")
    parser.add_argument('--force', action='store_true', help="Force mode")
    parser.add_argument('--execution-id', help="Unique execution ID for this monitor instance")
    parser.add_argument('--refresh-rate', type=float, default=1.0, help="Refresh rate in seconds")
    parser.add_argument('--clear-on-start', action='store_true', help="Clear completed tasks memory on start for fresh monitoring")
    parser.add_argument('--singleTerm', action='store_true', help="Single terminal mode flag (informational only)")
    parser.add_argument('--interactive', action='store_true', help="Interactive mode flag (informational only)")

    args = parser.parse_args()

    # Detect current terminal type
    current_terminal = detect_current_terminal()
    colors = setup_terminal_colors(current_terminal)

    # Monitor session identification
    monitor_session_id = f"monitor_{int(time.time())}"

    print("Starting enhanced task monitor...")
    print(f"Monitor session ID: {monitor_session_id}")
    print(f"Arguments received: --flow={args.flow}, --completed={args.completed}, --runtime={args.runtime}")
    print(f"Execution ID: {args.execution_id}")

    # Verify critical files exist before proceeding
    missing_files = []
    for file_path, name in [(args.flow, "Flow"), (args.completed, "Completed"), (args.runtime, "Runtime")]:
        if not os.path.exists(file_path):
            missing_files.append(f"{name} ({file_path})")

    if missing_files:
        print(f"ERROR: Missing required files: {', '.join(missing_files)}")
        print("Monitor cannot start without these files.")
        return 1

    if current_terminal:
        print(f"Detected terminal: {current_terminal.value}")
    else:
        print("Terminal type detection failed, using default colors")

    # Show execution isolation
    if args.execution_id:
        print(f"Monitoring execution ID: {args.execution_id}")
        print("This monitor will ONLY track tasks from this specific execution.")
    else:
        print("WARNING: No execution ID provided - monitor may show mixed results from different runs!")

    print("Note: Each monitor instance only shows tasks from its own execution run.")
    print("Monitor initialization complete - starting main loop...")
    print()

    # Keep track of tasks we've seen running (enhanced memory)
    seen_running = {}  # task_name -> {'start_time': ..., 'first_seen': ..., 'last_seen': ...}
    completed_tasks = {}  # task_name -> {'start_time': ..., 'end_time': ..., 'status': ...}

    # Clear stale data if requested or if force mode is detected
    if args.clear_on_start or args.force:
        print("Clearing task monitoring memory for fresh start...")
        seen_running.clear()
        completed_tasks.clear()

    # Monitor statistics
    monitor_start_time = time.time()
    update_count = 0

    time.sleep(1)

    # Hide cursor for smoother display updates
    hide_cursor()

    try:
        while True:
            # Capture all output in a buffer to write at once (prevents flicker)
            output_buffer = StringIO()
            old_stdout = sys.stdout

            try:
                sys.stdout = output_buffer

                update_count += 1

                # Load flow tasks
                flow_tasks = load_flow_tasks(args.flow)
                filtered_tasks = filter_tasks_by_range(flow_tasks, args.start, args.end, args.only)

                # FIRST: Detect currently running tasks (check this BEFORE loading completed tasks)
                try:
                    running_tasks = detect_running_tasks(flow_tasks, args.execution_id)
                except Exception as e:
                    running_tasks = {}

                # Update our memory: track tasks that start running
                current_time = get_current_time()
                newly_started_tasks = []

                for task_name, running_info in running_tasks.items():
                    if task_name not in seen_running:
                        seen_running[task_name] = {
                            'start_time': running_info['start_time'],
                            'first_seen': current_time,
                            'last_seen': current_time
                        }
                        newly_started_tasks.append(task_name)
                    else:
                        seen_running[task_name]['last_seen'] = current_time

                # SECOND: Load completed tasks from execution-specific file
                # Since file is execution-specific, we can safely reload it each time to get updates
                try:
                    file_completed_tasks = load_completed_tasks(args.completed)
                    file_completed_dict = {task.get('name'): task for task in file_completed_tasks if task.get('name')}

                    # Update completed_tasks with latest file data
                    for task_name, file_task in file_completed_dict.items():
                        # Always update with latest file data since file is execution-specific
                        if task_name not in running_tasks:  # Don't override currently running tasks
                            original_status = file_task.get('status', 'completed')
                            completed_tasks[task_name] = {
                                'start_time': file_task.get('start_time', 'N/A'),
                                'end_time': file_task.get('end_time', 'N/A'),
                                'status': original_status
                            }

                            # Show when new completions are detected
                            #if update_count > 1 and task_name not in [t for t in completed_tasks.keys() if t != task_name]:
                                #print(f"NEW COMPLETION: {task_name} -> {original_status}")

                except Exception as e:
                    file_completed_dict = {}

                # THIRD: Update completed tasks based on transitions from running to not-running
                # This relies ONLY on our execution-specific memory and PID detection
                for task_name, task_info in seen_running.items():
                    if task_name not in running_tasks and task_name not in completed_tasks:
                        # Task was running but isn't anymore - mark as completed
                        completed_tasks[task_name] = {
                            'start_time': task_info['start_time'],
                            'end_time': current_time,
                            'status': 'completed'  # We can't determine success/failure without file data
                        }

                # Display newly started tasks for immediate feedback
                #if newly_started_tasks:
                    #print(f"{colors['green']}{colors['bold']}NEW TASK(S) STARTED:{colors['reset']}")
                    #for task_name in newly_started_tasks:
                        #print(f"  {colors['cyan']}? {task_name}{colors['reset']} started at {running_tasks[task_name]['start_time']}")
                    #print()

                # Calculate statistics
                total_tasks = len(filtered_tasks)
                running_count = len(running_tasks)

                # Count completed tasks by status
                success_count = 0
                failed_count = 0
                not_executed_count = 0
                skipped_count = 0

                for task_info in completed_tasks.values():
                    status = task_info.get('status', 'unknown').lower()
                    if status == 'success':
                        success_count += 1
                    elif status in ['failed', 'error', 'interrupted', 'timeout']:
                        failed_count += 1
                    elif status == 'completed':
                        success_count += 1  # Treat 'completed' as success
                    elif status in ['not executed']:
                        not_executed_count += 1
                    elif status in ['skipped']:
                        skipped_count += 1
                    else:
                        # FIXED: Don't default unknown statuses to success
                        # Check if it might be an interrupted task based on status string
                        if 'interrupt' in status:
                            failed_count += 1
                        else:
                            success_count += 1

                waiting_count = total_tasks - running_count - success_count - failed_count - not_executed_count - skipped_count

                # Print header with styling
                print_header(colors, current_terminal, args.execution_id, monitor_session_id)

                # Status summary with colors
                status_line = (f"{colors['green']}{success_count} completed{colors['reset']} | "
                              f"{colors['red']}{failed_count} failed{colors['reset']} | "
                              f"{colors['cyan']}{running_count} running{colors['reset']} | "
                              f"{colors['white']}{waiting_count} waiting{colors['reset']}")

                if not_executed_count > 0:
                    status_line += f" | {colors['dim']}{not_executed_count} not executed{colors['reset']}"
                if skipped_count > 0:
                    status_line += f" | {colors['dim']}{skipped_count} skipped{colors['reset']}"

                print(f"Status: {status_line}")

                # Enhanced progress bar
                if total_tasks > 0:
                    progress_bar = create_progress_bar(success_count, failed_count, running_count, total_tasks, colors)
                    print(f"Progress: {progress_bar}")
                    if failed_count > 0 or not_executed_count > 0:
                        legend = (f"Legend: {colors['green']}= Success{colors['reset']}  "
                                 f"{colors['red']}X Failed/Error{colors['reset']}  "
                                 f"{colors['cyan']}~ Running{colors['reset']}  "
                                 f"- Waiting")
                        print(legend)

                # Monitor statistics
                monitor_uptime = time.time() - monitor_start_time
                print(f"Monitor uptime: {format_runtime(monitor_uptime)} | Updates: {update_count}")
                print()

                # Enhanced status table with colors
                table = PrettyTable()
                table.field_names = ["Task Name", "Status", "Start Time", "End Time", "Runtime", "PID"]
                table.align = "l"

                for task in filtered_tasks:
                    task_name = task['name']

                    if task_name in running_tasks:
                        # Currently running
                        running_info = running_tasks[task_name]
                        runtime_seconds = calculate_runtime(running_info['start_time'])
                        status_display = create_status_display("running", colors)

                        table.add_row([
                            f"{colors['bold']}{task_name}{colors['reset']}",
                            status_display,
                            running_info['start_time'],
                            "-",
                            f"{colors['cyan']}{format_runtime(runtime_seconds)}{colors['reset']}",
                            f"{colors['dim']}{running_info['pid']}{colors['reset']}"
                        ])

                    elif task_name in completed_tasks:
                        # Completed
                        completed_info = completed_tasks[task_name]
                        runtime_seconds = calculate_runtime(completed_info['start_time'], completed_info['end_time'])

                        # Get the actual status and format it properly
                        actual_status = completed_info.get('status', 'completed')
                        status_display = create_status_display(actual_status, colors)

                        # Color the runtime based on status
                        runtime_color = colors['green'] if actual_status.lower() == 'success' else colors['red'] if 'fail' in actual_status.lower() else colors['reset']

                        table.add_row([
                            task_name,
                            status_display,
                            completed_info['start_time'],
                            completed_info['end_time'],
                            f"{runtime_color}{format_runtime(runtime_seconds)}{colors['reset']}",
                            "-"
                        ])

                    else:
                        # Waiting
                        status_display = create_status_display("waiting", colors)
                        table.add_row([
                            f"{colors['dim']}{task_name}{colors['reset']}",
                            status_display,
                            "-",
                            "-",
                            "-",
                            "-"
                        ])

                print(table)
                print()

                # Currently running tasks summary
                if running_count > 0:
                    print(f"{colors['bold']}{colors['cyan']}Currently Running:{colors['reset']}")
                    for task_name, running_info in running_tasks.items():
                        if any(task['name'] == task_name for task in filtered_tasks):
                            runtime_seconds = calculate_runtime(running_info['start_time'])
                            print(f"  {colors['cyan']}{task_name}{colors['reset']} "
                                  f"(PID: {colors['dim']}{running_info['pid']}{colors['reset']}) - "
                                  f"{colors['cyan']}{format_runtime(runtime_seconds)}{colors['reset']}")
                    print()

                # Summary statistics
                if total_tasks > 0:
                    completion_rate = (success_count + failed_count) / total_tasks * 100
                    success_rate = success_count / (success_count + failed_count) * 100 if (success_count + failed_count) > 0 else 0

                    stats_line = (f"Completion: {completion_rate:.1f}% | "
                                 f"Success Rate: {success_rate:.1f}% | "
                                 f"Total Tasks: {total_tasks}")
                    print(f"{colors['dim']}{stats_line}{colors['reset']}")

                # File status indicator
                files_status = []
                for file_path, label in [(args.flow, "Flow"), (args.completed, "Completed"), (args.runtime, "Runtime")]:
                    try:
                        if os.path.exists(file_path):
                            mtime = os.path.getmtime(file_path)
                            age = time.time() - mtime
                            if age < 60:  # Less than 1 minute old
                                files_status.append(f"{colors['green']}{label}+{colors['reset']}")
                            else:
                                files_status.append(f"{colors['dim']}{label}+{colors['reset']}")
                        else:
                            files_status.append(f"{colors['red']}{label}-{colors['reset']}")
                    except Exception as e:
                        files_status.append(f"{colors['red']}{label}?{colors['reset']}")

                print(f"Files: {' '.join(files_status)}")

                # Show execution context
                context_info = []
                if args.start:
                    context_info.append(f"Start: {args.start}")
                if args.end:
                    context_info.append(f"End: {args.end}")
                if args.only:
                    context_info.append(f"Only: {args.only}")
                if args.force:
                    context_info.append("Force mode")

                if context_info:
                    print(f"{colors['dim']}Context: {' | '.join(context_info)}{colors['reset']}")
                    print()

                # Execution isolation info
                if args.execution_id:
                    print(f"{colors['dim']}Tracking execution: {args.execution_id} | PID files: /tmp/task_pid_*_{args.execution_id}_*.txt{colors['reset']}")
                    print()

            finally:
                # Restore stdout and write buffered content all at once
                sys.stdout = old_stdout
                buffered_content = output_buffer.getvalue()
                output_buffer.close()

                # Clear screen and write all content in one operation
                sys.stdout.write('\033[H\033[2J')  # Home + clear
                sys.stdout.write(buffered_content)
                sys.stdout.flush()

                # Update interval with resource-conservative refresh rates
                refresh_interval = args.refresh_rate

                # Conservative refresh rates to reduce CPU usage
                if running_count > 0:
                    refresh_interval = 2.0  # 2s when tasks are running (reduced from 0.5s)
                elif success_count + failed_count < total_tasks:
                    refresh_interval = 3.0  # 3s when tasks are expected to start (reduced from 1s)
                else:
                    refresh_interval = max(args.refresh_rate, 5.0)  # 5s when all done (increased from 2s)

                time.sleep(refresh_interval)

    except KeyboardInterrupt:
        show_cursor()  # Restore cursor visibility
        clear_screen()
        print(f"{colors['bold']}{colors['yellow']}Task monitor stopped by user.{colors['reset']}")
        print(f"Monitor ran for {format_runtime(time.time() - monitor_start_time)} with {update_count} updates.")

        # Final summary
        if total_tasks > 0:
            final_completion = (success_count + failed_count) / total_tasks * 100
            print(f"Final status: {final_completion:.1f}% completion, {success_count} successful, {failed_count} failed")

    except Exception as e:
        show_cursor()  # Restore cursor visibility
        clear_screen()
        print(f"{colors['red']}Error in task monitor: {e}{colors['reset']}")
        print("Monitor terminated unexpectedly.")

    finally:
        show_cursor()  # Always restore cursor on exit

if __name__ == "__main__":
    main()
