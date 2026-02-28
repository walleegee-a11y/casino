#!/usr/local/bin/python3.12

import os
import re
import sys
import time
import argparse
import pandas as pd
import csv
from typing import List, Dict, Any, Optional, Tuple
from PyQt5.QtWidgets import (
    QApplication, QFileDialog, QWidget, QVBoxLayout, QPushButton,
    QLabel, QCheckBox, QHBoxLayout, QRadioButton, QButtonGroup,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QLineEdit, QSplitter, QMainWindow, QDockWidget, QDialog, QTextEdit,
    QScrollArea
)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QColor, QClipboard
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from matplotlib.patches import RegularPolygon
from matplotlib.lines import Line2D  # For legend elements


class NumericTableWidgetItem(QTableWidgetItem):
    """Table item that handles numeric sorting properly."""
    def __init__(self, value, is_numeric=False):
        super().__init__(str(value))
        self.is_numeric = is_numeric
        if is_numeric:
            try:
                self.sort_value = float(value)
            except (ValueError, TypeError):
                self.sort_value = float('-inf')
        else:
            self.sort_value = str(value)

    def __lt__(self, other):
        if self.is_numeric:
            try:
                return self.sort_value < other.sort_value
            except (AttributeError, TypeError):
                return True
        return super().__lt__(other)


class DetachableWidget(QMainWindow):
    """A window that can be reattached to the main window."""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.original_parent = parent
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Add a button to reattach the window
        self.attach_button = QPushButton("Reattach Window")
        self.attach_button.clicked.connect(self.reattach_window)
        self.layout.addWidget(self.attach_button)
        
        # Store the original geometry when detached
        self.original_geometry = None
    
    def reattach_window(self):
        if hasattr(self.original_parent, 'reattach_pane'):
            self.original_parent.reattach_pane(self)


class ReverseTextTableItem(QTableWidgetItem):
    """Table item that shows truncated text with ellipsis when it doesn't fit in the column."""
    def __init__(self, text, is_numeric=False):
        super().__init__(text)
        self.full_text = text
        self.is_numeric = is_numeric
        if is_numeric:
            self.setData(Qt.UserRole, float(text) if text else 0.0)
            self.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        else:
            self.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # Store the original text and set tooltip
        self.setToolTip(self.full_text)
    
    def __lt__(self, other):
        if self.is_numeric:
            return self.data(Qt.UserRole) < other.data(Qt.UserRole)
        return super().__lt__(other)
    
    def update_text_display(self, available_width, font_metrics):
        """Update the displayed text based on available width."""
        if self.is_numeric:
            self.setText(self.full_text)
            return

        # elide from the right, keeping the leftmost characters
        elided = font_metrics.elidedText(
            self.full_text,
            Qt.ElideRight,
            available_width
        )
        self.setText(elided)
    
    def __lt__(self, other):
        if self.is_numeric:
            return self.data(Qt.UserRole) < other.data(Qt.UserRole)
        return super().__lt__(other)
    
    def update_text_display(self, available_width, font_metrics):
        """Update the displayed text based on available width."""
        if self.is_numeric:
            self.setText(self.full_text)
            return

        # elide from the right, keeping the leftmost characters
        elided = font_metrics.elidedText(
            self.full_text,
            Qt.ElideRight,
            available_width
        )
        self.setText(elided)


class TimingPathViewer(QWidget):
    def __init__(self, paths=None):
        super().__init__()
        self.paths = paths or []
        self.detached_windows = {}
        self.selected_rows = []  # Initialize selected rows list
        self.highlighted_points = []  # Initialize highlighted points list
        
        # Define colors as class variables
        self.OLIVE = "#778a35"
        self.PEWTER = "#ebebe8"
        self.OLIVE_GREEN = "#31352e"
        self.IVORY = "#EBECE0"
        self.PURPLE_HAZE = "#a98ab0"
        self.TEAL = "#9dced0"
        self.MISTY_BLUE = "#c8d3da"
        self.FOREST_GREEN = "#2B5434"
        self.BLUE_GROTTO = "#045ab7"
        self.CRIMSON = "#90010a"
        self.ROYAL_BLUE = "#0c1446"
        self.SAGE_GREEN = "#D6D3C0"
        self.DARK_BLUE = "#061828"
        self.DEEP_BLUE = "#050A30"
        self.MIDNIGHT = "#050A30"
        self.SCARLET = "#A92420"
        
        # Define common font styles
        self.FONT_STYLE = """
            font-family: "Terminus";
            font-size: 9pt;
        """
        
        # Initialize tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        
        # Define the close tab handler
        def close_tab(index):
            # Remove only the clicked tab
            self.tab_widget.removeTab(index)
        
        # Connect the close handler
        self.tab_widget.tabCloseRequested.connect(close_tab)
        
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Timing Path Viewer")
        
        # Create main layout
        main_layout = QVBoxLayout()
        
        # Create splitter for left and right panes
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Create left pane (Timing Path Data)
        self.left_pane = QWidget()
        left_layout = QVBoxLayout(self.left_pane)
        
        # Add detach button for left pane
        left_header = QHBoxLayout()
        left_detach_btn = QPushButton("Detach Timing Data")
        left_detach_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.FOREST_GREEN};
                color: {self.IVORY};
                border: 2px solid black;
                padding: 5px 15px;
                border-radius: 4px;
                {self.FONT_STYLE}
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.OLIVE_GREEN};
            }}
            QPushButton:pressed {{
                background-color: {self.DARK_BLUE};
            }}
        """)
        left_detach_btn.clicked.connect(lambda: self.detach_pane('left'))
        
        # Style the label
        timing_label = QLabel("Timing Path Data")
        timing_label.setStyleSheet(f"""
            QLabel {{
                {self.FONT_STYLE}
                font-weight: bold;
            }}
        """)
        left_header.addWidget(timing_label)
        left_header.addWidget(left_detach_btn)
        left_layout.addLayout(left_header)
        
        # Create button row layout
        button_row = QHBoxLayout()
        
        # Add load button
        self.loadFileBtn = QPushButton("Load Timing File")
        self.loadFileBtn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.BLUE_GROTTO};
                color: {self.IVORY};
                border: 2px solid black;
                padding: 8px 20px;
                border-radius: 4px;
                {self.FONT_STYLE}
                font-weight: bold;
                min-height: 15px;
            }}
            QPushButton:hover {{
                background-color: {self.ROYAL_BLUE};
            }}
            QPushButton:pressed {{
                background-color: {self.DEEP_BLUE};
            }}
        """)
        self.loadFileBtn.clicked.connect(self.load_timing_file)
        button_row.addWidget(self.loadFileBtn)

        # Add direct input for file path below the Load Timing File button
        file_input_row = QHBoxLayout()
        self.filePathInput = QLineEdit()
        self.filePathInput.setPlaceholderText("Enter timing file path...")
        self.filePathInput.setStyleSheet(f"""
            QLineEdit {{
                {self.FONT_STYLE}
                padding: 4px;
                border: 1px solid {self.DARK_BLUE};
                border-radius: 2px;
                min-width: 250px;
            }}
        """)
        file_input_row.addWidget(self.filePathInput)

        self.filePathEnterBtn = QPushButton("Load")
        self.filePathEnterBtn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.OLIVE};
                color: {self.IVORY};
                border: 2px solid black;
                padding: 6px 16px;
                border-radius: 4px;
                {self.FONT_STYLE}
                font-weight: bold;
                min-height: 15px;
            }}
            QPushButton:hover {{
                background-color: {self.OLIVE_GREEN};
            }}
            QPushButton:pressed {{
                background-color: {self.DARK_BLUE};
            }}
        """)
        self.filePathEnterBtn.clicked.connect(self.load_timing_file_from_input)
        file_input_row.addWidget(self.filePathEnterBtn)

        left_layout.addLayout(file_input_row)
        
        # Add cell filter controls
        cell_filter_layout = QHBoxLayout()
        
        # Cell filter label
        cell_filter_label = QLabel("Cell Filter:")
        cell_filter_label.setStyleSheet(f"""
            QLabel {{
                {self.FONT_STYLE}
                font-weight: bold;
            }}
        """)
        cell_filter_layout.addWidget(cell_filter_label)
        
        # Cell filter input field
        self.cellFilterInput = QLineEdit()
        self.cellFilterInput.setPlaceholderText("e.g., CKINV*|INV*|BUF*")
        self.cellFilterInput.setStyleSheet(f"""
            QLineEdit {{
                {self.FONT_STYLE}
                padding: 4px;
                border: 1px solid {self.DARK_BLUE};
                border-radius: 2px;
                min-width: 150px;
            }}
        """)
        cell_filter_layout.addWidget(self.cellFilterInput)
        
        # Reload button to apply filter
        self.reloadFilterBtn = QPushButton("Reload with Filter")
        self.reloadFilterBtn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.PURPLE_HAZE};
                color: {self.IVORY};
                border: 2px solid black;
                padding: 8px 15px;
                border-radius: 4px;
                {self.FONT_STYLE}
                font-weight: bold;
                min-height: 15px;
            }}
            QPushButton:hover {{
                background-color: {self.ROYAL_BLUE};
            }}
            QPushButton:pressed {{
                background-color: {self.DEEP_BLUE};
            }}
        """)
        self.reloadFilterBtn.clicked.connect(self.reload_with_filter)
        cell_filter_layout.addWidget(self.reloadFilterBtn)
        
        button_row.addLayout(cell_filter_layout)
        
        # Add adjust width button
        self.adjustWidthBtn = QPushButton("Adjust Column Widths")
        self.adjustWidthBtn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.TEAL};
                color: {self.DARK_BLUE};
                border: 2px solid black;
                padding: 8px 20px;
                border-radius: 4px;
                {self.FONT_STYLE}
                font-weight: bold;
                min-height: 15px;
            }}
            QPushButton:hover {{
                background-color: {self.MISTY_BLUE};
            }}
            QPushButton:pressed {{
                background-color: {self.BLUE_GROTTO};
            }}
        """)
        self.adjustWidthBtn.clicked.connect(self.adjust_column_widths)
        button_row.addWidget(self.adjustWidthBtn)
        
        # Add Put Path button
        self.putPathBtn = QPushButton("Put a Path")
        self.putPathBtn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.OLIVE};
                color: {self.IVORY};
                border: 2px solid black;
                padding: 8px 20px;
                border-radius: 4px;
                {self.FONT_STYLE}
                font-weight: bold;
                min-height: 15px;
            }}
            QPushButton:hover {{
                background-color: {self.OLIVE_GREEN};
            }}
            QPushButton:pressed {{
                background-color: {self.DARK_BLUE};
            }}
        """)
        self.putPathBtn.clicked.connect(self.put_individual_path)
        button_row.addWidget(self.putPathBtn)
        
        # Add '?' button for PrimeTime report_timing options
        self.ptGuideBtn = QPushButton("?")
        self.ptGuideBtn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.BLUE_GROTTO};
                color: {self.IVORY};
                border: 2px solid black;
                padding: 8px 16px;
                border-radius: 4px;
                {self.FONT_STYLE}
                font-weight: bold;
                min-height: 15px;
            }}
            QPushButton:hover {{
                background-color: {self.ROYAL_BLUE};
            }}
            QPushButton:pressed {{
                background-color: {self.DEEP_BLUE};
            }}
        """)
        self.ptGuideBtn.setToolTip("PrimeTime report_timing options")
        self.ptGuideBtn.clicked.connect(self.show_primetime_guide)
        button_row.addWidget(self.ptGuideBtn)
        
        # Add Clear Selection button for Timing Path Data
        self.clearSelectionBtn = QPushButton("Clear Selection")
        self.clearSelectionBtn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.SCARLET};
                color: {self.IVORY};
                border: 2px solid black;
                padding: 8px 20px;
                border-radius: 4px;
                {self.FONT_STYLE}
                font-weight: bold;
                min-height: 15px;
            }}
            QPushButton:hover {{
                background-color: {self.CRIMSON};
            }}
            QPushButton:pressed {{
                background-color: {self.DARK_BLUE};
            }}
        """)
        self.clearSelectionBtn.clicked.connect(self.clear_path_selection)
        button_row.addWidget(self.clearSelectionBtn)
        
        # Add button row to main layout
        left_layout.addLayout(button_row)
        
        # Add table widget for timing paths to left pane
        self.table = QTableWidget()
        self.table.setColumnCount(9)  # Number of columns for timing path data
        self.table.setHorizontalHeaderLabels([
            "Path #", "Startpoint", "Endpoint", "Launch Clock", "Capture Clock", 
            "Path Group", "Slack", "Period", "Skew"
        ])
        
        # Style the table
        self.table.setStyleSheet(f"""
            QTableWidget {{
                {self.FONT_STYLE}
                gridline-color: {self.DARK_BLUE};
            }}
            QHeaderView::section {{
                {self.FONT_STYLE}
                background-color: {self.MISTY_BLUE};
                padding: 4px;
                border: 1px solid {self.DARK_BLUE};
            }}
        """)
        
        # Set up the horizontal header properties
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)  # Prevent last section from stretching
        
        # Make columns interactively resizable
        for i in range(self.table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Interactive)
        
        # Set table properties
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.MultiSelection)
        self.table.itemSelectionChanged.connect(self.on_table_selection_changed)
        
        left_layout.addWidget(self.table)
        
        # Create right pane (Visualization Controls)
        self.right_pane = QWidget()
        right_layout = QVBoxLayout(self.right_pane)
        
        # Add detach button for right pane
        right_header = QHBoxLayout()
        right_detach_btn = QPushButton("Detach Visualization Controls")
        right_detach_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.FOREST_GREEN};
                color: {self.IVORY};
                border: 2px solid black;
                padding: 5px 15px;
                border-radius: 4px;
                {self.FONT_STYLE}
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.OLIVE_GREEN};
            }}
            QPushButton:pressed {{
                background-color: {self.DARK_BLUE};
            }}
        """)
        right_detach_btn.clicked.connect(lambda: self.detach_pane('right'))
        
        # Style the visualization label
        viz_label = QLabel("Visualization Controls")
        viz_label.setStyleSheet(f"""
            QLabel {{
                {self.FONT_STYLE}
                font-weight: bold;
            }}
        """)
        right_header.addWidget(viz_label)
        right_header.addWidget(right_detach_btn)
        right_layout.addLayout(right_header)
        
        # Add visualization options
        options_layout = QHBoxLayout()
        
        # Style for checkboxes
        checkbox_style = f"""
            QCheckBox {{
                {self.FONT_STYLE}
            }}
            QCheckBox::indicator {{
                width: 12px;
                height: 12px;
            }}
        """
        
        # Option to show/hide pin names on the plot
        self.showPinNamesCheck = QCheckBox("Show pin names")
        self.showPinNamesCheck.setStyleSheet(checkbox_style)
        options_layout.addWidget(self.showPinNamesCheck)
        
        # Option to show/hide legend on the plot
        self.showLegendCheck = QCheckBox("Show legend")
        self.showLegendCheck.setStyleSheet(checkbox_style)
        self.showLegendCheck.setChecked(True)  # Default to showing legend
        options_layout.addWidget(self.showLegendCheck)
        
        # Option to enable/disable pin highlighting
        self.enableHighlightCheck = QCheckBox("Enable pin highlighting")
        self.enableHighlightCheck.setStyleSheet(checkbox_style)
        self.enableHighlightCheck.setChecked(True)  # Default to enabling highlighting
        options_layout.addWidget(self.enableHighlightCheck)
        
        # Option to use shortened pin names in highlights
        self.useShortenedNamesCheck = QCheckBox("Use shortened pin names")
        self.useShortenedNamesCheck.setStyleSheet(checkbox_style)
        self.useShortenedNamesCheck.setChecked(True)  # Default to using shortened names
        options_layout.addWidget(self.useShortenedNamesCheck)
        
        # Connect the checkboxes
        self.enableHighlightCheck.toggled.connect(self.on_highlight_toggled)
        self.useShortenedNamesCheck.toggled.connect(self.on_shortened_names_toggled)
        
        # Add Clear Highlights button for Visualization Controls
        self.clearHighlightsBtn = QPushButton("Clear Highlights")
        self.clearHighlightsBtn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.SCARLET};
                color: {self.IVORY};
                border: 2px solid black;
                padding: 4px 10px;
                border-radius: 4px;
                {self.FONT_STYLE}
                font-weight: bold;
                min-height: 15px;
            }}
            QPushButton:hover {{
                background-color: {self.CRIMSON};
            }}
            QPushButton:pressed {{
                background-color: {self.DARK_BLUE};
            }}
        """)
        self.clearHighlightsBtn.clicked.connect(self.clear_all_highlighted_points)
        options_layout.addWidget(self.clearHighlightsBtn)
        
        right_layout.addLayout(options_layout)

        # Style for radio buttons
        radio_style = f"""
            QRadioButton {{
                {self.FONT_STYLE}
            }}
            QRadioButton::indicator {{
                width: 12px;
                height: 12px;
            }}
        """

        # Radio buttons for ranking metric selection
        rank_group = QWidget()
        rank_layout = QHBoxLayout(rank_group)
        self.rankIncrRadio = QRadioButton("Rank by Incr Delay")
        self.rankTransRadio = QRadioButton("Rank by Tran Time")
        self.rankDeltaRadio = QRadioButton("Rank by Delta")
        self.rankIncrRadio.setStyleSheet(radio_style)
        self.rankTransRadio.setStyleSheet(radio_style)
        self.rankDeltaRadio.setStyleSheet(radio_style)
        self.rankIncrRadio.setChecked(True)  # Default selection
        rank_layout.addWidget(self.rankIncrRadio)
        rank_layout.addWidget(self.rankTransRadio)
        rank_layout.addWidget(self.rankDeltaRadio)
        right_layout.addWidget(rank_group)
        
        # Path type filter options
        path_filter_label = QLabel("Filter path types:")
        path_filter_label.setStyleSheet(f"""
            QLabel {{
                {self.FONT_STYLE}
                font-weight: bold;
            }}
        """)
        right_layout.addWidget(path_filter_label)
        
        path_filter_layout = QHBoxLayout()
        
        # Checkboxes for path types
        self.showDataPathCheck = QCheckBox("Data Path")
        self.showDataPathCheck.setStyleSheet(checkbox_style)
        self.showDataPathCheck.setChecked(True)  # Default to showing data path
        path_filter_layout.addWidget(self.showDataPathCheck)
        
        self.showLaunchClockCheck = QCheckBox("Launch Clock Path")
        self.showLaunchClockCheck.setStyleSheet(checkbox_style)
        self.showLaunchClockCheck.setChecked(True)  # Default to showing launch clock path
        path_filter_layout.addWidget(self.showLaunchClockCheck)
        
        self.showCaptureClockCheck = QCheckBox("Capture Clock Path")
        self.showCaptureClockCheck.setStyleSheet(checkbox_style)
        self.showCaptureClockCheck.setChecked(True)  # Default to showing capture clock path
        path_filter_layout.addWidget(self.showCaptureClockCheck)
        
        right_layout.addLayout(path_filter_layout)
        
        # Cell filter for visualization
        cell_filter_viz_label = QLabel("Cell filter for visualization:")
        cell_filter_viz_label.setStyleSheet(f"""
            QLabel {{
                {self.FONT_STYLE}
                font-weight: bold;
            }}
        """)
        right_layout.addWidget(cell_filter_viz_label)
        
        # Cell filter input field for visualization
        cell_filter_viz_layout = QHBoxLayout()
        self.cellFilterVizInput = QLineEdit()
        self.cellFilterVizInput.setPlaceholderText("e.g., ^INV|^BUF")
        self.cellFilterVizInput.setStyleSheet(f"""
            QLineEdit {{
                {self.FONT_STYLE}
                padding: 4px;
                border: 1px solid {self.DARK_BLUE};
                border-radius: 2px;
                min-width: 150px;
            }}
        """)
        cell_filter_viz_layout.addWidget(self.cellFilterVizInput)
        
        # Apply filter button for visualization
        self.applyVizFilterBtn = QPushButton("Apply Filter")
        self.applyVizFilterBtn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.PURPLE_HAZE};
                color: {self.IVORY};
                border: 2px solid black;
                padding: 4px 10px;
                border-radius: 4px;
                {self.FONT_STYLE}
                font-weight: bold;
                min-height: 15px;
            }}
            QPushButton:hover {{
                background-color: {self.ROYAL_BLUE};
            }}
            QPushButton:pressed {{
                background-color: {self.DEEP_BLUE};
            }}
        """)
        self.applyVizFilterBtn.clicked.connect(self.apply_visualization_filter)
        cell_filter_viz_layout.addWidget(self.applyVizFilterBtn)
        
        # Clear filter button for visualization
        self.clearVizFilterBtn = QPushButton("Clear Filter")
        self.clearVizFilterBtn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.SCARLET};
                color: {self.IVORY};
                border: 2px solid black;
                padding: 4px 10px;
                border-radius: 4px;
                {self.FONT_STYLE}
                font-weight: bold;
                min-height: 15px;
            }}
            QPushButton:hover {{
                background-color: {self.CRIMSON};
            }}
            QPushButton:pressed {{
                background-color: {self.DARK_BLUE};
            }}
        """)
        self.clearVizFilterBtn.clicked.connect(self.clear_visualization_filter)
        cell_filter_viz_layout.addWidget(self.clearVizFilterBtn)
        
        right_layout.addLayout(cell_filter_viz_layout)
        
        # Top ranked points percentage control
        top_ranked_layout = QHBoxLayout()
        
        # Option to show only top ranked points
        self.showTopRankedOnlyCheck = QCheckBox("Show only top ranked points")
        self.showTopRankedOnlyCheck.setStyleSheet(checkbox_style)
        self.showTopRankedOnlyCheck.setChecked(False)  # Default to showing all points
        top_ranked_layout.addWidget(self.showTopRankedOnlyCheck)
        
        # Percentage input field
        percentage_label = QLabel("Top %:")
        percentage_label.setStyleSheet(f"""
            QLabel {{
                {self.FONT_STYLE}
                font-weight: bold;
            }}
        """)
        top_ranked_layout.addWidget(percentage_label)
        
        self.topRankedPercentageInput = QLineEdit()
        self.topRankedPercentageInput.setText("20")  # Default to 20%
        self.topRankedPercentageInput.setPlaceholderText("20")
        self.topRankedPercentageInput.setStyleSheet(f"""
            QLineEdit {{
                {self.FONT_STYLE}
                padding: 4px;
                border: 1px solid {self.DARK_BLUE};
                border-radius: 2px;
                min-width: 50px;
                max-width: 60px;
            }}
        """)
        top_ranked_layout.addWidget(self.topRankedPercentageInput)
        
        right_layout.addLayout(top_ranked_layout)

        # Add tab widget for visualization
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {self.DARK_BLUE};
            }}
            QTabBar::tab {{
                {self.FONT_STYLE}
                background-color: {self.MISTY_BLUE};
                padding: 4px 8px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {self.BLUE_GROTTO};
                color: {self.IVORY};
            }}
        """)
        right_layout.addWidget(self.tab_widget)

        # Button layout for plot and export
        button_layout = QHBoxLayout()
        
        self.plotBtn = QPushButton("Draw Plot (Selected Paths)")
        self.plotBtn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.PURPLE_HAZE};
                color: {self.IVORY};
                border: 2px solid black;
                padding: 8px 20px;
                border-radius: 4px;
                {self.FONT_STYLE}
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.ROYAL_BLUE};
            }}
            QPushButton:pressed {{
                background-color: {self.DEEP_BLUE};
            }}
        """)
        self.plotBtn.clicked.connect(self.plot_selected_path)
        button_layout.addWidget(self.plotBtn)
        
        self.tableBtn = QPushButton("Show Table (Selected Paths)")
        self.tableBtn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.SCARLET};
                color: {self.IVORY};
                border: 2px solid black;
                padding: 8px 20px;
                border-radius: 4px;
                {self.FONT_STYLE}
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.CRIMSON};
            }}
            QPushButton:pressed {{
                background-color: {self.DARK_BLUE};
            }}
        """)
        self.tableBtn.clicked.connect(self.show_table)
        button_layout.addWidget(self.tableBtn)
        
        self.reportCmdBtn = QPushButton("Generate Timing Commands")
        self.reportCmdBtn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.OLIVE};
                color: {self.IVORY};
                border: 2px solid black;
                padding: 8px 20px;
                border-radius: 4px;
                {self.FONT_STYLE}
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.OLIVE_GREEN};
            }}
            QPushButton:pressed {{
                background-color: {self.DARK_BLUE};
            }}
        """)
        self.reportCmdBtn.clicked.connect(self.generate_timing_command)
        button_layout.addWidget(self.reportCmdBtn)
        
        self.exportCsvBtn = QPushButton("Export to CSV")
        self.exportCsvBtn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.SAGE_GREEN};
                color: {self.DARK_BLUE};
                border: 2px solid black;
                padding: 8px 20px;
                border-radius: 4px;
                {self.FONT_STYLE}
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.PEWTER};
            }}
            QPushButton:pressed {{
                background-color: {self.MISTY_BLUE};
            }}
        """)
        self.exportCsvBtn.clicked.connect(self.export_to_csv)
        button_layout.addWidget(self.exportCsvBtn)
        
        right_layout.addLayout(button_layout)
        
        # Add panes to splitter
        self.splitter.addWidget(self.left_pane)
        self.splitter.addWidget(self.right_pane)
        
        # Set initial splitter sizes (40% left, 60% right)
        self.splitter.setStretchFactor(0, 4)
        self.splitter.setStretchFactor(1, 6)
        self.splitter.setSizes([400, 600])
        
        # Add splitter to main layout
        main_layout.addWidget(self.splitter)
        
        # Set the main layout
        self.setLayout(main_layout)
        
        # Store original panes for reattachment
        self.original_panes = {
            'left': self.left_pane,
            'right': self.right_pane
        }
        
        # If paths were provided during initialization, update the path list
        self.update_path_list()

    def detach_pane(self, pane_type):
        """Detach a pane into its own window."""
        if pane_type not in self.detached_windows:
            pane = self.left_pane if pane_type == 'left' else self.right_pane
            title = "Timing Path Data" if pane_type == 'left' else "Visualization Controls"
            
            # Create new window
            detached = DetachableWidget(title, self)
            
            # Move the pane to the new window
            pane.setParent(detached.central_widget)
            detached.layout.addWidget(pane)
            
            # Position the detached window
            if self.window().isVisible():
                main_pos = self.window().pos()
                offset = QPoint(50, 50) if pane_type == 'left' else QPoint(100, 100)
                detached.move(main_pos + offset)
            
            # Show the detached window
            detached.show()
            
            # Store reference to detached window
            self.detached_windows[pane_type] = detached
            
            # Create placeholder in splitter
            placeholder = QWidget()
            placeholder_layout = QVBoxLayout(placeholder)
            reattach_btn = QPushButton(f"Reattach {title}")
            reattach_btn.clicked.connect(lambda: self.reattach_pane(detached))
            placeholder_layout.addWidget(reattach_btn)
            
            # Add placeholder to splitter
            if pane_type == 'left':
                self.splitter.insertWidget(0, placeholder)
            else:
                self.splitter.insertWidget(1, placeholder)

    def reattach_pane(self, window):
        """Reattach a detached window back to the main window."""
        for pane_type, detached in self.detached_windows.items():
            if detached == window:
                # Get the pane widget
                pane = self.original_panes[pane_type]
                
                # Remove the placeholder from the splitter
                placeholder = self.splitter.widget(0 if pane_type == 'left' else 1)
                placeholder.setParent(None)
                
                # Move the pane back to the splitter
                pane.setParent(None)
                if pane_type == 'left':
                    self.splitter.insertWidget(0, pane)
                else:
                    self.splitter.insertWidget(1, pane)
                
                # Close and remove the detached window
                window.close()
                del self.detached_windows[pane_type]
                
                # Restore splitter sizes
                self.splitter.setStretchFactor(0, 4)
                self.splitter.setStretchFactor(1, 6)
                self.splitter.setSizes([400, 600])
                break

    def closeEvent(self, event):
        """Handle application closing."""
        # Close any detached windows
        for window in self.detached_windows.values():
            window.close()
        super().closeEvent(event)

    def table_resize_event(self, event):
        """Handle table resize events to maintain proper column widths."""
        super(QTableWidget, self.table).resizeEvent(event)
        
        # Update text display for all items
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if isinstance(item, ReverseTextTableItem):
                    # Get the available width
                    available_width = self.table.columnWidth(col) - 10  # Subtract padding
                    
                    # Update the text display
                    item.update_text_display(available_width, self.table.fontMetrics())
    
    def update_column_widths(self):
        """Set initial column widths while preserving user adjustments."""
        # Only set initial widths if they haven't been manually adjusted
        if not hasattr(self, '_columns_initialized'):
            total_width = self.table.viewport().width()
            
            # Set column widths based on content type
            pin_columns = [0, 1]  # Startpoint and Endpoint columns
            clock_columns = [2, 3]  # Launch Clock and Capture Clock columns
            metric_columns = [5, 6, 7]  # Slack, Period, Skew columns (numeric values)
            
            # Calculate widths
            pin_width = int(total_width * 0.25)  # 25% for pin columns
            clock_width = int(total_width * 0.12)  # 12% for clock columns
            group_width = int(total_width * 0.14)  # 14% for Path Group
            metric_width = int(total_width * 0.04)  # 4% for metric columns
            
            # Set the widths
            for col in range(self.table.columnCount()):
                if col in pin_columns:
                    self.table.setColumnWidth(col, pin_width)
                elif col in clock_columns:
                    self.table.setColumnWidth(col, clock_width)
                elif col == 4:  # Path Group
                    self.table.setColumnWidth(col, group_width)
                elif col in metric_columns:
                    self.table.setColumnWidth(col, metric_width)
            
            self._columns_initialized = True
    
    def update_path_list(self):
        """Update the table with timing paths."""
        if not self.paths:
            self.table.setRowCount(0)
            return
            
        # Clear existing items
        self.table.setRowCount(0)
        
        # Track maximum lengths for each column
        max_lengths = {i: 0 for i in range(self.table.columnCount())}
        
        # Add paths to table
        for i, path in enumerate(self.paths):
            self.table.insertRow(i)
            
            # Extract pin names from startpoint and endpoint
            startpoint = path['startpoint'].split(' (')[0]  # Get base path without pin
            endpoint = path['endpoint'].split(' (')[0]  # Get base path without pin
            
            # Get actual start and end pins
            actual_start = path.get('actual_start', {}).get('pin', startpoint)
            actual_end = path.get('actual_end', {}).get('pin', endpoint)
            
            # Clean up clock names by removing parentheses
            launch_clock = path.get('launch_clock', 'N/A').rstrip(')').lstrip('(')
            capture_clock = path.get('capture_clock', 'N/A').rstrip(')').lstrip('(')
            
            def format_path_with_pin(base_path, pin_path):
                # If pin_path is already a complete path (contains the base_path)
                if base_path in pin_path:
                    return pin_path
                
                # If pin_path is just a pin name or different path
                if base_path != pin_path:
                    return f"{base_path} ({pin_path})"
                return base_path
            
            startpoint_full = format_path_with_pin(startpoint, actual_start)
            endpoint_full = format_path_with_pin(endpoint, actual_end)
            
            # Prepare data for each column
            path_num = i + 1
            row_data = {
                0: path_num,  # Store as integer for proper sorting
                1: startpoint_full,
                2: endpoint_full,
                3: launch_clock,
                4: capture_clock,
                5: path['path_group'],
                6: round(path['slack'], 4),  # Round to 4 decimal places
                7: round(path['period'], 4),  # Round to 4 decimal places
                8: round(path['skew'], 4)     # Round to 4 decimal places
            }
            
            # Update maximum lengths (using string representation for length calculation)
            for col, value in row_data.items():
                if isinstance(value, (int, float)):
                    max_lengths[col] = max(max_lengths[col], len(f"{value:.4f}" if isinstance(value, float) else str(value)))
                else:
                    max_lengths[col] = max(max_lengths[col], len(str(value)))
            
            # Add items to table
            for col, value in row_data.items():
                is_numeric = isinstance(value, (int, float))
                if is_numeric and isinstance(value, float):
                    item = ReverseTextTableItem(f"{value:.4f}", is_numeric)
                else:
                    item = ReverseTextTableItem(str(value), is_numeric)
                self.table.setItem(i, col, item)
        
        # Calculate total content width
        total_width = self.table.viewport().width()
        padding = 20  # Padding for each column
        min_width = 50  # Minimum column width
        
        total_content_width = sum(max_lengths.values()) * 8 + (len(max_lengths) * padding)
        
        # If content is narrower than viewport, distribute extra space proportionally
        if total_content_width < total_width:
            extra_space = total_width - total_content_width
            for col in max_lengths:
                content_width = max_lengths[col] * 8 + padding
                ratio = content_width / total_content_width if total_content_width > 0 else 1.0
                width = int(content_width + (extra_space * ratio))
                self.table.setColumnWidth(col, max(width, min_width))
        else:
            # If content is wider than viewport, scale down proportionally
            scale_factor = total_width / total_content_width
            for col in max_lengths:
                width = int(max_lengths[col] * 8 * scale_factor + padding)
                self.table.setColumnWidth(col, max(width, min_width))
        
        # Enable sorting after populating data
        self.table.setSortingEnabled(True)
        
        # Select the first row if available
        if self.table.rowCount() > 0:
            self.table.selectRow(0)
    
    def apply_regex_filter(self, column, pattern):
        """Apply regex filter to the specified column."""
        try:
            regex = re.compile(pattern, re.IGNORECASE) if pattern else None
            
            for row in range(self.table.rowCount()):
                item = self.table.item(row, column)
                if item:
                    text = item.text()
                    match = regex.search(text) if regex else True
                    self.table.setRowHidden(row, not match)
        except re.error:
            # Invalid regex pattern - show all rows
            for row in range(self.table.rowCount()):
                self.table.setRowHidden(row, False)
    
    def on_table_selection_changed(self):
        """Handle table selection changes."""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        
        # Store selected rows for use in other functions
        self.selected_rows = list(selected_rows)
        
        # The visualization will be updated when the respective buttons are clicked
    
    def load_timing_file(self):
        """Load a timing file and parse it."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Timing Report", "", "Timing Reports (*.rpt *.txt);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            # Create a simple progress label
            progress_label = QLabel("0")
            progress_label.setStyleSheet("""
                QLabel {
                    font-family: "Terminus";
                    font-size: 30pt;
                    color: #045ab7;
                    font-weight: bold;
                }
            """)
            progress_label.setAlignment(Qt.AlignCenter)
            progress_label.setWindowTitle("Loading Timing Paths")
            progress_label.setWindowModality(Qt.WindowModal)
            progress_label.setFixedSize(200, 100)
            progress_label.move(self.mapToGlobal(self.rect().center()) - progress_label.rect().center())
            progress_label.show()
            
            # Read the file
            with open(file_path, "r") as f:
                print(f"Reading timing report from: {file_path}")
                rpt_text = f.read()
                file_size_mb = len(rpt_text) / (1024 * 1024)
                print(f"File size: {file_size_mb:.2f} MB")
            
            # Store the file content for potential reloading with filters
            self.current_file_content = rpt_text
            self.current_file_path = file_path
            
            # Parse the timing paths
            print("Starting to parse timing paths...")
            self.paths = []
            
            # Get cell filter regex from input field
            cell_filter_regex = self.cellFilterInput.text().strip()
            if not cell_filter_regex:
                cell_filter_regex = None
            
            # Parse paths with progress updates
            for i, path in enumerate(parse_timing_paths(rpt_text, cell_filter_regex)):
                self.paths.append(path)
                progress_label.setText(str(i + 1))
                QApplication.processEvents()
            
            progress_label.close()
            
            if not self.paths:
                QMessageBox.warning(self, "No Paths Found", "No timing paths found in the selected file.")
                return
                
            print(f"Found {len(self.paths)} timing paths.")
            
            # Update the list widget
            self.update_path_list()
            
            QMessageBox.information(self, "Success", f"Successfully loaded {len(self.paths)} timing paths.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading timing file: {str(e)}")
            import traceback
            traceback.print_exc()

    def reload_with_filter(self):
        """Reload the current file with the cell filter applied."""
        if not hasattr(self, 'current_file_content'):
            QMessageBox.warning(self, "No File Loaded", "Please load a timing file first.")
            return
            
        try:
            # Create a simple progress label
            progress_label = QLabel("0")
            progress_label.setStyleSheet("""
                QLabel {
                    font-family: "Terminus";
                    font-size: 30pt;
                    color: #045ab7;
                    font-weight: bold;
                }
            """)
            progress_label.setAlignment(Qt.AlignCenter)
            progress_label.setWindowTitle("Reloading with Filter")
            progress_label.setWindowModality(Qt.WindowModal)
            progress_label.setFixedSize(200, 100)
            progress_label.move(self.mapToGlobal(self.rect().center()) - progress_label.rect().center())
            progress_label.show()
            
            # Get cell filter regex from input field
            cell_filter_regex = self.cellFilterInput.text().strip()
            if not cell_filter_regex:
                cell_filter_regex = None
            
            # Parse the timing paths with filter
            print("Reloading timing paths with cell filter...")
            self.paths = []
            
            # Parse paths with progress updates
            for i, path in enumerate(parse_timing_paths(self.current_file_content, cell_filter_regex)):
                self.paths.append(path)
                progress_label.setText(str(i + 1))
                QApplication.processEvents()
            
            progress_label.close()
            
            if not self.paths:
                QMessageBox.warning(self, "No Paths Found", 
                                  f"No timing paths found after applying cell filter: {cell_filter_regex}")
                return
                
            print(f"Found {len(self.paths)} timing paths after filtering.")
            
            # Update the list widget
            self.update_path_list()
            
            filter_info = f" with filter: {cell_filter_regex}" if cell_filter_regex else ""
            QMessageBox.information(self, "Success", 
                                  f"Successfully reloaded {len(self.paths)} timing paths{filter_info}.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error reloading with filter: {str(e)}")
            import traceback
            traceback.print_exc()

    def apply_visualization_filter(self):
        """Apply cell filter to visualization without reloading the file."""
        if not self.paths:
            QMessageBox.warning(self, "No Paths Loaded", "Please load timing paths first.")
            return
            
        # Get cell filter regex from visualization input field
        cell_filter_regex = self.cellFilterVizInput.text().strip()
        if not cell_filter_regex:
            QMessageBox.information(self, "No Filter", "Please enter a cell filter pattern.")
            return
            
        try:
            # Compile the regex to validate it
            re.compile(cell_filter_regex, re.IGNORECASE)
        except re.error as e:
            QMessageBox.critical(self, "Invalid Regex", f"Invalid regex pattern: {str(e)}")
            return
            
        # Store the filter for use in plotting and table display
        self.visualization_cell_filter = cell_filter_regex
        
        QMessageBox.information(self, "Filter Applied", 
                              f"Cell filter '{cell_filter_regex}' applied to visualization.\n"
                              "Use 'Draw Plot' or 'Show Table' to see the filtered results.")

    def clear_visualization_filter(self):
        """Clear the visualization cell filter."""
        if hasattr(self, 'visualization_cell_filter'):
            delattr(self, 'visualization_cell_filter')
            self.cellFilterVizInput.clear()
            QMessageBox.information(self, "Filter Cleared", 
                                  "Cell filter has been cleared.\n"
                                  "Use 'Draw Plot' or 'Show Table' to see all points.")
        else:
            QMessageBox.information(self, "No Filter", "No cell filter is currently applied.")

    def plot_selected_path(self):
        """Plot the selected timing paths."""
        if not hasattr(self, 'selected_rows') or not self.selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select one or more timing paths first.")
            return
            
        # Get all selected paths
        selected_paths = [self.paths[row] for row in self.selected_rows]
        
        # Determine ranking method from radio buttons
        if self.rankIncrRadio.isChecked():
            ranking_method = "incr"
        elif self.rankTransRadio.isChecked():
            ranking_method = "trans"
        else:
            ranking_method = "delta"
        
        # Get visualization cell filter if applied
        cell_filter_regex = getattr(self, 'visualization_cell_filter', None)
        
        # Get custom top ranked percentage
        try:
            top_ranked_percentage = float(self.topRankedPercentageInput.text()) / 100.0
            if top_ranked_percentage <= 0 or top_ranked_percentage > 1:
                top_ranked_percentage = 0.20  # Default to 20% if invalid
        except (ValueError, AttributeError):
            top_ranked_percentage = 0.20  # Default to 20% if invalid
        
        # Reset highlighted point when creating new plots
        if hasattr(self, 'highlighted_point'):
            delattr(self, 'highlighted_point')
        
        # Initialize highlighted points list for multiple selections
        self.highlighted_points = []
        
        # Clear any existing highlights from all plots
        self.clear_all_plot_highlights()
        
        # Clear table highlights when creating new plots
        self.clear_table_highlights()
        
        # Initialize plot figures list
        self.plot_figures = []
        
        # Get highlighted point if any (should be None now)
        highlight_point = getattr(self, 'highlighted_point', {}).get('point', None)
        
        # Get highlighted points for multiple selections
        highlighted_points = getattr(self, 'highlighted_points', [])
        
        # Plot each selected path
        for i, path in enumerate(selected_paths):
            path_label = f"Path {self.selected_rows[i] + 1}"
            display_path(path, ranking_method=ranking_method)
            
            # Get highlighted points for this specific path
            current_highlights = []
            for hp in highlighted_points:
                if hp.get('path_idx') == i:
                    # Verify that the point actually exists in this path
                    point_exists = any(
                        pt['pin'] == hp['point']['pin'] and 
                        pt['cell'] == hp['point']['cell'] and
                        pt['location'] == hp['point']['location']
                        for pt in path['points']
                    )
                    if point_exists:
                        current_highlights.append(hp['point'])
            
            # For backward compatibility, also check single highlighted point
            if highlight_point and self.highlighted_point.get('path_idx') == i:
                # Verify that the point actually exists in this path
                point_exists = any(
                    pt['pin'] == highlight_point['pin'] and 
                    pt['cell'] == highlight_point['cell'] and
                    pt['location'] == highlight_point['location']
                    for pt in path['points']
                )
                if point_exists and highlight_point not in current_highlights:
                    current_highlights.append(highlight_point)
            
            fig = plot_path(path, show_labels=self.showPinNamesCheck.isChecked(), 
                     show_legend=self.showLegendCheck.isChecked(),
                     ranking_method=ranking_method,
                     show_data_path=self.showDataPathCheck.isChecked(),
                     show_launch_clock=self.showLaunchClockCheck.isChecked(),
                     show_capture_clock=self.showCaptureClockCheck.isChecked(),
                     show_top_ranked_only=self.showTopRankedOnlyCheck.isChecked(),
                     cell_filter_regex=cell_filter_regex,
                     top_frac=top_ranked_percentage,
                     highlight_points=current_highlights)
            
            # Store the figure reference for highlighting
            self.plot_figures.append(fig)
            self.current_plot_figure = fig  # Keep the last one as current for backward compatibility
            
            # Add click event handler to the plot
            fig.canvas.mpl_connect('button_press_event', 
                lambda event, p=path, path_idx=i: self.on_plot_click(event, p, path_idx))
    
    def on_plot_click(self, event, path, path_idx):
        """Handle plot clicks to select corresponding point in table."""
        # Check if highlighting is enabled
        if not self.enableHighlightCheck.isChecked():
            return
            
        if event.inaxes is None:
            return
            
        # Convert click coordinates back to original scale
        click_x = event.xdata * 2000.0
        click_y = event.ydata * 2000.0
        
        # Find the closest point within a reasonable distance
        min_distance = float('inf')
        closest_point = None
        
        for point in path['points']:
            point_x, point_y = point['location']
            distance = ((click_x - point_x) ** 2 + (click_y - point_y) ** 2) ** 0.5
            
            if distance < min_distance and distance < 1000:  # Within 1mm
                min_distance = distance
                closest_point = point
        
        if closest_point:
            # Find the table that corresponds to this path
            for i in range(self.tab_widget.count()):
                tab_widget = self.tab_widget.widget(i)
                if hasattr(tab_widget, 'layout') and tab_widget.layout().count() > 0:
                    table = tab_widget.layout().itemAt(0).widget()
                    if hasattr(table, 'path_idx') and table.path_idx == path_idx:
                        # Find the row in the table that corresponds to this point
                        for row in range(table.rowCount()):
                            if hasattr(table, 'filtered_points') and row < len(table.filtered_points):
                                table_point = table.filtered_points[row]
                                if (table_point['pin'] == closest_point['pin'] and 
                                    table_point['cell'] == closest_point['cell']):
                                    # Select the row in the table
                                    table.selectRow(row)
                                    table.scrollToItem(table.item(row, 0))
                                    
                                    # Store the selected point
                                    self.highlighted_point = {
                                        'path_idx': path_idx,
                                        'point': closest_point,
                                        'pin': closest_point['pin'],
                                        'cell': closest_point['cell'],
                                        'location': closest_point['location']
                                    }
                                    
                                    # Add to highlighted points list for multiple selections
                                    new_highlight = {
                                        'path_idx': path_idx,
                                        'point': closest_point,
                                        'pin': closest_point['pin'],
                                        'cell': closest_point['cell'],
                                        'location': closest_point['location']
                                    }
                                    
                                    # Check if this point is already highlighted
                                    point_exists = any(
                                        hp['pin'] == closest_point['pin'] and 
                                        hp['cell'] == closest_point['cell'] and
                                        hp['location'] == closest_point['location'] and
                                        hp['path_idx'] == path_idx
                                        for hp in self.highlighted_points
                                    )
                                    
                                    if not point_exists:
                                        self.highlighted_points.append(new_highlight)
                                    
                                    # Clear highlights from all plots first
                                    if hasattr(self, 'plot_figures') and self.plot_figures:
                                        for fig in self.plot_figures:
                                            ax = fig.gca()
                                            for artist in ax.get_children():
                                                if hasattr(artist, '_highlighted_point'):
                                                    artist.remove()
                                            fig.canvas.draw()
                                            fig.canvas.flush_events()
                                    
                                    # Then highlight the selected point in the correct plot
                                    self.highlight_point_in_plot(closest_point)
                                    
                                    if self.useShortenedNamesCheck.isChecked():
                                        display_name = self.get_shortened_pin_name(closest_point['pin'])
                                    else:
                                        display_name = closest_point['pin']
                                    print(f"Selected point from plot: {display_name} ({closest_point['cell']}) at {closest_point['location']}")
                                    break
                        break

    def show_table(self):
        """Display the selected timing path data in a table format."""
        if not hasattr(self, 'selected_rows') or not self.selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select one or more timing paths first.")
            return
            
        # Get all selected paths
        selected_paths = [self.paths[row] for row in self.selected_rows]
        
        # Determine ranking method
        if self.rankIncrRadio.isChecked():
            ranking_method = "incr"
        elif self.rankTransRadio.isChecked():
            ranking_method = "trans"
        else:
            ranking_method = "delta"
            
        # Get visualization cell filter if applied
        cell_filter_regex = getattr(self, 'visualization_cell_filter', None)
        
        # Get custom top ranked percentage
        try:
            top_ranked_percentage = float(self.topRankedPercentageInput.text()) / 100.0
            if top_ranked_percentage <= 0 or top_ranked_percentage > 1:
                top_ranked_percentage = 0.20  # Default to 20% if invalid
        except (ValueError, AttributeError):
            top_ranked_percentage = 0.20  # Default to 20% if invalid
            
        # Helper to pick ranking value based on selected method
        def get_rank_val(pt):
            if ranking_method == "incr":
                return pt["incr"]
            elif ranking_method == "trans":
                return pt["trans"]
            elif ranking_method == "delta":
                delta_val = pt.get("delta", 0.0) if pt.get("delta") is not None else 0.0
                return abs(delta_val)  # Use absolute value for Delta
            else:
                return pt["incr"]  # Default to incr
        
        # Create a separate table for each selected path
        for path_idx, path in enumerate(selected_paths):
            # Create a new table widget for this path
            table = QTableWidget()
            
            # Set up the table with headers
            headers = ["Org #", "Order", "Pin", "Type", "Cell", "DTrans", "Trans", "Derate", "Delta", 
                      "Incr", "Path", "Location (µm)", "Path Type"]
            table.setColumnCount(len(headers))
            table.setHorizontalHeaderLabels(headers)
            
            # Enable column resizing
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
            table.horizontalHeader().setStretchLastSection(False)
            
            # Set initial column widths based on content type
            total_width = table.viewport().width()
            
            # Column width percentages
            width_percentages = {
                0: 5,    # Org # (5%)
                1: 5,    # Order (5%)
                2: 25,   # Pin (25%)
                3: 5,    # Type (5%)
                4: 10,   # Cell (10%)
                5: 7,    # DTrans (7%)
                6: 7,    # Trans (7%)
                7: 7,    # Derate (7%)
                8: 7,    # Delta (7%)
                9: 7,    # Incr (7%)
                10: 7,   # Path (7%)
                11: 8,   # Location (8%)
                12: 10   # Path Type (10%)
            }
            
            # Set the column widths
            for col, percentage in width_percentages.items():
                width = int(total_width * percentage / 100)
                table.setColumnWidth(col, width)
            
            # Enable sorting
            table.setSortingEnabled(True)
            
            # Enable selection of rows
            table.setSelectionBehavior(QTableWidget.SelectRows)
            table.setSelectionMode(QTableWidget.SingleSelection)
            
            # Get all points from the path
            all_points = path["points"]
            
            # Filter points based on selected path types
            filtered_points = []
            
            # Add points in the specified order: launch clock, data, capture clock
            # This matches the order in the timing report file
            if self.showLaunchClockCheck.isChecked():
                launch_clock_points = [pt for pt in path["clock_path"]]
                filtered_points.extend(launch_clock_points)
                
            if self.showDataPathCheck.isChecked():
                data_points = [pt for pt in path["data_path"]]
                filtered_points.extend(data_points)
                
            if self.showCaptureClockCheck.isChecked():
                capture_clock_points = [pt for pt in path.get("capture_path", [])]
                filtered_points.extend(capture_clock_points)
                
            # If no path types are selected, show all points
            if not filtered_points:
                filtered_points = all_points
                
            # Apply cell filter if provided
            if cell_filter_regex:
                filtered_points = [pt for pt in filtered_points 
                                 if not re.search(cell_filter_regex, pt["cell"], re.IGNORECASE)]
                
            # Always include highlighted point in table even if filtered out
            if hasattr(self, 'highlighted_point') and self.highlighted_point:
                highlight_point = self.highlighted_point.get('point')
                if highlight_point and self.highlighted_point.get('path_idx') == path_idx:
                    # Check if highlighted point is not already in filtered_points
                    point_exists = any(
                        pt['pin'] == highlight_point['pin'] and 
                        pt['cell'] == highlight_point['cell'] and
                        pt['location'] == highlight_point['location']
                        for pt in filtered_points
                    )
                    if not point_exists:
                        # Add the highlighted point to the table
                        filtered_points.append(highlight_point)
            
            # Calculate threshold for top ranked points
            values = [get_rank_val(pt) for pt in filtered_points]
            if values:
                threshold = sorted(values, reverse=True)[max(1, int(len(values) * top_ranked_percentage)) - 1]
            else:
                threshold = 0
                
            # If "Show only top ranked points" is checked, filter to only include top ranked points
            if self.showTopRankedOnlyCheck.isChecked():
                # Always include highlighted point even if it doesn't meet ranking criteria
                if hasattr(self, 'highlighted_point') and self.highlighted_point:
                    highlight_point = self.highlighted_point.get('point')
                    if highlight_point and self.highlighted_point.get('path_idx') == path_idx:
                        # Check if highlighted point is not already in filtered_points
                        point_exists = any(
                            pt['pin'] == highlight_point['pin'] and 
                            pt['cell'] == highlight_point['cell'] and
                            pt['location'] == highlight_point['location']
                            for pt in filtered_points
                        )
                        if not point_exists:
                            # Add the highlighted point to the table
                            filtered_points.append(highlight_point)
                
                # Now filter by ranking
                filtered_points = [pt for pt in filtered_points if get_rank_val(pt) >= threshold]
            
            # Store filtered points for this table to enable click handling
            table.filtered_points = filtered_points
            table.path_idx = path_idx
            
            # Connect cell click event
            table.cellClicked.connect(lambda row, col, t=table: 
                self.on_table_cell_clicked(row, col, t.path_idx, t.filtered_points))
            
            # Create a color gradient for the top 20% ranked points
            # From yellow (low delay) to red (high delay)
            def get_color_for_rank(rank_val, max_val):
                if rank_val < threshold:
                    return None  # No color for points below threshold
                
                # Calculate color intensity (0 to 1)
                # Normalize the rank value between threshold and max_val
                normalized_val = (rank_val - threshold) / (max_val - threshold) if max_val > threshold else 1.0
                intensity = min(1.0, normalized_val)
                
                # Create a gradient from yellow to red
                # Yellow: RGB(255, 255, 0)
                # Red: RGB(255, 0, 0)
                
                # Red component stays at 255
                r = 255
                
                # Green component decreases from 255 (yellow) to 0 (red)
                g = int(255 * (1 - intensity))
                
                # Blue component stays at 0
                b = 0
                
                return QColor(r, g, b)
            
            # Find the maximum rank value for color scaling
            max_rank_val = max([get_rank_val(pt) for pt in filtered_points]) if filtered_points else 0
            
            # Sort points by rank value (descending) for ordering
            sorted_points = sorted(filtered_points, key=lambda pt: get_rank_val(pt), reverse=True)
            
            # Create a function to get the rank order for a point
            def get_rank_order(point):
                try:
                    return sorted_points.index(point) + 1
                except ValueError:
                    return 0
            
            total_points = len(sorted_points)
            
            # Populate the table with data
            table.setRowCount(len(filtered_points))
            for i, pt in enumerate(filtered_points):
                # Determine path type
                path_type = ""
                if pt["pin"] == path["last_common_pin"]:
                    path_type = "LAST COMMON PIN"
                elif pt in path["clock_path"]:
                    path_type = "Launch Clock"
                elif pt in path.get("capture_path", []):
                    path_type = "Capture Clock"
                elif pt in path["data_path"]:
                    path_type = "Data"
                
                # Check if this is a launch or capture clock point
                if pt.get("is_launch_clock", False):
                    path_type = "Launch Clock"
                if pt.get("is_capture_clock", False):
                    path_type = "Capture Clock"
                
                # Determine pin type
                pin_type = "INPUT" if pt.get("is_input", False) else "OUTPUT"
                
                # Format location in micrometers (scale by 2000)
                x_um = pt['location'][0] / 2000.0
                y_um = pt['location'][1] / 2000.0
                location = f"({x_um:.2f}, {y_um:.2f})"
                
                # Get all timing values, using "-" for missing values
                dtrans = f"{pt.get('dtrans', '-')}" if pt.get('dtrans') is not None else "-"
                trans = f"{pt['trans']:.4f}" if pt['trans'] is not None else "-"
                derate = f"{pt['derate']:.4f}" if pt['derate'] is not None else "-"
                delta = f"{pt.get('delta', '-')}" if pt.get('delta') is not None else "-"
                incr = f"{pt['incr']:.4f}"
                path_delay = f"{pt.get('path_delay', '-')}" if pt.get('path_delay') is not None else "-"
                
                # Get the rank order for this point
                order = get_rank_order(pt)
                order_text = f"{order}/{total_points}"
                
                # Set cell values with proper numeric sorting for Order column
                table.setItem(i, 0, NumericTableWidgetItem(i + 1, is_numeric=True))  # Original order number
                table.setItem(i, 1, NumericTableWidgetItem(order, is_numeric=True))  # Rank order
                table.setItem(i, 2, NumericTableWidgetItem(pt['pin']))
                table.setItem(i, 3, NumericTableWidgetItem(pin_type))
                table.setItem(i, 4, NumericTableWidgetItem(pt['cell']))
                table.setItem(i, 5, NumericTableWidgetItem(dtrans))
                table.setItem(i, 6, NumericTableWidgetItem(trans))
                table.setItem(i, 7, NumericTableWidgetItem(derate))
                table.setItem(i, 8, NumericTableWidgetItem(delta))
                table.setItem(i, 9, NumericTableWidgetItem(incr))
                table.setItem(i, 10, NumericTableWidgetItem(path_delay))
                table.setItem(i, 11, NumericTableWidgetItem(location))
                table.setItem(i, 12, NumericTableWidgetItem(path_type))
                
                # Apply color gradient for top ranked points
                rank_val = get_rank_val(pt)
                color = get_color_for_rank(rank_val, max_rank_val)
                if color:
                    for col in range(table.columnCount()):
                        table.item(i, col).setBackground(color)
            
            # Adjust column widths to content
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            
            # Create a tab name for this individual path
            actual_start = path.get('actual_start', {}).get('pin', path['startpoint'])
            actual_end = path.get('actual_end', {}).get('pin', path['endpoint'])
            tab_name = f"Path {self.selected_rows[path_idx]+1}: {actual_start} ? {actual_end}"
            
            if len(tab_name) > 30:  # Truncate long tab names
                tab_name = tab_name[:27] + "..."
                
            # Create a widget to hold the table
            tab_widget = QWidget()
            tab_layout = QVBoxLayout(tab_widget)
            tab_layout.addWidget(table)
            tab_layout.setContentsMargins(0, 0, 0, 0)
            
            # Check if a tab with this name already exists
            existing_tab_index = -1
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i) == tab_name:
                    existing_tab_index = i
                    break
                    
            if existing_tab_index >= 0:
                # Replace existing tab
                self.tab_widget.removeTab(existing_tab_index)
                self.tab_widget.insertTab(existing_tab_index, tab_widget, tab_name)
                self.tab_widget.setCurrentIndex(existing_tab_index)
            else:
                # Add new tab
                self.tab_widget.addTab(tab_widget, tab_name)
                self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)
        
        # Show the tab widget
        self.tab_widget.show()
    
    def on_table_cell_clicked(self, row, column, path_idx, filtered_points):
        """Handle table cell clicks to highlight corresponding point in plot."""
        # Check if highlighting is enabled
        if not self.enableHighlightCheck.isChecked():
            return
            
        if row < len(filtered_points):
            selected_point = filtered_points[row]
            
            # Store the selected point for highlighting in plots
            self.highlighted_point = {
                'path_idx': path_idx,
                'point': selected_point,
                'pin': selected_point['pin'],
                'cell': selected_point['cell'],
                'location': selected_point['location']
            }
            
            # Add to highlighted points list for multiple selections
            new_highlight = {
                'path_idx': path_idx,
                'point': selected_point,
                'pin': selected_point['pin'],
                'cell': selected_point['cell'],
                'location': selected_point['location']
            }
            
            # Check if this point is already highlighted
            point_exists = any(
                hp['pin'] == selected_point['pin'] and 
                hp['cell'] == selected_point['cell'] and
                hp['location'] == selected_point['location'] and
                hp['path_idx'] == path_idx
                for hp in getattr(self, 'highlighted_points', [])
            )
            
            if not point_exists:
                if not hasattr(self, 'highlighted_points'):
                    self.highlighted_points = []
                self.highlighted_points.append(new_highlight)
            
            # Clear previous highlights in all tables
            for i in range(self.tab_widget.count()):
                tab_widget = self.tab_widget.widget(i)
                if hasattr(tab_widget, 'layout') and tab_widget.layout().count() > 0:
                    table = tab_widget.layout().itemAt(0).widget()
                    if hasattr(table, 'path_idx') and table.path_idx == path_idx:
                        # Restore original colors for this table
                        for r in range(table.rowCount()):
                            if hasattr(table, 'filtered_points') and r < len(table.filtered_points):
                                pt = table.filtered_points[r]
                                
                                # Get ranking method from UI
                                if self.rankIncrRadio.isChecked():
                                    ranking_method = "incr"
                                elif self.rankTransRadio.isChecked():
                                    ranking_method = "trans"
                                else:
                                    ranking_method = "delta"
                                
                                rank_val = self.get_rank_val(pt, ranking_method)
                                
                                # Calculate threshold and max value for this table
                                values = [self.get_rank_val(p, ranking_method) for p in table.filtered_points]
                                if values:
                                    threshold = sorted(values, reverse=True)[max(1, int(len(values) * 0.20)) - 1]
                                    max_rank_val = max(values)
                                    color = self.get_color_for_rank(rank_val, max_rank_val, threshold)
                                else:
                                    color = None
                                
                                for c in range(table.columnCount()):
                                    item = table.item(r, c)
                                    if item:
                                        if color:
                                            item.setBackground(color)
                                        else:
                                            item.setBackground(QColor(255, 255, 255))  # White background
            
            # Highlight the selected row in the current table
            current_table = None
            for i in range(self.tab_widget.count()):
                tab_widget = self.tab_widget.widget(i)
                if hasattr(tab_widget, 'layout') and tab_widget.layout().count() > 0:
                    table = tab_widget.layout().itemAt(0).widget()
                    if hasattr(table, 'path_idx') and table.path_idx == path_idx:
                        current_table = table
                        break
            
            if current_table:
                # Highlight all selected points in this table with different colors
                for highlight_idx, hp in enumerate(getattr(self, 'highlighted_points', [])):
                    if hp.get('path_idx') == path_idx:
                        # Find the row in the table that corresponds to this highlighted point
                        for r in range(current_table.rowCount()):
                            if hasattr(current_table, 'filtered_points') and r < len(current_table.filtered_points):
                                table_point = current_table.filtered_points[r]
                                if (table_point['pin'] == hp['point']['pin'] and 
                                    table_point['cell'] == hp['point']['cell'] and
                                    table_point['location'] == hp['point']['location']):
                                    
                                    # Use different colors for different selection order
                                    highlight_colors = [
                                        QColor(173, 216, 230),  # Light blue
                                        QColor(255, 182, 193),  # Light pink
                                        QColor(144, 238, 144),  # Light green
                                        QColor(255, 218, 185),  # Peach
                                        QColor(221, 160, 221),  # Plum
                                        QColor(255, 255, 224),  # Light yellow
                                        QColor(176, 224, 230),  # Powder blue
                                        QColor(255, 192, 203),  # Pink
                                    ]
                                    
                                    highlight_color = highlight_colors[highlight_idx % len(highlight_colors)]
                                    
                                    # Highlight the row with the selected color
                                    for c in range(current_table.columnCount()):
                                        item = current_table.item(r, c)
                                        if item:
                                            # Create a color overlay on top of the existing color
                                            current_color = item.background().color()
                                            # Blend the colors
                                            blended_color = QColor(
                                                min(255, (current_color.red() + highlight_color.red()) // 2),
                                                min(255, (current_color.green() + highlight_color.green()) // 2),
                                                min(255, (current_color.blue() + highlight_color.blue()) // 2)
                                            )
                                            item.setBackground(blended_color)
                                    break
            
            # If there's an active plot, highlight the point
            if hasattr(self, 'plot_figures') and self.plot_figures:
                # Clear highlights from all plots first
                for fig in self.plot_figures:
                    ax = fig.gca()
                    for artist in ax.get_children():
                        if hasattr(artist, '_highlighted_point'):
                            artist.remove()
                    fig.canvas.draw()
                    fig.canvas.flush_events()
                
                # Then highlight the selected point in the correct plot
                self.highlight_point_in_plot(selected_point)
            
            if self.useShortenedNamesCheck.isChecked():
                display_name = self.get_shortened_pin_name(selected_point['pin'])
            else:
                display_name = selected_point['pin']
            print(f"Selected point: {display_name} ({selected_point['cell']}) at {selected_point['location']}")
    
    def highlight_point_in_plot(self, point):
        """Highlight a specific point in the current plot."""
        if not hasattr(self, 'plot_figures') or not self.plot_figures:
            return
            
        # Get the path index for this point
        path_idx = getattr(self, 'highlighted_point', {}).get('path_idx', 0)
        
        # Make sure we have a valid path index
        if path_idx >= len(self.plot_figures):
            return
            
        # Get the target figure for this path
        target_fig = self.plot_figures[path_idx]
        ax = target_fig.gca()
        
        # Clear previous highlights in this plot
        for artist in ax.get_children():
            if hasattr(artist, '_highlighted_point'):
                artist.remove()
        
        # Highlight all points in the highlighted_points list for this path
        for highlight_idx, hp in enumerate(self.highlighted_points):
            if hp.get('path_idx') == path_idx:
                hp_point = hp['point']
                x, y = hp_point['location'][0] / 2000.0, hp_point['location'][1] / 2000.0
                
                # Use different colors for different selection order
                highlight_colors = [
                    'red',      # First selection
                    'blue',     # Second selection
                    'green',    # Third selection
                    'purple',   # Fourth selection
                    'orange',   # Fifth selection
                    'brown',    # Sixth selection
                    'pink',     # Seventh selection
                    'gray',     # Eighth selection
                ]
                
                highlight_color = highlight_colors[highlight_idx % len(highlight_colors)]
                
                # Draw a large circle around the highlighted point
                highlight_circle = plt.Circle((x, y), 0.5, color=highlight_color, fill=False, linewidth=3, alpha=0.8)
                highlight_circle._highlighted_point = True
                ax.add_patch(highlight_circle)
                
                # Add a text annotation
                if self.useShortenedNamesCheck.isChecked():
                    display_name = self.get_shortened_pin_name(hp_point['pin'])
                else:
                    display_name = hp_point['pin']
                    
                highlight_text = ax.text(x, y + 0.7, f"{display_name}", 
                                       color=highlight_color, fontsize=10, fontweight='bold',
                                       ha='center', va='bottom',
                                       bbox=dict(boxstyle="round,pad=0.3", facecolor='yellow', alpha=0.8))
                highlight_text._highlighted_point = True
                
                # Add tooltip with full pin name
                highlight_text.set_gid(f"highlight_{hp_point['pin']}")  # Set a unique ID for the text
                highlight_text._full_pin_name = hp_point['pin']  # Store the full pin name
        
        # Redraw the plot
        target_fig.canvas.draw()
        target_fig.canvas.flush_events()
    
    def get_rank_val(self, pt, ranking_method="incr"):
        """Helper function to get ranking value for a point."""
        if ranking_method == "incr":
            return pt["incr"]
        elif ranking_method == "trans":
            return pt["trans"]
        elif ranking_method == "delta":
            delta_val = pt.get("delta", 0.0) if pt.get("delta") is not None else 0.0
            return abs(delta_val)  # Use absolute value for Delta
        else:
            return pt["incr"]  # Default to incr

    def get_color_for_rank(self, rank_val, max_val, threshold):
        """Helper function to get color for ranked points."""
        if rank_val < threshold:
            return None  # No color for points below threshold
        
        # Calculate color intensity (0 to 1)
        # Normalize the rank value between threshold and max_val
        normalized_val = (rank_val - threshold) / (max_val - threshold) if max_val > threshold else 1.0
        intensity = min(1.0, normalized_val)
        
        # Create a gradient from yellow to red
        # Yellow: RGB(255, 255, 0)
        # Red: RGB(255, 0, 0)
        
        # Red component stays at 255
        r = 255
        
        # Green component decreases from 255 (yellow) to 0 (red)
        g = int(255 * (1 - intensity))
        
        # Blue component stays at 0
        b = 0
        
        return QColor(r, g, b)

    def export_to_excel(self):
        """Export all timing paths to an Excel file with detailed information."""
        try:
            # Ask user for save location
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Excel Report", "", "Excel Files (*.xlsx);;All Files (*)"
            )
            
            if not file_path:
                return  # User cancelled
                
            if not file_path.endswith('.xlsx'):
                file_path += '.xlsx'
                
            # Create a progress message
            QMessageBox.information(self, "Exporting", "Exporting timing data to Excel. This may take a moment...")
            
            # Create Excel writer
            with pd.ExcelWriter(file_path) as writer:
                # Create summary sheet
                summary_data = []
                for i, path in enumerate(self.paths):
                    summary_data.append({
                        'Path #': i+1,
                        'Startpoint': path['startpoint'],
                        'Endpoint': path['endpoint'],
                        'Launch Clock': path['launch_clock'],
                        'Capture Clock': path['capture_clock'],
                        'Path Group': path['path_group'],
                        'Slack': path['slack'],
                        'Last Common Pin': path['last_common_pin'] or 'N/A',
                        'Total Points': len(path['points'])
                    })
                
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
                
                # Create detailed sheets for each path
                for i, path in enumerate(self.paths):
                    sheet_name = f'Path_{i+1}'
                    if len(sheet_name) > 31:  # Excel sheet name length limit
                        sheet_name = sheet_name[:31]
                    
                    # Extract all points data
                    points_data = []
                    for pt in path['points']:
                        # Determine path type
                        path_type = ""
                        if pt["pin"] == path["last_common_pin"]:
                            path_type = "LAST COMMON PIN"
                        elif pt in path["clock_path"]:
                            path_type = "LAUNCH CLOCK"
                        elif pt in path.get("capture_path", []):
                            path_type = "CAPTURE CLOCK"
                        elif pt in path["data_path"]:
                            path_type = "DATA PATH"
                        
                        # Check if this is a launch or capture clock point
                        if pt.get("is_launch_clock", False):
                            path_type = "LAUNCH CLOCK"
                        if pt.get("is_capture_clock", False):
                            path_type = "CAPTURE CLOCK"
                        
                        # Determine pin type
                        pin_type = "INPUT" if pt.get("is_input", False) else "OUTPUT"
                        
                        # Format location
                        location = f"({pt['location'][0]:.2f}, {pt['location'][1]:.2f})"
                        
                        # Get all timing values
                        points_data.append({
                            'Pin': pt['pin'],
                            'Type': pin_type,
                            'Cell': pt['cell'],
                            'DTrans': pt.get('dtrans', '-'),
                            'Trans': pt['trans'] if pt['trans'] is not None else '-',
                            'Derate': pt['derate'] if pt['derate'] is not None else '-',
                            'Delta': pt.get('delta', '-'),
                            'Incr': pt['incr'],
                            'Path': pt.get('path_delay', '-'),
                            'Location': location,
                            'Path Type': path_type,
                            'X': pt['location'][0],
                            'Y': pt['location'][1]
                        })
                    
                    pd.DataFrame(points_data).to_excel(writer, sheet_name=sheet_name, index=False)
            
            QMessageBox.information(self, "Export Complete", f"Timing data exported to {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting to Excel: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def export_to_csv(self):
        """Export all timing paths to CSV files with detailed information."""
        try:
            # Ask user for save directory
            directory = QFileDialog.getExistingDirectory(
                self, "Select Directory to Save CSV Files"
            )
            
            if not directory:
                return  # User cancelled
                
            # Create a progress message
            QMessageBox.information(self, "Exporting", "Exporting timing data to CSV files. This may take a moment...")
            
            # Create summary CSV
            summary_path = os.path.join(directory, "timing_paths_summary.csv")
            with open(summary_path, 'w', newline='') as csvfile:
                fieldnames = ['Path #', 'Startpoint', 'Endpoint', 'Launch Clock', 'Capture Clock', 
                             'Path Group', 'Slack', 'Last Common Pin', 'Total Points']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for i, path in enumerate(self.paths):
                    writer.writerow({
                        'Path #': i+1,
                        'Startpoint': path['startpoint'],
                        'Endpoint': path['endpoint'],
                        'Launch Clock': path['launch_clock'],
                        'Capture Clock': path['capture_clock'],
                        'Path Group': path['path_group'],
                        'Slack': path['slack'],
                        'Last Common Pin': path['last_common_pin'] or 'N/A',
                        'Total Points': len(path['points'])
                    })
            
            # Create detailed CSV files for each path
            for i, path in enumerate(self.paths):
                csv_path = os.path.join(directory, f"timing_path_{i+1}.csv")
                with open(csv_path, 'w', newline='') as csvfile:
                    fieldnames = ['Pin', 'Type', 'Cell', 'DTrans', 'Trans', 'Derate', 'Delta', 
                                 'Incr', 'Path', 'Location', 'Path Type', 'X', 'Y']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for pt in path['points']:
                        # Determine path type
                        path_type = ""
                        if pt["pin"] == path["last_common_pin"]:
                            path_type = "LAST COMMON PIN"
                        elif pt in path["clock_path"]:
                            path_type = "LAUNCH CLOCK"
                        elif pt in path.get("capture_path", []):
                            path_type = "CAPTURE CLOCK"
                        elif pt in path["data_path"]:
                            path_type = "DATA PATH"
                        
                        # Check if this is a launch or capture clock point
                        if pt.get("is_launch_clock", False):
                            path_type = "LAUNCH CLOCK"
                        if pt.get("is_capture_clock", False):
                            path_type = "CAPTURE CLOCK"
                        
                        # Determine pin type
                        pin_type = "INPUT" if pt.get("is_input", False) else "OUTPUT"
                        
                        # Format location
                        location = f"({pt['location'][0]:.2f}, {pt['location'][1]:.2f})"
                        
                        # Get all timing values
                        writer.writerow({
                            'Pin': pt['pin'],
                            'Type': pin_type,
                            'Cell': pt['cell'],
                            'DTrans': pt.get('dtrans', '-'),
                            'Trans': pt['trans'] if pt['trans'] is not None else '-',
                            'Derate': pt['derate'] if pt['derate'] is not None else '-',
                            'Delta': pt.get('delta', '-'),
                            'Incr': pt['incr'],
                            'Path': pt.get('path_delay', '-'),
                            'Location': location,
                            'Path Type': path_type,
                            'X': pt['location'][0],
                            'Y': pt['location'][1]
                        })
            
            QMessageBox.information(self, "Export Complete", f"Timing data exported to CSV files in {directory}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting to CSV: {str(e)}")
            import traceback
            traceback.print_exc()

    def generate_timing_command(self):
        """Generate timing report command for the selected paths."""
        if not hasattr(self, 'selected_rows') or not self.selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select one or more timing paths first.")
            return
            
        # Get all selected paths
        selected_paths = [self.paths[row] for row in self.selected_rows]
        
        # Create a dialog to show the commands
        dialog = QDialog(self)
        dialog.setWindowTitle("Timing Report Commands")
        dialog.setMinimumWidth(800)
        dialog.setMinimumHeight(600)
        
        layout = QVBoxLayout(dialog)
        
        # Add text edit for commands
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet(f"""
            QTextEdit {{
                {self.FONT_STYLE}
                background-color: {self.IVORY};
                border: 2px solid {self.DARK_BLUE};
            }}
        """)
        layout.addWidget(text_edit)
        
        # Generate commands for each selected path
        commands = []
        for i, path in enumerate(selected_paths):
            # Get startpoint and endpoint
            startpoint = path.get('actual_start', {}).get('pin', path['startpoint'])
            endpoint = path.get('actual_end', {}).get('pin', path['endpoint'])
            
            # Get all pins in the data path
            through_pins = []
            for pt in path['data_path']:
                # Skip startpoint and endpoint
                if pt['pin'] != startpoint and pt['pin'] != endpoint:
                    through_pins.append(pt['pin'])
            
            # Build the command
            cmd = f"report_timing -net -from {startpoint}"
            
            # Add through points if any exist
            if through_pins:
                through_list = " ".join(through_pins)
                cmd += f" -through {{ {through_list} }}"
                
            cmd += f" -to {endpoint}"

            # Generate the command
            command = f"# Path {self.selected_rows[i] + 1}: {startpoint} -> {endpoint}\n"
            command += f"{cmd}\n\n"
            commands.append(command)
        
        # Display all commands
        text_edit.setPlainText("".join(commands))
        
        # Add close button
        close_button = QPushButton("Close")
        close_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.BLUE_GROTTO};
                color: {self.IVORY};
                border: 2px solid black;
                padding: 8px 20px;
                border-radius: 4px;
                {self.FONT_STYLE}
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.ROYAL_BLUE};
            }}
        """)
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        
        dialog.exec_()

    def adjust_column_widths(self):
        """Adjust column widths based on content length."""
        # Get the font metrics for width calculations
        font_metrics = self.table.fontMetrics()
        
        # Calculate maximum width needed for each column
        max_widths = {}
        
        # Check header widths
        for col in range(self.table.columnCount()):
            header_text = self.table.horizontalHeaderItem(col).text()
            max_widths[col] = font_metrics.horizontalAdvance(header_text) + 20  # Add padding
        
        # Check content widths
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    text = item.text()
                    width = font_metrics.horizontalAdvance(text) + 20  # Add padding
                    max_widths[col] = max(max_widths[col], width)
        
        # Set the column widths
        for col, width in max_widths.items():
            self.table.setColumnWidth(col, width)

    def put_individual_path(self):
        """Open a dialog to paste an individual timing path."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Put a Path")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(400)
        
        layout = QVBoxLayout(dialog)
        
        # Add text edit for path input
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("Paste your timing path here...")
        text_edit.setStyleSheet(f"""
            QTextEdit {{
                {self.FONT_STYLE}
                background-color: {self.IVORY};
                border: 2px solid {self.DARK_BLUE};
            }}
        """)
        layout.addWidget(text_edit)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("OK")
        ok_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.BLUE_GROTTO};
                color: {self.IVORY};
                border: 2px solid black;
                padding: 8px 20px;
                border-radius: 4px;
                {self.FONT_STYLE}
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.ROYAL_BLUE};
            }}
        """)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.SCARLET};
                color: {self.IVORY};
                border: 2px solid black;
                padding: 8px 20px;
                border-radius: 4px;
                {self.FONT_STYLE}
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.CRIMSON};
            }}
        """)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        # Connect buttons
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        if dialog.exec_() == QDialog.Accepted:
            path_text = text_edit.toPlainText()
            if path_text.strip():
                try:
                    # Parse the individual path
                    paths = parse_timing_paths(path_text)
                    if paths:
                        # Add the new path to existing paths
                        if not self.paths:
                            self.paths = []
                        self.paths.extend(paths)
                        self.update_path_list()
                        QMessageBox.information(self, "Success", f"Successfully added {len(paths)} timing path(s).")
                    else:
                        QMessageBox.warning(self, "No Paths Found", "No valid timing paths found in the input text.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error parsing timing path: {str(e)}")
                    import traceback
                    traceback.print_exc()

    def clear_all_plot_highlights(self):
        """Clear all highlights from all plots."""
        if hasattr(self, 'plot_figures') and self.plot_figures:
            for fig in self.plot_figures:
                ax = fig.gca()
                for artist in ax.get_children():
                    if hasattr(artist, '_highlighted_point'):
                        artist.remove()
                fig.canvas.draw()
                fig.canvas.flush_events()

    def clear_table_highlights(self):
        """Clear highlights from all tables."""
        for i in range(self.tab_widget.count()):
            tab_widget = self.tab_widget.widget(i)
            if hasattr(tab_widget, 'layout') and tab_widget.layout().count() > 0:
                table = tab_widget.layout().itemAt(0).widget()
                if hasattr(table, 'filtered_points'):
                    # Get ranking method from UI
                    if self.rankIncrRadio.isChecked():
                        ranking_method = "incr"
                    elif self.rankTransRadio.isChecked():
                        ranking_method = "trans"
                    else:
                        ranking_method = "delta"
                    
                    # Calculate threshold and max value for this table
                    values = [self.get_rank_val(p, ranking_method) for p in table.filtered_points]
                    if values:
                        threshold = sorted(values, reverse=True)[max(1, int(len(values) * 0.20)) - 1]
                        max_rank_val = max(values)
                    else:
                        threshold = 0
                        max_rank_val = 0
                    
                    for row in range(table.rowCount()):
                        if row < len(table.filtered_points):
                            pt = table.filtered_points[row]
                            rank_val = self.get_rank_val(pt, ranking_method)
                            color = self.get_color_for_rank(rank_val, max_rank_val, threshold)
                            
                            for col in range(table.columnCount()):
                                item = table.item(row, col)
                                if item:
                                    if color:
                                        item.setBackground(color)
                                    else:
                                        item.setBackground(QColor(255, 255, 255))  # White background

    def clear_all_highlighted_points(self):
        """Clear all highlighted points."""
        if hasattr(self, 'highlighted_points'):
            self.highlighted_points.clear()
        else:
            self.highlighted_points = []
        if hasattr(self, 'highlighted_point'):
            delattr(self, 'highlighted_point')
        self.clear_all_plot_highlights()
        self.clear_table_highlights()

    def on_highlight_toggled(self, checked):
        """Handle toggling of the highlight checkbox."""
        if not checked:
            # Clear all highlights when disabling highlight
            self.clear_all_highlighted_points()
            # Also clear the highlighted point reference
            if hasattr(self, 'highlighted_point'):
                delattr(self, 'highlighted_point')

    def get_shortened_pin_name(self, pin_name):
        """Get shortened pin name by taking the last part after the final '/' delimiter."""
        if not pin_name:
            return ""
        # Split by '/' and take the last part
        parts = pin_name.split('/')
        return parts[-1] if parts else pin_name

    def on_shortened_names_toggled(self, checked):
        """Handle toggling of the shortened names checkbox."""
        # Update existing highlights if any
        if hasattr(self, 'highlighted_points') and self.highlighted_points:
            # Re-highlight all current points to update the display names
            for hp in self.highlighted_points:
                current_point = hp.get('point')
                if current_point:
                    self.highlight_point_in_plot(current_point)

    def clear_path_selection(self):
        """Clear the selection in the table."""
        self.table.clearSelection()

    def show_primetime_guide(self):
        """Show a dialog with essential PrimeTime report_timing options and a copy button"""
        pt_options = [
            "-path_type full_clock_expanded",
            "-input_pins",
            "-transition_time",
            "-crosstalk_delta",
            "-derate",
            "-physical",
        ]
        pt_options_text = "\n".join(pt_options)

        dialog = QDialog(self)
        dialog.setWindowTitle("PrimeTime report_timing options")
        dialog.setMinimumWidth(400)
        dialog.setMinimumHeight(220)
        layout = QVBoxLayout(dialog)

        label = QLabel("Recommended options for report_timing:")
        label.setStyleSheet(f"{self.FONT_STYLE} font-weight: bold;")
        layout.addWidget(label)

        text_box = QTextEdit(pt_options_text)
        text_box.setReadOnly(True)
        text_box.setStyleSheet(f"background-color: {self.IVORY}; {self.FONT_STYLE}")
        layout.addWidget(text_box)

        copy_btn = QPushButton("Copy Options to Clipboard")
        copy_btn.setStyleSheet(f"background-color: {self.BLUE_GROTTO}; color: {self.IVORY}; {self.FONT_STYLE} font-weight: bold;")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(pt_options_text))
        layout.addWidget(copy_btn)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(f"background-color: {self.SCARLET}; color: {self.IVORY}; {self.FONT_STYLE} font-weight: bold;")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec_()

    def load_timing_file_from_input(self):
        """Load timing file from the path entered by the user"""
        file_path = self.filePathInput.text().strip()
        if not file_path:
            QMessageBox.warning(self, "No File Path", "Please enter a timing file path.")
            return
        if not os.path.exists(file_path):
            QMessageBox.critical(self, "File Not Found", f"File not found:\n{file_path}")
            return
        try:
            with open(file_path, "r") as f:
                print(f"Reading timing report from: {file_path}")
                rpt_text = f.read()
                file_size_mb = len(rpt_text) / (1024 * 1024)
                print(f"File size: {file_size_mb:.2f} MB")
            self.current_file_content = rpt_text
            self.current_file_path = file_path
            print("Starting to parse timing paths...")
            self.paths = parse_timing_paths(rpt_text)
            if not self.paths:
                QMessageBox.warning(self, "No Paths Found", "No timing paths found in the selected file.")
                return
            print(f"Found {len(self.paths)} timing paths.")
            self.update_path_list()
            QMessageBox.information(self, "Success", f"Successfully loaded {len(self.paths)} timing paths.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading timing file: {str(e)}")
            import traceback
            traceback.print_exc()


def select_rpt_file() -> str:
    app = QApplication(sys.argv)
    file_path, _ = QFileDialog.getOpenFileName(
        None, "Select Timing Report", "", "Timing Reports (*.rpt *.txt);;All Files (*)"
    )
    if not file_path:
        print("[ERROR] No file selected.")
        sys.exit(1)
    return file_path


def parse_point(pin: str, cell: str, rest: str, cell_filter_regex: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Parse a single point from the timing report."""
    # Skip header lines and clock-related lines
    if pin == "Point" or pin == "clock" or pin == "clock source latency":
        return None
    
    # Apply cell type filter if provided
    if cell_filter_regex and re.search(cell_filter_regex, cell, re.IGNORECASE):
        return None
    
    # Split the line into parts
    parts = rest.strip().split()
    
    # Check if we have enough parts for timing values
    if len(parts) < 3:
        return None
    
    try:
        # Extract coordinates from the last part
        coords_match = re.search(r'\(([\d\.]+),([\d\.]+)\)', parts[-1])
        if not coords_match:
            return None
            
        x = float(coords_match.group(1))
        y = float(coords_match.group(2))
        
        # Initialize timing values
        dtrans = None
        trans = None
        derate = None
        delta = None
        incr = 0.0
        path_delay = 0.0
        
        # Determine if this is an input pin or output pin based on the format
        is_input = False
        
        # Count the number of numeric columns before the location
        numeric_columns = 0
        for part in parts:
            try:
                float(part)
                numeric_columns += 1
            except ValueError:
                pass
        
        # If there are 6 or more numeric columns (DTrans, Trans, Derate, Delta, Incr, Path),
        # this is an INPUT pin
        if numeric_columns >= 6:
            # Input pin format
            # Find DTrans, Trans, Derate, Delta, Incr values
            for i, part in enumerate(parts):
                if part != "-" and part != "&" and part != "r" and part != "f":
                    try:
                        if dtrans is None:
                            dtrans = float(part)
                        elif trans is None:
                            trans = float(part)
                        elif derate is None:
                            derate = float(part)
                        elif delta is None:
                            delta = float(part)
                        elif incr == 0.0:
                            incr = float(part)
                        else:
                            break
                    except ValueError:
                        continue
            
            # Look for Path value after Incr
            for i, part in enumerate(parts):
                if part == "&" and i + 1 < len(parts):
                    try:
                        path_delay = float(parts[i + 1])
                        break
                    except ValueError:
                        continue
            
            is_input = True
        else:
            # Output pin format: Trans Derate Incr Path Location
            # Find the Trans value
            for i, part in enumerate(parts):
                if part != "-" and part != "&" and part != "r" and part != "f":
                    try:
                        if trans is None:
                            trans = float(part)
                        elif derate is None:
                            derate = float(part)
                        elif incr == 0.0:
                            incr = float(part)
                        else:
                            break
                    except ValueError:
                        continue
            
            # Look for Path value after Incr
            for i, part in enumerate(parts):
                if part == "&" and i + 1 < len(parts):
                    try:
                        path_delay = float(parts[i + 1])
                        break
                    except ValueError:
                        continue
            
            is_input = False
        
        # Check if this is a launch clock point
        is_launch_clock = False
        if "clock" in pin.lower() or "clk" in pin.lower():
            if "LAUNCH CLOCK" in rest:
                is_launch_clock = True
        
        # Check if this is a capture clock point
        is_capture_clock = False
        if "clock" in pin.lower() or "clk" in pin.lower():
            if "CAPTURE CLOCK" in rest:
                is_capture_clock = True
        
        # Store the original line format for display
        original_format = f"{pin} {cell} {rest}"
        
        # For input pins, set incr to 0.0 to match the original format
        if is_input:
            incr = 0.0
        
        return {
            "pin": pin,
            "cell": cell,
            "is_input": is_input,
            "dtrans": dtrans,
            "trans": trans,
            "derate": derate,
            "delta": delta,
            "incr": incr,
            "path_delay": path_delay,
            "location": (x, y),
            "is_launch_clock": is_launch_clock,
            "is_capture_clock": is_capture_clock,
            "original_format": original_format,
        }
    except (ValueError, IndexError) as e:
        print(f"[WARN] Failed to parse point {pin}: {e}")
        return None

def parse_timing_paths(report_text: str, cell_filter_regex: Optional[str] = None) -> List[Dict[str, Any]]:
    """Parse timing paths from the report text."""
    start_time = time.time()
    print("Parsing timing paths...")
    
    if cell_filter_regex:
        print(f"Applying cell filter regex: {cell_filter_regex}")
    
    # Precompile regex patterns for better performance
    path_block_pattern = re.compile(r"(?=^\s*Startpoint: )", re.MULTILINE)
    startpoint_pattern = re.compile(r"Startpoint:\s+(\S+)")
    endpoint_pattern = re.compile(r"Endpoint:\s+(\S+)")
    clock_pattern = re.compile(r"clocked by (\S+)")
    slack_pattern = re.compile(r"slack.*?([\-\d\.]+)\s*$", flags=re.MULTILINE)
    group_pattern = re.compile(r"Path Group:\s+(\S+)")
    last_common_pattern = re.compile(r"Last common pin:\s+(\S+)")
    period_pattern = re.compile(r"clock\s+(\S+)\s+\((\w+)\s+edge\)")
    crpr_pattern = re.compile(r"clock reconvergence pessimism\s+([\-\d\.]+)")
    clock_uncertainty_pattern = re.compile(r"clock uncertainty\s+([\-\d\.]+)")
    setup_hold_pattern = re.compile(r"\s+(?:\*|library|clock gating)\s+(setup|hold)\s+time\s+([\-\d\.]+)\s+([\-\d\.]+)")
    data_required_pattern = re.compile(r"data required time\s+([\-\d\.]+)")
    
    # Split the report into blocks where each block starts with "Startpoint:"
    path_blocks = path_block_pattern.split(report_text)
    timing_paths = []
    
    total_blocks = len(path_blocks)
    print(f"Found {total_blocks} timing path blocks to process")
    
    # Process blocks in batches for better performance
    batch_size = 20
    for batch_start in range(0, total_blocks, batch_size):
        batch_end = min(batch_start + batch_size, total_blocks)
        
        for i in range(batch_start, batch_end):
            block = path_blocks[i]
            if not block.strip().startswith("Startpoint:"):
                continue
                
            try:
                # Extract path information using precompiled patterns
                start_match = startpoint_pattern.search(block)
                end_match = endpoint_pattern.search(block)
                
                if not start_match or not end_match:
                    continue
                    
                start_declared = start_match.group(1)
                end = end_match.group(1)
                
                clocks = clock_pattern.findall(block)
                launch_clk = clocks[0] if clocks else "?"
                capture_clk = clocks[-1] if clocks else "?"
                
                slack_match = slack_pattern.search(block)
                slack = float(slack_match.group(1)) if slack_match else 0.0
                
                group_match = group_pattern.search(block)
                path_group = group_match.group(1) if group_match else "N/A"
                
                last_common = last_common_pattern.search(block)
                last_common_pin = last_common.group(1) if last_common else None
                
                # Extract period information
                period = 0.0
                period_matches = period_pattern.findall(block)
                
                # Extract CRPR, Clock Uncertainty, Setup/Hold Time, and Data Required Time
                crpr = 0.0
                crpr_match = crpr_pattern.search(block)
                if crpr_match:
                    crpr = float(crpr_match.group(1))
                
                clock_uncertainty = 0.0
                clock_uncertainty_match = clock_uncertainty_pattern.search(block)
                if clock_uncertainty_match:
                    clock_uncertainty = float(clock_uncertainty_match.group(1))
                
                # Updated extraction for setup/hold time
                setup_hold_time = 0.0
                setup_hold_type = "setup"
                
                # Try to find setup/hold time using the updated pattern
                setup_hold_match = setup_hold_pattern.search(block)
                if setup_hold_match:
                    setup_hold_type = setup_hold_match.group(1)
                    setup_hold_time = float(setup_hold_match.group(3))
                else:
                    # Fallback to the old pattern if the new one doesn't match
                    old_setup_hold_pattern = re.compile(r"clock gating (setup|hold) time\s+([\-\d\.]+)")
                    old_setup_hold_match = old_setup_hold_pattern.search(block)
                    if old_setup_hold_match:
                        setup_hold_type = old_setup_hold_match.group(1)
                        setup_hold_time = float(old_setup_hold_match.group(2))
                
                data_required_time = 0.0
                data_required_match = data_required_pattern.search(block)
                if data_required_match:
                    data_required_time = float(data_required_match.group(1))
                
                # Find clock edge information
                clock_edge_lines = []
                lines = block.split('\n')
                for line in lines:
                    if "clock" in line and "edge" in line:
                        name_edge_match = re.search(r"clock\s+(\S+)\s+\((\w+)\s+edge\)", line)
                        if name_edge_match:
                            clock_name = name_edge_match.group(1)
                            edge_type = name_edge_match.group(2)
                            
                            # Extract the last number in the line (edge value)
                            numbers = re.findall(r"([\d\.]+)\s*$", line)
                            if numbers:
                                edge_value = float(numbers[-1])
                                clock_edge_lines.append((clock_name, edge_type, edge_value))
                            else:
                                # If no numbers at the end, try to find all numbers in the line
                                all_numbers = re.findall(r"([\d\.]+)", line)
                                if all_numbers:
                                    edge_value = float(all_numbers[-1])
                                    clock_edge_lines.append((clock_name, edge_type, edge_value))
                
                # If we found at least two clock edge lines, use them to calculate the period
                launch_clock_edge = None
                capture_clock_edge = None
                launch_clock_edge_value = 0.0
                capture_clock_edge_value = 0.0
                
                if len(clock_edge_lines) >= 2:
                    # First line is launch clock edge
                    launch_clock_name, launch_edge_type, launch_edge_value = clock_edge_lines[0]
                    launch_clock_edge = f"{launch_clock_name} ({launch_edge_type} edge)"
                    launch_clock_edge_value = launch_edge_value
                    
                    # Second line is capture clock edge
                    capture_clock_name, capture_edge_type, capture_edge_value = clock_edge_lines[1]
                    capture_clock_edge = f"{capture_clock_name} ({capture_edge_type} edge)"
                    capture_clock_edge_value = capture_edge_value
                    
                    # Calculate period as the difference between capture and launch edge values
                    period = capture_clock_edge_value - launch_clock_edge_value
                else:
                    # Try to find period directly in the report
                    period_match = re.search(r"Period\s+(\d+\.\d+)", block)
                    if period_match:
                        period = float(period_match.group(1))
                
                # Split block into data and capture sections if "data arrival time" is present.
                if "data arrival time" in block:
                    data_section, capture_section = block.split("data arrival time", 1)
                else:
                    data_section = block
                    capture_section = ""

                # Process points in the data section
                points = []
                data_lines = data_section.split('\n')
                
                for line in data_lines:
                    # Skip empty lines and header lines
                    if not line.strip() or line.strip().startswith("Point") or "clock" in line:
                        continue
                    
                    # Try to parse the line as a point
                    parts = line.strip().split()
                    if len(parts) >= 3:  # Need at least pin, cell, and some timing values
                        pin = parts[0]
                        cell = parts[1].strip('()')
                        rest = ' '.join(parts[2:])
                        point = parse_point(pin, cell, rest, cell_filter_regex)
                        if point:
                            points.append(point)

                # Record where the capture section begins
                capture_start_idx = len(points)
                
                # Process points in the capture section
                capture_lines = capture_section.split('\n')
                
                for line in capture_lines:
                    # Skip empty lines and header lines
                    if not line.strip() or line.strip().startswith("Point") or "clock" in line:
                        continue
                    
                    # Try to parse the line as a point
                    parts = line.strip().split()
                    if len(parts) >= 3:  # Need at least pin, cell, and some timing values
                        pin = parts[0]
                        cell = parts[1].strip('()')
                        rest = ' '.join(parts[2:])
                        point = parse_point(pin, cell, rest, cell_filter_regex)
                        if point:
                            points.append(point)

                if not points:
                    continue

                # Find the startpoint in the data section
                start_idx = next((i for i, pt in enumerate(points) if start_declared in pt["pin"]), 0)
                
                # Clock path: points before the startpoint
                clock_path = points[:start_idx]
                
                # Data path: from startpoint until capture section starts
                data_path = points[start_idx:capture_start_idx]
                
                # Capture path: points from the capture section
                capture_path = points[capture_start_idx:] if capture_lines else []

                # Determine the actual start and end points of the data path
                actual_start = data_path[0] if data_path else None
                actual_end = data_path[-1] if data_path else None
                
                # Calculate launch and capture clock latencies
                launch_clock_latency = 0.0
                capture_clock_latency = 0.0
                
                # Get launch clock latency from the startpoint's path value
                if actual_start and "path_delay" in actual_start:
                    launch_clock_latency = actual_start["path_delay"]
                
                # Get capture clock latency from the last point of capture path
                if capture_path and len(capture_path) > 0:
                    last_capture_point = capture_path[-1]
                    if "path_delay" in last_capture_point:
                        # Capture clock latency includes the capture rise/fall edge, so we need to subtract the period
                        capture_clock_latency = last_capture_point["path_delay"] - period
                
                # Calculate skew
                skew = capture_clock_latency - launch_clock_latency

                # --- Extract dominant exceptions section ---
                exception_setup = None
                exception_hold = None
                exception_rows = []
                # Find the exceptions section
                exc_start = block.find('The dominant exceptions are:')
                if exc_start != -1:
                    exc_lines = block[exc_start:].splitlines()
                    # Find the header line
                    header_idx = None
                    for idx, line in enumerate(exc_lines):
                        if line.strip().startswith('From') and 'Setup' in line and 'Hold' in line:
                            header_idx = idx
                            break
                    if header_idx is not None:
                        # Parse all exception rows after the header and separator
                        for line in exc_lines[header_idx+2:]:
                            if not line.strip() or line.strip().startswith('The overridden exceptions are:'):
                                break
                            parts = line.split()
                            # Try to extract Setup and Hold (last two columns)
                            if len(parts) >= 5:
                                setup_val = parts[-2]
                                hold_val = parts[-1]
                                exception_rows.append({
                                    'from': parts[0],
                                    'through': parts[1],
                                    'to': parts[2],
                                    'setup': setup_val,
                                    'hold': hold_val,
                                    'raw': line.strip()
                                })
                        # Use the first row as summary if available
                        if exception_rows:
                            exception_setup = exception_rows[0]['setup']
                            exception_hold = exception_rows[0]['hold']

                timing_paths.append({
                    "startpoint": start_declared,
                    "endpoint": end,
                    "launch_clock": launch_clk,
                    "capture_clock": capture_clk,
                    "last_common_pin": last_common_pin,
                    "path_group": path_group,
                    "slack": slack,
                    "period": period,
                    "launch_clock_edge": launch_clock_edge,
                    "capture_clock_edge": capture_clock_edge,
                    "launch_clock_edge_value": launch_clock_edge_value,
                    "capture_clock_edge_value": capture_clock_edge_value,
                    "points": points,
                    "clock_path": clock_path,
                    "data_path": data_path,
                    "capture_path": capture_path,
                    "actual_start": actual_start,
                    "actual_end": actual_end,
                    "launch_clock_latency": launch_clock_latency,
                    "capture_clock_latency": capture_clock_latency,
                    "skew": skew,
                    "crpr": crpr,
                    "clock_uncertainty": clock_uncertainty,
                    "setup_hold_time": setup_hold_time,
                    "setup_hold_type": setup_hold_type,
                    "data_required_time": data_required_time,
                    # --- new exception info ---
                    "exception_setup": exception_setup,
                    "exception_hold": exception_hold,
                    "exception_rows": exception_rows
                })
            except Exception as e:
                print(f"[WARN] Failed to parse path block {i+1}: {e}")
                import traceback
                traceback.print_exc()

    parse_time = time.time() - start_time
    print(f"Successfully parsed {len(timing_paths)} timing paths in {parse_time:.2f} seconds")
    return timing_paths


def display_path(path: dict, top_frac: float = 0.20, ranking_method="incr"):
    """Display information about a timing path.
    
    Args:
        path: The timing path dictionary
        top_frac: Fraction of points to mark as top ranked
        ranking_method: Method to use for ranking points ("incr", "trans", or "delta")
    """
    print("=" * 80)
    print(f"Startpoint: {path['startpoint']}")
    print(f"Endpoint  : {path['endpoint']}")
    print(f"Launch CLK: {path['launch_clock']}")
    print(f"Capture CLK: {path['capture_clock']}")
    print(f"Last Common Pin: {path['last_common_pin']}")
    print(f"Path Group: {path['path_group']}")
    print(f"Slack: {path['slack']}")

    points = path["points"]
    clock_path = path["clock_path"]
    data_path = path["data_path"]
    capture_path = path.get("capture_path", [])

    # Helper to pick ranking value based on selected method.
    def get_rank_val(pt):
        if ranking_method == "incr":
            return pt["incr"]
        elif ranking_method == "trans":
            return pt["trans"]
        elif ranking_method == "delta":
            delta_val = pt.get("delta", 0.0) if pt.get("delta") is not None else 0.0
            return abs(delta_val)  # Use absolute value for Delta
        else:
            return pt["incr"]  # Default to incr

    values = [get_rank_val(pt) for pt in points]
    threshold = sorted(values, reverse=True)[max(1, int(len(values) * top_frac)) - 1]

    # Print column headers
    print("\nPoint List:")
    print(f"{'Pin':60} {'Type':6} {'Cell':20} {'DTrans':8} {'Trans':8} {'Derate':8} {'Delta':8} {'Incr':8} {'Path':8} {'Location':20} {'Path Type':15}")
    print("-" * 150)

    for pt in points:
        # Determine path type
        path_type = ""
        if pt["pin"] == path["last_common_pin"]:
            path_type = "LAST COMMON PIN"
        elif get_rank_val(pt) >= threshold:
            path_type = "TOP 20% RANKED"
        elif pt in clock_path:
            path_type = "LAUNCH CLOCK"
        elif pt in capture_path:
            path_type = "CAPTURE CLOCK"
        elif pt in data_path:
            path_type = "DATA PATH"
        
        # Check if this is a launch or capture clock point
        if pt.get("is_launch_clock", False):
            path_type = "LAUNCH CLOCK"
        if pt.get("is_capture_clock", False):
            path_type = "CAPTURE CLOCK"
        
        # Determine pin type based on the presence of DTrans and Delta values
        # Input pins have both DTrans and Delta values
        pin_type = "INPUT" if pt.get("is_input", False) else "OUTPUT"
        
        # Format location
        location = f"({pt['location'][0]:.2f}, {pt['location'][1]:.2f})"
        
        # Get all timing values, using "-" for missing values
        dtrans = f"{pt.get('dtrans', '-')}" if pt.get('dtrans') is not None else "-"
        trans = f"{pt['trans']:.4f}" if pt['trans'] is not None else "-"
        derate = f"{pt['derate']:.4f}" if pt['derate'] is not None else "-"
        delta = f"{pt.get('delta', '-')}" if pt.get('delta') is not None else "-"
        incr = f"{pt['incr']:.4f}"
        path_delay = f"{pt.get('path_delay', '-')}" if pt.get('path_delay') is not None else "-"
        
        # Print the line with all timing values
        print(f"{pt['pin']:60} {pin_type:6} {pt['cell']:20} {dtrans:8} {trans:8} {derate:8} {delta:8} {incr:8} {path_delay:8} {location:20} {path_type:15}")
        
        # Print the original format from the timing report for debugging
        # Use the stored original format if available
        if "original_format" in pt:
            #print(f"  Original format: {pt['original_format']}")
            print(f"  Original:")
        else:
            # Fallback to reconstructed format if original format is not available
            if pin_type == "INPUT":
                # Input pin format: DTrans Trans Derate Delta Incr Path Location
                # Add "&" before Path value and "f" or "r" after it
                # Use the original incr value from the report, not the parsed one
                original_incr = "0.0000"  # Default value for input pins
                print(f"  Original format: {pt['pin']} {pt['cell']} {dtrans} {trans} {derate} {delta} {original_incr} & {path_delay} f {location}")
            else:
                # Output pin format: Trans Derate Incr Path Location
                # Add "&" before Path value and "f" or "r" after it
                print(f"  Original format: {pt['pin']} {pt['cell']} {trans} {derate} {incr} & {path_delay} f {location}")


def plot_path(path: dict, top_frac: float = 0.20, show_labels: bool = True, show_legend: bool = True, 
              ranking_method="incr", show_data_path=True, show_launch_clock=True, 
              show_capture_clock=True, show_top_ranked_only=False, cell_filter_regex=None, 
              highlight_points=None):
    """Plot a timing path visualization.
    
    Args:
        path: The timing path dictionary
        top_frac: Fraction of points to mark as top ranked
        show_labels: Whether to show pin names on the plot
        show_legend: Whether to show the legend on the plot
        ranking_method: Method to use for ranking points ("incr", "trans", or "delta")
        show_data_path: Whether to show the data path
        show_launch_clock: Whether to show the launch clock path
        show_capture_clock: Whether to show the capture clock path
        show_top_ranked_only: Whether to show only top ranked points
        cell_filter_regex: Optional regex pattern to filter cell types
        highlight_points: Optional list of points to highlight in the plot
    """
    start_time = time.time()
    print("Generating visualization...")
    
    # Extract points
    extract_start = time.time()
    points = path["points"]
    clock_path = path["clock_path"]
    data_path = path["data_path"]
    capture_path = path.get("capture_path", [])
    print(f"  - Extracting points: {time.time() - extract_start:.4f} seconds")

    # Helper to pick ranking value based on selected method.
    def get_rank_val(pt):
        if ranking_method == "incr":
            return pt["incr"]
        elif ranking_method == "trans":
            return pt["trans"]
        elif ranking_method == "delta":
            delta_val = pt.get("delta", 0.0) if pt.get("delta") is not None else 0.0
            return abs(delta_val)  # Use absolute value for Delta
        else:
            return pt["incr"]  # Default to incr

    values = [get_rank_val(pt) for pt in points]
    threshold = sorted(values, reverse=True)[max(1, int(len(values) * top_frac)) - 1]

    # Determine first and last point of the data path (for "S" and "E" markers)
    s_point = data_path[0] if data_path else None
    e_point = data_path[-1] if data_path else None

    # Determine LS and CS markers for launch and capture clock starting points.
    ls_point = clock_path[0] if clock_path else None
    cs_point = capture_path[0] if capture_path else None
    
    # Extract Period information from the path
    period = path.get("period", 0.0)
    
    # Get clock edge information
    launch_clock_edge = path.get("launch_clock_edge", "Unknown")
    capture_clock_edge = path.get("capture_clock_edge", "Unknown")
    launch_clock_edge_value = path.get("launch_clock_edge_value", 0.0)
    capture_clock_edge_value = path.get("capture_clock_edge_value", 0.0)
    
    # Get latency and skew information
    launch_clock_latency = path.get("launch_clock_latency", 0.0)
    capture_clock_latency = path.get("capture_clock_latency", 0.0)
    skew = path.get("skew", 0.0)
    
    # Get CRPR, Clock Uncertainty, Setup/Hold Time, and Data Required Time
    crpr = path.get("crpr", 0.0)
    clock_uncertainty = path.get("clock_uncertainty", 0.0)
    setup_hold_time = path.get("setup_hold_time", 0.0)
    setup_hold_type = path.get("setup_hold_type", "setup")
    data_required_time = path.get("data_required_time", 0.0)
    
    # DEBUG: Print detailed information about clock latencies and skew
    print("\n" + "="*80)
    print("DEBUG - CLOCK LATENCY AND SKEW INFORMATION:")
    #print(f"Launch Clock: {path['launch_clock']}")
    #print(f"Capture Clock: {path['capture_clock']}")
    print(f"Launch Clock Edge: {launch_clock_edge}")
    print(f"Capture Clock Edge: {capture_clock_edge}")
    print(f"Launch Edge Value: {launch_clock_edge_value:.4f}")
    print(f"Capture Edge Value: {capture_clock_edge_value:.4f}")
    print(f"Period: {period:.4f}")
    print(f"Launch Clock Latency: {launch_clock_latency:.4f}")
    print(f"Capture Clock Latency: {capture_clock_latency:.4f}")
    print(f"Clock Skew: {skew:.4f}")
    print(f"CRPR: {crpr:.4f}")
    print(f"Clock Uncertainty: {clock_uncertainty:.4f}")
    print(f"{setup_hold_type.capitalize()} Time: {setup_hold_time:.4f}")
    print(f"Data Required Time: {data_required_time:.4f}")
    
    # Print the points used for latency calculation
    if s_point:
        print(f"\nLaunch Clock Point: {s_point['pin']} (Path: {s_point.get('path_delay', 0.0):.4f})")
    else:
        print("\nLaunch Clock Point: Not found")
        
    if capture_path and len(capture_path) > 0:
        last_capture_point = capture_path[-1]
        print(f"Capture Clock Point: {last_capture_point['pin']} (Path: {last_capture_point.get('path_delay', 0.0):.4f})")
    else:
        print("Capture Clock Point: Not found")
    
    print("="*80 + "\n")

    # Create figure with a white background for better performance
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(10, 8), facecolor='white')
    ax.set_facecolor('white')

    # Draw arrows between points using scaled coordinates (µm)
    def draw_arrows(segment, color, label=None):
        if not segment:
            return
            
        # Pre-calculate all coordinates for better performance
        coords = [(pt["location"][0] / 2000.0, pt["location"][1] / 2000.0) for pt in segment]
        
        # Draw all arrows at once
        for i in range(len(coords) - 1):
            x1, y1 = coords[i]
            x2, y2 = coords[i + 1]
            arrow = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='->', color=color, alpha=0.6, mutation_scale=10)
            ax.add_patch(arrow)
            
        # Add label only to the first arrow
        if label and len(coords) > 1:
            x1, y1 = coords[0]
            x2, y2 = coords[1]
            ax.plot([x1, x2], [y1, y2], color=color, label=label, alpha=0.6)

    # Draw the three path types with different colors and labels, respecting filter settings
    if show_launch_clock:
        draw_arrows(clock_path, color='orange', label='Launch Clock Path')
    if show_data_path:
        draw_arrows(data_path, color='blue', label='Data Path')
    if show_capture_clock:
        draw_arrows(capture_path, color='green', label='Capture Clock Path')

    # Pre-calculate all coordinates for better performance
    all_coords = [(pt["location"][0] / 2000.0, pt["location"][1] / 2000.0) for pt in points]
    
    # Process points in batches for better performance
    special_points = []
    regular_points = []
    
    # Track common pins to adjust their positions
    common_pins = []
    
    for i, pt in enumerate(points):
        x, y = all_coords[i]
        cell = pt["cell"]
        
        # Apply cell filter if provided
        if cell_filter_regex and re.search(cell_filter_regex, cell, re.IGNORECASE):
            # Always show highlighted point even if it matches cell filter
            if highlight_points and any(pt['pin'] == hp['pin'] and 
                                      pt['cell'] == hp['cell'] and
                                      pt['location'] == hp['location'] for hp in highlight_points):
                pass  # Don't skip this point
            else:
                continue
            
        marker = "o"
        color_marker = "gray"
        size = 10

        # Mark start (S) and end (E) points.
        if pt is s_point:
            special_points.append((x, y, "S", "navy", pt))
            continue
        elif pt is e_point:
            special_points.append((x, y, "E", "black", pt))
            continue

        # LS/CS markers for clock paths.
        if ls_point is not None and pt["pin"] == ls_point["pin"]:
            if cs_point is not None and pt["pin"] == cs_point["pin"]:
                group_letter = path["path_group"] if path["path_group"] != "N/A" else "G"
                special_points.append((x, y, group_letter, "purple", pt))
            else:
                special_points.append((x, y, "LS", "blue", pt))
            continue

        if cs_point is not None and pt["pin"] == cs_point["pin"]:
            special_points.append((x, y, "CS", "red", pt))
            continue

        # Special text annotations for MUX or LAG cells - only on input pins
        if pt.get("is_input", False):  # Only mark MUX/LAT on input pins
            if re.match(r"MUX", cell):
                special_points.append((x, y, "MUX", "purple", pt))
                continue
            elif re.match(r"LAG", cell):
                special_points.append((x, y, "LAT", "purple", pt))
                continue

        # Mark the last common pin.
        if pt["pin"] == path["last_common_pin"]:
            common_pins.append((x, y, pt))
            continue

        # For points in the data path, apply rules based on cell type and ranking value.
        if pt in data_path:
            if "INV" in cell:
                marker = '^'
                color_marker = 'lightblue'
                size = 15
                if get_rank_val(pt) >= threshold:
                    color_marker = 'red'
            elif "BUF" in cell:
                marker = '^'
                color_marker = 'blue'
                size = 15
                if get_rank_val(pt) >= threshold:
                    color_marker = 'red'
            elif get_rank_val(pt) >= threshold:
                marker = 'D'
                color_marker = 'red'
                size = 15
        else:
            if re.match(r"CKBUF|CKINV", cell):
                marker = '^'
                color_marker = 'black'
                size = 15
                if get_rank_val(pt) >= threshold:
                    color_marker = 'red'
            elif get_rank_val(pt) >= threshold:
                marker = 'D'
                color_marker = 'red'
                size = 15

        # Skip points that are not in the selected path types
        if show_top_ranked_only and get_rank_val(pt) < threshold:
            # Always show highlighted point even if it doesn't meet ranking criteria
            if highlight_points and any(pt['pin'] == hp['pin'] and 
                                      pt['cell'] == hp['cell'] and
                                      pt['location'] == hp['location'] for hp in highlight_points):
                pass  # Don't skip this point
            else:
                continue
            
        if pt in data_path and not show_data_path:
            # Always show highlighted point even if data path is hidden
            if highlight_points and any(pt['pin'] == hp['pin'] and 
                                      pt['cell'] == hp['cell'] and
                                      pt['location'] == hp['location'] for hp in highlight_points):
                pass  # Don't skip this point
            else:
                continue
            
        if pt in clock_path and not show_launch_clock:
            # Always show highlighted point even if launch clock is hidden
            if highlight_points and any(pt['pin'] == hp['pin'] and 
                                      pt['cell'] == hp['cell'] and
                                      pt['location'] == hp['location'] for hp in highlight_points):
                pass  # Don't skip this point
            else:
                continue
            
        if pt in capture_path and not show_capture_clock:
            # Always show highlighted point even if capture clock is hidden
            if highlight_points and any(pt['pin'] == hp['pin'] and 
                                      pt['cell'] == hp['cell'] and
                                      pt['location'] == hp['location'] for hp in highlight_points):
                pass  # Don't skip this point
            else:
                continue

        regular_points.append((x, y, marker, color_marker, size, pt))

    # Draw special points
    for x, y, text, color, pt in special_points:
        if text in ["S", "E"]:
            # Add path value for start and end points
            path_value = pt.get("path_delay", 0.0)
            ax.text(x, y, f"{text}\n{path_value:.4f}", color=color, fontsize=12, ha="center", va="center")
        elif text in ["LS", "CS"]:
            ax.text(x, y, text, color=color, fontsize=20, ha="center", va="center")
        elif text in ["MUX", "LAT"]:
            ax.text(x, y, text, color=color, fontsize=10, ha="center", va="center")
        else:
            group_letter = path["path_group"] if path["path_group"] != "N/A" else "G"
            ax.text(x, y, group_letter, color=color, fontsize=20, ha="center", va="center")
            
        if show_labels:
            ax.annotate(f"{pt['pin']} ({x:.2f}, {y:.2f})", (x, y), fontsize=6)
    
    # Draw common pins with adjusted positions to prevent overlapping
    for i, (x, y, pt) in enumerate(common_pins):
        # Add path value for common pin
        path_value = pt.get("path_delay", 0.0)
        
        # Calculate offset based on index to prevent overlapping
        # For multiple common pins, spread them out vertically
        offset = i * 0.5  # Adjust this value to control spacing
        
        # Draw the star marker
        ax.scatter(x, y, color="darkgreen", s=200, marker="*")
        
        # Add text with offset
        ax.text(x, y + offset, f"C\n{path_value:.4f}", color="red", fontsize=12, ha="center", va="center")
        
        if show_labels:
            ax.annotate(f"{pt['pin']} ({x:.2f}, {y:.2f})", (x, y), fontsize=6)

    # Draw regular points in batches for better performance
    x_coords = [x for x, _, _, _, _, _ in regular_points]
    y_coords = [y for _, y, _, _, _, _ in regular_points]
    markers = [m for _, _, m, _, _, _ in regular_points]
    colors = [c for _, _, _, c, _, _ in regular_points]
    sizes = [s for _, _, _, _, s, _ in regular_points]
    points_data = [p for _, _, _, _, _, p in regular_points]
    
    # Group points by marker and color for more efficient plotting
    marker_color_groups = {}
    for i, (marker, color) in enumerate(zip(markers, colors)):
        key = (marker, color)
        if key not in marker_color_groups:
            marker_color_groups[key] = []
        marker_color_groups[key].append(i)
    
    # Plot each group at once
    for (marker, color), indices in marker_color_groups.items():
        if indices:
            group_x = [x_coords[i] for i in indices]
            group_y = [y_coords[i] for i in indices]
            group_sizes = [sizes[i] for i in indices]
            ax.scatter(group_x, group_y, color=color, s=group_sizes, marker=marker)
            
            # Add labels if needed
            if show_labels:
                for i in indices:
                    x, y = x_coords[i], y_coords[i]
                    pt = points_data[i]
                    ax.annotate(f"{pt['pin']} ({x:.2f}, {y:.2f})", (x, y), fontsize=6)

    # Create legend elements
    # Use actual start and end points from the path data
    actual_start = path.get('actual_start', {}).get('pin', s_point['pin'] if s_point else 'N/A')
    actual_end = path.get('actual_end', {}).get('pin', e_point['pin'] if e_point else 'N/A')
    
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label=f"Start: {actual_start}",
               markerfacecolor='navy', markersize=15),
        Line2D([0], [0], marker='o', color='w', label=f"End: {actual_end}",
               markerfacecolor='black', markersize=15),
        Line2D([0], [0], marker='o', color='w', label=f"Group: {path['path_group']}",
               markerfacecolor='purple', markersize=15),
        Line2D([0], [0], marker='o', color='w', label=f"Slack: {path['slack']}",
               markerfacecolor='gray', markersize=15),
        Line2D([0], [0], marker='o', color='w', label=f"Period: {period:.4f}",
               markerfacecolor='gray', markersize=15),
        Line2D([0], [0], marker='o', color='w', label=f"Skew: {skew:.4f}",
               markerfacecolor='gray', markersize=15),
        Line2D([0], [0], marker='o', color='w', label=f"CRPR: {crpr:.4f}",
               markerfacecolor='gray', markersize=15),
        Line2D([0], [0], marker='o', color='w', label=f"Clock Uncertainty: {clock_uncertainty:.4f}",
               markerfacecolor='gray', markersize=15),
        Line2D([0], [0], marker='o', color='w', label=f"{setup_hold_type.capitalize()} Time: {setup_hold_time:.4f}",
               markerfacecolor='gray', markersize=15),
        Line2D([0], [0], marker='o', color='w', label=f"Data Required Time: {data_required_time:.4f}",
               markerfacecolor='gray', markersize=15),
    ]
    
    # Only add path type legends if they are shown
    if show_launch_clock:
        legend_elements.append(Line2D([0], [0], color='orange', label=f'Launch Clock Path ({path["launch_clock"].rstrip(") ")})'))
    if show_data_path:
        legend_elements.append(Line2D([0], [0], color='blue', label='Data Path'))
    if show_capture_clock:
        legend_elements.append(Line2D([0], [0], color='green', label=f'Capture Clock Path ({path["capture_clock"].rstrip(") ")})'))
    
    # Only show legend if requested
    if show_legend:
        ax.legend(handles=legend_elements, loc='upper right')

    ax.set_title("Timing Path Visualization (Coordinates in µm)")
    ax.set_xlabel("X (µm)")
    ax.set_ylabel("Y (µm)")
    ax.grid(True)
    fig.tight_layout()
    
    # Store the figure reference for highlighting
    # We need to access the viewer instance to store this
    # This will be handled by the calling method
    
    # Highlight the specified point if provided
    if highlight_points:
        # Check if the highlighted points are actually being displayed in this plot
        # by checking if they're in the filtered points that are being plotted
        point_is_displayed = False
        
        # Check if the points exist in the current path's points
        for pt in points:
            if any(pt['pin'] == hp['pin'] and pt['cell'] == hp['cell'] and pt['location'] == hp['location'] for hp in highlight_points):
                point_is_displayed = True
                break
        
        # Only highlight if the points are actually being displayed
        if point_is_displayed:
            print(f"Highlighting points in plot for path {path.get('startpoint', 'N/A')} -> {path.get('endpoint', 'N/A')}")
            for hp in highlight_points:
                x, y = hp['location'][0] / 2000.0, hp['location'][1] / 2000.0
                
                # Use different colors for different selection order
                highlight_colors = [
                    'red',      # First selection
                    'blue',     # Second selection
                    'green',    # Third selection
                    'purple',   # Fourth selection
                    'orange',   # Fifth selection
                    'brown',    # Sixth selection
                    'pink',     # Seventh selection
                    'gray',     # Eighth selection
                ]
                
                highlight_color = highlight_colors[hp['highlight_idx'] % len(highlight_colors)]
                
                # Draw a large circle around the highlighted point
                highlight_circle = plt.Circle((x, y), 0.5, color=highlight_color, fill=False, linewidth=3, alpha=0.8)
                highlight_circle._highlighted_point = True
                ax.add_patch(highlight_circle)
                
                # Add a text annotation
                if self.useShortenedNamesCheck.isChecked():
                    display_name = self.get_shortened_pin_name(hp['pin'])
                else:
                    display_name = hp['pin']
                    
                highlight_text = ax.text(x, y + 0.7, f"{display_name}", 
                                       color=highlight_color, fontsize=10, fontweight='bold',
                                       ha='center', va='bottom',
                                       bbox=dict(boxstyle="round,pad=0.3", facecolor='yellow', alpha=0.8))
                highlight_text._highlighted_point = True
                
                # Add tooltip with full pin name
                highlight_text.set_gid(f"highlight_{hp['pin']}")  # Set a unique ID for the text
                highlight_text._full_pin_name = hp['pin']  # Store the full pin name
        else:
            print(f"Points not found in current plot, skipping highlights")
    
    total_time = time.time() - start_time
    print(f"Visualization complete in {total_time:.2f} seconds. Displaying plot...")
    plt.show()
    
    return fig


def debug_parse_line(line: str, cell_filter_regex: Optional[str] = None):
    """Debug function to parse and display a single line from the timing report.
    
    Args:
        line: The line from the timing report to parse
        cell_filter_regex: Optional regex pattern to filter cell types
    """
    print("\n" + "="*80)
    print("DEBUG - Parsing line:")
    print(line)
    print("="*80)
    
    # Split the line into parts
    parts = line.strip().split()
    
    # Print each part with its index
    print("\nDEBUG - Parts with indices:")
    for i, part in enumerate(parts):
        print(f"  [{i}] {part}")
    
    # Try to identify the pin and cell
    if len(parts) >= 2:
        pin = parts[0]
        cell = parts[1].strip('()')
        rest = ' '.join(parts[2:])
        
        print(f"\nDEBUG - Extracted pin: {pin}")
        print(f"DEBUG - Extracted cell: {cell}")
        print(f"DEBUG - Rest of line: {rest}")
        
        # Check if cell would be filtered
        if cell_filter_regex and re.search(cell_filter_regex, cell, re.IGNORECASE):
            print(f"\nDEBUG - Cell '{cell}' would be filtered by regex: {cell_filter_regex}")
            return
        
        # Parse the point
        point = parse_point(pin, cell, rest, cell_filter_regex)
        
        if point:
            print("\nDEBUG - Successfully parsed point:")
            print(f"  Pin: {point['pin']}")
            print(f"  Cell: {point['cell']}")
            print(f"  Is Input: {point['is_input']}")
            print(f"  DTrans: {point['dtrans']}")
            print(f"  Trans: {point['trans']}")
            print(f"  Derate: {point['derate']}")
            print(f"  Delta: {point['delta']}")
            print(f"  Incr: {point['incr']}")
            print(f"  Path: {point['path_delay']}")
            print(f"  Location: {point['location']}")
        else:
            print("\nDEBUG - Failed to parse point")
    else:
        print("\nDEBUG - Line does not have enough parts to parse")
    
    print("="*80 + "\n")


def main():
    """Main function to run the timing path viewer."""
    start_time = time.time()
    
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", "-f", type=str, help="path to timing report file")
    ap.add_argument("--debug", "-d", type=str, help="debug a specific line from the timing report")
    ap.add_argument("--cell-filter", "-c", type=str, help="regex pattern to filter out specific cell types (e.g., 'CKINV*|INV*|BUF*')")
    args = ap.parse_args()

    # If debug line is provided, parse and display it
    if args.debug:
        debug_parse_line(args.debug, args.cell_filter)
        return

    app = QApplication(sys.argv)
    viewer = TimingPathViewer()
    
    # If a file is provided as a command-line argument, load it
    if args.file:
        with open(args.file, "r") as f:
            print(f"Reading timing report from: {args.file}")
            rpt_text = f.read()
            file_size_mb = len(rpt_text) / (1024 * 1024)
            print(f"File size: {file_size_mb:.2f} MB")
        
        print("Starting to parse timing paths...")
        paths = parse_timing_paths(rpt_text, args.cell_filter)
        if not paths:
            print("No timing paths found. Is this a physical timing report?")
            return

        print(f"Found {len(paths)} timing paths.")
        viewer.paths = paths
        viewer.update_path_list()
        
        # Set the cell filter in the GUI if provided
        if args.cell_filter:
            viewer.cellFilterInput.setText(args.cell_filter)
    
    viewer.resize(1000, 600)
    viewer.show()
    
    total_time = time.time() - start_time
    print(f"Total startup time: {total_time:.2f} seconds")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
