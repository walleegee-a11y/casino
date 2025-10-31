"""
Widget for displaying and navigating to updated directories after refresh.
"""

from pathlib import Path
from typing import List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ..config.settings import AppConfig


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
        go_button = QPushButton("Go ?")
        go_button.setFont(QFont(*self.config.fonts.get_font_tuple(8)))
        go_button.setFixedSize(50, 20)
        go_button.setStyleSheet("""
            QPushButton {
                background-color: #43B0F1;
                color: white;
                border: none;
                border-radius: 2px;
                font-weight: bold;
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
