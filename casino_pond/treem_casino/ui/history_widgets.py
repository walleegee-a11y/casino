"""
Complete history navigation UI components with Go button and terminal operation styling.
"""

import getpass
from pathlib import Path
from typing import List, Optional
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QMenu, QAction,
    QDialog, QListWidget, QListWidgetItem, QSplitter, QTextEdit, QDialogButtonBox,
    QMessageBox, QMainWindow  # ADD THIS
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QColor

from ..config.settings import AppConfig
from ..services.history_service import DirectoryHistoryService, HistoryEntry


class HistoryNavigationWidget(QWidget):
    """Widget for back/forward navigation with Go button."""

    # Signals
    navigate_requested = pyqtSignal(Path)

    def __init__(self, config: AppConfig, history_service: DirectoryHistoryService, parent=None):
        super().__init__(parent)
        self.config = config
        self.history_service = history_service
        self.setup_ui()
        self.setup_connections()

        # Initialize button states immediately
        self.update_button_states()

    def setup_ui(self):
        """Setup the navigation UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Back button with dropdown
        self.back_button = QPushButton("< Back")
        self.back_button.setFont(QFont(*self.config.fonts.get_font_tuple()))
        self.back_button.setStyleSheet("background-color: #7B7B7B; padding: 2px 6px; color: black;")
        self.back_button.setFixedWidth(100)
        self.back_button.setEnabled(False)

        # Forward button
        self.forward_button = QPushButton("Forward >")
        self.forward_button.setFont(QFont(*self.config.fonts.get_font_tuple()))
        self.forward_button.setStyleSheet("background-color: #7B7B7B; padding: 2px 6px; color: black;")
        self.forward_button.setFixedWidth(100)
        self.forward_button.setEnabled(False)

        # Current location label
        self.current_label = QLabel("Current: /")
        self.current_label.setFont(QFont(*self.config.fonts.get_font_tuple(8)))
        self.current_label.setStyleSheet("color: #31352e;")
        self.current_label.setWordWrap(True)

        # History button
        self.history_button = QPushButton("History")
        self.history_button.setFont(QFont(*self.config.fonts.get_font_tuple()))
        self.history_button.setStyleSheet("background-color: #7B7B7B; padding: 2px 6px; color: black;")
        self.history_button.setFixedWidth(70)

        layout.addWidget(self.back_button)
        layout.addWidget(self.forward_button)
        layout.addWidget(self.current_label, stretch=1)
        layout.addWidget(self.history_button)

    def setup_connections(self):
        """Setup signal connections."""
        # Button clicks
        self.back_button.clicked.connect(self.go_back)
        self.forward_button.clicked.connect(self.go_forward)
        self.history_button.clicked.connect(self.show_history_dialog)

        # Context menus for dropdown
        self.back_button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.back_button.customContextMenuRequested.connect(self.show_back_menu)

        self.forward_button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.forward_button.customContextMenuRequested.connect(self.show_forward_menu)

        # Connect to history service signals
        self.history_service.history_changed.connect(self.update_button_states)
        self.history_service.current_changed.connect(self.update_current_display)

    def go_back(self):
        """Go back in history."""
        print(f"DEBUG: HistoryNavigationWidget.go_back() called")
        print(f"DEBUG: can_go_back = {self.history_service.can_go_back()}")
        print(f"DEBUG: current_index = {self.history_service.current_index}")
        print(f"DEBUG: history length = {len(self.history_service.history)}")

        if not self.history_service.can_go_back():
            print("DEBUG: Cannot go back - button should be disabled")
            return

        entry = self.history_service.go_back()
        if entry:
            print(f"DEBUG: Going back to: {entry.path}")
            self.navigate_requested.emit(entry.path)
        else:
            print("DEBUG: go_back() returned None - this shouldn't happen")

    def go_forward(self):
        """Go forward in history."""
        print(f"DEBUG: HistoryNavigationWidget.go_forward() called")
        print(f"DEBUG: can_go_forward = {self.history_service.can_go_forward()}")
        print(f"DEBUG: current_index = {self.history_service.current_index}")
        print(f"DEBUG: history length = {len(self.history_service.history)}")

        if not self.history_service.can_go_forward():
            print("DEBUG: Cannot go forward - button should be disabled")
            return

        entry = self.history_service.go_forward()
        if entry:
            print(f"DEBUG: Going forward to: {entry.path}")
            self.navigate_requested.emit(entry.path)
        else:
            print("DEBUG: go_forward() returned None - this shouldn't happen")

    def show_back_menu(self, position):
        """Show back history dropdown menu."""
        back_entries = self.history_service.get_back_entries(10)
        if not back_entries:
            print("DEBUG: No back entries for dropdown menu")
            return

        print(f"DEBUG: Showing back menu with {len(back_entries)} entries")
        menu = QMenu(self)
        for entry in back_entries:
            action = QAction(entry.display_name, self)
            action.setToolTip(entry.tooltip_text)
            action.triggered.connect(lambda checked, e=entry: self.jump_to_entry(e))
            menu.addAction(action)

        menu.exec_(self.back_button.mapToGlobal(position))

    def show_forward_menu(self, position):
        """Show forward history dropdown menu."""
        forward_entries = self.history_service.get_forward_entries(10)
        if not forward_entries:
            print("DEBUG: No forward entries for dropdown menu")
            return

        print(f"DEBUG: Showing forward menu with {len(forward_entries)} entries")
        menu = QMenu(self)
        for entry in forward_entries:
            action = QAction(entry.display_name, self)
            action.setToolTip(entry.tooltip_text)
            action.triggered.connect(lambda checked, e=entry: self.jump_to_entry(e))
            menu.addAction(action)

        menu.exec_(self.forward_button.mapToGlobal(position))

    def jump_to_entry(self, entry: HistoryEntry):
        """Jump to a specific history entry."""
        print(f"DEBUG: Jumping to history entry: {entry.path}")
        if self.history_service.jump_to_entry(entry):
            self.navigate_requested.emit(entry.path)
        else:
            print("DEBUG: Failed to jump to entry")

    def show_history_dialog(self):
        """Show full history dialog with terminal support."""
        print("DEBUG: Showing history dialog")
        dialog = HistoryViewerDialog(self.config, self.history_service, self)

        # FIXED: Get main window and connect directly to open_terminal_at_path
        main_window = None
        parent = self.parent()
        while parent:
            # Check if this is the main window by class name
            if parent.__class__.__name__ == 'MainWindow':
                main_window = parent
                break
            parent = parent.parent()

        if main_window and hasattr(main_window, 'open_terminal_at_path'):
            print("DEBUG: Successfully connected to main window's open_terminal_at_path")
            dialog.open_terminal_requested.connect(main_window.open_terminal_at_path)
        else:
            print("ERROR: Could not find main window or open_terminal_at_path method")

        if dialog.exec_() == dialog.Accepted:
            selected_entry = dialog.get_selected_entry()
            if selected_entry:
                print(f"DEBUG: Selected entry from dialog: {selected_entry.path}")
                self.jump_to_entry(selected_entry)

    def update_button_states(self):
        """Update back/forward button states."""
        can_back = self.history_service.can_go_back()
        can_forward = self.history_service.can_go_forward()

        print(f"DEBUG: Updating button states - Back: {can_back}, Forward: {can_forward}")
        print(f"DEBUG: History state - Index: {self.history_service.current_index}, Length: {len(self.history_service.history)}")

        # Enable/disable buttons
        self.back_button.setEnabled(can_back)
        self.forward_button.setEnabled(can_forward)

        # Update button styling based on state
        if can_back:
            self.back_button.setStyleSheet("background-color: #AAB7AA; padding: 2px 6px; color: black; font-weight: ;")
        else:
            self.back_button.setStyleSheet("background-color: #7B7B7B; padding: 2px 6px; color: gray;")

        if can_forward:
            self.forward_button.setStyleSheet("background-color: #AAB7AA; padding: 2px 6px; color: black; font-weight: ;")
        else:
            self.forward_button.setStyleSheet("background-color: #7B7B7B; padding: 2px 6px; color: gray;")

    def update_current_display(self, path: Path, operation: str):
        """Update current location display."""
        display_path = str(path)
        if len(display_path) > 60:
            parts = path.parts
            if len(parts) > 3:
                display_path = ".../" + "/".join(parts[-3:])

        self.current_label.setText(f"Current: {display_path}")
        self.current_label.setToolTip(f"Full path: {path}\nOperation: {operation}")

        print(f"DEBUG: Updated current display to: {display_path}")

    def debug_history_state(self):
        """Print current history state for debugging."""
        print(f"DEBUG: === History State ===")
        print(f"Current index: {self.history_service.current_index}")
        print(f"History length: {len(self.history_service.history)}")
        print(f"Can go back: {self.history_service.can_go_back()}")
        print(f"Can go forward: {self.history_service.can_go_forward()}")

        for i, entry in enumerate(self.history_service.history):
            marker = " <-- CURRENT" if i == self.history_service.current_index else ""
            print(f"  [{i}] {entry.path}{marker}")
        print(f"========================")


class HistoryViewerDialog(QDialog):
    """Dialog for viewing full history with Go buttons that open terminals."""

    # Signal for opening terminal
    open_terminal_requested = pyqtSignal(Path)

    def __init__(self, config: AppConfig, history_service: DirectoryHistoryService, parent=None):
        super().__init__(parent)
        self.config = config
        self.history_service = history_service
        self.selected_entry: Optional[HistoryEntry] = None
        self.setup_ui()
        self.populate_history()

    def setup_ui(self):
        """Setup dialog UI with Operation History below Navigation History."""
        self.setWindowTitle("Directory History")
        self.resize(800, 600)
        self.setFont(QFont(*self.config.fonts.get_font_tuple()))

        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("Directory Navigation & Operation History")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)

        # Navigation history section (top)
        nav_label = QLabel("Navigation History")
        nav_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(nav_label)

        self.nav_list = QListWidget()
        self.nav_list.setFont(QFont(*self.config.fonts.get_font_tuple(10)))
        self.nav_list.setMaximumHeight(200)  # Limit height
        layout.addWidget(self.nav_list)

        # Operation history section (bottom)
        op_label = QLabel("Operation History")
        op_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(op_label)

        self.op_list = QListWidget()
        self.op_list.setFont(QFont(*self.config.fonts.get_font_tuple(10)))
        layout.addWidget(self.op_list)

        # Details area
        details_label = QLabel("Details:")
        details_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(details_label)

        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(100)
        self.details_text.setReadOnly(True)
        self.details_text.setFont(QFont(*self.config.fonts.get_font_tuple(9)))
        self.details_text.setStyleSheet("background-color: #f5f5f5;")
        layout.addWidget(self.details_text)

        # Buttons
        button_box = QDialogButtonBox()

        self.go_button = QPushButton("Go to Selected")
        self.go_button.setEnabled(False)
        button_box.addButton(self.go_button, QDialogButtonBox.AcceptRole)

        self.clear_button = QPushButton("Clear History")
        button_box.addButton(self.clear_button, QDialogButtonBox.ResetRole)

        close_button = button_box.addButton(QDialogButtonBox.Close)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # Connect clear button directly
        self.clear_button.clicked.connect(self.clear_history)

        layout.addWidget(button_box)

        # Connect selection handlers
        self.nav_list.itemSelectionChanged.connect(self.on_nav_selection_changed)
        self.op_list.itemSelectionChanged.connect(self.on_op_selection_changed)

    def populate_history(self):
        """Populate history lists with meaningful entries and thin Go buttons."""
        # Populate navigation history - FILTER OUT base directory navigations
        self.nav_list.clear()

        # Get base directory path to filter
        base_dir = self.config.paths.base_directory

        # Filter: only show navigations that are NOT to base directory
        nav_entries = []
        for entry in self.history_service.history:
            if entry.operation == "navigate":
                # Skip if this is navigation to base directory
                if entry.path == base_dir:
                    continue
                # Skip if path is parent or grandparent (too high level)
                try:
                    if len(entry.path.relative_to(base_dir).parts) < 2:
                        continue
                except ValueError:
                    # Path not under base_dir, include it
                    pass
                nav_entries.append(entry)

        for entry in reversed(nav_entries[-50:]):
            # Create widget for item with Go button
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(2, 2, 2, 2)
            item_layout.setSpacing(5)

            # Entry label
            entry_label = QLabel(f"{entry.path.name} - {entry.timestamp.strftime('%H:%M:%S')}")
            entry_label.setFont(QFont(*self.config.fonts.get_font_tuple(10)))

            # Thin Go button - opens terminal (text symbol only)
            go_btn = QPushButton("Go")
            go_btn.setFont(QFont(*self.config.fonts.get_font_tuple(7)))
            go_btn.setFixedSize(35, 16)
            go_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.config.colors.olive};
                    padding: 0px 4px;     /* Minimal padding to keep it thin */
                    color: black;
                    border: none;
                    border-radius: 2px;
                }}
                QPushButton:hover {{
                    background-color: #88aa44;
                }}
            """)
            go_btn.clicked.connect(lambda checked, e=entry: self.open_terminal_at(e.path))
            go_btn.setToolTip(f"Open terminal at: {entry.path}")

            item_layout.addWidget(entry_label, stretch=1)
            item_layout.addWidget(go_btn)

            # Create list item
            item = QListWidgetItem(self.nav_list)
            item.setData(Qt.UserRole, entry)
            item.setSizeHint(item_widget.sizeHint())
            self.nav_list.addItem(item)
            self.nav_list.setItemWidget(item, item_widget)

        # Populate operation history
        self.op_list.clear()
        op_entries = self.history_service.get_operation_history()

        for entry in reversed(op_entries[-50:]):
            # Create widget for item with Go button
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(2, 2, 2, 2)
            item_layout.setSpacing(5)

            # Entry label
            item_text = f"{entry.operation.title()}: {entry.path.name}"
            if entry.details:
                item_text += f" - {entry.details[:30]}..."
            item_text += f" ({entry.timestamp.strftime('%m-%d %H:%M')})"

            entry_label = QLabel(item_text)
            entry_label.setFont(QFont(*self.config.fonts.get_font_tuple(10)))

            # Color code by operation type
            if entry.operation == "clone":
                entry_label.setStyleSheet(f"color: {self.config.colors.blue_grotto};")
            elif entry.operation == "trash":
                entry_label.setStyleSheet(f"color: {self.config.colors.burnt_sienna};")
            elif entry.operation == "restore":
                entry_label.setStyleSheet(f"color: {self.config.colors.olive};")
            elif entry.operation == "delete":
                entry_label.setStyleSheet(f"color: {self.config.colors.scarlet};")
            elif entry.operation == "create_run":
                entry_label.setStyleSheet(f"color: {self.config.colors.dark_blue};")
            elif entry.operation == "terminal":
                entry_label.setStyleSheet("color: white; background-color: black; padding: 2px;")

            # Thin Go button - opens terminal
            go_btn = QPushButton("Go")
            go_btn.setFont(QFont(*self.config.fonts.get_font_tuple(7)))
            go_btn.setFixedSize(35, 16)
            go_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.config.colors.olive};
                    padding: 0px 4px;     /* Minimal padding to keep it thin */
                    color: black;
                    border: none;
                    border-radius: 2px;
                }}
                QPushButton:hover {{
                    background-color: #88aa44;
                }}
            """)
            go_btn.clicked.connect(lambda checked, e=entry: self.open_terminal_at(e.path))
            go_btn.setToolTip(f"Open terminal at: {entry.path}")

            item_layout.addWidget(entry_label, stretch=1)
            item_layout.addWidget(go_btn)

            # Create list item
            item = QListWidgetItem(self.op_list)
            item.setData(Qt.UserRole, entry)
            item.setSizeHint(item_widget.sizeHint())
            self.op_list.addItem(item)
            self.op_list.setItemWidget(item, item_widget)

    def open_terminal_at(self, path: Path):
        """Open terminal at path - FIXED to actually open terminal."""
        print(f"DEBUG: Opening terminal from history dialog at: {path}")

        # Emit signal that will be caught by main window to open terminal
        self.open_terminal_requested.emit(path)

        # Dialog stays open for more operations

    def on_nav_selection_changed(self):
        """Handle navigation list selection change."""
        self.op_list.clearSelection()
        selected_items = self.nav_list.selectedItems()
        if selected_items:
            entry = selected_items[0].data(Qt.UserRole)
            self.selected_entry = entry
            self.update_details(entry)
            self.go_button.setEnabled(True)

    def on_op_selection_changed(self):
        """Handle operation list selection change."""
        self.nav_list.clearSelection()
        selected_items = self.op_list.selectedItems()
        if selected_items:
            entry = selected_items[0].data(Qt.UserRole)
            self.selected_entry = entry
            self.update_details(entry)
            self.go_button.setEnabled(True)

    def update_details(self, entry: HistoryEntry):
        """Update details display."""
        details = f"Path: {entry.path}\n"
        details += f"Operation: {entry.operation.title()}\n"
        details += f"Time: {entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        details += f"User: {entry.user}\n"

        if entry.details:
            details += f"Details: {entry.details}\n"

        # Add additional context
        if entry.operation == "clone":
            details += "\nThis was a directory cloning operation"
        elif entry.operation == "trash":
            details += "\nItems were moved to TrashBin"
        elif entry.operation == "restore":
            details += "\nItems were restored from TrashBin"
        elif entry.operation == "delete":
            details += "\nItems were permanently deleted"
        elif entry.operation == "create_run":
            details += "\nA new run directory was created"
        elif entry.operation == "terminal":
            details += "\nGoGoGo terminal was opened at this location"

        details += "\n\nClick 'Go' button to open terminal at this location"

        self.details_text.setText(details)

    def clear_history(self):
        """Clear all history."""
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear all history?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.history_service.clear_history()
            self.populate_history()
            self.details_text.clear()
            self.go_button.setEnabled(False)

    def get_selected_entry(self) -> Optional[HistoryEntry]:
        """Get the selected history entry."""
        return self.selected_entry


class QuickHistoryWidget(QWidget):
    """Compact widget showing recent operations with terminal operation styling."""

    # Signals
    navigate_requested = pyqtSignal(Path)

    def __init__(self, config: AppConfig, history_service: DirectoryHistoryService, parent=None):
        super().__init__(parent)
        self.config = config
        self.history_service = history_service
        self.setup_ui()
        self.setup_connections()
        self.update_recent_operations()

    def setup_ui(self):
        """Setup compact history widget."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Recent operations label
        self.recent_label = QLabel("Recent: ")
        self.recent_label.setFont(QFont(*self.config.fonts.get_font_tuple(8)))
        self.recent_label.setStyleSheet("color: #31352e;")
        layout.addWidget(self.recent_label)

        # Recent operation buttons (dynamic)
        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(2)
        layout.addLayout(self.button_layout)

        layout.addStretch()

    def setup_connections(self):
        """Setup connections."""
        self.history_service.history_changed.connect(self.update_recent_operations)

    def update_recent_operations(self):
        """Update recent operation buttons with terminal operation styling."""
        # Clear existing buttons
        while self.button_layout.count():
            item = self.button_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Get recent non-navigation operations
        recent_ops = self.history_service.get_recent_operations(count=30)

        # Filter out navigation operations
        non_nav_ops = [op for op in recent_ops if op.operation != "navigate"]

        print(f"Debug: Found {len(non_nav_ops)} non-navigation operations")
        for i, op in enumerate(non_nav_ops[:10]):
            print(f"  {i+1}: {op.operation} - {op.path.name}")

        # Create buttons for recent operations - SHOW 5 operations
        for i, entry in enumerate(non_nav_ops[:10]):
            # Create shorter button text
            button_text = self._get_short_operation_text(entry)

            button = QPushButton(button_text)
            button.setFont(QFont(*self.config.fonts.get_font_tuple(7)))
            button.setMaximumHeight(20)
            button.setMaximumWidth(70)
            button.setMinimumWidth(60)

            # Enhanced tooltip with more info
            tooltip = f"{entry.operation.title()}: {entry.path.name}"
            tooltip += f"\nTime: {entry.timestamp.strftime('%m-%d %H:%M')}"
            if entry.details:
                tooltip += f"\nDetails: {entry.details}"
            button.setToolTip(tooltip)

            # Color code by operation
            button.setStyleSheet(self._get_operation_style(entry.operation))

            button.clicked.connect(lambda checked, e=entry: self._navigate_to_operation_target(e))
            self.button_layout.addWidget(button)

        if len(non_nav_ops) < 5:
            print(f"Debug: Only {len(non_nav_ops)} operations available, showing all of them")

    def _get_short_operation_text(self, entry: HistoryEntry) -> str:
        """Get shortened text for operation button."""
        operation_short = {
            "clone": "Clone",
            "trash": "Trash",
            "restore": "Restore",
            "delete": "Delete",
            "create_run": "Run",
            "navigate": "Nav",
            "terminal": "Term"
        }

        short_op = operation_short.get(entry.operation, entry.operation.title())
        dir_name = entry.path.name
        if len(dir_name) > 8:
            dir_name = dir_name[:8] + "..."

        return f"{short_op}"

    def _get_operation_style(self, operation: str) -> str:
        """Get CSS style for operation type with special terminal styling."""
        styles = {
            "clone": "background-color: #172748; color: white; font-size: 8px; padding: 2px;",
            "trash": "background-color: #172748; color: #FFFF00; font-size: 8px; padding: 2px;",
            "restore": "background-color: #7DCCFA; black: white; font-size: 8px; padding: 2px;",
            "create_run": "background-color: #051537; color: white; font-size: 8px; padding: 2px;",
            "delete": "background-color: #B53439; color: #FFFF00; font-size: 8px; padding: 2px;",
            "terminal": "background-color: black; color: white; font-size: 8px; padding: 2px; font-weight: bold;",
        }

        return styles.get(operation, "background-color: #d1e2c4; color: black; font-size: 8px; padding: 2px;")

    def _navigate_to_operation_target(self, entry: HistoryEntry):
        """Navigate to the most relevant directory for this operation."""
        target_path = entry.path

        if entry.operation == "clone":
            if entry.details and "Cloned to:" in entry.details:
                dest_name = entry.details.split("Cloned to: ")[-1]
                dest_path = entry.path.parent / dest_name
                if dest_path.exists():
                    target_path = dest_path

        elif entry.operation == "trash":
            trash_path = entry.path.parent / "TrashBin"
            if trash_path.exists():
                target_path = trash_path

        elif entry.operation == "restore":
            if "TrashBin" in str(entry.path):
                restored_location = entry.path.parent.parent
                if restored_location.exists():
                    target_path = restored_location

        elif entry.operation == "create_run":
            if entry.details and "Created run directory:" in entry.details:
                run_name = entry.details.split("Created run directory: ")[-1]
                run_path = entry.path / run_name
                if run_path.exists():
                    target_path = run_path

        elif entry.operation == "terminal":
            target_path = entry.path

        self.navigate_requested.emit(target_path)
