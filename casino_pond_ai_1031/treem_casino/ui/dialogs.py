"""
CloneDialog that matches the original implementation exactly.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTreeWidget,
    QTreeWidgetItem, QPushButton, QProgressBar, QRadioButton, QWidget, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ..config.settings import AppConfig


class CloneDialog(QDialog):
    """Original CloneDialog implementation matching the attached code."""

    def __init__(self, config: AppConfig, source_path, directory_service=None, parent=None):
        super().__init__(parent)
        self.config = config

        # Convert to string for compatibility with original code
        if hasattr(source_path, '__fspath__') or isinstance(source_path, Path):
            self.dir_path = str(source_path)
        else:
            self.dir_path = source_path

        self.selected_items = {}
        self.updating_check_states = False

        # Original font setup
        font = QFont("Terminus", 10)
        self.setFont(font)
        self.setWindowTitle("Select Items to Clone")
        self.resize(400, 600)

        layout = QVBoxLayout(self)

        # Base directory label
        self.base_dir_label = QLabel("Selected Base Directory to Clone:\n" + self.dir_path)
        self.base_dir_label.setWordWrap(True)
        self.base_dir_label.setFont(font)
        self.base_dir_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.base_dir_label)

        # New directory name input
        label_new_dir_name = QLabel("New Directory Name for Cloned Items:")
        label_new_dir_name.setFont(font)
        layout.addWidget(label_new_dir_name)

        self.new_dir_name_input = QLineEdit()
        self.new_dir_name_input.setFont(font)
        layout.addWidget(self.new_dir_name_input)

        # Select items label
        label_select_items = QLabel("Select items to clone:")
        label_select_items.setFont(font)
        layout.addWidget(label_select_items)

        # Tree widget
        self.tree_widget = QTreeWidget()
        self.tree_widget.setFont(font)
        self.tree_widget.setHeaderLabels(["Name", "Action"])

        # Configure column resizing behavior
        header = self.tree_widget.header()
        header.setStretchLastSection(True)  # Allow last column to stretch

        # Set initial column widths (will be adjusted on first show)
        self.tree_widget.setColumnWidth(0, 240)  # Name column
        # Action column will auto-adjust with stretch

        self.tree_widget.setSelectionMode(QTreeWidget.ExtendedSelection)
        layout.addWidget(self.tree_widget)

        # Selected items label
        self.selected_items_label = QLabel("Selected Items: None")
        self.selected_items_label.setFont(font)
        layout.addWidget(self.selected_items_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFont(font)
        layout.addWidget(self.progress_bar)

        # Populate tree (original logic)
        self.populate_tree_original()

        # Connect signals
        self.tree_widget.itemDoubleClicked.connect(self.handle_item_double_clicked)
        self.tree_widget.itemChanged.connect(self.handle_item_checked)
        self.tree_widget.itemExpanded.connect(self.handle_item_expanded)  # ADD THIS LINE
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.show_context_menu)

        # Control buttons
        button_layout = QHBoxLayout()

        select_all_copy_button = QPushButton("Select All as Copy")
        select_all_copy_button.setFont(font)
        select_all_copy_button.clicked.connect(lambda: self.set_all_items_action("copy"))

        select_all_link_button = QPushButton("Select All as Link")
        select_all_link_button.setFont(font)
        select_all_link_button.clicked.connect(lambda: self.set_all_items_action("link"))

        select_all_button = QPushButton("Select All")
        select_all_button.setFont(font)
        select_all_button.clicked.connect(self.select_all_items)

        deselect_all_button = QPushButton("Deselect All")
        deselect_all_button.setFont(font)
        deselect_all_button.clicked.connect(self.deselect_all_items)

        expand_all_button = QPushButton("Expand All")
        expand_all_button.setFont(font)
        expand_all_button.clicked.connect(self.expand_all_items)

        button_layout.addWidget(select_all_copy_button)
        button_layout.addWidget(select_all_link_button)
        button_layout.addWidget(select_all_button)
        button_layout.addWidget(deselect_all_button)
        button_layout.addWidget(expand_all_button)

        layout.addLayout(button_layout)

        # Dialog buttons
        buttons_layout = QHBoxLayout()

        self.clone_button = QPushButton("Start Clone")
        self.clone_button.setFont(font)
        self.clone_button.setStyleSheet("background-color: #051537; color: white;")
        self.clone_button.clicked.connect(self.start_clone)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFont(font)
        self.cancel_button.clicked.connect(self.reject)

        buttons_layout.addWidget(self.clone_button)
        buttons_layout.addWidget(self.cancel_button)

        layout.addLayout(buttons_layout)

    def showEvent(self, event):
        """Adjust column widths when dialog is shown."""
        super().showEvent(event)
        # Adjust column widths based on actual dialog size
        width = self.tree_widget.viewport().width()
        self.tree_widget.setColumnWidth(0, int(width * 0.65))  # 65% for Name column

    def resizeEvent(self, event):
        """Adjust column widths when dialog is resized."""
        super().resizeEvent(event)
        # Adjust column widths proportionally
        width = self.tree_widget.viewport().width()
        self.tree_widget.setColumnWidth(0, int(width * 0.65))  # 65% for Name column

    def populate_tree_original(self):
        """Original tree population logic from the attached code."""
        def clone_sort_key(x):
            full_path = os.path.join(self.dir_path, x)
            is_works = x.startswith("works_")
            try:
                mtime = os.path.getmtime(full_path)
            except (FileNotFoundError, OSError):
                mtime = 0
            return (1 if is_works else 0, -mtime)

        try:
            items = sorted(os.listdir(self.dir_path), key=clone_sort_key)
        except (OSError, PermissionError):
            QMessageBox.warning(self, "Error", f"Cannot read directory: {self.dir_path}")
            return

        if items:
            for item_name in items:
                item_path = os.path.join(self.dir_path, item_name)
                tree_item = QTreeWidgetItem(self.tree_widget.invisibleRootItem(), [item_name])
                self.selected_items[item_path] = {'selected': False, 'action': 'copy'}
                tree_item.setData(0, Qt.UserRole, item_path)

                if os.path.isdir(item_path):
                    tree_item.setFlags(tree_item.flags() | Qt.ItemIsTristate)
                    tree_item.setCheckState(0, Qt.Unchecked)
                    try:
                        sub_items = os.listdir(item_path)
                        if sub_items:
                            self.add_directory_items(tree_item, item_path)
                        else:
                            tree_item.setText(0, f"{item_name} (Empty)")
                    except (OSError, PermissionError):
                        tree_item.setText(0, f"{item_name} (No Access)")
                else:
                    tree_item.setFlags(tree_item.flags() | Qt.ItemIsUserCheckable)
                    tree_item.setCheckState(0, Qt.Unchecked)
                    self.add_action_widget(tree_item, item_path)
        else:
            root = self.tree_widget.invisibleRootItem()
            root.setText(0, f"{os.path.basename(self.dir_path)} (Empty)")
            root.setFlags(root.flags() | Qt.ItemIsUserCheckable)
            root.setCheckState(0, Qt.Unchecked)
            self.selected_items[self.dir_path] = {'selected': False, 'action': 'create_dir'}

    def add_directory_items(self, parent_item, path):
        """Add directory items with optimized empty checking."""
        parent_item.takeChildren()
        try:
            def clone_sort_key(x):
                full_path = os.path.join(path, x)
                is_works = x.startswith("works_")
                try:
                    mtime = os.path.getmtime(full_path)
                except (FileNotFoundError, OSError):
                    mtime = 0
                return (1 if is_works else 0, -mtime)

            items = sorted(os.listdir(path), key=clone_sort_key)
            if items:
                for item_name in items:
                    item_path = os.path.join(path, item_name)
                    tree_item = QTreeWidgetItem(parent_item, [item_name])
                    self.selected_items[item_path] = {'selected': False, 'action': 'copy'}
                    tree_item.setData(0, Qt.UserRole, item_path)

                    if os.path.isdir(item_path):
                        tree_item.setFlags(tree_item.flags() | Qt.ItemIsTristate)
                        tree_item.setCheckState(0, Qt.Unchecked)

                        try:
                            # OPTIMIZATION: Use scandir with next() - stops after first item found
                            # This is much faster than os.listdir() which reads entire directory
                            with os.scandir(item_path) as entries:
                                first_entry = next(entries, None)

                            if first_entry is not None:
                                # Directory has contents - don't load children yet (lazy loading)
                                # Children will be loaded when user double-clicks or expands
                                # Create checkable dummy child so parent tristate checkbox works
                                dummy_child = QTreeWidgetItem(tree_item, ["Loading..."])
                                dummy_child.setFlags(dummy_child.flags() | Qt.ItemIsUserCheckable)
                                dummy_child.setCheckState(0, Qt.Unchecked)
                                # Store path for later loading
                                dummy_child.setData(0, Qt.UserRole, item_path)
                            else:
                                # Directory is empty
                                tree_item.setText(0, f"{item_name} (Empty)")

                        except (OSError, PermissionError):
                                tree_item.setText(0, f"{item_name} (No Access)")
                    else:
                        # It's a file
                        tree_item.setFlags(tree_item.flags() | Qt.ItemIsUserCheckable)
                        tree_item.setCheckState(0, Qt.Unchecked)
                        self.add_action_widget(tree_item, item_path)
            else:
                # Parent directory is empty
                parent_item.setText(0, f"{os.path.basename(path)} (Empty)")
                parent_item.setFlags(parent_item.flags() | Qt.ItemIsUserCheckable)
                parent_item.setCheckState(0, Qt.Unchecked)
                self.selected_items[path] = {'selected': False, 'action': 'create_dir'}

        except PermissionError:
            pass

    def set_item_action(self, path, action):
        """Original set_item_action method."""
        if path and path in self.selected_items:
            self.selected_items[path]['action'] = action

    def add_action_widget(self, tree_item, item_path):
        """Original add_action_widget method."""
        copy_radio = QRadioButton("Copy")
        link_radio = QRadioButton("Link")
        copy_radio.setChecked(True)
        copy_radio.toggled.connect(lambda checked, p=item_path: self.set_item_action(p, 'copy') if checked else None)
        link_radio.toggled.connect(lambda checked, p=item_path: self.set_item_action(p, 'link') if checked else None)

        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.addWidget(copy_radio)
        action_layout.addWidget(link_radio)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_widget.setLayout(action_layout)

        self.tree_widget.setItemWidget(tree_item, 1, action_widget)

    def handle_item_double_clicked(self, item):
            """Handle double-click with lazy loading support."""
            item_path = item.data(0, Qt.UserRole)

            if os.path.isdir(item_path):
                # Just toggle expansion - loading will be handled by handle_item_expanded
                item.setExpanded(not item.isExpanded())
            else:
                # It's a file - toggle selection
                new_state = Qt.Checked if item.checkState(0) == Qt.Unchecked else Qt.Unchecked
                self.set_subtree_check_state(item, new_state)

    def handle_item_expanded(self, item):
            """Handle item expansion - load children if needed and preserve checkbox state."""
            item_path = item.data(0, Qt.UserRole)

            if not item_path or not os.path.isdir(item_path):
                return

            # Check if this item has the dummy "Loading..." child
            if item.childCount() == 1:
                first_child = item.child(0)
                if first_child.text(0) == "Loading...":
                    # Remember parent's check state
                    parent_check_state = item.checkState(0)

                    # Remove dummy child and load actual children
                    item.removeChild(first_child)
                    self.add_directory_items(item, item_path)

                    # Restore parent's check state and propagate to children if needed
                    if parent_check_state == Qt.Checked:
                        self.set_subtree_check_state(item, Qt.Checked)
                    elif parent_check_state == Qt.PartiallyChecked:
                        # Keep partially checked state
                        item.setCheckState(0, Qt.PartiallyChecked)

    def set_subtree_check_state(self, item, state):
        """Original set_subtree_check_state method."""
        self.tree_widget.blockSignals(True)
        item.setCheckState(0, state)
        self.tree_widget.blockSignals(False)
        item_path = item.data(0, Qt.UserRole)
        if item_path in self.selected_items:
            self.selected_items[item_path]['selected'] = (state == Qt.Checked)
        for i in range(item.childCount()):
            child = item.child(i)
            self.set_subtree_check_state(child, state)
        self.update_selected_items_label()

    def handle_item_checked(self, item, column=0):
        """Original handle_item_checked method."""
        item_path = item.data(0, Qt.UserRole)
        if item_path:
            self.selected_items[item_path]['selected'] = (item.checkState(0) == Qt.Checked)
        self.update_selected_items_label()

    def update_selected_items_label(self):
        """Original update_selected_items_label method."""
        selected_count = sum(1 for info in self.selected_items.values() if info['selected'])
        self.selected_items_label.setText(f"Selected Items: {selected_count}")

    def show_context_menu(self, position):
        """Original show_context_menu method."""
        from PyQt5.QtWidgets import QMenu
        menu = QMenu()
        copy_action = menu.addAction("Set Selected as Copy")
        link_action = menu.addAction("Set Selected as Link")
        copy_action.triggered.connect(lambda: self.set_selected_action("copy"))
        link_action.triggered.connect(lambda: self.set_selected_action("link"))
        menu.exec_(self.tree_widget.viewport().mapToGlobal(position))

    def set_selected_action(self, action):
        """Original set_selected_action method."""
        for item in self.tree_widget.selectedItems():
            item_path = item.data(0, Qt.UserRole)
            if item_path in self.selected_items:
                self.selected_items[item_path]['action'] = action
            action_widget = self.tree_widget.itemWidget(item, 1)
            if action_widget:
                copy_radio, link_radio = action_widget.findChildren(QRadioButton)
                if action == 'copy':
                    copy_radio.setChecked(True)
                else:
                    link_radio.setChecked(True)

    def expand_all_items(self):
        """Original expand_all_items method."""
        root = self.tree_widget.invisibleRootItem()
        self.expand_recursive(root)

    def expand_recursive(self, item):
        """Original expand_recursive method."""
        if item.childCount() == 0 and os.path.isdir(item.data(0, Qt.UserRole)):
            self.add_directory_items(item, item.data(0, Qt.UserRole))
        item.setExpanded(True)
        for i in range(item.childCount()):
            self.expand_recursive(item.child(i))

    def set_all_items_action(self, action):
        """Original set_all_items_action method."""
        root = self.tree_widget.invisibleRootItem()
        self.apply_action_to_all(root, action)

    def apply_action_to_all(self, item, action):
        """Original apply_action_to_all method."""
        for i in range(item.childCount()):
            child = item.child(i)
            child_path = child.data(0, Qt.UserRole)
            if child_path in self.selected_items:
                self.selected_items[child_path]['action'] = action
            action_widget = self.tree_widget.itemWidget(child, 1)
            if action_widget:
                copy_radio, link_radio = action_widget.findChildren(QRadioButton)
                if action == 'copy':
                    copy_radio.setChecked(True)
                else:
                    link_radio.setChecked(True)
            self.apply_action_to_all(child, action)

    def select_all_items(self):
        """Original select_all_items method."""
        root = self.tree_widget.invisibleRootItem()
        self.set_subtree_check_state(root, Qt.Checked)
        self.update_selected_items_label()

    def deselect_all_items(self):
        """Original deselect_all_items method."""
        root = self.tree_widget.invisibleRootItem()
        self.set_subtree_check_state(root, Qt.Unchecked)
        self.update_selected_items_label()

    def start_clone(self):
        """Original start_clone method."""
        dest_dir_name = self.new_dir_name_input.text().strip()
        if not dest_dir_name:
            QMessageBox.warning(self, "Error", "Please enter a name for the cloned directory.")
            return

        parent_dir = os.path.dirname(self.dir_path)
        dest_dir_path = os.path.join(parent_dir, dest_dir_name)

        if os.path.exists(dest_dir_path):
            reply = QMessageBox.question(
                self, "Directory Exists",
                f"The directory '{dest_dir_name}' already exists. Continue and overwrite existing files?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        try:
            os.makedirs(dest_dir_path, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create directory '{dest_dir_path}': {e}")
            return

        selected_items = {path: info for path, info in self.selected_items.items() if info['selected']}
        if not selected_items:
            QMessageBox.warning(self, "Error", "No items selected for cloning.")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(selected_items))
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Cloning %p%")

        errors = []
        processed_count = 0

        for src_path, info in selected_items.items():
            try:
                relative_path = os.path.relpath(src_path, self.dir_path)
                dest_item_path = os.path.join(dest_dir_path, relative_path)

                # Skip if source and destination are the same
                if os.path.realpath(src_path) == os.path.realpath(dest_item_path):
                    print(f"Skipping {src_path} because source and destination are the same file.")
                    continue

                # Handle symlinks
                if os.path.islink(src_path):
                    # Create parent directory if needed
                    os.makedirs(os.path.dirname(dest_item_path), exist_ok=True)
                    link_target = os.readlink(src_path)
                    if not os.path.exists(dest_item_path):
                        os.symlink(link_target, dest_item_path)
                    print(f"Processing symlink: {src_path}")

                # Handle directories
                elif os.path.isdir(src_path):
                    if info['action'] == 'copy':
                        # Copy entire directory tree with all contents
                        if not os.path.exists(dest_item_path):
                            shutil.copytree(src_path, dest_item_path, symlinks=True)
                            print(f"Copied directory tree: {src_path} -> {dest_item_path}")
                        else:
                            # Directory exists, copy contents recursively
                            self._copy_directory_contents(src_path, dest_item_path)
                            print(f"Merged directory contents: {src_path} -> {dest_item_path}")
                    elif info['action'] == 'link':
                        # Create symlink to directory
                        os.makedirs(os.path.dirname(dest_item_path), exist_ok=True)
                        if not os.path.exists(dest_item_path):
                            os.symlink(src_path, dest_item_path)
                            print(f"Created directory symlink: {src_path} -> {dest_item_path}")

                # Handle regular files
                else:
                    # Create parent directory if needed
                    os.makedirs(os.path.dirname(dest_item_path), exist_ok=True)

                    if info['action'] == 'copy':
                        shutil.copy2(src_path, dest_item_path)
                        print(f"Copied file: {src_path} -> {dest_item_path}")
                    elif info['action'] == 'link':
                        if not os.path.exists(dest_item_path):
                            os.symlink(src_path, dest_item_path)
                            print(f"Created file symlink: {src_path} -> {dest_item_path}")

                processed_count += 1
                self.progress_bar.setValue(processed_count)

            except Exception as e:
                errors.append(f"Failed to process {src_path}: {e}")
                print(f"Error processing {src_path}: {e}")

        self.progress_bar.setValue(len(selected_items))

        if errors:
            QMessageBox.warning(self, "Errors Occurred", "\n".join(errors))
        else:
            QMessageBox.information(self, "Clone Completed", f"Cloning completed successfully to '{dest_dir_name}'.")

        self.progress_bar.setVisible(False)

        if not errors:
            self.accept()

    def _copy_directory_contents(self, src_dir, dest_dir):
        """Recursively copy directory contents, merging with existing destination."""
        try:
            for item in os.listdir(src_dir):
                src_item = os.path.join(src_dir, item)
                dest_item = os.path.join(dest_dir, item)

                if os.path.islink(src_item):
                    # Copy symlink
                    if not os.path.exists(dest_item):
                        link_target = os.readlink(src_item)
                        os.symlink(link_target, dest_item)

                elif os.path.isdir(src_item):
                    # Recursively copy subdirectory
                    if not os.path.exists(dest_item):
                        shutil.copytree(src_item, dest_item, symlinks=True)
                    else:
                        self._copy_directory_contents(src_item, dest_item)

                else:
                    # Copy file
                    shutil.copy2(src_item, dest_item)

        except Exception as e:
            print(f"Error copying directory contents from {src_dir} to {dest_dir}: {e}")
            raise

