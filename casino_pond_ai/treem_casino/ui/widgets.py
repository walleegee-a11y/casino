"""
Custom UI widgets for the Treem Casino application.
Provides reusable, enhanced widgets with modern styling and behavior.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from PyQt5.QtWidgets import (
    QTreeView, QAbstractItemView, QStyledItemDelegate, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLineEdit, QLabel, QProgressBar, QTextEdit,
    QDialog, QDialogButtonBox, QMessageBox, QFrame, QSizePolicy, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QModelIndex
from PyQt5.QtGui import QFont, QColor, QBrush, QPainter

from ..config.settings import AppConfig
from ..models.memo import Memo


class BlinkingDelegate(QStyledItemDelegate):
    """Custom delegate for blinking text effects in tree views."""

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.blink_state = True
        self.blink_texts: Set[Tuple[QModelIndex, str]] = set()

        # Setup blink timer
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self._toggle_blink_state)
        self.blink_timer.start(self.config.ui.blink_interval)

    def _toggle_blink_state(self):
        """Toggle blink state and update view."""
        self.blink_state = not self.blink_state
        if self.parent():
            self.parent().viewport().update()

    def add_blinking_item(self, index: QModelIndex, text_to_blink: str):
        """Add an item to the blinking set."""
        self.blink_texts.add((index, text_to_blink))

    def remove_blinking_item(self, index: QModelIndex, text_to_blink: str):
        """Remove an item from the blinking set."""
        self.blink_texts.discard((index, text_to_blink))

    def clear_blinking_items(self):
        """Clear all blinking items."""
        self.blink_texts.clear()

    def paint(self, painter: QPainter, option, index: QModelIndex):
        """Custom paint method for blinking effect."""
        text = index.data()

        # Check if this item should blink
        should_blink = any(
            expression in text for _, expression in self.blink_texts
            if _ == index
        )

        if should_blink:
            font = option.font
            font.setBold(True)
            painter.setFont(font)

            if self.blink_state:
                painter.setPen(QColor('blue'))
                painter.setBrush(QBrush(QColor('orange')))
            else:
                painter.setPen(QColor('black'))
                painter.setBrush(QBrush(QColor('white')))

        # Call parent paint method
        super().paint(painter, option, index)


class EnhancedTreeView(QTreeView):
    """Enhanced tree view with keyboard navigation and context menu support."""

    # Signals
    enter_pressed = pyqtSignal()
    selection_changed_custom = pyqtSignal(list)  # List of selected paths

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setup_view()

    def setup_view(self):
        """Setup tree view properties."""
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setHeaderHidden(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(self.config.ui.tree_minimum_height)
        self.setStyleSheet(f"background-color: {self.config.colors.tree_background};")
        self.setContextMenuPolicy(Qt.CustomContextMenu)

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.enter_pressed.emit()
        else:
            super().keyPressEvent(event)

    def selectionChanged(self, selected, deselected):
        """Handle selection changes."""
        super().selectionChanged(selected, deselected)

        # Emit custom signal with selected paths
        selected_paths = []
        for index in self.selectedIndexes():
            path_data = index.data(Qt.UserRole)
            if path_data:
                selected_paths.append(Path(path_data))

        self.selection_changed_custom.emit(selected_paths)


class ProgressWidget(QWidget):
    """Enhanced widget for showing operation progress with better visibility."""

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setup_ui()
        self.hide()  # Hidden by default

    def setup_ui(self):
        """Setup enhanced progress widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        # Progress message label
        self.label = QLabel("Operation in progress...")
        self.label.setFont(QFont(*self.config.fonts.get_font_tuple(9)))
        self.label.setStyleSheet("color: #31352e; font-weight: bold;")
        self.label.setWordWrap(True)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFont(QFont(*self.config.fonts.get_font_tuple(8)))

        # Enhanced styling for better visibility
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #31352e;
                border-radius: 5px;
                background-color: #f0f0f0;
                text-align: center;
                font-weight: bold;
                color: #31352e;
                padding: 1px;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #88aa44, stop: 1 #778a35
                );
                border-radius: 3px;
                margin: 0px;
            }
        """)

        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)

        # Optional details frame (for scan-specific information)
        self.details_frame = QFrame()
        self.details_frame.setFrameStyle(QFrame.StyledPanel)
        self.details_frame.setStyleSheet("background-color: #f8f8f8; border: 1px solid #d0d0d0;")

        details_layout = QVBoxLayout(self.details_frame)
        details_layout.setContentsMargins(5, 3, 5, 3)

        self.details_label = QLabel()
        self.details_label.setFont(QFont(*self.config.fonts.get_font_tuple(8)))
        self.details_label.setStyleSheet("color: #666; font-style: italic;")
        self.details_label.setWordWrap(True)
        details_layout.addWidget(self.details_label)

        layout.addWidget(self.details_frame)
        self.details_frame.hide()  # Hidden by default

    def show_progress(self, message: str, progress: int = 0, details: str = None):
        """Show progress with enhanced message and optional details."""
        self.label.setText(message)
        self.progress_bar.setValue(progress)

        # Set progress bar text to show percentage and operation
        progress_text = f"{progress}%"
        if progress > 0 and progress < 100:
            if "scan" in message.lower():
                progress_text = f"Scanning... {progress}%"
            elif "estimating" in message.lower():
                progress_text = f"Analyzing... {progress}%"
            elif "finalizing" in message.lower():
                progress_text = f"Completing... {progress}%"
        elif progress == 100:
            progress_text = "Complete!"

        self.progress_bar.setFormat(progress_text)

        # Show details if provided
        if details:
            self.details_label.setText(details)
            self.details_frame.show()
        else:
            self.details_frame.hide()

        self.show()

        # Ensure the widget updates immediately
        self.repaint()

    def hide_progress(self):
        """Hide progress widget."""
        self.hide()
        self.details_frame.hide()

    def update_progress(self, message: str, progress: int, details: str = None):
        """Update progress display with new values."""
        self.show_progress(message, progress, details)

    def set_scan_mode(self, enabled: bool):
        """Enable/disable scan-specific styling and behavior."""
        if enabled:
            # Scan mode: more prominent display
            self.setStyleSheet("""
                ProgressWidget {
                    background-color: #e8f4e8;
                    border: 1px solid #778a35;
                    border-radius: 3px;
                    padding: 2px;
                }
            """)
            self.label.setStyleSheet("color: #2d4a1a; font-weight: bold;")
        else:
            # Normal mode
            self.setStyleSheet("")
            self.label.setStyleSheet("color: #31352e; font-weight: bold;")


class ScanProgressWidget(ProgressWidget):
    """Specialized progress widget for directory scanning operations."""

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(config, parent)
        self.total_estimated = 0
        self.current_count = 0
        self.scan_start_time = None

    def start_scan(self, base_path: str, estimated_dirs: int = 0):
        """Start scan progress tracking."""
        import time
        self.scan_start_time = time.time()
        self.total_estimated = estimated_dirs
        self.current_count = 0

        self.set_scan_mode(True)

        if estimated_dirs > 0:
            details = f"Scanning {estimated_dirs} directories from {Path(base_path).name}"
        else:
            details = f"Scanning directories from {Path(base_path).name}"

        self.show_progress("Initializing directory scan...", 0, details)

    def update_scan_progress(self, message: str, dirs_processed: int, current_dir: str = None):
        """Update scan progress with directory-specific information."""
        self.current_count = dirs_processed

        if self.total_estimated > 0:
            progress = min(95, int((dirs_processed / self.total_estimated) * 100))
        else:
            # Fallback progress calculation
            progress = min(90, int(dirs_processed / 10))

        # Create detailed message
        detailed_message = message
        if current_dir:
            detailed_message += f"\nCurrent: {current_dir}"

        # Calculate ETA if we have enough data
        eta_text = ""
        if self.scan_start_time and dirs_processed > 5 and self.total_estimated > 0:
            import time
            elapsed = time.time() - self.scan_start_time
            rate = dirs_processed / elapsed
            remaining = self.total_estimated - dirs_processed
            if rate > 0:
                eta_seconds = int(remaining / rate)
                if eta_seconds > 60:
                    eta_text = f" (ETA: {eta_seconds//60}m {eta_seconds%60}s)"
                elif eta_seconds > 0:
                    eta_text = f" (ETA: {eta_seconds}s)"

        details = f"Processed: {dirs_processed}"
        if self.total_estimated > 0:
            details += f"/{self.total_estimated}"
        details += eta_text

        self.show_progress(detailed_message, progress, details)

    def complete_scan(self, success: bool = True, final_message: str = None):
        """Complete the scan operation."""
        if success:
            message = final_message or "Directory scan completed successfully!"
            details = f"Total directories processed: {self.current_count}"

            if self.scan_start_time:
                import time
                elapsed = time.time() - self.scan_start_time
                if elapsed > 1:
                    details += f" in {elapsed:.1f}s"

            self.show_progress(message, 100, details)
        else:
            error_message = final_message or "Directory scan failed"
            self.show_progress(error_message, 0, "Please check the directory path and permissions")

        self.set_scan_mode(False)


class SearchWidget(QWidget):
    """Widget for directory search functionality."""

    # Signals
    search_requested = pyqtSignal(str)
    search_cleared = pyqtSignal()

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setup_ui()

    def setup_ui(self):
        """Setup search widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Search label
        search_label = QLabel("Search:")
        search_label.setFont(QFont(*self.config.fonts.get_font_tuple()))

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setFont(QFont(*self.config.fonts.get_font_tuple(10)))
        self.search_input.setPlaceholderText("Enter directory name or pattern...")
        self.search_input.textChanged.connect(self._on_text_changed)
        self.search_input.returnPressed.connect(self._on_search_requested)

        # Search button
        self.search_button = QPushButton("Search")
        self.search_button.setFont(QFont(*self.config.fonts.get_font_tuple()))
        self.search_button.clicked.connect(self._on_search_requested)

        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.setFont(QFont(*self.config.fonts.get_font_tuple()))
        self.clear_button.clicked.connect(self._on_clear_requested)
        self.clear_button.setEnabled(False)

        layout.addWidget(search_label)
        layout.addWidget(self.search_input)
        layout.addWidget(self.search_button)
        layout.addWidget(self.clear_button)

    def _on_text_changed(self, text: str):
        """Handle search text changes."""
        self.clear_button.setEnabled(bool(text))
        if not text:
            self.search_cleared.emit()

    def _on_search_requested(self):
        """Handle search request."""
        query = self.search_input.text().strip()
        if query:
            self.search_requested.emit(query)

    def _on_clear_requested(self):
        """Handle clear request."""
        self.search_input.clear()
        self.search_cleared.emit()

    def set_search_text(self, text: str):
        """Set search text programmatically."""
        self.search_input.setText(text)


class MemoDialog(QDialog):
    """Dialog for adding/editing directory memos."""

    def __init__(self, config: AppConfig, dir_path: Path, existing_memo: Optional[Memo] = None, parent=None):
        super().__init__(parent)
        self.config = config
        self.dir_path = dir_path
        self.existing_memo = existing_memo
        self.setup_ui()

    def setup_ui(self):
        """Setup memo dialog UI."""
        self.setWindowTitle("Add/Edit Memo")
        self.resize(500, 300)
        self.setFont(QFont(*self.config.fonts.get_font_tuple()))

        layout = QVBoxLayout(self)

        # Directory path label
        path_label = QLabel(f"Directory: {self.dir_path.name}")
        path_label.setWordWrap(True)
        path_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(path_label)

        # Full path label
        full_path_label = QLabel(f"Full Path: {self.dir_path}")
        full_path_label.setWordWrap(True)
        full_path_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(full_path_label)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # Memo input label
        memo_label = QLabel("Enter memo:")
        memo_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(memo_label)

        # Memo text input
        self.memo_input = QTextEdit()
        self.memo_input.setFont(QFont(*self.config.fonts.get_font_tuple(10)))

        # Set existing memo text
        if self.existing_memo:
            self.memo_input.setPlainText(self.existing_memo.text)

        layout.addWidget(self.memo_input)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Focus on text input
        self.memo_input.setFocus()

    def get_memo_text(self) -> str:
        """Get the memo text from the dialog."""
        return self.memo_input.toPlainText().strip()


class MemoViewerDialog(QDialog):
    """Dialog for viewing directory memo details."""

    def __init__(self, config: AppConfig, dir_path: Path, memo: Memo, parent=None):
        super().__init__(parent)
        self.config = config
        self.dir_path = dir_path
        self.memo = memo
        self.setup_ui()

    def setup_ui(self):
        """Setup memo viewer dialog UI."""
        self.setWindowTitle("View Memo")
        self.resize(600, 400)
        self.setFont(QFont(*self.config.fonts.get_font_tuple()))

        layout = QVBoxLayout(self)

        # Directory info
        dir_label = QLabel(f"Directory: {self.dir_path.name}")
        dir_label.setWordWrap(True)
        dir_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(dir_label)

        full_path_label = QLabel(f"Full Path: {self.dir_path}")
        full_path_label.setWordWrap(True)
        full_path_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(full_path_label)

        # Memo metadata
        metadata_text = f"Added by: {self.memo.user}\nDate: {self.memo.formatted_timestamp}"
        if self.memo.category:
            metadata_text += f"\nCategory: {self.memo.category}"
        if self.memo.tags:
            metadata_text += f"\nTags: {', '.join(self.memo.tags)}"

        metadata_label = QLabel(metadata_text)
        metadata_label.setStyleSheet("color: blue; font-size: 11px;")
        layout.addWidget(metadata_label)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # Memo content
        memo_label = QLabel("Memo:")
        memo_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(memo_label)

        memo_text_widget = QTextEdit()
        memo_text_widget.setReadOnly(True)
        memo_text_widget.setPlainText(self.memo.text)
        memo_text_widget.setStyleSheet("background-color: #f5f5f5;")
        memo_text_widget.setFont(QFont(*self.config.fonts.get_font_tuple(10)))
        layout.addWidget(memo_text_widget)

        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.accept)
        layout.addWidget(button_box)


class StatusWidget(QWidget):
    """Widget for displaying application status and help information."""

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setup_ui()

    def setup_ui(self):
        """Setup status widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Help label
        self.help_label = QLabel(
            ""
        )
        self.help_label.setFont(QFont(*self.config.fonts.get_font_tuple(8)))
        self.help_label.setStyleSheet(f"color: {self.config.colors.olive_green};")
        self.help_label.setWordWrap(True)
        self.help_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Depth status label
        self.depth_label = QLabel("Current Depth: 0/0")
        self.depth_label.setFont(QFont(*self.config.fonts.get_font_tuple(8)))
        self.depth_label.setStyleSheet("color: black;")
        self.depth_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        layout.addWidget(self.help_label, stretch=1)
        layout.addWidget(self.depth_label, stretch=0)

    def update_depth_status(self, current_depth: int, max_depth: int):
        """Update depth status display."""
        self.depth_label.setText(f"(current depth : {current_depth} / {max_depth})")

    def set_help_text(self, text: str):
        """Set help text."""
        self.help_label.setText(text)


class FilterControlWidget(QWidget):
    """Widget for directory filtering controls."""

    # Signals
    user_filter_toggled = pyqtSignal(bool)
    sort_order_changed = pyqtSignal(str)  # "mtime" or "name"

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setup_ui()

    def setup_ui(self):
        """Setup filter control UI."""
        layout = QHBoxLayout(self)
        layout.setSpacing(self.config.ui.button_spacing)

        # Set directory label
        set_dir_label = QLabel("Set Dir:")
        set_dir_label.setFont(QFont(*self.config.fonts.get_font_tuple()))
        set_dir_label.setFixedWidth(60)
        layout.addWidget(set_dir_label)

        # User filter button
        self.user_filter_button = QPushButton("All users")
        self.user_filter_button.setFont(QFont(*self.config.fonts.get_font_tuple()))
        self.user_filter_button.setFixedWidth(85)
        self.user_filter_button.setCheckable(True)
        self.user_filter_button.setStyleSheet("background-color: #00493A; color: white;")
        self.user_filter_button.toggled.connect(self._on_user_filter_toggled)
        layout.addWidget(self.user_filter_button)

        # Sort order button
        self.sort_button = QPushButton("mTime")
        self.sort_button.setFont(QFont(*self.config.fonts.get_font_tuple()))
        self.sort_button.setFixedWidth(self.config.ui.depth_button_width)
        self.sort_button.setCheckable(True)
        self.sort_button.setChecked(True)
        self.sort_button.setStyleSheet(f"background-color: {self.config.colors.tan}; color: white;")
        self.sort_button.toggled.connect(self._on_sort_toggled)
        layout.addWidget(self.sort_button)

        # Add stretch to fill remaining space
        layout.addStretch()

    def _on_user_filter_toggled(self, checked: bool):
        """Handle user filter toggle."""
        if checked:
            self.user_filter_button.setStyleSheet(f"background-color: {self.config.colors.ebony}; color: white;")
            self.user_filter_button.setText("Me only")
        else:
            self.user_filter_button.setStyleSheet("background-color: #00493A; color: white;")
            self.user_filter_button.setText("All users")

        self.user_filter_toggled.emit(checked)

    def _on_sort_toggled(self, checked: bool):
        """Handle sort order toggle."""
        if checked:
            sort_order = "mtime"
            self.sort_button.setText("mTime")
            self.sort_button.setStyleSheet(f"background-color: {self.config.colors.tan}; color: white;")
        else:
            sort_order = "name"
            self.sort_button.setText("Name")
            self.sort_button.setStyleSheet("background-color: #A7A88A; color: black;")

        self.sort_order_changed.emit(sort_order)


class DepthControlWidget(QWidget):
    """Widget for depth level controls."""

    # Signals
    depth_level_selected = pyqtSignal(int)

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.depth_buttons: Dict[int, QPushButton] = {}
        self.current_depth = 0
        self.setup_ui()

    def setup_ui(self):
        """Setup depth control UI."""
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)

    def update_depth_buttons(self, max_depth: int):
        """Update depth buttons based on maximum depth."""
        # Clear existing buttons
        for button in self.depth_buttons.values():
            button.deleteLater()
        self.depth_buttons.clear()

        # Create new buttons
        for level in range(max_depth + 1):
            button = QPushButton(str(level))
            button.setFont(QFont(*self.config.fonts.get_font_tuple()))
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.setStyleSheet("background-color: #4B4B4B; color: white;")
            button.clicked.connect(lambda checked, l=level: self._on_depth_selected(l))

            self.layout.addWidget(button, stretch=1)
            self.depth_buttons[level] = button

    def _on_depth_selected(self, level: int):
        """Handle depth level selection."""
        self.current_depth = level
        self.update_button_styles()
        self.depth_level_selected.emit(level)

    def update_button_styles(self):
        """Update button styles based on current depth."""
        for level, button in self.depth_buttons.items():
            if level == self.current_depth:
                button.setStyleSheet("background-color: #4B4B4B; color: black;")
            else:
                button.setStyleSheet("background-color: #4B4B4B; color: white;")

    def set_current_depth(self, depth: int):
        """Set current depth programmatically."""
        self.current_depth = depth
        self.update_button_styles()


class ConfirmationDialog(QDialog):
    """Enhanced confirmation dialog with detailed options."""

    def __init__(self, title: str, message: str, items: List[str] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.items = items or []
        self.setup_ui(message)

    def setup_ui(self, message: str):
        """Setup confirmation dialog UI."""
        layout = QVBoxLayout(self)

        # Main message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(message_label)

        # Items list (if provided)
        if self.items:
            items_label = QLabel("Items:")
            items_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            layout.addWidget(items_label)

            items_text = QTextEdit()
            items_text.setReadOnly(True)
            items_text.setMaximumHeight(150)
            items_text.setPlainText('\n'.join(self.items))
            items_text.setStyleSheet("background-color: #f5f5f5; font-size: 10px;")
            layout.addWidget(items_text)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Yes | QDialogButtonBox.No
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Set default focus to No button for safety
        button_box.button(QDialogButtonBox.No).setDefault(True)
        button_box.button(QDialogButtonBox.No).setFocus()

    @staticmethod
    def confirm_operation(title: str, message: str, items: List[str] = None, parent=None) -> bool:
        """Static method for quick confirmation dialogs."""
        dialog = ConfirmationDialog(title, message, items, parent)
        return dialog.exec_() == QDialog.Accepted


class UpdatedDirectoriesWidget(QWidget):
    """Widget showing recently updated directories with navigation buttons."""

    # Signals
    navigate_requested = pyqtSignal(Path)
    cleared = pyqtSignal()

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.updated_paths: List[Path] = []
        self.setup_ui()
        self.hide()  # Hidden by default

    def setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)

        # Header with title and clear button
        header_layout = QHBoxLayout()

        self.title_label = QLabel("? Updated Directories (0)")
        self.title_label.setFont(QFont(*self.config.fonts.get_font_tuple(10)))
        self.title_label.setStyleSheet("""
            color: #051537;
            font-weight: bold;
            background-color: #E8F4F8;
            padding: 4px 8px;
            border-radius: 3px;
        """)

        self.clear_button = QPushButton("Clear")
        self.clear_button.setFont(QFont(*self.config.fonts.get_font_tuple(8)))
        self.clear_button.setFixedSize(60, 22)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #7B7B7B;
                color: white;
                border: none;
                border-radius: 2px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #999999;
            }
        """)
        self.clear_button.clicked.connect(self.clear_updates)

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.clear_button)

        layout.addLayout(header_layout)

        # Scroll area for directory buttons
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(120)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #CCCCCC;
                background-color: #FAFAFA;
                border-radius: 3px;
            }
        """)

        # Container for buttons
        self.buttons_widget = QWidget()
        self.buttons_layout = QVBoxLayout(self.buttons_widget)
        self.buttons_layout.setContentsMargins(3, 3, 3, 3)
        self.buttons_layout.setSpacing(2)
        self.buttons_layout.addStretch()

        scroll.setWidget(self.buttons_widget)
        layout.addWidget(scroll)

        # Style the main widget
        self.setStyleSheet("""
            UpdatedDirectoriesWidget {
                background-color: #F0F8FF;
                border: 2px solid #43B0F1;
                border-radius: 5px;
            }
        """)

    def set_updated_directories(self, paths: List[Path]):
        """Set the list of updated directories."""
        self.updated_paths = paths
        self.update_display()

        if paths:
            self.show()
        else:
            self.hide()

    def update_display(self):
        """Update the display of updated directories."""
        # Clear existing buttons
        while self.buttons_layout.count() > 1:  # Keep the stretch
            item = self.buttons_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Update title
        count = len(self.updated_paths)
        self.title_label.setText(f"? Updated Directories ({count})")

        # Create buttons for each updated directory
        for i, path in enumerate(self.updated_paths):
            self.add_directory_button(path, i)

    def add_directory_button(self, path: Path, index: int):
        """Add a button for a directory."""
        button_frame = QFrame()
        button_frame.setFrameStyle(QFrame.StyledPanel)
        button_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #D0D0D0;
                border-radius: 3px;
                margin: 1px;
            }
            QFrame:hover {
                background-color: #E8F4F8;
                border: 1px solid #43B0F1;
            }
        """)

        frame_layout = QHBoxLayout(button_frame)
        frame_layout.setContentsMargins(5, 3, 5, 3)

        # Directory name label with path info
        dir_label = QLabel(self.format_path_display(path))
        dir_label.setFont(QFont(*self.config.fonts.get_font_tuple(9)))
        dir_label.setStyleSheet("color: #31352e; border: none;")
        dir_label.setToolTip(str(path))
        dir_label.setWordWrap(True)


        # Go button
        go_button = QPushButton("Go >")
        go_button.setFont(QFont(*self.config.fonts.get_font_tuple(7)))  # Smaller font size
        go_button.setFixedSize(35, 16)  # Thinner button size (width x height)
        go_button.setStyleSheet("""
            QPushButton {
                background-color: #43B0F1;
                color: white;
                border: none;
                border-radius: 2px;
                font-weight: normal;  /* Changed from bold to normal */
                padding: 0px 4px;     /* Minimal padding to keep it thin */
            }
            QPushButton:hover {
                background-color: #2A90D1;
            }
        """)


        go_button.clicked.connect(lambda checked, p=path: self.navigate_to_path(p))

        frame_layout.addWidget(dir_label, stretch=1)
        frame_layout.addWidget(go_button)

        self.buttons_layout.insertWidget(index, button_frame)

    def format_path_display(self, path: Path) -> str:
        """Format path for display (show last 3-4 components)."""
        parts = path.parts
        if len(parts) > 4:
            return ".../" + "/".join(parts[-4:])
        return str(path)

    def navigate_to_path(self, path: Path):
        """Navigate to a specific path."""
        self.navigate_requested.emit(path)

    def clear_updates(self):
        """Clear all updated directories."""
        self.updated_paths.clear()
        self.update_display()
        self.hide()
        self.cleared.emit()

    def has_updates(self) -> bool:
        """Check if there are any updates."""
        return len(self.updated_paths) > 0
