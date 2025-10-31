#!/usr/local/bin/python3.12 -u

import os
import re
import subprocess
import sys
import yaml
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTextEdit, QLineEdit, QLabel, QMessageBox,
                             QSplitter, QShortcut, QDialog, QFormLayout, QDialogButtonBox,
                             QCheckBox, QComboBox, QTabWidget, QScrollArea, QGroupBox)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QKeySequence
from prettytable import PrettyTable
from PyQt5 import QtWidgets, QtCore, QtGui

import random

# Add Hawkeye import
try:
    from hawkeye_casino.core.analyzer import HawkeyeAnalyzer
    from hawkeye_casino.gui import GUI_AVAILABLE, HawkeyeDashboard
    HAWKEYE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Hawkeye module not available: {e}")
    HAWKEYE_AVAILABLE = False
    HawkeyeAnalyzer = None
    HawkeyeDashboard = None

# Fixed import - use MainWindow instead of DirectoryTracerApp
from treem_casino.ui.main_window import MainWindow
from treem_casino.config.settings import AppConfig

# Fixed import - use MainWindow instead of DirectoryTracerApp
from treem_casino.ui.main_window import MainWindow
from treem_casino.config.settings import AppConfig

# Define colors as variables
OLIVE = "#778a35"
PEWTER = "#ebebe8"
OLIVE_GREEN = "#31352e"
IVORY = "#EBECE0"
PURPLE_HAZE = "#a98ab0"
TEAL = "#9dced0"
MISTY_BLUE = "#c8d3da"
FOREST_GREEN = "#2B5434"
BLUE_GROTTO = "#045ab7"
CRIMSON = "#90010a"
ROYAL_BLUE = "#0c1446"
SAGE_GREEN = "#D6D3C0"
DARK_BLUE = "#061828"
DEEP_BLUE = "#050A30"
MIDNIGHT = "#050A30"
SCARLET = "#A92420"

# Default hotkey mappings (can be customized by user)
DEFAULT_HOTKEYS = {
    'dk_mgr': 'Ctrl+D',
    'flow_mgr': 'Ctrl+F',
    'timer': 'Ctrl+T',
    'indicator': 'Ctrl+I'
}

# Default macro configurations
DEFAULT_MACROS = {
    'manual_inn_macro': {
        'hotkey': 'Ctrl+Shift+M',
        'manager': 'flow_mgr',
        'args': '-only manual_inn -force -y',
        'description': 'Execute manual_inn task with force and auto-confirm'
    },
    'syn_macro': {
        'hotkey': 'Ctrl+Shift+S',
        'manager': 'flow_mgr',
        'args': '-only syn -force -y',
        'description': 'Execute synthesis task with force and auto-confirm'
    }
}

# Help messages for dk_mgr and flow_mgr
DK_MGR_HELP = """
[dk_mgr Help]<br>
<span style='color: black; font-weight: bold;'>Options:</span><br>
<table>
    <tr><td>-init_git</td>     <td>:</td> <td>Initialize and commit to Git</td></tr>
    <tr><td>-create_ver</td>   <td>:</td> <td>Flag to create db_ver <span style='color: red;'>(no value is required)</span></td></tr>
    <tr><td>-link_set</td>     <td>:</td> <td>ver.make describing design,mem, pdk, std, io, ip, and misc</td></tr>
    <tr><td>-link_ver</td>     <td>:</td> <td>Version name for linking</td></tr>
</table><br>
"""

FLOW_MGR_HELP = """
[flow_mgr Help]<br>
<span style='color: black; font-weight: bold;'>Options:</span><br>
<table>
    <tr><td>-start</td>    <td>:</td> <td>Set the start task</td></tr>
    <tr><td>-end</td>      <td>:</td> <td>Set the end task</td></tr>
    <tr><td>-only</td>     <td>:</td> <td>Set the subtasks only</td></tr>
    <tr><td>-force</td>    <td>:</td> <td>Force tasks ignoring status completed</td></tr>
    <tr><td>-flow</td>     <td>:</td> <td>Set flow_casino.yaml</td></tr>
    <tr><td>-monitor</td>     <td>:</td> <td>To enable monitoring term</td></tr>
    <tr><td>-max_workers</td>     <td>:</td> <td>Set max workers</td></tr>
    <tr><td>-y</td>        <td>:</td> <td>Automatically proceed with execution without confirmation prompt</td></tr>
</table><br>
"""

# Help messages for dk_mgr and flow_mgr
DK_MGR_ARGS = [
    "-init_git", "-create_ver", "-link_set", "-link_ver"
]

FLOW_MGR_ARGS = [
    "-start", "-end", "-only", "-force", "-flow", "-monitor", "-max_workers"
]

# Maps manager names to their argument lists
MANAGER_ARGUMENTS = {
    "dk_mgr": DK_MGR_ARGS,
    "flow_mgr": FLOW_MGR_ARGS
}

def run_casino_script(self):
    try:
        env_vars = os.environ
        prj_base = os.getenv('casino_prj_base')

        if prj_base:
            os.chdir(prj_base)
            self.append_output(f"Going to {prj_base} : $prj_base\n")
        else:
            self.append_output("Error: prj_base is not set in the configuration file.\n")
            return

        casino_pond = env_vars.get("casino_pond")
        if not casino_pond:
            self.append_output("Error: casino_pond is not set in the environment.\n")
            return

    except Exception as e:
        QMessageBox.critical(self, "Execution Error", str(e))

    self.input_box.setFocus()

def display_selected_env_vars(env_vars, selected_vars, console_output):
    """Display environment variables in a table format in the GUI console."""
    table = PrettyTable()
    table.field_names = ["Variable", "Value"]

    for var_name in selected_vars:
        if var_name in env_vars:
            table.add_row([var_name, env_vars[var_name]])

    table.align = "l"
    console_output.insertPlainText(str(table) + "\n")
    console_output.ensureCursorVisible()

class CommandExecutionThread(QThread):
    output_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    task_done_signal = pyqtSignal(str)

    def __init__(self, command, manager_name):
        super().__init__()
        self.command = command
        self.manager_name = manager_name
        self.process = None

    def run(self):
        try:
            is_buffered = self.manager_name in ['indicator', 'timer']
            bufsize = 1 if is_buffered else 0

            env = os.environ.copy()

            if 'DISPLAY' in env:
                pass
            elif 'DISPLAY' in os.environ:
                env['DISPLAY'] = os.environ['DISPLAY']

            if 'XAUTHORITY' in os.environ:
                env['XAUTHORITY'] = os.environ['XAUTHORITY']

            if 'XDG_RUNTIME_DIR' in os.environ:
                env['XDG_RUNTIME_DIR'] = os.environ['XDG_RUNTIME_DIR']

            if sys.platform == 'win32':
                self.process = subprocess.Popen(
                    self.command,
                    stdout=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    encoding='utf-8',
                    errors='replace',
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    bufsize=bufsize,
                    env=env
                )
            else:
                if self.manager_name == 'flow_mgr':
                    self.process = subprocess.Popen(
                        self.command,
                        stdout=subprocess.PIPE,
                        stdin=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        encoding='utf-8',
                        errors='replace',
                        shell=True,
                        bufsize=bufsize,
                        env=env
                    )
                else:
                    self.process = subprocess.Popen(
                        self.command,
                        stdout=subprocess.PIPE,
                        stdin=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        encoding='utf-8',
                        errors='replace',
                        shell=True,
                        start_new_session=True,
                        bufsize=bufsize,
                        env=env
                    )

            output_buffer = []
            buffer_size = 10 if is_buffered else 1

            while True:
                output = self.process.stdout.readline()
                if output == '' and self.process.poll() is not None:
                    break

                if output:
                    if "Press 'y' to continue with the execution" in output:
                        if '-y' in self.command:
                            self.process.stdin.write('y\n')
                            self.process.stdin.flush()
                            self.output_signal.emit(output)
                            self.output_signal.emit("y\n")
                        else:
                            self.output_signal.emit(output)
                            self.output_signal.emit("Waiting for user input... Type 'y' to continue or 'n' to abort, then press Enter.\n")
                    elif not is_buffered:
                        self.output_signal.emit(output)
                    else:
                        output_buffer.append(output)
                        if len(output_buffer) >= buffer_size:
                            self.output_signal.emit(''.join(output_buffer))
                            output_buffer = []

            if output_buffer:
                self.output_signal.emit(''.join(output_buffer))

            self.process.stdout.close()
            self.process.wait()

            if self.process.returncode != 0:
                self.error_signal.emit(f"\nCommand failed with return code {self.process.returncode}\n")
            else:
                self.task_done_signal.emit(self.manager_name)

        except Exception as e:
            self.error_signal.emit(f"\nError executing the command: {e}\n")

    def send_input(self, input_text):
        if self.process:
            try:
                self.process.stdin.write(input_text + '\n')
                self.process.stdin.flush()
            except Exception as e:
                self.error_signal.emit(f"\nError sending input to the command: {e}\n")

class InputField(QLineEdit):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.command_histories = {}
        self.history_index = -1
        self.current_manager = None
        self.auto_complete_options = []
        self.installEventFilter(self)

    def set_current_manager(self, manager_name):
        self.current_manager = manager_name
        if self.current_manager not in self.command_histories:
            self.command_histories[self.current_manager] = []
        self.history_index = -1

    def add_to_history(self, command):
        if self.current_manager and command.strip():
            self.command_histories[self.current_manager].append(command)
            self.history_index = -1

    def get_current_history(self):
        if self.current_manager in self.command_histories:
            return self.command_histories[self.current_manager]
        return []

    def eventFilter(self, source, event):
        if event.type() == event.KeyPress and source == self:
            if event.key() == Qt.Key_Tab:
                self.auto_complete()
                return True
        return super().eventFilter(source, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            history = self.get_current_history()
            if history and self.history_index < len(history) - 1:
                self.history_index += 1
                self.setText(history[-(self.history_index + 1)])
        elif event.key() == Qt.Key_Down:
            history = self.get_current_history()
            if history and self.history_index > 0:
                self.history_index -= 1
                self.setText(history[-(self.history_index + 1)])
            elif self.history_index == 0:
                self.history_index = -1
                self.clear()
        else:
            super().keyPressEvent(event)

    def auto_complete(self):
        current_text = self.text().strip()
        words = current_text.split()

        if words and words[-1].startswith('-'):
            last_word = words[-1]
            manager_name = self.main_window.selected_manager[0] if self.main_window.selected_manager else None

            if manager_name and manager_name in MANAGER_ARGUMENTS:
                possible_args = [arg for arg in MANAGER_ARGUMENTS[manager_name] if arg.startswith(last_word)]

                if len(possible_args) == 1:
                    completed_text = ' '.join(words[:-1] + [possible_args[0]]) + ' '
                    self.setText(completed_text)
                    self.setCursorPosition(len(completed_text))
                elif len(possible_args) > 1:
                    self.main_window.console_output.insertPlainText(f"\nPossible arguments: {', '.join(possible_args)}\n")
                    self.main_window.scroll_to_bottom()
                    self.setFocus()
        elif words and self.main_window.selected_manager and self.main_window.selected_manager[0] == 'flow_mgr':
            last_word = words[-1]
            if len(words) >= 2 and words[-2] in ['-start', '-end', '-only']:
                matching_tasks = [task for task in self.main_window.flow_task_names if task.startswith(last_word)]
                if len(matching_tasks) == 1:
                    completed_text = ' '.join(words[:-1] + [matching_tasks[0]]) + ' '
                    self.setText(completed_text)
                    self.setCursorPosition(len(completed_text))
                elif len(matching_tasks) > 1:
                    self.main_window.console_output.insertPlainText(f"\nPossible tasks: {', '.join(matching_tasks)}\n")
                    self.main_window.scroll_to_bottom()
                    self.setFocus()

class ClickableLabel(QLabel):
    """Custom QLabel that displays the title letter by letter and resets input field when clicked."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_text = "CA$INO"
        self.original_color = MIDNIGHT
        self.clicked_color = CRIMSON
        self.current_text = ""
        self.text_index = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.display_letter)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent().input_field.clear()
            self.current_text = ""
            self.text_index = 0
            self.timer.start(100)
            self.parent().go_back_to_base_dir()
            self.parent().display_ascii_art()
            self.parent().show_info()

    def display_letter(self):
        if self.text_index < len(self.original_text):
            next_letter = self.original_text[self.text_index]
            self.current_text += next_letter

            prj_name = os.getenv('casino_prj_name', 'N/A')
            design_ver = os.getenv('casino_design_ver', 'N/A')
            dk_ver = os.getenv('casino_dk_ver', 'N/A')
            tag = os.getenv('casino_tag', 'N/A')

            title_html = f"""
            <div style='text-align: center;'>
                <h1 style='color: {self.clicked_color}; font-weight: bold; font-size: 14px; margin: 1px;'>{self.current_text}</h1>
                <div style='color: {MIDNIGHT}; font-size: 10px; font-family: Terminus; margin: 1px;'>
                    {prj_name} | {design_ver} | {dk_ver} | {tag}
                </div>
            </div>
            """
            self.setText(title_html)
            self.text_index += 1
        else:
            self.timer.stop()
            QTimer.singleShot(200, self.reset_color)

    def reset_color(self):
        prj_name = os.getenv('casino_prj_name', 'N/A')
        design_ver = os.getenv('casino_design_ver', 'N/A')
        dk_ver = os.getenv('casino_dk_ver', 'N/A')
        tag = os.getenv('casino_tag', 'N/A')

        title_html = f"""
        <div style='text-align: center;'>
            <h1 style='color: {ROYAL_BLUE}; font-weight: bold; font-size: 14px; margin: 1px;'>{self.current_text}</h1>
            <div style='color: {MIDNIGHT}; font-size: 10px; font-family: Terminus; margin: 1px;'>
                {prj_name} | {design_ver} | {dk_ver} | {tag}
            </div>
        </div>
        """
        self.setText(title_html)

class MacroTab(QWidget):
    """Widget for macro configuration tab"""

    def __init__(self, available_managers=None, parent=None):
        super().__init__(parent)
        self.macro_widgets = {}
        self.available_managers = available_managers or ['flow_mgr', 'dk_mgr', 'timer', 'indicator']
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel("Configure macro shortcuts to execute predefined manager commands:")
        instructions.setStyleSheet("color: gray; margin-bottom: 10px; font-size: 10px;")
        layout.addWidget(instructions)

        # Scroll area for macros
        scroll = QScrollArea()
        scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_widget)

        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        # Add macro button
        add_button = QPushButton("Add New Macro")
        add_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {FOREST_GREEN};
                color: white;
                border: 1px solid {MIDNIGHT};
                border-radius: 3px;
                padding: 5px;
                font-family: Terminus;
                font-size: 9px;
            }}
        """)
        add_button.clicked.connect(self.add_macro)
        layout.addWidget(add_button)

    def add_macro(self, macro_name=None, macro_config=None):
        """Add a new macro configuration widget"""
        try:
            if macro_name is None:
                macro_name = f"macro_{len(self.macro_widgets) + 1}"

            if macro_config is None:
                macro_config = {
                    'hotkey': '',
                    'manager': 'flow_mgr',
                    'args': '',
                    'description': ''
                }

            macro_widget = self.create_macro_widget(macro_name, macro_config)
            self.scroll_layout.addWidget(macro_widget)
            self.macro_widgets[macro_name] = macro_widget
        except Exception as e:
            print(f"Error adding macro: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add macro: {str(e)}")

    def create_macro_widget(self, macro_name, macro_config):
        """Create a single macro configuration widget"""
        try:
            # Ensure macro_name is a string
            if not isinstance(macro_name, str):
                macro_name = str(macro_name)

            group = QGroupBox(macro_name)
            group.setStyleSheet(f"""
                QGroupBox {{
                    font-family: Terminus;
                    font-size: 10px;
                    font-weight: bold;
                    border: 1px solid {MIDNIGHT};
                    border-radius: 3px;
                    margin-top: 10px;
                    padding-top: 10px;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }}
            """)

            form_layout = QFormLayout(group)

            # Macro name (editable)
            name_input = QLineEdit(str(macro_name))
            name_input.setStyleSheet("padding: 3px; font-family: Terminus; font-size: 9px;")
            # Connect name input to update group box title in real-time
            name_input.textChanged.connect(lambda text: group.setTitle(text or "unnamed"))
            form_layout.addRow("Name:", name_input)

            # Hotkey input
            hotkey_input = QLineEdit(str(macro_config.get('hotkey', '')))
            hotkey_input.setPlaceholderText("e.g., Ctrl+Shift+M")
            hotkey_input.setStyleSheet("padding: 3px; font-family: Terminus; font-size: 9px;")
            form_layout.addRow("Hotkey:", hotkey_input)

            # Manager selection - Custom ComboBox with click-only selection
            manager_combo = QComboBox()
            manager_combo.addItems(self.available_managers)
            manager_combo.setCurrentText(str(macro_config.get('manager', 'flow_mgr')))

            # Disable wheel events to prevent accidental changes
            manager_combo.wheelEvent = lambda event: None

            manager_combo.setStyleSheet("""
                QComboBox {
                    padding: 5px 8px;
                    font-family: Terminus;
                    font-size: 9px;
                    background-color: white;
                    border: 1px solid #050A30;
                    border-radius: 3px;
                    min-height: 20px;
                }
                QComboBox::drop-down {
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 20px;
                    border-left: 1px solid #050A30;
                    border-radius: 3px;
                    background-color: #ebebe8;
                }
                QComboBox::down-arrow {
                    width: 12px;
                    height: 12px;
                    background-color: #050A30;
                }
                QComboBox:hover {
                    border: 2px solid #045ab7;
                }
                QComboBox:focus {
                    border: 2px solid #045ab7;
                    outline: none;
                }
                QComboBox QAbstractItemView {
                    background-color: white;
                    color: #050A30;
                    selection-background-color: #9dced0;
                    selection-color: black;
                    font-family: Terminus;
                    font-size: 9px;
                    padding: 2px;
                    border: 1px solid #050A30;
                    outline: none;
                }
                QComboBox QAbstractItemView::item {
                    padding: 6px 8px;
                    border-bottom: 1px solid #ebebe8;
                    min-height: 18px;
                }
                QComboBox QAbstractItemView::item:hover {
                    background-color: #c8d3da;
                    color: black;
                }
                QComboBox QAbstractItemView::item:selected {
                    background-color: #9dced0;
                    color: black;
                }
            """)
            form_layout.addRow("Manager:", manager_combo)

            # Arguments input
            args_input = QLineEdit(str(macro_config.get('args', '')))
            args_input.setPlaceholderText("e.g., -only manual_inn -force -y")
            args_input.setStyleSheet("padding: 3px; font-family: Terminus; font-size: 9px;")
            form_layout.addRow("Arguments:", args_input)

            # Description input
            desc_input = QLineEdit(str(macro_config.get('description', '')))
            desc_input.setPlaceholderText("Brief description of the macro")
            desc_input.setStyleSheet("padding: 3px; font-family: Terminus; font-size: 9px;")
            form_layout.addRow("Description:", desc_input)

            # Buttons layout
            buttons_layout = QHBoxLayout()

            # Copy button
            copy_btn = QPushButton("Copy")
            copy_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {TEAL};
                    color: black;
                    border: 1px solid {MIDNIGHT};
                    border-radius: 3px;
                    padding: 3px;
                    font-family: Terminus;
                    font-size: 9px;
                    max-width: 60px;
                }}
            """)
            copy_btn.macro_name = macro_name
            copy_btn.macro_widget = group
            copy_btn.clicked.connect(self.handle_copy_macro)
            buttons_layout.addWidget(copy_btn)

            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {CRIMSON};
                    color: white;
                    border: 1px solid {MIDNIGHT};
                    border-radius: 3px;
                    padding: 3px;
                    font-family: Terminus;
                    font-size: 9px;
                    max-width: 60px;
                }}
            """)
            delete_btn.macro_name = macro_name
            delete_btn.macro_widget = group
            delete_btn.clicked.connect(self.handle_delete_macro)
            buttons_layout.addWidget(delete_btn)

            # Create a widget to hold the buttons
            buttons_widget = QWidget()
            buttons_widget.setLayout(buttons_layout)
            form_layout.addRow("", buttons_widget)

            # Store references to inputs
            group.name_input = name_input
            group.hotkey_input = hotkey_input
            group.manager_combo = manager_combo
            group.args_input = args_input
            group.desc_input = desc_input

            return group

        except Exception as e:
            print(f"Error creating macro widget: {e}")
            import traceback
            traceback.print_exc()
            # Return a simple placeholder widget if there's an error
            placeholder = QLabel(f"Error creating macro widget: {str(e)}")
            return placeholder

    def handle_copy_macro(self):
        """Handle copy button click for macro widgets"""
        try:
            sender = self.sender()  # Get the button that was clicked
            if hasattr(sender, 'macro_name') and hasattr(sender, 'macro_widget'):
                self.copy_macro(sender.macro_name, sender.macro_widget)
        except Exception as e:
            print(f"Error handling copy macro: {e}")

    def copy_macro(self, macro_name, widget):
        """Copy an existing macro configuration"""
        try:
            # Get the current configuration from the widget
            if not hasattr(widget, 'name_input'):
                return

            # Extract current values (copy everything except name)
            current_hotkey = widget.hotkey_input.text().strip()
            current_manager = widget.manager_combo.currentText()
            current_args = widget.args_input.text().strip()
            current_desc = widget.desc_input.text().strip()

            # Create a new macro name
            new_macro_name = self.generate_unique_macro_name("new_macro")

            # Create new macro config (copy everything including hotkey)
            new_macro_config = {
                'hotkey': current_hotkey,  # Copy hotkey as well
                'manager': current_manager,
                'args': current_args,
                'description': current_desc
            }

            # Add the new macro
            self.add_macro(new_macro_name, new_macro_config)

            print(f"Created copy of macro '{macro_name}' as '{new_macro_name}'")

        except Exception as e:
            print(f"Error copying macro: {e}")
            import traceback
            traceback.print_exc()

    def generate_unique_macro_name(self, base_name):
        """Generate a unique macro name by appending a number"""
        if not base_name:
            base_name = "new_macro"

        # Check if base_name already exists
        if base_name not in self.macro_widgets:
            return base_name

        # Find a unique name
        counter = 1
        while True:
            new_name = f"{base_name}_{counter}"
            if new_name not in self.macro_widgets:
                return new_name
            counter += 1

    def handle_delete_macro(self):
        """Handle delete button click for macro widgets"""
        try:
            sender = self.sender()  # Get the button that was clicked
            if hasattr(sender, 'macro_name') and hasattr(sender, 'macro_widget'):
                self.delete_macro(sender.macro_name, sender.macro_widget)
        except Exception as e:
            print(f"Error handling delete macro: {e}")

    def delete_macro(self, macro_name, widget):
        """Delete a macro configuration"""
        try:
            # Find and remove the widget from our tracking dictionary
            key_to_remove = None

            for key, stored_widget in list(self.macro_widgets.items()):
                if stored_widget == widget:
                    key_to_remove = key
                    break

            # Remove from tracking first
            if key_to_remove:
                del self.macro_widgets[key_to_remove]
                print(f"Removed macro '{key_to_remove}' from tracking")

            # Remove from layout
            if widget and hasattr(widget, 'parent') and widget.parent():
                self.scroll_layout.removeWidget(widget)

            # Schedule widget for deletion
            if widget:
                widget.deleteLater()

            # Process events to ensure cleanup happens
            QApplication.processEvents()

        except Exception as e:
            print(f"Error deleting macro: {e}")
            import traceback
            traceback.print_exc()

    def load_macros(self, macros):
        """Load macro configurations into the UI"""
        try:
            # Clear existing macros more thoroughly
            for key, widget in list(self.macro_widgets.items()):
                try:
                    if widget:
                        self.scroll_layout.removeWidget(widget)
                        widget.deleteLater()
                except RuntimeError:
                    # Widget already deleted
                    pass

            # Clear the tracking dictionary
            self.macro_widgets.clear()

            # Process events to ensure all widgets are properly deleted
            QApplication.processEvents()

            # Small delay to ensure cleanup is complete
            QTimer.singleShot(50, lambda: self._load_macros_delayed(macros))

        except Exception as e:
            print(f"Error loading macros: {e}")
            import traceback
            traceback.print_exc()

    def _load_macros_delayed(self, macros):
        """Load macros after a short delay to ensure cleanup is complete"""
        try:
            # Load new macros
            for macro_name, macro_config in macros.items():
                self.add_macro(macro_name, macro_config)
        except Exception as e:
            print(f"Error in delayed macro loading: {e}")
            import traceback
            traceback.print_exc()

    def get_macro_configs(self):
        """Get all macro configurations"""
        macros = {}
        try:
            # Create a copy of the items to avoid modification during iteration
            widgets_copy = list(self.macro_widgets.items())

            for macro_name, widget in widgets_copy:
                # Check if widget is still valid before accessing its attributes
                try:
                    if widget is None or not hasattr(widget, 'name_input'):
                        continue

                    # Check if the widget's children are still alive
                    if (hasattr(widget, 'name_input') and
                        hasattr(widget, 'hotkey_input') and
                        hasattr(widget, 'manager_combo') and
                        hasattr(widget, 'args_input') and
                        hasattr(widget, 'desc_input')):

                        # Additional safety check - try to access text first
                        try:
                            name_text = widget.name_input.text()
                            hotkey_text = widget.hotkey_input.text()
                            manager_text = widget.manager_combo.currentText()
                            args_text = widget.args_input.text()
                            desc_text = widget.desc_input.text()

                            current_name = name_text.strip() or macro_name
                            macros[current_name] = {
                                'hotkey': hotkey_text.strip(),
                                'manager': manager_text,
                                'args': args_text.strip(),
                                'description': desc_text.strip()
                            }
                        except RuntimeError:
                            # Widget has been deleted, skip it and remove from our tracking
                            print(f"Widget for macro '{macro_name}' has been deleted, skipping...")
                            continue

                except (RuntimeError, AttributeError) as e:
                    # Widget has been deleted or is invalid, skip it
                    print(f"Skipping invalid widget for macro '{macro_name}': {e}")
                    continue

        except Exception as e:
            print(f"Error getting macro configs: {e}")
            import traceback
            traceback.print_exc()

        return macros

class HotkeyConfigDialog(QDialog):
    """Enhanced dialog for editing hotkey configurations with macro support"""

    def __init__(self, current_mappings, current_macros, available_managers, parent=None):
        super().__init__(parent)
        self.current_mappings = current_mappings.copy()
        self.current_macros = current_macros.copy()
        self.available_managers = list(available_managers)
        self.hotkey_inputs = {}

        self.setWindowTitle("Edit Hotkeys & Macros")
        self.setModal(True)
        self.resize(500, 600)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {PEWTER};
                color: {MIDNIGHT};
            }}
            QTabWidget::pane {{
                border: 1px solid {MIDNIGHT};
                border-radius: 3px;
            }}
            QTabBar::tab {{
                background-color: {ROYAL_BLUE};
                color: white;
                padding: 5px 10px;
                margin: 2px;
                border-radius: 3px;
                font-family: Terminus;
                font-size: 9px;
            }}
            QTabBar::tab:selected {{
                background-color: {BLUE_GROTTO};
            }}
            QLabel {{
                color: {MIDNIGHT};
                font-family: Terminus;
                font-size: 10px;
            }}
            QLineEdit {{
                background-color: white;
                border: 1px solid {MIDNIGHT};
                border-radius: 3px;
                padding: 5px;
                font-family: Terminus;
                font-size: 9px;
            }}
            QPushButton {{
                background-color: {ROYAL_BLUE};
                border: 1px solid {MIDNIGHT};
                border-radius: 5px;
                color: white;
                font-family: Terminus;
                font-size: 9px;
                padding: 5px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {BLUE_GROTTO};
            }}
            QPushButton:pressed {{
                background-color: {FOREST_GREEN};
            }}
        """)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        title_label = QLabel("Configure Keyboard Shortcuts and Macros")
        title_label.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {ROYAL_BLUE}; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # Create tabbed interface
        self.tab_widget = QTabWidget()

        # Standard hotkeys tab
        hotkey_tab = self.create_hotkey_tab()
        self.tab_widget.addTab(hotkey_tab, "Manager Hotkeys")

        # Macros tab - pass the available managers to MacroTab
        self.macro_tab = MacroTab(self.available_managers)
        self.macro_tab.load_macros(self.current_macros)
        self.tab_widget.addTab(self.macro_tab, "Macro Commands")

        layout.addWidget(self.tab_widget)

        # Buttons
        button_layout = QHBoxLayout()

        test_button = QPushButton("Test")
        test_button.setStyleSheet(f"background-color: {TEAL}; color: black;")
        test_button.clicked.connect(self.test_hotkeys)
        button_layout.addWidget(test_button)

        reset_button = QPushButton("Reset to Defaults")
        reset_button.setStyleSheet(f"background-color: {PURPLE_HAZE}; color: black;")
        reset_button.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_button)

        button_layout.addStretch()

        # Create custom buttons instead of using QDialogButtonBox
        buttons_layout = QHBoxLayout()

        apply_button = QPushButton("Apply")
        apply_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {FOREST_GREEN};
                color: white;
                border: 1px solid {MIDNIGHT};
                border-radius: 5px;
                padding: 8px 15px;
                font-family: Terminus;
                font-size: 10px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {OLIVE};
            }}
        """)
        apply_button.clicked.connect(self.apply_changes)
        buttons_layout.addWidget(apply_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {PURPLE_HAZE};
                color: black;
                border: 1px solid {MIDNIGHT};
                border-radius: 5px;
                padding: 8px 15px;
                font-family: Terminus;
                font-size: 10px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {CRIMSON};
                color: white;
            }}
        """)
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)

        close_button = QPushButton("Close")
        close_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ROYAL_BLUE};
                color: white;
                border: 1px solid {MIDNIGHT};
                border-radius: 5px;
                padding: 8px 15px;
                font-family: Terminus;
                font-size: 10px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {BLUE_GROTTO};
            }}
        """)
        close_button.clicked.connect(self.accept)
        buttons_layout.addWidget(close_button)

        layout.addLayout(button_layout)
        layout.addLayout(buttons_layout)

    def create_hotkey_tab(self):
        """Create the standard hotkey configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        instructions = QLabel("Use formats like: Ctrl+D, Alt+F1, Shift+Ctrl+T")
        instructions.setStyleSheet("color: gray; margin-bottom: 10px;")
        layout.addWidget(instructions)

        form_layout = QFormLayout()

        for manager_name in sorted(self.available_managers):
            input_field = QLineEdit()
            input_field.setText(self.current_mappings.get(manager_name, ''))
            input_field.setPlaceholderText("e.g., Ctrl+D")
            self.hotkey_inputs[manager_name] = input_field

            label = QLabel(f"{manager_name}:")
            form_layout.addRow(label, input_field)

        layout.addLayout(form_layout)
        layout.addStretch()

        return widget

    def test_hotkeys(self):
        """Test if the entered hotkeys are valid"""
        errors = []
        mappings = self.get_hotkey_mappings()
        macros = self.macro_tab.get_macro_configs()

        # Test regular hotkeys
        for manager_name, hotkey in mappings.items():
            if hotkey.strip():
                try:
                    seq = QKeySequence(hotkey)
                    if seq.isEmpty():
                        errors.append(f"{manager_name}: Invalid hotkey format '{hotkey}'")
                except Exception as e:
                    errors.append(f"{manager_name}: Error parsing '{hotkey}' - {str(e)}")

        # Test macro hotkeys
        for macro_name, macro_config in macros.items():
            hotkey = macro_config.get('hotkey', '').strip()
            if hotkey:
                try:
                    seq = QKeySequence(hotkey)
                    if seq.isEmpty():
                        errors.append(f"Macro '{macro_name}': Invalid hotkey format '{hotkey}'")
                except Exception as e:
                    errors.append(f"Macro '{macro_name}': Error parsing '{hotkey}' - {str(e)}")

        # Check for duplicate hotkeys
        all_hotkeys = {}
        for manager_name, hotkey in mappings.items():
            if hotkey.strip():
                if hotkey in all_hotkeys:
                    errors.append(f"Duplicate hotkey '{hotkey}' used for {manager_name} and {all_hotkeys[hotkey]}")
                else:
                    all_hotkeys[hotkey] = manager_name

        for macro_name, macro_config in macros.items():
            hotkey = macro_config.get('hotkey', '').strip()
            if hotkey:
                if hotkey in all_hotkeys:
                    errors.append(f"Duplicate hotkey '{hotkey}' used for macro '{macro_name}' and {all_hotkeys[hotkey]}")
                else:
                    all_hotkeys[hotkey] = f"macro '{macro_name}'"

        if errors:
            QMessageBox.warning(self, "Hotkey Validation", "\n".join(errors))
        else:
            QMessageBox.information(self, "Hotkey Validation", "All hotkeys are valid!")

    def reset_to_defaults(self):
        """Reset all hotkeys to default values"""
        for manager_name, input_field in self.hotkey_inputs.items():
            default_hotkey = DEFAULT_HOTKEYS.get(manager_name, '')
            input_field.setText(default_hotkey)

        # Reset macros to defaults
        self.macro_tab.load_macros(DEFAULT_MACROS)

    def apply_changes(self):
        """Apply changes without closing the dialog"""
        try:
            # Validate first
            errors = []
            mappings = self.get_hotkey_mappings()
            macros = self.macro_tab.get_macro_configs()

            # Validate regular hotkeys
            for manager_name, hotkey in mappings.items():
                if hotkey.strip():
                    try:
                        seq = QKeySequence(hotkey)
                        if seq.isEmpty():
                            errors.append(f"{manager_name}: Invalid hotkey format '{hotkey}'")
                    except Exception:
                        errors.append(f"{manager_name}: Invalid hotkey format '{hotkey}'")

            # Validate macro hotkeys
            for macro_name, macro_config in macros.items():
                hotkey = macro_config.get('hotkey', '').strip()
                if hotkey:
                    try:
                        seq = QKeySequence(hotkey)
                        if seq.isEmpty():
                            errors.append(f"Macro '{macro_name}': Invalid hotkey format '{hotkey}'")
                    except Exception:
                        errors.append(f"Macro '{macro_name}': Invalid hotkey format '{hotkey}'")

            # Check for duplicates
            all_hotkeys = {}
            for manager_name, hotkey in mappings.items():
                if hotkey.strip():
                    if hotkey in all_hotkeys:
                        errors.append(f"Duplicate hotkey '{hotkey}' for {manager_name} and {all_hotkeys[hotkey]}")
                    else:
                        all_hotkeys[hotkey] = manager_name

            for macro_name, macro_config in macros.items():
                hotkey = macro_config.get('hotkey', '').strip()
                if hotkey:
                    if hotkey in all_hotkeys:
                        errors.append(f"Duplicate hotkey '{hotkey}' for macro '{macro_name}' and {all_hotkeys[hotkey]}")
                    else:
                        all_hotkeys[hotkey] = f"macro '{macro_name}'"

            if errors:
                QMessageBox.warning(self, "Validation Errors", "\n".join(errors))
                return

            # If validation passes, apply changes to main application
            if hasattr(self.parent(), 'apply_new_hotkeys_and_macros'):
                self.parent().apply_new_hotkeys_and_macros(mappings, macros)

                # Update the dialog's internal state to reflect applied changes
                self.current_mappings = mappings.copy()
                self.current_macros = macros.copy()

                # Update the hotkey inputs to show the current applied state
                for manager_name, input_field in self.hotkey_inputs.items():
                    current_value = mappings.get(manager_name, '')
                    if input_field.text() != current_value:
                        input_field.setText(current_value)

                # Force refresh the macro tab to show all changes including name updates
                # Get the current macro configs before refresh
                current_macro_configs = self.macro_tab.get_macro_configs()

                # Always reload the macro tab to ensure names and all changes are reflected
                self.macro_tab.load_macros(current_macro_configs)

                QMessageBox.information(self, "Applied", "Changes have been applied successfully!\nThe configuration is now active.")
            else:
                QMessageBox.warning(self, "Error", "Cannot apply changes - parent window not found")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error applying changes: {str(e)}")
            import traceback
            traceback.print_exc()

    def validate_and_accept(self):
        """Validate hotkeys before accepting the dialog (kept for compatibility)"""
        self.apply_changes()
        # Don't close dialog - this method is kept for compatibility but doesn't close

    def get_hotkey_mappings(self):
        """Get the current hotkey mappings from input fields"""
        mappings = {}
        for manager_name, input_field in self.hotkey_inputs.items():
            hotkey = input_field.text().strip()
            if hotkey:
                mappings[manager_name] = hotkey
        return mappings

    def get_macro_configs(self):
        """Get the current macro configurations"""
        return self.macro_tab.get_macro_configs()

# Create a wrapper for the directory tracer that matches the expected interface
class DirectoryTracerWrapper(QWidget):
    """Wrapper to provide the expected interface for the directory tracer"""

    def __init__(self):
        super().__init__()
        # Initialize the config
        self.config = AppConfig()

        # Create the main window (tree manager)
        self.main_window = MainWindow(self.config)

        # Setup layout to contain the main window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.main_window)

    def get_selected_directory(self):
        """Get currently selected directory path"""
        try:
            # Get selected paths from the tree view
            selected_paths = self.main_window.get_selected_paths()
            if selected_paths:
                return str(selected_paths[0])
            else:
                # Return current base directory as fallback
                return str(self.config.paths.base_directory)
        except Exception as e:
            print(f"Error getting selected directory: {e}")
            # Return environment base as fallback
            return os.getenv('casino_prj_base', os.getcwd())

class CasinoGUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.selected_manager = None
        self.current_manager_button = None
        self.hotkey_mappings = self.load_user_hotkeys()
        self.macro_mappings = self.load_user_macros()

        prj_base = os.getenv('casino_prj_base')
        if prj_base:
            try:
                os.chdir(prj_base)
                print(f"Going to {prj_base} : $prj_base\n")
            except Exception as e:
                print(f"Error: Could not change directory to {prj_base}. {str(e)}")
                sys.exit(1)
        else:
            print("Error: prj_base is not set in the environment.")
            sys.exit(1)

        pond_base = os.getenv('casino_pond')
        if not pond_base:
            QMessageBox.critical(self, "Error", "casino_pond environment variable not set.")
            sys.exit(1)

        self.manager_command_histories = {}
        self.setWindowTitle("CA$INO")
        self.setGeometry(100, 100, 1400, 800)
        self.setFont(QFont("Arial", 14))

        self.layout = QVBoxLayout(self)

        title_label = ClickableLabel(self)
        prj_name = os.getenv('casino_prj_name', 'N/A')
        design_ver = os.getenv('casino_design_ver', 'N/A')
        dk_ver = os.getenv('casino_dk_ver', 'N/A')
        tag = os.getenv('casino_tag', 'N/A')

        title_html = f"""
        <div style='text-align: center;'>
            <h1 style='color: {MIDNIGHT}; font-weight: bold; font-size: 14px; margin: 1px;'>CA$INO</h1>
            <div style='color: {MIDNIGHT}; font-size: 10px; font-family: Terminus; margin: 1px;'>
                {prj_name} | {design_ver} | {dk_ver} | {tag}
            </div>
        </div>
        """
        title_label.setText(title_html)
        title_label.setStyleSheet(f"QLabel {{ background-color: {SAGE_GREEN}; border: 2px solid {MIDNIGHT}; border-radius: 5px; padding: 5px; }}")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFixedHeight(75)

        self.layout.addWidget(title_label)

        splitter = QSplitter(Qt.Horizontal)
        left_pane = self.create_button_pane()
        middle_pane = self.create_console_pane()

        # Use the wrapper instead of DirectoryTracerApp
        self.directory_tracer_app = DirectoryTracerWrapper()

        splitter.addWidget(left_pane)
        splitter.addWidget(middle_pane)
        splitter.addWidget(self.directory_tracer_app)
        splitter.setSizes([150, 650, 600])

        self.layout.addWidget(splitter)

        self.input_field.setEnabled(False)
        self.input_field.setFocus()

        self.display_ascii_art()
        self.show_info()

        self.flow_task_names = set()
        self.command_thread = None
        self.active_threads = {}

    def load_user_hotkeys(self):
        """Load user-defined hotkeys from a configuration file or use defaults"""
        config_file = os.path.expanduser("~/.casino_hotkeys.yaml")

        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    if config and 'hotkeys' in config:
                        hotkeys = DEFAULT_HOTKEYS.copy()
                        hotkeys.update(config['hotkeys'])
                        return hotkeys
                    else:
                        # Handle old format
                        hotkeys = DEFAULT_HOTKEYS.copy()
                        if config:
                            hotkeys.update(config)
                        return hotkeys
            else:
                self.save_default_config()
                return DEFAULT_HOTKEYS.copy()
        except Exception as e:
            print(f"Error loading hotkey config: {e}")
            return DEFAULT_HOTKEYS.copy()

    def load_user_macros(self):
        """Load user-defined macros from a configuration file or use defaults"""
        config_file = os.path.expanduser("~/.casino_hotkeys.yaml")

        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    if config and 'macros' in config:
                        return config['macros']
                    else:
                        return DEFAULT_MACROS.copy()
            else:
                return DEFAULT_MACROS.copy()
        except Exception as e:
            print(f"Error loading macro config: {e}")
            return DEFAULT_MACROS.copy()

    def save_default_config(self):
        """Save default configuration for user customization"""
        config_file = os.path.expanduser("~/.casino_hotkeys.yaml")
        try:
            config = {
                'hotkeys': DEFAULT_HOTKEYS,
                'macros': DEFAULT_MACROS
            }

            with open(config_file, 'w') as f:
                f.write("# Configuration for Casino GUI\n")
                f.write("# Available modifiers: Ctrl, Alt, Shift, Meta\n")
                f.write("# Example formats: 'Ctrl+D', 'Alt+F1', 'Shift+Ctrl+T'\n\n")
                yaml.dump(config, f, default_flow_style=False)

            print(f"Default config created at: {config_file}")
        except Exception as e:
            print(f"Error creating default config: {e}")

    def setup_hotkeys(self):
        """Set up keyboard shortcuts for manager buttons and macros"""
        # Clear existing shortcuts
        if hasattr(self, 'shortcuts'):
            for shortcut in self.shortcuts.values():
                shortcut.setEnabled(False)
                shortcut.deleteLater()

        if hasattr(self, 'macro_shortcuts'):
            for shortcut in self.macro_shortcuts.values():
                shortcut.setEnabled(False)
                shortcut.deleteLater()

        self.shortcuts = {}
        self.macro_shortcuts = {}

        # Setup manager hotkeys
        for manager_name, button in self.manager_buttons.items():
            if manager_name in self.hotkey_mappings:
                hotkey = self.hotkey_mappings[manager_name]
                try:
                    shortcut = QShortcut(QKeySequence(hotkey), self)
                    shortcut.activated.connect(lambda checked=False, btn=button: btn.click())
                    self.shortcuts[manager_name] = shortcut
                except Exception as e:
                    print(f"Error setting up hotkey {hotkey} for {manager_name}: {e}")

        # Setup macro hotkeys
        for macro_name, macro_config in self.macro_mappings.items():
            hotkey = macro_config.get('hotkey', '').strip()
            if hotkey:
                try:
                    shortcut = QShortcut(QKeySequence(hotkey), self)
                    shortcut.activated.connect(lambda checked=False, name=macro_name, config=macro_config:
                                             self.execute_macro(name, config))
                    self.macro_shortcuts[macro_name] = shortcut
                except Exception as e:
                    print(f"Error setting up macro hotkey {hotkey} for {macro_name}: {e}")


    def clean_manager_state(self):
        """Clean up previous manager state before executing new command"""
        try:
            # Terminate any running command threads
            if hasattr(self, 'command_thread') and self.command_thread and self.command_thread.isRunning():
                self.console_output.insertHtml(f"<span style='color: orange;'>[CLEANUP] Terminating previous process...</span><br>")
                self.command_thread.terminate()
                self.command_thread.wait(2000)
                if self.command_thread.isRunning():
                    self.console_output.insertHtml(f"<span style='color: red;'>[WARNING] Previous process did not terminate cleanly</span><br>")

            # Clear any active threads for all managers
            if hasattr(self, 'active_threads'):
                for manager_name, threads in list(self.active_threads.items()):
                    for thread in threads:
                        if thread.isRunning():
                            thread.terminate()
                            thread.wait(1000)
                    self.active_threads[manager_name] = []

            # Reset selected manager state
            if hasattr(self, 'selected_manager') and self.selected_manager and self.selected_manager[2]:
                self.reset_single_button_color(self.selected_manager[2])

            self.selected_manager = None
            self.waiting_for_arguments = False

            # Clear input field
            self.input_field.clear()
            self.input_field.setEnabled(False)

            # Go back to base directory
            prj_base = os.getenv('casino_prj_base')
            if prj_base:
                os.chdir(prj_base)
                self.console_output.insertHtml(f"<span style='color: blue;'>[RESET] Returned to base directory: {prj_base}</span><br>")

            self.console_output.insertHtml(f"<span style='color: green;'>[READY] Environment cleaned for macro execution</span><br>")

        except Exception as e:
            self.console_output.insertHtml(f"<span style='color: red;'>[ERROR] Cleanup failed: {str(e)}</span><br>")
            import traceback
            traceback.print_exc()

    def execute_macro(self, macro_name, macro_config):
        """Execute a predefined macro command"""
        manager = macro_config.get('manager', 'flow_mgr')
        args = macro_config.get('args', '')
        description = macro_config.get('description', '')

        # Clean previous manager state before executing macro
        self.clean_manager_state()

        # Display macro execution info
        self.console_output.insertHtml(f"<br><span style='color: purple;'>[MACRO] Executing '{macro_name}': {description}</span><br>")
        self.console_output.insertHtml(f"<span style='color: blue;'>Command: {manager} {args}</span><br>")

        # Get manager path
        manager_key = f"casino_{manager}_py"
        manager_path = os.getenv(manager_key)

        if not manager_path or not os.path.exists(manager_path):
            self.console_output.insertHtml(f"<span style='color: red;'>Error: Manager '{manager}' not found</span><br>")
            return

        # Select the manager (this will handle directory changes and setup)
        if manager in self.manager_buttons:
            self.select_manager_for_macro(manager, manager_path, self.manager_buttons[manager])

        # Execute with arguments
        self.execute_manager(manager_path, args)

        # Enable input field and set focus for additional user input
        self.input_field.setEnabled(True)
        self.input_field.setFocus()
        self.console_output.ensureCursorVisible()

    def select_manager_for_macro(self, manager_name, manager_path, button):
        """Select manager for macro execution (simplified version of select_manager)"""
        if self.selected_manager and self.selected_manager[2]:
            self.reset_single_button_color(self.selected_manager[2])

        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {PURPLE_HAZE};
                border: 1px solid {MIDNIGHT};
                border-radius: 5px;
                color: black;
                font-weight: bold;
                padding: 5px;
                text-align: center;
            }}
        """)

        self.selected_manager = (manager_name, manager_path, button)
        self.input_field.set_current_manager(manager_name)

        # Handle directory changes based on manager type
        if manager_name == 'flow_mgr':
            selected_directory = self.directory_tracer_app.get_selected_directory()
            if selected_directory:
                os.chdir(selected_directory)
                self.console_output.insertHtml(f"<span style='color: purple;'>[GO TO] {selected_directory}</span><br>")
                self.collect_flow_task_names(selected_directory)
        elif manager_name == 'timer':
            selected_directory = self.directory_tracer_app.get_selected_directory()
            if selected_directory:
                os.chdir(selected_directory)
                self.console_output.insertHtml(f"<span style='color: purple;'>[GO TO] {selected_directory}</span><br>")
        else:
            prj_base = os.getenv('casino_prj_base')
            if prj_base:
                os.chdir(prj_base)
                self.console_output.insertHtml(f"<span style='color: purple;'>[GO TO] {prj_base}</span><br>")

    def create_button_pane(self):
        """Create the left pane containing only buttons in vertical layout"""
        button_pane = QWidget()
        button_pane.setFixedWidth(150)
        button_pane.setStyleSheet(f"background-color: {PEWTER}; border: 1px solid {MIDNIGHT};")

        button_layout = QVBoxLayout(button_pane)
        button_layout.setSpacing(5)
        button_layout.setContentsMargins(10, 10, 10, 10)

        self.create_manager_buttons_vertical(button_layout)
        return button_pane

    def create_console_pane(self):
        """Create the middle pane containing console and input field"""
        console_pane = QWidget()
        console_layout = QVBoxLayout(console_pane)

        self.console_output = QTextEdit(self)
        self.console_output.setReadOnly(True)
        self.console_output.setFont(QFont("Terminus", 8))
        console_layout.addWidget(self.console_output)

        self.input_box_layout = QHBoxLayout()
        self.input_label = QLabel("Command-line args / User Input:")
        self.input_label.setFont(QFont("Terminus", 8))
        self.input_box_layout.addWidget(self.input_label)

        self.input_field = InputField(self)
        self.input_field.setFont(QFont("Terminus", 8))
        self.input_field.returnPressed.connect(self.send_user_input)
        self.input_box_layout.addWidget(self.input_field)

        console_layout.addLayout(self.input_box_layout)
        return console_pane

    def create_manager_buttons_vertical(self, layout):
        """Create buttons for managers in vertical layout"""
        scripts = {
            re.sub(r"^casino_|_py$", "", key): value
            for key, value in os.environ.items()
            if key.endswith('_py')
        }

        if not scripts:
            QMessageBox.warning(self, "Error", "No Python scripts found in the environment.")
            return

        self.manager_buttons = {}

        for manager_name, manager_path in scripts.items():
            button = QPushButton(manager_name, self)
            button.setFont(QFont("Terminus", 10))
            button.setFixedHeight(30)
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ROYAL_BLUE};
                    border: 1px solid {MIDNIGHT};
                    border-radius: 5px;
                    color: white;
                    font-weight: ;
                    padding: 5px;
                }}
                QPushButton:hover {{
                    background-color: {BLUE_GROTTO};
                }}
                QPushButton:pressed {{
                    background-color: {FOREST_GREEN};
                }}
            """)
            button.clicked.connect(lambda checked, path=manager_path, name=manager_name, btn=button:
                                 self.select_manager(name, path, btn))
            layout.addWidget(button)
            self.manager_buttons[manager_name] = button

        self.setup_hotkeys()
        layout.addStretch()

        config_button = QPushButton("Edit Hotkeys", self)
        config_button.setFont(QFont("Terminus", 9))
        config_button.setFixedHeight(30)
        config_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {FOREST_GREEN};
                border: 1px solid {MIDNIGHT};
                border-radius: 5px;
                color: white;
                font-weight: ;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {OLIVE};
            }}
        """)
        config_button.clicked.connect(self.open_hotkey_config)
        layout.addWidget(config_button)

        quit_button = QPushButton("Quit", self)
        quit_button.setFont(QFont("Terminus", 10))
        quit_button.setFixedHeight(30)
        quit_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {PURPLE_HAZE};
                border: 1px solid {MIDNIGHT};
                border-radius: 5px;
                color: black;
                font-weight: ;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {CRIMSON};
                color: white;
            }}
        """)
        quit_button.clicked.connect(self.close)
        layout.addWidget(quit_button)

        quit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        quit_shortcut.activated.connect(self.close)

    def open_hotkey_config(self):
        """Open the hotkey configuration dialog with macro support"""
        # Get available managers dynamically from environment
        available_managers = []
        scripts = {
            re.sub(r"^casino_|_py$", "", key): value
            for key, value in os.environ.items()
            if key.endswith('_py')
        }
        available_managers = list(scripts.keys())

        dialog = HotkeyConfigDialog(self.hotkey_mappings, self.macro_mappings, available_managers, self)
        if dialog.exec_() == QDialog.Accepted:
            new_mappings = dialog.get_hotkey_mappings()
            new_macros = dialog.get_macro_configs()
            self.apply_new_hotkeys_and_macros(new_mappings, new_macros)

    def apply_new_hotkeys_and_macros(self, new_mappings, new_macros):
        """Apply new hotkey mappings and macro configurations"""
        try:
            # Disable old shortcuts
            for shortcut in getattr(self, 'shortcuts', {}).values():
                shortcut.setEnabled(False)
                shortcut.deleteLater()
            for shortcut in getattr(self, 'macro_shortcuts', {}).values():
                shortcut.setEnabled(False)
                shortcut.deleteLater()

            old_mappings = self.hotkey_mappings.copy()
            old_macros = self.macro_mappings.copy()

            self.hotkey_mappings = new_mappings
            self.macro_mappings = new_macros
            self.setup_hotkeys()

            # Save to config file
            config_file = os.path.expanduser("~/.casino_hotkeys.yaml")
            config = {
                'hotkeys': new_mappings,
                'macros': new_macros
            }

            with open(config_file, 'w') as f:
                f.write("# Configuration for Casino GUI\n")
                f.write("# Available modifiers: Ctrl, Alt, Shift, Meta\n")
                f.write("# Example formats: 'Ctrl+D', 'Alt+F1', 'Shift+Ctrl+T'\n\n")
                yaml.dump(config, f, default_flow_style=False)

            # Show changes
            changes_found = False

            # Check hotkey changes
            for manager_name in set(old_mappings.keys()) | set(new_mappings.keys()):
                old_key = old_mappings.get(manager_name, 'Not set')
                new_key = new_mappings.get(manager_name, 'Not set')

                if old_key != new_key:
                    if not changes_found:
                        self.console_output.insertHtml("<br><span style='color: blue;'>[CONFIG] Applied new configuration:</span><br>")
                        changes_found = True
                    self.console_output.insertHtml(f"<span style='color: gray;'>{manager_name}: {old_key} -> {new_key}</span><br>")

            # Check macro changes
            for macro_name in set(old_macros.keys()) | set(new_macros.keys()):
                old_macro = old_macros.get(macro_name, {})
                new_macro = new_macros.get(macro_name, {})
                old_key = old_macro.get('hotkey', 'Not set')
                new_key = new_macro.get('hotkey', 'Not set')

                if old_key != new_key or old_macro.get('args') != new_macro.get('args'):
                    if not changes_found:
                        self.console_output.insertHtml("<br><span style='color: blue;'>[CONFIG] Applied new configuration:</span><br>")
                        changes_found = True
                    self.console_output.insertHtml(f"<span style='color: gray;'>Macro '{macro_name}': {old_key} -> {new_key}</span><br>")

            if not changes_found:
                self.console_output.insertHtml("<br><span style='color: blue;'>[CONFIG] No changes made.</span><br>")
            else:
                self.console_output.insertHtml("<span style='color: green;'>Configuration applied successfully!</span><br>")

        except Exception as e:
            self.console_output.insertHtml(f"<br><span style='color: red;'>Error applying configuration: {str(e)}</span><br>")

        self.console_output.ensureCursorVisible()

    def go_back_to_base_dir(self):
        prj_base = os.getenv('casino_prj_base')
        if prj_base:
            os.chdir(prj_base)
            self.console_output.insertHtml(f"<br><span style='color: blue;'>[BACK TO] {prj_base}. </span><br>")
        else:
            self.console_output.insertHtml(f"<br><span style='color: red;'>prj_base not set.</span><br>")


    def display_ascii_art(self):
        """Display ASCII art in light green color in the console output with a moving effect."""
        self.ascii_art_lines = [
            #"\n\n ====================================================================",
            "\n\n ",
            "   .d$$$$b.        d$$$$      $$     $$$$$$$ $$$b    $$$  .d$$$$$b.       -TM-",
            "  d$$P  Y$$b      d$$$$$  .d$$$$$b.    $$$   $$$$b   $$$ d$$P\" \"Y$$b ",
            "  $$$    $$$     d$$P$$$ d$$P $$\"$$b   $$$   $$$$$b  $$$ $$$     $$$ ",
            "  $$$           d$$P $$$ Y$$b.$$       $$$   $$$Y$$b $$$ $$$     $$$ ",
            "  $$$          d$$P  $$$  \"Y$$$$$b.    $$$   $$$ Y$$b$$$ $$$     $$$ ",
            "  $$$    $$$  d$$P   $$$      $$\"$$b   $$$   $$$  Y$$$$$ $$$     $$$ ",
            "  Y$$b  d$$P d$$$$$$$$$$ Y$$b $$.$$P   $$$   $$$   Y$$$$ Y$$b. .d$$P ",
            "   \"Y$$$$P\" d$$P     $$$  \"Y$$$$$P\"  $$$$$$$ $$$    Y$$$  \"Y$$$$$P\"  ",
            "                              $$                                    ",
            #" ====================================================================\n"
            "\n\n"
        ]

        self.current_line_index = 0  # To track which line is being displayed
        self.console_output.clear()  # Clear the console output before displaying the ASCII art

        # Use a QTimer to create a delay between displaying each line
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ascii_art)
        self.timer.start(50)  # Adjust the delay in milliseconds (200ms for a slower movement)


    def update_ascii_art(self):
        """Display the next line of ASCII art with a delay."""
        if self.current_line_index < len(self.ascii_art_lines):
            line = self.ascii_art_lines[self.current_line_index]
            ascii_html = f"<span style='color: black;'>{line.replace(' ', '&nbsp;')}</span><br>"
            self.console_output.insertHtml(ascii_html)
            self.console_output.ensureCursorVisible()
            self.current_line_index += 1
        else:
            self.timer.stop()

    def reset_manager_button_colors(self):
        """Reset the color of all manager buttons to default."""
        for manager_name, button in self.manager_buttons.items():
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ROYAL_BLUE};
                    border: 1px solid {MIDNIGHT};
                    border-radius: 5px;
                    color: white;
                    font-weight: ;
                    padding: 5px;
                    text-align: center;
                }}
                QPushButton:hover {{
                    background-color: {BLUE_GROTTO};
                }}
                QPushButton:pressed {{
                    background-color: {FOREST_GREEN};
                }}
            """)

    def show_info(self):
        """Display environment variables in a PrettyTable format when the title button is clicked."""
        selected_vars = ["casino_prj_name", "casino_design_ver", "casino_dk_ver", "casino_tag", "casino_prj_base", "casino_pond"]

        table = PrettyTable()
        table.field_names = ["Variable", "Value"]
        table.align["Variable"] = "l"
        table.align["Value"] = "l"

        for var in selected_vars:
            value = os.getenv(var, "Not set")
            table.add_row([var, value])

        prj_base = os.getenv('casino_prj_base')
        self.console_output.insertHtml("<span style='color: black;'>\n- Environment Information:</span><br>")
        self.console_output.insertHtml(f"<span style='color: black;'>{table.get_string().replace(' ', '&nbsp;').replace('\n', '<br>')}</span><br>")
        self.console_output.insertHtml(f"<span style='color: blue;'>- Going to {prj_base}</span><br><br>")
        self.console_output.ensureCursorVisible()

    def keyPressEvent(self, event):
        """Handle global key press events"""
        if event.key() == Qt.Key_H and event.modifiers() == Qt.ControlModifier:
            self.display_hotkey_help()
            return

        super().keyPressEvent(event)

    def display_hotkey_help(self):
        """Display available hotkeys and macros in console"""
        self.console_output.insertHtml("<br><span style='color: blue;'>[HOTKEYS] Available keyboard shortcuts:</span><br>")

        # Manager hotkeys table
        table = PrettyTable()
        table.field_names = ["Hotkey", "Manager"]
        table.align = "l"

        for manager_name, hotkey in self.hotkey_mappings.items():
            if manager_name in self.manager_buttons:
                table.add_row([hotkey, manager_name])

        table.add_row(["Ctrl+Q", "Quit"])
        table.add_row(["Ctrl+H", "Show this help"])

        self.console_output.insertPlainText(str(table) + "\n")

        # Macro shortcuts table
        if self.macro_mappings:
            self.console_output.insertHtml("<br><span style='color: purple;'>[MACROS] Available macro shortcuts:</span><br>")

            macro_table = PrettyTable()
            macro_table.field_names = ["Hotkey", "Macro", "Description"]
            macro_table.align = "l"

            for macro_name, macro_config in self.macro_mappings.items():
                hotkey = macro_config.get('hotkey', 'Not set')
                description = macro_config.get('description', 'No description')
                macro_table.add_row([hotkey, macro_name, description])

            self.console_output.insertPlainText(str(macro_table) + "\n")

        self.console_output.insertHtml(f"<span style='color: gray;'>Config file: ~/.casino_hotkeys.yaml</span><br>")
        self.console_output.ensureCursorVisible()

    def select_manager(self, manager_name, manager_path, button):
        if self.selected_manager and self.selected_manager[2]:
            self.reset_single_button_color(self.selected_manager[2])

        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {BLUE_GROTTO};
                border: 1px solid {MIDNIGHT};
                border-radius: 5px;
                color: yellow;
                font-weight: ;
                padding: 5px;
                text-align: center;
            }}
        """)

        self.selected_manager = (manager_name, manager_path, button)
        self.input_field.set_current_manager(manager_name)
        self.input_field.setEnabled(True)
        self.waiting_for_arguments = False

        self.console_output.insertHtml(f"<br><span style='color: blue;'>[BEGIN] Selected {manager_name}. </span><br>")

        if manager_name == 'dk_mgr':
            self.console_output.insertHtml(DK_MGR_HELP)
            self.waiting_for_arguments = True

        elif manager_name == 'flow_mgr':
            self.console_output.insertHtml(FLOW_MGR_HELP)
            selected_directory = self.directory_tracer_app.get_selected_directory()
            if selected_directory:
                os.chdir(selected_directory)
                self.console_output.insertHtml(f"<br><span style='color: purple;'>[GO TO] {selected_directory}. </span><br>")
                self.collect_flow_task_names(selected_directory)
            self.waiting_for_arguments = True

        elif manager_name == 'timer':
            selected_directory = self.directory_tracer_app.get_selected_directory()
            if selected_directory:
                os.chdir(selected_directory)
                self.console_output.insertHtml(f"<br><span style='color: purple;'>[GO TO] {selected_directory}. </span><br>")
                timer_script = os.path.join(os.getenv('casino_pond', ''), 'timer_casino.py')
                if os.path.exists(timer_script):
                    self.execute_manager(timer_script)
                else:
                    self.console_output.insertHtml("<br><span style='color: red;'>Error: timer_casino.py not found in casino_pond directory.</span><br>")
            else:
                self.console_output.insertHtml("<br><span style='color: red;'>Error: No directory selected.</span><br>")

        else:
            prj_base = os.getenv('casino_prj_base')
            if prj_base:
                os.chdir(prj_base)
                self.console_output.insertHtml(f"<br><span style='color: purple;'>[GO TO] {prj_base}. </span><br>")
            else:
                self.console_output.insertHtml(f"<br><span style='color: red;'>prj_base not set.</span><br>")

            self.execute_manager(manager_path)

        self.console_output.ensureCursorVisible()
        self.input_field.setFocus()

    def reset_single_button_color(self, button):
        """Reset a single button to default color"""
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ROYAL_BLUE};
                border: 1px solid {MIDNIGHT};
                border-radius: 5px;
                color: white;
                font-weight: ;
                padding: 5px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {BLUE_GROTTO};
            }}
            QPushButton:pressed {{
                background-color: {FOREST_GREEN};
            }}
        """)

    def execute_manager(self, manager_path, command_args=""):
        """Execute a manager with optional command arguments"""
        python_path = sys.executable
        full_command = f'"{python_path}" "{manager_path}" {command_args}'

        self.console_output.insertPlainText(f"\nExecuting: {full_command}\n")

        if 'flow_mgr' in manager_path or 'fm_casino' in manager_path:
            self.check_x11_environment()

        self.scroll_to_bottom()

        self.command_thread = CommandExecutionThread(full_command, self.selected_manager[0])
        self.command_thread.output_signal.connect(self.update_console_output)
        self.command_thread.error_signal.connect(self.handle_execution_error)
        self.command_thread.task_done_signal.connect(self.notify_task_done)
        self.command_thread.start()

        if self.selected_manager[0] not in self.active_threads:
            self.active_threads[self.selected_manager[0]] = []
        self.active_threads[self.selected_manager[0]].append(self.command_thread)

    def check_x11_environment(self):
        """Check and display X11 environment information for debugging"""
        self.console_output.insertPlainText("\n=== X11 Environment Check ===\n")

        display = os.environ.get('DISPLAY', 'Not set')
        self.console_output.insertPlainText(f"DISPLAY: {display}\n")

        xauthority = os.environ.get('XAUTHORITY', 'Not set')
        self.console_output.insertPlainText(f"XAUTHORITY: {xauthority}\n")

        xdg_runtime = os.environ.get('XDG_RUNTIME_DIR', 'Not set')
        self.console_output.insertPlainText(f"XDG_RUNTIME_DIR: {xdg_runtime}\n")

        try:
            result = subprocess.run(['which', 'xterm'], capture_output=True, text=True)
            if result.returncode == 0:
                self.console_output.insertPlainText(f"xterm found at: {result.stdout.strip()}\n")
            else:
                self.console_output.insertPlainText("xterm not found in PATH\n")
        except Exception as e:
            self.console_output.insertPlainText(f"Error checking xterm: {e}\n")

        self.console_output.insertPlainText("=============================\n")

    def send_user_input(self):
        user_input = self.input_field.text().strip()

        if user_input:
            self.console_output.insertPlainText(f"> {user_input}\n")
            self.scroll_to_bottom()

            if self.selected_manager:
                manager_name = self.selected_manager[0]
                if manager_name not in self.manager_command_histories:
                    self.manager_command_histories[manager_name] = []

                if user_input not in self.manager_command_histories[manager_name]:
                    self.manager_command_histories[manager_name].append(user_input)

                self.input_field.add_to_history(user_input)

            if hasattr(self, 'waiting_for_arguments') and self.waiting_for_arguments:
                self.execute_manager(self.selected_manager[1], user_input)
                self.waiting_for_arguments = False
            else:
                if self.command_thread and self.command_thread.isRunning():
                    self.command_thread.send_input(user_input)
                else:
                    self.console_output.insertPlainText("\nNo process is currently running to receive input.\n")
                    self.scroll_to_bottom()

            self.input_field.clear()
        else:
            QMessageBox.warning(self, "Error", "Input is empty!")

    def update_console_output(self, text):
        self.console_output.insertPlainText(text)
        self.scroll_to_bottom()
        self.input_field.setFocus()

    def handle_execution_error(self, error_message):
        self.console_output.insertPlainText(error_message)

        if "return code 2" in error_message:
            self.console_output.insertPlainText("\nInvalid arguments. Please provide the correct arguments for execution.\n")
            self.waiting_for_arguments = True

        self.scroll_to_bottom()
        self.input_field.setFocus()

    def notify_task_done(self, manager_name):
        self.console_output.insertHtml(f"<br><span style='color: green;'>[END] Completed {manager_name}. </span><br>")
        self.scroll_to_bottom()

        if manager_name in self.active_threads:
            self.active_threads[manager_name] = [t for t in self.active_threads[manager_name] if t.isRunning()]

        button = self.manager_buttons.get(manager_name)
        if button:
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ROYAL_BLUE};
                    border: 1px solid {MIDNIGHT};
                    border-radius: 5px;
                    color: white;
                    font-weight: ;
                    padding: 5px;
                    text-align: center;
                }}
                QPushButton:hover {{
                    background-color: {BLUE_GROTTO};
                }}
                QPushButton:pressed {{
                    background-color: {FOREST_GREEN};
                }}
            """)

    def scroll_to_bottom(self):
        self.console_output.moveCursor(self.console_output.textCursor().End)
        self.console_output.ensureCursorVisible()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.input_field.setFocus()

    def collect_flow_task_names(self, directory):
        """Collect task names from flow_casino.yaml files and display in a table"""
        self.flow_task_names.clear()
        self.flow_task_order = []

        current_flow = os.path.join(directory, 'common', 'flow', 'flow_casino.yaml')
        if os.path.exists(current_flow):
            self.parse_flow_yaml(current_flow)

        parent_flow = os.path.join(os.path.dirname(directory), 'common', 'flow', 'flow_casino.yaml')
        if os.path.exists(parent_flow):
            self.parse_flow_yaml(parent_flow)

        if self.flow_task_names:
            table = PrettyTable()
            table.field_names = ["Available Tasks"]
            table.align["Available Tasks"] = "l"

            for task in self.flow_task_order:
                table.add_row([task])

            self.console_output.insertHtml(f"<br><span style='color: green;'>Found {len(self.flow_task_names)} tasks for auto-completion:</span><br>")
            self.console_output.insertPlainText(str(table) + "\n")
            self.scroll_to_bottom()

    def parse_flow_yaml(self, yaml_file):
        """Parse flow_casino.yaml and extract task names"""
        try:
            with open(yaml_file, 'r') as f:
                flow_data = yaml.safe_load(f)
                if isinstance(flow_data, dict):
                    self.extract_task_names(flow_data)
        except Exception as e:
            self.console_output.insertHtml(f"<br><span style='color: red;'>Error parsing {yaml_file}: {str(e)}</span><br>")

    def extract_task_names(self, data):
        """Recursively extract task names from YAML data"""
        if isinstance(data, dict):
            if 'name' in data:
                task_name = data['name']
                self.flow_task_names.add(task_name)
                self.flow_task_order.append(task_name)
            for value in data.values():
                self.extract_task_names(value)
        elif isinstance(data, list):
            for item in data:
                self.extract_task_names(item)

    def closeEvent(self, event):
        """Handle window close event"""
        for manager_name, threads in self.active_threads.items():
            for thread in threads:
                if thread.isRunning():
                    thread.terminate()
                    thread.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication([])
    window = CasinoGUI()
    window.show()
    sys.exit(app.exec_())
