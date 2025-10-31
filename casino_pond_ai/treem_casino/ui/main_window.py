"""
Complete main window with change detection, terminal history tracking and bottom progress bar.
"""

import getpass
import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QApplication, QMessageBox, QMenu, QAction,
    QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
from PyQt5.QtGui import QFont, QKeySequence, QClipboard

from ..config.settings import AppConfig
from ..models.directory import DirectoryHierarchy, DirectoryFilter
from ..services.directory_service import DirectoryService
from ..services.memo_service import MemoService
from ..services.history_service import DirectoryHistoryService
from ..services.change_detection_service import ChangeDetectionService, DirectoryChange
from ..ui.widgets import (
    EnhancedTreeView, BlinkingDelegate, ProgressWidget, SearchWidget,
    MemoDialog, MemoViewerDialog, StatusWidget, FilterControlWidget,
    DepthControlWidget, ConfirmationDialog, UpdatedDirectoriesWidget
)
from ..ui.history_widgets import HistoryNavigationWidget, QuickHistoryWidget
from ..utils.tree_model import DirectoryTreeModel
from ..utils.logger import get_logger


logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """Main application window with change detection, terminal history tracking and bottom progress bar."""

    def __init__(self, config: AppConfig):
        """Main application window initialization."""
        super().__init__()
        self.config = config

        # Services - Initialize history service FIRST
        self.history_service = DirectoryHistoryService(config)
        self.directory_service = DirectoryService(config)
        self.memo_service = MemoService(config)
        self.change_service = ChangeDetectionService()

        # UI components
        self.tree_view: Optional[EnhancedTreeView] = None
        self.tree_model: Optional[DirectoryTreeModel] = None
        self.blinking_delegate: Optional[BlinkingDelegate] = None
        self.history_navigation: Optional[HistoryNavigationWidget] = None
        self.quick_history: Optional[QuickHistoryWidget] = None
        self.updated_dirs_widget: Optional[UpdatedDirectoriesWidget] = None

        # State
        self.current_hierarchy: Optional[DirectoryHierarchy] = None
        self.current_filter = DirectoryFilter()
        self.current_depth = 0
        self.max_depth = 0
        self.programmatic_navigation = False

        # Setup
        self.setup_ui()
        self.setup_connections()
        self.setup_shortcuts()

        # Initial load
        print(f"DEBUG: Initial refresh_directory_tree call")
        self.refresh_directory_tree()

    def setup_ui(self):
        """Setup the main user interface."""
        self.setWindowTitle("GoGoGo")
        self.resize(600, 600)
        self.setMinimumSize(400, 400)
        self.setStyleSheet(f"background-color: {self.config.colors.background};")

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Base directory input
        input_layout = QHBoxLayout()

        base_dir_label = QLabel("Base Directory:")
        base_dir_label.setFont(QFont(*self.config.fonts.get_font_tuple()))
        input_layout.addWidget(base_dir_label)

        self.base_dir_input = QLineEdit(str(self.config.paths.base_directory))
        self.base_dir_input.setFont(QFont(*self.config.fonts.get_font_tuple(8)))
        input_layout.addWidget(self.base_dir_input)

        main_layout.addLayout(input_layout)

        # History navigation
        self.history_navigation = HistoryNavigationWidget(self.config, self.history_service)
        main_layout.addWidget(self.history_navigation)

        # Tree view with custom delegate
        self.tree_view = EnhancedTreeView(self.config)
        self.blinking_delegate = BlinkingDelegate(self.config, self.tree_view)
        self.tree_view.setItemDelegate(self.blinking_delegate)
        main_layout.addWidget(self.tree_view, stretch=1)

        # Progress widget
        self.progress_widget = ProgressWidget(self.config)
        main_layout.addWidget(self.progress_widget)

        # Main action buttons
        button_layout = self.create_action_buttons()
        main_layout.addLayout(button_layout)

        # Filter and depth controls
        control_layout = QHBoxLayout()
        control_layout.setSpacing(5)

#       # Set directory label
#       set_dir_label = QLabel("Set Dir:")
#       set_dir_label.setFont(QFont(*self.config.fonts.get_font_tuple()))
#       set_dir_label.setFixedWidth(60)
#       control_layout.addWidget(set_dir_label)

        # Filter controls
        self.filter_controls = FilterControlWidget(self.config)
        control_layout.addWidget(self.filter_controls)

        # Depth controls
        self.depth_controls = DepthControlWidget(self.config)
        control_layout.addWidget(self.depth_controls, stretch=1)

        main_layout.addLayout(control_layout)

        # Quick history widget
        self.quick_history = QuickHistoryWidget(self.config, self.history_service)
        main_layout.addWidget(self.quick_history)

        # Updated directories widget
        self.updated_dirs_widget = UpdatedDirectoriesWidget(self.config)
        main_layout.addWidget(self.updated_dirs_widget)

        # Status widget
        self.status_widget = StatusWidget(self.config)
        main_layout.addWidget(self.status_widget)

        # Scan progress bar
        self.scan_progress_bar = ProgressWidget(self.config)
        self.scan_progress_bar.setMaximumHeight(35)
        self.scan_progress_bar.progress_bar.setMaximumHeight(25)
        self.scan_progress_bar.label.setFont(QFont(*self.config.fonts.get_font_tuple(9)))
        self.scan_progress_bar.progress_bar.setTextVisible(True)

        self.scan_progress_bar.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #31352e;
                border-radius: 4px;
                background-color: #ebebe8;
                text-align: center;
                font-size: 8px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #88aa44, stop: 1 #778a35
                );
                border-radius: 2px;
            }
        """)

        main_layout.addWidget(self.scan_progress_bar)

    @pyqtSlot(Path)
    def open_terminal_at_path(self, path: Path):
        """Open terminal at specified path - called from history dialog Go buttons."""
        print(f"DEBUG: open_terminal_at_path called with: {path}")
        print(f"DEBUG: path type: {type(path)}")
        print(f"DEBUG: path exists: {path.exists()}")
        print(f"DEBUG: path is_dir: {path.is_dir()}")

        # Convert string to Path if needed
        if isinstance(path, str):
            path = Path(path)

        if not path.exists():
            print(f"ERROR: Path does not exist: {path}")
            QMessageBox.warning(self, "Invalid Path", f"Path does not exist: {path}")
            return

        if not path.is_dir():
            print(f"ERROR: Path is not a directory: {path}")
            QMessageBox.warning(self, "Invalid Path", "Selected path is not a directory.")
            return

        logger.info(f"Opening terminal from history at: {path}")

        # Add terminal opening to history
        self.history_service.add_terminal_operation(path)

        # Open terminal - same logic as Go button in main window
        print(f"DEBUG: About to call directory_service.open_terminal")
        print(f"DEBUG: directory_service exists: {self.directory_service is not None}")

        try:
            result = self.directory_service.open_terminal(path)
            print(f"DEBUG: open_terminal returned: {result}")

            if not result:
                print(f"ERROR: open_terminal returned False")
                QMessageBox.warning(self, "Terminal Error", f"Failed to open terminal at: {path}")
        except Exception as e:
            print(f"ERROR: Exception in open_terminal: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Terminal Error", f"Exception opening terminal: {e}")

    def create_action_buttons(self) -> QHBoxLayout:
        """Create main action buttons."""
        layout = QHBoxLayout()
        layout.setSpacing(5)

        # Go button
        self.go_button = QPushButton("Go")
        self.go_button.setStyleSheet(f"background-color: {self.config.colors.olive}; color: black;")
        self.go_button.setFont(QFont(*self.config.fonts.get_font_tuple()))
        self.go_button.setSizePolicy(self.go_button.sizePolicy().Expanding, self.go_button.sizePolicy().Fixed)

        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setStyleSheet(f"background-color: {self.config.colors.sage_green}; color: black;")
        self.refresh_button.setFont(QFont(*self.config.fonts.get_font_tuple()))
        self.refresh_button.setSizePolicy(self.refresh_button.sizePolicy().Expanding, self.refresh_button.sizePolicy().Fixed)

        # Clone button
        self.clone_button = QPushButton("Clone")
        self.clone_button.setStyleSheet(f"background-color: {self.config.colors.dark_blue}; color: white;")
        self.clone_button.setFont(QFont(*self.config.fonts.get_font_tuple()))
        self.clone_button.setSizePolicy(self.clone_button.sizePolicy().Expanding, self.clone_button.sizePolicy().Fixed)

        # TrashBin button
        self.trash_button = QPushButton("TrashBin")
        self.trash_button.setStyleSheet(f"background-color: {self.config.colors.dark_blue}; color: yellow;")
        self.trash_button.setFont(QFont(*self.config.fonts.get_font_tuple()))
        self.trash_button.setSizePolicy(self.trash_button.sizePolicy().Expanding, self.trash_button.sizePolicy().Fixed)

        # Restore button
        self.restore_button = QPushButton("Restore")
        self.restore_button.setStyleSheet(f"background-color: {self.config.colors.blue_grotto}; color: black;")
        self.restore_button.setFont(QFont(*self.config.fonts.get_font_tuple()))
        self.restore_button.setSizePolicy(self.restore_button.sizePolicy().Expanding, self.restore_button.sizePolicy().Fixed)

        # Delete button
        self.remove_button = QPushButton("Del")
        self.remove_button.setStyleSheet(f"background-color: {self.config.colors.scarlet}; color: yellow;")
        self.remove_button.setFont(QFont(*self.config.fonts.get_font_tuple()))
        self.remove_button.setSizePolicy(self.remove_button.sizePolicy().Expanding, self.remove_button.sizePolicy().Fixed)

        # Add buttons to layout
        layout.addWidget(self.go_button)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.clone_button)
        layout.addWidget(self.trash_button)
        layout.addWidget(self.restore_button)
        layout.addWidget(self.remove_button)

        return layout

    def setup_connections(self):
        """Setup signal-slot connections."""
        # Button connections
        self.go_button.clicked.connect(self.go_to_selected_directory)
        self.refresh_button.clicked.connect(self.refresh_directory_tree)
        self.clone_button.clicked.connect(self.clone_selected_directory)
        self.trash_button.clicked.connect(self.move_selected_directory)
        self.restore_button.clicked.connect(self.restore_selected_directory)
        self.remove_button.clicked.connect(self.remove_selected_directory)

        # Tree view connections
        self.tree_view.enter_pressed.connect(self.go_to_selected_directory)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)
        self.tree_view.selection_changed_custom.connect(self.on_selection_changed)

        # Filter connections
        self.filter_controls.user_filter_toggled.connect(self.on_user_filter_toggled)
        self.filter_controls.sort_order_changed.connect(self.on_sort_order_changed)

        # Depth connections
        self.depth_controls.depth_level_selected.connect(self.set_depth_level)

        # History navigation connections
        if hasattr(self, 'history_navigation') and self.history_navigation:
            self.history_navigation.navigate_requested.connect(self.navigate_to_path_from_history)

        if hasattr(self, 'quick_history') and self.quick_history:
            self.quick_history.navigate_requested.connect(self.navigate_to_path_from_history)

        # Change detection connections
        self.change_service.changes_detected.connect(self.on_changes_detected)
        self.updated_dirs_widget.navigate_requested.connect(self.navigate_to_path_from_update)
        self.updated_dirs_widget.cleared.connect(self.on_updates_cleared)

        # History service signals
        self.history_service.history_changed.connect(self.update_history_button_states)
        self.history_service.current_changed.connect(self.on_history_current_changed)

        # Service connections
        self.directory_service.hierarchy_updated.connect(self.on_hierarchy_updated)
        self.directory_service.operation_completed.connect(self.on_operation_completed)
        self.directory_service.progress_updated.connect(self.on_progress_updated)

        # Memo service connections
        self.memo_service.memo_added.connect(lambda path, memo: self.on_memo_changed())
        self.memo_service.memo_updated.connect(lambda path, memo: self.on_memo_changed())
        self.memo_service.memo_removed.connect(lambda path: self.on_memo_changed())
        self.memo_service.memos_loaded.connect(self.on_memos_loaded)
        self.memo_service.sync_error.connect(self.on_memo_error)

    def setup_shortcuts(self):
            """Setup keyboard shortcuts."""
            # Ctrl+V for viewing memo
            self.addAction(self.create_action("View Memo", QKeySequence("Ctrl+V"), self.view_selected_memo))

            # F5 for refresh
            self.addAction(self.create_action("Refresh", QKeySequence.Refresh, self.refresh_directory_tree))

            # Alt+Left for back
            self.addAction(self.create_action("Go Back", QKeySequence("Alt+Left"), self.go_back))

            # Alt+Right for forward
            self.addAction(self.create_action("Go Forward", QKeySequence("Alt+Right"), self.go_forward))

            # Ctrl+H for history
            self.addAction(self.create_action("Show History", QKeySequence("Ctrl+H"),
                                            lambda: self.history_navigation.show_history_dialog()))

            # ESC for clearing updates
            self.addAction(self.create_action("Clear Updates", QKeySequence(Qt.Key_Escape),
                                             lambda: self.updated_dirs_widget.clear_updates() if self.updated_dirs_widget.has_updates() else None))

            # Ctrl+1 through Ctrl+5 for depth navigation
            self.addAction(self.create_action("Set Depth 0", QKeySequence("Ctrl+0"), lambda: self.set_depth_level(0)))
            self.addAction(self.create_action("Set Depth 1", QKeySequence("Ctrl+1"), lambda: self.set_depth_level(1)))
            self.addAction(self.create_action("Set Depth 2", QKeySequence("Ctrl+2"), lambda: self.set_depth_level(2)))
            self.addAction(self.create_action("Set Depth 3", QKeySequence("Ctrl+3"), lambda: self.set_depth_level(3)))
            self.addAction(self.create_action("Set Depth 4", QKeySequence("Ctrl+4"), lambda: self.set_depth_level(4)))
            self.addAction(self.create_action("Set Depth 5", QKeySequence("Ctrl+5"), lambda: self.set_depth_level(5)))
            self.addAction(self.create_action("Set Depth 6", QKeySequence("Ctrl+6"), lambda: self.set_depth_level(6)))

    def create_action(self, name: str, shortcut: QKeySequence, slot) -> QAction:
        """Create a QAction with shortcut."""
        action = QAction(name, self)
        action.setShortcut(shortcut)
        action.triggered.connect(slot)
        return action

    @pyqtSlot()
    def go_to_selected_directory(self):
        """Open terminal at selected directory and add to recent history."""
        selected_paths = self.get_selected_paths()
        if not selected_paths:
            QMessageBox.warning(self, "No Selection", "Please select a directory.")
            return

        path = selected_paths[0]
        if not path.is_dir():
            QMessageBox.warning(self, "Invalid Selection", "Selected path is not a directory.")
            return

        logger.info(f"Opening terminal at: {path}")

        # Add terminal opening to history
        self.history_service.add_terminal_operation(path)

        # Open terminal
        self.directory_service.open_terminal(path)
        self.add_navigation_history(path)


#   @pyqtSlot(Path)
#   def open_terminal_at_path(self, path: Path):
#       """Open terminal at specified path - called from history dialog Go buttons."""
#       # Convert to Path if string
#       if isinstance(path, str):
#           path = Path(path)
#
#       # Basic validation
#       if not path.exists() or not path.is_dir():
#           return
#
#       # Use the same terminal opening logic as the main Go button
#       self.directory_service.open_terminal(path)
#       self.history_service.add_terminal_operation(path)

    @pyqtSlot(Path)
    def open_terminal_at_path(self, path: Path):
        """Open terminal at specified path - called from history dialog Go buttons."""
        if isinstance(path, str):
            path = Path(path)

        if not path.exists() or not path.is_dir():
            print(f"ERROR: Path invalid - exists: {path.exists()}, is_dir: {path.is_dir()}")
            return

        print(f"DEBUG: About to call directory_service.open_terminal")
        result = self.directory_service.open_terminal(path)
        print(f"DEBUG: open_terminal returned: {result}")

        self.history_service.add_terminal_operation(path)

    @pyqtSlot()
    def refresh_directory_tree(self):
        """Refresh the directory tree with change detection."""
        base_path = Path(self.base_dir_input.text().strip())

        if not base_path.exists():
            QMessageBox.warning(
                self,
                "Directory Not Found",
                f"The directory '{base_path}' does not exist. Please verify the path."
            )
            return

        logger.info(f"Refreshing directory tree from: {base_path}")

        # Capture current state before refresh (if we have a hierarchy)
        if self.current_hierarchy:
            logger.info("Capturing state for change detection")

        # Show scan progress immediately
        self.scan_progress_bar.show_progress("Preparing to scan directory structure...", 0)

        # Add to history ONLY if not programmatic navigation
        if not self.programmatic_navigation:
            print(f"DEBUG: refresh_directory_tree - adding {base_path} to history")
            self.add_navigation_history(base_path)
        else:
            print(f"DEBUG: refresh_directory_tree - skipping history add (programmatic)")

        # Use limited initial depth for faster loading
        initial_depth = min(self.config.ui.initial_scan_depth, self.config.ui.max_directory_depth)
        self.directory_service.scan_directory_async(base_path, fast_mode=True)

    def go_back(self):
        """Go back in history."""
        print(f"DEBUG: go_back called, can_go_back={self.history_service.can_go_back()}")

        if not self.history_service.can_go_back():
            print("DEBUG: Cannot go back - no history")
            return

        entry = self.history_service.go_back()
        if entry:
            print(f"DEBUG: Going back to {entry.path}")
            self.navigate_to_path_from_history(entry.path)
        else:
            print("DEBUG: go_back returned None")

    def go_forward(self):
        """Go forward in history."""
        print(f"DEBUG: go_forward called, can_go_forward={self.history_service.can_go_forward()}")

        if not self.history_service.can_go_forward():
            print("DEBUG: Cannot go forward - no forward history")
            return

        entry = self.history_service.go_forward()
        if entry:
            print(f"DEBUG: Going forward to {entry.path}")
            self.navigate_to_path_from_history(entry.path)
        else:
            print("DEBUG: go_forward returned None")

    def navigate_to_path_from_history(self, path: Path):
        """Navigate to a path from history."""
        print(f"DEBUG: Navigating to path from history: {path}")

        self.programmatic_navigation = True
        try:
            current_base = Path(self.base_dir_input.text())

            try:
                path.relative_to(current_base)
                print(f"DEBUG: Path {path} is under current base {current_base}")
                self.navigate_to_directory(str(path))
            except ValueError:
                print(f"DEBUG: Path {path} is NOT under current base {current_base}")
                base_path = self.find_base_path_for_target(path)
                if base_path and base_path != current_base:
                    print(f"DEBUG: Changing base directory to {base_path}")
                    self.base_dir_input.setText(str(base_path))
                    self.refresh_directory_tree()
                    QTimer.singleShot(1000, lambda: self.navigate_to_directory(str(path)))
                else:
                    print(f"DEBUG: Using fallback navigation to {path}")
                    self.navigate_to_directory(str(path))

        except Exception as e:
            print(f"DEBUG: Error in navigate_to_path_from_history: {e}")
            self.navigate_to_directory(str(path))
        finally:
            self.programmatic_navigation = False

    @pyqtSlot(Path)
    def navigate_to_path_from_update(self, path: Path):
        """Navigate to an updated directory."""
        self.programmatic_navigation = True
        try:
            current_base = Path(self.base_dir_input.text())

            try:
                path.relative_to(current_base)
                self.navigate_to_directory(str(path))
            except ValueError:
                base_path = self.find_base_path_for_target(path)
                if base_path and base_path != current_base:
                    self.base_dir_input.setText(str(base_path))
                    self.refresh_directory_tree()
                    QTimer.singleShot(1000, lambda: self.navigate_to_directory(str(path)))
                else:
                    self.navigate_to_directory(str(path))
        finally:
            self.programmatic_navigation = False

    def find_base_path_for_target(self, target_path: Path) -> Optional[Path]:
        """Find appropriate base directory that contains the target path."""
        current_base = Path(self.base_dir_input.text())
        try:
            target_path.relative_to(current_base)
            return current_base
        except ValueError:
            if self.config.paths.project_base.exists():
                try:
                    target_path.relative_to(self.config.paths.project_base)
                    return self.config.paths.project_base
                except ValueError:
                    pass
            return target_path.parent if target_path.parent != target_path else target_path

    def add_navigation_history(self, path: Path):
        """Add navigation to history."""
        print(f"DEBUG: add_navigation_history called with {path}, programmatic={self.programmatic_navigation}")

        if not self.programmatic_navigation:
            print(f"DEBUG: Adding {path} to navigation history")
            self.history_service.add_navigation(path)
        else:
            print(f"DEBUG: Skipping history add - programmatic navigation")

    def navigate_to_directory(self, target_dir):
        """Navigate to directory."""
        if not self.tree_model:
            return

        index = self.tree_model.find_path_index(Path(target_dir))
        if index and index.isValid():
            self.tree_view.setCurrentIndex(index)
            self.tree_view.scrollTo(index)
            self.add_navigation_history(Path(target_dir))

    # CHANGE DETECTION METHODS

    @pyqtSlot(list)
    def on_changes_detected(self, changes: List[DirectoryChange]):
        """Handle detected directory changes after refresh."""
        updated_paths = [change.path for change in changes if change.is_updated]

        if updated_paths:
            logger.info(f"Detected {len(updated_paths)} updated directories")
            self.updated_dirs_widget.set_updated_directories(updated_paths)

            change_types = {}
            for change in changes:
                change_types[change.change_type] = change_types.get(change.change_type, 0) + 1

            summary = ", ".join([f"{count} {ctype}" for ctype, count in change_types.items()])
            self.show_status_message(f"Updates detected: {summary}", 5000)

    @pyqtSlot()
    def on_updates_cleared(self):
        """Handle when user clears the updates widget."""
        logger.info("Updated directories cleared by user")
        self.show_status_message("Updates cleared", 2000)

    # HIERARCHY AND UI UPDATE METHODS

    @pyqtSlot(DirectoryHierarchy)
    def on_hierarchy_updated(self, hierarchy: DirectoryHierarchy):
        """Handle updated directory hierarchy with change detection."""
        logger.info(f"Directory hierarchy updated, max depth: {hierarchy.calculate_max_depth()}")

        # Detect changes from previous hierarchy
        if self.current_hierarchy:
            self.change_service.detect_changes(hierarchy)
        else:
            # First load - just capture state
            self.change_service.capture_state(hierarchy)

        self.current_hierarchy = hierarchy
        self.max_depth = hierarchy.calculate_max_depth()

        self.depth_controls.update_depth_buttons(self.max_depth)
        self.status_widget.update_depth_status(self.current_depth, self.max_depth)

        self.update_tree_view()
        # self.auto_expand_user_workspace()  # Disabled: Keep initial state without auto-selection

    def update_tree_view(self):
        """Update tree view with current hierarchy and filter."""
        if not self.current_hierarchy:
            return

        filtered_hierarchy = self.directory_service.apply_filter(
            self.current_hierarchy,
            self.current_filter
        )

        self.tree_model = DirectoryTreeModel(
            filtered_hierarchy,
            self.current_filter,
            self.memo_service.memo_collection,
            self.config
        )

        self.tree_view.setModel(self.tree_model)
        self.apply_highlighting()

    def apply_highlighting(self):
        """Apply highlighting patterns exactly like original code."""
        if not self.tree_model:
            return

        # Clear existing highlights
        self.blinking_delegate.clear_blinking_items()

        # Get current user and patterns
        username = getpass.getuser()
        user_pattern = f"works_{username}"

        # Get environment variables for pattern matching
        design_ver = os.getenv('casino_design_ver', '')
        dk_ver = os.getenv('casino_dk_ver', '')
        tag = os.getenv('casino_tag', '')

        # Apply highlighting using original color logic
        if design_ver and dk_ver and tag:
            env_pattern = f"{design_ver}_{dk_ver}_{tag}"
            self.tree_model.highlight_pattern(env_pattern, "#045AB7", priority=100)
            print(f"DEBUG: Applied BLUE highlighting for environment pattern: {env_pattern}")

        # Apply red color ONLY for current user's workspace (exact match)
        self.tree_model.highlight_pattern(user_pattern, "brown", priority=80, exact_match=True)
        print(f"DEBUG: Applied BROWN highlighting for EXACT user pattern: {user_pattern}")

        # Add blinking effect for current user's workspace only
        user_indexes = self.tree_model.find_pattern_indexes(user_pattern)
        for index in user_indexes:
            self.blinking_delegate.add_blinking_item(index, user_pattern)

    def auto_expand_user_workspace(self):
        """Automatically expand to user workspace if found."""
        if not self.tree_model:
            return

        user_pattern = self.config.get_user_workspace_pattern()
        user_index = self.tree_model.find_pattern_index(user_pattern)

        if user_index and user_index.isValid():
            self.tree_view.setExpanded(user_index, True)
            self.tree_view.setCurrentIndex(user_index)

            item_depth = self.tree_model.get_item_depth(user_index)
            self.current_depth = item_depth
            self.depth_controls.set_current_depth(item_depth)
            self.status_widget.update_depth_status(self.current_depth, self.max_depth)

    @pyqtSlot(bool)
    def on_user_filter_toggled(self, me_only: bool):
        """Handle user filter toggle."""
        self.current_filter.show_only_user_workspace = me_only
        if me_only:
            self.current_filter.user_name = getpass.getuser()

        self.update_tree_view()
        logger.info(f"User filter toggled: {'me_only' if me_only else 'all_users'}")

    @pyqtSlot(str)
    def on_sort_order_changed(self, sort_order: str):
        """Handle sort order change."""
        self.current_filter.sort_by = sort_order
        self.update_tree_view()
        logger.info(f"Sort order changed: {sort_order}")

    @pyqtSlot(int)
    def set_depth_level(self, level: int):
        """Set tree expansion depth level."""
        self.current_depth = level
        self.status_widget.update_depth_status(self.current_depth, self.max_depth)

        if self.tree_model:
            self.tree_model.expand_to_depth(self.tree_view, level)

    @pyqtSlot(list)
    def on_selection_changed(self, selected_paths: List[Path]):
        """Handle tree view selection changes."""
        if selected_paths and self.tree_model:
            first_path = selected_paths[0]
            index = self.tree_model.find_path_index(first_path)
            if index and index.isValid():
                depth = self.tree_model.get_item_depth(index)
                self.current_depth = depth
                self.depth_controls.set_current_depth(depth)
                self.status_widget.update_depth_status(self.current_depth, self.max_depth)

    @pyqtSlot(str, int)
    def on_progress_updated(self, message: str, progress: int):
        """Handle progress updates - use bottom progress bar for scanning."""
        if ("Scanning" in message or "directory" in message.lower() or
            "scan" in message.lower() or "Starting" in message):
            self.scan_progress_bar.show_progress("", progress)
            if progress >= 100:
                QTimer.singleShot(1500, self.scan_progress_bar.hide_progress)
        else:
            self.progress_widget.show_progress(message, progress)

    @pyqtSlot(str, bool)
    def on_operation_completed(self, operation: str, success: bool):
        """Handle completed operations."""
        self.progress_widget.hide_progress()

        if success:
            logger.info(f"Operation completed successfully: {operation}")
        else:
            logger.error(f"Operation failed: {operation}")
            QMessageBox.warning(self, "Operation Failed", f"Operation failed: {operation}")

    def update_history_button_states(self):
        """Update history button states when history changes."""
        if hasattr(self, 'history_navigation') and self.history_navigation:
            self.history_navigation.update_button_states()

    def on_history_current_changed(self, path, operation):
        """Handle history current position changes."""
        if hasattr(self, 'history_navigation') and self.history_navigation:
            self.history_navigation.update_current_display(path, operation)

    # CONTEXT MENU AND CLIPBOARD

    def show_context_menu(self, position):
        """Show context menu for tree view with better color contrast."""
        selected_paths = self.get_selected_paths()
        if not selected_paths:
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #f5f5f5;
                border: 1px solid #cccccc;
                padding: 4px;
                font-size: 11px;
            }
            QMenu::item {
                background-color: transparent;
                color: #333333;
                padding: 6px 14px;
                margin: 0px;
            }
            QMenu::item:selected {
                background-color: #e0e0e0;
                color: #333333;
            }
            QMenu::item:hover {
                background-color: #e0e0e0;
                color: #333333;
            }
            QMenu::item:disabled {
                color: #999999;
            }
            QMenu::separator {
                height: 1px;
                background-color: #cccccc;
                margin: 4px 8px;
            }
        """)

        # Copy full path action
        copy_full_path_action = menu.addAction("Copy Full Path")
        copy_full_path_action.triggered.connect(lambda: self.copy_full_paths_to_clipboard(selected_paths))

        # Copy directory name action
        copy_name_action = menu.addAction("Copy Directory Name")
        copy_name_action.triggered.connect(lambda: self.copy_names_to_clipboard(selected_paths))

        # Memo actions (only for single selection)
        if len(selected_paths) == 1:
            path = selected_paths[0]
            menu.addSeparator()

            if self.memo_service.has_memo(path):
                view_memo_action = menu.addAction("View Memo")
                view_memo_action.triggered.connect(lambda: self.view_memo(path))

            add_memo_action = menu.addAction("Add/Edit Memo")
            add_memo_action.triggered.connect(self.mark_selected_directory)

            if self.memo_service.has_memo(path):
                remove_memo_action = menu.addAction("Remove Memo")
                remove_memo_action.triggered.connect(lambda: self.remove_memo(path))

        # Symlink action (only for single selection)
        if len(selected_paths) == 1:
            path = selected_paths[0]
            # Check if this is a symlink
            if path.is_symlink():
                menu.addSeparator()
                show_real_path_action = menu.addAction("Show Real Path")
                show_real_path_action.triggered.connect(lambda: self.show_real_path(path))

        menu.exec_(self.tree_view.viewport().mapToGlobal(position))

    def copy_full_paths_to_clipboard(self, paths: List[Path]):
        """Copy selected full paths to clipboard."""
        try:
            paths_text = "\n".join(str(path) for path in paths)
            clipboard = QApplication.clipboard()
            clipboard.setText(paths_text, QClipboard.Clipboard)

            if clipboard.supportsSelection():
                clipboard.setText(paths_text, QClipboard.Selection)

            message = f"Copied {len(paths)} full path(s) to clipboard"
            self.show_status_message(message)

        except Exception as e:
            print(f"ERROR: Failed to copy paths to clipboard: {e}")
            self.show_status_message(f"Failed to copy: {e}")

    def copy_names_to_clipboard(self, paths: List[Path]):
        """Copy selected directory names to clipboard."""
        try:
            names_text = "\n".join(path.name for path in paths)
            clipboard = QApplication.clipboard()
            clipboard.setText(names_text, QClipboard.Clipboard)

            if clipboard.supportsSelection():
                clipboard.setText(names_text, QClipboard.Selection)

            message = f"Copied {len(paths)} directory name(s) to clipboard"
            self.show_status_message(message)

        except Exception as e:
            print(f"ERROR: Failed to copy names to clipboard: {e}")
            self.show_status_message(f"Failed to copy: {e}")

    def show_status_message(self, message: str, duration: int = 3000):
        """Show temporary status message."""
        self.status_widget.set_help_text(message)
        QTimer.singleShot(duration, lambda: self.status_widget.set_help_text(
            #"Help: Use arrow keys to navigate and Enter to go to the chosen directory."
            ""
        ))

    def show_real_path(self, path: Path):
        """Show the real path of a symlink with option to copy to clipboard."""
        if not path.is_symlink():
            return

        try:
            real_path = path.resolve()

            msg = QMessageBox(self)
            msg.setWindowTitle("Symlink Real Path")
            msg.setText(f"Symlink:\n{path}\n\nReal Path:\n{real_path}")
            msg.setIcon(QMessageBox.Information)

            # Add Copy button
            copy_btn = msg.addButton("Copy Real Path", QMessageBox.ActionRole)
            ok_btn = msg.addButton(QMessageBox.Ok)

            msg.exec_()

            # Check which button was clicked
            if msg.clickedButton() == copy_btn:
                clipboard = QApplication.clipboard()
                clipboard.setText(str(real_path), QClipboard.Clipboard)

                if clipboard.supportsSelection():
                    clipboard.setText(str(real_path), QClipboard.Selection)

                self.show_status_message("Real path copied to clipboard")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to resolve symlink:\n{e}")
            self.show_status_message(f"Failed to resolve symlink: {e}")

    # CORE OPERATIONS (Clone, Trash, Restore, Delete)

    @pyqtSlot()
    def clone_selected_directory(self):
        """Clone selected directory."""
        selected_dir = self.get_selected_directory()
        if not selected_dir:
            QMessageBox.critical(self, "Error", "Please select a directory to clone.")
            return

        from ..ui.dialogs import CloneDialog
        dialog = CloneDialog(self.config, selected_dir, self.directory_service, self)
        if dialog.exec_() == dialog.Accepted:
            dest_name = dialog.new_dir_name_input.text().strip()
            if dest_name:
                source_path = Path(selected_dir)
                dest_path = source_path.parent / dest_name
                self.history_service.add_clone_operation(source_path, dest_path)
            QTimer.singleShot(500, self.refresh_directory_tree)

    @pyqtSlot()
    def move_selected_directory(self):
        """Move selected directories to TrashBin with proper permission handling."""
        selected_indexes = self.tree_view.selectedIndexes()
        if not selected_indexes:
            QMessageBox.critical(self, "Error", "Please select one or more directories to move.")
            return

        selected_dirs = set()
        for index in selected_indexes:
            dir_path = index.data(Qt.UserRole)
            if dir_path:
                selected_dirs.add(dir_path)

        if not selected_dirs:
            QMessageBox.critical(self, "Error", "No valid directories selected for removal.")
            return

        reply = QMessageBox.question(
            self,
            'Confirmation',
            f"Are you sure you want to move {len(selected_dirs)} selected directories to TrashBin?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        first_dir = list(selected_dirs)[0]
        parent_dir = os.path.dirname(first_dir)
        trash_bin = os.path.join(parent_dir, "TrashBin")

        try:
            if not os.path.exists(trash_bin):
                os.makedirs(trash_bin)
                logger.info(f"Created TrashBin directory: {trash_bin}")
            elif not os.access(trash_bin, os.W_OK):
                raise PermissionError(f"No write permission to TrashBin: {trash_bin}")

        except PermissionError as e:
            current_user = getpass.getuser()
            parent_owner = self._get_directory_owner(parent_dir)

            error_msg = (
                f"Permission denied: Cannot create or access TrashBin.\n\n"
                f"Location: {trash_bin}\n"
                f"Current user: {current_user}\n"
                f"Directory owner: {parent_owner or 'unknown'}\n\n"
                f"This usually happens when trying to move files in another user's workspace. "
                f"You may need to:\n"
                f"? Ask the directory owner ({parent_owner}) to move these files\n"
                f"? Use system commands with appropriate permissions\n"
                f"? Contact your system administrator"
            )

            QMessageBox.warning(self, "Permission Error", error_msg)
            logger.warning(f"TrashBin permission error: {e}")
            return

        except Exception as e:
            error_msg = (
                f"Failed to create TrashBin directory.\n\n"
                f"Location: {trash_bin}\n"
                f"Error: {str(e)}\n\n"
                f"Please check:\n"
                f"? Available disk space\n"
                f"? Directory permissions\n"
                f"? File system restrictions"
            )

            QMessageBox.critical(self, "TrashBin Error", error_msg)
            logger.error(f"Failed to create TrashBin: {e}")
            return

        errors = []
        moved_paths = []
        permission_errors = []

        for selected_dir in selected_dirs:
            try:
                if not os.access(os.path.dirname(selected_dir), os.W_OK):
                    permission_errors.append(selected_dir)
                    continue

                shutil.move(selected_dir, trash_bin)
                moved_paths.append(Path(selected_dir))
                logger.info(f"Moved to trash: {selected_dir}")

            except PermissionError:
                permission_errors.append(selected_dir)
            except Exception as e:
                errors.append(f"Failed to move {os.path.basename(selected_dir)}: {str(e)}")
                logger.error(f"Move error for {selected_dir}: {e}")

        if permission_errors:
            current_user = getpass.getuser()
            perm_error_msg = (
                f"Permission denied for {len(permission_errors)} directories.\n\n"
                f"Current user: {current_user}\n"
                f"Directories with permission issues:\n" +
                "\n".join([f"? {os.path.basename(d)}" for d in permission_errors[:5]]) +
                (f"\n? ... and {len(permission_errors) - 5} more" if len(permission_errors) > 5 else "") +
                f"\n\nThese directories are likely owned by other users. "
                f"Contact the directory owners or system administrator for assistance."
            )
            QMessageBox.warning(self, "Permission Errors", perm_error_msg)

        if errors:
            QMessageBox.warning(
                self,
                "Move Errors",
                f"Some directories could not be moved:\n\n" + "\n".join(errors)
            )

        if moved_paths:
            success_count = len(moved_paths)
            QMessageBox.information(
                self,
                "Move Completed",
                f"Successfully moved {success_count} director{'y' if success_count == 1 else 'ies'} to TrashBin."
            )

            self.history_service.add_trash_operation(moved_paths, Path(trash_bin))
            self.refresh_directory()
            self.navigate_to_directory(trash_bin)
        elif not permission_errors and not errors:
            QMessageBox.information(self, "No Action", "No directories were moved.")

    def _get_directory_owner(self, directory_path: str) -> Optional[str]:
        """Get the owner of a directory."""
        try:
            import pwd
            stat_info = os.stat(directory_path)
            owner_uid = stat_info.st_uid
            owner_info = pwd.getpwuid(owner_uid)
            return owner_info.pw_name
        except (ImportError, OSError, KeyError):
            return None

    @pyqtSlot()
    def restore_selected_directory(self):
        """Restore selected directories from TrashBin."""
        selected_indexes = self.tree_view.selectedIndexes()
        if not selected_indexes:
            QMessageBox.critical(self, "Error", "Please select one or more directories to restore.")
            return

        selected_dirs = set()
        for index in selected_indexes:
            dir_path = index.data(Qt.UserRole)
            if dir_path:
                selected_dirs.add(dir_path)

        if not selected_dirs:
            QMessageBox.critical(self, "Error", "No valid directories selected for restoration.")
            return

        valid_dirs = {d for d in selected_dirs if "/TrashBin/" in d}
        invalid_dirs = selected_dirs - valid_dirs

        if invalid_dirs:
            QMessageBox.information(
                self,
                "Invalid Selection",
                "The following directories are not in TrashBin and will not be restored:\n" + "\n".join(invalid_dirs)
            )
            return

        reply = QMessageBox.question(
            self,
            'Confirmation',
            f"Are you sure you want to restore {len(valid_dirs)} selected directories from TrashBin?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            errors = []
            restored_paths = []

            for selected_dir in valid_dirs:
                trash_bin = os.path.dirname(selected_dir)
                restore_path = os.path.join(os.path.dirname(trash_bin), os.path.basename(selected_dir))
                try:
                    shutil.move(selected_dir, restore_path)
                    restored_paths.append(Path(selected_dir))
                except Exception as e:
                    errors.append(f"Failed to restore {selected_dir}: {str(e)}")

            if errors:
                QMessageBox.warning(self, "Errors Occurred", "\n".join(errors))
            else:
                QMessageBox.information(self, "Success", "Selected directories successfully restored.")

            if restored_paths:
                self.history_service.add_restore_operation(restored_paths)

            self.refresh_directory()
            self.navigate_to_directory(trash_bin)

    @pyqtSlot()
    def remove_selected_directory(self):
        """Permanently delete selected directories."""
        selected_indexes = self.tree_view.selectedIndexes()
        if not selected_indexes:
            QMessageBox.critical(self, "Error", "Please select one or more directories to delete.")
            return

        selected_dirs = set()
        for index in selected_indexes:
            dir_path = index.data(Qt.UserRole)
            if dir_path:
                selected_dirs.add(dir_path)

        if not selected_dirs:
            QMessageBox.critical(self, "Error", "No valid directories selected for deletion.")
            return

        reply = QMessageBox.question(
            self,
            'Initial Confirmation',
            f"You are about to delete {len(selected_dirs)} directories permanently.\n"
            "Would you like to review this decision before proceeding?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        final_reply = QMessageBox.question(
            self,
            'Final Confirmation',
            "The following directories will be deleted permanently:\n" +
            "\n".join(selected_dirs) + "\n\nAre you sure you want to proceed?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if final_reply == QMessageBox.Yes:
            errors = []
            parent_dirs = set()
            deleted_paths = []

            for selected_dir in selected_dirs:
                parent_dirs.add(os.path.dirname(selected_dir))
                try:
                    shutil.rmtree(selected_dir)
                    deleted_paths.append(Path(selected_dir))
                except Exception as e:
                    errors.append(f"Failed to delete {selected_dir}: {str(e)}")

            if errors:
                QMessageBox.warning(self, "Errors Occurred", "\n".join(errors))
            else:
                QMessageBox.information(self, "Success", "All selected directories have been permanently deleted.")

            if deleted_paths:
                self.history_service.add_delete_operation(deleted_paths)

            self.refresh_directory()
            if parent_dirs:
                self.navigate_to_directory(parent_dirs.pop())

    # MEMO FUNCTIONS

    def mark_selected_directory(self):
        """Add/edit memo for selected directory."""
        selected_index = self.tree_view.currentIndex()
        if not selected_index.isValid():
            QMessageBox.critical(self, "Error", "Please select a directory to mark.")
            return

        dir_path = selected_index.data(Qt.UserRole)
        if not dir_path:
            return

        existing_memo = self.memo_service.get_memo(Path(dir_path))

        from ..ui.widgets import MemoDialog
        dialog = MemoDialog(self.config, Path(dir_path), existing_memo, self)
        if dialog.exec_() == dialog.Accepted:
            memo_text = dialog.get_memo_text()
            if memo_text:
                self.memo_service.add_memo(Path(dir_path), memo_text)
                self.update_tree_view()
                self.navigate_to_directory(dir_path)

    def remove_memo(self, path: Path):
        """Remove memo for directory."""
        if self.memo_service.remove_memo(path):
            self.update_tree_view()
            self.navigate_to_directory(str(path))

    def view_memo(self, path: Path):
        """View memo details."""
        memo = self.memo_service.get_memo(path)
        if memo:
            from ..ui.widgets import MemoViewerDialog
            dialog = MemoViewerDialog(self.config, path, memo, self)
            dialog.exec_()

    def view_selected_memo(self):
        """View memo for currently selected directory."""
        selected_index = self.tree_view.currentIndex()
        if selected_index.isValid():
            dir_path = selected_index.data(Qt.UserRole)
            if dir_path and self.memo_service.has_memo(Path(dir_path)):
                self.view_memo(Path(dir_path))

    def on_memo_changed(self):
        """Handle memo changes."""
        logger.info("Memo collection changed")
        if self.tree_model:
            self.tree_model.update_memo_collection(self.memo_service.memo_collection)

    def on_memos_loaded(self, memo_collection):
        """Handle memos loaded."""
        logger.info("Loaded memos")
        if self.tree_model:
            self.tree_model.update_memo_collection(memo_collection)

    @pyqtSlot(str)
    def on_memo_error(self, error: str):
        """Handle memo service errors."""
        logger.error(f"Memo service error: {error}")
        QMessageBox.warning(self, "Memo Error", f"Memo operation failed: {error}")

    # UTILITY METHODS

    def get_selected_directory(self):
        """Get single selected directory."""
        index = self.tree_view.currentIndex()
        if not index.isValid():
            return None
        dir_path = index.data(Qt.UserRole)
        return dir_path if dir_path else None

    def get_selected_paths(self) -> List[Path]:
        """Get currently selected directory paths."""
        if not self.tree_view or not self.tree_view.selectedIndexes():
            return []

        paths = []
        for index in self.tree_view.selectedIndexes():
            path_data = index.data(Qt.UserRole)
            if path_data:
                paths.append(Path(path_data))

        return paths

    def refresh_directory(self):
        """Refresh directory."""
        selected_index = self.tree_view.currentIndex()
        selected_path = selected_index.data(Qt.UserRole) if selected_index.isValid() else None

        self.tree_view.setModel(None)
        self.memo_service.load_memos()
        self.current_hierarchy = None
        self.refresh_directory_tree()

        if selected_path:
            self.select_directory_path(selected_path)
            self.tree_view.viewport().update()
            self.tree_view.scrollTo(self.tree_view.currentIndex())

    def select_directory_path(self, path):
        """Select directory path in tree view."""
        if not self.tree_model:
            return

        index = self.tree_model.find_path_index(Path(path))
        if index and index.isValid():
            self.tree_view.setCurrentIndex(index)
            self.tree_view.scrollTo(index, self.tree_view.PositionAtCenter)

    def keyPressEvent(self, event):
        """Handle main window key press events."""
        if event.key() == Qt.Key_V and event.modifiers() == Qt.ControlModifier:
            self.view_selected_memo()
        elif event.key() == Qt.Key_Left and event.modifiers() == Qt.AltModifier:
            self.go_back()
        elif event.key() == Qt.Key_Right and event.modifiers() == Qt.AltModifier:
            self.go_forward()
        elif event.key() == Qt.Key_Escape:
            if self.updated_dirs_widget.has_updates():
                self.updated_dirs_widget.clear_updates()
        else:
            super().keyPressEvent(event)
