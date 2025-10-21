"""Main GUI dashboard for Hawkeye

DEBUG MODE:
-----------
To enable debug output for troubleshooting:
1. Set DEBUG_MODE = True (around line 55)
2. Restart the application
3. Debug messages will appear in console with categories:
   - [DEBUG:UI] - User interface interactions
   - [DEBUG:DISCOVERY] - Run discovery operations
   - [DEBUG:ANALYSIS] - Data analysis operations
   - [DEBUG:TABLE] - Table creation operations
   - [DEBUG:CHART] - Chart creation operations
   - [DEBUG:FILTER] - Filter operations

Default: DEBUG_MODE = False (production mode)
"""

import os
import sys
import csv
import io
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Set, Optional
from collections import Counter
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence

from ..core.constants import Columns, StatusValues, Colors
from ..core.analyzer import HawkeyeAnalyzer, ARCHIVE_AVAILABLE
from ..core.config import get_all_configured_jobs_and_tasks
from .workers import BackgroundWorker

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout,
        QHBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton,
        QLabel, QComboBox, QFrame, QGroupBox, QTextEdit,
        QTabWidget, QSplitter, QFileDialog, QMessageBox,
        QScrollArea, QStatusBar, QHeaderView, QDialog,
        QCheckBox, QDialogButtonBox, QMenu, QProgressBar,
        QStyledItemDelegate, QLineEdit, QCompleter,
        QStyleOptionViewItem, QStyle, QApplication  # ADD THESE

    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QStringListModel
    from PyQt5.QtGui import QFont, QColor, QPalette, QClipboard
    GUI_AVAILABLE = True
except ImportError:
    print("Warning: PyQt5 not available. Using console mode only.")
    GUI_AVAILABLE = False
    QMainWindow = object
    QLineEdit = object

# Import matplotlib for charting
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available. Chart functionality will be disabled.")

# ============================================================================
# DEBUG MODE CONFIGURATION
# ============================================================================
# Set DEBUG_MODE = True to enable debug output for troubleshooting
# Set DEBUG_MODE = False for production use (default)
DEBUG_MODE = False

def debug_print(message: str, category: str = ""):
    """Print debug message if DEBUG_MODE is enabled

    Args:
        message: The debug message to print
        category: Optional category for filtering (e.g., "FILTER", "CHART", "TABLE")
    """
    if DEBUG_MODE:
        if category:
            print(f"[DEBUG:{category}] {message}")
        else:
            print(f"[DEBUG] {message}")

# ============================================================================


if GUI_AVAILABLE:

    class RightAlignDelegate(QStyledItemDelegate):
        """Custom delegate to show text from the right when column is narrow"""

        def paint(self, painter, option, index):
            """Paint cell with right-aligned text and left ellipsis"""

            painter.save()

            # Get the item's data
            text = index.data(Qt.DisplayRole)

            # STEP 1: Paint the full background (selection, alternating rows, etc.)
            opt = QStyleOptionViewItem(option)
            self.initStyleOption(opt, index)
            opt.text = ""  # Clear text to only paint background

            # CRITICAL: For first column, ensure no decoration space
            if index.column() == 0:
                opt.decorationSize = QSize(0, 0)  # No decoration space
                opt.features &= ~QStyleOptionViewItem.HasDecoration  # No decoration flag

            style = opt.widget.style() if opt.widget else QApplication.style()
            style.drawControl(style.CE_ItemViewItem, opt, painter, opt.widget)

            # STEP 2: Determine text color based on state
            if option.state & QStyle.State_Selected:
                color_group = QPalette.Active if option.state & QStyle.State_Active else QPalette.Inactive
                text_color = option.palette.color(color_group, QPalette.HighlightedText)
            else:
                text_color = index.data(Qt.ForegroundRole)
                if text_color is None:
                    text_color = option.palette.color(QPalette.Active, QPalette.Text)
                elif not isinstance(text_color, QColor):
                    text_color = QColor(text_color)

            painter.setPen(text_color)

            # STEP 3: Paint text with padding
            if text and str(text).strip():
                # SPECIAL HANDLING: First column gets minimal left padding
                if index.column() == 0:
                    text_margin_left = 4  # Minimal left padding for first column
                    text_margin_right = 4
                else:
                    text_margin_left = 4
                    text_margin_right = 4

                text_rect = option.rect.adjusted(text_margin_left, 0, -text_margin_right, 0)

                # Get font metrics
                font_metrics = painter.fontMetrics()

                # Calculate available width for text
                available_width = text_rect.width()

                # Elide text from left if too long
                elided_text = font_metrics.elidedText(
                    str(text),
                    Qt.ElideLeft,
                    available_width
                )

                # Draw the text
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, elided_text)

            painter.restore()

        def sizeHint(self, option, index):
            """Return the size hint for the item"""
            hint = super().sizeHint(option, index)

            # For first column, ensure no extra space for tree decoration
            if index.column() == 0:
                # Remove any indentation from size hint
                pass

            return hint

    class HawkeyeDashboard(QMainWindow):
        """PyQt5 GUI Dashboard for CASINO Hawkeye Analysis"""

        def __init__(self, analyzer: HawkeyeAnalyzer, runs_data: Dict[str, Any]):
            super().__init__()

            self.analyzer = analyzer
            self.runs_data = runs_data
            self.all_keywords = self.collect_all_keywords()
            self.initializing = True
            self.table_focused_mode = False
            self.path_columns_hidden = False
            self.user_hidden_columns = set()

           # ADD THIS: Track hide data state (0=show all, 1=hide invalid, 2=hide invalid+zero)
            self.hide_data_state = 0  # 0=show all, 1=hide invalid, 2=hide invalid+zero
            self.hide_data_hidden_columns = set()  # Columns hidden by hide invalid/zero
            self.hide_data_hidden_rows = set()     # Row indices hidden by hide invalid/zero

            # History storage
            self.keyword_filter_history = []
            self.keyword_visibility_history = []
            self.max_history_size = 20

            self.keyword_column_width_presets = [ 60, 80, 100, 'autofit']
            self.keyword_column_width_index = 2  # Start with 100 (index 2)

            # Chart settings storage (ADD THIS)
            self.chart_settings = {
                'chart_type': 'Line Chart',
                'x_axis_index': Columns.RUN_VERSION,
                'y_axis_indices': [],
                'title': 'CASINO Hawkeye Analysis',
                'width': '12',
                'height': '8',
                'title_font': '16',
                'label_font': '12',
                'legend_font': '10',
                'show_grid': True,
                'show_legend': True,
                'tight_layout': True
            }
            self.path_components = self.extract_path_components()

            # Window tracking to prevent garbage collection
            self.chart_windows = []
            self.table_windows = []

            # Setup window
            self.setWindowTitle(f"CASINO Hawkeye Analysis Explorer - "
                              f"{self.analyzer.config.get('project', {}).get('name', 'Project Analysis')}")
            self.setGeometry(100, 100, 1800, 900)
            self.setMinimumSize(1400, 600)

            self.create_widgets()
            self.populate_tree_with_discovery()

            # Enable mouse tracking for hover detection
            self.table.setMouseTracking(True)
            self.table.viewport().setMouseTracking(True)

            # Store the item under cursor
            self.hovered_item = None
            self.hovered_column = -1
            self.hovered_header = None  # ADD THIS for header tracking

            # Store LAST VALID hover state (persists during keyboard input)
            self.last_hovered_item = None
            self.last_hovered_column = -1
            self.last_hovered_header = None  # ADD THIS

        def cycle_keyword_column_width(self):
            """Cycle through keyword column width presets (60 ? 80 ? 100? Autofit ? 40...)"""
            # Advance to next preset
            self.keyword_column_width_index = (self.keyword_column_width_index + 1) % len(self.keyword_column_width_presets)

            # Get new width preset
            width_preset = self.keyword_column_width_presets[self.keyword_column_width_index]

            # Count visible keyword columns
            headers = self.generate_dynamic_headers()
            path_column_count = Columns.PATH_COLUMN_COUNT
            visible_keyword_cols = 0

            for col_index in range(path_column_count, len(headers)):
                if not self.table.isColumnHidden(col_index):
                    visible_keyword_cols += 1

            if width_preset == 'autofit':
                # Autofit mode: use minimum width with auto-expansion
                self.set_keyword_column_widths(min_width=60, fixed_width=False)

                # Update button text
                self.keyword_width_btn.setText(f"Keyword Width: Autofit")

                # Update status
                self.status_bar.showMessage(
                    f"Keyword columns set to Autofit mode (minimum 60px, expands for content) "
                    f"({visible_keyword_cols} visible keyword columns)"
                )
                debug_print(f"Keyword columns set to Autofit mode", "UI")

            else:
                # Fixed width mode: force exact width
                self.set_keyword_column_widths(min_width=width_preset, fixed_width=True)

                # Update button text
                self.keyword_width_btn.setText(f"Keyword Width: {width_preset}px")

                # Update status
                self.status_bar.showMessage(
                    f"Keyword columns fixed to {width_preset}px width "
                    f"({visible_keyword_cols} visible keyword columns)"
                )
                debug_print(f"Keyword columns fixed to {width_preset}px width", "UI")


        def set_keyword_column_widths(self, min_width: int = 80, fixed_width: bool = False) -> None:
            """Set width for keyword columns

            Args:
                min_width: Width in pixels for keyword columns (default: 80)
                fixed_width: If True, force exact width. If False, use as minimum (default: False)
            """
            headers = self.generate_dynamic_headers()
            path_column_count = Columns.PATH_COLUMN_COUNT

            if fixed_width:
                # FIXED WIDTH MODE: Force exact width for keyword columns
                for col_index in range(self.table.columnCount()):
                    if col_index >= path_column_count:
                        # Force fixed width for keyword columns
                        self.table.setColumnWidth(col_index, min_width)
                    else:
                        # Path columns: auto-fit with padding
                        self.table.resizeColumnToContents(col_index)
                        current_width = self.table.columnWidth(col_index)
                        self.table.setColumnWidth(col_index, current_width + 20)
            else:
                # MINIMUM WIDTH MODE: Auto-fit with minimum enforcement
                for col_index in range(self.table.columnCount()):
                    self.table.resizeColumnToContents(col_index)
                    current_width = self.table.columnWidth(col_index)

                    # Apply minimum width for keyword columns only
                    if col_index >= path_column_count:
                        # Ensure keyword columns are at least min_width pixels
                        new_width = max(current_width + 20, min_width)
                        self.table.setColumnWidth(col_index, new_width)
                    else:
                        # Path columns just get padding
                        self.table.setColumnWidth(col_index, current_width + 20)

        def collect_all_keywords(self) -> List[str]:
            """Collect all unique keywords from configuration and existing runs"""
            keywords = set()

            # From configuration (base keywords only, not dynamic_table_row or sta_pt)
            if hasattr(self.analyzer, 'config') and 'tasks' in self.analyzer.config:
                for task_name, task_config in self.analyzer.config['tasks'].items():
                    # SKIP sta_pt task - keywords will be generated on-demand
                    if task_name == 'sta_pt':
                        continue

                    if task_name == 'custom_extraction':
                        continue

                    for keyword_config in task_config.get('keywords', []):
                        keyword_name = keyword_config['name']
                        keyword_type = keyword_config.get('type', 'string')

                        if keyword_type == 'dynamic_table_row':
                            # Skip - will be collected from actual data
                            pass
                        elif keyword_type == 'multiple_values':
                            pair_value = keyword_config.get('pair_value', '')
                            if pair_value:
                                value_names = pair_value.split()
                                for value_name in value_names:
                                    individual_keyword = f"{keyword_name}_{value_name}"
                                    keywords.add(individual_keyword)
                            else:
                                keywords.add(keyword_name)
                        else:
                            keywords.add(keyword_name)

            # **CRITICAL: Collect from actual run data (includes dynamic_table_row and sta_pt keywords)**
            for run_path, run_data in self.runs_data.items():
                if 'jobs' in run_data:
                    for job_name, job_data in run_data['jobs'].items():
                        for task_name, task_data in job_data.get('tasks', {}).items():
                            for keyword_name in task_data.get('keywords', {}).keys():
                                keywords.add(keyword_name)
                elif 'tasks' in run_data:
                    for task_name, task_data in run_data.get('tasks', {}).items():
                        for keyword_name in task_data.get('keywords', {}).keys():
                            keywords.add(keyword_name)

            return sorted(list(keywords))

        def generate_dynamic_headers(self) -> List[str]:
            """Generate dynamic table headers based on configuration and discovered keywords"""
            path_headers = [
                "Base Dir", "Top Name", "User", "Block", "DK Ver/Tag",
                "Run Version", "Job", "Task", "Status"
            ]

            keyword_headers = []

            # First, collect configured keywords
            if hasattr(self.analyzer, 'config') and 'tasks' in self.analyzer.config:
                for task_name, task_config in self.analyzer.config['tasks'].items():
                    if task_name == 'custom_extraction':
                        continue

                    for keyword_config in task_config.get('keywords', []):
                        keyword_name = keyword_config['name']
                        keyword_type = keyword_config.get('type', 'string')

                        if keyword_type == 'dynamic_table_row':
                            # For dynamic_table_row, skip - will be discovered from data
                            pass
                        elif keyword_type == 'multiple_values':
                            pair_value = keyword_config.get('pair_value', '')
                            if pair_value:
                                value_names = pair_value.split()
                                for value_name in value_names:
                                    individual_header = f"{keyword_name}-{value_name}"
                                    if individual_header not in keyword_headers:
                                        keyword_headers.append(individual_header)
                            else:
                                if keyword_name not in keyword_headers:
                                    keyword_headers.append(keyword_name)
                        else:
                            if keyword_name not in keyword_headers:
                                keyword_headers.append(keyword_name)

            # Second, discover dynamic keywords from actual run data
            discovered_keywords = set()
            for run_path, run_data in self.runs_data.items():
                # Handle both formats
                if 'jobs' in run_data:
                    for job_name, job_data in run_data['jobs'].items():
                        for task_name, task_data in job_data.get('tasks', {}).items():
                            for keyword_name in task_data.get('keywords', {}).keys():
                                discovered_keywords.add(keyword_name)
                elif 'tasks' in run_data:
                    for task_name, task_data in run_data.get('tasks', {}).items():
                        for keyword_name in task_data.get('keywords', {}).keys():
                            discovered_keywords.add(keyword_name)

            # Add discovered keywords that aren't in configured keywords
            # Convert keyword_name format to header format (underscore to dash)
            configured_keyword_names = set()
            for header in keyword_headers:
                # Convert header format back to keyword format for comparison
                keyword_format = header.replace('-', '_')
                configured_keyword_names.add(keyword_format)

            for discovered_keyword in sorted(discovered_keywords):
                if discovered_keyword not in configured_keyword_names:
                    # Check if this is a dynamic_table_row generated keyword
                    # Format: base_name_column (e.g., s_wns_all, s_tns_reg2reg)
                    # Convert to header format: base_name-column
                    header_format = discovered_keyword.replace('_', '-', 1)  # Replace first underscore
                    # Then replace remaining underscores with dashes for multi-word columns
                    parts = discovered_keyword.split('_')
                    if len(parts) >= 2:
                        # Reconstruct as base_name-column
                        base_parts = []
                        col_part = parts[-1]
                        base_parts = parts[:-1]
                        base_name = '_'.join(base_parts)
                        header_format = f"{base_name}-{col_part}"
                    else:
                        header_format = discovered_keyword

                    if header_format not in keyword_headers:
                        keyword_headers.append(header_format)

            all_headers = path_headers + keyword_headers
            return all_headers

        def create_widgets(self):
            """Create the GUI widgets"""
            central_widget = QWidget()
            self.setCentralWidget(central_widget)

            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(10, 10, 10, 10)

            # Title
            title_label = QLabel("CASINO Hawkeye Analysis Explorer")
            title_font = QFont("Terminus", 16)
            title_font.setBold(True)
            title_label.setFont(title_font)
            title_label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(title_label)

            # Control buttons frame
            button_frame = QFrame()
            button_layout = QHBoxLayout(button_frame)

            # Check Status button - REMOVE .setShortcut()
            check_status_btn = QPushButton("Check Status (^S)")
            check_status_btn.clicked.connect(self.check_status_simple)
            # check_status_btn.setShortcut("^S")  # REMOVE THIS LINE
            check_status_btn.setToolTip("Check file status of selected runs (^S)")
            check_status_btn.setStyleSheet(f"background-color: {Colors.BLUE_GROTTO}; color: black; padding: 2px;")
            check_status_btn.setFocusPolicy(Qt.NoFocus)  # ? ADD THIS
            button_layout.addWidget(check_status_btn)

            # Gather Selected button - REMOVE .setShortcut()
            gather_btn = QPushButton("Gather Selected (^G)")
            gather_btn.clicked.connect(self.gather_selected_runs)
            # gather_btn.setShortcut("^G")  # REMOVE THIS LINE
            gather_btn.setToolTip("Analyze selected tasks (^G)")
            gather_btn.setStyleSheet(f"background-color: {Colors.ROYAL_BLUE}; color: white; padding: 2px;")
            gather_btn.setFocusPolicy(Qt.NoFocus)  # ? ADD THIS
            button_layout.addWidget(gather_btn)

            # Refresh Analysis button - REMOVE .setShortcut()
            refresh_btn = QPushButton("Refresh Analysis (^R)")
            refresh_btn.clicked.connect(self.refresh_analysis)
            # refresh_btn.setShortcut("^R")  # REMOVE THIS LINE
            refresh_btn.setToolTip("Refresh the run list (^R)")
            refresh_btn.setStyleSheet(f"background-color: {Colors.FOREST_GREEN}; color: white; padding: 2px;")
            button_layout.addWidget(refresh_btn)

            # Create Chart/Table button
            if MATPLOTLIB_AVAILABLE:
                chart_table_btn = QPushButton("Create Chart/Table")
                chart_table_btn.clicked.connect(lambda: self.show_chart_dialog(self.table))
                chart_table_btn.setStyleSheet(f"background-color: {Colors.SCARLET}; color: white; padding: 2px;")
                chart_table_btn.setToolTip("Create charts and tables from selected data")
                button_layout.addWidget(chart_table_btn)

            # Export CSV button
            export_csv_btn = QPushButton("Export CSV")
            export_csv_btn.clicked.connect(self.export_table_to_csv)
            export_csv_btn.setStyleSheet(f"background-color: {Colors.MISTY_BLUE}; color: black; padding: 2px;")
            button_layout.addWidget(export_csv_btn)

            # Export HTML button
            export_html_btn = QPushButton("Export HTML")
            export_html_btn.clicked.connect(self.export_table_to_html)
            export_html_btn.setStyleSheet(f"background-color: {Colors.MISTY_BLUE}; color: black; padding: 2px;")
            button_layout.addWidget(export_html_btn)

            # Archive Analysis button
            archive_btn = QPushButton("Archive Analysis")
            archive_btn.clicked.connect(self.archive_analysis_data)

            if ARCHIVE_AVAILABLE:
                archive_btn.setStyleSheet(f"background-color: {Colors.TEAL}; color: black; padding: 2px;")
                archive_btn.setToolTip("Archive current analysis data to database")
            else:
                archive_btn.setStyleSheet(f"background-color: {Colors.PEWTER}; color: gray; padding: 2px;")
                archive_btn.setToolTip("Archive functionality not available - hawkeye_archive.py not found")
                archive_btn.setEnabled(False)
            button_layout.addWidget(archive_btn)

            # Clear Selection button
            clear_selection_btn = QPushButton("Clear Selection (ESC)")
            clear_selection_btn.clicked.connect(self.clear_selection)
            clear_selection_btn.setStyleSheet(f"background-color: {Colors.PURPLE_HAZE}; color: black; padding: 2px;")
            button_layout.addWidget(clear_selection_btn)

            # Cycling Hide Data button (Show All ? Hide Invalid ? Hide Invalid+Zero ? Show All...)
            self.cycle_hide_btn = QPushButton("Hide Invalid Data (^I)")
            self.cycle_hide_btn.clicked.connect(self.cycle_hide_data)
            self.cycle_hide_btn.setToolTip("Hide invalid/zero data based on currently filtered rows (respects Advanced Filters)")
            self.cycle_hide_btn.setStyleSheet(f"background-color: {Colors.MISTY_BLUE}; color: black; padding: 2px;")
            button_layout.addWidget(self.cycle_hide_btn)

            # Toggle Path Columns button
            self.toggle_path_btn = QPushButton("Hide Path Columns (^P)")
            self.toggle_path_btn.clicked.connect(self.toggle_path_columns)
            self.toggle_path_btn.setStyleSheet(f"background-color: {Colors.MISTY_BLUE}; color: black; padding: 2px;")
            button_layout.addWidget(self.toggle_path_btn)

            # Show Hidden Columns button
            self.show_hidden_columns_btn = QPushButton("Show Hidden Columns")
            self.show_hidden_columns_btn.clicked.connect(self.show_hidden_columns)
            self.show_hidden_columns_btn.setStyleSheet(f"background-color: {Colors.TEAL}; color: black; padding: 2px;")
            self.show_hidden_columns_btn.setEnabled(False)
            button_layout.addWidget(self.show_hidden_columns_btn)

            # ADD THIS: Keyword Column Width button
            self.keyword_width_btn = QPushButton("Keyword Width: 80px")
            self.keyword_width_btn.clicked.connect(self.cycle_keyword_column_width)
            self.keyword_width_btn.setToolTip("Cycle keyword column widths (40px ? 60px ? 80px ? Autofit ? 40px...)")
            self.keyword_width_btn.setStyleSheet(f"background-color: {Colors.SAGE_GREEN}; color: black; padding: 2px;")
            button_layout.addWidget(self.keyword_width_btn)

            button_layout.addStretch()
            main_layout.addWidget(button_frame)

            # Enhanced Filter frame
            filter_group = QGroupBox("Advanced Filters")
            filter_layout = QVBoxLayout(filter_group)

            # Filter Row 1: Base Dir, Top Name, User, Block, DK Ver/Tag
            filter_row1 = QHBoxLayout()

            # Base Dir filter
            filter_row1.addWidget(QLabel("Base Dir:"))
            self.base_dir_combo = QComboBox()
            self.base_dir_combo.addItems(["all"] + self.path_components.get('base_dir', []))
            self.base_dir_combo.setEditable(True)
            self.base_dir_combo.setInsertPolicy(QComboBox.NoInsert)
            self.base_dir_combo.currentTextChanged.connect(self.apply_filters)
            filter_row1.addWidget(self.base_dir_combo)

            self.base_dir_multi_btn = QPushButton("...")
            self.base_dir_multi_btn.setMaximumWidth(30)
            self.base_dir_multi_btn.clicked.connect(lambda: self.show_multi_select_dialog('base_dir', 'Base Dir'))
            filter_row1.addWidget(self.base_dir_multi_btn)

            # Top Name filter
            filter_row1.addWidget(QLabel("Top Name:"))
            self.top_name_combo = QComboBox()
            self.top_name_combo.addItems(["all"] + self.path_components.get('top_name', []))
            self.top_name_combo.setEditable(True)
            self.top_name_combo.setInsertPolicy(QComboBox.NoInsert)
            self.top_name_combo.currentTextChanged.connect(self.apply_filters)
            filter_row1.addWidget(self.top_name_combo)

            self.top_name_multi_btn = QPushButton("...")
            self.top_name_multi_btn.setMaximumWidth(30)
            self.top_name_multi_btn.clicked.connect(lambda: self.show_multi_select_dialog('top_name', 'Top Name'))
            filter_row1.addWidget(self.top_name_multi_btn)

            # User filter
            filter_row1.addWidget(QLabel("User:"))
            self.user_combo = QComboBox()
            self.user_combo.addItems(["all"] + self.path_components.get('user', []))
            self.user_combo.setEditable(True)
            self.user_combo.setInsertPolicy(QComboBox.NoInsert)
            self.user_combo.currentTextChanged.connect(self.apply_filters)
            filter_row1.addWidget(self.user_combo)

            self.user_multi_btn = QPushButton("...")
            self.user_multi_btn.setMaximumWidth(30)
            self.user_multi_btn.clicked.connect(lambda: self.show_multi_select_dialog('user', 'User'))
            filter_row1.addWidget(self.user_multi_btn)

            # Block filter
            filter_row1.addWidget(QLabel("Block:"))
            self.block_combo = QComboBox()
            self.block_combo.addItems(["all"] + self.path_components.get('block', []))
            self.block_combo.setEditable(True)
            self.block_combo.setInsertPolicy(QComboBox.NoInsert)
            self.block_combo.currentTextChanged.connect(self.apply_filters)
            filter_row1.addWidget(self.block_combo)

            self.block_multi_btn = QPushButton("...")
            self.block_multi_btn.setMaximumWidth(30)
            self.block_multi_btn.clicked.connect(lambda: self.show_multi_select_dialog('block', 'Block'))
            filter_row1.addWidget(self.block_multi_btn)

            # DK Ver/Tag filter
            filter_row1.addWidget(QLabel("DK Ver/Tag:"))
            self.dk_ver_tag_combo = QComboBox()
            self.dk_ver_tag_combo.addItems(["all"] + self.path_components.get('dk_ver_tag', []))
            self.dk_ver_tag_combo.setEditable(True)
            self.dk_ver_tag_combo.setInsertPolicy(QComboBox.NoInsert)
            self.dk_ver_tag_combo.currentTextChanged.connect(self.apply_filters)
            filter_row1.addWidget(self.dk_ver_tag_combo)

            self.dk_ver_tag_multi_btn = QPushButton("...")
            self.dk_ver_tag_multi_btn.setMaximumWidth(30)
            self.dk_ver_tag_multi_btn.clicked.connect(lambda: self.show_multi_select_dialog('dk_ver_tag', 'DK Ver/Tag'))
            filter_row1.addWidget(self.dk_ver_tag_multi_btn)

            # Hide invalid checkbox
            self.hide_invalid_status_cb = QCheckBox("Hide 'No Job Dir' & 'Not Configured' & 'No Files'")
            self.hide_invalid_status_cb.setChecked(True)
            self.hide_invalid_status_cb.stateChanged.connect(self.apply_filters)
            filter_row1.addWidget(self.hide_invalid_status_cb)

            filter_row1.addStretch()
            filter_layout.addLayout(filter_row1)

            # Filter Row 2: Run Version, Job, Task, Status
            filter_row2 = QHBoxLayout()

            # Run Version filter
            filter_row2.addWidget(QLabel("Run Version:"))
            self.run_version_combo = QComboBox()
            self.run_version_combo.addItems(["all"] + self.path_components.get('run_version', []))
            self.run_version_combo.setEditable(True)
            self.run_version_combo.setInsertPolicy(QComboBox.NoInsert)
            self.run_version_combo.currentTextChanged.connect(self.apply_filters)
            filter_row2.addWidget(self.run_version_combo)

            self.run_version_multi_btn = QPushButton("...")
            self.run_version_multi_btn.setMaximumWidth(30)
            self.run_version_multi_btn.clicked.connect(lambda: self.show_multi_select_dialog('run_version', 'Run Version'))
            filter_row2.addWidget(self.run_version_multi_btn)

            # Job filter
            filter_row2.addWidget(QLabel("Job:"))
            self.job_combo = QComboBox()
            self.job_combo.addItems(["all"])
            self.job_combo.setEditable(True)
            self.job_combo.setInsertPolicy(QComboBox.NoInsert)
            self.job_combo.currentTextChanged.connect(self.apply_filters)
            filter_row2.addWidget(self.job_combo)

            self.job_multi_btn = QPushButton("...")
            self.job_multi_btn.setMaximumWidth(30)
            self.job_multi_btn.clicked.connect(lambda: self.show_multi_select_dialog('job', 'Job'))
            filter_row2.addWidget(self.job_multi_btn)

            # Task filter
            filter_row2.addWidget(QLabel("Task:"))
            self.task_combo = QComboBox()
            tasks = ["all"] + list(self.analyzer.config.get('tasks', {}).keys())
            self.task_combo.addItems(tasks)
            self.task_combo.setEditable(True)
            self.task_combo.setInsertPolicy(QComboBox.NoInsert)
            self.task_combo.currentTextChanged.connect(self.apply_filters)
            filter_row2.addWidget(self.task_combo)

            self.task_multi_btn = QPushButton("...")
            self.task_multi_btn.setMaximumWidth(30)
            self.task_multi_btn.clicked.connect(lambda: self.show_multi_select_dialog('task', 'Task'))
            filter_row2.addWidget(self.task_multi_btn)

            # Status filter
            filter_row2.addWidget(QLabel("Status:"))
            self.status_combo = QComboBox()
            self.status_combo.addItems(["all", StatusValues.COMPLETED, StatusValues.READY,
                                       StatusValues.NO_FILES, StatusValues.NO_JOB_DIR,
                                       StatusValues.NOT_CONFIGURED, StatusValues.FAILED])
            self.status_combo.setEditable(True)
            self.status_combo.setInsertPolicy(QComboBox.NoInsert)
            self.status_combo.setMinimumWidth(150)
            self.status_combo.currentTextChanged.connect(self.apply_filters)
            filter_row2.addWidget(self.status_combo)

            self.status_multi_btn = QPushButton("...")
            self.status_multi_btn.setMaximumWidth(30)
            self.status_multi_btn.clicked.connect(lambda: self.show_multi_select_dialog('status', 'Status'))
            filter_row2.addWidget(self.status_multi_btn)

            # Clear filters button
            clear_btn = QPushButton("Clear All Filters")
            clear_btn.clicked.connect(self.clear_filters)
            filter_row2.addWidget(clear_btn)

            filter_row2.addStretch()
            filter_layout.addLayout(filter_row2)

            # Filter Row 3
            filter_row3 = QHBoxLayout()

            # Keyword filter
            filter_row3.addWidget(QLabel("Keyword Filter:"))
            self.keyword_filter_input = QLineEdit()
            self.keyword_filter_input.setPlaceholderText("e.g., 'error', 'warning', '>100'")
            self.keyword_filter_input.setClearButtonEnabled(True)  # Add native X clear button
            self.keyword_filter_input.textChanged.connect(self.apply_filters)
            self.keyword_filter_input.textChanged.connect(self.save_keyword_filter_history)
            self.setup_keyword_filter_autocomplete()
            filter_row3.addWidget(self.keyword_filter_input)

            # Keyword column visibility
            filter_row3.addWidget(QLabel("Show Keyword Columns:"))
            self.keyword_visibility_input = QLineEdit()
            self.keyword_visibility_input.setPlaceholderText("e.g., 'hotspot,power' for OR, 'hotspot+power' for AND")
            self.keyword_visibility_input.setClearButtonEnabled(True)  # Add native X clear button
            self.keyword_visibility_input.textChanged.connect(self.apply_keyword_column_visibility)
            self.keyword_visibility_input.textChanged.connect(self.save_keyword_visibility_history)
            self.setup_keyword_visibility_autocomplete()
            filter_row3.addWidget(self.keyword_visibility_input)

            filter_row3.addStretch()
            filter_layout.addLayout(filter_row3)

            main_layout.addWidget(filter_group)

            # Table widget
            self.table = QTreeWidget()
            headers = self.generate_dynamic_headers()
            self.table.setHeaderLabels(headers)
            self.table.setAlternatingRowColors(True)

            # CRITICAL: Remove tree decoration from first column
            self.table.setRootIsDecorated(False)  # No expand/collapse indicators
            self.table.setIndentation(0)  # No indentation for hierarchy

            self.table.itemDoubleClicked.connect(self.on_item_double_click)
            self.table.setColumnWidth(Columns.BASE_DIR, 100)
            self.table.setColumnWidth(Columns.TOP_NAME, 100)
            self.table.setColumnWidth(Columns.USER, 100)
            self.table.setColumnWidth(Columns.BLOCK, 120)
            self.table.setColumnWidth(Columns.DK_VER_TAG, 200)
            self.table.setColumnWidth(Columns.RUN_VERSION, 150)
            self.table.setColumnWidth(Columns.JOB, 100)
            self.table.setColumnWidth(Columns.TASK, 100)
            self.table.setColumnWidth(Columns.STATUS, 80)
            self.table.setSelectionMode(QTreeWidget.ExtendedSelection)

            # ADD: Ensure selection behavior is correct
            self.table.setSelectionBehavior(QTreeWidget.SelectRows)  # Select entire rows

            # Set custom delegate for right-aligned display
            self.right_align_delegate = RightAlignDelegate()
            # ADD THIS: Set custom delegate for right-aligned display
            self.right_align_delegate = RightAlignDelegate()
            for col in range(100):  # Apply to first 100 columns
                self.table.setItemDelegateForColumn(col, self.right_align_delegate)

            self.table.setStyleSheet("""
                QTreeWidget {
                    outline: none;
                    border: 1px solid #ccc;
                    gridline-color: transparent;
                    show-decoration-selected: 1;
                }

                QTreeWidget::item {
                    padding: 0px;
                    margin: 0px;
                    border: none;
                    outline: none;
                }

                QTreeWidget::branch {
                    /* Remove tree branch decorations completely */
                    background: transparent;
                    border: none;
                    margin: 0px;
                    padding: 0px;
                }

                QTreeWidget::item:selected {
                    background-color: #3daee9;
                    color: white;
                    border: none;
                }

                QTreeWidget::item:selected:!active {
                    background-color: #85c1e9;
                    color: white;
                    border: none;
                }

                QTreeWidget::item:hover:!selected {
                    background-color: #e8f4f8;
                }

                QTreeWidget::item:hover {
                    border: none;
                }
            """)

            # Install event filter to track mouse position
            self.table.viewport().installEventFilter(self)

            # ALSO install event filter on header to track header hover
            self.table.header().installEventFilter(self)  # ADD THIS

            # Enable context menus
            self.table.setContextMenuPolicy(Qt.CustomContextMenu)
            self.table.customContextMenuRequested.connect(self.show_context_menu)

            self.table.header().setContextMenuPolicy(Qt.CustomContextMenu)
            self.table.header().customContextMenuRequested.connect(self.show_column_context_menu)

            # Enable sorting
            self.table.header().setSectionsClickable(True)
            self.table.header().sectionClicked.connect(self.on_header_clicked)

            self.current_sort_column = -1
            self.sort_ascending = True

            # ESC and Space key handling for table
            original_keyPressEvent = self.table.keyPressEvent

            def custom_keyPressEvent(event):
                if event.key() == Qt.Key_Escape:
                    self.table.clearSelection()
                    event.accept()
                elif event.key() == Qt.Key_Space:
                    # Handle Space key for selection toggle with 3-level priority
                    item_to_toggle = None

                    # Priority 1: Use hovered item (under mouse cursor)
                    if self.hovered_item:
                        item_to_toggle = self.hovered_item
                    # Priority 2: Use current item (keyboard navigation or default)
                    elif self.table.currentItem():
                        item_to_toggle = self.table.currentItem()
                    # Priority 3: Use first visible item as fallback
                    else:
                        for i in range(self.table.topLevelItemCount()):
                            item = self.table.topLevelItem(i)
                            if item and not item.isHidden():
                                item_to_toggle = item
                                self.table.setCurrentItem(item)
                                break

                    # Toggle selection if we found an item
                    if item_to_toggle:
                        is_selected = item_to_toggle.isSelected()
                        item_to_toggle.setSelected(not is_selected)

                        # Get row info for status message
                        row_index = self.table.indexOfTopLevelItem(item_to_toggle)
                        new_state = "selected" if not is_selected else "deselected"

                        self.status_bar.showMessage(f"Row {row_index} {new_state} (Space)")
                    else:
                        self.status_bar.showMessage("No items available to select")

                    event.accept()
                else:
                    original_keyPressEvent(event)

            self.table.keyPressEvent = custom_keyPressEvent

            self.table.setFocusPolicy(Qt.StrongFocus)
            self.table.setFocus()

            main_layout.addWidget(self.table)

            # Progress bar
            self.progress_bar = QProgressBar()
            self.progress_bar.setMaximumHeight(15)
            self.progress_bar.setTextVisible(True)
            self.progress_bar.setAlignment(Qt.AlignCenter)
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    text-align: center;
                    font-size: 10px;
                    background-color: #f0f0f0;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 2px;
                }
            """)

            # ADD THIS LINE - Add progress bar to main layout BEFORE status bar
            main_layout.addWidget(self.progress_bar)

            # CRITICAL: Hide by default
            self.progress_bar.hide()

            # Status bar
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)

            # Setup APPLICATION-WIDE keyboard shortcuts
            # These work regardless of which widget has focus
            from PyQt5.QtWidgets import QShortcut
            from PyQt5.QtGui import QKeySequence

            # Create shortcuts on the MAIN WINDOW (self), not individual widgets
            # Use Qt.ApplicationShortcut context to work everywhere

            # ^S for Check Status
            self.shortcut_check = QShortcut(QKeySequence("Ctrl+S"), self)
            self.shortcut_check.setContext(Qt.ApplicationShortcut)
            self.shortcut_check.activated.connect(self.check_status_simple)

            # ^G for Gather Selected
            self.shortcut_gather = QShortcut(QKeySequence("Ctrl+G"), self)
            self.shortcut_gather.setContext(Qt.ApplicationShortcut)
            self.shortcut_gather.activated.connect(self.gather_selected_runs)

            # ^R for Refresh
            self.shortcut_refresh = QShortcut(QKeySequence("Ctrl+R"), self)
            self.shortcut_refresh.setContext(Qt.ApplicationShortcut)
            self.shortcut_refresh.activated.connect(self.refresh_analysis)

            # ^W for Keyword Width cycling
            self.shortcut_width = QShortcut(QKeySequence("Ctrl+W"), self)
            self.shortcut_width.setContext(Qt.ApplicationShortcut)
            self.shortcut_width.activated.connect(self.cycle_keyword_column_width)


        def eventFilter(self, source, event):
            """Filter events to track mouse hover position"""
            if source == self.table.viewport():
                if event.type() == event.MouseMove:
                    # Get item under mouse cursor
                    pos = event.pos()
                    item = self.table.itemAt(pos)

                    if item and not item.isHidden():
                        # CRITICAL: Account for horizontal scroll offset
                        # Get the horizontal scrollbar value
                        h_scroll_offset = self.table.horizontalScrollBar().value()

                        # Adjust mouse X position by scroll offset
                        x_pos = pos.x() + h_scroll_offset

                        column = -1
                        x_offset = 0

                        # Iterate through ALL columns (including hidden ones)
                        for i in range(self.table.columnCount()):
                            if self.table.isColumnHidden(i):
                                # Skip hidden columns - they don't take up visual space
                                continue

                            col_width = self.table.columnWidth(i)

                            # Check if adjusted mouse X position is within this column's bounds
                            if x_offset <= x_pos < x_offset + col_width:
                                column = i  # This is the LOGICAL column index
                                break

                            # Add this column's width to the offset
                            x_offset += col_width

                        # Update hover state
                        self.hovered_item = item
                        self.hovered_column = column

                        # Show tooltip with what will be copied
                        if column >= 0:
                            cell_value = item.text(column)
                            headers = self.generate_dynamic_headers()
                            column_name = headers[column] if column < len(headers) else f"Column {column}"

                            # Get row index for tooltip
                            row_index = self.table.indexOfTopLevelItem(item)

                            # Set tooltip to show what Ctrl+C and Ctrl+Shift+C will copy
                            tooltip = f"[Ctrl+C to copy cell value]\n[Ctrl+Shift+C to copy column name]\n"
                            tooltip += f"Row {row_index} | Column: '{column_name}'\nValue: {cell_value}"

                            # DEBUG: Show scroll offset and logical column
                                  #f"Row {row_index}, Logical Column {column} ({column_name}): {cell_value}")

                            self.table.viewport().setToolTip(tooltip)
                    else:
                        # Mouse is over empty space or hidden item
                        self.hovered_item = None
                        self.hovered_column = -1
                        self.table.viewport().setToolTip("")

                elif event.type() == event.Leave:
                    # Mouse left the table viewport
                    self.hovered_item = None
                    self.hovered_column = -1
                    self.table.viewport().setToolTip("")

            return super().eventFilter(source, event)

        def populate_tree_with_discovery(self):
            """Populate table with discovered runs (fast run-level view)"""
            try:
                self.table.clear()
                self.clear_user_hidden_columns()
            except Exception as e:
                pass

            headers = ["Base Dir", "Top Name", "User", "Block", "DK Ver/Tag", "Run Version"]
            self.table.setHeaderLabels(headers)

            # FAST: detailed_check=False means no job/task checking
            import time
            start_time = time.time()
            debug_print("Starting fast discovery (no job/task checking)...", "DISCOVERY")

            runs = self.analyzer.discover_runs(detailed_check=False)

            elapsed = time.time() - start_time
            debug_print(f"Discovery completed in {elapsed:.2f} seconds", "DISCOVERY")

            # FAST: Build path components from runs WITHOUT filesystem access
            self.update_path_components_from_runs_fast(runs)

            # FAST: Populate table with run-level data only
            for i, run in enumerate(runs):
                clean_path = self.clean_path(run['full_path'])
                path_parts = Path(clean_path).parts

                if len(path_parts) >= 7:
                    base_dir = path_parts[-7] if len(path_parts) >= 7 else "unknown"
                    top_name = path_parts[-6] if len(path_parts) >= 6 else "unknown"
                    user = path_parts[-5].replace('works_', '') if len(path_parts) >= 5 else "unknown"
                    block = path_parts[-4] if len(path_parts) >= 4 else "unknown"
                    dk_ver_tag = path_parts[-3] if len(path_parts) >= 3 else "unknown"
                    run_version = path_parts[-1]
                else:
                    base_dir = run.get('base_dir', 'unknown')
                    top_name = run.get('top_name', 'unknown')
                    user = run.get('user', 'unknown')
                    block = run.get('block', 'unknown')
                    dk_ver_tag = run.get('dk_ver_tag', 'unknown')
                    run_version = run.get('run_version', 'unknown')

                row_data = [base_dir, top_name, user, block, dk_ver_tag, run_version]

                item = QTreeWidgetItem(self.table, row_data)
                item.setData(0, Qt.UserRole, run['full_path'])
                item.setData(0, Qt.UserRole + 3, run.get('jobs_and_tasks', {}))

                tooltip_parts = [
                    f"Run Version: {run_version}",
                    f"Path: {run['full_path']}",
                    "",
                    "Actions:",
                    "- Use filters to narrow down run versions",
                    "- Click 'Check Status' to see job/task breakdown",
                    "- Click 'Gather Selected' to analyze specific tasks"
                ]

                for col in range(len(row_data)):
                    item.setToolTip(col, "\n".join(tooltip_parts))

#           # Auto-fit columns
#           for i in range(self.table.columnCount()):
#               self.table.resizeColumnToContents(i)
#               current_width = self.table.columnWidth(i)
#               self.table.setColumnWidth(i, current_width + 20)

            # Auto-fit columns with minimum width for keyword columns
            self.set_keyword_column_widths(min_width=80, fixed_width=False)

            total_runs = len(runs)
            elapsed_str = f"{elapsed:.2f}s" if elapsed < 60 else f"{int(elapsed/60)}m {int(elapsed%60)}s"

            self.status_bar.showMessage(
                f"Discovery completed in {elapsed_str}: {total_runs} run versions found. "
                f"Use 'Check Status' for job/task details.")

            self.update_job_dropdown()
            self.update_task_dropdown()
            self.update_status_dropdown()

            # CRITICAL: Check if there's an active keyword visibility filter and apply it
            # Do NOT unconditionally show all columns
            keyword_visibility_text = self.keyword_visibility_input.text().strip()
            if keyword_visibility_text:
                # User has active filter - apply it
                self.apply_keyword_column_visibility()
            else:
                # No filter - show all columns
                self.show_all_keyword_columns()

            self.initializing = False

            # CRITICAL: Set first item as current AND ensure table has focus
            if self.table.topLevelItemCount() > 0:
                first_item = self.table.topLevelItem(0)
                if first_item:
                    self.table.setCurrentItem(first_item)
                    # Don't select it, just set as current so Space key has a target
                    first_item.setSelected(False)

                    # CRITICAL: Ensure table has keyboard focus
                    self.table.setFocus(Qt.OtherFocusReason)

            else:
                pass

        def update_path_components_from_runs_fast(self, runs: List[Dict[str, Any]]):
            """Update path components from discovered runs WITHOUT filesystem access"""
            components = {
                'base_dir': set(),
                'top_name': set(),
                'user': set(),
                'block': set(),
                'dk_ver_tag': set(),
                'run_version': set()
            }

            # FAST: Just extract from run dictionaries (no filesystem access)
            for run in runs:
                components['base_dir'].add(run.get('base_dir', 'unknown'))
                components['top_name'].add(run.get('top_name', 'unknown'))
                components['user'].add(run.get('user', 'unknown'))
                components['block'].add(run.get('block', 'unknown'))
                components['dk_ver_tag'].add(run.get('dk_ver_tag', 'unknown'))
                components['run_version'].add(run.get('run_version', 'unknown'))

            self.path_components = {key: sorted(list(value)) for key, value in components.items()}

            self.update_filter_dropdowns()
            self.show_all_keyword_columns()
            self.update_show_hidden_columns_button_state()

        def extract_path_components(self) -> Dict[str, List[str]]:
            """Extract unique values for each path component from all runs"""
            components = {
                'base_dir': set(),
                'top_name': set(),
                'user': set(),
                'block': set(),
                'dk_ver_tag': set(),
                'run_version': set()
            }

            for run_path in self.runs_data.keys():
                clean_path = self.clean_path(run_path)
                path_parts = Path(clean_path).parts

                if len(path_parts) >= 7:
                    components['base_dir'].add(path_parts[-7] if len(path_parts) >= 7 else "unknown")
                    components['top_name'].add(path_parts[-6] if len(path_parts) >= 6 else "unknown")
                    components['user'].add(path_parts[-5].replace('works_', '') if len(path_parts) >= 5 else "unknown")
                    components['block'].add(path_parts[-4] if len(path_parts) >= 4 else "unknown")
                    components['dk_ver_tag'].add(path_parts[-3] if len(path_parts) >= 3 else "unknown")
                    components['run_version'].add(path_parts[-1])

            return {key: sorted(list(value)) for key, value in components.items()}

        def clean_path(self, path: str) -> str:
            """Clean path by removing ./ patterns"""
            cleaned = path.replace('/./', '/')
            if cleaned.startswith('./'):
                cleaned = cleaned[2:]
            return cleaned

        def update_path_components_from_runs(self, runs: List[Dict[str, Any]]):
            """Update path components from discovered runs for filtering"""
            components = {
                'base_dir': set(),
                'top_name': set(),
                'user': set(),
                'block': set(),
                'dk_ver_tag': set(),
                'run_version': set()
            }

            for run in runs:
                clean_path = self.clean_path(run['full_path'])
                path_parts = Path(clean_path).parts

                if len(path_parts) >= 7:
                    components['base_dir'].add(path_parts[-7] if len(path_parts) >= 7 else "unknown")
                    components['top_name'].add(path_parts[-6] if len(path_parts) >= 6 else "unknown")
                    components['user'].add(path_parts[-5].replace('works_', '') if len(path_parts) >= 5 else "unknown")
                    components['block'].add(path_parts[-4] if len(path_parts) >= 4 else "unknown")
                    components['dk_ver_tag'].add(path_parts[-3] if len(path_parts) >= 3 else "unknown")
                    components['run_version'].add(path_parts[-1])

            self.path_components = {key: sorted(list(value)) for key, value in components.items()}

            self.update_filter_dropdowns()
            self.show_all_keyword_columns()
            self.update_show_hidden_columns_button_state()

        def update_filter_dropdowns(self):
            """Update filter dropdowns with current path components"""
            current_selections = {
                'base_dir': self.base_dir_combo.currentText(),
                'top_name': self.top_name_combo.currentText(),
                'user': self.user_combo.currentText(),
                'block': self.block_combo.currentText(),
                'dk_ver_tag': self.dk_ver_tag_combo.currentText(),
                'run_version': self.run_version_combo.currentText(),
                'job': self.job_combo.currentText()
            }

            self.base_dir_combo.clear()
            self.base_dir_combo.addItems(["all"] + self.path_components.get('base_dir', []))

            self.top_name_combo.clear()
            self.top_name_combo.addItems(["all"] + self.path_components.get('top_name', []))

            self.user_combo.clear()
            self.user_combo.addItems(["all"] + self.path_components.get('user', []))

            self.block_combo.clear()
            self.block_combo.addItems(["all"] + self.path_components.get('block', []))

            self.dk_ver_tag_combo.clear()
            self.dk_ver_tag_combo.addItems(["all"] + self.path_components.get('dk_ver_tag', []))

            self.run_version_combo.clear()
            self.run_version_combo.addItems(["all"] + self.path_components.get('run_version', []))

            self.update_job_dropdown()

            # Restore selections
            for combo_name, selection in current_selections.items():
                if combo_name == 'base_dir':
                    combo = self.base_dir_combo
                elif combo_name == 'top_name':
                    combo = self.top_name_combo
                elif combo_name == 'user':
                    combo = self.user_combo
                elif combo_name == 'job':
                    combo = self.job_combo
                else:
                    combo = getattr(self, f"{combo_name}_combo")
                if selection in [combo.itemText(i) for i in range(combo.count())]:
                    combo.setCurrentText(selection)

        def update_job_dropdown(self):
            """Update Job dropdown with jobs from configuration"""
            current_selection = self.job_combo.currentText()

            self.job_combo.clear()
            job_list = []

            if hasattr(self.analyzer, 'config') and 'jobs' in self.analyzer.config:
                job_list = list(self.analyzer.config['jobs'].keys())

            self.job_combo.addItems(["all"] + sorted(job_list))

            if current_selection in [self.job_combo.itemText(i) for i in range(self.job_combo.count())]:
                self.job_combo.setCurrentText(current_selection)

        def update_task_dropdown(self):
            """Update Task dropdown with tasks from configuration"""
            current_selection = self.task_combo.currentText()

            self.task_combo.clear()
            task_list = []

            if hasattr(self.analyzer, 'config') and 'tasks' in self.analyzer.config:
                task_list = list(self.analyzer.config['tasks'].keys())

            self.task_combo.addItems(["all"] + sorted(task_list))

            if current_selection in [self.task_combo.itemText(i) for i in range(self.task_combo.count())]:
                self.task_combo.setCurrentText(current_selection)

        def update_status_dropdown(self):
            """Update Status dropdown with status values from table"""
            current_selection = self.status_combo.currentText()

            self.status_combo.clear()
            status_list = []

            if self.table.columnCount() > Columns.STATUS:
                table_count = self.table.topLevelItemCount()

                for i in range(table_count):
                    item = self.table.topLevelItem(i)
                    if item:
                        status_text = item.text(Columns.STATUS)
                        if status_text and status_text not in status_list:
                            if status_text.endswith('%'):
                                status_text = StatusValues.COMPLETED
                            elif status_text in ["Ready to Analyze", "Analyzed", "Successfully analyzed"]:
                                status_text = StatusValues.COMPLETED
                            elif status_text in ["No Log Files", "Task Dir Missing", "No Data", "Analysis failed"]:
                                status_text = StatusValues.FAILED
                            elif status_text in ["Not Analyzed", "No files to analyze", "No files found for analysis"]:
                                status_text = StatusValues.NOT_STARTED

                            if status_text not in status_list:
                                status_list.append(status_text)
            else:
                status_list = ["Not Checked", StatusValues.READY, StatusValues.NO_FILES,
                              StatusValues.NO_JOB_DIR, StatusValues.NOT_CONFIGURED,
                              StatusValues.COMPLETED, StatusValues.FAILED]

            self.status_combo.addItems(["all"] + sorted(status_list))

            if current_selection in [self.status_combo.itemText(i) for i in range(self.status_combo.count())]:
                self.status_combo.setCurrentText(current_selection)

        def _apply_filters_preserve_hide_data(self):
            """Apply filters while preserving rows/columns hidden by 'Hide Invalid Data'"""
            if hasattr(self, 'initializing') and self.initializing:
                return

            # Get filter values
            status_filter = self.parse_filter_values(self.status_combo.currentText())
            job_filter = self.parse_filter_values(self.job_combo.currentText())
            task_filter = self.parse_filter_values(self.task_combo.currentText())
            base_dir_filter = self.parse_filter_values(self.base_dir_combo.currentText())
            top_name_filter = self.parse_filter_values(self.top_name_combo.currentText())
            user_filter = self.parse_filter_values(self.user_combo.currentText())
            block_filter = self.parse_filter_values(self.block_combo.currentText())
            dk_ver_tag_filter = self.parse_filter_values(self.dk_ver_tag_combo.currentText())
            run_version_filter = self.parse_filter_values(self.run_version_combo.currentText())

            keyword_filter_text = self.keyword_filter_input.text().strip()

            # CRITICAL: Only show items that are NOT in hide_data_hidden_rows
            for i in range(self.table.topLevelItemCount()):
                # Skip rows hidden by "Hide Invalid Data"
                if i in self.hide_data_hidden_rows:
                    continue

                item = self.table.topLevelItem(i)
                item.setHidden(False)  # Unhide for filter evaluation

            # Apply filters
            for i in range(self.table.topLevelItemCount()):
                # Skip rows hidden by "Hide Invalid Data"
                if i in self.hide_data_hidden_rows:
                    continue

                item = self.table.topLevelItem(i)

                run_path = item.data(0, Qt.UserRole)
                if run_path is None:
                    continue

                base_dir = item.text(Columns.BASE_DIR)
                top_name = item.text(Columns.TOP_NAME)
                user = item.text(Columns.USER)
                block = item.text(Columns.BLOCK)
                dk_ver_tag = item.text(Columns.DK_VER_TAG)
                run_version = item.text(Columns.RUN_VERSION)
                job_name = item.text(Columns.JOB)
                task_name = item.text(Columns.TASK)
                status_text = item.text(Columns.STATUS)

                should_hide = False

                if not self.matches_filter(status_text, status_filter):
                    should_hide = True
                elif (self.hide_invalid_status_cb.isChecked() and
                      status_text in [StatusValues.NO_JOB_DIR, StatusValues.NOT_CONFIGURED, StatusValues.NO_FILES]):
                    should_hide = True
                elif not self.matches_filter(job_name, job_filter):
                    should_hide = True
                elif not self.matches_filter(task_name, task_filter):
                    should_hide = True
                elif not self.matches_filter(base_dir, base_dir_filter):
                    should_hide = True
                elif not self.matches_filter(top_name, top_name_filter):
                    should_hide = True
                elif not self.matches_filter(user, user_filter):
                    should_hide = True
                elif not self.matches_filter(block, block_filter):
                    should_hide = True
                elif not self.matches_filter(dk_ver_tag, dk_ver_tag_filter):
                    should_hide = True
                elif not self.matches_filter(run_version, run_version_filter):
                    should_hide = True
                elif keyword_filter_text and not self.matches_keyword_filter(item, keyword_filter_text):
                    should_hide = True

                item.setHidden(should_hide)

            visible_items = sum(1 for i in range(self.table.topLevelItemCount())
                              if not self.table.topLevelItem(i).isHidden())
            active_filters = self.get_active_filters_text()
            self.status_bar.showMessage(f"Showing {visible_items} of {self.table.topLevelItemCount()} rows | {active_filters}")

        def apply_filters(self):
            """Apply filters to the table with support for multiple selections"""
            if hasattr(self, 'initializing') and self.initializing:
                return

            # Get filter values
            status_filter = self.parse_filter_values(self.status_combo.currentText())
            job_filter = self.parse_filter_values(self.job_combo.currentText())
            task_filter = self.parse_filter_values(self.task_combo.currentText())
            base_dir_filter = self.parse_filter_values(self.base_dir_combo.currentText())
            top_name_filter = self.parse_filter_values(self.top_name_combo.currentText())
            user_filter = self.parse_filter_values(self.user_combo.currentText())
            block_filter = self.parse_filter_values(self.block_combo.currentText())
            dk_ver_tag_filter = self.parse_filter_values(self.dk_ver_tag_combo.currentText())
            run_version_filter = self.parse_filter_values(self.run_version_combo.currentText())

            keyword_filter_text = self.keyword_filter_input.text().strip()

            # Show all items first
            for i in range(self.table.topLevelItemCount()):
                self.table.topLevelItem(i).setHidden(False)

            # Apply filters
            for i in range(self.table.topLevelItemCount()):
                item = self.table.topLevelItem(i)

                run_path = item.data(0, Qt.UserRole)
                if run_path is None:
                    continue

                base_dir = item.text(Columns.BASE_DIR)
                top_name = item.text(Columns.TOP_NAME)
                user = item.text(Columns.USER)
                block = item.text(Columns.BLOCK)
                dk_ver_tag = item.text(Columns.DK_VER_TAG)
                run_version = item.text(Columns.RUN_VERSION)
                job_name = item.text(Columns.JOB)
                task_name = item.text(Columns.TASK)
                status_text = item.text(Columns.STATUS)

                should_hide = False

                if not self.matches_filter(status_text, status_filter):
                    should_hide = True
                elif (self.hide_invalid_status_cb.isChecked() and
                      status_text in [StatusValues.NO_JOB_DIR, StatusValues.NOT_CONFIGURED, StatusValues.NO_FILES]):
                    should_hide = True
                elif not self.matches_filter(job_name, job_filter):
                    should_hide = True
                elif not self.matches_filter(task_name, task_filter):
                    should_hide = True
                elif not self.matches_filter(base_dir, base_dir_filter):
                    should_hide = True
                elif not self.matches_filter(top_name, top_name_filter):
                    should_hide = True
                elif not self.matches_filter(user, user_filter):
                    should_hide = True
                elif not self.matches_filter(block, block_filter):
                    should_hide = True
                elif not self.matches_filter(dk_ver_tag, dk_ver_tag_filter):
                    should_hide = True
                elif not self.matches_filter(run_version, run_version_filter):
                    should_hide = True
                elif keyword_filter_text and not self.matches_keyword_filter(item, keyword_filter_text):
                    should_hide = True

                item.setHidden(should_hide)

            visible_items = sum(1 for i in range(self.table.topLevelItemCount())
                              if not self.table.topLevelItem(i).isHidden())
            active_filters = self.get_active_filters_text()
            self.status_bar.showMessage(f"Showing {visible_items} of {self.table.topLevelItemCount()} rows | {active_filters}")

            self.update_show_hidden_columns_button_state()

        def parse_filter_values(self, filter_text: str) -> List[str]:
            """Parse filter text to support multiple comma-separated values"""
            if not filter_text or filter_text.strip() == "all":
                return ["all"]

            values = [v.strip() for v in filter_text.split(',') if v.strip()]
            return values if values else ["all"]

        def matches_filter(self, value: str, filter_values: List[str]) -> bool:
            """Check if value matches any of the filter values"""
            if "all" in filter_values:
                return True
            return value in filter_values

        def matches_keyword_filter(self, item, keyword_filter_text: str) -> bool:
            """Check if any visible keyword column matches the keyword filter"""
            if not keyword_filter_text:
                return True

            headers = self.generate_dynamic_headers()
            path_column_count = Columns.PATH_COLUMN_COUNT

            for col in range(path_column_count, item.columnCount()):
                if col < len(headers) and not self.table.isColumnHidden(col):
                    keyword_value = item.text(col)
                    if self.matches_keyword_value(keyword_value, keyword_filter_text):
                        return True

            return False

        def matches_keyword_value(self, value: str, filter_text: str) -> bool:
            """Check if keyword value matches filter text with operators"""
            if not value or not filter_text:
                return False

            if value in ["-", "N/A", "n/a", "NA", "na", "", "null", "NULL", "None", "none"]:
                return False

            if filter_text.startswith(('>', '<', '>=', '<=')):
                try:
                    if filter_text.startswith('>='):
                        operator = '>='
                        filter_value = float(filter_text[2:])
                    elif filter_text.startswith('<='):
                        operator = '<='
                        filter_value = float(filter_text[2:])
                    elif filter_text.startswith('>'):
                        operator = '>'
                        filter_value = float(filter_text[1:])
                    elif filter_text.startswith('<'):
                        operator = '<'
                        filter_value = float(filter_text[1:])
                    else:
                        return False

                    cell_value = float(value.replace(',', '').replace('$', '').replace('%', ''))

                    if operator == '>':
                        return cell_value > filter_value
                    elif operator == '<':
                        return cell_value < filter_value
                    elif operator == '>=':
                        return cell_value >= filter_value
                    elif operator == '<=':
                        return cell_value <= filter_value

                except (ValueError, TypeError):
                    return filter_text.lower() in value.lower()
            else:
                return filter_text.lower() in value.lower()

        def get_active_filters_text(self) -> str:
            """Get text describing active filters"""
            active_filters = []
            if self.status_combo.currentText() != "all":
                active_filters.append(f"Status: {self.status_combo.currentText()}")
            if self.job_combo.currentText() != "all":
                active_filters.append(f"Job: {self.job_combo.currentText()}")
            if self.task_combo.currentText() != "all":
                active_filters.append(f"Task: {self.task_combo.currentText()}")
            if self.base_dir_combo.currentText() != "all":
                active_filters.append(f"Base Dir: {self.base_dir_combo.currentText()}")
            if self.top_name_combo.currentText() != "all":
                active_filters.append(f"Top Name: {self.top_name_combo.currentText()}")
            if self.user_combo.currentText() != "all":
                active_filters.append(f"User: {self.user_combo.currentText()}")
            if self.block_combo.currentText() != "all":
                active_filters.append(f"Block: {self.block_combo.currentText()}")
            if self.dk_ver_tag_combo.currentText() != "all":
                active_filters.append(f"DK Ver/Tag: {self.dk_ver_tag_combo.currentText()}")
            if self.run_version_combo.currentText() != "all":
                active_filters.append(f"Run Version: {self.run_version_combo.currentText()}")

            keyword_filter_text = self.keyword_filter_input.text().strip()
            if keyword_filter_text:
                active_filters.append(f"Keyword: {keyword_filter_text}")

            keyword_visibility_text = self.keyword_visibility_input.text().strip()
            if keyword_visibility_text:
                active_filters.append(f"Show Columns: {keyword_visibility_text}")

            return ", ".join(active_filters) if active_filters else "None"

        def clear_filters(self):
            """Clear all filters"""
            self.status_combo.setCurrentText("all")
            self.job_combo.setCurrentText("all")
            self.task_combo.setCurrentText("all")
            self.base_dir_combo.setCurrentText("all")
            self.top_name_combo.setCurrentText("all")
            self.user_combo.setCurrentText("all")
            self.block_combo.setCurrentText("all")
            self.dk_ver_tag_combo.setCurrentText("all")
            self.run_version_combo.setCurrentText("all")
            self.keyword_filter_input.clear()
            self.keyword_visibility_input.clear()
            self.show_all_keyword_columns()
            self.apply_filters()

        def apply_keyword_column_visibility(self):
            """Apply keyword column visibility based on input"""
            visibility_text = self.keyword_visibility_input.text().strip()

            if not visibility_text:
                self.show_all_keyword_columns()
            else:
                self.show_specific_keyword_columns(visibility_text)

        def show_all_keyword_columns(self):
            """Show all keyword columns (except those hidden by hide data state)"""
            headers = self.generate_dynamic_headers()
            path_column_count = Columns.PATH_COLUMN_COUNT

            for col in range(path_column_count, len(headers)):
                # CRITICAL: Don't show columns that are hidden by "Hide Invalid Data"
                if col not in self.hide_data_hidden_columns:
                    self.table.setColumnHidden(col, False)
                # If column is in hide_data_hidden_columns, keep it hidden

        def show_specific_keyword_columns(self, filter_text: str):
            """Show only keyword columns that match the filter text with AND/OR logic, hide others

            IMPORTANT: Respects hide_data_hidden_columns - won't show columns hidden by "Hide Invalid Data"
            """
            headers = self.generate_dynamic_headers()
            path_column_count = Columns.PATH_COLUMN_COUNT

            # First, hide all keyword columns
            for col in range(path_column_count, len(headers)):
                self.table.setColumnHidden(col, True)

            # Parse filter text for mixed AND/OR logic
            # Split by comma first (OR groups)
            or_groups = [group.strip() for group in filter_text.split(',') if group.strip()]

            for col in range(path_column_count, len(headers)):
                if col < len(headers):
                    column_name = headers[col].lower()

                    # Check if column matches ANY of the OR groups
                    matches_any_group = False

                    for or_group in or_groups:
                        # Within each OR group, check for AND logic ('+' separator)
                        if '+' in or_group:
                            # AND logic: column must contain ALL terms in this group
                            and_terms = [term.strip().lower() for term in or_group.split('+') if term.strip()]
                            if all(term in column_name for term in and_terms):
                                matches_any_group = True
                                break
                        else:
                            # Simple term: column must contain this term
                            if or_group.lower() in column_name:
                                matches_any_group = True
                                break

                    # Show column if it matches any OR group
                    # BUT CRITICAL: Don't show if it's hidden by "Hide Invalid Data"
                    if matches_any_group:
                        if col not in self.hide_data_hidden_columns:
                            self.table.setColumnHidden(col, False)
                        # else: keep it hidden (it's in hide_data_hidden_columns)

        def clear_keyword_visibility_filter(self):
            """Clear keyword column visibility filter"""
            self.keyword_visibility_input.clear()
            self.show_all_keyword_columns()


        def check_status_simple(self):
            """Expand to detailed view with Job/Task breakdown and file status checking"""
            selected_items = self.table.selectedItems()

            if not selected_items:
                QMessageBox.information(self, "No Selection",
                                      "Please select one or more runs to check status for.\n\n"
                                      "This will expand the view to show Job/Task breakdown with file status.")
                return

            # Extract unique run paths from selected items
            selected_runs = []
            for item in selected_items:
                if not item.text(0).startswith("---"):
                    run_path = item.data(0, Qt.UserRole)
                    if run_path and run_path not in selected_runs:
                        selected_runs.append(run_path)

            if not selected_runs:
                QMessageBox.information(self, "No Valid Runs Selected",
                                      "Please select valid run items to check status for.")
                return

            # Setup DETERMINATE progress bar (shows actual progress)
            total_runs = len(selected_runs)
            self.progress_bar.setRange(0, total_runs)  # CRITICAL: Set range for determinate mode
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat(f"Initializing... (0/{total_runs})")
            self.progress_bar.show()
            QApplication.processEvents()

            try:
                # Clear table and prepare for detailed view
                self.table.clear()
                self.clear_user_hidden_columns()

                headers = self.generate_dynamic_headers()
                self.table.setHeaderLabels(headers)

                # Process each run with progress updates
                for run_index, run_path in enumerate(selected_runs, start=1):
                    # Update progress bar
                    self.progress_bar.setValue(run_index - 1)

                    # Extract run name for display
                    run_name = run_path.split('/')[-1] if '/' in run_path else run_path

                    # Update progress bar text
                    self.progress_bar.setFormat(f"Checking status: {run_index}/{total_runs} - {run_name}")

                    # Also update status bar for more detail
                    self.status_bar.showMessage(f"Processing run {run_index}/{total_runs}: {run_name}")

                    # Force GUI update
                    QApplication.processEvents()

                    # Process this run
                    self.populate_detailed_view_for_single_run(run_path, headers)

                # Final progress update
                self.progress_bar.setValue(total_runs)
                self.progress_bar.setFormat(f"Completed: {total_runs} runs")
                QApplication.processEvents()

                # Set column widths
                self.set_column_widths_for_detailed_view()

                # Update dropdowns
                self.update_job_dropdown()
                self.update_task_dropdown()
                self.update_status_dropdown()

                # ADD THIS: Re-apply filters after status check
                self.reapply_filters_after_table_update()

                # ADD THIS: Set first item as current for Space key
                if self.table.topLevelItemCount() > 0:
                    first_item = self.table.topLevelItem(0)
                    if first_item:
                        self.table.setCurrentItem(first_item)
                        first_item.setSelected(False)


                # Calculate total tasks checked
                total_tasks = sum(len(get_all_configured_jobs_and_tasks(self.analyzer.config).get(job, []))
                                 for job in get_all_configured_jobs_and_tasks(self.analyzer.config).keys()) * total_runs

                self.status_bar.showMessage(
                    f"Status check completed for {total_runs} runs ({total_tasks} tasks total). "
                    f"Use 'Gather Selected' to analyze specific tasks.")

            except Exception as e:
                print(f"ERROR: Status check failed: {e}")
                import traceback
                traceback.print_exc()
                self.status_bar.showMessage(f"Status check failed: {str(e)}")
                QMessageBox.critical(self, "Error", f"Status check failed:\n{str(e)}")
            finally:
                # Hide progress bar
                self.progress_bar.hide()
                QApplication.processEvents()

        def populate_detailed_view_for_single_run(self, run_path: str, headers: List[str]):
            """Populate detailed view for a single run

            Args:
                run_path: Path to the run directory
                headers: List of column headers
            """
            # Find run data
            run_data = None
            runs = self.analyzer.discover_runs()
            for run in runs:
                if run['full_path'] == run_path:
                    run_data = run
                    break

            if not run_data:
                print(f"WARNING: Run data not found for {run_path}")
                return

            # Extract path components
            clean_path = self.clean_path(run_data['full_path'])
            path_parts = Path(clean_path).parts

            if len(path_parts) >= 7:
                base_dir = path_parts[-7] if len(path_parts) >= 7 else "unknown"
                top_name = path_parts[-6] if len(path_parts) >= 6 else "unknown"
                user = path_parts[-5].replace('works_', '') if len(path_parts) >= 5 else "unknown"
                block = path_parts[-4] if len(path_parts) >= 4 else "unknown"
                dk_ver_tag = path_parts[-3] if len(path_parts) >= 3 else "unknown"
                run_version = path_parts[-1]
            else:
                base_dir = top_name = user = block = dk_ver_tag = run_version = "unknown"

            # Get configured jobs and tasks
            configured_jobs = get_all_configured_jobs_and_tasks(self.analyzer.config)

            # Create table rows for each job/task combination
            for job_name, configured_tasks in configured_jobs.items():
                for task_name in configured_tasks:
                    # Create row data
                    row_data = [""] * len(headers)

                    row_data[Columns.BASE_DIR] = base_dir
                    row_data[Columns.TOP_NAME] = top_name
                    row_data[Columns.USER] = user
                    row_data[Columns.BLOCK] = block
                    row_data[Columns.DK_VER_TAG] = dk_ver_tag
                    row_data[Columns.RUN_VERSION] = run_version
                    row_data[Columns.JOB] = job_name
                    row_data[Columns.TASK] = task_name

                    # Check file status for this task
                    status, tooltip_text = self.check_task_file_status(run_data['full_path'], job_name, task_name)
                    row_data[Columns.STATUS] = status

                    # Initialize keyword columns with "-"
                    for i in range(Columns.PATH_COLUMN_COUNT, len(headers)):
                        row_data[i] = "-"

                    # Create table item
                    item = QTreeWidgetItem(self.table, row_data)
                    item.setData(0, Qt.UserRole, run_data['full_path'])
                    item.setData(0, Qt.UserRole + 1, job_name)
                    item.setData(0, Qt.UserRole + 2, task_name)

                    # Set tooltip for status column
                    item.setToolTip(Columns.STATUS, tooltip_text)

                    # Color the Status column only
                    color = self.get_status_color(status)
                    item.setForeground(Columns.STATUS, color)

                    # Make Status column bold
                    font = item.font(Columns.STATUS)
                    font.setBold(True)
                    item.setFont(Columns.STATUS, font)

            # Set first item as current so Space key works immediately
            if self.table.topLevelItemCount() > 0:
                first_item = self.table.topLevelItem(0)
                if first_item:
                    self.table.setCurrentItem(first_item)
                    first_item.setSelected(False)


        def populate_detailed_view_with_status_check(self, selected_run_paths: List[str]):
            """Populate table with detailed Job/Task view with file status checking"""
            self.table.clear()
            self.clear_user_hidden_columns()

            headers = self.generate_dynamic_headers()
            self.table.setHeaderLabels(headers)

            for run_path in selected_run_paths:
                run_data = None
                runs = self.analyzer.discover_runs()
                for run in runs:
                    if run['full_path'] == run_path:
                        run_data = run
                        break

                if not run_data:
                    continue

                clean_path = self.clean_path(run_data['full_path'])
                path_parts = Path(clean_path).parts
                if len(path_parts) >= 7:
                    base_dir = path_parts[-7] if len(path_parts) >= 7 else "unknown"
                    top_name = path_parts[-6] if len(path_parts) >= 6 else "unknown"
                    user = path_parts[-5].replace('works_', '') if len(path_parts) >= 5 else "unknown"
                    block = path_parts[-4] if len(path_parts) >= 4 else "unknown"
                    dk_ver_tag = path_parts[-3] if len(path_parts) >= 3 else "unknown"
                    run_version = path_parts[-1]
                else:
                    base_dir = top_name = user = block = dk_ver_tag = run_version = "unknown"

                jobs_and_tasks = run_data.get('jobs_and_tasks', {})
                configured_jobs = get_all_configured_jobs_and_tasks(self.analyzer.config)

                for job_name, configured_tasks in configured_jobs.items():
                    for task_name in configured_tasks:
                        row_data = [""] * len(headers)

                        row_data[Columns.BASE_DIR] = base_dir
                        row_data[Columns.TOP_NAME] = top_name
                        row_data[Columns.USER] = user
                        row_data[Columns.BLOCK] = block
                        row_data[Columns.DK_VER_TAG] = dk_ver_tag
                        row_data[Columns.RUN_VERSION] = run_version
                        row_data[Columns.JOB] = job_name
                        row_data[Columns.TASK] = task_name

                        status, tooltip_text = self.check_task_file_status(run_data['full_path'], job_name, task_name)
                        row_data[Columns.STATUS] = status

                        for i in range(Columns.PATH_COLUMN_COUNT, len(headers)):
                            row_data[i] = "-"

                        item = QTreeWidgetItem(self.table, row_data)
                        item.setData(0, Qt.UserRole, run_data['full_path'])
                        item.setData(0, Qt.UserRole + 1, job_name)
                        item.setData(0, Qt.UserRole + 2, task_name)

                        item.setToolTip(Columns.STATUS, tooltip_text)

                        # CRITICAL: Only color the Status column to preserve selection visibility
                        color = self.get_status_color(status)
                        item.setForeground(Columns.STATUS, color)

                        # Make Status column bold for emphasis
                        font = item.font(Columns.STATUS)
                        font.setBold(True)
                        item.setFont(Columns.STATUS, font)

            self.set_column_widths_for_detailed_view()

            self.update_job_dropdown()
            self.update_task_dropdown()
            self.update_status_dropdown()

            total_tasks = sum(len(tasks) for tasks in configured_jobs.values()) * len(selected_run_paths)
            self.status_bar.showMessage(
                f"Detailed view: {len(selected_run_paths)} selected runs with {total_tasks} tasks. "
                f"Status updated based on file checking. Use 'Gather Selected' to analyze specific tasks.")

        def check_task_file_status(self, run_path: str, job_name: str, task_name: str) -> tuple:
            """Check file status for a specific task

            Args:
                run_path: Path to run directory
                job_name: Name of job
                task_name: Name of task

            Returns:
                Tuple of (status, tooltip_text)
            """
            job_path = os.path.join(run_path, job_name)
            if not os.path.exists(job_path):
                return StatusValues.NO_JOB_DIR, "Details: Job directory does not exist"

            if task_name not in self.analyzer.config.get('tasks', {}):
                return StatusValues.NOT_CONFIGURED, "Details: Task not configured in vista_casino.yaml"

            task_config = self.analyzer.config['tasks'][task_name]
            task_log_files = task_config.get('log_files', [])
            task_report_files = task_config.get('report_files', [])

            log_files = []
            report_files = []

            import glob

            # SPECIAL HANDLING FOR STA_PT TASK (has {mode}/{corner} placeholders)
            if task_name == 'sta_pt' and 'sta_config' in self.analyzer.config:
                sta_config = self.analyzer.config['sta_config']
                modes = sta_config.get('modes', [])
                corners = sta_config.get('corners', [])


                # Expand placeholders for all mode/corner combinations
                for mode in modes:
                    for corner in corners:
                        # Expand log file patterns
                        for log_pattern in task_log_files:
                            expanded_pattern = log_pattern.replace('{mode}', mode).replace('{corner}', corner)
                            search_path = os.path.join(job_path, expanded_pattern)

                            for file_path in glob.glob(search_path):
                                if os.path.exists(file_path):
                                    log_files.append(file_path)

                        # Expand report file patterns
                        for report_pattern in task_report_files:
                            expanded_pattern = report_pattern.replace('{mode}', mode).replace('{corner}', corner)
                            search_path = os.path.join(job_path, expanded_pattern)

                            for file_path in glob.glob(search_path):
                                if os.path.exists(file_path):
                                    report_files.append(file_path)
            else:
                # STANDARD HANDLING FOR NON-STA TASKS
                for log_pattern in task_log_files:
                    search_path = log_pattern if log_pattern.startswith('/') else os.path.join(job_path, log_pattern)
                    for file_path in glob.glob(search_path):
                        if os.path.exists(file_path):
                            log_files.append(file_path)

                for report_pattern in task_report_files:
                    search_path = report_pattern if report_pattern.startswith('/') else os.path.join(job_path, report_pattern)
                    for file_path in glob.glob(search_path):
                        if os.path.exists(file_path):
                            report_files.append(file_path)

            # Determine status based on found files
            if log_files or report_files:
                status = StatusValues.READY
                tooltip = f"Details: Job directory exists with log/report files\nFiles found: {len(log_files)} logs, {len(report_files)} reports"

                # Show sample files
                if log_files:
                    sample_logs = [os.path.basename(f) for f in log_files[:3]]
                    tooltip += f"\nSample logs: {', '.join(sample_logs)}"
                    if len(log_files) > 3:
                        tooltip += f" ... and {len(log_files) - 3} more"

                if report_files:
                    sample_reports = [os.path.basename(f) for f in report_files[:3]]
                    tooltip += f"\nSample reports: {', '.join(sample_reports)}"
                    if len(report_files) > 3:
                        tooltip += f" ... and {len(report_files) - 3} more"
            else:
                if task_log_files or task_report_files:
                    status = StatusValues.NO_FILES
                    tooltip = "Details: Job directory exists but expected log/report files not found"
                    if task_log_files:
                        tooltip += f"\nExpected log files: {', '.join(task_log_files)}"
                    if task_report_files:
                        tooltip += f"\nExpected report files: {', '.join(task_report_files)}"
                else:
                    status = StatusValues.NOT_CONFIGURED
                    tooltip = "Details: Job directory exists but no specific file patterns configured"

            return status, tooltip

        def get_status_color(self, status: str) -> QColor:
            """Get color for status"""
            if status == StatusValues.COMPLETED:
                return QColor(0, 100, 0)
            elif status == StatusValues.READY:
                return QColor(0, 150, 0)
            elif status == StatusValues.NO_FILES:
                return QColor(255, 165, 0)
            elif status == StatusValues.NO_JOB_DIR:
                return QColor(255, 100, 0)
            elif status == StatusValues.NOT_CONFIGURED:
                return QColor(128, 128, 128)
            elif status == StatusValues.FAILED:
                return QColor(255, 0, 0)
            else:
                return QColor(0, 0, 0)

        def set_column_widths_for_detailed_view(self):
            """Set column widths for detailed view"""
            self.table.setColumnWidth(Columns.BASE_DIR, 100)
            self.table.setColumnWidth(Columns.TOP_NAME, 100)
            self.table.setColumnWidth(Columns.USER, 100)
            self.table.setColumnWidth(Columns.BLOCK, 120)
            self.table.setColumnWidth(Columns.DK_VER_TAG, 200)
            self.table.setColumnWidth(Columns.RUN_VERSION, 150)
            self.table.setColumnWidth(Columns.JOB, 100)
            self.table.setColumnWidth(Columns.TASK, 100)
            self.table.setColumnWidth(Columns.STATUS, 80)

        def gather_selected_runs(self):
            """Analyze selected tasks with progress"""
            selected_items = self.table.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "No Selection",
                                  "Please select at least one task row to analyze.\n\n"
                                  "Selection methods:\n"
                                  "- Ctrl+Click: Individual selection\n"
                                  "- Shift+Click: Range selection\n"
                                  "- Space key: Toggle selection\n\n"
                                  "Only selected task(s) will be analyzed.")
                return

            # Group selections
            selected_analysis = {}
            for item in selected_items:
                run_path = item.data(0, Qt.UserRole)
                job_name = item.data(0, Qt.UserRole + 1)
                task_name = item.data(0, Qt.UserRole + 2)
                if run_path and job_name and task_name:
                    if run_path not in selected_analysis:
                        selected_analysis[run_path] = {}
                    if job_name not in selected_analysis[run_path]:
                        selected_analysis[run_path][job_name] = set()
                    selected_analysis[run_path][job_name].add(task_name)

            if not selected_analysis:
                QMessageBox.warning(self, "No Valid Items", "No valid items found in selection.")
                return

            total_tasks = sum(sum(len(tasks) for tasks in jobs.values())
                             for jobs in selected_analysis.values())

            # Configure and show progress bar
            self.progress_bar.setRange(0, total_tasks)
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat(f"Initializing... (0/{total_tasks})")
            self.progress_bar.show()

            # Update immediately
            QApplication.processEvents()

            # Create and start worker
            self.bg_worker = BackgroundWorker(self.analyzer, selected_analysis)
            self.bg_worker.progress_update.connect(self.update_progress)
            self.bg_worker.finished_signal.connect(self.analysis_complete)
            self.bg_worker.start()

        def update_progress(self, current: int, total: int, message: str):
            """Update progress bar"""
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(current)
            self.progress_bar.setFormat(f"{message}: {current}/{total} (%p%)")

            # Force immediate GUI update from worker thread signal
            QApplication.processEvents()

            # Debug output

        def analysis_complete(self, analysis_results: Dict[str, Any]):
            """Handle analysis completion"""
            self.progress_bar.hide()
            self.setEnabled(True)
            QApplication.processEvents()

            if not analysis_results:
                self.status_bar.showMessage("Analysis completed - no results")
                if hasattr(self, 'bg_worker'):
                    self.bg_worker.deleteLater()
                return

            # Update runs data
            self.runs_data.update(analysis_results)

            # **ADD THIS: Regenerate headers after analysis to include new dynamic keywords**
            self.all_keywords = self.collect_all_keywords()
            new_headers = self.generate_dynamic_headers()
            self.table.setHeaderLabels(new_headers)

            # Reconstruct selected analysis structure
            selected_analysis = {}
            for run_path, run_data in analysis_results.items():
                if 'jobs' in run_data:
                    selected_analysis[run_path] = {}
                    for job_name, job_data in run_data['jobs'].items():
                        if 'tasks' in job_data:
                            selected_analysis[run_path][job_name] = set(job_data['tasks'].keys())

            # Update table with results
            self.update_selected_runs_in_table(selected_analysis)

            # Show completion message
            total_tasks = sum(sum(len(tasks) for tasks in jobs.values())
                             for jobs in selected_analysis.values())
            total_runs = len(analysis_results)
            task_text = "task" if total_tasks == 1 else "tasks"
            run_text = "run" if total_runs == 1 else "runs"
            self.status_bar.showMessage(
                f"Analysis completed for {total_tasks} {task_text} across {total_runs} {run_text}.")

            # Clear filters to show results
            self.clear_filters()

            # Clean up worker
            if hasattr(self, 'bg_worker'):
                self.bg_worker.deleteLater()

        def update_selected_runs_in_table(self, selected_analysis: Dict[str, Dict[str, Set[str]]]):
            """Update selected runs in table and focus on selected tasks"""
            debug_print(f"Updating {len(selected_analysis)} selected runs in table", "ANALYSIS")

            # **REGENERATE headers to include new dynamic keywords**
            headers = self.generate_dynamic_headers()
            debug_print(f"Using {len(headers)} headers for table update", "ANALYSIS")

            selected_task_identifiers = set()
            for run_path, jobs in selected_analysis.items():
                for job_name, tasks in jobs.items():
                    for task_name in tasks:
                        selected_task_identifiers.add((run_path, job_name, task_name))


            hidden_count = 0
            shown_count = 0
            for i in range(self.table.topLevelItemCount()):
                item = self.table.topLevelItem(i)
                run_path = item.data(0, Qt.UserRole)
                job_name = item.data(0, Qt.UserRole + 1)
                task_name = item.data(0, Qt.UserRole + 2)

                task_identifier = (run_path, job_name, task_name)
                is_selected_task = task_identifier in selected_task_identifiers


                if is_selected_task:
                    if run_path in self.runs_data:
                        run_data = self.runs_data[run_path]

                        if job_name and task_name:
                            if 'jobs' in run_data and job_name in run_data['jobs']:
                                if task_name in run_data['jobs'][job_name]['tasks']:
                                    task_data = run_data['jobs'][job_name]['tasks'][task_name]
                                else:
                                    continue
                            else:
                                continue
                        else:
                            continue

                        status_text = task_data.get('simplified_status', StatusValues.COMPLETED)
                        item.setText(Columns.STATUS, status_text)

                        # **ENSURE item has enough columns**
                        current_column_count = item.columnCount()
                        if current_column_count < len(headers):
                            # Expand item to match header count
                            for col_idx in range(current_column_count, len(headers)):
                                item.setText(col_idx, "-")

                        # Update keyword columns
                        for i, header in enumerate(headers[Columns.PATH_COLUMN_COUNT:], Columns.PATH_COLUMN_COUNT):
                            if "-" in header:
                                keyword_parts = header.split("-")
                                if len(keyword_parts) >= 2:
                                    base_keyword = keyword_parts[0]
                                    value_suffix = keyword_parts[1]
                                    keyword_name = f"{base_keyword}_{value_suffix}"
                                else:
                                    keyword_name = header
                            else:
                                keyword_name = header

                            value = self.get_keyword_value(task_data, keyword_name, "-")
                            item.setText(i, value)

                            # **DEBUG: Show what we're setting**
                            if value != "-":
                                pass

                        # CRITICAL: Only color the Status column to preserve selection visibility
                        status_text = task_data.get('simplified_status', StatusValues.COMPLETED)
                        if status_text == StatusValues.COMPLETED:
                            color = QColor(0, 100, 0)
                        elif status_text == StatusValues.NOT_STARTED:
                            color = QColor(128, 128, 128)
                        elif status_text == StatusValues.FAILED:
                            color = QColor(255, 0, 0)
                        else:
                            color = QColor(0, 0, 0)

                        # Only apply color to Status column
                        item.setForeground(Columns.STATUS, color)

                        # Make Status column bold
                        font = item.font(Columns.STATUS)
                        font.setBold(True)
                        item.setFont(Columns.STATUS, font)


                        # Tooltip
                        tooltip_parts = []
                        tooltip_parts.append(f"Status: {task_data.get('simplified_status', StatusValues.COMPLETED)}")
                        tooltip_parts.append(f"Details: {task_data.get('status_details', 'No details available')}")

                        if 'error_details' in task_data and task_data['error_details']:
                            tooltip_parts.append("")
                            tooltip_parts.append("Errors:")
                            tooltip_parts.extend(task_data['error_details'])

                        item.setToolTip(Columns.STATUS, "\n".join(tooltip_parts))

                        shown_count += 1
                    else:
                        pass
                else:
                    item.setHidden(True)
                    hidden_count += 1


            total_selected_tasks = sum(len(tasks) for jobs in selected_analysis.values() for tasks in jobs.values())
            visible_tasks = sum(1 for i in range(self.table.topLevelItemCount()) if not self.table.topLevelItem(i).isHidden())
            self.status_bar.showMessage(f"Analysis completed. Showing {visible_tasks} selected tasks (out of {total_selected_tasks} analyzed).")

            self.table_focused_mode = True

            self.update_status_dropdown()
            self.update_job_dropdown()
            self.update_task_dropdown()

            # ADD THIS: Re-apply filters after updating table
            self.reapply_filters_after_table_update()

            self.table.viewport().update()

            # Apply minimum column widths for keyword columns
            self.set_keyword_column_widths(min_width=80, fixed_width=False)

        def get_keyword_value(self, task_data: Dict[str, Any], keyword_name: str, default: str = "-") -> str:
            """Get keyword value from task data"""
            for name, keyword_data in task_data['keywords'].items():
                if name.lower() == keyword_name.lower():
                    if keyword_data['value'] is not None:
                        if isinstance(keyword_data['value'], dict) and 'h' in keyword_data['value'] and 'v' in keyword_data['value']:
                            h_val = keyword_data['value']['h']
                            v_val = keyword_data['value']['v']
                            return f"{h_val:.2f}H/{v_val:.2f}V"
                        else:
                            value = keyword_data['value']
                            if isinstance(value, (int, float)):
                                if abs(value) >= 1e6:
                                    if value == int(value):
                                        return str(int(value))
                                    else:
                                        return f"{value:,.0f}" if value >= 1000 else f"{value:.2f}"
                                elif abs(value) < 1e-3 and value != 0:
                                    return f"{value:.2e}"
                                elif isinstance(value, float):
                                    if value == int(value):
                                        return str(int(value))
                                    else:
                                        return f"{value:.6g}"
                                else:
                                    return str(value)
                            else:
                                return str(value)
                    else:
                        return default
            return default

        def refresh_analysis(self):
            """Refresh analysis data while preserving filter state"""
            if hasattr(self, '_refreshing') and self._refreshing:
                self.status_bar.showMessage("Refresh already in progress...")
                return

            try:
                self._refreshing = True
                self.initializing = True

                # Save filter state
                current_filters = {
                    'status': self.status_combo.currentText(),
                    'job': self.job_combo.currentText(),
                    'task': self.task_combo.currentText(),
                    'base_dir': self.base_dir_combo.currentText(),
                    'top_name': self.top_name_combo.currentText(),
                    'user': self.user_combo.currentText(),
                    'block': self.block_combo.currentText(),
                    'dk_ver_tag': self.dk_ver_tag_combo.currentText(),
                    'run_version': self.run_version_combo.currentText(),
                    'hide_invalid': self.hide_invalid_status_cb.isChecked()
                }

                self.table.clear()
                self.clear_user_hidden_columns()

                self.populate_tree_with_discovery()

                # Apply minimum column widths for keyword columns
                self.set_keyword_column_widths(min_width=80, fixed_width=False)

                # Restore filters
                self.status_combo.blockSignals(True)
                self.job_combo.blockSignals(True)
                self.task_combo.blockSignals(True)
                self.base_dir_combo.blockSignals(True)
                self.top_name_combo.blockSignals(True)
                self.user_combo.blockSignals(True)
                self.block_combo.blockSignals(True)
                self.dk_ver_tag_combo.blockSignals(True)
                self.run_version_combo.blockSignals(True)

                self.status_combo.setCurrentText(current_filters['status'])
                self.job_combo.setCurrentText(current_filters['job'])
                self.task_combo.setCurrentText(current_filters['task'])
                self.base_dir_combo.setCurrentText(current_filters['base_dir'])
                self.top_name_combo.setCurrentText(current_filters['top_name'])
                self.user_combo.setCurrentText(current_filters['user'])
                self.block_combo.setCurrentText(current_filters['block'])
                self.dk_ver_tag_combo.setCurrentText(current_filters['dk_ver_tag'])
                self.run_version_combo.setCurrentText(current_filters['run_version'])
                self.hide_invalid_status_cb.setChecked(current_filters['hide_invalid'])

                self.status_combo.blockSignals(False)
                self.job_combo.blockSignals(False)
                self.task_combo.blockSignals(False)
                self.base_dir_combo.blockSignals(False)
                self.top_name_combo.blockSignals(False)
                self.user_combo.blockSignals(False)
                self.block_combo.blockSignals(False)
                self.dk_ver_tag_combo.blockSignals(False)
                self.run_version_combo.blockSignals(False)

                self.initializing = False

                # CRITICAL: Re-apply keyword column visibility before row filters
                keyword_visibility_text = self.keyword_visibility_input.text().strip()
                if keyword_visibility_text:
                    self.apply_keyword_column_visibility()

                self.apply_filters()

                filtered_count = sum(1 for i in range(self.table.topLevelItemCount())
                                   if not self.table.topLevelItem(i).isHidden())
                total_count = self.table.topLevelItemCount()
                self.status_bar.showMessage(f"Analysis refreshed: {filtered_count} of {total_count} run versions displayed (filtered)")

            except Exception as e:
                print(f"ERROR: Refresh failed: {e}")
                import traceback
                traceback.print_exc()
                self.status_bar.showMessage(f"Refresh failed: {str(e)}")
            finally:
                self._refreshing = False
                self.initializing = False

                # CRITICAL: Scroll to leftmost position after refresh
                # Place in finally block to ensure it always runs
                self.table.horizontalScrollBar().setValue(0)
                self.table.verticalScrollBar().setValue(0)

        def clear_selection(self):
            """Clear all selected items"""
            self.table.clearSelection()
            self.status_bar.showMessage("Selection cleared")

        def toggle_path_columns(self):
            """Toggle visibility of path columns"""
            self.path_columns_hidden = not self.path_columns_hidden

            if self.path_columns_hidden:
                self.table.setColumnHidden(Columns.BASE_DIR, True)
                self.table.setColumnHidden(Columns.TOP_NAME, True)
                self.table.setColumnHidden(Columns.JOB, True)
                self.toggle_path_btn.setText("Show Path Columns (P)")
                self.status_bar.showMessage("Hidden Base Dir, Top Name, and Job columns. Press 'P' or click 'Show Path Columns' to restore.")
            else:
                self.table.setColumnHidden(Columns.BASE_DIR, False)
                self.table.setColumnHidden(Columns.TOP_NAME, False)
                self.table.setColumnHidden(Columns.JOB, False)
                self.toggle_path_btn.setText("Hide Path Columns (P)")
                self.status_bar.showMessage("Showed Base Dir, Top Name, and Job columns.")

            self.table.viewport().update()

        def reapply_filters_after_table_update(self):
            """Re-apply all current filter settings after table content changes"""
            # Skip if initializing
            if hasattr(self, 'initializing') and self.initializing:
                return

            # CRITICAL: Re-apply keyword column visibility FIRST (before row filters)
            # This ensures columns are hidden/shown based on user's filter
            keyword_visibility_text = self.keyword_visibility_input.text().strip()
            if keyword_visibility_text:
                # User has active keyword column filter - apply it
                self.apply_keyword_column_visibility()
            else:
                # No filter - show all keyword columns
                self.show_all_keyword_columns()

            # Then re-apply row/value filters
            self.apply_filters()

            # Update status bar with filter info
            visible_items = sum(1 for i in range(self.table.topLevelItemCount())
                               if not self.table.topLevelItem(i).isHidden())
            total_items = self.table.topLevelItemCount()
            active_filters = self.get_active_filters_text()

            if active_filters != "None":
                self.status_bar.showMessage(
                    f"Showing {visible_items} of {total_items} rows | Active filters: {active_filters}")
            else:
                self.status_bar.showMessage(f"Showing {visible_items} of {total_items} rows")


        def cycle_hide_data(self):
            """Cycle through hide data states: Show All ? Hide Invalid ? Hide Invalid+Zero ? Show All"""
            # Advance to next state
            self.hide_data_state = (self.hide_data_state + 1) % 3


            if self.hide_data_state == 0:
                # State 0: Show All Data
                self.show_all_data()
                self.cycle_hide_btn.setText("Hide Invalid Data (^I)")
                self.cycle_hide_btn.setStyleSheet(f"background-color: {Colors.MISTY_BLUE}; color: black; padding: 2px;")
                self.status_bar.showMessage("Showing all data. Press ^I to hide invalid data (works on filtered rows).")

            elif self.hide_data_state == 1:
                # State 1: Hide Invalid Data
                self.hide_invalid_data()
                self.cycle_hide_btn.setText("Hide Invalid + Zero (^I)")
                self.cycle_hide_btn.setStyleSheet(f"background-color: {Colors.OLIVE}; color: black; padding: 2px;")
                # Status message set by hide_invalid_data()

            elif self.hide_data_state == 2:
                # State 2: Hide Invalid + Zero Data
                self.hide_invalid_and_zero_data()
                self.cycle_hide_btn.setText("Show All Data (^I)")
                self.cycle_hide_btn.setStyleSheet(f"background-color: {Colors.TEAL}; color: black; padding: 2px;")
                # Status message set by hide_invalid_and_zero_data()

        def hide_invalid_data(self):
            """Hide columns and rows with only invalid values"""
            def is_invalid(value_text: str) -> bool:
                """Check if value is invalid (empty, dash, N/A, etc.)"""
                if not value_text or not value_text.strip():
                    return True
                return value_text in ["-", "N/A", "n/a", "NA", "na", "No Data",
                                     "null", "NULL", "None", "none"]

            self._hide_data_by_condition(is_invalid, "invalid")

        def hide_invalid_and_zero_data(self):
            """Hide columns and rows with invalid values OR zero values"""
            def is_invalid_or_zero(value_text: str) -> bool:
                """Check if value is invalid or zero"""
                if not value_text or not value_text.strip():
                    return True

                if value_text in ["-", "N/A", "n/a", "NA", "na", "No Data",
                                 "null", "NULL", "None", "none"]:
                    return True

                try:
                    clean_value = value_text.replace(',', '').replace('$', '').replace('%', '').strip()
                    return abs(float(clean_value)) < 1e-10
                except (ValueError, TypeError):
                    return False

            self._hide_data_by_condition(is_invalid_or_zero, "invalid/zero")

        def show_all_data(self):
            """Show all hidden rows and columns (except user-hidden columns)"""
            # Clear hide data tracking
            self.hide_data_hidden_columns.clear()
            self.hide_data_hidden_rows.clear()

            # Show all rows
            for i in range(self.table.topLevelItemCount()):
                item = self.table.topLevelItem(i)
                item.setHidden(False)

            # Show all columns except user-hidden ones
            headers = self.generate_dynamic_headers()
            path_column_count = Columns.PATH_COLUMN_COUNT

            for col_index in range(path_column_count, len(headers)):
                # Don't unhide columns that user explicitly hid via context menu
                if col_index not in self.user_hidden_columns:
                    # Don't unhide if path columns are toggled off
                    if self.path_columns_hidden and col_index in [Columns.BASE_DIR, Columns.TOP_NAME, Columns.JOB]:
                        continue
                    self.table.setColumnHidden(col_index, False)

            # Re-apply filters after showing all data
            self.reapply_filters_after_table_update()

            # Update count in status bar
            visible_rows = sum(1 for i in range(self.table.topLevelItemCount())
                              if not self.table.topLevelItem(i).isHidden())
            total_rows = self.table.topLevelItemCount()

            self.status_bar.showMessage(f"Showing all data: {visible_rows}/{total_rows} rows visible.")

        def _hide_data_by_condition(self, condition_func, description: str):
            """Generic function to hide columns/rows based on condition

            Args:
                condition_func: Function that takes value_text and returns True if invalid
                description: Description for status message (e.g., 'invalid', 'invalid/zero')
            """
            # Clear previous hide data tracking
            self.hide_data_hidden_columns.clear()
            self.hide_data_hidden_rows.clear()

            # CRITICAL FIX: Only analyze rows that are currently visible (passing Advanced Filters)
            # Do NOT show all rows temporarily - respect current filter state
            all_items = [self.table.topLevelItem(i)
                         for i in range(self.table.topLevelItemCount())
                         if not self.table.topLevelItem(i).isHidden()]

            if not all_items:
                self.status_bar.showMessage("No items to analyze (all rows filtered out).")
                return

            headers = self.generate_dynamic_headers()
            path_column_count = Columns.PATH_COLUMN_COUNT
            columns_to_hide = []
            rows_to_hide = []

            # Check columns against condition
            for col_index in range(path_column_count, len(headers)):
                if all(condition_func(item.text(col_index)) for item in all_items):
                    columns_to_hide.append((col_index, headers[col_index]))

            # CRITICAL FIX: Hide columns BEFORE checking rows
            for col_index, _ in columns_to_hide:
                self.table.setColumnHidden(col_index, True)
                self.hide_data_hidden_columns.add(col_index)

            # Check rows against condition (NOW columns are already hidden)
            for item in all_items:
                valid_values = sum(
                    1 for col_index in range(path_column_count, item.columnCount())
                    if col_index < len(headers)
                    and not self.table.isColumnHidden(col_index)
                    and not condition_func(item.text(col_index))
                )
                total_cols = sum(
                    1 for col_index in range(path_column_count, item.columnCount())
                    if col_index < len(headers) and not self.table.isColumnHidden(col_index)
                )

                # ALSO FIX: Handle case when all columns are hidden (total_cols == 0)
                if total_cols == 0 or (total_cols > 0 and valid_values == 0):
                    # Get actual table row index for tracking
                    actual_row_index = self.table.indexOfTopLevelItem(item)
                    rows_to_hide.append((actual_row_index, item))

            # Apply row hiding and track what we hid
            for row_index, item in rows_to_hide:
                item.setHidden(True)
                self.hide_data_hidden_rows.add(row_index)

            # DO NOT call reapply_filters_after_table_update() here!
            # Instead, manually apply filters WITHOUT unhiding our hidden rows
            self._apply_filters_preserve_hide_data()

            visible_rows = sum(1 for i in range(self.table.topLevelItemCount())
                               if not self.table.topLevelItem(i).isHidden())
            total_rows = self.table.topLevelItemCount()

            summary = f"Hidden {len(columns_to_hide)} {description} columns and {len(rows_to_hide)} {description} rows "
            summary += f"from filtered dataset. Showing {visible_rows}/{total_rows} rows."
            self.status_bar.showMessage(summary)


        def show_hidden_columns(self):
            """Show columns hidden via context menu"""
            hidden_columns_count = 0

            for col_index in list(self.user_hidden_columns):
                if self.table.isColumnHidden(col_index):
                    if not (self.path_columns_hidden and col_index in [Columns.BASE_DIR, Columns.TOP_NAME, Columns.JOB]):
                        self.table.setColumnHidden(col_index, False)
                        self.user_hidden_columns.discard(col_index)
                        hidden_columns_count += 1

            if hidden_columns_count > 0:
                self.status_bar.showMessage(f"Shown {hidden_columns_count} previously hidden columns.")
            else:
                self.status_bar.showMessage("No user-hidden columns to show.")

            self.update_show_hidden_columns_button_state()

        def update_show_hidden_columns_button_state(self):
            """Update Show Hidden Columns button state and text with count"""
            if hasattr(self, 'show_hidden_columns_btn'):
                hidden_count = len(self.user_hidden_columns)

                if hidden_count > 0:
                    self.show_hidden_columns_btn.setEnabled(True)
                    self.show_hidden_columns_btn.setText(f"Show Hidden Columns ({hidden_count} ea)")
                else:
                    self.show_hidden_columns_btn.setEnabled(False)
                    self.show_hidden_columns_btn.setText("Show Hidden Columns")

        def clear_user_hidden_columns(self):
            """Clear user hidden columns tracking"""
            self.user_hidden_columns.clear()
            self.update_show_hidden_columns_button_state()

        def archive_analysis_data(self):
            """Archive analysis data to database"""
            if not ARCHIVE_AVAILABLE:
                QMessageBox.warning(self, "Archive Unavailable",
                                  "Archive functionality is not available.\n"
                                  "Please ensure hawkeye_archive.py is in the same directory.")
                return

            if not hasattr(self.analyzer, 'analysis_results') or not self.analyzer.analysis_results:
                QMessageBox.warning(self, "No Data to Archive",
                                  "No analysis data found to archive.\n"
                                  "Please run 'Gather Selected' first to analyze some runs.")
                return

            try:
                from hawkeye_archive import HawkeyeArchive

                casino_prj_base = os.getenv('casino_prj_base')
                casino_prj_name = os.getenv('casino_prj_name')
                if casino_prj_name:
                    archive_path = os.path.join(casino_prj_base, casino_prj_name, 'hawkeye_archive')
                    archive = HawkeyeArchive(archive_path)
                else:
                    archive = HawkeyeArchive()

                num_runs = len(self.analyzer.analysis_results)
                reply = QMessageBox.question(self, "Archive Analysis Data",
                                           f"Archive {num_runs} analyzed run(s) to database?\n\n"
                                           f"This will store all analysis results for future reference.\n"
                                           f"Existing entries will be updated with new data.",
                                           QMessageBox.Yes | QMessageBox.No,
                                           QMessageBox.Yes)

                if reply != QMessageBox.Yes:
                    return

                progress = QProgressBar()
                progress.setRange(0, 0)

                progress_dialog = QDialog(self)
                progress_dialog.setWindowTitle("Archiving Data")
                progress_dialog.setModal(True)
                progress_dialog.resize(300, 100)

                layout = QVBoxLayout(progress_dialog)
                layout.addWidget(QLabel("Archiving analysis data..."))
                layout.addWidget(progress)

                progress_dialog.show()
                QApplication.processEvents()

                results = archive.archive_analysis_data(self.analyzer)

                progress_dialog.close()

                if results['errors']:
                    error_msg = "\n".join(results['errors'][:5])
                    if len(results['errors']) > 5:
                        error_msg += f"\n... and {len(results['errors']) - 5} more errors"

                    QMessageBox.warning(self, "Archive Completed with Errors",
                                      f"Archive completed with some errors:\n\n"
                                      f"Archived: {results['archived_entries']} runs\n"
                                      f"Skipped: {results['skipped_entries']} runs\n"
                                      f"Errors: {len(results['errors'])}\n\n"
                                      f"Error details:\n{error_msg}")
                else:
                    QMessageBox.information(self, "Archive Successful",
                                          f"Successfully archived analysis data!\n\n"
                                          f"Archived: {results['archived_entries']} runs\n"
                                          f"Skipped: {results['skipped_entries']} runs\n\n"
                                          f"Archived runs:\n{chr(10).join(results['archived_runs'][:5])}"
                                          f"{'...' if len(results['archived_runs']) > 5 else ''}")

                self.statusBar().showMessage(f"Archived {results['archived_entries']} runs", 5000)

            except Exception as e:
                QMessageBox.critical(self, "Archive Error",
                                   f"Failed to archive data:\n{str(e)}")
                print(f"Archive error: {e}")

        def export_table_to_csv(self):
            """Export table to CSV with options"""
            dialog = QDialog(self)
            dialog.setWindowTitle("Export CSV Options")
            dialog.setModal(True)
            dialog.resize(400, 200)

            layout = QVBoxLayout(dialog)

            title_label = QLabel("Choose Export Option:")
            title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            layout.addWidget(title_label)

            desc_label = QLabel("Select what data to export:")
            layout.addWidget(desc_label)

            self.export_full_table = QCheckBox("Export Full Table (All Data)")
            self.export_filtered_table = QCheckBox("Export Filtered Table (Currently Displayed)")

            self.export_filtered_table.setChecked(True)

            self.export_full_table.setToolTip("Export all data in the table, ignoring any active filters")
            self.export_filtered_table.setToolTip("Export only the data currently visible (respects active filters and sorting)")

            layout.addWidget(self.export_full_table)
            layout.addWidget(self.export_filtered_table)

            button_layout = QHBoxLayout()

            export_btn = QPushButton("Export CSV")
            export_btn.clicked.connect(dialog.accept)
            export_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
            button_layout.addWidget(export_btn)

            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(dialog.reject)
            cancel_btn.setStyleSheet("background-color: #f44336; color: white; padding: 8px;")
            button_layout.addWidget(cancel_btn)

            layout.addLayout(button_layout)

            if dialog.exec_() != QDialog.Accepted:
                return

            export_full = self.export_full_table.isChecked()
            export_filtered = self.export_filtered_table.isChecked()

            if not export_full and not export_filtered:
                QMessageBox.warning(self, "No Option Selected", "Please select an export option.")
                return

            if export_full:
                items_to_export = []
                for i in range(self.table.topLevelItemCount()):
                    item = self.table.topLevelItem(i)
                    if item:
                        items_to_export.append(item)
                export_mode = "full"
            else:
                items_to_export = []
                for i in range(self.table.topLevelItemCount()):
                    item = self.table.topLevelItem(i)
                    if item and not item.isHidden():
                        items_to_export.append(item)
                export_mode = "filtered"

            if not items_to_export:
                QMessageBox.information(self, "No Data", "No data to export.")
                return

            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

            if export_mode == "full":
                default_filename = f"hawkeye_data_full_{timestamp}.csv"
            else:
                active_filters = []
                if self.status_combo.currentText() != "all":
                    active_filters.append("status")
                if self.job_combo.currentText() != "all":
                    active_filters.append("job")
                if self.task_combo.currentText() != "all":
                    active_filters.append("task")
                if self.top_name_combo.currentText() != "all":
                    active_filters.append("user")
                if self.block_combo.currentText() != "all":
                    active_filters.append("block")
                if self.dk_ver_tag_combo.currentText() != "all":
                    active_filters.append("dk_ver_tag")
                if self.run_version_combo.currentText() != "all":
                    active_filters.append("run_version")
                if self.keyword_filter_input.text().strip():
                    active_filters.append("keyword")

                filter_suffix = "_filtered" if active_filters else "_displayed"
                default_filename = f"hawkeye_data{filter_suffix}_{timestamp}.csv"

            try:
                csv_buffer = io.StringIO()
                writer = csv.writer(csv_buffer)

                all_headers = self.generate_dynamic_headers()
                visible_headers = []
                visible_column_indices = []

                for i, header in enumerate(all_headers):
                    if i < self.table.columnCount() and not self.table.isColumnHidden(i):
                        visible_headers.append(header)
                        visible_column_indices.append(i)

                writer.writerow(visible_headers)

                for item in items_to_export:
                    row_data = []
                    for col_index in visible_column_indices:
                        if col_index < item.columnCount():
                            row_data.append(item.text(col_index))
                        else:
                            row_data.append("")
                    writer.writerow(row_data)

                csv_content = csv_buffer.getvalue()
                csv_buffer.close()

                export_type = "Full table" if export_mode == "full" else "Filtered table"
                self.show_csv_contents_dialog(csv_content, export_type, len(items_to_export), default_filename)

            except Exception as e:
                QMessageBox.critical(self, "Export Error",
                                   f"Error generating CSV data: {str(e)}")

        def show_csv_contents_dialog(self, csv_content: str, export_type: str, row_count: int, filename: str):
            """Show CSV contents in dialog"""
            dialog = QDialog(self)
            dialog.setWindowTitle(f"CSV Export - {export_type}")
            dialog.setModal(True)
            dialog.resize(800, 600)

            layout = QVBoxLayout(dialog)

            title_label = QLabel(f"CSV Export Successful - {export_type}")
            title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2E8B57;")
            layout.addWidget(title_label)

            info_label = QLabel(f"Exported {row_count} rows to: {filename}")
            info_label.setStyleSheet("color: #666; margin-bottom: 10px;")
            layout.addWidget(info_label)

            content_label = QLabel("CSV Contents (select all to copy):")
            content_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            layout.addWidget(content_label)

            text_area = QTextEdit()
            text_area.setPlainText(csv_content)
            text_area.setReadOnly(True)
            text_area.setStyleSheet("""
                QTextEdit {
                    font-family: 'Courier New', monospace;
                    font-size: 10px;
                    background-color: #f8f8f8;
                    border: 1px solid #ccc;
                    padding: 5px;
                }
            """)
            layout.addWidget(text_area)

            button_layout = QHBoxLayout()

            copy_btn = QPushButton("Copy All to Clipboard")
            copy_btn.clicked.connect(lambda: self.copy_csv_to_clipboard(csv_content))
            copy_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-weight: bold;")
            button_layout.addWidget(copy_btn)

            save_btn = QPushButton("Save to File")
            save_btn.clicked.connect(lambda: self.save_csv_to_file(csv_content, filename, dialog))
            save_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 8px; font-weight: bold;")
            button_layout.addWidget(save_btn)

            select_all_btn = QPushButton("Select All Text")
            select_all_btn.clicked.connect(text_area.selectAll)
            select_all_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
            button_layout.addWidget(select_all_btn)

            button_layout.addStretch()

            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            close_btn.setStyleSheet("background-color: #f44336; color: white; padding: 8px;")
            button_layout.addWidget(close_btn)

            layout.addLayout(button_layout)

            dialog.exec_()

        def copy_csv_to_clipboard(self, csv_content: str):
            """Copy CSV to clipboard"""
            try:
                clipboard = QApplication.clipboard()
                clipboard.setText(csv_content)
                self.status_bar.showMessage("CSV content copied to clipboard")
                QMessageBox.information(self, "Copied", "CSV content has been copied to clipboard!")
            except Exception as e:
                QMessageBox.warning(self, "Copy Error", f"Failed to copy to clipboard: {str(e)}")

        def save_csv_to_file(self, csv_content: str, default_filename: str, dialog):
            """Save CSV to file"""
            try:
                filename, _ = QFileDialog.getSaveFileName(
                    dialog, "Save CSV File",
                    default_filename, "CSV files (*.csv);;All files (*.*)"
                )

                if filename:
                    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                        csvfile.write(csv_content)

                    self.status_bar.showMessage(f"CSV saved to {filename}")
                    QMessageBox.information(dialog, "Save Successful",
                                          f"CSV file has been saved to:\n{filename}")

            except Exception as e:
                QMessageBox.critical(dialog, "Save Error", f"Failed to save CSV file: {str(e)}")

        def export_table_to_html(self):
            """Export table to HTML"""
            try:
                filename, _ = QFileDialog.getSaveFileName(
                    self, "Export Table to HTML", "", "HTML files (*.html);;All files (*.*)"
                )

                if not filename:
                    return

                html_content = self.generate_html_table()

                with open(filename, 'w', encoding='utf-8') as htmlfile:
                    htmlfile.write(html_content)

                total_rows = self.table.topLevelItemCount()
                self.status_bar.showMessage(f"Exported {total_rows} rows to HTML: {filename}")

            except Exception as e:
                QMessageBox.critical(self, "Export Error",
                                   f"Error exporting to HTML:\n{str(e)}")

        def generate_html_table(self) -> str:
            """Generate HTML table with styling"""
            headers = []
            for i in range(self.table.columnCount()):
                headers.append(self.table.headerItem().text(i))

            html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hawkeye Analysis Export</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            color: white;
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }

        .table-wrapper {
            overflow-x: auto;
            margin: 20px;
            max-height: 600px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }

        th {
            background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #495057;
            border-bottom: 2px solid #dee2e6;
            position: sticky;
            top: 0;
            z-index: 10;
        }

        td {
            padding: 12px;
            border-bottom: 1px solid #e9ecef;
        }

        tr:hover td {
            background: #f8f9fa;
        }

        tr:nth-child(even) {
            background: #f8f9fa;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Hawkeye Analysis Export</h1>
        </div>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
"""

            for header in headers:
                html += f"                        <th>{header}</th>\n"

            html += """                    </tr>
                </thead>
                <tbody>
"""

            for i in range(self.table.topLevelItemCount()):
                item = self.table.topLevelItem(i)
                html += "                    <tr>\n"
                for j in range(item.columnCount()):
                    value = item.text(j)
                    html += f"                        <td>{value}</td>\n"
                html += "                    </tr>\n"

            html += """                </tbody>
            </table>
        </div>
    </div>
</body>
</html>"""

            return html

        def show_context_menu(self, position):
            """Show context menu for selected runs"""
            item = self.table.itemAt(position)
            if not item:
                return

            selected_items = self.table.selectedItems()
            if not selected_items:
                return

            context_menu = QMenu(self)

            run_paths = set()
            for selected_item in selected_items:
                run_path = selected_item.data(0, Qt.UserRole)
                if run_path:
                    run_paths.add(run_path)

            if len(run_paths) == 1:
                run_path = list(run_paths)[0]

                go_to_dir_action = context_menu.addAction("Go to Run Directory")
                go_to_dir_action.triggered.connect(lambda: self.open_run_directory(run_path))

                context_menu.addSeparator()

                copy_path_action = context_menu.addAction("Copy Run Directory Path")
                copy_path_action.triggered.connect(lambda: self.copy_run_path(run_path))
            else:
                context_menu.addAction(f"Multiple runs selected ({len(run_paths)})")
                context_menu.addSeparator()

                copy_all_action = context_menu.addAction("Copy All Run Directory Paths")
                copy_all_action.triggered.connect(lambda: self.copy_all_run_paths(run_paths))

            context_menu.exec_(self.table.mapToGlobal(position))

        def show_column_statistics(self, column_index: int):
            """Show statistics for numeric columns"""
            headers = self.generate_dynamic_headers()
            column_name = headers[column_index]

            values = []
            for i in range(self.table.topLevelItemCount()):
                item = self.table.topLevelItem(i)
                if not item.isHidden():
                    text = item.text(column_index)
                    if text and text not in ['-', 'N/A']:
                        try:
                            values.append(float(text.replace(',', '')))
                        except ValueError:
                            pass

            if not values:
                QMessageBox.information(self, "No Data",
                    f"Column '{column_name}' has no numeric values")
                return

            # Calculate statistics
            import statistics
            stats = {
                'Count': len(values),
                'Min': min(values),
                'Max': max(values),
                'Mean': statistics.mean(values),
                'Median': statistics.median(values),
                'Std Dev': statistics.stdev(values) if len(values) > 1 else 0
            }

            # Show dialog
            msg = f"Statistics for '{column_name}':\n\n"
            for key, value in stats.items():
                if isinstance(value, float):
                    msg += f"{key}: {value:.4f}\n"
                else:
                    msg += f"{key}: {value}\n"

            QMessageBox.information(self, f"Column Statistics - {column_name}", msg)

        def show_column_context_menu(self, position):
            """Show context menu for column headers"""
            header = self.table.header()
            column_index = header.logicalIndexAt(position)

            if column_index < 0:
                return

            headers = self.generate_dynamic_headers()

            if column_index >= len(headers):
                return

            column_name = headers[column_index]

            context_menu = QMenu(self)

            title_action = context_menu.addAction(f"Column: {column_name}")
            title_action.setEnabled(False)
            context_menu.addSeparator()

            if self.table.isColumnHidden(column_index):
                show_action = context_menu.addAction("Show Column")
                show_action.triggered.connect(lambda: self.toggle_column_visibility(column_index, True))
            else:
                hide_action = context_menu.addAction("Hide Column")
                hide_action.triggered.connect(lambda: self.toggle_column_visibility(column_index, False))

            # ========== ADD THIS SECTION ==========
            # Add separator and statistics option for keyword columns
            if column_index >= Columns.PATH_COLUMN_COUNT:  # Only for keyword columns
                context_menu.addSeparator()
                stats_action = context_menu.addAction("Show Statistics")
                stats_action.triggered.connect(lambda: self.show_column_statistics(column_index))
            # ======================================

            context_menu.exec_(header.mapToGlobal(position))

        def toggle_column_visibility(self, column_index: int, show: bool):
            """Toggle column visibility"""
            self.table.setColumnHidden(column_index, not show)

            if not show:
                self.user_hidden_columns.add(column_index)
            else:
                self.user_hidden_columns.discard(column_index)

            headers = self.generate_dynamic_headers()
            if column_index < len(headers):
                column_name = headers[column_index]
                action = "shown" if show else "hidden"
                self.status_bar.showMessage(f"Column '{column_name}' {action}.")

            self.update_show_hidden_columns_button_state()

        def open_run_directory(self, run_path: str):
            """Open terminal in run directory"""
            try:
                if os.path.exists(run_path):

                    current_gid = os.getgid()
                    current_groups = os.getgroups()

                    current_env = os.environ.copy()

                    try:
                        import grp
                        group_info = grp.getgrgid(current_gid)
                        group_name = group_info.gr_name

                        terminal_command = f"cd {run_path}; newgrp {group_name} && exec bash"
                        process = subprocess.Popen([
                            "gnome-terminal",
                            "--working-directory", run_path,
                            "--", "bash", "-c", terminal_command
                        ], env=current_env)


                    except Exception as e:
                        process = subprocess.Popen(["gnome-terminal", "--working-directory", run_path])

                    self.status_bar.showMessage(f"Opened terminal in directory: {run_path}")
                    return
                else:
                    QMessageBox.warning(self, "Directory Not Found",
                                      f"The directory does not exist:\n{run_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error",
                                   f"Failed to open terminal:\n{str(e)}")

        def copy_run_path(self, run_path: str):
            """Copy run path to clipboard"""
            try:
                clipboard = QApplication.clipboard()
                clipboard.setText(run_path)
                self.status_bar.showMessage(f"Copied to clipboard: {run_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error",
                                   f"Failed to copy to clipboard:\n{str(e)}")

        def copy_all_run_paths(self, run_paths: Set[str]):
            """Copy all run paths to clipboard"""
            try:
                clipboard = QApplication.clipboard()
                paths_text = "\n".join(sorted(run_paths))
                clipboard.setText(paths_text)
                self.status_bar.showMessage(f"Copied {len(run_paths)} paths to clipboard")
            except Exception as e:
                QMessageBox.critical(self, "Error",
                                   f"Failed to copy to clipboard:\n{str(e)}")

        def on_item_double_click(self, item, column: int):
            """Handle double-click on table item"""
            run_path = item.data(0, Qt.UserRole)
            if run_path:
                if run_path in self.runs_data:
                    # Show run details if available
                    pass
                else:
                    QMessageBox.information(self, "Run Not Analyzed",
                                          "This run has not been analyzed yet.\n\n"
                                          "Select it and click 'Gather Selected' to analyze.")

        def on_header_clicked(self, logical_index: int):
            """Handle header click for sorting"""
            try:
                if logical_index < 0 or logical_index >= self.table.columnCount():
                    return

                if self.current_sort_column == logical_index:
                    self.sort_ascending = not self.sort_ascending
                else:
                    self.current_sort_column = logical_index
                    self.sort_ascending = True

                self.update_header_sort_indicators()
                self.sort_table_by_column(logical_index, self.sort_ascending)

                sort_direction = "ascending" if self.sort_ascending else "descending"
                headers = self.generate_dynamic_headers()
                column_name = headers[logical_index] if logical_index < len(headers) else "Unknown"
                self.status_bar.showMessage(f"Sorted by {column_name} ({sort_direction})")

            except Exception as e:
                print(f"Error in on_header_clicked: {e}")
                QMessageBox.warning(self, "Sorting Error",
                                  f"Unable to sort column {logical_index}. Please try again.")

        def update_header_sort_indicators(self):
            """Update header to show sort indicators with blue color for sorted column"""
            header = self.table.headerItem()
            if not header:
                return

            try:
                headers = self.generate_dynamic_headers()

                # Reset all headers to default color and remove indicators
                for i in range(self.table.columnCount()):
                    if i < len(headers):
                        header.setText(i, headers[i])
                    else:
                        text = header.text(i)
                        if text.endswith(" ^") or text.endswith(" v"):
                            text = text[:-2]
                        header.setText(i, text)

                    # Reset to default (black) color
                    header.setForeground(i, QColor(0, 0, 0))

                # Update the currently sorted column
                if 0 <= self.current_sort_column < self.table.columnCount():
                    if self.current_sort_column < len(headers):
                        base_text = headers[self.current_sort_column]
                    else:
                        base_text = header.text(self.current_sort_column)
                        if base_text.endswith(" ^") or base_text.endswith(" v"):
                            base_text = base_text[:-2]

                    indicator = " ^" if self.sort_ascending else " v"
                    header.setText(self.current_sort_column, base_text + indicator)

                    # Set blue color for sorted column
                    header.setForeground(self.current_sort_column, QColor(0, 100, 200))

            except Exception as e:
                print(f"Error in update_header_sort_indicators: {e}")

        def sort_table_by_column(self, column: int, ascending: bool = True):
            """Sort table by specified column"""
            try:
                if column < 0 or column >= self.table.columnCount():
                    return

                items = []
                item_count = self.table.topLevelItemCount()
                for i in range(item_count):
                    item = self.table.takeTopLevelItem(0)
                    if item:
                        items.append(item)

                def sort_key(item):
                    try:
                        if not item or column >= item.columnCount():
                            return (2, "", 0)  # Priority 2, empty string, zero

                        text = item.text(column)
                        if not text:
                            return (2, "", 0)

                        text = text.strip()

                        # Handle special "invalid" values
                        if text in ["-", "N/A", "n/a", "NA", "na", "", "null", "NULL", "None", "none", "undefined", "UNDEFINED"]:
                            return (1, "", 0)  # Priority 1 (sorts after valid data)

                        # Try to parse as number
                        try:
                            clean_text = text.replace(',', '').replace(' ', '').replace('$', '').replace('%', '')

                            if clean_text.replace('-', '').replace('.', '').replace('e', '').replace('E', '').replace('+', '').isdigit():
                                num_val = float(clean_text)
                                return (0, num_val, 0)  # Priority 0 (sorts first), numeric value
                            else:
                                int_val = int(clean_text)
                                return (0, int_val, 0)  # Priority 0, integer value
                        except (ValueError, TypeError):
                            # Not a number, treat as string
                            return (0, 0, text.lower())  # Priority 0, zero for numeric slot, string value
                    except Exception as e:
                        return (2, "", 0)  # Priority 2 on error

                # Check if all valid values are identical - if so, skip sorting
                priority_0_items = [item for item in items if sort_key(item)[0] == 0]

                if priority_0_items:
                    # Get unique keys for valid data only (compare actual values, not priority)
                    distinct_keys = set(sort_key(item)[1:] for item in priority_0_items)

                    if len(distinct_keys) == 1:
                        # All valid values are identical - restore original order without sorting
                        for item in items:
                            self.table.addTopLevelItem(item)

                        headers = self.generate_dynamic_headers()
                        column_name = headers[column] if column < len(headers) else f"Column {column}"
                        self.status_bar.showMessage(f"Column '{column_name}' has identical values - not sorted")
                        return

                # Sort by the composite key: (priority, numeric_value, string_value)
                items.sort(key=sort_key, reverse=False)

                # If descending, reverse only the priority 0 items (valid data)
                if not ascending:
                    priority_0_items = [item for item in items if sort_key(item)[0] == 0]
                    priority_1_items = [item for item in items if sort_key(item)[0] == 1]
                    priority_2_items = [item for item in items if sort_key(item)[0] == 2]

                    priority_0_items.reverse()
                    items = priority_0_items + priority_1_items + priority_2_items

                for item in items:
                    self.table.addTopLevelItem(item)

            except Exception as e:
                print(f"Error in sort_table_by_column: {e}")
                import traceback
                traceback.print_exc()
                headers = self.generate_dynamic_headers()
                column_name = headers[column] if column < len(headers) else f"Column {column}"
                QMessageBox.warning(self, "Sorting Error",
                                  f"Unable to sort column '{column_name}' (column {column}).\n\n"
                                  f"This may be due to special characters or data format issues.\n"
                                  f"Error details: {str(e)}")

        def keyPressEvent(self, event):
            """Handle key press events"""

            # Handle Ctrl+C for Copy cell value at mouse position
            if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_C:
                # Use hovered item (under mouse) instead of current item (clicked)
                if self.hovered_item and self.hovered_column >= 0:
                    cell_value = self.hovered_item.text(self.hovered_column)

                    # Initialize clipboard
                    clipboard = QApplication.clipboard()

                    # Copy to both CLIPBOARD (Ctrl+V) and PRIMARY (middle-click paste)
                    clipboard.setText(cell_value, QClipboard.Clipboard)
                    clipboard.setText(cell_value, QClipboard.Selection)

                    # Get column name for status message
                    headers = self.generate_dynamic_headers()
                    column_name = headers[self.hovered_column] if self.hovered_column < len(headers) else f"Column {self.hovered_column}"

                    self.status_bar.showMessage(f"Copied cell value from '{column_name}': {cell_value}")
                else:
                    self.status_bar.showMessage("Hover over a cell first, then press Ctrl+C")
                event.accept()

            # Handle Ctrl+Shift+C for Copy COLUMN HEADER NAME
            elif event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier) and event.key() == Qt.Key_C:
                if self.hovered_column >= 0:
                    # Get column header name
                    headers = self.generate_dynamic_headers()

                    if self.hovered_column < len(headers):
                        column_name = headers[self.hovered_column]

                        clipboard = QApplication.clipboard()

                        # Copy column header name to clipboard
                        clipboard.setText(column_name, QClipboard.Clipboard)
                        clipboard.setText(column_name, QClipboard.Selection)

                        self.status_bar.showMessage(f"Copied column header: {column_name}")
                    else:
                        self.status_bar.showMessage(f"Copied column index: {self.hovered_column}")
                else:
                    self.status_bar.showMessage("Hover over a cell first, then press Ctrl+Shift+C")
                event.accept()

            # Handle Ctrl+S for Check Status
            elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_S:
                self.check_status_simple()
                event.accept()

            # Handle Ctrl+G for Gather Selected
            elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_G:
                self.gather_selected_runs()
                event.accept()

            # Handle Ctrl+R for Refresh
            elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_R:
                self.refresh_analysis()
                event.accept()

            # Handle P for path columns toggle
            elif event.key() == Qt.Key_P:
                self.toggle_path_columns()
                event.accept()

            # Handle I for cycling through hide data states (Show All ? Hide Invalid ? Hide Invalid+Zero)
            elif event.key() == Qt.Key_I:
                self.cycle_hide_data()
                event.accept()

            else:
                super().keyPressEvent(event)

        def save_keyword_filter_history(self):
            """Save keyword filter to history"""
            text = self.keyword_filter_input.text().strip()
            if text and text not in self.keyword_filter_history:
                self.keyword_filter_history.insert(0, text)
                self.keyword_filter_history = self.keyword_filter_history[:self.max_history_size]

        def save_keyword_visibility_history(self):
            """Save keyword visibility to history"""
            text = self.keyword_visibility_input.text().strip()
            if text and text not in self.keyword_visibility_history:
                self.keyword_visibility_history.insert(0, text)
                self.keyword_visibility_history = self.keyword_visibility_history[:self.max_history_size]

        def setup_keyword_filter_autocomplete(self):
            """Setup autocomplete for keyword filter"""
            completer = QCompleter()
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setCompletionMode(QCompleter.PopupCompletion)
            completer.setMaxVisibleItems(10)

            self.keyword_filter_input.textChanged.connect(self.update_keyword_filter_completer)
            self.update_keyword_filter_completer()
            self.keyword_filter_input.setCompleter(completer)

        def setup_keyword_visibility_autocomplete(self):
            """Setup autocomplete for keyword visibility"""
            completer = QCompleter()
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setCompletionMode(QCompleter.PopupCompletion)
            completer.setMaxVisibleItems(10)

            self.keyword_visibility_input.textChanged.connect(self.update_keyword_visibility_completer)
            self.update_keyword_visibility_completer()
            self.keyword_visibility_input.setCompleter(completer)

        def update_keyword_filter_completer(self):
            """Update completer model for keyword filter"""
            common_filters = [
                "error", "warning", "status", "completion",
                ">100", "<50", ">=80", "<=20",
                "error,warning", "status,completion"
            ]

            all_suggestions = self.keyword_filter_history + common_filters
            seen = set()
            unique_suggestions = []
            for item in all_suggestions:
                if item not in seen:
                    seen.add(item)
                    unique_suggestions.append(item)

            model = QStringListModel(unique_suggestions)
            if hasattr(self.keyword_filter_input, 'completer') and self.keyword_filter_input.completer():
                self.keyword_filter_input.completer().setModel(model)

        def update_keyword_visibility_completer(self):
            """Update completer model for keyword visibility"""
            common_patterns = [
                "hotspot", "power", "timing", "area", "utilization",
                "hotspot,power", "timing,area", "power,timing",
                "hotspot+power", "timing+area", "power+hotspot"
            ]

            all_suggestions = self.keyword_visibility_history + common_patterns
            seen = set()
            unique_suggestions = []
            for item in all_suggestions:
                if item not in seen:
                    seen.add(item)
                    unique_suggestions.append(item)

            model = QStringListModel(unique_suggestions)
            if hasattr(self.keyword_visibility_input, 'completer') and self.keyword_visibility_input.completer():
                self.keyword_visibility_input.completer().setModel(model)

        def show_chart_dialog(self, table):
            if not MATPLOTLIB_AVAILABLE:
                QMessageBox.warning(self, "Matplotlib Required",
                                  "Matplotlib is not available. Please install it to create charts.")
                return

            dialog = QDialog(self)
            dialog.setWindowTitle("Create Chart/Table")
            dialog.setModal(False)  # CRITICAL: Must be non-modal for independent operation
            dialog.resize(600, 700)

            layout = QVBoxLayout(dialog)

            # Title
            title_label = QLabel("Create Chart/Table from Table Data")
            title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            layout.addWidget(title_label)

            # Chart Type Selection
            type_group = QGroupBox("Chart Type")
            type_layout = QVBoxLayout(type_group)

            self.chart_type_combo = QComboBox()
            self.chart_type_combo.addItems([
                "Line Chart",
                "Bar Chart",
                "Scatter Plot",
                "Horizontal Bar Chart",
                "Area Chart"
            ])
            # Restore previous setting
            self.chart_type_combo.setCurrentText(self.chart_settings['chart_type'])
            type_layout.addWidget(self.chart_type_combo)
            layout.addWidget(type_group)

            # Data Selection
            data_group = QGroupBox("Data Selection")
            data_layout = QVBoxLayout(data_group)

            data_layout.addWidget(QLabel("X-axis Column:"))
            self.x_axis_combo = QComboBox()
            headers = self.generate_dynamic_headers()
            self.x_axis_combo.addItems(headers)
            # Restore previous setting
            self.x_axis_combo.setCurrentIndex(self.chart_settings['x_axis_index'])
            data_layout.addWidget(self.x_axis_combo)

            # Y-axis filter section
            y_filter_label = QLabel("Y-axis Column Filter:")
            y_filter_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            data_layout.addWidget(y_filter_label)

            # Current main GUI filter (read-only info)
            current_main_filter = self.keyword_visibility_input.text().strip()
            if current_main_filter:
                main_filter_info = QLabel(f"Main GUI filter: '{current_main_filter}'")
                main_filter_info.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
                data_layout.addWidget(main_filter_info)

            # Chart dialog filter (editable)
            filter_layout = QHBoxLayout()
            filter_layout.addWidget(QLabel("Filter:"))
            self.chart_y_filter_input = QLineEdit()
            self.chart_y_filter_input.setPlaceholderText("e.g., 'timing', 'power+wns', 'area,power' (OR/AND)")
            self.chart_y_filter_input.setClearButtonEnabled(True)

            # Start with main GUI filter if exists
            if current_main_filter:
                self.chart_y_filter_input.setText(current_main_filter)

            # Connect to real-time filtering
            self.chart_y_filter_input.textChanged.connect(
                lambda: self.filter_chart_y_axis_columns(headers)
            )
            filter_layout.addWidget(self.chart_y_filter_input)

            # Clear filter button
            clear_filter_btn = QPushButton("Clear")
            clear_filter_btn.setMaximumWidth(60)
            clear_filter_btn.clicked.connect(lambda: self.chart_y_filter_input.clear())
            filter_layout.addWidget(clear_filter_btn)
            data_layout.addLayout(filter_layout)

            # Filter help text
            filter_help = QLabel("Use ',' for OR (any match), '+' for AND (all terms)")
            filter_help.setStyleSheet("color: #666; font-size: 9px; font-style: italic;")
            data_layout.addWidget(filter_help)

            # Y-axis column list with selection count
            y_axis_header_layout = QHBoxLayout()
            y_axis_header_layout.addWidget(QLabel("Y-axis Column(s) (Ctrl+Click for multiple):"))

            # Selected count label
            self.y_axis_selected_count_label = QLabel("(0 selected)")
            self.y_axis_selected_count_label.setStyleSheet("color: #2196F3; font-weight: bold;")
            y_axis_header_layout.addWidget(self.y_axis_selected_count_label)
            y_axis_header_layout.addStretch()
            data_layout.addLayout(y_axis_header_layout)

            # Y-axis list widget
            self.y_axis_list = QTreeWidget()
            self.y_axis_list.setHeaderHidden(True)
            self.y_axis_list.setSelectionMode(QTreeWidget.ExtendedSelection)

            # Store all keyword column info for filtering
            self.all_y_axis_columns = []
            for i, header in enumerate(headers[Columns.PATH_COLUMN_COUNT:], Columns.PATH_COLUMN_COUNT):
                self.all_y_axis_columns.append((i, header))

            # Initial population (with filter if exists)
            self.populate_chart_y_axis_list(headers, current_main_filter)

            # Connect selection change to update count
            self.y_axis_list.itemSelectionChanged.connect(
                lambda: self.update_chart_y_axis_selection_count()
            )

            self.y_axis_list.setMaximumHeight(200)
            data_layout.addWidget(self.y_axis_list)

            # Selected columns display (read-only)
            selected_layout = QHBoxLayout()
            selected_layout.addWidget(QLabel("Selected:"))
            self.selected_columns_display = QLineEdit()
            self.selected_columns_display.setReadOnly(True)
            self.selected_columns_display.setPlaceholderText("No columns selected")
            selected_layout.addWidget(self.selected_columns_display)

            # Clear All button
            clear_all_btn = QPushButton("Clear All")
            clear_all_btn.setMaximumWidth(80)
            clear_all_btn.clicked.connect(lambda: self.clear_y_axis_selection())
            selected_layout.addWidget(clear_all_btn)
            data_layout.addLayout(selected_layout)

            # Select All button
            select_all_layout = QHBoxLayout()
            select_all_visible_btn = QPushButton("Select All Visible")
            select_all_visible_btn.clicked.connect(lambda: self.select_all_visible_y_axis())
            select_all_layout.addWidget(select_all_visible_btn)
            select_all_layout.addStretch()
            data_layout.addLayout(select_all_layout)

            # Update display initially
            self.update_selected_columns_display()

            layout.addWidget(data_group)

            # Chart Customization
            custom_group = QGroupBox("Chart Customization")
            custom_layout = QVBoxLayout(custom_group)

            # Title
            custom_layout.addWidget(QLabel("Chart Title:"))
            self.chart_title_input = QLineEdit(self.chart_settings['title'])
            custom_layout.addWidget(self.chart_title_input)

            # Size
            size_layout = QHBoxLayout()
            size_layout.addWidget(QLabel("Width:"))
            self.chart_width_spin = QComboBox()
            self.chart_width_spin.addItems(["8", "10", "12", "14", "16", "20"])
            self.chart_width_spin.setCurrentText(self.chart_settings['width'])
            self.chart_width_spin.setEditable(True)
            size_layout.addWidget(self.chart_width_spin)

            size_layout.addWidget(QLabel("Height:"))
            self.chart_height_spin = QComboBox()
            self.chart_height_spin.addItems(["6", "8", "10", "12", "14"])
            self.chart_height_spin.setCurrentText(self.chart_settings['height'])
            self.chart_height_spin.setEditable(True)
            size_layout.addWidget(self.chart_height_spin)

            size_layout.addWidget(QLabel("(inches)"))
            custom_layout.addLayout(size_layout)

            # Font sizes
            font_layout = QHBoxLayout()
            font_layout.addWidget(QLabel("Title Font:"))
            self.title_font_spin = QComboBox()
            self.title_font_spin.addItems(["12", "14", "16", "18", "20", "24"])
            self.title_font_spin.setCurrentText(self.chart_settings['title_font'])
            self.title_font_spin.setEditable(True)
            font_layout.addWidget(self.title_font_spin)

            font_layout.addWidget(QLabel("Label Font:"))
            self.label_font_spin = QComboBox()
            self.label_font_spin.addItems(["8", "10", "12", "14", "16"])
            self.label_font_spin.setCurrentText(self.chart_settings['label_font'])
            self.label_font_spin.setEditable(True)
            font_layout.addWidget(self.label_font_spin)

            font_layout.addWidget(QLabel("Legend Font:"))
            self.legend_font_spin = QComboBox()
            self.legend_font_spin.addItems(["8", "10", "12", "14"])
            self.legend_font_spin.setCurrentText(self.chart_settings['legend_font'])
            self.legend_font_spin.setEditable(True)
            font_layout.addWidget(self.legend_font_spin)

            custom_layout.addLayout(font_layout)

            # Grid and Legend
            options_layout = QHBoxLayout()
            self.show_grid_cb = QCheckBox("Show Grid")
            self.show_grid_cb.setChecked(self.chart_settings['show_grid'])
            options_layout.addWidget(self.show_grid_cb)

            self.show_legend_cb = QCheckBox("Show Legend")
            self.show_legend_cb.setChecked(self.chart_settings['show_legend'])
            options_layout.addWidget(self.show_legend_cb)

            self.tight_layout_cb = QCheckBox("Tight Layout")
            self.tight_layout_cb.setChecked(self.chart_settings['tight_layout'])
            self.tight_layout_cb.setToolTip("Automatically adjust subplot params for better fit")
            options_layout.addWidget(self.tight_layout_cb)

            custom_layout.addLayout(options_layout)

            layout.addWidget(custom_group)

            # Buttons
            button_layout = QHBoxLayout()

            create_chart_btn = QPushButton("Create Chart")
            create_chart_btn.clicked.connect(lambda: self.create_chart_from_dialog(dialog))
            create_chart_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-weight: bold;")
            button_layout.addWidget(create_chart_btn)

            create_table_btn = QPushButton("Create Table")
            create_table_btn.clicked.connect(lambda: self.create_table_from_chart_dialog(dialog))
            create_table_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 8px; font-weight: bold;")
            button_layout.addWidget(create_table_btn)

            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.close)  # Use close() instead of reject()
            close_btn.setStyleSheet("background-color: #f44336; color: white; padding: 8px;")
            close_btn.setToolTip("Close this dialog (created charts/tables remain open)")
            button_layout.addWidget(close_btn)

            layout.addLayout(button_layout)

            # CRITICAL: Use show() instead of exec_() to make dialog NON-MODAL
            # This allows interaction with created charts and tables while dialog stays open
            dialog.setWindowFlags(Qt.Window)  # Make it a top-level window
            dialog.show()
            dialog.raise_()
            dialog.activateWindow()

            # Keep reference to prevent garbage collection
            if not hasattr(self, 'chart_dialogs'):
                self.chart_dialogs = []
            self.chart_dialogs.append(dialog)
            dialog.destroyed.connect(
                lambda: self.chart_dialogs.remove(dialog) if dialog in self.chart_dialogs else None)

        def populate_chart_y_axis_list(self, headers: List[str], filter_text: str = ""):
            """Populate Y-axis list with optional filtering

            Args:
                headers: List of all column headers
                filter_text: Filter string (supports AND/OR logic)
            """
            # Check if widget exists and is valid
            if not hasattr(self, 'y_axis_list'):
                return

            try:
                _ = self.y_axis_list.isVisible()
            except RuntimeError:
                # Widget has been deleted
                return

            # Clear existing items
            self.y_axis_list.clear()

            # Save current selection state
            previously_selected_indices = []
            if hasattr(self, 'chart_settings') and 'y_axis_indices' in self.chart_settings:
                previously_selected_indices = self.chart_settings['y_axis_indices']

            visible_count = 0

            for col_index, header in self.all_y_axis_columns:
                # Check if this column matches the filter
                should_show = True

                if filter_text:
                    column_name = header.lower()

                    # Parse filter text for mixed AND/OR logic
                    or_groups = [group.strip() for group in filter_text.split(',') if group.strip()]

                    matches_any_group = False
                    for or_group in or_groups:
                        if '+' in or_group:
                            # AND logic: column must contain ALL terms
                            and_terms = [term.strip().lower() for term in or_group.split('+') if term.strip()]
                            if all(term in column_name for term in and_terms):
                                matches_any_group = True
                                break
                        else:
                            # Simple term: column must contain this term
                            if or_group.lower() in column_name:
                                matches_any_group = True
                                break

                    should_show = matches_any_group

                # Add item if it passes the filter
                if should_show:
                    item = QTreeWidgetItem([header])
                    item.setData(0, Qt.UserRole, col_index)
                    self.y_axis_list.addTopLevelItem(item)
                    visible_count += 1

                    # Restore selection if this column was previously selected
                    if col_index in previously_selected_indices:
                        item.setSelected(True)

            # Update count displays
            total_keywords = len(self.all_y_axis_columns)

            if filter_text:
                # Show filter status
                filter_status = QLabel(f"Showing {visible_count} of {total_keywords} columns")
                filter_status.setStyleSheet("color: #2196F3; font-size: 10px;")
                # Note: This label would need to be added to layout dynamically
                # For simplicity, we'll just update the count

            # Update selection count
            self.update_chart_y_axis_selection_count()

        def filter_chart_y_axis_columns(self, headers: List[str]):
            """Filter Y-axis columns based on filter input (real-time)

            Args:
                headers: List of all column headers
            """
            filter_text = self.chart_y_filter_input.text().strip()
            self.populate_chart_y_axis_list(headers, filter_text)

        def update_chart_y_axis_selection_count(self):
            """Update the selected column count label"""
            # Check if widgets still exist and are valid
            if not hasattr(self, 'y_axis_list'):
                return

            try:
                _ = self.y_axis_list.isVisible()
            except RuntimeError:
                # Widget deleted
                return

            if not hasattr(self, 'y_axis_selected_count_label'):
                return

            try:
                _ = self.y_axis_selected_count_label.isVisible()
            except RuntimeError:
                return

            selected_items = self.y_axis_list.selectedItems()
            count = len(selected_items)

            if count == 0:
                self.y_axis_selected_count_label.setText("(0 selected)")
                self.y_axis_selected_count_label.setStyleSheet("color: #999; font-weight: normal;")
            elif count == 1:
                self.y_axis_selected_count_label.setText("(1 selected)")
                self.y_axis_selected_count_label.setStyleSheet("color: #2196F3; font-weight: bold;")
            else:
                self.y_axis_selected_count_label.setText(f"({count} selected)")
                self.y_axis_selected_count_label.setStyleSheet("color: #2196F3; font-weight: bold;")

            # Also update the selected columns display
            self.update_selected_columns_display()

        def select_all_visible_y_axis(self):
            """Select all visible Y-axis columns"""
            for i in range(self.y_axis_list.topLevelItemCount()):
                item = self.y_axis_list.topLevelItem(i)
                item.setSelected(True)

            self.update_chart_y_axis_selection_count()

        def clear_y_axis_selection(self):
            """Clear all Y-axis column selections"""
            if hasattr(self, 'y_axis_list'):
                self.y_axis_list.clearSelection()
                self.selected_columns_display.clear()
                self.update_chart_y_axis_selection_count()

        def truncate_label_from_start(self, label: str, max_length: int = 40) -> str:
            """Truncate label from the beginning if too long

            Args:
                label: Original label text
                max_length: Maximum length to keep

            Returns:
                Truncated label with "..." prefix if needed

            Examples:
                "03_net-01_V2_SDC_T4_B6_spacing_20_0_short_care_r10_hold_fix_clk_lvt-fe00_te06_pv00"
                becomes "...lvt-fe00_te06_pv00"
            """
            if len(label) <= max_length:
                return label

            # Keep the last max_length characters
            truncated = label[-(max_length-3):]  # -3 for "..."
            return f"...{truncated}"

        def update_selected_columns_display(self):
            """Update the display of selected Y-axis columns"""
            # Check if widget exists AND is still valid (not deleted)
            if not hasattr(self, 'selected_columns_display'):
                return

            # CRITICAL: Check if the C++ object still exists
            try:
                # Try to access a property to check if widget is still valid
                _ = self.selected_columns_display.isVisible()
            except RuntimeError:
                # Widget has been deleted, skip update
                return

            # Also check y_axis_list validity
            if not hasattr(self, 'y_axis_list'):
                return

            try:
                _ = self.y_axis_list.isVisible()
            except RuntimeError:
                return

            selected_items = self.y_axis_list.selectedItems()

            if selected_items:
                headers = self.generate_dynamic_headers()
                selected_names = []
                for item in selected_items:
                    col_index = item.data(0, Qt.UserRole)
                    if col_index < len(headers):
                        selected_names.append(headers[col_index])

                # Display as comma-separated list
                display_text = ", ".join(selected_names)

                # Block signals to prevent recursion
                self.selected_columns_display.blockSignals(True)
                self.selected_columns_display.setText(display_text)
                self.selected_columns_display.blockSignals(False)
            else:
                self.selected_columns_display.blockSignals(True)
                self.selected_columns_display.clear()
                self.selected_columns_display.blockSignals(False)

        def clear_y_axis_selection(self):
            """Clear all Y-axis column selections"""
            if hasattr(self, 'y_axis_list'):
                self.y_axis_list.clearSelection()
                self.selected_columns_display.clear()

        def create_chart_from_dialog(self, dialog):
            """Create chart based on user selections"""
            import matplotlib.pyplot as plt
            import numpy as np

            # Get selections
            chart_type = self.chart_type_combo.currentText()
            x_column = self.x_axis_combo.currentIndex()

            selected_y_items = self.y_axis_list.selectedItems()
            if not selected_y_items:
                QMessageBox.warning(dialog, "No Y-axis Selected",
                                  "Please select at least one Y-axis column.")
                return

            y_columns = [item.data(0, Qt.UserRole) for item in selected_y_items]

            # Get customization options
            chart_title = self.chart_title_input.text()
            width = float(self.chart_width_spin.currentText())
            height = float(self.chart_height_spin.currentText())
            title_font = int(self.title_font_spin.currentText())
            label_font = int(self.label_font_spin.currentText())
            legend_font = int(self.legend_font_spin.currentText())
            show_grid = self.show_grid_cb.isChecked()
            show_legend = self.show_legend_cb.isChecked()
            tight_layout = self.tight_layout_cb.isChecked()

            # SAVE SETTINGS FOR NEXT TIME (ADD THIS BLOCK)
            self.chart_settings = {
                'chart_type': chart_type,
                'x_axis_index': x_column,
                'y_axis_indices': y_columns,
                'title': chart_title,
                'width': str(width),
                'height': str(height),
                'title_font': str(title_font),
                'label_font': str(label_font),
                'legend_font': str(legend_font),
                'show_grid': show_grid,
                'show_legend': show_legend,
                'tight_layout': tight_layout
            }

            # Extract data from SELECTED rows only
            headers = self.generate_dynamic_headers()
            selected_items = self.table.selectedItems()

            # Get unique selected rows (avoid duplicates from multi-column selection)
            selected_rows = []
            seen_rows = set()
            for item in selected_items:
                row_index = self.table.indexOfTopLevelItem(item)
                if row_index not in seen_rows:
                    seen_rows.add(row_index)
                    selected_rows.append(self.table.topLevelItem(row_index))

            if not selected_rows:
                QMessageBox.warning(dialog, "No Selection",
                                  "Please select rows in the table to chart.\n\n"
                                  "Use Ctrl+Click or Shift+Click to select multiple rows.")
                return

            x_data = []
            x_data_full = []  # Store full labels for tooltip
            y_data = {col: [] for col in y_columns}

            # Extract data from selected rows only
            for item in selected_rows:
                if item and not item.isHidden():
                    x_val = item.text(x_column)
                    x_data_full.append(x_val)  # Store full label

                    # TRUNCATE LONG LABELS from the beginning
                    x_val_display = self.truncate_label_from_start(x_val, max_length=35)
                    x_data.append(x_val_display)



                    for y_col in y_columns:
                        y_val_text = item.text(y_col)
                        try:
                            y_val = float(y_val_text.replace(',', '').replace('$', '').replace('%', ''))
                            y_data[y_col].append(y_val)
                        except (ValueError, AttributeError):
                            y_data[y_col].append(0)

            if not x_data:
                QMessageBox.warning(dialog, "No Data",
                                  "Selected rows contain no valid data to chart.")
                return

            # Create figure
            fig, ax = plt.subplots(figsize=(width, height))

            # Plot data
            for y_col in y_columns:
                y_label = headers[y_col]

                if chart_type == "Line Chart":
                    ax.plot(x_data, y_data[y_col], marker='o', label=y_label, linewidth=2)
                elif chart_type == "Bar Chart":
                    x_pos = np.arange(len(x_data))
                    offset = (y_columns.index(y_col) - len(y_columns)/2) * 0.8 / len(y_columns)
                    ax.bar(x_pos + offset, y_data[y_col], width=0.8/len(y_columns), label=y_label)
                    ax.set_xticks(x_pos)
                    ax.set_xticklabels(x_data)  # Remove rotation here, will be set below
                elif chart_type == "Scatter Plot":
                    ax.scatter(x_data, y_data[y_col], label=y_label, s=100, alpha=0.6)
                elif chart_type == "Horizontal Bar Chart":
                    y_pos = np.arange(len(x_data))
                    offset = (y_columns.index(y_col) - len(y_columns)/2) * 0.8 / len(y_columns)
                    ax.barh(y_pos + offset, y_data[y_col], height=0.8/len(y_columns), label=y_label)
                    ax.set_yticks(y_pos)
                    ax.set_yticklabels(x_data)  # Y-axis doesn't need rotation for horizontal bars
                elif chart_type == "Area Chart":
                    ax.fill_between(range(len(x_data)), y_data[y_col], alpha=0.5, label=y_label)
                    ax.plot(x_data, y_data[y_col], linewidth=2)

            # Customization
            ax.set_title(chart_title, fontsize=title_font, fontweight='bold')
            ax.set_xlabel(headers[x_column], fontsize=label_font)

            # Create Y-axis label from selected columns
            y_labels = [headers[col] for col in y_columns]
            if len(y_labels) == 1:
                y_axis_label = y_labels[0]
            else:
                y_axis_label = "Value"  # Default label for multiple columns

            ax.set_ylabel(y_axis_label, fontsize=label_font)

            # Rotate X-axis labels to 45 degrees for all chart types except horizontal bar
            if chart_type != "Horizontal Bar Chart":
                plt.setp(ax.get_xticklabels(), rotation=45, ha='right', rotation_mode='anchor')

                # ADD: Show full label on hover (matplotlib limitation - add as title hint)
                # Create a mapping of truncated to full labels for reference
                if len(x_data) != len(x_data_full):
                    print("WARNING: Label count mismatch")
                else:
                    # Add subtitle with truncation info
                    if any('...' in label for label in x_data):
                        fig.text(0.5, 0.02,
                                'Note: Long labels are truncated with "..." prefix. ' +
                                'See selected rows in table for full names.',
                                ha='center', fontsize=8, style='italic', color='gray')

            if show_grid:
                ax.grid(True, alpha=0.3, linestyle='--')

            if show_legend and len(y_columns) > 1:
                ax.legend(fontsize=legend_font, loc='best')

            ax.tick_params(labelsize=label_font - 2)

            # Apply tight layout if enabled
            tight_layout = self.tight_layout_cb.isChecked()
            if tight_layout:
                plt.tight_layout()

            # Show chart with non-blocking mode so dialog stays interactive
            plt.show(block=False)

            # Force drawing to ensure chart appears immediately
            plt.pause(0.001)

            # Don't close dialog - it's now non-modal and user can create more charts/tables

        def create_table_from_chart_dialog(self, dialog):
            """Create summary table based on chart dialog selections"""
            # Get selections from chart dialog
            x_column = self.x_axis_combo.currentIndex()

            selected_y_items = self.y_axis_list.selectedItems()
            if not selected_y_items:
                QMessageBox.warning(dialog, "No Y-axis Selected",
                                  "Please select at least one Y-axis column.")
                return

            y_columns = [item.data(0, Qt.UserRole) for item in selected_y_items]

            # Get headers
            headers = self.generate_dynamic_headers()

            # Build selected column indices: x-axis + y-axis columns
            selected_column_indices = [x_column] + y_columns
            selected_column_names = [headers[idx] for idx in selected_column_indices if idx < len(headers)]

            # Get selected rows from main table
            selected_items = self.table.selectedItems()

            # Get unique selected rows (avoid duplicates from multi-column selection)
            selected_rows = []
            seen_rows = set()
            for item in selected_items:
                row_index = self.table.indexOfTopLevelItem(item)
                if row_index not in seen_rows:
                    seen_rows.add(row_index)
                    selected_rows.append(self.table.topLevelItem(row_index))

            if not selected_rows:
                QMessageBox.warning(dialog, "No Selection",
                                  "Please select rows in the main table first.\n\n"
                                  "Use Ctrl+Click or Shift+Click to select multiple rows.")
                return

            # Create table window
            from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeWidget

            # CRITICAL: Create with NO parent for TRUE independence (like matplotlib charts)
            # This ensures the table window works independently from main window and dialog
            table_window = QMainWindow()
            table_window.setWindowTitle(f"Summary Table - {len(selected_column_names)} columns, {len(selected_rows)} rows")
            table_window.setGeometry(300, 300, 1200, 800)

            # Use Qt.Window flag for independent top-level window
            table_window.setWindowFlags(Qt.Window)
            table_window.setAttribute(Qt.WA_DeleteOnClose, True)

            # Track window to prevent garbage collection
            self.table_windows.append(table_window)
            table_window.destroyed.connect(
                lambda: self.table_windows.remove(table_window) if table_window in self.table_windows else None)

            central_widget = QWidget()
            table_window.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)

            # Create table
            summary_table = QTreeWidget()
            run_info_headers = ["User", "Block", "DK Ver/Tag", "Run Ver", "Job", "Task"]
            summary_table.setHeaderLabels(run_info_headers + selected_column_names)
            summary_table.setAlternatingRowColors(True)

            for i in range(len(run_info_headers)):
                summary_table.setColumnWidth(i, 120)

            # Populate table

            for item in selected_rows:
                user = item.text(Columns.USER)
                block = item.text(Columns.BLOCK)
                dk_ver_tag = item.text(Columns.DK_VER_TAG)
                run_version = item.text(Columns.RUN_VERSION)
                job = item.text(Columns.JOB)
                task = item.text(Columns.TASK)

                row_data = [user, block, dk_ver_tag, run_version, job, task]

                # Add selected column values (x-axis + y-axis)
                for col_idx in selected_column_indices:
                    if col_idx < item.columnCount():
                        value = item.text(col_idx)
                        row_data.append(value)
                    else:
                        row_data.append("-")

                QTreeWidgetItem(summary_table, row_data)

            # Auto-resize columns to fit content
            for i in range(summary_table.columnCount()):
                summary_table.resizeColumnToContents(i)
                # Add padding for keyword columns (after path columns)
                if i >= len(run_info_headers):
                    current_width = summary_table.columnWidth(i)
                    summary_table.setColumnWidth(i, current_width + 20)

            layout.addWidget(summary_table)

            # Buttons
            btn_layout = QHBoxLayout()
            export_btn = QPushButton("Export to CSV")
            export_btn.clicked.connect(lambda: self.export_summary_to_csv(summary_table, selected_column_names))
            btn_layout.addWidget(export_btn)
            btn_layout.addStretch()
            layout.addLayout(btn_layout)

            # Show and raise window
            table_window.show()
            table_window.raise_()
            table_window.activateWindow()

            # Process events to ensure window is displayed
            QApplication.processEvents()

            # Update status bar
            self.status_bar.showMessage(
                f"Created summary table with {len(selected_column_names)} columns and {len(selected_rows)} rows from chart dialog selection")

            # Don't close dialog - it's now non-modal and fully interactive alongside the table

        def create_chart(self, items, column_name: str, chart_type: str, table=None, chart_index: int = 0):
            """Create a chart for the specified column"""
            dynamic_headers = self.generate_dynamic_headers()

            # Find column index
            column_index = None
            for i, header in enumerate(dynamic_headers):
                if header == column_name:
                    column_index = i
                    break

            if column_index is None:
                return

            # Extract data
            labels = []
            values = []

            for item in items:
                # Build label from path components
                user = item.text(Columns.USER)
                block = item.text(Columns.BLOCK)
                dk_ver_tag = item.text(Columns.DK_VER_TAG)
                run_version = item.text(Columns.RUN_VERSION)
                job = item.text(Columns.JOB)
                task = item.text(Columns.TASK)

                label = f"{user}/{block}/{dk_ver_tag}/{run_version}/{job}/{task}"
                labels.append(label)

                # Extract value
                value_text = item.text(column_index)
                try:
                    if value_text != "-" and value_text.strip():
                        value = float(value_text)
                    else:
                        value = 0
                except ValueError:
                    value = 0
                values.append(value)

            # Create chart window
            from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

            chart_window = QMainWindow()
            chart_window.setWindowTitle(f"{chart_type} - {column_name}")
            chart_window.setGeometry(300 + (chart_index * 50) % 200,
                                    300 + (chart_index * 50) % 200,
                                    1000, 700)

            chart_window.setWindowFlags(Qt.Window)
            chart_window.setAttribute(Qt.WA_DeleteOnClose, True)

            self.chart_windows.append(chart_window)
            chart_window.destroyed.connect(
                lambda: self.chart_windows.remove(chart_window) if chart_window in self.chart_windows else None)

            central_widget = QWidget()
            chart_window.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)

            # Create matplotlib figure
            fig = Figure(figsize=(14, 8))
            canvas = FigureCanvas(fig)
            layout.addWidget(canvas)

            fig.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.25)

            ax = fig.add_subplot(111)

            # Create chart based on type
            if chart_type == "Bar Chart":
                bars = ax.bar(range(len(labels)), values)
                ax.set_xticks(range(len(labels)))

                short_labels = []
                for label in labels:
                    parts = label.split('/')
                    if len(parts) >= 6:
                        short_label = f"{parts[0]}/{parts[1]}/{parts[5]}"
                    else:
                        short_label = label
                    short_labels.append(short_label)

                ax.set_xticklabels(short_labels, rotation=45, ha='right', fontsize=9)
                ax.set_ylabel(column_name, fontsize=12)
                ax.set_title(f"{column_name} Comparison", fontsize=14, pad=20)

                for bar, value in zip(bars, values):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{value:.2f}', ha='center', va='bottom')

            elif chart_type == "Line Chart":
                ax.plot(range(len(labels)), values, marker='o', linewidth=2, markersize=6)
                ax.set_xticks(range(len(labels)))

                short_labels = []
                for label in labels:
                    parts = label.split('/')
                    if len(parts) >= 6:
                        short_label = f"{parts[0]}/{parts[1]}/{parts[5]}"
                    else:
                        short_label = label
                    short_labels.append(short_label)

                ax.set_xticklabels(short_labels, rotation=45, ha='right', fontsize=9)
                ax.set_ylabel(column_name, fontsize=12)
                ax.set_title(f"{column_name} Trend", fontsize=14, pad=20)
                ax.grid(True, alpha=0.3)

            elif chart_type == "Scatter Plot":
                ax.scatter(range(len(labels)), values, s=100, alpha=0.7)
                ax.set_xticks(range(len(labels)))

                short_labels = []
                for label in labels:
                    parts = label.split('/')
                    if len(parts) >= 6:
                        short_label = f"{parts[0]}/{parts[1]}/{parts[5]}"
                    else:
                        short_label = label
                    short_labels.append(short_label)

                ax.set_xticklabels(short_labels, rotation=45, ha='right', fontsize=9)
                ax.set_ylabel(column_name, fontsize=12)
                ax.set_title(f"{column_name} Distribution", fontsize=14, pad=20)
                ax.grid(True, alpha=0.3)

            fig.tight_layout()
            canvas.draw()

            # Add save button
            save_btn = QPushButton("Save Chart")
            save_btn.clicked.connect(lambda: self.save_chart(fig, column_name, chart_type))
            layout.addWidget(save_btn)

            chart_window.show()
            chart_window.raise_()
            canvas.draw()
            canvas.flush_events()
            QApplication.processEvents()

        def save_chart(self, fig, column_name: str, chart_type: str):
            """Save chart to file"""
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save Chart",
                f"{column_name}_{chart_type.lower().replace(' ', '_')}.png",
                "PNG files (*.png);;PDF files (*.pdf);;All files (*.*)"
            )

            if filename:
                try:
                    fig.savefig(filename, dpi=300, bbox_inches='tight')
                    self.statusBar().showMessage(f"Chart saved to {filename}")
                except Exception as e:
                    QMessageBox.critical(self, "Save Error", f"Error saving chart: {str(e)}")

        def show_table_dialog(self, table):
            """Show dialog to create summary table"""
            selected_items = table.selectedItems()
            all_items = []
            for i in range(table.topLevelItemCount()):
                item = table.topLevelItem(i)
                if not item.isHidden():
                    all_items.append(item)

            if not all_items:
                self.status_bar.showMessage("No data available for table creation.")
                return

            # Create dialog similar to chart dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Create Summary Table")
            dialog.setModal(True)
            dialog.resize(500, 400)

            layout = QVBoxLayout(dialog)

            label = QLabel("Select columns to include in summary table:")
            layout.addWidget(label)

            # Scroll area for columns
            scroll_area = QScrollArea()
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)

            dynamic_headers = self.generate_dynamic_headers()
            keyword_headers = dynamic_headers[Columns.PATH_COLUMN_COUNT:]

            # Check data availability
            column_data_status = {}
            for i, header in enumerate(keyword_headers):
                column_index = i + Columns.PATH_COLUMN_COUNT
                valid_count = 0
                for item in all_items:
                    value_text = item.text(column_index)
                    if value_text != "-" and value_text.strip():
                        valid_count += 1
                column_data_status[header] = (valid_count, len(all_items))

            column_checkboxes = {}
            for header in keyword_headers:
                valid_count, total_count = column_data_status.get(header, (0, 0))
                if valid_count > 0:
                    checkbox = QCheckBox(f"{header} ({valid_count}/{total_count} valid)")
                else:
                    checkbox = QCheckBox(f"{header} (no data)")
                    checkbox.setEnabled(False)

                column_checkboxes[header] = checkbox
                scroll_layout.addWidget(checkbox)

            scroll_area.setWidget(scroll_widget)
            scroll_area.setWidgetResizable(True)
            scroll_area.setMaximumHeight(200)
            layout.addWidget(scroll_area)

            # Select/Clear buttons
            button_layout = QHBoxLayout()
            select_all_btn = QPushButton("Select All")
            clear_all_btn = QPushButton("Clear All")

            select_all_btn.clicked.connect(lambda: [cb.setChecked(True) for cb in column_checkboxes.values() if cb.isEnabled()])
            clear_all_btn.clicked.connect(lambda: [cb.setChecked(False) for cb in column_checkboxes.values()])

            button_layout.addWidget(select_all_btn)
            button_layout.addWidget(clear_all_btn)
            button_layout.addStretch()
            layout.addLayout(button_layout)

            # Item selection
            item_label = QLabel("Items to include:")
            layout.addWidget(item_label)

            item_combo = QComboBox()
            if selected_items:
                item_combo.addItems([
                    f"Selected items ({len(selected_items)})",
                    f"All visible items ({len(all_items)})"
                ])
            else:
                item_combo.addItems([f"All visible items ({len(all_items)})"])
            layout.addWidget(item_combo)

            # Dialog buttons
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)

            if dialog.exec_() == QDialog.Accepted:
                selected_columns = [col for col, cb in column_checkboxes.items()
                                  if cb.isChecked() and cb.isEnabled()]

                if not selected_columns:
                    QMessageBox.warning(self, "No Columns", "Please select at least one column.")
                    return

                items_to_use = selected_items if (selected_items and
                                                 item_combo.currentText().startswith("Selected")) else all_items

                self.create_summary_table(items_to_use, selected_columns, table)

        def create_summary_table(self, items, selected_columns, table=None):
            """Create summary table window"""
            from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeWidget

            table_window = QMainWindow()
            table_window.setWindowTitle(f"Summary Table - {len(selected_columns)} columns, {len(items)} items")
            table_window.setGeometry(300, 300, 1200, 800)

            # CRITICAL: Set window flags to keep window alive and track it
            table_window.setWindowFlags(Qt.Window)
            table_window.setAttribute(Qt.WA_DeleteOnClose, True)

            # Track window to prevent garbage collection
            self.table_windows.append(table_window)
            table_window.destroyed.connect(
                lambda: self.table_windows.remove(table_window) if table_window in self.table_windows else None)

            central_widget = QWidget()
            table_window.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)

            # Create table
            summary_table = QTreeWidget()
            run_info_headers = ["User", "Block", "DK Ver/Tag", "Run Ver", "Job", "Task"]
            summary_table.setHeaderLabels(run_info_headers + selected_columns)
            summary_table.setAlternatingRowColors(True)

            for i in range(len(run_info_headers)):
                summary_table.setColumnWidth(i, 120)

            # Populate
            dynamic_headers = self.generate_dynamic_headers()


            for item in items:
                user = item.text(Columns.USER)
                block = item.text(Columns.BLOCK)
                dk_ver_tag = item.text(Columns.DK_VER_TAG)
                run_version = item.text(Columns.RUN_VERSION)
                job = item.text(Columns.JOB)
                task = item.text(Columns.TASK)

                row_data = [user, block, dk_ver_tag, run_version, job, task]

                # Add keyword values
                for col_name in selected_columns:
                    col_idx = dynamic_headers.index(col_name) if col_name in dynamic_headers else -1
                    if col_idx >= 0:
                        value = item.text(col_idx)
                        row_data.append(value)
                        # DEBUG: Show first few values
                        if len(row_data) <= 8:
                            pass
                    else:
                        row_data.append("-")

                QTreeWidgetItem(summary_table, row_data)

            # Auto-resize columns to fit content
            for i in range(summary_table.columnCount()):
                summary_table.resizeColumnToContents(i)
                # Add padding for keyword columns (after path columns)
                if i >= len(run_info_headers):
                    current_width = summary_table.columnWidth(i)
                    summary_table.setColumnWidth(i, current_width + 20)

            layout.addWidget(summary_table)

            # Buttons
            btn_layout = QHBoxLayout()
            export_btn = QPushButton("Export to CSV")
            export_btn.clicked.connect(lambda: self.export_summary_to_csv(summary_table, selected_columns))
            btn_layout.addWidget(export_btn)
            btn_layout.addStretch()
            layout.addLayout(btn_layout)

            # Show and raise window
            table_window.show()
            table_window.raise_()
            table_window.activateWindow()

            # Update status bar
            self.status_bar.showMessage(f"Created summary table with {len(selected_columns)} columns and {len(items)} items")

        def export_summary_to_csv(self, summary_table, selected_columns):
            """Export summary table to CSV"""
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Summary", "", "CSV files (*.csv)")

            if filename:
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    run_info_headers = ["User", "Block", "DK Ver/Tag", "Run Ver", "Job", "Task"]
                    writer.writerow(run_info_headers + selected_columns)

                    for i in range(summary_table.topLevelItemCount()):
                        item = summary_table.topLevelItem(i)
                        row = [item.text(j) for j in range(item.columnCount())]
                        writer.writerow(row)

                self.status_bar.showMessage(f"Exported to {filename}")

        def show_multi_select_dialog(self, filter_type: str, filter_name: str):
            """Show multi-select dialog for filter values"""
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Select {filter_name} Values")
            dialog.setModal(True)

            # Use larger size for task filter (5-pane layout)
            if filter_type == 'task':
                dialog.resize(1200, 700)
            else:
                dialog.resize(600, 500)

            layout = QVBoxLayout(dialog)

            # Add label
            label = QLabel(f"Select {filter_name} values to filter by:")
            layout.addWidget(label)

            # Create scroll area for checkboxes
            scroll_area = QScrollArea()
            scroll_widget = QWidget()

            # Get available values based on filter type
            if filter_type == 'status':
                # Get status values from table
                values = []
                for i in range(self.table.topLevelItemCount()):
                    item = self.table.topLevelItem(i)
                    status_text = item.text(Columns.STATUS)
                    if status_text and status_text not in values:
                        # Normalize status text
                        if status_text.endswith('%'):
                            status_text = StatusValues.COMPLETED
                        if status_text not in values:
                            values.append(status_text)
                values.sort()
                # Use vertical layout
                scroll_layout = QVBoxLayout(scroll_widget)
                checkboxes = {}
                for value in values:
                    checkbox = QCheckBox(value)
                    checkboxes[value] = checkbox
                    scroll_layout.addWidget(checkbox)

            elif filter_type == 'job':
                # Get job values from configuration
                values = []
                if hasattr(self.analyzer, 'config') and 'jobs' in self.analyzer.config:
                    values = list(self.analyzer.config['jobs'].keys())
                values.sort()
                # Use vertical layout
                scroll_layout = QVBoxLayout(scroll_widget)
                checkboxes = {}
                for value in values:
                    checkbox = QCheckBox(value)
                    checkboxes[value] = checkbox
                    scroll_layout.addWidget(checkbox)

            elif filter_type == 'task':
                # Special handling for tasks - organize by job categories in 5 panes
                scroll_layout = QHBoxLayout(scroll_widget)

                # Get all configured jobs and tasks
                configured_jobs = get_all_configured_jobs_and_tasks(self.analyzer.config)

                # Define job categories for each pane
                pane_categories = [
                    # Pane 1: Synthesis and verification
                    ['syn_dc', 'dft', 'ldrc_dc', 'lec_fm', 'sta_pt', 'sim'],
                    # Pane 2: Innovus APR
                    ['apr_inn'],
                    # Pane 3: ICC2 APR
                    ['apr_icc2'],
                    # Pane 4: Physical verification
                    ['pex', 'pv'],
                    # Pane 5: Power and bump
                    ['psi', 'bump']
                ]

                # Define pane titles
                pane_titles = [
                    "Synthesis & Verification & STA",
                    "Innovus APR",
                    "ICC2 APR",
                    "PEX & Physical Verification",
                    "Power/Signal Integrity & Bump"
                ]

                checkboxes = {}

                # Create 5 panes
                for pane_index, job_categories in enumerate(pane_categories):
                    pane_widget = QWidget()
                    pane_layout = QVBoxLayout(pane_widget)

                    # Add pane title
                    pane_title = QLabel(f"<b>{pane_titles[pane_index]}</b>")
                    pane_title.setAlignment(Qt.AlignCenter)
                    pane_layout.addWidget(pane_title)

                    # Create section for each job in this pane
                    for job_name in job_categories:
                        if job_name in configured_jobs:
                            tasks = configured_jobs[job_name]
                            if tasks:
                                # Create job group
                                job_group = QGroupBox(f"Job: {job_name}")
                                job_layout = QVBoxLayout(job_group)

                                # Add task checkboxes (preserve YAML order)
                                for task_name in tasks:
                                    checkbox = QCheckBox(task_name)
                                    checkboxes[task_name] = checkbox
                                    job_layout.addWidget(checkbox)

                                pane_layout.addWidget(job_group)

                    # Add stretch
                    pane_layout.addStretch()

                    # Add pane to main layout
                    scroll_layout.addWidget(pane_widget)

            else:
                # For other filter types (base_dir, user, block, etc.)
                values = self.path_components.get(filter_type, [])
                scroll_layout = QVBoxLayout(scroll_widget)
                checkboxes = {}
                for value in values:
                    checkbox = QCheckBox(value)
                    checkboxes[value] = checkbox
                    scroll_layout.addWidget(checkbox)

            # Add "Select All" and "Clear All" buttons
            button_layout = QHBoxLayout()
            select_all_btn = QPushButton("Select All")
            clear_all_btn = QPushButton("Clear All")

            def select_all():
                for checkbox in checkboxes.values():
                    checkbox.setChecked(True)

            def clear_all():
                for checkbox in checkboxes.values():
                    checkbox.setChecked(False)

            select_all_btn.clicked.connect(select_all)
            clear_all_btn.clicked.connect(clear_all)

            button_layout.addWidget(select_all_btn)
            button_layout.addWidget(clear_all_btn)
            button_layout.addStretch()
            scroll_layout.addLayout(button_layout)

            scroll_area.setWidget(scroll_widget)
            scroll_area.setWidgetResizable(True)
            layout.addWidget(scroll_area)

            # Add dialog buttons
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)

            # Show dialog
            if dialog.exec_() == QDialog.Accepted:
                # Get selected values
                selected_values = [value for value, checkbox in checkboxes.items()
                                 if checkbox.isChecked()]

                if selected_values:
                    # Update the corresponding combo box
                    combo_text = ", ".join(selected_values)
                    if filter_type == 'base_dir':
                        self.project_combo.setCurrentText(combo_text)
                    elif filter_type == 'top_name':
                        # Note: top_name is not used in current implementation
                        pass
                    elif filter_type == 'user':
                        self.top_name_combo.setCurrentText(combo_text)
                    elif filter_type == 'block':
                        self.block_combo.setCurrentText(combo_text)
                    elif filter_type == 'dk_ver_tag':
                        self.dk_ver_tag_combo.setCurrentText(combo_text)
                    elif filter_type == 'run_version':
                        self.run_version_combo.setCurrentText(combo_text)
                    elif filter_type == 'job':
                        self.job_combo.setCurrentText(combo_text)
                    elif filter_type == 'task':
                        self.task_combo.setCurrentText(combo_text)
                    elif filter_type == 'status':
                        self.status_combo.setCurrentText(combo_text)

                    # Apply filters
                    self.apply_filters()

else:
    HawkeyeDashboard = None
