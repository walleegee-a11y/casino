#! /usr/local/bin/python3.12 -u

import os
import sys
import shutil
import yaml
import getpass
import re
import subprocess
import tempfile
import logging
import difflib
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QAbstractItemView, QTextEdit, QComboBox, QPushButton,
    QFileDialog, QCheckBox, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QGroupBox, QDateEdit, QFormLayout, QTimeEdit,
    QScrollArea, QShortcut, QTabWidget, QTextBrowser, QFrame, QSizePolicy,
    QSplitter
)
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtGui import QColor, QFont, QKeySequence
from PyQt5.QtCore import Qt, QDate, QTime

# Set default application font
DEFAULT_FONT = QFont("Terminus", 8)  # Updated to size 8
QApplication.setFont(DEFAULT_FONT)

# Classical professional button colors
BUTTON_STYLES = {
    "default": {
        "background": "#F5F5F5",  # Off-white
        "border": "#BEBEBE",      # Gray
        "hover": "#E8E8E8",
        "pressed": "#D8D8D8"
    },
    "action": {
        "background": "#4A90E2",  # Professional Blue
        "border": "#357ABD",
        "hover": "#5A9FF2",
        "pressed": "#3A80D2",
        "text": "#FFFFFF"
    },
    "danger": {
        "background": "#DC3545",  # Muted Red
        "border": "#BD2130",
        "hover": "#E04555",
        "pressed": "#CC2535",
        "text": "#FFFFFF"
    },
    "gray": {
        "background": "#E0E0E0",  # Medium Gray
        "border": "#BEBEBE",
        "hover": "#D0D0D0",
        "pressed": "#C0C0C0"
    },
    "blue": {
        "background": "#5B9BD5",  # Classic Blue
        "border": "#4A7FB5",
        "hover": "#6BABE5",
        "pressed": "#4B8BC5",
        "text": "#FFFFFF"
    },
    "success": {
        "background": "#28A745",  # Green
        "border": "#1E7E34",
        "hover": "#38B755",
        "pressed": "#1E8E3E",
        "text": "#FFFFFF"
    }
}

def style_button(button, style_type="default"):
    """Apply consistent professional button styling"""
    style = BUTTON_STYLES[style_type]
    text_color = style.get('text', '#000000')  # Default to black text
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {style['background']};
            border: 1px solid {style['border']};
            border-radius: 2px;
            padding: 4px 8px;
            color: {text_color};
            font-family: Terminus;
            font-size: 8pt;
        }}
        QPushButton:hover {{
            background-color: {style['hover']};
        }}
        QPushButton:pressed {{
            background-color: {style['pressed']};
        }}
        QPushButton:disabled {{
            background-color: #F0F0F0;
            border: 1px solid #E0E0E0;
            color: #A0A0A0;
        }}
    """)

# File extension sets
TEXT_EXTS = {'.txt', '.py', '.c', '.cpp', '.h', '.hpp', '.log', '.rpt',
             '.yaml', '.yml', '.json', '.md', '.cfg', '.conf', '.csh',
             '.ini', '.xml', '.csv'}
IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'}


class RichTextDescriptionEditor(QDialog):
    """Rich text WYSIWYG editor with interactive checkboxes and tables"""

    def __init__(self, current_description, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Description")
        self.setMinimumSize(1000, 650)

        layout = QVBoxLayout()

        # Rich text editor (single view, WYSIWYG)
        self.editor = QTextEdit()
        self.editor.setAcceptRichText(True)

        # Load content - try HTML first, fall back to plain text
        if current_description.strip().startswith('<'):
            self.editor.setHtml(current_description)
        else:
            # Convert markdown to HTML or use as plain text
            self.editor.setPlainText(current_description)

        self.editor.textChanged.connect(self.on_text_changed)

        # Install event filter for checkbox clicking and keyboard shortcuts
        self.editor.viewport().installEventFilter(self)  # For mouse clicks
        self.editor.installEventFilter(self)  # For keyboard (Tab/Shift+Tab)

        layout.addWidget(self.editor)

        # Formatting toolbar
        toolbar1 = QHBoxLayout()
        toolbar2 = QHBoxLayout()

        # Row 1: Text formatting
        btn_bold = QPushButton("[B] Bold")
        btn_bold.setMaximumWidth(90)
        btn_bold.clicked.connect(self.toggle_bold)
        style_button(btn_bold, "default")

        btn_italic = QPushButton("[I] Italic")
        btn_italic.setMaximumWidth(90)
        btn_italic.clicked.connect(self.toggle_italic)
        style_button(btn_italic, "default")

        btn_underline = QPushButton("[U] Underline")
        btn_underline.setMaximumWidth(100)
        btn_underline.clicked.connect(self.toggle_underline)
        style_button(btn_underline, "default")

        btn_color = QPushButton("[Color]")
        btn_color.setMaximumWidth(80)
        btn_color.clicked.connect(self.change_text_color)
        style_button(btn_color, "default")

        # Font size combo
        self.font_size_combo = QComboBox()
        self.font_size_combo.addItems(["8", "10", "12", "14", "16", "18", "20", "24"])
        self.font_size_combo.setCurrentText("10")
        self.font_size_combo.setMaximumWidth(60)
        self.font_size_combo.currentTextChanged.connect(self.change_font_size)

        toolbar1.addWidget(QLabel("Format:"))
        toolbar1.addWidget(btn_bold)
        toolbar1.addWidget(btn_italic)
        toolbar1.addWidget(btn_underline)
        toolbar1.addWidget(btn_color)
        toolbar1.addWidget(QLabel("Size:"))
        toolbar1.addWidget(self.font_size_combo)
        toolbar1.addStretch()

        # Stats label
        self.stats_label = QLabel()
        self.update_stats()
        toolbar1.addWidget(self.stats_label)

        # Row 2: Lists, tables, and checkboxes
        btn_bullet = QPushButton("[-] Bullet List")
        btn_bullet.setMaximumWidth(110)
        btn_bullet.clicked.connect(self.insert_bullet_list)
        style_button(btn_bullet, "default")

        btn_numbered = QPushButton("[1] Numbered List")
        btn_numbered.setMaximumWidth(130)
        btn_numbered.clicked.connect(self.insert_numbered_list)
        style_button(btn_numbered, "default")

        btn_checkbox = QPushButton("[ ] Task Item")
        btn_checkbox.setMaximumWidth(110)
        btn_checkbox.clicked.connect(self.insert_checkbox)
        style_button(btn_checkbox, "default")

        btn_table = QPushButton("[Table]")
        btn_table.setMaximumWidth(80)
        btn_table.clicked.connect(self.insert_table)
        style_button(btn_table, "default")

        btn_clear = QPushButton("[Clear Format]")
        btn_clear.setMaximumWidth(110)
        btn_clear.clicked.connect(self.clear_formatting)
        style_button(btn_clear, "gray")

        toolbar2.addWidget(btn_bullet)
        toolbar2.addWidget(btn_numbered)
        toolbar2.addWidget(btn_checkbox)
        toolbar2.addWidget(btn_table)
        toolbar2.addWidget(btn_clear)
        toolbar2.addStretch()

        layout.addLayout(toolbar1)
        layout.addLayout(toolbar2)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("[Save]")
        btn_save.clicked.connect(self.accept)
        style_button(btn_save, "success")

        btn_cancel = QPushButton("[Cancel]")
        btn_cancel.clicked.connect(self.reject)
        style_button(btn_cancel, "gray")

        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def eventFilter(self, obj, event):
        """Handle mouse clicks on checkboxes to toggle them, and keyboard shortcuts"""
        from PyQt5.QtCore import QEvent, Qt
        from PyQt5.QtGui import QMouseEvent, QTextCursor, QKeyEvent

        # Handle keyboard events for Tab/Shift+Tab in lists and Enter for checkboxes
        if obj == self.editor and event.type() == QEvent.KeyPress:
            if isinstance(event, QKeyEvent):
                cursor = self.editor.textCursor()
                current_list = cursor.currentList()

                # Handle Tab - indent list item OR checkbox line
                if event.key() == Qt.Key_Tab:
                    # Check if in a list
                    if current_list:
                        cursor.beginEditBlock()
                        list_format = current_list.format()
                        list_format.setIndent(list_format.indent() + 1)
                        current_list.setFormat(list_format)
                        cursor.endEditBlock()
                        return True
                    else:
                        # Check if on a checkbox line
                        cursor.select(QTextCursor.LineUnderCursor)
                        line_text = cursor.selectedText()
                        cursor.clearSelection()
                        stripped = line_text.lstrip()
                        if stripped.startswith('[ ] ') or stripped.startswith('[v] '):
                            # Add indent to checkbox line
                            cursor = self.editor.textCursor()
                            cursor.movePosition(QTextCursor.StartOfBlock)
                            cursor.insertText("  ")  # Add 2 spaces indent
                            return True

                # Handle Shift+Tab - outdent list item OR checkbox line
                if event.key() == Qt.Key_Backtab:
                    # Check if in a list
                    if current_list:
                        cursor.beginEditBlock()
                        list_format = current_list.format()
                        if list_format.indent() > 0:
                            list_format.setIndent(list_format.indent() - 1)
                            current_list.setFormat(list_format)
                        cursor.endEditBlock()
                        return True
                    else:
                        # Check if on a checkbox line
                        cursor.select(QTextCursor.LineUnderCursor)
                        line_text = cursor.selectedText()
                        cursor.clearSelection()
                        if line_text.startswith('  '):  # Has indent
                            stripped = line_text.lstrip()
                            if stripped.startswith('[ ] ') or stripped.startswith('[v] '):
                                # Remove 2 spaces indent from checkbox line
                                cursor = self.editor.textCursor()
                                cursor.movePosition(QTextCursor.StartOfBlock)
                                cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 2)
                                if cursor.selectedText() == "  ":
                                    cursor.removeSelectedText()
                                return True

                # Handle Enter for checkbox auto-continuation
                if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                    # Get current line text
                    cursor.select(QTextCursor.LineUnderCursor)
                    line_text = cursor.selectedText()
                    cursor.clearSelection()

                    # Check if line starts with checkbox pattern
                    stripped = line_text.lstrip()
                    if stripped.startswith('[ ] ') or stripped.startswith('[v] '):
                        # Get indentation of current line
                        indent = line_text[:len(line_text) - len(stripped)]

                        # Check if checkbox line is empty (just checkbox, no text)
                        checkbox_content = stripped[4:].strip()  # Text after "[ ] " or "[v] "

                        if not checkbox_content:
                            # Empty checkbox line - exit checkbox mode (don't create next)
                            # Just insert normal newline
                            cursor = self.editor.textCursor()
                            cursor.insertText("\n")
                            return True
                        else:
                            # Non-empty checkbox line - auto-create next checkbox
                            cursor = self.editor.textCursor()
                            cursor.insertText("\n" + indent + "[ ] ")
                            return True

        # Handle mouse clicks on checkboxes
        if obj == self.editor.viewport() and event.type() == QEvent.MouseButtonRelease:
            if isinstance(event, QMouseEvent):
                # Get cursor position at click
                cursor = self.editor.cursorForPosition(event.pos())

                # Get current line text
                cursor.select(QTextCursor.LineUnderCursor)
                line_text = cursor.selectedText()
                cursor.clearSelection()

                # Get cursor position within the line
                line_start_pos = cursor.block().position()
                click_pos = self.editor.cursorForPosition(event.pos()).position()
                pos_in_line = click_pos - line_start_pos

                # Check for checkbox patterns "[ ]" or "[v]" near click position
                # Look for pattern within 3 characters of click
                for i in range(max(0, pos_in_line - 3), min(len(line_text) - 2, pos_in_line + 3)):
                    if i + 2 < len(line_text):
                        pattern = line_text[i:i+3]
                        if pattern == '[ ]' or pattern == '[v]':
                            # Found checkbox pattern near click - toggle it
                            new_pattern = '[v]' if pattern == '[ ]' else '[ ]'

                            # Replace the pattern
                            cursor = self.editor.textCursor()
                            cursor.setPosition(line_start_pos + i)
                            cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 3)
                            cursor.insertText(new_pattern)

                            # Don't auto-create next checkbox
                            # User will press Enter and click button again if they want more

                            return True  # Event handled

        return super().eventFilter(obj, event)

    def on_text_changed(self):
        """Update stats on text change"""
        self.update_stats()

    def update_stats(self):
        """Update character and word count"""
        text = self.editor.toPlainText()
        char_count = len(text)
        word_count = len(text.split())
        line_count = len(text.splitlines())
        self.stats_label.setText(
            f"Stats: {char_count} chars, {word_count} words, {line_count} lines"
        )

    def toggle_bold(self):
        """Toggle bold formatting"""
        fmt = self.editor.currentCharFormat()
        fmt.setFontWeight(QFont.Normal if fmt.fontWeight() == QFont.Bold else QFont.Bold)
        self.editor.mergeCurrentCharFormat(fmt)
        self.editor.setFocus()

    def toggle_italic(self):
        """Toggle italic formatting"""
        fmt = self.editor.currentCharFormat()
        fmt.setFontItalic(not fmt.fontItalic())
        self.editor.mergeCurrentCharFormat(fmt)
        self.editor.setFocus()

    def toggle_underline(self):
        """Toggle underline formatting"""
        fmt = self.editor.currentCharFormat()
        fmt.setFontUnderline(not fmt.fontUnderline())
        self.editor.mergeCurrentCharFormat(fmt)
        self.editor.setFocus()

    def change_text_color(self):
        """Open color picker and change text color"""
        from PyQt5.QtWidgets import QColorDialog
        color = QColorDialog.getColor()
        if color.isValid():
            fmt = self.editor.currentCharFormat()
            fmt.setForeground(color)
            self.editor.mergeCurrentCharFormat(fmt)
        self.editor.setFocus()

    def change_font_size(self, size):
        """Change font size"""
        try:
            fmt = self.editor.currentCharFormat()
            fmt.setFontPointSize(int(size))
            self.editor.mergeCurrentCharFormat(fmt)
        except ValueError:
            pass
        self.editor.setFocus()

    def insert_bullet_list(self):
        """Insert or toggle bullet list"""
        from PyQt5.QtGui import QTextListFormat
        cursor = self.editor.textCursor()
        list_format = QTextListFormat()
        list_format.setStyle(QTextListFormat.ListDisc)
        cursor.insertList(list_format)
        self.editor.setFocus()

    def insert_numbered_list(self):
        """Insert or toggle numbered list"""
        from PyQt5.QtGui import QTextListFormat
        cursor = self.editor.textCursor()
        list_format = QTextListFormat()
        list_format.setStyle(QTextListFormat.ListDecimal)
        cursor.insertList(list_format)
        self.editor.setFocus()

    def insert_checkbox(self):
        """Insert an interactive checkbox (plain text, no bullet)"""
        cursor = self.editor.textCursor()

        # Just insert checkbox at current position (no list structure)
        # This avoids the bullet marker
        cursor.insertText("[ ] ")

        self.editor.setFocus()

    def insert_table(self):
        """Insert a table"""
        from PyQt5.QtWidgets import QInputDialog

        # Ask for dimensions
        rows, ok1 = QInputDialog.getInt(self, "Insert Table", "Number of rows:", 3, 1, 20)
        if not ok1:
            return

        cols, ok2 = QInputDialog.getInt(self, "Insert Table", "Number of columns:", 3, 1, 10)
        if not ok2:
            return

        cursor = self.editor.textCursor()

        # Create table format
        from PyQt5.QtGui import QTextTableFormat, QTextLength
        table_format = QTextTableFormat()
        table_format.setBorder(1)
        table_format.setCellPadding(4)
        table_format.setCellSpacing(0)
        table_format.setWidth(QTextLength(QTextLength.PercentageLength, 100))

        # Insert table
        table = cursor.insertTable(rows, cols, table_format)
        self.editor.setFocus()

    def clear_formatting(self):
        """Clear all formatting from selected text"""
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            # Create plain format
            from PyQt5.QtGui import QTextCharFormat
            plain_format = QTextCharFormat()
            cursor.mergeCharFormat(plain_format)
        self.editor.setFocus()

    def get_description(self):
        """Get the edited description as plain text"""
        return self.editor.toPlainText()

    def get_description_html(self):
        """Get the edited description as HTML"""
        return self.editor.toHtml()

    def get_description_markdown(self):
        """Convert HTML to markdown for backward compatibility"""
        try:
            import html2text
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = False
            h.body_width = 0  # Don't wrap lines
            html = self.editor.toHtml()
            markdown_text = h.handle(html)
            return markdown_text.strip()
        except ImportError:
            # Fallback to plain text if html2text not installed
            return self.editor.toPlainText()


# Keep old class name as alias for backward compatibility
MarkdownDescriptionEditor = RichTextDescriptionEditor


class DescriptionHistoryDialog(QDialog):
    """Enhanced history dialog with visual diffs, timeline view, and version restoration"""

    def __init__(self, issue_data, yaml_path, parent=None):
        super().__init__(parent)
        self.issue_data = issue_data
        self.yaml_path = yaml_path
        self.current_description = issue_data.get('description', '')
        self.current_description_html = issue_data.get('description_html', '')
        self.history = issue_data.get('description_history', [])

        self.setWindowTitle(f"Description History - {issue_data.get('id', '')}")
        self.setMinimumSize(950, 700)

        layout = QVBoxLayout()

        # Header with search and info
        header_layout = QHBoxLayout()
        title_label = QLabel(f"<b>Change History ({len(self.history)} versions)</b>")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search history...")
        self.search_box.setMaximumWidth(250)
        self.search_box.textChanged.connect(self.filter_history)
        header_layout.addWidget(self.search_box)

        layout.addLayout(header_layout)

        # Horizontal splitter for 3-column layout
        splitter = QSplitter(Qt.Horizontal)

        # Left panel: Version list
        self.version_list = QListWidget()
        self.version_list.setMinimumWidth(200)
        self.version_list.setMaximumWidth(350)
        self.version_list.setStyleSheet("""
            QListWidget {
                background-color: #f6f8fa;
                border: 1px solid #d0d7de;
                border-radius: 6px;
                font-size: 10px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #d0d7de;
            }
            QListWidget::item:hover {
                background-color: #e6f2ff;
                color: #000000;
            }
            QListWidget::item:selected {
                background-color: #0969da;
                color: white;
            }
            QListWidget::item:selected:hover {
                background-color: #0550ae;
                color: white;
            }
        """)
        self.version_list.currentRowChanged.connect(self.on_version_selected)

        # Middle panel: Current version (always visible)
        middle_panel = QWidget()
        middle_layout = QVBoxLayout(middle_panel)
        middle_layout.setContentsMargins(5, 0, 5, 0)

        # Current version header
        current_header = QLabel("[CURRENT] Version")
        current_header.setStyleSheet("""
            QLabel {
                background-color: #28a745;
                color: white;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        current_header.setAlignment(Qt.AlignCenter)
        middle_layout.addWidget(current_header)

        # Current version content
        self.current_display = QTextBrowser()
        self.current_display.setStyleSheet("""
            QTextBrowser {
                background-color: #f0fff4;
                border: 2px solid #28a745;
                border-radius: 6px;
                padding: 12px;
                font-family: 'Consolas', monospace;
                font-size: 10px;
            }
        """)
        # Display HTML if available, otherwise plain text
        if self.current_description_html:
            self.current_display.setHtml(self.current_description_html)
        else:
            self.current_display.setPlainText(self.current_description)
        middle_layout.addWidget(self.current_display)

        # Right panel: Selected version viewer
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 0, 0, 0)

        # Selected version info header
        self.info_label = QLabel("Select a version from the list")
        self.info_label.setStyleSheet("""
            QLabel {
                background-color: #0969da;
                color: white;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setWordWrap(True)
        right_layout.addWidget(self.info_label)

        # Selected version content display
        self.content_display = QTextBrowser()
        self.content_display.setStyleSheet("""
            QTextBrowser {
                background-color: white;
                border: 1px solid #d0d7de;
                border-radius: 6px;
                padding: 12px;
                font-family: 'Consolas', monospace;
                font-size: 10px;
            }
        """)
        right_layout.addWidget(self.content_display)

        # Action buttons for selected version
        action_layout = QHBoxLayout()

        self.btn_restore_version = QPushButton("[Restore] Selected")
        self.btn_restore_version.setEnabled(False)
        style_button(self.btn_restore_version, "blue")
        self.btn_restore_version.clicked.connect(self.on_restore_clicked)

        self.btn_show_full_diff = QPushButton("[Toggle] Diff/Full")
        self.btn_show_full_diff.setEnabled(False)
        style_button(self.btn_show_full_diff, "action")
        self.btn_show_full_diff.clicked.connect(self.on_toggle_diff)

        action_layout.addWidget(self.btn_show_full_diff)
        action_layout.addWidget(self.btn_restore_version)
        action_layout.addStretch()

        right_layout.addLayout(action_layout)

        # Add panels to splitter (3 columns)
        splitter.addWidget(self.version_list)
        splitter.addWidget(middle_panel)
        splitter.addWidget(right_panel)

        # Set relative sizes: List=1, Current=2, Selected=2
        splitter.setStretchFactor(0, 1)  # Version list
        splitter.setStretchFactor(1, 2)  # Current version (middle)
        splitter.setStretchFactor(2, 2)  # Selected version (right)

        layout.addWidget(splitter)

        # Populate version list
        self.showing_diff = True  # Track whether showing diff or full text
        self.populate_version_list()

        # Bottom buttons
        btn_layout = QHBoxLayout()

        btn_export = QPushButton("[Export] History")
        btn_export.clicked.connect(self.export_history)
        style_button(btn_export, "action")

        btn_close = QPushButton("[Close]")
        btn_close.clicked.connect(self.close)
        style_button(btn_close, "gray")

        btn_layout.addWidget(btn_export)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def populate_version_list(self):
        """Populate version list in left panel"""
        self.version_list.clear()

        # Add current version first
        current_item = QListWidgetItem("[CURRENT] Version")
        current_item.setData(Qt.UserRole, {
            'is_current': True,
            'description': self.current_description,
            'description_html': self.current_description_html,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'user': getpass.getuser()
        })
        current_item.setBackground(QColor("#e6ffec"))
        current_item.setForeground(QColor("#28a745"))
        self.version_list.addItem(current_item)

        # Add historical versions (reverse chronological)
        for idx, entry in enumerate(reversed(self.history)):
            version_number = len(self.history) - idx
            timestamp = entry.get('timestamp', '')
            user = entry.get('user', '')
            restored_from = entry.get('restored_from')

            # Create list item text
            item_text = f"Version #{version_number}\n{timestamp}\nUser: {user}"
            if restored_from:
                item_text += f"\n[Restored]"

            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.UserRole, {
                'is_current': False,
                'version_number': version_number,
                'entry': entry,
                'description': entry.get('old_description', ''),
                'description_html': entry.get('old_description_html', ''),
                'timestamp': timestamp,
                'user': user,
                'restored_from': restored_from
            })
            self.version_list.addItem(list_item)

        # Select first historical version by default (to show comparison)
        # Current version is always visible in middle panel
        if self.version_list.count() > 1:
            self.version_list.setCurrentRow(1)  # First historical version
        elif self.version_list.count() > 0:
            self.version_list.setCurrentRow(0)  # Current version if no history

    def on_version_selected(self, row):
        """Handle version selection from list (3-column view)"""
        if row < 0 or row >= self.version_list.count():
            return

        item = self.version_list.item(row)
        data = item.data(Qt.UserRole)

        if data['is_current']:
            # Current version selected - show info in right panel
            self.info_label.setText(
                f"[CURRENT] Version Selected\n"
                f"Time: {data['timestamp']} | User: {data['user']}"
            )
            self.btn_restore_version.setEnabled(False)
            self.btn_show_full_diff.setEnabled(False)

            # Show message in right panel
            self.content_display.setHtml("""
                <div style='text-align: center; padding: 40px; color: #666;'>
                    <h2 style='color: #28a745;'>[CURRENT] Version</h2>
                    <p>This is the active version.</p>
                    <p>The current content is displayed in the middle panel.</p>
                    <hr style='margin: 20px 0; border: 1px solid #ddd;'>
                    <p><i>Select a historical version from the list to compare with current.</i></p>
                </div>
            """)
            self.showing_diff = False

        else:
            # Historical version selected - show in right panel for comparison
            version_num = data['version_number']
            restored_info = f"\n[Restored from {data['restored_from']}]" if data['restored_from'] else ""

            self.info_label.setText(
                f"Version #{version_num} (Historical)\n"
                f"Time: {data['timestamp']} | User: {data['user']}{restored_info}"
            )
            self.btn_restore_version.setEnabled(True)
            self.btn_show_full_diff.setEnabled(True)

            # Show diff by default (comparing with current in middle panel)
            self.showing_diff = True
            self.show_version_diff(data)

        # Store current selection data for actions
        self.selected_version_data = data

    def show_version_diff(self, data):
        """Show diff for selected version"""
        old_desc = data['description']
        diff_html = self.generate_diff_html(old_desc, self.current_description, data['timestamp'])
        self.content_display.setHtml(diff_html)

    def show_version_full_text(self, data):
        """Show full text for selected version"""
        # Display HTML if available, otherwise plain text
        html = data.get('description_html', '')
        if html:
            self.content_display.setHtml(html)
        else:
            self.content_display.setPlainText(data['description'])

    def on_toggle_diff(self):
        """Toggle between diff view and full text view"""
        if not hasattr(self, 'selected_version_data'):
            return

        data = self.selected_version_data
        if data['is_current']:
            return  # No diff for current version

        self.showing_diff = not self.showing_diff

        if self.showing_diff:
            self.show_version_diff(data)
        else:
            self.show_version_full_text(data)

    def on_restore_clicked(self):
        """Restore the selected version"""
        if not hasattr(self, 'selected_version_data'):
            return

        data = self.selected_version_data
        if data['is_current']:
            return  # Can't restore current version

        # Call the existing restore_version method
        self.restore_version(data['entry'], data['version_number'])

    def generate_diff_html(self, old_text, new_text, change_time=""):
        """Generate color-coded HTML diff using difflib"""
        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()

        differ = difflib.Differ()
        diff = list(differ.compare(old_lines, new_lines))

        # Count changes
        added_count = sum(1 for line in diff if line.startswith('+ '))
        removed_count = sum(1 for line in diff if line.startswith('- '))

        html = f"""
        <style>
            body {{
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                line-height: 1.5;
            }}
            .diff-header {{
                background-color: #0969da;
                color: white;
                padding: 8px 12px;
                border-radius: 4px;
                margin-bottom: 12px;
                font-weight: bold;
            }}
            .stats {{
                font-size: 10px;
                color: #57606a;
                margin-bottom: 8px;
                padding: 6px;
                background-color: #f6f8fa;
                border-radius: 3px;
            }}
            .added {{
                background-color: #ccffd8;
                color: #116329;
                padding: 2px 6px;
                margin: 1px 0;
                border-left: 3px solid #28a745;
            }}
            .removed {{
                background-color: #ffd7d5;
                color: #82071e;
                padding: 2px 6px;
                margin: 1px 0;
                border-left: 3px solid #d32f2f;
            }}
            .unchanged {{
                color: #57606a;
                padding: 2px 6px;
                margin: 1px 0;
            }}
        </style>
        <div class="diff-header">Unified Diff View</div>
        <div class="stats">
            Changes: <span style="color: #28a745;">+{added_count} additions</span>,
            <span style="color: #d32f2f;">-{removed_count} deletions</span>
        </div>
        <div>
        """

        for line in diff:
            if line.startswith('- '):
                html += f"<div class='removed'>− {self.escape_html(line[2:])}</div>"
            elif line.startswith('+ '):
                html += f"<div class='added'>+ {self.escape_html(line[2:])}</div>"
            elif line.startswith('  '):
                html += f"<div class='unchanged'>  {self.escape_html(line[2:])}</div>"
            # Skip '? ' diff hints for cleaner output

        html += "</div>"
        return html

    def escape_html(self, text):
        """Escape HTML special characters"""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#39;'))

    def restore_version(self, entry, version_number):
        """Restore a previous version with user confirmation"""
        old_description = entry.get('old_description', '')

        # Confirmation dialog
        reply = QMessageBox.question(
            self,
            "Restore Version",
            f"<b>Restore version #{version_number}?</b><br><br>"
            f"<b>Modified:</b> {entry.get('timestamp')}<br>"
            f"<b>By:</b> {entry.get('user')}<br><br>"
            f"This will create a new history entry preserving the full history.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Create new history entry for restoration
            history_entry = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'user': getpass.getuser(),
                'old_description': self.current_description,
                'restored_from': f"Version #{version_number} ({entry.get('timestamp')})"
            }

            # Update issue data
            self.issue_data['description'] = old_description
            self.issue_data['description_history'].append(history_entry)

            # Save to YAML file
            try:
                with open(self.yaml_path, 'w') as f:
                    yaml.safe_dump(self.issue_data, f)

                QMessageBox.information(
                    self,
                    "[OK] Success",
                    f"Version #{version_number} restored successfully!"
                )

                # Refresh the dialog to show new state
                self.current_description = old_description
                self.history = self.issue_data['description_history']
                self.populate_version_list()

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "[ERROR] Failed",
                    f"Failed to restore version:<br>{str(e)}"
                )

    def filter_history(self, search_text):
        """Filter version list by search text"""
        search_text = search_text.lower().strip()

        # Show/hide items based on search
        for i in range(self.version_list.count()):
            item = self.version_list.item(i)
            data = item.data(Qt.UserRole)

            if not search_text:
                # Show all if no search text
                item.setHidden(False)
            else:
                # Search in timestamp, user, and description
                timestamp = data.get('timestamp', '').lower()
                user = data.get('user', '').lower()
                description = data.get('description', '').lower()

                # Current version is always visible or check match
                if data['is_current']:
                    matches = search_text in timestamp or search_text in user or search_text in description
                else:
                    matches = (search_text in timestamp or
                              search_text in user or
                              search_text in description)

                item.setHidden(not matches)

    def export_history(self):
        """Export full history to HTML file"""
        try:
            # Create HTML export
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>History Export - {self.issue_data.get('id', '')}</title>
                <style>
                    body {{
                        font-family: -apple-system, sans-serif;
                        max-width: 1000px;
                        margin: 40px auto;
                        padding: 20px;
                        background: #f6f8fa;
                    }}
                    .header {{
                        background: #0969da;
                        color: white;
                        padding: 20px;
                        border-radius: 8px;
                        margin-bottom: 30px;
                    }}
                    .current {{
                        background: #e6ffec;
                        border: 2px solid #28a745;
                        padding: 20px;
                        border-radius: 8px;
                        margin-bottom: 20px;
                    }}
                    .version {{
                        background: white;
                        border: 1px solid #d0d7de;
                        padding: 20px;
                        border-radius: 8px;
                        margin-bottom: 20px;
                    }}
                    .version-header {{
                        font-weight: bold;
                        color: #0969da;
                        margin-bottom: 10px;
                    }}
                    .meta {{
                        color: #57606a;
                        font-size: 14px;
                        margin-bottom: 15px;
                    }}
                    pre {{
                        background: #f6f8fa;
                        padding: 15px;
                        border-radius: 6px;
                        overflow-x: auto;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Description History Export</h1>
                    <p><b>Issue ID:</b> {self.issue_data.get('id', '')}</p>
                    <p><b>Title:</b> {self.issue_data.get('title', '')}</p>
                    <p><b>Exported:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                </div>

                <div class="current">
                    <h2>[CURRENT] Version</h2>
                    <pre>{self.escape_html(self.current_description)}</pre>
                </div>
            """

            # Add history entries
            for idx, entry in enumerate(reversed(self.history)):
                version_num = len(self.history) - idx
                html_content += f"""
                <div class="version">
                    <div class="version-header">Version #{version_num}</div>
                    <div class="meta">
                        Time: {entry.get('timestamp', '')} |
                        User: {entry.get('user', '')}
                """

                if entry.get('restored_from'):
                    html_content += f" | [Restored from {entry.get('restored_from')}]"

                html_content += f"""
                    </div>
                    <pre>{self.escape_html(entry.get('old_description', ''))}</pre>
                </div>
                """

            html_content += """
            </body>
            </html>
            """

            # Save to file
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export History",
                f"history_{self.issue_data.get('id', 'unknown')}.html",
                "HTML Files (*.html)"
            )

            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(html_content)

                QMessageBox.information(
                    self,
                    "[OK] Success",
                    f"History exported successfully to:<br>{filename}"
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "[ERROR] Failed",
                f"Failed to export history:<br>{str(e)}"
            )


class FastTrackGUI(QWidget):
    STATUS_OPTIONS = ["Open", "In Progress", "Resolved", "Closed"]
    STATUS_COLORS = {
        "Open": QColor("#FFF4E6"),          # Light cream/beige
        "In Progress": QColor("#E3F2FD"),   # Light blue
        "Resolved": QColor("#E8F5E9"),      # Light green
        "Closed": QColor("#F5F5F5")         # Light gray
    }
    SEVERITY_COLORS = {
        "Critical": QColor("#D32F2F"),      # Deep Red
        "Major": QColor("#F57C00"),         # Deep Orange
        "Minor": QColor("#FBC02D"),         # Muted Yellow
        "Enhancement": QColor("#388E3C"),   # Forest Green
        "Info": QColor("#E0E0E0")           # Medium Gray
    }

    class DragDropListWidget(QListWidget):
        """Custom QListWidget with drag and drop support for files"""
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setAcceptDrops(True)
            self.setDragDropMode(QAbstractItemView.DragDrop)
            self.parent_gui = parent

        def dragEnterEvent(self, event):
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
            else:
                event.ignore()

        def dragMoveEvent(self, event):
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
            else:
                event.ignore()

        def dropEvent(self, event):
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
                files = []
                for url in event.mimeData().urls():
                    file_path = url.toLocalFile()
                    if os.path.isfile(file_path):
                        files.append(file_path)

                if files and self.parent_gui:
                    self.parent_gui._add_dropped_files(files)
            else:
                event.ignore()

    class NoEscapeDialog(QDialog):
        def keyPressEvent(self, event):
            if event.key() == Qt.Key_Escape:
                event.ignore()
            else:
                super().keyPressEvent(event)

    def __init__(self, prj_base=None):
        super().__init__()
        self.setFont(DEFAULT_FONT)  # Set font for this widget and all children
        self.prj_base = prj_base or os.getenv('casino_prj_base', '')
        self.prj_name = os.getenv('casino_prj_name', '')
        self.proj_dir = (os.path.join(self.prj_base, self.prj_name)
                         if self.prj_base and self.prj_name else self.prj_base)
        self.assigner = getpass.getuser()

        # Initialize directory structure
        if self.proj_dir:
            self.fast_dir = os.path.join(self.proj_dir, 'FastTrack')
            self.attach_dir = os.path.join(self.fast_dir, 'attachments')
            self.deleted_dir = os.path.join(self.fast_dir, 'deleted_issues')
            self.deleted_attach_dir = os.path.join(self.deleted_dir, 'attachments')

            os.makedirs(self.fast_dir, exist_ok=True)
            os.makedirs(self.attach_dir, exist_ok=True)
            os.makedirs(self.deleted_dir, exist_ok=True)
            os.makedirs(self.deleted_attach_dir, exist_ok=True)

        self.blks = self._load_blocks()
        self.assignees = self._load_assignees()
        self.setWindowTitle("FastTrack Issue Manager")
        self._init_ui()
        self._update_summary_table()  # Initialize summary table

    def _init_ui(self):
        layout = QVBoxLayout()

        # Top bar with project info
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel(f"Project Dir: {self.proj_dir}"))
        top_bar.addWidget(QLabel(f"Assigner: {self.assigner}"))
        top_bar.addStretch()

        layout.addLayout(top_bar)

        # Create main horizontal layout for left pane and right content
        main_layout = QHBoxLayout()

        # Create left pane for Issue Summary
        left_pane = QVBoxLayout()
        left_pane.setContentsMargins(0, 0, 10, 0)  # Add right margin for separation

        # Add summary table to left pane
        summary_group = QGroupBox("Issue Summary")
        summary_layout = QVBoxLayout(summary_group)

        # Create summary table
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(2)
        self.summary_table.setRowCount(5)  # Status rows + total
        self.summary_table.setHorizontalHeaderLabels(["Status", "Count"])
        self.summary_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.summary_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.summary_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Add rows for each status
        self.status_rows = {
            "Open": 0,
            "In Progress": 1,
            "Resolved": 2,
            "Closed": 3,
            "Total": 4
        }

        for status, row in self.status_rows.items():
            self.summary_table.setItem(row, 0, QTableWidgetItem(status))
            self.summary_table.setItem(row, 1, QTableWidgetItem("0"))

            # Set color for status rows
            if status in self.STATUS_COLORS:
                color = self.STATUS_COLORS[status]
                for col in range(2):
                    item = self.summary_table.item(row, col)
                    item.setBackground(color)

        # Add button to view Open issues details
        open_issues_btn = QPushButton("View Open Issues Details")
        style_button(open_issues_btn, "blue")
        open_issues_btn.clicked.connect(self._view_open_issues)
        open_issues_btn.setToolTip("View details of all open issues (Ctrl+O)")
        summary_layout.addWidget(open_issues_btn)

        # Add refresh button for summary
        refresh_summary_btn = QPushButton("Refresh Summary")
        style_button(refresh_summary_btn, "gray")
        refresh_summary_btn.clicked.connect(self._update_summary_table)
        refresh_summary_btn.setToolTip("Refresh issue summary counts (Ctrl+R)")
        summary_layout.addWidget(refresh_summary_btn)

        summary_layout.addWidget(self.summary_table)
        left_pane.addWidget(summary_group)

        # Add a stretch to push the summary to the top of the left pane
        left_pane.addStretch(1)

        # Create right content area
        right_content = QVBoxLayout()

        # Issue creation fields
        right_content.addWidget(QLabel("Title:"))
        self.title_edit = QTextEdit(); self.title_edit.setFixedHeight(40)
        right_content.addWidget(self.title_edit)
        right_content.addWidget(QLabel("Description:"))

        # Description formatting toolbar
        desc_toolbar = QHBoxLayout()

        btn_bullet = QPushButton("[-] Bullet")
        btn_bullet.setMaximumWidth(90)
        btn_bullet.clicked.connect(lambda: self._insert_desc_bullet())
        style_button(btn_bullet, "default")

        btn_numbered = QPushButton("[1] Numbered")
        btn_numbered.setMaximumWidth(100)
        btn_numbered.clicked.connect(lambda: self._insert_desc_numbered())
        style_button(btn_numbered, "default")

        btn_task = QPushButton("[ ] Task")
        btn_task.setMaximumWidth(90)
        btn_task.clicked.connect(lambda: self._insert_desc_task())
        style_button(btn_task, "default")

        desc_toolbar.addWidget(btn_bullet)
        desc_toolbar.addWidget(btn_numbered)
        desc_toolbar.addWidget(btn_task)
        desc_toolbar.addStretch()

        right_content.addLayout(desc_toolbar)

        self.desc_edit = QTextEdit()
        self.desc_edit.setAcceptRichText(True)

        # Install event filter for list keyboard shortcuts
        self.desc_edit.viewport().installEventFilter(self)
        self.desc_edit.installEventFilter(self)

        right_content.addWidget(self.desc_edit)
        right_content.addWidget(QLabel("Severity:"))
        self.severity_combo = QComboBox(); self.severity_combo.addItems(["Critical","Major","Minor","Enhancement","Info"])
        right_content.addWidget(self.severity_combo)
        right_content.addWidget(QLabel("Category:"))
        self.stage_combo = QComboBox(); self.stage_combo.setEditable(True)
        self.stage_combo.addItems(["casino", "design", "dk", "syn", "dft", "lec", "sta", "ldrc", "vclp", "sim", "floorplan", "place", "cts", "route", "pex", "pv", "psi", "bump", "signoff"])
        right_content.addWidget(self.stage_combo)
        right_content.addWidget(QLabel("Affected Block (select multiple):"))
        self.module_list = QListWidget(); self.module_list.setSelectionMode(QAbstractItemView.MultiSelection)
        for blk in self.blks: self.module_list.addItem(blk)
        right_content.addWidget(self.module_list)
        right_content.addWidget(QLabel("Assignee:"))
        self.assignee_combo = QComboBox(); self.assignee_combo.addItems(self.assignees)
        right_content.addWidget(self.assignee_combo)
        right_content.addWidget(QLabel("Due Date:"))
        due_date_layout = QHBoxLayout()
        self.due_date_edit = QDateEdit()
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.due_date_edit.setDate(QDate.currentDate())
        self.due_date_edit.setMinimumDate(QDate.currentDate())

        self.due_time_edit = QTimeEdit()
        self.due_time_edit.setDisplayFormat("HH:mm")
        self.due_time_edit.setTime(QTime.currentTime())

        due_date_layout.addWidget(self.due_date_edit)
        due_date_layout.addWidget(self.due_time_edit)
        right_content.addLayout(due_date_layout)
        right_content.addWidget(QLabel("Run Directory:"))
        self.runid_edit = QTextEdit(); self.runid_edit.setFixedHeight(30)
        right_content.addWidget(self.runid_edit)
        # Attachments
        attachments_label = QLabel("Attachments :")
        right_content.addWidget(attachments_label)
        self.attach_list = self.DragDropListWidget(self)
        right_content.addWidget(self.attach_list)
        h_attach = QHBoxLayout()
        btn_add = QPushButton("Add...")
        style_button(btn_add, "blue")
        btn_add.clicked.connect(self._add_attachments)

        btn_remove = QPushButton("Remove")
        style_button(btn_remove, "danger")
        btn_remove.clicked.connect(self._remove_attachments)

        h_attach.addWidget(btn_add)
        h_attach.addWidget(btn_remove)
        right_content.addLayout(h_attach)
        self.link_check = QCheckBox("Create symlink instead of copy"); right_content.addWidget(self.link_check)
        # Action buttons
        h_btns = QHBoxLayout()
        self.submit_btn = QPushButton("Submit Issue")
        style_button(self.submit_btn, "action")
        self.submit_btn.clicked.connect(self._submit)
        self.submit_btn.setToolTip("Submit a new issue (Ctrl+S)")

        self.load_btn = QPushButton("Load Issue")
        style_button(self.load_btn, "blue")
        self.load_btn.clicked.connect(self._load_issue)
        self.load_btn.setToolTip("Load an existing issue (Ctrl+L)")

        self.view_btn = QPushButton("View Issues")
        style_button(self.view_btn, "gray")
        self.view_btn.clicked.connect(self._view_issues)
        self.view_btn.setToolTip("View all issues (Ctrl+V)")

        h_btns.addWidget(self.submit_btn)
        h_btns.addWidget(self.load_btn)
        h_btns.addWidget(self.view_btn)
        right_content.addLayout(h_btns)

        # Add left pane and right content to main layout
        main_layout.addLayout(left_pane, 1)  # 1 is the stretch factor
        main_layout.addLayout(right_content, 3)  # 3 is the stretch factor

        # Add main layout to the main layout
        layout.addLayout(main_layout)
        self.setLayout(layout)

        # Apply consistent table styling
        table_style = """
            QTableWidget {
                font-family: Terminus;
                font-size: 8pt;
            }
            QHeaderView::section {
                background-color: #E0E0E0;
                padding: 4px;
                font-family: Terminus;
                font-size: 8pt;
            }
            QTableWidget::item {
                padding: 4px;
            }
        """
        self.summary_table.setStyleSheet(table_style)

        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()

    def _load_blocks(self):
        raw = os.getenv('casino_all_blks','')
        return [b.strip() for b in re.split(r'[\s,]+', raw) if b.strip()]

    def _load_assignees(self):
        base, ass = self.proj_dir, []
        if base and os.path.isdir(base):
            for e in os.listdir(base):
                if e.startswith('works_'):
                    ass.append(e[len('works_'):])
        return sorted(ass)

    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for main window"""
        # Ctrl+N: Clear form for new issue
        shortcut_new = QShortcut(QKeySequence("Ctrl+N"), self)
        shortcut_new.activated.connect(self._clear_form)

        # Ctrl+S: Submit issue
        shortcut_submit = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut_submit.activated.connect(self._submit)

        # Ctrl+L: Load issue
        shortcut_load = QShortcut(QKeySequence("Ctrl+L"), self)
        shortcut_load.activated.connect(self._load_issue)

        # Ctrl+V: View issues
        shortcut_view = QShortcut(QKeySequence("Ctrl+V"), self)
        shortcut_view.activated.connect(self._view_issues)

        # Ctrl+R: Refresh summary table
        shortcut_refresh = QShortcut(QKeySequence("Ctrl+R"), self)
        shortcut_refresh.activated.connect(self._update_summary_table)

        # Ctrl+O: View open issues
        shortcut_open = QShortcut(QKeySequence("Ctrl+O"), self)
        shortcut_open.activated.connect(self._view_open_issues)

    def _add_attachments(self):
        """Add attachments with improved validation and feedback"""
        try:
            if not self.proj_dir:
                QMessageBox.warning(self, "Error", "Project directory not set")
                return

            start_dir = self.proj_dir
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "Select Attachment Files",
                start_dir
            )

            if not files:
                return

            # Check total size of attachments
            total_size = sum(os.path.getsize(f) for f in files if os.path.exists(f))
            size_limit_mb = 100  # 100MB limit
            if total_size > size_limit_mb * 1024 * 1024:
                QMessageBox.warning(self, "Warning",
                    f"Total attachment size ({total_size/1024/1024:.1f}MB) "
                    f"exceeds the recommended limit of {size_limit_mb}MB.\n\n"
                    "Large attachments may cause performance issues.")
                return

            skipped_files = []
            added_files = []

            for f in files:
                if not os.path.exists(f):
                    skipped_files.append(f"File not found: {f}")
                    continue

                filename = os.path.basename(f)
                file_size = os.path.getsize(f)

                # Skip empty files
                if file_size == 0:
                    skipped_files.append(f"Empty file: {filename}")
                    continue

                # Check if file is already in the list
                duplicate = False
                for i in range(self.attach_list.count()):
                    existing_item = self.attach_list.item(i)
                    if existing_item and existing_item.data(Qt.UserRole) == f:
                        duplicate = True
                        break

                if duplicate:
                    skipped_files.append(f"Already added: {filename}")
                    continue

                # Add the file
                try:
                    item = QListWidgetItem(filename)
                    item.setData(Qt.UserRole, f)
                    self.attach_list.addItem(item)
                    added_files.append(filename)
                except Exception as e:
                    logging.error(f"Error creating QListWidgetItem: {str(e)}")
                    skipped_files.append(f"Failed to add: {filename}")
                    continue

            # Show summary message
            if added_files or skipped_files:
                message = ""
                if added_files:
                    message += f"Added {len(added_files)} file(s):\n"
                    message += "\n".join(f"- {f}" for f in added_files)
                if skipped_files:
                    if message:
                        message += "\n\n"
                    message += "Skipped files:\n"
                    message += "\n".join(f"- {f}" for f in skipped_files)

                QMessageBox.information(self, "Attachment Summary", message)

        except Exception as e:
            QMessageBox.critical(self, "Error",
                f"Failed to add attachments:\n{str(e)}")
            logging.exception("Error in _add_attachments")

    def _remove_attachments(self):
        for it in self.attach_list.selectedItems():
            self.attach_list.takeItem(self.attach_list.row(it))

    def _add_dropped_files(self, files):
        """Add files that were dropped onto the attachment list"""
        try:
            if not self.proj_dir:
                QMessageBox.warning(self, "Error", "Project directory not set")
                return

            # Check total size of attachments
            total_size = sum(os.path.getsize(f) for f in files if os.path.exists(f))
            size_limit_mb = 100  # 100MB limit
            if total_size > size_limit_mb * 1024 * 1024:
                QMessageBox.warning(self, "Warning",
                    f"Total attachment size ({total_size/1024/1024:.1f}MB) "
                    f"exceeds the recommended limit of {size_limit_mb}MB.\n\n"
                    "Large attachments may cause performance issues.")
                return

            skipped_files = []
            added_files = []

            for f in files:
                if not os.path.exists(f):
                    skipped_files.append(f"File not found: {f}")
                    continue

                filename = os.path.basename(f)
                file_size = os.path.getsize(f)

                # Skip empty files
                if file_size == 0:
                    skipped_files.append(f"Empty file: {filename}")
                    continue

                # Check if file is already in the list
                duplicate = False
                for i in range(self.attach_list.count()):
                    existing_item = self.attach_list.item(i)
                    if existing_item and existing_item.data(Qt.UserRole) == f:
                        duplicate = True
                        break

                if duplicate:
                    skipped_files.append(f"Already added: {filename}")
                    continue

                # Add the file
                try:
                    item = QListWidgetItem(filename)
                    item.setData(Qt.UserRole, f)
                    self.attach_list.addItem(item)
                    added_files.append(filename)
                except Exception as e:
                    logging.error(f"Error creating QListWidgetItem: {str(e)}")
                    skipped_files.append(f"Failed to add: {filename}")
                    continue

            # Show summary message
            if added_files or skipped_files:
                message = ""
                if added_files:
                    message += f"Added {len(added_files)} file(s) via drag & drop:\n"
                    message += "\n".join(f"- {f}" for f in added_files)
                if skipped_files:
                    if message:
                        message += "\n\n"
                    message += "Skipped files:\n"
                    message += "\n".join(f"- {f}" for f in skipped_files)

                QMessageBox.information(self, "Attachment Summary", message)

        except Exception as e:
            QMessageBox.critical(self, "Error",
                f"Failed to add dropped files:\n{str(e)}")
            logging.exception("Error in _add_dropped_files")

    def _insert_desc_bullet(self):
        """Insert bullet list in submit form description"""
        from PyQt5.QtGui import QTextListFormat
        cursor = self.desc_edit.textCursor()
        list_format = QTextListFormat()
        list_format.setStyle(QTextListFormat.ListDisc)
        cursor.insertList(list_format)
        self.desc_edit.setFocus()

    def _insert_desc_numbered(self):
        """Insert numbered list in submit form description"""
        from PyQt5.QtGui import QTextListFormat
        cursor = self.desc_edit.textCursor()
        list_format = QTextListFormat()
        list_format.setStyle(QTextListFormat.ListDecimal)
        cursor.insertList(list_format)
        self.desc_edit.setFocus()

    def _insert_desc_task(self):
        """Insert task checkbox in submit form description"""
        cursor = self.desc_edit.textCursor()
        cursor.insertText("[ ] ")
        self.desc_edit.setFocus()

    def eventFilter(self, obj, event):
        """Handle keyboard shortcuts and mouse clicks for lists and task items in submit form"""
        from PyQt5.QtCore import QEvent, Qt
        from PyQt5.QtGui import QMouseEvent, QTextCursor, QKeyEvent

        # Only handle events for desc_edit (submit form description field)
        if not hasattr(self, 'desc_edit'):
            return super().eventFilter(obj, event)

        # Handle keyboard events for Tab/Shift+Tab in lists and Enter for checkboxes
        if obj == self.desc_edit and event.type() == QEvent.KeyPress:
            if isinstance(event, QKeyEvent):
                cursor = self.desc_edit.textCursor()
                current_list = cursor.currentList()

                # Handle Tab - indent list item OR checkbox line
                if event.key() == Qt.Key_Tab:
                    if current_list:
                        # List indenting
                        cursor.beginEditBlock()
                        list_format = current_list.format()
                        list_format.setIndent(list_format.indent() + 1)
                        current_list.setFormat(list_format)
                        cursor.endEditBlock()
                        return True
                    else:
                        # Checkbox line indenting
                        cursor.select(QTextCursor.LineUnderCursor)
                        line_text = cursor.selectedText()
                        cursor.clearSelection()
                        stripped = line_text.lstrip()
                        if stripped.startswith('[ ] ') or stripped.startswith('[v] '):
                            cursor = self.desc_edit.textCursor()
                            cursor.movePosition(QTextCursor.StartOfBlock)
                            cursor.insertText("  ")  # Add 2 spaces indent
                            return True

                # Handle Shift+Tab - outdent list item OR checkbox line
                if event.key() == Qt.Key_Backtab:
                    if current_list:
                        # List outdenting
                        cursor.beginEditBlock()
                        list_format = current_list.format()
                        if list_format.indent() > 0:
                            list_format.setIndent(list_format.indent() - 1)
                            current_list.setFormat(list_format)
                        cursor.endEditBlock()
                        return True
                    else:
                        # Checkbox line outdenting
                        cursor.select(QTextCursor.LineUnderCursor)
                        line_text = cursor.selectedText()
                        cursor.clearSelection()
                        if line_text.startswith('  '):
                            stripped = line_text.lstrip()
                            if stripped.startswith('[ ] ') or stripped.startswith('[v] '):
                                cursor = self.desc_edit.textCursor()
                                cursor.movePosition(QTextCursor.StartOfBlock)
                                cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 2)
                                if cursor.selectedText() == "  ":
                                    cursor.removeSelectedText()
                                return True

                # Handle Enter for checkbox auto-continuation
                if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                    cursor.select(QTextCursor.LineUnderCursor)
                    line_text = cursor.selectedText()
                    cursor.clearSelection()

                    stripped = line_text.lstrip()
                    if stripped.startswith('[ ] ') or stripped.startswith('[v] '):
                        indent = line_text[:len(line_text) - len(stripped)]
                        checkbox_content = stripped[4:].strip()

                        if not checkbox_content:
                            # Empty checkbox line - exit checkbox mode
                            cursor = self.desc_edit.textCursor()
                            cursor.insertText("\n")
                            return True
                        else:
                            # Non-empty checkbox line - auto-create next checkbox
                            cursor = self.desc_edit.textCursor()
                            cursor.insertText("\n" + indent + "[ ] ")
                            return True

        # Handle mouse clicks on checkboxes in submit form description
        if hasattr(self, 'desc_edit') and obj == self.desc_edit.viewport() and event.type() == QEvent.MouseButtonRelease:
            if isinstance(event, QMouseEvent):
                cursor = self.desc_edit.cursorForPosition(event.pos())
                cursor.select(QTextCursor.LineUnderCursor)
                line_text = cursor.selectedText()
                cursor.clearSelection()

                line_start_pos = cursor.block().position()
                click_pos = self.desc_edit.cursorForPosition(event.pos()).position()
                pos_in_line = click_pos - line_start_pos

                # Check for checkbox patterns "[ ]" or "[v]" near click position
                for i in range(max(0, pos_in_line - 3), min(len(line_text) - 2, pos_in_line + 3)):
                    if i + 2 < len(line_text):
                        pattern = line_text[i:i+3]
                        if pattern == '[ ]' or pattern == '[v]':
                            new_pattern = '[v]' if pattern == '[ ]' else '[ ]'
                            cursor = self.desc_edit.textCursor()
                            cursor.setPosition(line_start_pos + i)
                            cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 3)
                            cursor.insertText(new_pattern)
                            return True

        return super().eventFilter(obj, event)

    def _submit(self):
        """Submit a new issue"""
        try:
            # Validate project directory
            if not self.proj_dir or not os.path.isdir(self.fast_dir):
                QMessageBox.warning(self, "Error",
                    "Project directory not properly initialized.\n"
                    f"Expected directory: {self.fast_dir}")
                return

            # Get and validate form values with detailed feedback
            title = self.title_edit.toPlainText().strip()
            desc = self.desc_edit.toPlainText().strip()
            severity = self.severity_combo.currentText()
            stage = self.stage_combo.currentText()
            assignee = self.assignee_combo.currentText()
            run_id = self.runid_edit.toPlainText().strip()

            validation_errors = []
            if not title:
                validation_errors.append("- Title is required")
            if not desc:
                validation_errors.append("- Description is required")
            if len(title) > 100:  # Add reasonable length limits
                validation_errors.append("- Title must be less than 100 characters")

            # Get selected modules
            modules = [item.text() for item in self.module_list.selectedItems()]
            if not modules:
                validation_errors.append("- At least one block must be selected")

            # Validate due date
            due_date = self.due_date_edit.date()
            current_date = QDate.currentDate()
            if due_date < current_date:
                validation_errors.append("- Due date cannot be in the past")

            if validation_errors:
                QMessageBox.warning(self, "Validation Error",
                    "Please correct the following errors:\n" +
                    "\n".join(validation_errors))
                return

            # Generate issue ID
            issue_id = self._generate_issue_id()
            issue_filename = f"{issue_id}.yaml"

            # Create issue-specific attachment directory
            issue_attach_dir = os.path.join(self.attach_dir, issue_id)
            os.makedirs(issue_attach_dir, exist_ok=True)

            # Prepare issue data
            issue_data = {
                'id': issue_id,
                'title': title,
                'description': desc,
                'severity': severity,
                'stage': stage,
                'modules': modules,
                'assignee': assignee,
                'assigner': self.assigner,
                'status': 'Open',
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'due_date': due_date.toString("yyyy-MM-dd"),
                'run_id': run_id,
                'attachments': []
            }

            # Handle attachments
            for i in range(self.attach_list.count()):
                item = self.attach_list.item(i)
                if not item:
                    continue

                src_path = item.data(Qt.UserRole)
                if not src_path or not os.path.exists(src_path):
                    continue

                try:
                    filename = os.path.basename(src_path)
                    dst_path = os.path.join(issue_attach_dir, filename)

                    if os.path.exists(dst_path):
                        # Add timestamp to filename to make it unique
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        base, ext = os.path.splitext(filename)
                        filename = f"{base}_{timestamp}{ext}"
                        dst_path = os.path.join(issue_attach_dir, filename)

                    if self.link_check.isChecked():
                        if os.path.exists(dst_path):
                            os.remove(dst_path)
                        os.symlink(src_path, dst_path)
                    else:
                        shutil.copy2(src_path, dst_path)
                    issue_data['attachments'].append(dst_path)
                except Exception as e:
                    QMessageBox.warning(self, "Warning",
                                      f"Failed to copy attachment {filename}: {str(e)}")

            # Save issue file
            issue_path = os.path.join(self.fast_dir, issue_filename)
            try:
                with open(issue_path, 'w') as f:
                    yaml.safe_dump(issue_data, f)
                QMessageBox.information(self, "Success",
                                      f"Issue {issue_id} created successfully")
                self._clear_form()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save issue: {str(e)}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create issue: {str(e)}")

    def _load_issue(self):
        fast_dir = os.path.join(self.proj_dir, "FastTrack")
        if not os.path.isdir(fast_dir):
            QMessageBox.warning(self, "Error", "No FastTrack directory found.")
            return

        # Create dialog to show issues in a table
        dlg = self.NoEscapeDialog(self)
        dlg.setWindowTitle("Load Issue")
        dlg.setMinimumWidth(800)
        dlg.setMinimumHeight(500)

        layout = QVBoxLayout(dlg)

        # Add search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_edit = QLineEdit()
        search_edit.setPlaceholderText("Enter text to filter issues...")
        search_layout.addWidget(search_label)
        search_layout.addWidget(search_edit)
        layout.addLayout(search_layout)

        # Add table for issues
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["ID", "Title", "Assigner", "Assignee", "Severity"])
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)

        # Set column widths
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Title
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Assigner
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Assignee
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Severity

        layout.addWidget(table)

        # Add buttons
        btn_layout = QHBoxLayout()
        load_btn = QPushButton("Load Selected Issue")
        style_button(load_btn, "action")
        close_btn = QPushButton("Cancel")
        style_button(close_btn, "gray")
        btn_layout.addWidget(load_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        # Populate table with issues
        issues = []
        for fn in os.listdir(fast_dir):
            if not fn.endswith(('.yaml','.yml')):
                continue
            path = os.path.join(fast_dir, fn)
            try:
                data = yaml.safe_load(open(path))
                issues.append((data, path))
            except Exception:
                pass

        # Sort issues by creation date (newest first)
        issues.sort(key=lambda x: x[0].get('created_at', ''), reverse=True)

        # Function to populate table with filtered issues
        def populate_table(filter_text=""):
            table.setRowCount(0)
            for data, path in issues:
                # Apply filter if provided
                if filter_text:
                    filter_text = filter_text.lower()
                    title = data.get('title', '').lower()
                    desc = data.get('description', '').lower()
                    if filter_text not in title and filter_text not in desc:
                        continue

                row = table.rowCount()
                table.insertRow(row)

                # Set data
                table.setItem(row, 0, QTableWidgetItem(data.get('id', '')))
                table.setItem(row, 1, QTableWidgetItem(data.get('title', '')))
                table.setItem(row, 2, QTableWidgetItem(data.get('assigner', '')))
                table.setItem(row, 3, QTableWidgetItem(data.get('assignee', '')))

                # Set severity with color
                severity_item = QTableWidgetItem(data.get('severity', ''))
                severity = data.get('severity', '')
                if severity in self.SEVERITY_COLORS:
                    severity_item.setBackground(self.SEVERITY_COLORS[severity])
                table.setItem(row, 4, severity_item)

                # Set tooltip with description
                title_item = table.item(row, 1)
                title_item.setToolTip(data.get('description', ''))

                # Store path for later use
                table.item(row, 0).setData(Qt.UserRole, path)

        # Initial population
        populate_table()

        # Connect search functionality
        search_edit.textChanged.connect(lambda text: populate_table(text))

        # Connect load button
        def load_selected():
            try:
                selected = table.selectedItems()
                if not selected:
                    QMessageBox.warning(dlg, "Warning", "Please select an issue to load.")
                    return

                row = selected[0].row()
                path = table.item(row, 0).data(Qt.UserRole)

                data = yaml.safe_load(open(path))
                self.title_edit.setPlainText(data.get('title', ''))
                self.desc_edit.setPlainText(data.get('description', ''))
                self.severity_combo.setCurrentText(data.get('severity', ''))
                self.stage_combo.setCurrentText(data.get('stage', ''))
                mods = set(data.get('modules', []))
                for i in range(self.module_list.count()):
                    item = self.module_list.item(i)
                    item.setSelected(item.text() in mods)
                self.assignee_combo.setCurrentText(data.get('assignee', ''))
                self.runid_edit.setPlainText(data.get('run_id', ''))

                # Clear and reload attachments
                self.attach_list.clear()
                for attach_path in data.get('attachments', []):
                    if os.path.exists(attach_path):
                        item = QListWidgetItem(os.path.basename(attach_path))
                        item.setData(Qt.UserRole, attach_path)
                        self.attach_list.addItem(item)

                if "due_date" in data:
                    try:
                        # Try to parse with hours first
                        if len(data["due_date"]) > 10:  # Contains time
                            date_str, time_str = data["due_date"].split(" ")
                            due_date = QDate.fromString(date_str, "yyyy-MM-dd")
                            due_time = QTime.fromString(time_str, "HH:mm")
                            self.due_date_edit.setDate(due_date)
                            self.due_time_edit.setTime(due_time)
                        else:
                            due_date = QDate.fromString(data["due_date"], "yyyy-MM-dd")
                            self.due_date_edit.setDate(due_date)
                            self.due_time_edit.setTime(QTime(0, 0))  # Default to midnight
                    except:
                        self.due_date_edit.setDate(QDate.currentDate())
                        self.due_time_edit.setTime(QTime.currentTime())
                dlg.accept()
            except Exception as e:
                QMessageBox.critical(dlg, "Error", f"Failed to load issue: {e}")

        load_btn.clicked.connect(load_selected)
        close_btn.clicked.connect(dlg.reject)

        # Connect double-click to load
        table.itemDoubleClicked.connect(lambda item: load_selected())

        dlg.exec_()

    def _view_issues(self):
        fast_dir = os.path.join(self.proj_dir, "FastTrack")
        dlg = self.NoEscapeDialog(self)  # Use our custom dialog class
        dlg.setWindowTitle("Issue Status Viewer")
        layout = QVBoxLayout(dlg)

        # Store description dialogs and their child windows to prevent garbage collection
        description_dialogs = []
        editor_dialogs = []
        history_dialogs = []

        # Filter presets section
        presets_layout = QHBoxLayout()
        presets_label = QLabel("Filter Presets:")
        presets_combo = QComboBox()
        presets_combo.addItem("-- Select Preset --")
        presets_combo.setMinimumWidth(200)

        btn_save_preset = QPushButton("Save Current Filters")
        style_button(btn_save_preset, "action")
        btn_save_preset.setToolTip("Save current filter settings as a preset")

        btn_delete_preset = QPushButton("Delete Preset")
        style_button(btn_delete_preset, "danger")
        btn_delete_preset.setToolTip("Delete the selected preset")
        btn_delete_preset.setEnabled(False)

        btn_clear_filters = QPushButton("Clear All Filters")
        style_button(btn_clear_filters, "gray")
        btn_clear_filters.setToolTip("Clear all filters and show all issues")

        presets_layout.addWidget(presets_label)
        presets_layout.addWidget(presets_combo)
        presets_layout.addWidget(btn_save_preset)
        presets_layout.addWidget(btn_delete_preset)
        presets_layout.addWidget(btn_clear_filters)
        presets_layout.addStretch()
        layout.addLayout(presets_layout)

        # Description search bar
        desc_search = QLineEdit()
        desc_search.setPlaceholderText("Search Description...")
        layout.addWidget(desc_search)
        cols = ["ID","Title","Assigner","Assignee","Status","Created","Due Date","Severity","Stage","Blocks","Run Dir"]
        tbl = QTableWidget()
        tbl.setColumnCount(len(cols))
        tbl.setHorizontalHeaderLabels(cols)

        # Make headers clickable for sorting
        tbl.horizontalHeader().setSectionsClickable(True)
        tbl.horizontalHeader().setSortIndicatorShown(True)

        for idx in range(tbl.columnCount()):
            mode = QHeaderView.ResizeToContents if idx < 9 else QHeaderView.Interactive
            tbl.horizontalHeader().setSectionResizeMode(idx, mode)

        # Filter row
        tbl.insertRow(0)
        self.col_filters = []
        for c, col in enumerate(cols):
            le = QLineEdit()
            le.setPlaceholderText(col)
            tbl.setCellWidget(0, c, le)
            self.col_filters.append((c, le))

        # Custom sorting state tracking
        self._current_sort_column = -1
        self._current_sort_order = Qt.AscendingOrder

        # Custom sort function that excludes filter row
        def manual_sort(logical_index):
            """Sort table data while keeping filter row (row 0) fixed"""
            # Toggle sort order if clicking same column
            if self._current_sort_column == logical_index:
                self._current_sort_order = Qt.DescendingOrder if self._current_sort_order == Qt.AscendingOrder else Qt.AscendingOrder
            else:
                self._current_sort_column = logical_index
                self._current_sort_order = Qt.AscendingOrder

            # Update header to show sort indicator
            tbl.horizontalHeader().setSortIndicator(logical_index, self._current_sort_order)

            # Collect all data rows (skip row 0 which is filter row)
            rows_data = []
            for r in range(1, tbl.rowCount()):
                row_data = []
                for c in range(tbl.columnCount()):
                    # Get cell widget or item
                    widget = tbl.cellWidget(r, c)
                    if widget:
                        # For widgets (like comboboxes), get current text
                        if hasattr(widget, 'currentText'):
                            row_data.append(widget.currentText())
                        else:
                            row_data.append('')
                    else:
                        item = tbl.item(r, c)
                        row_data.append(item.text() if item else '')

                # Store the issue path index for this row
                rows_data.append((r-1, row_data))  # r-1 because _issue_paths is 0-indexed

            # Sort the data based on the selected column
            def sort_key(row_tuple):
                _, row_data = row_tuple
                value = row_data[logical_index]
                # Try to convert to number for numeric sorting
                try:
                    return (0, float(value))  # Numbers sort before text
                except (ValueError, TypeError):
                    return (1, value.lower())  # Text sorting (case-insensitive)

            rows_data.sort(key=sort_key, reverse=(self._current_sort_order == Qt.DescendingOrder))

            # Now reorder the issue paths and descriptions to match sorted order
            sorted_paths = []
            sorted_descriptions = []
            for issue_idx, _ in rows_data:
                sorted_paths.append(self._issue_paths[issue_idx])
                sorted_descriptions.append(self._descriptions[issue_idx])

            self._issue_paths = sorted_paths
            self._descriptions = sorted_descriptions

            # Repopulate the table with sorted data (preserve the sorted order)
            populate(preserve_order=True)

        # Connect header click to custom sort function
        tbl.horizontalHeader().sectionClicked.connect(manual_sort)

        # Modify Status button
        btn_modify = QPushButton("Modify Status")
        style_button(btn_modify, "action")
        btn_modify.setEnabled(False)
        layout.addWidget(btn_modify)
        # Table widget
        layout.addWidget(tbl)

        # Enable context menu for table
        tbl.setContextMenuPolicy(Qt.CustomContextMenu)

        # Enable row selection behavior for better row highlighting
        tbl.setSelectionBehavior(QAbstractItemView.SelectRows)

        # Enable row hovering effect
        tbl.setMouseTracking(True)
        tbl.setStyleSheet("""
            QTableWidget {
                font-family: Terminus;
                font-size: 8pt;
            }
            QTableWidget::item:hover {
                background-color: #6BA3D0;
                color: #FFFFFF;
            }
            QTableWidget::item:selected:hover {
                background-color: #4080C0;
                color: #FFFFFF;
            }
            QTableWidget::item:selected {
                background-color: #5B9BD5;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #E0E0E0;
                padding: 4px;
                font-family: Terminus;
                font-size: 8pt;
            }
        """)

        # Action buttons
        btns = QHBoxLayout()
        btn_det = QPushButton("Check Attachments")
        style_button(btn_det, "blue")
        btn_save = QPushButton("Save Changes")
        style_button(btn_save, "success")
        btn_delete = QPushButton("Delete Issue")
        style_button(btn_delete, "danger")
        btn_restore = QPushButton("Restore Issue")
        style_button(btn_restore, "action")
        btn_auto_size = QPushButton("Auto Size")
        style_button(btn_auto_size, "gray")
        btn_close = QPushButton("Close")
        style_button(btn_close, "danger")
        btn_refresh = QPushButton("Refresh")
        style_button(btn_refresh, "gray")
        btn_html = QPushButton("Export HTML")
        style_button(btn_html, "blue")
        for b in (btn_modify, btn_det, btn_save, btn_delete, btn_restore, btn_auto_size, btn_refresh, btn_html, btn_close):
            btns.addWidget(b)
        layout.addLayout(btns)
        user = self.assigner
        self._issue_paths = []
        self._descriptions = []
        self._status_combos = []  # Store references to all status combos

        # Filter preset management
        presets_file = os.path.join(self.fast_dir, "filter_presets.json")

        def load_presets():
            """Load filter presets from file"""
            if not os.path.exists(presets_file):
                return {}
            try:
                import json
                with open(presets_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}

        def save_presets(presets):
            """Save filter presets to file"""
            try:
                import json
                with open(presets_file, 'w') as f:
                    json.dump(presets, f, indent=2)
            except Exception as e:
                QMessageBox.warning(dlg, "Error", f"Failed to save presets: {str(e)}")

        def refresh_presets_combo():
            """Refresh the presets combo box"""
            current_selection = presets_combo.currentText()
            presets_combo.clear()
            presets_combo.addItem("-- Select Preset --")

            presets = load_presets()
            for preset_name in sorted(presets.keys()):
                presets_combo.addItem(preset_name)

            # Restore selection if it still exists
            index = presets_combo.findText(current_selection)
            if index >= 0:
                presets_combo.setCurrentIndex(index)

        def on_preset_selected(index):
            """Load selected preset"""
            if index <= 0:  # First item is "-- Select Preset --"
                btn_delete_preset.setEnabled(False)
                return

            btn_delete_preset.setEnabled(True)
            preset_name = presets_combo.currentText()
            presets = load_presets()

            if preset_name not in presets:
                return

            preset_data = presets[preset_name]
            filters = preset_data.get('filters', {})

            # Apply filters to column filter boxes
            for c, le in self.col_filters:
                col_name = cols[c]
                if col_name in filters:
                    le.setText(filters[col_name])
                    # Highlight filter input with yellow background
                    le.setStyleSheet("background-color: #FFFACD; font-weight: bold;")
                else:
                    le.clear()
                    le.setStyleSheet("")  # Clear highlighting

            # Apply description filter
            if 'description' in filters:
                desc_search.setText(filters['description'])
                desc_search.setStyleSheet("background-color: #FFFACD; font-weight: bold;")
            else:
                desc_search.clear()
                desc_search.setStyleSheet("")  # Clear highlighting

        def on_save_preset():
            """Save current filters as a preset"""
            from PyQt5.QtWidgets import QInputDialog

            # Collect current filter values
            current_filters = {}
            has_filters = False

            for c, le in self.col_filters:
                text = le.text().strip()
                if text:
                    current_filters[cols[c]] = text
                    has_filters = True

            desc_text = desc_search.text().strip()
            if desc_text:
                current_filters['description'] = desc_text
                has_filters = True

            if not has_filters:
                QMessageBox.information(dlg, "No Filters",
                    "Please set some filters before saving a preset.")
                return

            # Ask for preset name
            preset_name, ok = QInputDialog.getText(
                dlg, "Save Filter Preset",
                "Enter a name for this preset:"
            )

            if ok and preset_name.strip():
                preset_name = preset_name.strip()

                presets = load_presets()

                # Check if preset already exists
                if preset_name in presets:
                    reply = QMessageBox.question(
                        dlg, "Overwrite Preset",
                        f"Preset '{preset_name}' already exists. Overwrite?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        return

                # Save preset
                presets[preset_name] = {
                    'filters': current_filters,
                    'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                save_presets(presets)
                refresh_presets_combo()

                # Select the newly created preset
                index = presets_combo.findText(preset_name)
                if index >= 0:
                    presets_combo.setCurrentIndex(index)

                QMessageBox.information(dlg, "Success",
                    f"Filter preset '{preset_name}' saved successfully.")

        def on_delete_preset():
            """Delete the selected preset"""
            if presets_combo.currentIndex() <= 0:
                return

            preset_name = presets_combo.currentText()

            reply = QMessageBox.question(
                dlg, "Delete Preset",
                f"Are you sure you want to delete preset '{preset_name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                presets = load_presets()
                if preset_name in presets:
                    del presets[preset_name]
                    save_presets(presets)
                    refresh_presets_combo()
                    presets_combo.setCurrentIndex(0)
                    QMessageBox.information(dlg, "Success",
                        f"Preset '{preset_name}' deleted successfully.")

        def on_clear_filters():
            """Clear all filter inputs and reset to show all issues"""
            # Clear all column filters
            for c, le in self.col_filters:
                le.clear()
                le.setStyleSheet("")  # Remove highlighting

            # Clear description filter
            desc_search.clear()
            desc_search.setStyleSheet("")  # Remove highlighting

            # Reset preset combo to default
            presets_combo.setCurrentIndex(0)

        # Connect preset signals
        presets_combo.currentIndexChanged.connect(on_preset_selected)
        btn_save_preset.clicked.connect(on_save_preset)
        btn_delete_preset.clicked.connect(on_delete_preset)
        btn_clear_filters.clicked.connect(on_clear_filters)

        # Load initial presets
        refresh_presets_combo()

        def populate(preserve_order=False):
            """Populate table with issue data

            Args:
                preserve_order: If True, use existing order in _issue_paths.
                               If False, load from directory and sort by filename.
            """
            tbl.setRowCount(1)  # Keep filter row
            self._status_combos.clear()

            if not os.path.isdir(fast_dir):
                return

            # If not preserving order, reload from directory
            if not preserve_order:
                self._issue_paths.clear()
                self._descriptions.clear()

                for fn in sorted(os.listdir(fast_dir)):
                    if not fn.endswith(('.yaml','.yml')):
                        continue

                    path = os.path.join(fast_dir, fn)
                    data = yaml.safe_load(open(path))
                    desc = data.get('description', '')
                    self._issue_paths.append(path)
                    self._descriptions.append(desc)

            # Now populate table using current order in _issue_paths
            for idx, path in enumerate(self._issue_paths):
                data = yaml.safe_load(open(path))
                desc = self._descriptions[idx]

                r = tbl.rowCount()
                tbl.insertRow(r)

                # Get status for background color
                status = data.get('status', '')
                status_color = self.STATUS_COLORS.get(status)

                vals = [
                    data.get('id', ''),
                    data.get('title', ''),
                    data.get('assigner', ''),
                    data.get('assignee', ''),
                    status,
                    data.get('created_at', ''),
                    data.get('due_date', ''),
                    data.get('severity', ''),
                    data.get('stage', ''),
                    ', '.join(data.get('modules', [])),
                    data.get('run_id', '')
                ]

                # Add number of attachments to title
                attachments = data.get('attachments', [])
                if attachments:
                    num_attachments = len(attachments)
                    vals[1] = f"{vals[1]} ({num_attachments})"

                for c, val in enumerate(vals):
                    if c == 4:  # Status column
                        cb = QComboBox()
                        cb.addItems(self.STATUS_OPTIONS)
                        cb.setCurrentText(val)
                        cb.setEnabled(False)
                        tbl.setCellWidget(r, c, cb)
                        if status_color:
                            cb.setStyleSheet(f"QComboBox {{ background-color: {status_color.name()}; }}")
                    else:
                        item = QTableWidgetItem(val)
                        if c == 1:  # Title column
                            item.setToolTip(desc)
                        tbl.setItem(r, c, item)

                        # Apply status color to all cells except severity
                        if status_color and c != 7:  # Skip severity column
                            item.setBackground(status_color)

                # Apply severity color to the severity column (index 7)
                severity = data.get('severity', '')
                severity_color = self.SEVERITY_COLORS.get(severity)
                if severity_color:
                    severity_cell = tbl.item(r, 7)
                    if severity_cell:
                        severity_cell.setBackground(severity_color)

                # Format blocks with newlines and ensure status color is applied
                blocks = data.get('modules', [])
                blocks_text = '\n'.join(blocks) if blocks else ''
                blocks_item = QTableWidgetItem(blocks_text)
                blocks_item.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
                if status_color:
                    blocks_item.setBackground(status_color)
                tbl.setItem(r, 9, blocks_item)

                # Check if due date is overdue
                due_date_str = data.get('due_date', '')
                if due_date_str:
                    try:
                        if len(due_date_str) > 10:  # Contains time
                            due_date = datetime.strptime(due_date_str, "%Y-%m-%d %H:%M")
                            formatted_date = due_date.strftime("%Y-%m-%d %H:%M")
                        else:
                            due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
                            formatted_date = due_date.strftime("%Y-%m-%d 00:00")

                        due_date_cell = tbl.item(r, 6)
                        if due_date_cell:
                            due_date_cell.setText(formatted_date)
                            if due_date < datetime.now():
                                font = due_date_cell.font()
                                font.setBold(True)
                                due_date_cell.setFont(font)
                                due_date_cell.setForeground(QColor("#FF0000"))
                    except Exception:
                        pass

            tbl.resizeColumnsToContents()
            btn_modify.setEnabled(False)

        def on_row_selected(r, c):
            if r <= 0:
                btn_modify.setEnabled(False)
                return
            ass = tbl.item(r, 2).text(); to = tbl.item(r, 3).text()
            btn_modify.setEnabled(user in (ass, to))

        def on_cell_clicked(row, col):
            # Title click shows description in popup window (non-modal, multiple allowed)
            if row <= 0 or col != 1:
                return
            path = self._issue_paths[row-1]

            with open(path, 'r') as f:
                data = yaml.safe_load(f)

            # Create non-modal dialog
            dlg2 = QDialog(dlg)
            dlg2.setWindowTitle(f"Description - {data.get('id', '')}")
            dlg2.setMinimumWidth(700)
            dlg2.setMinimumHeight(400)

            # Make it a normal window (not modal dialog)
            dlg2.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint)

            v = QVBoxLayout(dlg2)

            # Description text edit
            te = QTextEdit()
            te.setReadOnly(True)
            te.setPlainText(data.get('description',''))
            v.addWidget(te)

            # Buttons
            btn_layout = QHBoxLayout()

            btn_modify = QPushButton("Modify")
            style_button(btn_modify, "action")

            btn_history = QPushButton("History")
            style_button(btn_history, "blue")

            btn_close = QPushButton("Close")
            style_button(btn_close, "gray")

            btn_layout.addWidget(btn_modify)
            btn_layout.addWidget(btn_history)
            btn_layout.addWidget(btn_close)
            v.addLayout(btn_layout)

            def on_modify_description():
                """Launch enhanced markdown editor for description (non-modal)"""
                # Load HTML version if available, otherwise plain text
                current_description_html = data.get('description_html', '')
                current_description = current_description_html if current_description_html else data.get('description', '')

                # Create non-modal rich text editor
                editor = MarkdownDescriptionEditor(current_description, dlg2)
                editor.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint)
                editor.setWindowTitle(f"Edit Description - {data.get('id', '')}")

                # Define save handler
                def on_editor_save():
                    # Get both HTML and plain text/markdown
                    new_description_html = editor.get_description_html().strip()
                    new_description_text = editor.get_description().strip()

                    old_description = data.get('description', '')
                    old_description_html = data.get('description_html', '')

                    if new_description_text == old_description:
                        QMessageBox.information(editor, "No Changes", "Description was not modified.")
                        return

                    if not new_description_text:
                        QMessageBox.warning(editor, "Error", "Description cannot be empty.")
                        return

                    # Add to change history
                    if 'description_history' not in data:
                        data['description_history'] = []

                    history_entry = {
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'user': getpass.getuser(),
                        'old_description': old_description,
                        'old_description_html': old_description_html
                    }
                    data['description_history'].append(history_entry)

                    # Update description (both formats)
                    data['description'] = new_description_text
                    data['description_html'] = new_description_html

                    # Save to file
                    try:
                        with open(path, 'w') as f:
                            yaml.safe_dump(data, f)

                        # Update the descriptions array
                        self._descriptions[row-1] = new_description_text

                        # Update tooltip in table
                        title_item = tbl.item(row, col)
                        if title_item:
                            title_item.setToolTip(new_description_text)

                        # Update displayed description
                        te.setPlainText(new_description_text)

                        # Reload data for history
                        with open(path, 'r') as f:
                            data.clear()
                            data.update(yaml.safe_load(f))

                        QMessageBox.information(editor, "[OK] Success", "Description updated successfully!")
                        editor.close()

                    except Exception as e:
                        QMessageBox.critical(editor, "[ERROR] Failed", f"Failed to save description:<br>{str(e)}")

                # Override accepted signal to call our save handler
                editor.accepted.connect(on_editor_save)

                # Show as non-modal window
                editor.show()

                # Store reference to prevent garbage collection
                editor_dialogs.append(editor)

                # Cleanup when closed
                def on_editor_closed():
                    if editor in editor_dialogs:
                        editor_dialogs.remove(editor)

                editor.finished.connect(on_editor_closed)

            def on_show_history():
                """Show enhanced history dialog with visual diffs (non-modal)"""
                # Create non-modal history dialog
                history_dlg = DescriptionHistoryDialog(data, path, dlg2)
                history_dlg.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint)
                history_dlg.setWindowTitle(f"Description History - {data.get('id', '')}")

                # Define reload handler for when history is closed
                def on_history_closed():
                    # Reload data in case version was restored
                    try:
                        with open(path, 'r') as f:
                            data.clear()
                            data.update(yaml.safe_load(f))

                        # Update displayed description if it changed
                        te.setPlainText(data.get('description', ''))

                        # Update the descriptions array
                        self._descriptions[row-1] = data.get('description', '')

                        # Update tooltip in table
                        title_item = tbl.item(row, col)
                        if title_item:
                            title_item.setToolTip(data.get('description', ''))

                    except Exception as e:
                        print(f"Error reloading data after history dialog: {e}")

                    # Cleanup reference
                    if history_dlg in history_dialogs:
                        history_dialogs.remove(history_dlg)

                # Connect close handler
                history_dlg.finished.connect(on_history_closed)

                # Show as non-modal window
                history_dlg.show()

                # Store reference to prevent garbage collection
                history_dialogs.append(history_dlg)

            btn_modify.clicked.connect(on_modify_description)
            btn_history.clicked.connect(on_show_history)
            btn_close.clicked.connect(dlg2.close)

            # Show as non-modal window (allows multiple descriptions open + interaction with issue viewer)
            dlg2.show()

            # Store reference to prevent garbage collection
            description_dialogs.append(dlg2)

            # Clean up reference when dialog is closed
            def on_dialog_closed():
                if dlg2 in description_dialogs:
                    description_dialogs.remove(dlg2)

            dlg2.finished.connect(on_dialog_closed)

        def on_modify():
            selected_rows = tbl.selectedItems()
            if not selected_rows:
                return

            # Get all unique selected rows (excluding row 0 which is the filter row)
            rows_to_modify = set(item.row() for item in selected_rows if item.row() > 0)
            if not rows_to_modify:
                return

            # Store current values before modification
            for r in rows_to_modify:
                # Create status combo
                cb = QComboBox()
                cb.addItems(self.STATUS_OPTIONS)
                current_status = tbl.item(r, 4).text() if tbl.item(r, 4) else ""
                cb.setCurrentText(current_status)
                tbl.setCellWidget(r, 4, cb)
                self._status_combos.append((r, cb))

                # Assignee
                assignee_cb = QComboBox()
                assignee_cb.addItems(self.assignees)
                current_assignee = tbl.item(r, 3).text() if tbl.item(r, 3) else ""
                assignee_cb.setCurrentText(current_assignee)
                tbl.setCellWidget(r, 3, assignee_cb)

                # Due Date
                date_time_layout = QVBoxLayout()
                date_time_layout.setSpacing(2)  # Reduce spacing between elements
                date_time_layout.setContentsMargins(0, 0, 0, 0)

                # Display current value as text
                current_value = tbl.item(r, 6).text() if tbl.item(r, 6) else ""
                current_value_label = QLabel("Original:")
                current_value_label.setStyleSheet("color: #666666; font-size: 9px; padding: 2px;")
                date_time_layout.addWidget(current_value_label)

                # Create vertical layout for date and time inputs
                input_layout = QVBoxLayout()
                input_layout.setContentsMargins(0, 0, 0, 0)
                input_layout.setSpacing(2)  # Reduce spacing between date and time

                # Add date widget
                date_edit = QDateEdit()
                date_edit.setCalendarPopup(True)
                date_edit.setDisplayFormat("yyyy-MM-dd")
                input_layout.addWidget(date_edit)

                # Add time widget
                time_edit = QTimeEdit()
                time_edit.setDisplayFormat("HH:mm")
                input_layout.addWidget(time_edit)

                # Set values for the edit widgets
                if current_value:
                    try:
                        if len(current_value) > 10:  # Contains time
                            date_str, time_str = current_value.split(" ")
                            date = QDate.fromString(date_str, "yyyy-MM-dd")
                            time = QTime.fromString(time_str, "HH:mm")
                            date_edit.setDate(date)
                            time_edit.setTime(time)
                        else:
                            date = QDate.fromString(current_value, "yyyy-MM-dd")
                            date_edit.setDate(date)
                            time_edit.setTime(QTime(0, 0))
                    except:
                        date_edit.setDate(QDate.currentDate())
                        time_edit.setTime(QTime.currentTime())
                else:
                    date_edit.setDate(QDate.currentDate())
                    time_edit.setTime(QTime.currentTime())

                date_time_layout.addLayout(input_layout)

                date_time_widget = QWidget()
                date_time_widget.setLayout(date_time_layout)
                tbl.setCellWidget(r, 6, date_time_widget)

                # Severity
                severity_cb = QComboBox()
                severity_cb.addItems(["Critical", "Major", "Minor", "Enhancement", "Info"])
                severity_cb.setCurrentText(tbl.item(r, 7).text() if tbl.item(r, 7) else "")
                tbl.setCellWidget(r, 7, severity_cb)

                # Stage
                stage_cb = QComboBox()
                stage_cb.setEditable(True)
                stage_cb.addItems(["casino", "design", "dk", "syn", "dft", "lec", "sta", "ldrc", "vclp", "sim",
                               "floorplan", "place", "cts", "route", "pex", "pv", "psi", "bump", "signoff"])
                stage_cb.setCurrentText(tbl.item(r, 8).text() if tbl.item(r, 8) else "")
                tbl.setCellWidget(r, 8, stage_cb)

                # Blocks
                list_widget = QListWidget()
                list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
                for blk in self.blks:
                    list_widget.addItem(blk)
                current_blocks = tbl.item(r, 9).text().split(", ") if tbl.item(r, 9) and tbl.item(r, 9).text() else []
                for i in range(list_widget.count()):
                    item = list_widget.item(i)
                    item.setSelected(item.text() in current_blocks)

                list_widget.setMinimumHeight(100)
                list_widget.setMaximumHeight(150)
                tbl.setCellWidget(r, 9, list_widget)
                tbl.setRowHeight(r, max(tbl.rowHeight(r), 120))

        def on_cancel_modify():
            """Cancel modification and restore original values"""
            # Get all modified rows
            modified_rows = set(row for row, _ in self._status_combos)

            # Restore original cells by repopulating from data
            for r in modified_rows:
                if r <= 0:  # Skip filter row
                    continue

                try:
                    path = self._issue_paths[r-1]
                    with open(path, 'r') as f:
                        d = yaml.safe_load(f)

                    # Clear all cell widgets first (important for Due Date and other complex widgets)
                    for c in [3, 4, 6, 7, 8, 9]:  # Columns that may have widgets
                        tbl.removeCellWidget(r, c)

                    # Restore all fields to original values
                    tbl.setItem(r, 3, QTableWidgetItem(d.get('assignee', '')))
                    tbl.setItem(r, 4, QTableWidgetItem(d.get('status', '')))
                    tbl.setItem(r, 6, QTableWidgetItem(d.get('due_date', '')))
                    tbl.setItem(r, 7, QTableWidgetItem(d.get('severity', '')))
                    tbl.setItem(r, 8, QTableWidgetItem(d.get('stage', '')))
                    tbl.setItem(r, 9, QTableWidgetItem(", ".join(d.get('blocks', []))))

                    # Apply status color
                    status = d.get('status', '')
                    status_color = self.STATUS_COLORS.get(status)
                    if status_color:
                        for c in range(tbl.columnCount()):
                            if c != 7:  # Skip severity column
                                item = tbl.item(r, c)
                                if item:
                                    item.setBackground(status_color)

                    # Apply severity color
                    severity = d.get('severity', '')
                    severity_color = self.SEVERITY_COLORS.get(severity)
                    if severity_color:
                        severity_cell = tbl.item(r, 7)
                        if severity_cell:
                            severity_cell.setBackground(severity_color)

                    # Reset row height
                    tbl.setRowHeight(r, tbl.rowHeight(0))
                except Exception as e:
                    logging.error(f"Error canceling modification for row {r}: {e}")

            # Clear status combo tracking
            self._status_combos.clear()
            btn_modify.setEnabled(True)

        def on_save():
            changes_made = False
            save_errors = []
            modified_rows = set(row for row, _ in self._status_combos)

            try:
                # Save changes for all modified rows
                for r in modified_rows:
                    if r <= 0:  # Skip filter row
                        continue

                    path = self._issue_paths[r-1]
                    with open(path, 'r') as f:
                        d = yaml.safe_load(f)

                    original_data = d.copy()

                    # Get all modified values
                    status_widget = tbl.cellWidget(r, 4)
                    if status_widget:
                        d['status'] = status_widget.currentText()

                    assignee_widget = tbl.cellWidget(r, 3)
                    if assignee_widget:
                        d['assignee'] = assignee_widget.currentText()

                    date_time_widget = tbl.cellWidget(r, 6)
                    if date_time_widget and date_time_widget.layout():
                        input_layout = date_time_widget.layout().itemAt(1).layout()
                        if input_layout:
                            date_edit = input_layout.itemAt(0).widget()
                            time_edit = input_layout.itemAt(1).widget()
                            if date_edit and time_edit:
                                d['due_date'] = f"{date_edit.date().toString('yyyy-MM-dd')} {time_edit.time().toString('HH:mm')}"

                    severity_widget = tbl.cellWidget(r, 7)
                    if severity_widget:
                        d['severity'] = severity_widget.currentText()

                    stage_widget = tbl.cellWidget(r, 8)
                    if stage_widget:
                        d['stage'] = stage_widget.currentText()

                    blocks_widget = tbl.cellWidget(r, 9)
                    if blocks_widget:
                        new_blocks = []
                        for i in range(blocks_widget.count()):
                            if blocks_widget.item(i).isSelected():
                                new_blocks.append(blocks_widget.item(i).text())
                        if new_blocks:  # Only update if blocks were modified
                            d['modules'] = new_blocks

                    # Save if changes were made
                    if d != original_data:
                        try:
                            with open(path, 'w') as f:
                                yaml.safe_dump(d, f)
                            changes_made = True
                        except Exception as e:
                            save_errors.append(f"Failed to save changes for issue {d.get('id', '')}: {str(e)}")

                # Show appropriate message
                if save_errors:
                    error_msg = "\n".join(save_errors)
                    QMessageBox.warning(dlg, "Save Errors", f"Some changes could not be saved:\n{error_msg}")
                elif changes_made:
                    QMessageBox.information(dlg, "Success", "All changes saved successfully.")
                else:
                    QMessageBox.information(dlg, "No Changes", "No changes were made to save.")

                # Refresh the table
                populate()

            except Exception as e:
                QMessageBox.critical(dlg, "Error", f"An error occurred while saving changes: {str(e)}")

        def on_delete():
            selected_items = tbl.selectedItems()
            if not selected_items:
                QMessageBox.warning(dlg, "Warning", "Please select an issue to delete.")
                return

            row = selected_items[0].row()
            if row <= 0:  # Skip if filter row is selected
                return

            issue_id = tbl.item(row, 0).text()
            issue_path = self._issue_paths[row-1]

            try:
                # Load issue data
                with open(issue_path, 'r') as f:
                    issue_data = yaml.safe_load(f)

                # Create confirmation dialog with issue details
                confirm_dlg = QDialog(dlg)
                confirm_dlg.setWindowTitle("Confirm Delete Issue")
                confirm_layout = QVBoxLayout(confirm_dlg)

                # Add issue details
                details = QTextEdit()
                details.setReadOnly(True)
                details_text = f"""
ID: {issue_data.get('id', '')}
Title: {issue_data.get('title', '')}
Status: {issue_data.get('status', '')}
Severity: {issue_data.get('severity', '')}
Stage: {issue_data.get('stage', '')}
Assigner: {issue_data.get('assigner', '')}
Assignee: {issue_data.get('assignee', '')}
Created: {issue_data.get('created_at', '')}
Blocks: {', '.join(issue_data.get('modules', []))}
Run Directory: {issue_data.get('run_id', '')}

Description:
{issue_data.get('description', '')}
"""
                details.setPlainText(details_text)
                confirm_layout.addWidget(details)

                # Add warning message
                warning_label = QLabel("Are you sure you want to delete this issue?")
                warning_label.setStyleSheet("color: red; font-weight: bold;")
                confirm_layout.addWidget(warning_label)

                # Add buttons
                btn_layout = QHBoxLayout()
                btn_yes = QPushButton("Yes, Delete")
                style_button(btn_yes, "danger")
                btn_no = QPushButton("No, Cancel")
                style_button(btn_no, "gray")
                btn_layout.addWidget(btn_yes)
                btn_layout.addWidget(btn_no)
                confirm_layout.addLayout(btn_layout)

                def proceed_delete():
                    try:
                        # Move issue file to deleted directory
                        deleted_filename = f"deleted_{os.path.basename(issue_path)}"
                        deleted_path = os.path.join(self.deleted_dir, deleted_filename)
                        shutil.move(issue_path, deleted_path)

                        # Move the issue-specific attachment directory to deleted attachments directory
                        issue_attach_dir = os.path.join(self.attach_dir, issue_id)
                        if os.path.exists(issue_attach_dir):
                            deleted_attach_dir = os.path.join(self.deleted_attach_dir, issue_id)
                            if os.path.exists(deleted_attach_dir):
                                shutil.rmtree(deleted_attach_dir)
                            shutil.move(issue_attach_dir, deleted_attach_dir)

                        # Update the table
                        populate()
                        QMessageBox.information(dlg, "Success", f"Issue {issue_id} has been moved to deleted issues.")
                        confirm_dlg.accept()
                    except Exception as e:
                        QMessageBox.critical(confirm_dlg, "Error", f"Failed to delete issue: {str(e)}")

                btn_yes.clicked.connect(proceed_delete)
                btn_no.clicked.connect(confirm_dlg.reject)

                confirm_dlg.resize(600, 400)
                if confirm_dlg.exec_() == QDialog.Accepted:
                    self._update_summary_table()

            except Exception as e:
                QMessageBox.critical(dlg, "Error", f"Failed to process issue: {str(e)}")

        def on_restore():
            # Create dialog to show deleted issues
            restore_dlg = QDialog(dlg)
            restore_dlg.setWindowTitle("Restore Deleted Issue")
            restore_layout = QVBoxLayout(restore_dlg)

            # Create table for deleted issues
            restore_tbl = QTableWidget()
            restore_tbl.setColumnCount(4)
            restore_tbl.setHorizontalHeaderLabels(["ID", "Title", "Deleted Date", "Assignee"])
            restore_tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            restore_tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            restore_tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
            restore_tbl.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)

            # Populate deleted issues
            deleted_issues = []
            if os.path.exists(self.deleted_dir):
                for fn in os.listdir(self.deleted_dir):
                    if fn.startswith('deleted_') and fn.endswith('.yaml'):
                        path = os.path.join(self.deleted_dir, fn)
                        try:
                            with open(path, 'r') as f:
                                data = yaml.safe_load(f)
                                deleted_issues.append((data, path))
                        except Exception:
                            continue

            restore_tbl.setRowCount(len(deleted_issues))
            for i, (data, path) in enumerate(deleted_issues):
                restore_tbl.setItem(i, 0, QTableWidgetItem(data.get('id', '')))
                restore_tbl.setItem(i, 1, QTableWidgetItem(data.get('title', '')))
                restore_tbl.setItem(i, 2, QTableWidgetItem(data.get('created_at', '')))
                restore_tbl.setItem(i, 3, QTableWidgetItem(data.get('assignee', '')))
                restore_tbl.item(i, 0).setData(Qt.UserRole, path)

            restore_layout.addWidget(restore_tbl)

            # Add restore button
            btn_restore_issue = QPushButton("Restore Selected Issue")
            style_button(btn_restore_issue, "action")

            def restore_selected():
                selected_items = restore_tbl.selectedItems()
                if not selected_items:
                    QMessageBox.warning(restore_dlg, "Warning", "Please select an issue to restore.")
                    return

                row = selected_items[0].row()
                issue_path = restore_tbl.item(row, 0).data(Qt.UserRole)
                issue_id = restore_tbl.item(row, 0).text()

                try:
                    # Load issue data
                    with open(issue_path, 'r') as f:
                        issue_data = yaml.safe_load(f)

                    # Create confirmation dialog with issue details
                    confirm_dlg = QDialog(restore_dlg)
                    confirm_dlg.setWindowTitle("Confirm Restore Issue")
                    confirm_layout = QVBoxLayout(confirm_dlg)

                    # Add issue details
                    details = QTextEdit()
                    details.setReadOnly(True)
                    details_text = f"""
ID: {issue_data.get('id', '')}
Title: {issue_data.get('title', '')}
Status: {issue_data.get('status', '')}
Severity: {issue_data.get('severity', '')}
Stage: {issue_data.get('stage', '')}
Assigner: {issue_data.get('assigner', '')}
Assignee: {issue_data.get('assignee', '')}
Created: {issue_data.get('created_at', '')}
Blocks: {', '.join(issue_data.get('modules', []))}
Run Directory: {issue_data.get('run_id', '')}

Description:
{issue_data.get('description', '')}
"""
                    details.setPlainText(details_text)
                    confirm_layout.addWidget(details)

                    # Add confirmation message
                    confirm_label = QLabel("Are you sure you want to restore this issue?")
                    confirm_label.setStyleSheet("color: green; font-weight: bold;")
                    confirm_layout.addWidget(confirm_label)

                    # Add buttons
                    btn_layout = QHBoxLayout()
                    btn_yes = QPushButton("Yes, Restore")
                    style_button(btn_yes, "action")
                    btn_no = QPushButton("No, Cancel")
                    style_button(btn_no, "gray")
                    btn_layout.addWidget(btn_yes)
                    btn_layout.addWidget(btn_no)
                    confirm_layout.addLayout(btn_layout)

                    def proceed_restore():
                        try:
                            # Move issue file back to active directory
                            new_path = os.path.join(self.fast_dir, os.path.basename(issue_path).replace('deleted_', ''))
                            shutil.move(issue_path, new_path)

                            # Move the issue-specific attachment directory back to attachments
                            deleted_attach_dir = os.path.join(self.deleted_attach_dir, issue_id)
                            if os.path.exists(deleted_attach_dir):
                                issue_attach_dir = os.path.join(self.attach_dir, issue_id)
                                if os.path.exists(issue_attach_dir):
                                    shutil.rmtree(issue_attach_dir)
                                shutil.move(deleted_attach_dir, issue_attach_dir)

                            QMessageBox.information(confirm_dlg, "Success", "Issue has been restored successfully.")
                            confirm_dlg.accept()
                            restore_dlg.accept()
                            populate()  # Refresh main table
                            self._update_summary_table()
                        except Exception as e:
                            QMessageBox.critical(confirm_dlg, "Error", f"Failed to restore issue: {str(e)}")

                    btn_yes.clicked.connect(proceed_restore)
                    btn_no.clicked.connect(confirm_dlg.reject)

                    confirm_dlg.resize(600, 400)
                    confirm_dlg.exec_()

                except Exception as e:
                    QMessageBox.critical(restore_dlg, "Error", f"Failed to process issue: {str(e)}")

            btn_restore_issue.clicked.connect(restore_selected)
            restore_layout.addWidget(btn_restore_issue)

            restore_dlg.resize(800, 400)
            restore_dlg.exec_()

        def apply_filters():
            patterns = {}
            # compile column regex, skip invalid
            for c, le in self.col_filters:
                txt = le.text()
                if not txt:
                    continue
                try:
                    patterns[c] = re.compile(txt)
                except re.error:
                    continue
            # compile description regex, skip invalid
            desc_pat = None
            txt_desc = desc_search.text()
            if txt_desc:
                try:
                    desc_pat = re.compile(txt_desc)
                except re.error:
                    desc_pat = None
            for r in range(1, tbl.rowCount()):
                show = True
                # filter columns
                for c, pat in patterns.items():
                    widget = tbl.cellWidget(r, c)
                    val = widget.currentText() if widget else tbl.item(r, c).text()
                    if not pat.search(val):
                        show = False
                        break
                # filter description
                if show and desc_pat and not desc_pat.search(self._descriptions[r-1]):
                    show = False
                tbl.setRowHidden(r, not show)

        def on_auto_size():
            # Reset all column widths and row heights first
            for col in range(tbl.columnCount()):
                tbl.setColumnWidth(col, tbl.horizontalHeader().defaultSectionSize())
            for row in range(tbl.rowCount()):
                tbl.setRowHeight(row, tbl.verticalHeader().defaultSectionSize())

            # Adjust column widths based on content
            for col in range(tbl.columnCount()):
                max_width = 0
                # Get header width
                header_width = tbl.horizontalHeader().sectionSize(col)
                max_width = max(max_width, header_width)

                # Check content width for each row
                for row in range(tbl.rowCount()):
                    item = tbl.item(row, col)
                    if item:
                        # Calculate text width (approximate)
                        if col == 9:  # Blocks column
                            # For blocks, consider the longest line
                            lines = item.text().split('\n')
                            text_width = max(len(line) for line in lines) * 8
                        else:
                            text_width = len(item.text()) * 8
                        max_width = max(max_width, text_width)

                # Set column width with some padding
                tbl.setColumnWidth(col, max_width + 20)

            # Adjust row heights based on content
            for row in range(tbl.rowCount()):
                max_height = 0
                for col in range(tbl.columnCount()):
                    item = tbl.item(row, col)
                    if item:
                        # For blocks column, count newlines
                        if col == 9:  # Blocks column
                            line_count = item.text().count('\n') + 1
                            height = line_count * 20  # Approximate height per line
                            max_height = max(max_height, height)
                        else:
                            # For other columns, use default height
                            max_height = max(max_height, 25)

                # Set row height with some padding, but cap it at a reasonable maximum
                tbl.setRowHeight(row, min(max_height + 10, 200))  # Cap at 200 pixels

        def on_refresh():
            # Reset all column widths and row heights to default
            for col in range(tbl.columnCount()):
                tbl.setColumnWidth(col, tbl.horizontalHeader().defaultSectionSize())
            for row in range(tbl.rowCount()):
                tbl.setRowHeight(row, tbl.verticalHeader().defaultSectionSize())

            # Reset blocks column formatting
            for row in range(1, tbl.rowCount()):  # Start from 1 to skip header row
                item = tbl.item(row, 9)  # Blocks column
                if item:
                    blocks = item.text().split(', ')  # Split by comma and space
                    blocks_text = '\n'.join(blocks)  # Join with newlines
                    item.setText(blocks_text)
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)

        def on_attach():
            r = tbl.currentRow()
            if r <= 0:  # Skip if no row or filter row is selected
                QMessageBox.warning(dlg, "Warning", "Please select an issue first.")
                return

            path = self._issue_paths[r-1]
            try:
                with open(path, 'r') as f:
                    data = yaml.safe_load(f)
                attachments = data.get('attachments', [])

                if not attachments:
                    QMessageBox.information(dlg, "No Attachments", "This issue has no attachments.")
                    return

                # Create a dialog to show attachments
                attach_dlg = QDialog(dlg)
                attach_dlg.setWindowTitle("Select Attachments to Open")
                attach_dlg.setMinimumWidth(600)  # Increased width for better readability
                attach_layout = QVBoxLayout(attach_dlg)

                # Add a label with more information
                attach_layout.addWidget(QLabel("Select attachments to open:"))
                info_label = QLabel("? Images will open with eog\n? Text files will open with gvim")
                info_label.setStyleSheet("color: #666666; font-size: 8pt;")
                attach_layout.addWidget(info_label)

                # Create a scroll area for attachments
                scroll = QScrollArea()
                scroll.setWidgetResizable(True)
                scroll_widget = QWidget()
                scroll_layout = QVBoxLayout(scroll_widget)

                # Create checkboxes for each attachment
                checkboxes = []
                for a in attachments:
                    if os.path.exists(a):
                        filename = os.path.basename(a)
                        ext = os.path.splitext(filename)[1].lower()
                        is_image = ext in IMAGE_EXTS

                        # Create a widget for each attachment with more info
                        attach_widget = QWidget()
                        attach_layout_h = QHBoxLayout(attach_widget)
                        attach_layout_h.setContentsMargins(0, 0, 0, 0)

                        # Add checkbox with file name
                        cb = QCheckBox(filename)
                        cb.setChecked(True)

                        # Add file type and size info
                        file_size = os.path.getsize(a)
                        size_str = f"{file_size/1024:.1f} KB" if file_size < 1024*1024 else f"{file_size/(1024*1024):.1f} MB"
                        type_label = QLabel(f"({'Image' if is_image else 'Text'} - {size_str})")
                        type_label.setStyleSheet("color: #666666; font-size: 8pt;")

                        attach_layout_h.addWidget(cb)
                        attach_layout_h.addWidget(type_label)
                        attach_layout_h.addStretch()

                        # Store full path as tooltip
                        attach_widget.setToolTip(a)

                        checkboxes.append((cb, a, is_image))
                        scroll_layout.addWidget(attach_widget)
                    else:
                        missing_widget = QWidget()
                        missing_layout = QHBoxLayout(missing_widget)
                        missing_layout.setContentsMargins(0, 0, 0, 0)

                        missing_label = QLabel(f"Missing: {os.path.basename(a)}")
                        missing_label.setStyleSheet("color: red;")
                        missing_layout.addWidget(missing_label)
                        missing_layout.addStretch()

                        scroll_layout.addWidget(missing_widget)

                scroll_layout.addStretch()
                scroll.setWidget(scroll_widget)
                attach_layout.addWidget(scroll)

                if not checkboxes:
                    QMessageBox.warning(dlg, "Error", "No valid attachments found.")
                    return

                # Add control buttons
                ctrl_layout = QHBoxLayout()
                select_all = QPushButton("Select All")
                select_none = QPushButton("Select None")
                style_button(select_all, "gray")
                style_button(select_none, "gray")
                ctrl_layout.addWidget(select_all)
                ctrl_layout.addWidget(select_none)
                ctrl_layout.addStretch()
                attach_layout.addLayout(ctrl_layout)

                # Add action buttons
                btn_layout = QHBoxLayout()
                btn_open = QPushButton("Open Selected")
                style_button(btn_open, "action")
                btn_cancel = QPushButton("Cancel")
                style_button(btn_cancel, "gray")
                btn_layout.addStretch()
                btn_layout.addWidget(btn_open)
                btn_layout.addWidget(btn_cancel)
                attach_layout.addLayout(btn_layout)

                def select_all_files():
                    for cb, _, _ in checkboxes:
                        cb.setChecked(True)

                def select_none_files():
                    for cb, _, _ in checkboxes:
                        cb.setChecked(False)

                def open_selected_files():
                    # Separate image and text files
                    image_files = []
                    text_files = []

                    for cb, filepath, is_image in checkboxes:
                        if cb.isChecked() and os.path.exists(filepath):
                            if is_image:
                                image_files.append(filepath)
                            else:
                                text_files.append(filepath)

                    if not image_files and not text_files:
                        QMessageBox.warning(attach_dlg, "Warning", "Please select at least one file to open.")
                        return

                    try:
                        # Handle image files
                        for img_file in image_files:
                            try:
                                # Start eog in a new session to prevent duplicate windows
                                process = subprocess.Popen(['eog', img_file],
                                              start_new_session=True,
                                              stdout=subprocess.DEVNULL,
                                              stderr=subprocess.DEVNULL)
                                if process.poll() is not None:  # Check if process failed to start
                                    raise subprocess.SubprocessError(f"Failed to start eog process for {img_file}")
                            except Exception as e:
                                logging.error(f"Failed to open image {os.path.basename(img_file)}: {str(e)}")
                                QMessageBox.warning(
                                    attach_dlg,
                                    "Error",
                                    f"Failed to open image {os.path.basename(img_file)}: {str(e)}"
                                )

                        # Handle text files
                        for txt_file in text_files:
                            try:
                                # Convert Windows path if needed
                                if sys.platform == 'win32':
                                    txt_file = txt_file.replace('\\', '/')

                                # Try to open with gvim
                                process = subprocess.Popen(['gvim', '-f', txt_file],
                                              stdout=subprocess.DEVNULL,
                                              stderr=subprocess.DEVNULL)
                                if process.poll() is not None:  # Check if process failed to start
                                    raise subprocess.SubprocessError(f"Failed to start gvim process for {txt_file}")

                            except Exception as e:
                                logging.error(f"Failed to open text file {os.path.basename(txt_file)}: {str(e)}")
                                QMessageBox.warning(
                                    attach_dlg,
                                    "Error",
                                    f"Failed to open text file {os.path.basename(txt_file)}: {str(e)}"
                                )

                    except Exception as e:
                        logging.error(f"Failed to open some files: {str(e)}")
                        QMessageBox.warning(
                            attach_dlg,
                            "Error",
                            f"Failed to open some files: {str(e)}"
                        )

                # Connect button signals
                select_all.clicked.connect(select_all_files)
                select_none.clicked.connect(select_none_files)
                btn_open.clicked.connect(open_selected_files)
                btn_cancel.clicked.connect(attach_dlg.reject)

                # Show dialog
                attach_dlg.exec_()

            except Exception as e:
                QMessageBox.critical(dlg, "Error", f"Failed to process attachments: {str(e)}")

        def generate_html_summary():
            try:
                # Create summary directory if it doesn't exist
                summary_dir = os.path.join(self.fast_dir, "summary")
                os.makedirs(summary_dir, exist_ok=True)

                # Generate filename with timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d__%H:%M:%S")
                default_filename = f"issue_summary_{timestamp}.html"
                file_path = os.path.join(summary_dir, default_filename)

                # Collect all issues
                issues = []
                for fn in os.listdir(fast_dir):
                    if not fn.endswith(('.yaml','.yml')):
                        continue
                    path = os.path.join(fast_dir, fn)
                    try:
                        data = yaml.safe_load(open(path))
                        issues.append(data)
                    except Exception:
                        continue

                # Sort issues by creation date (newest first)
                issues.sort(key=lambda x: x.get('created_at', ''), reverse=True)

                # Generate HTML content
                html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Issue Summary - {self.prj_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .status-open {{ background-color: #FFF4E6; }}
        .status-in-progress {{ background-color: #E3F2FD; }}
        .status-resolved {{ background-color: #E8F5E9; }}
        .status-closed {{ background-color: #F5F5F5; }}
        .severity-critical {{ background-color: #D32F2F; color: white; }}
        .severity-major {{ background-color: #F57C00; color: white; }}
        .severity-minor {{ background-color: #FBC02D; }}
        .severity-enhancement {{ background-color: #388E3C; color: white; }}
        .severity-info {{ background-color: #E0E0E0; }}
        .overdue {{ color: red; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>Issue Summary - {self.prj_name}</h1>
    <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

    <h2>Summary</h2>
    <table>
        <tr>
            <th>Status</th>
            <th>Count</th>
        </tr>
"""

                # Add status counts
                status_counts = {"Open": 0, "In Progress": 0, "Resolved": 0, "Closed": 0}
                for issue in issues:
                    status = issue.get('status', '')
                    if status in status_counts:
                        status_counts[status] += 1

                for status, count in status_counts.items():
                    html_content += f"""
        <tr>
            <td>{status}</td>
            <td>{count}</td>
        </tr>"""

                html_content += """
    </table>

    <h2>Issues</h2>
    <table>
        <tr>
            <th>ID</th>
            <th>Title</th>
            <th>Status</th>
            <th>Severity</th>
            <th>Stage</th>
            <th>Assigner</th>
            <th>Assignee</th>
            <th>Created</th>
            <th>Due Date</th>
            <th>Blocks</th>
        </tr>"""

                # Add issues
                for issue in issues:
                    status = issue.get('status', '')
                    severity = issue.get('severity', '')
                    due_date = issue.get('due_date', '')

                    # Check if overdue
                    overdue_class = ""
                    if due_date:
                        try:
                            if len(due_date) > 10:  # Contains time
                                due_datetime = datetime.strptime(due_date, "%Y-%m-%d %H:%M")
                            else:
                                due_datetime = datetime.strptime(due_date, "%Y-%m-%d")
                            if due_datetime < datetime.now():
                                overdue_class = "overdue"
                        except:
                            pass

                    html_content += f"""
        <tr>
            <td>{issue.get('id', '')}</td>
            <td>{issue.get('title', '')}</td>
            <td class="status-{status.lower().replace(' ', '-')}">{status}</td>
            <td class="severity-{severity.lower()}">{severity}</td>
            <td>{issue.get('stage', '')}</td>
            <td>{issue.get('assigner', '')}</td>
            <td>{issue.get('assignee', '')}</td>
            <td>{issue.get('created_at', '')}</td>
            <td class="{overdue_class}">{due_date}</td>
            <td>{', '.join(issue.get('modules', []))}</td>
        </tr>"""

                html_content += """
    </table>
</body>
</html>"""

                # Write to file
                with open(file_path, 'w') as f:
                    f.write(html_content)

                QMessageBox.information(dlg, "Success", f"HTML summary saved to:\n{file_path}")

            except Exception as e:
                QMessageBox.critical(dlg, "Error", f"Failed to generate HTML summary: {str(e)}")

        # Connect signals
        tbl.cellClicked.connect(on_row_selected)
        tbl.cellClicked.connect(on_cell_clicked)
        desc_search.textChanged.connect(apply_filters)
        for _, le in self.col_filters:
            le.textChanged.connect(apply_filters)
        btn_modify.clicked.connect(on_modify)
        btn_save.clicked.connect(on_save)
        btn_delete.clicked.connect(on_delete)
        btn_restore.clicked.connect(on_restore)
        btn_auto_size.clicked.connect(on_auto_size)
        btn_refresh.clicked.connect(on_refresh)
        btn_close.clicked.connect(dlg.close)
        btn_det.clicked.connect(on_attach)
        btn_html.clicked.connect(generate_html_summary)

        # ESC key to cancel modify mode
        esc_shortcut = QShortcut(QKeySequence("Escape"), dlg)
        esc_shortcut.activated.connect(on_cancel_modify)

        # Context menu (right-click) handler
        def show_context_menu(position):
            """Show context menu on right-click"""
            # Get the item at the clicked position
            item = tbl.itemAt(position)
            if not item:
                return

            row = item.row()
            if row <= 0:  # Skip filter row
                return

            # Create context menu
            from PyQt5.QtWidgets import QMenu
            menu = QMenu(tbl)

            # Add menu actions matching the buttons
            modify_action = menu.addAction("- Modify Status")
            save_action = menu.addAction("- Save Changes")
            menu.addSeparator()
            attach_action = menu.addAction("- Check Attachments")
            menu.addSeparator()
            delete_action = menu.addAction("- Delete Issue")
            restore_action = menu.addAction("- Restore Issue")
            menu.addSeparator()
            refresh_action = menu.addAction("- Refresh")
            export_action = menu.addAction("- Export HTML")

            # Execute the menu and handle the action
            action = menu.exec_(tbl.viewport().mapToGlobal(position))

            if action == modify_action:
                on_modify()
            elif action == save_action:
                on_save()
            elif action == attach_action:
                on_attach()
            elif action == delete_action:
                on_delete()
            elif action == restore_action:
                on_restore()
            elif action == refresh_action:
                on_refresh()
            elif action == export_action:
                generate_html_summary()

        # Connect context menu to table
        tbl.customContextMenuRequested.connect(show_context_menu)

        populate()
        dlg.resize(1200,600)
        dlg.exec_()
        # Update summary table after dialog is closed
        self._update_summary_table()

    def _update_summary_table(self):
        """Update the summary table with current issue counts"""
        fast_dir = os.path.join(self.proj_dir, "FastTrack")
        if not os.path.isdir(fast_dir):
            return

        # Initialize counts
        counts = {
            "Open": 0,
            "In Progress": 0,
            "Resolved": 0,
            "Closed": 0,
            "Total": 0
        }

        # Count issues by status
        for fn in os.listdir(fast_dir):
            if not fn.endswith(('.yaml','.yml')):
                continue
            path = os.path.join(fast_dir, fn)
            try:
                data = yaml.safe_load(open(path))
                status = data.get('status', '')
                if status in counts:
                    counts[status] += 1
                counts["Total"] += 1
            except Exception:
                pass

        # Update table
        for status, row in self.status_rows.items():
            count_item = self.summary_table.item(row, 1)
            count_item.setText(str(counts[status]))

            # Highlight Open issues
            if status == "Open" and counts[status] > 0:
                for col in range(2):
                    item = self.summary_table.item(row, col)
                    item.setForeground(QColor("#dc3545"))  # Red text for Open issues
            else:
                for col in range(2):
                    item = self.summary_table.item(row, col)
                    item.setForeground(QColor("#000000"))  # Black text for other statuses

    def _view_open_issues(self):
        """Show detailed information about Open issues"""
        fast_dir = os.path.join(self.proj_dir, "FastTrack")
        if not os.path.isdir(fast_dir):
            QMessageBox.warning(self, "Error", "No FastTrack directory found.")
            return

        # Collect Open issues
        open_issues = []
        for fn in os.listdir(fast_dir):
            if not fn.endswith(('.yaml','.yml')):
                continue
            path = os.path.join(fast_dir, fn)
            try:
                data = yaml.safe_load(open(path))
                if data.get('status') == 'Open':
                    open_issues.append(data)
            except Exception:
                pass

        if not open_issues:
            QMessageBox.information(self, "Open Issues", "No Open issues found.")
            return

        # Create dialog to show Open issues
        dlg = QDialog(self)
        dlg.setWindowTitle("Open Issues Details")
        dlg.setMinimumWidth(800)
        dlg.setMinimumHeight(500)

        layout = QVBoxLayout(dlg)

        # Add table for Open issues
        table = QTableWidget()
        table.setColumnCount(7)  # Added Assigner column
        table.setRowCount(len(open_issues))
        table.setHorizontalHeaderLabels(["ID", "Title", "Assigner", "Assignee", "Created", "Severity", "Stage"])

        # Populate table
        for i, issue in enumerate(sorted(open_issues, key=lambda x: x.get('created_at', ''), reverse=True)):
            table.setItem(i, 0, QTableWidgetItem(issue.get('id', '')))
            table.setItem(i, 1, QTableWidgetItem(issue.get('title', '')))
            table.setItem(i, 2, QTableWidgetItem(issue.get('assigner', '')))  # Added Assigner
            table.setItem(i, 3, QTableWidgetItem(issue.get('assignee', '')))
            table.setItem(i, 4, QTableWidgetItem(issue.get('created_at', '')))
            table.setItem(i, 5, QTableWidgetItem(issue.get('severity', '')))
            table.setItem(i, 6, QTableWidgetItem(issue.get('stage', '')))

            # Set tooltip with description
            title_item = table.item(i, 1)
            title_item.setToolTip(issue.get('description', ''))

            # Color severity
            severity_item = table.item(i, 5)  # Updated index for severity column
            severity = issue.get('severity', '')
            if severity in self.SEVERITY_COLORS:
                severity_item.setBackground(self.SEVERITY_COLORS[severity])

        # Set column widths
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Assigner
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)

        layout.addWidget(table)

        # Add buttons
        btn_layout = QHBoxLayout()
        view_btn = QPushButton("View Selected Issue")
        style_button(view_btn, "blue")
        close_btn = QPushButton("Close")
        style_button(close_btn, "gray")

        def view_selected():
            selected = table.selectedItems()
            if not selected:
                QMessageBox.warning(dlg, "Warning", "Please select an issue to view.")
                return

            row = selected[0].row()
            issue_id = table.item(row, 0).text()

            # Find the issue file
            for fn in os.listdir(fast_dir):
                if fn.startswith(issue_id) and fn.endswith('.yaml'):
                    path = os.path.join(fast_dir, fn)
                    try:
                        data = yaml.safe_load(open(path))
                        # Show issue details
                        detail_dlg = QDialog(dlg)
                        detail_dlg.setWindowTitle(f"Issue: {data.get('id', '')}")
                        detail_layout = QVBoxLayout(detail_dlg)

                        # Add issue details
                        details = QTextEdit()
                        details.setReadOnly(True)
                        details_text = f"""
ID: {data.get('id', '')}
Title: {data.get('title', '')}
Status: {data.get('status', '')}
Severity: {data.get('severity', '')}
Stage: {data.get('stage', '')}
Assigner: {data.get('assigner', '')}
Assignee: {data.get('assignee', '')}
Created: {data.get('created_at', '')}
Blocks: {', '.join(data.get('modules', []))}
Run Directory: {data.get('run_id', '')}

Description:
{data.get('description', '')}
"""
                        details.setPlainText(details_text)
                        detail_layout.addWidget(details)

                        # Add close button
                        close_btn = QPushButton("Close")
                        style_button(close_btn, "gray")
                        close_btn.clicked.connect(detail_dlg.close)
                        detail_layout.addWidget(close_btn)

                        detail_dlg.resize(700, 500)
                        detail_dlg.exec_()
                        break
                    except Exception as e:
                        QMessageBox.critical(dlg, "Error", f"Failed to load issue: {e}")

        view_btn.clicked.connect(view_selected)
        close_btn.clicked.connect(dlg.close)

        btn_layout.addWidget(view_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        dlg.exec_()

    def _generate_issue_id(self):
        """Generate a unique issue ID in format: 0019_20250419_141729"""
        try:
            # Get all existing issue numbers
            existing_nums = set()  # Using set to avoid duplicates

            # Check active issues in FastTrack directory
            if os.path.exists(self.fast_dir):
                for fn in os.listdir(self.fast_dir):
                    if fn.endswith('.yaml'):
                        try:
                            num_str = fn.split('_')[0]
                            if num_str.isdigit() and len(num_str) == 4:
                                existing_nums.add(int(num_str))
                        except (IndexError, ValueError):
                            continue

            # Check deleted issues
            if os.path.exists(self.deleted_dir):
                for fn in os.listdir(self.deleted_dir):
                    if fn.startswith('deleted_') and fn.endswith('.yaml'):
                        try:
                            parts = fn.split('_')
                            if len(parts) > 1:
                                num_str = parts[1]
                                if num_str.isdigit() and len(num_str) == 4:
                                    existing_nums.add(int(num_str))
                        except (IndexError, ValueError):
                            continue

            # Generate next number
            if existing_nums:
                next_num = max(existing_nums) + 1
            else:
                next_num = 1

            # Ensure the number is within valid range (1-9999)
            if next_num < 1 or next_num > 9999:
                logging.error(f"Issue number {next_num} out of range, resetting to 1")
                next_num = 1

            # Format as 4-digit number
            num_str = f"{next_num:04d}"

            # Add timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Create issue ID
            issue_id = f"{num_str}_{timestamp}"

            # Validate final format
            if not re.match(r'^\d{4}_\d{8}_\d{6}$', issue_id):
                raise ValueError(f"Generated ID has invalid format: {issue_id}")

            # Check for duplicate (shouldn't happen, but just in case)
            if os.path.exists(os.path.join(self.fast_dir, f"{issue_id}.yaml")):
                time.sleep(1)  # Wait a second
                return self._generate_issue_id()  # Try again

            logging.info(f"Generated new issue ID: {issue_id}")
            return issue_id

        except Exception as e:
            logging.error(f"Error in _generate_issue_id: {str(e)}")
            # Emergency fallback - should never happen
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"0001_{timestamp}"

    def _clear_form(self):
        """Clear form with improved handling"""
        try:
            # Check if there's any content in the form before clearing
            has_content = (
                self.title_edit.toPlainText().strip() or
                self.desc_edit.toPlainText().strip() or
                self.runid_edit.toPlainText().strip() or
                self.attach_list.count() > 0
            )

            # If there's content, ask for confirmation
            if has_content:
                reply = QMessageBox.question(
                    self,
                    "Clear Form",
                    "Are you sure you want to clear all fields?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

            self.title_edit.clear()
            self.desc_edit.clear()
            self.severity_combo.setCurrentIndex(0)
            self.stage_combo.setCurrentIndex(0)
            self.module_list.clearSelection()
            self.assignee_combo.setCurrentIndex(0)
            self.due_date_edit.setDate(QDate.currentDate())
            self.due_time_edit.setTime(QTime.currentTime())
            self.runid_edit.clear()
            self.attach_list.clear()
            self.link_check.setChecked(False)

        except Exception as e:
            QMessageBox.warning(self, "Warning",
                f"Some fields could not be cleared properly:\n{str(e)}")
            logging.exception("Error in _clear_form")

def launch_ftrack(prj_base=None):
    # Set up logging
    #logging.basicConfig(
        #level=logging.INFO,
        #format='%(asctime)s - %(levelname)s - %(message)s',
        #handlers=[
            #logging.FileHandler("ftrack_debug.log"),
            #logging.StreamHandler()
        #]
    #)
    #logging.info("Starting FastTrack application")

    app = QApplication(sys.argv)
    window = FastTrackGUI(prj_base)
    window.show()

    # Set up cleanup on application exit
    def cleanup():
        logging.info("Cleaning up FastTrack application")
        # Add any additional cleanup code here if needed

    app.aboutToQuit.connect(cleanup)
    return app.exec_()

if __name__ == "__main__":
    launch_ftrack()

