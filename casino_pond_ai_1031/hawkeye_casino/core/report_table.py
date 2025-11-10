"""
Report Table Widget for Hawkeye

Displays keywords in a grouped vertical pivot-style table for better readability
when dealing with many keywords (e.g., STA timing, PV rules).
"""

import re
from typing import Dict, List, Optional, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QHeaderView, QAbstractItemView,
    QFileDialog, QMessageBox, QSplitter, QDialog, QTextEdit, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QBrush

from .keyword_parser import KeywordParser, KeywordGrouping, STAKeyword, PVKeyword, ViolationKeyword, GenericKeyword


class NaturalSortTableItem(QTableWidgetItem):
    """Custom QTableWidgetItem with natural (alphanumeric) sorting support

    Sorts numbers naturally: 1, 2, 11 instead of 1, 11, 2
    """

    def __lt__(self, other):
        """Override less-than comparison for natural sorting"""
        # Get text values
        self_text = self.text()
        other_text = other.text()

        # Handle special values
        if self_text == '-' and other_text == '-':
            return False
        if self_text == '-':
            return True  # '-' comes first
        if other_text == '-':
            return False

        # Try numeric comparison first
        try:
            return float(self_text) < float(other_text)
        except (ValueError, TypeError):
            pass

        # Use natural sort key comparison for alphanumeric strings
        return self._natural_sort_key(self_text) < self._natural_sort_key(other_text)

    @staticmethod
    def _natural_sort_key(text: str):
        """Generate natural sort key for alphanumeric sorting"""
        def atoi(s):
            return int(s) if s.isdigit() else s.lower()
        return [atoi(c) for c in re.split(r'(\d+)', str(text))]


class ReportTableWidget(QWidget):
    """
    Grouped report table view for displaying keywords vertically.
    Provides pivot-style layout with smart grouping by mode/corner/metric.
    """

    # Signal emitted when user wants to export data
    export_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parser = KeywordParser()
        self.current_run_data = {}
        self.current_headers = []
        self.keyword_groups = {}
        self.yaml_groups = set()  # Track all unique groups from YAML

        # Multi-run comparison state
        self.multiple_runs_data = {}  # {run_path: [tasks]}
        self.comparison_mode = "side-by-side"  # "side-by-side" or "pivot"

        self._init_ui()

    def _init_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Top toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        # Run info label
        self.run_info_label = QLabel("No run selected")
        self.run_info_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        toolbar.addWidget(self.run_info_label)

        toolbar.addStretch()

        # Category selector
        toolbar.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "STA Timing",
            "STA Violations",
            "STA VTH Ratio",
            "STA Cell Usage",
            "PV (DRC/LVS/PERC)",
            "APR Timing",
            "APR Congestion",
            "All Metrics"
        ])
        self.category_combo.currentTextChanged.connect(self._on_category_changed)
        toolbar.addWidget(self.category_combo)

        # View mode toggle button (for multi-run comparison)
        self.view_mode_btn = QPushButton("Switch to Pivot View")
        self.view_mode_btn.clicked.connect(self._toggle_view_mode)
        self.view_mode_btn.setVisible(False)  # Hidden by default, shown when multiple runs
        toolbar.addWidget(self.view_mode_btn)

        # Export button
        self.export_btn = QPushButton("Export to CSV")
        self.export_btn.clicked.connect(self._export_to_csv)
        toolbar.addWidget(self.export_btn)

        layout.addLayout(toolbar)

        # Splitter for multiple tables (can show STA + PV simultaneously)
        self.splitter = QSplitter(Qt.Vertical)
        layout.addWidget(self.splitter)

        # Create initial table widgets and add to splitter
        self.sta_table = self._create_table_widget("STA Timing Metrics")
        self.violation_table = self._create_table_widget("Violation Metrics")
        self.vth_table = self._create_table_widget("VTH Ratio")
        self.cell_usage_table = self._create_table_widget("Cell Usage")
        self.pv_drc_table = self._create_table_widget("DRC Results")
        self.pv_lvs_table = self._create_table_widget("LVS Results")
        self.pv_flipchip_table = self._create_table_widget("FlipChip Results")
        self.pv_perc_table = self._create_table_widget("PERC Results")
        self.apr_timing_table = self._create_table_widget("APR Timing Summary")
        self.apr_congestion_table = self._create_table_widget("APR Congestion")

        # Add all tables to splitter (will be hidden/shown as needed)
        self.splitter.addWidget(self.sta_table)
        self.splitter.addWidget(self.violation_table)
        self.splitter.addWidget(self.vth_table)
        self.splitter.addWidget(self.cell_usage_table)
        self.splitter.addWidget(self.pv_drc_table)
        self.splitter.addWidget(self.pv_lvs_table)
        self.splitter.addWidget(self.pv_flipchip_table)
        self.splitter.addWidget(self.pv_perc_table)
        self.splitter.addWidget(self.apr_timing_table)
        self.splitter.addWidget(self.apr_congestion_table)

        # Initially show STA timing (hide others)
        self._on_category_changed("STA Timing")

    def _create_table_widget(self, title: str) -> QTableWidget:
        """Create a configured table widget"""
        table = QTableWidget()
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setSortingEnabled(True)

        # Style
        table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                font-size: 9pt;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #e8e8e8;
                padding: 6px;
                border: 1px solid #c0c0c0;
                font-weight: bold;
            }
        """)

        return table

    def set_keyword_groups(self, keyword_groups: Dict[str, List[str]]):
        """Set keyword group mappings from YAML configuration"""
        self.keyword_groups = keyword_groups
        self.parser.keyword_groups = keyword_groups

        # Extract unique groups from YAML
        self.yaml_groups = set(keyword_groups.keys())

        # Debug
        print(f"[DEBUG] set_keyword_groups() called with {len(keyword_groups)} groups")
        for group_name, kw_list in keyword_groups.items():
            print(f"[DEBUG]   Group '{group_name}': {len(kw_list)} keywords")
            if kw_list:
                print(f"[DEBUG]     First 3: {kw_list[:3]}")

    def _group_to_category_name(self, group: str) -> str:
        """
        Convert YAML group name to display-friendly category name.

        Examples:
            sta_timing -> STA Timing
            pv_drc -> PV - DRC
            err/warn -> Errors/Warnings
        """
        # Handle special cases
        if group == 'err/warn':
            return "Errors/Warnings"

        # Split by underscore
        parts = group.split('_')

        # Handle pv_ prefix specially
        if parts[0] == 'pv' and len(parts) > 1:
            # pv_drc -> PV - DRC
            pv_type = parts[1].upper()
            return f"PV - {pv_type}"

        # Handle sta_ prefix
        if parts[0] == 'sta' and len(parts) > 1:
            # sta_timing -> STA Timing
            # sta_cell_usage -> STA Cell Usage
            rest = ' '.join(word.capitalize() for word in parts[1:])
            return f"STA {rest}"

        # Default: capitalize each part
        return ' '.join(word.capitalize() for word in parts)

    def _category_to_table_widget(self, category: str) -> Optional[QTableWidget]:
        """Map category name to its corresponding table widget"""
        # Normalize category for case-insensitive matching
        category_lower = category.lower()

        # STA timing categories (setup, hold, or general timing)
        if "sta" in category_lower and ("setup timing" in category_lower or "hold timing" in category_lower or category_lower == "sta timing"):
            return self.sta_table
        # STA violation categories (mttv, max_cap, noise)
        elif "sta" in category_lower and ("mttv" in category_lower or "max cap" in category_lower or "noise" in category_lower):
            return self.violation_table
        # STA VTH ratio
        elif "sta" in category_lower and "vth" in category_lower:
            return self.vth_table
        # STA Cell Usage
        elif "sta" in category_lower and "cell usage" in category_lower:
            return self.cell_usage_table
        # PV categories
        elif "pv" in category_lower and "drc" in category_lower:
            return self.pv_drc_table
        elif "pv" in category_lower and "lvs" in category_lower:
            return self.pv_lvs_table
        elif "pv" in category_lower and "flipchip" in category_lower:
            return self.pv_flipchip_table
        elif "pv" in category_lower and "perc" in category_lower:
            return self.pv_perc_table
        # APR categories
        elif "timing" in category_lower and "apr" not in category_lower.replace("sta", ""):
            return self.apr_timing_table
        elif "congestion" in category_lower:
            return self.apr_congestion_table

        return None

    def _category_to_populate_method(self, category: str):
        """Map category name to its populate method"""
        # Normalize category for case-insensitive matching
        category_lower = category.lower()

        # STA timing categories
        if "sta" in category_lower and "setup timing" in category_lower:
            return lambda: self._populate_sta_timing_table(filter_timing='s')
        elif "sta" in category_lower and "hold timing" in category_lower:
            return lambda: self._populate_sta_timing_table(filter_timing='h')
        elif "sta timing" in category_lower:
            return lambda: self._populate_sta_timing_table(filter_timing=None)  # Show both
        # STA violation categories
        elif "sta" in category_lower and "mttv" in category_lower:
            return lambda: self._populate_violation_table(filter_type='max_tran')
        elif "sta" in category_lower and "max cap" in category_lower:
            return lambda: self._populate_violation_table(filter_type='max_cap')
        elif "sta" in category_lower and "noise" in category_lower:
            return lambda: self._populate_violation_table(filter_type='noise')
        # STA other
        elif "sta" in category_lower and "vth" in category_lower:
            return self._populate_vth_table
        elif "sta" in category_lower and "cell usage" in category_lower:
            return self._populate_cell_usage_table
        # PV categories
        elif "pv" in category_lower and "drc" in category_lower:
            return self._populate_pv_drc_table
        elif "pv" in category_lower and "lvs" in category_lower:
            return self._populate_pv_lvs_table
        elif "pv" in category_lower and "flipchip" in category_lower:
            return self._populate_pv_flipchip_table
        elif "pv" in category_lower and "perc" in category_lower:
            return self._populate_pv_perc_table
        # APR categories
        elif "timing" in category_lower and "apr" not in category_lower.replace("sta", ""):
            return self._populate_apr_timing_table
        elif "congestion" in category_lower:
            return self._populate_apr_congestion_table

        return None

    def set_run_data(self, run_path: str, task_name: str, task_data: Dict[str, Any], headers: List[str]):
        """
        Set the current run data to display in report view.

        Args:
            run_path: Full path to run
            task_name: Task name (e.g., "sta_pt", "DRC")
            task_data: Task data dict with 'keywords' key
            headers: List of all available headers
        """
        # Extract keyword values from dicts
        raw_keywords = task_data.get('keywords', {})
        keywords_dict = {}
        for kw_name, kw_data in raw_keywords.items():
            # Handle both dict format and direct value format
            if isinstance(kw_data, dict):
                keywords_dict[kw_name] = kw_data.get('value', '-')
            else:
                keywords_dict[kw_name] = kw_data

        self.current_run_data = {
            'run_path': run_path,
            'task_name': task_name,
            'task_data': task_data,
            'keywords': keywords_dict,
            'is_combined': False
        }
        self.current_headers = headers

        # Update run info label
        short_path = run_path.split('/')[-3:] if '/' in run_path else run_path.split('\\')[-3:]
        self.run_info_label.setText(f"Run: {'/'.join(short_path)} | Task: {task_name}")

        # Update category combo based on task
        self._update_categories_for_task(task_name)

        # Refresh current view
        self._refresh_view()

    def set_combined_run_data(self, combined_tasks: List[Dict[str, Any]], headers: List[str]):
        """
        Set combined data from multiple selected tasks.

        Args:
            combined_tasks: List of dicts with 'run_path', 'task_name', 'task_data'
            headers: List of all available headers
        """
        # Check if multiple distinct runs are present
        unique_run_paths = list(set(task['run_path'] for task in combined_tasks))

        if len(unique_run_paths) > 1:
            # Multiple runs - enable comparison mode
            self._set_multiple_runs_mode(combined_tasks, unique_run_paths, headers)
            return

        # Single run - use original merging logic
        merged_keywords = {}
        task_names = []

        for task_info in combined_tasks:
            task_name = task_info['task_name']
            task_names.append(task_name)

            raw_keywords = task_info['task_data'].get('keywords', {})
            for kw_name, kw_data in raw_keywords.items():
                # Extract value
                if isinstance(kw_data, dict):
                    value = kw_data.get('value', '-')
                else:
                    value = kw_data

                # Prefix keyword with task name to avoid collisions
                prefixed_name = f"{task_name}_{kw_name}"
                merged_keywords[prefixed_name] = value

                # Also store unprefixed for backward compatibility
                if kw_name not in merged_keywords:
                    merged_keywords[kw_name] = value

        self.current_run_data = {
            'run_path': combined_tasks[0]['run_path'],
            'task_name': ', '.join(task_names),
            'task_data': {'keywords': merged_keywords},
            'keywords': merged_keywords,
            'is_combined': True,
            'combined_tasks': combined_tasks
        }
        self.current_headers = headers
        self.multiple_runs_data = {}  # Clear multi-run state
        self.view_mode_btn.setVisible(False)  # Hide toggle button

        # Update run info label
        run_path = combined_tasks[0]['run_path']
        short_path = run_path.split('/')[-3:] if '/' in run_path else run_path.split('\\')[-3:]
        self.run_info_label.setText(
            f"Run: {'/'.join(short_path)} | Tasks: {', '.join(task_names)} ({len(combined_tasks)} selected)"
        )

        # Update category combo based on combined tasks
        self._update_categories_for_combined_tasks(task_names)

        # Refresh current view
        self._refresh_view()

    def _set_multiple_runs_mode(self, combined_tasks: List[Dict[str, Any]], unique_run_paths: List[str], headers: List[str]):
        """
        Set up multiple runs comparison mode.

        Args:
            combined_tasks: List of all tasks from all runs
            unique_run_paths: List of unique run paths
            headers: List of all available headers
        """
        # Group tasks by run
        runs_grouped = {}
        for task in combined_tasks:
            run_path = task['run_path']
            if run_path not in runs_grouped:
                runs_grouped[run_path] = []
            runs_grouped[run_path].append(task)

        self.multiple_runs_data = runs_grouped
        self.current_headers = headers

        # Merge keywords from all runs for category detection
        all_keywords = {}
        for run_path, tasks in runs_grouped.items():
            for task in tasks:
                raw_keywords = task['task_data'].get('keywords', {})
                for kw_name, kw_data in raw_keywords.items():
                    if isinstance(kw_data, dict):
                        value = kw_data.get('value', '-')
                    else:
                        value = kw_data
                    all_keywords[kw_name] = value

        self.current_run_data = {
            'keywords': all_keywords,
            'is_multi_run': True,
            'run_count': len(unique_run_paths)
        }

        # Show toggle button
        self.view_mode_btn.setVisible(True)
        self._update_toggle_button_text()

        # Update run info label
        run_names = [path.split('/')[-1] if '/' in path else path.split('\\')[-1] for path in unique_run_paths]
        self.run_info_label.setText(
            f"{len(unique_run_paths)} Runs: {', '.join(run_names[:3])}{'...' if len(run_names) > 3 else ''}"
        )

        # Update categories based on all keywords
        self._update_categories_for_combined_tasks([task['task_name'] for task in combined_tasks])

        # Refresh view
        self._refresh_view()

    def _toggle_view_mode(self):
        """Toggle between side-by-side and pivot view modes"""
        if self.comparison_mode == "side-by-side":
            self.comparison_mode = "pivot"
        else:
            self.comparison_mode = "side-by-side"

        self._update_toggle_button_text()
        self._refresh_view()

    def _update_toggle_button_text(self):
        """Update toggle button text based on current mode"""
        if self.comparison_mode == "side-by-side":
            self.view_mode_btn.setText("Switch to Side-by-Side View")
        else:
            self.view_mode_btn.setText("Switch to Pivot View")

    def _update_categories_for_task(self, task_name: str):
        """Update category dropdown based on single task type - dynamically from YAML groups"""
        # Extract groups present in current keywords
        keywords = self.current_run_data.get('keywords', {})
        categories = self._extract_categories_from_keywords(keywords)

        # Update combo box
        current_category = self.category_combo.currentText()

        # Block signals to prevent multiple triggers
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItems(categories)

        # Try to restore previous selection if still available, otherwise select first
        if current_category in categories:
            self.category_combo.setCurrentText(current_category)
        elif categories:
            self.category_combo.setCurrentIndex(0)

        # Unblock signals
        self.category_combo.blockSignals(False)

    def _extract_categories_from_keywords(self, keywords: Dict[str, Any]) -> List[str]:
        """
        Extract available categories from keywords by parsing them and determining their groups.

        Args:
            keywords: Dict of keyword_name -> value

        Returns:
            List of category display names
        """
        present_groups = set()

        # Debug: print what we're working with
        print(f"[DEBUG] Extracting categories from {len(keywords)} keywords")
        print(f"[DEBUG] Available groups in keyword_groups: {list(self.keyword_groups.keys())}")

        # For each keyword, determine its group by:
        # 1. First check if it exists in YAML keyword_groups (exact match)
        # 2. If not found, use the keyword parser to infer the group
        for kw_name in keywords.keys():
            found_group = None

            # Try exact match in YAML groups first
            for group_name, group_keywords in self.keyword_groups.items():
                if kw_name in group_keywords:
                    present_groups.add(group_name)
                    found_group = group_name
                    break

            # If not found in YAML, use parser to infer group
            if not found_group:
                parsed = self.parser.parse_keyword(kw_name, "")
                if parsed:
                    inferred_group = self._infer_group_from_parsed_keyword(parsed)
                    if inferred_group:
                        present_groups.add(inferred_group)
                        found_group = inferred_group
                        print(f"[DEBUG] Keyword '{kw_name}' -> inferred group '{found_group}' via parser")
                    else:
                        print(f"[DEBUG] Keyword '{kw_name}' -> parsed but no group inferred")
                else:
                    print(f"[DEBUG] Keyword '{kw_name}' -> NOT FOUND in any group and not parseable")
            else:
                print(f"[DEBUG] Keyword '{kw_name}' -> group '{found_group}' (YAML match)")

        print(f"[DEBUG] Present groups: {present_groups}")

        # Convert groups to category names
        categories = []
        for group in sorted(present_groups):
            category_name = self._group_to_category_name(group)
            categories.append(category_name)
            print(f"[DEBUG] Group '{group}' -> category '{category_name}'")

        # Always add "All Metrics" option
        if categories:
            categories.append("All Metrics")
        else:
            categories = ["All Metrics"]

        print(f"[DEBUG] Final categories: {categories}")
        return categories

    def _infer_group_from_parsed_keyword(self, parsed: Any) -> Optional[str]:
        """
        Infer the YAML group name from a parsed keyword object.

        Args:
            parsed: Parsed keyword object (STAKeyword, PVKeyword, ViolationKeyword, GenericKeyword)

        Returns:
            Group name string or None
        """
        from .keyword_parser import STAKeyword, PVKeyword, ViolationKeyword, GenericKeyword, VTHKeyword, CellUsageKeyword

        if isinstance(parsed, STAKeyword):
            # Differentiate between setup and hold timing
            if parsed.timing_type == 's':
                return "sta_setup_timing"
            elif parsed.timing_type == 'h':
                return "sta_hold_timing"
            else:
                return "sta_timing"  # Fallback
        elif isinstance(parsed, ViolationKeyword):
            # Differentiate between violation types
            if parsed.violation_type == 'max_tran':
                return "sta_mttv"
            elif parsed.violation_type == 'max_cap':
                return "sta_max_cap"
            elif parsed.violation_type == 'noise':
                return "sta_noise"
            else:
                return "sta_mttv"  # Fallback
        elif isinstance(parsed, VTHKeyword):
            return "sta_vth"
        elif isinstance(parsed, CellUsageKeyword):
            return "sta_cell_usage"
        elif isinstance(parsed, PVKeyword):
            # Map PV category to group name
            if parsed.category == 'DRC':
                return "pv_drc"
            elif parsed.category == 'LVS':
                return "pv_lvs"
            elif parsed.category == 'FlipChip':
                return "pv_flipchip"
            elif parsed.category == 'PERC':
                return "pv_perc"
            elif parsed.category == 'PERC' and 'ldl' in parsed.original_name.lower():
                return "pv_perc_ldl"
        elif isinstance(parsed, GenericKeyword):
            # GenericKeyword already has a group attribute
            return parsed.group

        return None

    def _update_categories_for_combined_tasks(self, task_names: List[str]):
        """Update category dropdown based on multiple selected tasks - dynamically from YAML groups"""
        # Use the same dynamic extraction as single task
        keywords = self.current_run_data.get('keywords', {})
        categories = self._extract_categories_from_keywords(keywords)

        # Update combo box
        # Block signals to prevent multiple triggers
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItems(categories)
        if categories:
            self.category_combo.setCurrentIndex(0)
        self.category_combo.blockSignals(False)

    def _refresh_view(self):
        """Refresh the current view based on selected category"""
        if not self.current_run_data:
            return

        category = self.category_combo.currentText()
        if not category:
            print("[DEBUG] _refresh_view: No category selected, skipping")
            return

        print(f"[DEBUG] _refresh_view: Refreshing with category '{category}'")
        self._on_category_changed(category)

    def _on_category_changed(self, category: str):
        """Handle category selection change - dynamically route to appropriate table"""
        print(f"[DEBUG] _on_category_changed called with category: '{category}'")

        # Check if we're in multi-run comparison mode
        if self.multiple_runs_data:
            print(f"[DEBUG] Multi-run mode detected, calling _display_multi_run_comparison")
            self._display_multi_run_comparison(category)
            return

        # Single run mode - original behavior
        print(f"[DEBUG] Single-run mode")
        # Hide all tables
        for table in [self.sta_table, self.violation_table, self.vth_table,
                     self.cell_usage_table, self.pv_drc_table, self.pv_lvs_table,
                     self.pv_flipchip_table, self.pv_perc_table,
                     self.apr_timing_table, self.apr_congestion_table]:
            table.setVisible(False)

        # Handle "All Metrics" specially - only show tables with data
        if category == "All Metrics":
            print(f"[DEBUG] Populating all tables for 'All Metrics'")
            self._populate_all_tables()
            # Only show tables that have data (more than just header row or empty state)
            for table in [self.sta_table, self.violation_table, self.vth_table,
                         self.cell_usage_table, self.pv_drc_table, self.pv_lvs_table,
                         self.pv_flipchip_table, self.pv_perc_table,
                         self.apr_timing_table, self.apr_congestion_table]:
                # Check if table has actual data (not just empty message)
                has_data = (table.rowCount() > 0 and
                           table.columnCount() > 1 and
                           not (table.rowCount() == 1 and
                                table.columnCount() == 1 and
                                table.item(0, 0) and
                                'No' in table.item(0, 0).text()))
                table.setVisible(has_data)
            return

        # Dynamic routing based on category name
        populate_method = self._category_to_populate_method(category)
        table_widget = self._category_to_table_widget(category)

        print(f"[DEBUG] Category '{category}' -> populate_method: {populate_method}, table_widget: {table_widget}")

        if populate_method and table_widget:
            print(f"[DEBUG] Calling populate method for category '{category}'")
            populate_method()
            table_widget.setVisible(True)
            print(f"[DEBUG] Table visible, rows: {table_widget.rowCount()}, cols: {table_widget.columnCount()}")
        else:
            # Fallback: show empty message
            print(f"Warning: No handler for category '{category}'")

    def _display_multi_run_comparison(self, category: str):
        """
        Display multiple runs comparison in either side-by-side or pivot mode.

        Args:
            category: Selected category name
        """
        # Clear all existing tables from splitter
        for i in reversed(range(self.splitter.count())):
            widget = self.splitter.widget(i)
            if widget:
                widget.setParent(None)

        if self.comparison_mode == "side-by-side":
            self._display_side_by_side_comparison(category)
        else:  # pivot mode
            self._display_pivot_comparison(category)

    def _display_side_by_side_comparison(self, category: str):
        """Display runs side-by-side in separate tables"""
        for run_path, tasks in sorted(self.multiple_runs_data.items()):
            # Create table for this run
            run_name = run_path.split('/')[-1] if '/' in run_path else run_path.split('\\')[-1]
            run_table = self._create_table_widget(f"Run: {run_name}")

            # Merge keywords from all tasks in this run
            merged_keywords = {}
            for task in tasks:
                raw_keywords = task['task_data'].get('keywords', {})
                for kw_name, kw_data in raw_keywords.items():
                    if isinstance(kw_data, dict):
                        value = kw_data.get('value', '-')
                    else:
                        value = kw_data
                    merged_keywords[kw_name] = value

            # Temporarily set this run's data as current
            original_data = self.current_run_data
            self.current_run_data = {'keywords': merged_keywords, 'is_combined': False}

            # Get populate method for this category
            populate_method = self._category_to_populate_method(category)

            if populate_method:
                # Create a temporary table attribute for the populate method
                category_lower = category.lower()
                if "sta" in category_lower and ("setup timing" in category_lower or "hold timing" in category_lower or category_lower == "sta timing"):
                    self.sta_table = run_table
                elif "sta" in category_lower and ("mttv" in category_lower or "max cap" in category_lower or "noise" in category_lower):
                    self.violation_table = run_table
                elif "sta" in category_lower and "vth" in category_lower:
                    self.vth_table = run_table
                elif "sta" in category_lower and "cell usage" in category_lower:
                    self.cell_usage_table = run_table
                elif "pv" in category_lower and "drc" in category_lower:
                    self.pv_drc_table = run_table
                elif "pv" in category_lower and "lvs" in category_lower:
                    self.pv_lvs_table = run_table
                elif "pv" in category_lower and "flipchip" in category_lower:
                    self.pv_flipchip_table = run_table
                elif "pv" in category_lower and "perc" in category_lower:
                    self.pv_perc_table = run_table

                # Call populate method
                populate_method()

            # Restore original data
            self.current_run_data = original_data

            # Add table to splitter
            self.splitter.addWidget(run_table)
            run_table.setVisible(True)

    def _display_pivot_comparison(self, category: str):
        """Display runs as columns in pivot table with parsed metrics"""
        # Create single comparison table
        comparison_table = self._create_table_widget(f"Multi-Run Comparison - {category}")

        # Collect all keywords and values from all runs
        run_names = []
        run_keywords_map = {}  # {run_name: {keyword: value}}

        for run_path, tasks in sorted(self.multiple_runs_data.items()):
            run_name = run_path.split('/')[-1] if '/' in run_path else run_path.split('\\')[-1]
            run_names.append(run_name)

            # Merge keywords from all tasks in this run
            merged_keywords = {}
            for task in tasks:
                raw_keywords = task['task_data'].get('keywords', {})
                for kw_name, kw_data in raw_keywords.items():
                    if isinstance(kw_data, dict):
                        value = kw_data.get('value', '-')
                    else:
                        value = kw_data
                    merged_keywords[kw_name] = value

            run_keywords_map[run_name] = merged_keywords

        # Collect all unique keywords across all runs
        all_keywords = set()
        for keywords in run_keywords_map.values():
            all_keywords.update(keywords.keys())

        # Filter keywords based on category
        filtered_keywords = self._filter_keywords_by_category(list(all_keywords), category)

        # Parse and group keywords by type for structured display
        parsed_rows = []
        for kw_name in filtered_keywords:
            parsed = self.parser.parse_keyword(kw_name, "")
            if parsed:
                # Collect values from all runs
                run_values = {}
                for run_name in run_names:
                    run_values[run_name] = run_keywords_map[run_name].get(kw_name, '-')

                parsed_rows.append({
                    'keyword': kw_name,
                    'parsed': parsed,
                    'run_values': run_values
                })

        # Determine table structure based on keyword type
        if parsed_rows:
            first_parsed = parsed_rows[0]['parsed']
            self._populate_pivot_table_by_type(comparison_table, parsed_rows, run_names, first_parsed)

        # Add to splitter
        self.splitter.addWidget(comparison_table)
        comparison_table.setVisible(True)

    def _populate_pivot_table_by_type(self, table: QTableWidget, parsed_rows: List[Dict], run_names: List[str], sample_parsed: Any):
        """Populate pivot table based on parsed keyword type"""
        from .keyword_parser import STAKeyword, PVKeyword, ViolationKeyword, VTHKeyword, CellUsageKeyword, GenericKeyword

        if isinstance(sample_parsed, STAKeyword):
            # STA keywords: Mode | Corner | Timing | Metric | Path Type | Run1 | Run2...
            headers = ["Mode", "Corner", "Timing", "Metric", "Path Type"] + run_names
            table.setColumnCount(len(headers))
            table.setHorizontalHeaderLabels(headers)

            # Group by mode/corner/timing/metric/path
            table.setRowCount(len(parsed_rows))
            for row_idx, row_data in enumerate(parsed_rows):
                kw = row_data['parsed']
                table.setItem(row_idx, 0, NaturalSortTableItem(kw.mode))
                table.setItem(row_idx, 1, NaturalSortTableItem(kw.corner))
                table.setItem(row_idx, 2, NaturalSortTableItem("Setup" if kw.timing_type == 's' else "Hold"))
                table.setItem(row_idx, 3, NaturalSortTableItem(kw.metric.upper()))
                table.setItem(row_idx, 4, NaturalSortTableItem(kw.path_type))

                # Add run values
                for col_idx, run_name in enumerate(run_names, start=5):
                    value = row_data['run_values'][run_name]
                    self._set_value_item(table, row_idx, col_idx, value)

        elif isinstance(sample_parsed, PVKeyword):
            # PV keywords: Category | Rule | Check Type | Run1 | Run2...
            headers = ["Category", "Rule", "Check Type"] + run_names
            table.setColumnCount(len(headers))
            table.setHorizontalHeaderLabels(headers)

            table.setRowCount(len(parsed_rows))
            for row_idx, row_data in enumerate(parsed_rows):
                kw = row_data['parsed']
                table.setItem(row_idx, 0, NaturalSortTableItem(kw.category))
                table.setItem(row_idx, 1, NaturalSortTableItem(kw.rule if kw.rule else '-'))
                table.setItem(row_idx, 2, NaturalSortTableItem(kw.check_type if kw.check_type else '-'))

                # Add run values
                for col_idx, run_name in enumerate(run_names, start=3):
                    value = row_data['run_values'][run_name]
                    self._set_value_item(table, row_idx, col_idx, value)

        elif isinstance(sample_parsed, ViolationKeyword):
            # Violation keywords: Mode | Corner | Type | Sub Type | Metric | Run1 | Run2...
            headers = ["Mode", "Corner", "Violation Type", "Sub Type", "Metric"] + run_names
            table.setColumnCount(len(headers))
            table.setHorizontalHeaderLabels(headers)

            table.setRowCount(len(parsed_rows))
            for row_idx, row_data in enumerate(parsed_rows):
                kw = row_data['parsed']
                table.setItem(row_idx, 0, NaturalSortTableItem(kw.mode))
                table.setItem(row_idx, 1, NaturalSortTableItem(kw.corner))
                table.setItem(row_idx, 2, NaturalSortTableItem(kw.violation_type.replace('_', ' ').title()))
                table.setItem(row_idx, 3, NaturalSortTableItem(kw.sub_type.replace('_', ' ').title() if kw.sub_type else '-'))
                table.setItem(row_idx, 4, NaturalSortTableItem(kw.metric.upper()))

                # Add run values
                for col_idx, run_name in enumerate(run_names, start=5):
                    value = row_data['run_values'][run_name]
                    self._set_value_item(table, row_idx, col_idx, value)

        elif isinstance(sample_parsed, (VTHKeyword, CellUsageKeyword, GenericKeyword)):
            # Simple keywords: Cell Type | Metric | Run1 | Run2...
            headers = ["Cell Type", "Metric"] + run_names
            table.setColumnCount(len(headers))
            table.setHorizontalHeaderLabels(headers)

            table.setRowCount(len(parsed_rows))
            for row_idx, row_data in enumerate(parsed_rows):
                kw = row_data['parsed']
                # Split metric name into cell type and metric (e.g., "pad_inst" -> "pad", "inst")
                parts = kw.name.rsplit('_', 1)
                if len(parts) == 2:
                    cell_type, metric = parts
                else:
                    # If no underscore, put everything in cell type, empty metric
                    cell_type, metric = parts[0], ""

                table.setItem(row_idx, 0, NaturalSortTableItem(cell_type))
                table.setItem(row_idx, 1, NaturalSortTableItem(metric))

                # Add run values (starting at column 2 now)
                for col_idx, run_name in enumerate(run_names, start=2):
                    value = row_data['run_values'][run_name]
                    self._set_value_item(table, row_idx, col_idx, value)

        # Auto-resize columns
        table.resizeColumnsToContents()

    def _set_value_item(self, table: QTableWidget, row: int, col: int, value: Any):
        """Helper to set a value item with proper formatting"""
        # Format integer values
        if isinstance(value, str) and value not in ['-', '']:
            try:
                float_val = float(value)
                if float_val.is_integer():
                    value = int(float_val)
            except (ValueError, TypeError):
                pass

        value_item = NaturalSortTableItem(str(value))

        if self._is_numeric_value(value):
            value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        else:
            value_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        if self._is_negative_value(value):
            value_item.setForeground(QBrush(QColor(200, 0, 0)))

        table.setItem(row, col, value_item)

    def _filter_keywords_by_category(self, keywords: List[str], category: str) -> List[str]:
        """Filter keywords based on selected category"""
        filtered = []

        for kw_name in keywords:
            # First check YAML groups
            found_in_yaml = False
            for group_name, group_keywords in self.keyword_groups.items():
                if kw_name in group_keywords:
                    category_name = self._group_to_category_name(group_name)
                    if category_name == category or category == "All Metrics":
                        filtered.append(kw_name)
                    found_in_yaml = True
                    break

            if found_in_yaml:
                continue

            # If not in YAML, try parsing
            parsed = self.parser.parse_keyword(kw_name, "")
            if parsed:
                # Determine if keyword belongs to this category
                inferred_group = self._infer_group_from_parsed_keyword(parsed)
                if inferred_group:
                    category_name = self._group_to_category_name(inferred_group)
                    if category_name == category or category == "All Metrics":
                        filtered.append(kw_name)
                elif category == "All Metrics":
                    # Include unparseable keywords in "All Metrics"
                    filtered.append(kw_name)

        return filtered

    def _populate_sta_timing_table(self, filter_timing=None):
        """Populate STA timing metrics in pivot table format

        Args:
            filter_timing: 's' for setup only, 'h' for hold only, None for both
        """
        if not self.current_run_data:
            return

        keywords_data = self.current_run_data.get('keywords', {})
        if not keywords_data:
            return

        # Parse and group keywords
        keyword_names = list(keywords_data.keys())
        grouping = self.parser.group_keywords(keyword_names, self.keyword_groups)

        if not grouping.sta_keywords:
            self._set_empty_table(self.sta_table, "No STA timing metrics found")
            return

        # Collect all unique path types
        path_types = set()
        for mode_data in grouping.sta_keywords.values():
            for corner_data in mode_data.values():
                for timing_data in corner_data.values():
                    for metric_keywords in timing_data.values():
                        for kw in metric_keywords:
                            path_types.add(kw.path_type)

        path_types = sorted(path_types, key=lambda x: (x != 'all', x))  # 'all' first

        # Set up table columns: Mode | Corner | Timing | Metric | {path_types}
        headers = ["Mode", "Corner", "Timing", "Metric"] + path_types
        self.sta_table.setColumnCount(len(headers))
        self.sta_table.setHorizontalHeaderLabels(headers)

        # Populate rows (filter by timing type if specified)
        rows = []
        # Determine which timing types to show
        timing_types = []
        if filter_timing == 's':
            timing_types = ['s']
        elif filter_timing == 'h':
            timing_types = ['h']
        else:
            timing_types = ['s', 'h']  # Show both

        for mode in sorted(grouping.sta_keywords.keys(), key=self.parser.natural_sort_key):
            for corner in sorted(grouping.sta_keywords[mode].keys(), key=self.parser.natural_sort_key):
                for timing_type in timing_types:
                    if timing_type not in grouping.sta_keywords[mode][corner]:
                        continue

                    timing_data = grouping.sta_keywords[mode][corner][timing_type]
                    timing_label = "Setup" if timing_type == 's' else "Hold"

                    for metric in ['wns', 'tns', 'num']:  # Standard order
                        if metric not in timing_data:
                            continue

                        row_data = {
                            'Mode': mode,
                            'Corner': corner,
                            'Timing': timing_label,
                            'Metric': metric.upper()
                        }

                        # Fill path type values
                        for kw in timing_data[metric]:
                            value = keywords_data.get(kw.original_name, '-')
                            row_data[kw.path_type] = self._format_value(value, metric)

                        rows.append(row_data)

        self._fill_table(self.sta_table, headers, rows)

    def _populate_violation_table(self, filter_type=None):
        """Populate violation metrics (max_tran, max_cap, noise)

        Args:
            filter_type: 'max_tran', 'max_cap', 'noise', or None for all types
        """
        if not self.current_run_data:
            return

        keywords_data = self.current_run_data.get('keywords', {})
        keyword_names = list(keywords_data.keys())
        grouping = self.parser.group_keywords(keyword_names, self.keyword_groups)

        if not grouping.violation_keywords:
            self._set_empty_table(self.violation_table, "No violation metrics found")
            return

        # Table columns: Mode | Corner | Violation Type | Count | Worst Value
        headers = ["Mode", "Corner", "Violation Type", "Sub Type", "Count", "Worst"]
        self.violation_table.setColumnCount(len(headers))
        self.violation_table.setHorizontalHeaderLabels(headers)

        rows = []
        for mode in sorted(grouping.violation_keywords.keys()):
            for corner in sorted(grouping.violation_keywords[mode].keys(), key=self.parser.natural_sort_key):
                for vtype in sorted(grouping.violation_keywords[mode][corner].keys()):
                    # Apply filter if specified
                    if filter_type is not None and vtype != filter_type:
                        continue

                    # Find num and worst keywords
                    num_kw = None
                    worst_kw = None
                    sub_type = ""

                    for kw in grouping.violation_keywords[mode][corner][vtype]:
                        if kw.metric == 'num':
                            num_kw = kw
                        elif kw.metric == 'worst':
                            worst_kw = kw
                        if kw.sub_type:
                            sub_type = kw.sub_type

                    row_data = {
                        'Mode': mode,
                        'Corner': corner,
                        'Violation Type': vtype.replace('_', ' ').title(),
                        'Sub Type': sub_type.replace('_', ' ').title() if sub_type else '-',
                        'Count': keywords_data.get(num_kw.original_name, '-') if num_kw else '-',
                        'Worst': keywords_data.get(worst_kw.original_name, '-') if worst_kw else '-'
                    }
                    rows.append(row_data)

        self._fill_table(self.violation_table, headers, rows)

    def _populate_vth_table(self):
        """Populate VTH ratio table"""
        if not self.current_run_data:
            return

        keywords_data = self.current_run_data.get('keywords', {})
        keyword_names = list(keywords_data.keys())
        grouping = self.parser.group_keywords(keyword_names, self.keyword_groups)

        if not grouping.vth_keywords:
            self._set_empty_table(self.vth_table, "No VTH ratio data found")
            return

        headers = ["VTH Type", "Percentage"]
        self.vth_table.setColumnCount(len(headers))
        self.vth_table.setHorizontalHeaderLabels(headers)

        rows = []
        for kw in grouping.vth_keywords:
            value = keywords_data.get(kw.original_name, '-')
            rows.append({'VTH Type': kw.name, 'Percentage': f"{value}%" if value != '-' else '-'})

        self._fill_table(self.vth_table, headers, rows)

    def _populate_cell_usage_table(self):
        """Populate cell usage table"""
        if not self.current_run_data:
            return

        keywords_data = self.current_run_data.get('keywords', {})
        keyword_names = list(keywords_data.keys())
        grouping = self.parser.group_keywords(keyword_names, self.keyword_groups)

        if not grouping.cell_usage_keywords:
            self._set_empty_table(self.cell_usage_table, "No cell usage data found")
            return

        headers = ["Cell Type", "Instance Count", "Area (um^2)"]
        self.cell_usage_table.setColumnCount(len(headers))
        self.cell_usage_table.setHorizontalHeaderLabels(headers)

        # Group by cell type (extract from keyword name)
        cell_types = {}
        for kw in grouping.cell_usage_keywords:
            parts = kw.name.split('_')
            cell_type = '_'.join(parts[:-1])  # Remove _inst or _area suffix
            metric = parts[-1]  # inst or area

            if cell_type not in cell_types:
                cell_types[cell_type] = {}
            cell_types[cell_type][metric] = keywords_data.get(kw.original_name, '-')

        rows = []
        for cell_type in sorted(cell_types.keys()):
            rows.append({
                'Cell Type': cell_type.replace('_', ' ').title(),
                'Instance Count': cell_types[cell_type].get('inst', '-'),
                'Area (um^2)': cell_types[cell_type].get('area', '-')
            })

        self._fill_table(self.cell_usage_table, headers, rows)

    def _populate_pv_drc_table(self):
        """Populate DRC table"""
        self._populate_pv_category_table('DRC', self.pv_drc_table,
                                         ["Rule", "Cell Count", "Flatten Count"])

    def _populate_pv_lvs_table(self):
        """Populate LVS table with appropriate columns"""
        if not self.current_run_data:
            return

        keywords_data = self.current_run_data.get('keywords', {})
        keyword_names = list(keywords_data.keys())
        grouping = self.parser.group_keywords(keyword_names, self.keyword_groups)

        # Filter for LVS keywords only
        if 'LVS' not in grouping.pv_keywords or not grouping.pv_keywords['LVS']:
            self._set_empty_table(self.pv_lvs_table, "No LVS metrics found")
            return

        # LVS has different columns: Status instead of Cell/Flatten counts
        headers = ["Check Type", "Status"]
        self.pv_lvs_table.setColumnCount(len(headers))
        self.pv_lvs_table.setHorizontalHeaderLabels(headers)

        rows = []
        for kw in grouping.pv_keywords['LVS']:
            value = keywords_data.get(kw.original_name, '-')
            check_type = kw.rule if kw.rule else 'Overall'

            rows.append({
                'Check Type': check_type,
                'Status': value
            })

        self._fill_table(self.pv_lvs_table, headers, rows)

    def _populate_pv_flipchip_table(self):
        """Populate FlipChip table"""
        self._populate_pv_category_table('FlipChip', self.pv_flipchip_table,
                                         ["Rule", "Cell Count", "Flatten Count"])

    def _populate_pv_perc_table(self):
        """Populate PERC table"""
        self._populate_pv_category_table('PERC', self.pv_perc_table,
                                         ["Rule", "Cell Count", "Flatten Count"])

    def _populate_pv_category_table(self, category_name: str, table_widget, headers: List[str]):
        """Generic method to populate a PV category table"""
        if not self.current_run_data:
            return

        keywords_data = self.current_run_data.get('keywords', {})
        keyword_names = list(keywords_data.keys())
        grouping = self.parser.group_keywords(keyword_names, self.keyword_groups)

        # Filter for specific category
        if category_name not in grouping.pv_keywords or not grouping.pv_keywords[category_name]:
            self._set_empty_table(table_widget, f"No {category_name} metrics found")
            return

        table_widget.setColumnCount(len(headers))
        table_widget.setHorizontalHeaderLabels(headers)

        # Group keywords by rule (combine _cell and _flatten entries for DRC/FlipChip)
        rules_data = {}
        for kw in grouping.pv_keywords[category_name]:
            value = keywords_data.get(kw.original_name, '-')
            rule_name = kw.rule if kw.rule else 'Total'

            if rule_name not in rules_data:
                rules_data[rule_name] = {'cell': '-', 'flatten': '-', 'violations': '-'}

            # Use check_type from parsed keyword metadata for more reliable detection
            if isinstance(value, str) and '/' in value:
                # Format: "cell/flatten" (old format)
                parts = value.split('/')
                rules_data[rule_name]['cell'] = parts[0] if len(parts) > 0 else '-'
                rules_data[rule_name]['flatten'] = parts[1] if len(parts) > 1 else '-'
            elif kw.check_type == 'cell':
                rules_data[rule_name]['cell'] = value
            elif kw.check_type == 'flatten':
                rules_data[rule_name]['flatten'] = value
            else:
                # Generic violation count or summary
                rules_data[rule_name]['violations'] = value
                # If no cell/flatten data, use as fallback
                if rules_data[rule_name]['cell'] == '-':
                    rules_data[rule_name]['cell'] = value

        # Build rows based on header structure (skip 'Total' rows)
        rows = []
        for rule_name in sorted(rules_data.keys()):
            # Skip 'Total' summary rows
            if rule_name.lower() == 'total':
                continue

            rule_info = rules_data[rule_name]

            if len(headers) == 3:  # ["Rule", "Cell Count", "Flatten Count"]
                rows.append({
                    'Rule': rule_name,
                    'Cell Count': rule_info['cell'],
                    'Flatten Count': rule_info['flatten']
                })
            elif len(headers) == 2:  # ["Rule", "Violations"]
                rows.append({
                    'Rule': rule_name,
                    'Violations': rule_info['violations']
                })

        self._fill_table(table_widget, headers, rows)

    def _populate_apr_timing_table(self):
        """Populate APR timing summary (generic s_wns, s_tns, h_wns, h_tns)"""
        if not self.current_run_data:
            return

        keywords_data = self.current_run_data.get('keywords', {})
        keyword_names = list(keywords_data.keys())
        grouping = self.parser.group_keywords(keyword_names, self.keyword_groups)

        if not grouping.timing_keywords:
            self._set_empty_table(self.apr_timing_table, "No APR timing data found")
            return

        headers = ["Timing Type", "Metric", "Value"]
        self.apr_timing_table.setColumnCount(len(headers))
        self.apr_timing_table.setHorizontalHeaderLabels(headers)

        rows = []
        for kw in grouping.timing_keywords:
            parts = kw.name.split('_')
            timing_type = "Setup" if parts[0] == 's' else "Hold"
            metric = parts[1].upper() if len(parts) > 1 else kw.name

            value = keywords_data.get(kw.original_name, '-')
            rows.append({
                'Timing Type': timing_type,
                'Metric': metric,
                'Value': value
            })

        self._fill_table(self.apr_timing_table, headers, rows)

    def _populate_apr_congestion_table(self):
        """Populate APR congestion metrics"""
        if not self.current_run_data:
            return

        keywords_data = self.current_run_data.get('keywords', {})
        keyword_names = list(keywords_data.keys())
        grouping = self.parser.group_keywords(keyword_names, self.keyword_groups)

        if not grouping.congestion_keywords:
            self._set_empty_table(self.apr_congestion_table, "No congestion data found")
            return

        headers = ["Metric", "Value"]
        self.apr_congestion_table.setColumnCount(len(headers))
        self.apr_congestion_table.setHorizontalHeaderLabels(headers)

        rows = []
        for kw in grouping.congestion_keywords:
            value = keywords_data.get(kw.original_name, '-')
            rows.append({
                'Metric': kw.name.replace('_', ' ').title(),
                'Value': value
            })

        self._fill_table(self.apr_congestion_table, headers, rows)

    def _populate_all_tables(self):
        """Populate all tables"""
        self._populate_sta_timing_table()
        self._populate_violation_table()
        self._populate_pv_drc_table()
        self._populate_pv_lvs_table()
        self._populate_pv_flipchip_table()
        self._populate_pv_perc_table()
        self._populate_apr_timing_table()
        self._populate_apr_congestion_table()

    def _fill_table(self, table: QTableWidget, headers: List[str], rows: List[Dict[str, Any]]):
        """Fill a table widget with data"""
        table.setRowCount(len(rows))

        for row_idx, row_data in enumerate(rows):
            for col_idx, header in enumerate(headers):
                value = row_data.get(header, '-')

                # Format PV Cell Count and Flatten Count as integers
                if header in ['Cell Count', 'Flatten Count'] and value != '-':
                    try:
                        # Convert to int if it's a whole number
                        float_val = float(value)
                        if float_val.is_integer():
                            value = int(float_val)
                    except (ValueError, TypeError):
                        pass  # Keep original value if conversion fails

                # Use NaturalSortTableItem for proper alphanumeric sorting
                item = NaturalSortTableItem(str(value))

                # Right-align numeric columns
                if self._is_numeric_value(value):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

                # Color-code negative values (red)
                if self._is_negative_value(value):
                    item.setForeground(QBrush(QColor(200, 0, 0)))

                table.setItem(row_idx, col_idx, item)

        # Auto-resize columns
        table.resizeColumnsToContents()
        for col in range(table.columnCount()):
            current_width = table.columnWidth(col)
            table.setColumnWidth(col, min(current_width + 20, 300))  # Add padding, cap at 300px

    def _set_empty_table(self, table: QTableWidget, message: str):
        """Display empty state message in table"""
        table.setRowCount(1)
        table.setColumnCount(1)
        table.setHorizontalHeaderLabels([""])
        item = NaturalSortTableItem(message)
        item.setTextAlignment(Qt.AlignCenter)
        item.setForeground(QBrush(QColor(128, 128, 128)))
        table.setItem(0, 0, item)
        table.horizontalHeader().setStretchLastSection(True)

    @staticmethod
    def _format_value(value: Any, metric: str) -> str:
        """Format value based on metric type"""
        if value in ['-', '', None]:
            return '-'

        if metric == 'num':
            # Integer count
            try:
                return str(int(float(value)))
            except (ValueError, TypeError):
                return str(value)
        else:
            # Timing value (ns)
            try:
                float_val = float(value)
                if float_val == 0:
                    return '0'
                return f"{float_val:.4f}".rstrip('0').rstrip('.')
            except (ValueError, TypeError):
                return str(value)

    @staticmethod
    def _is_numeric_value(value: Any) -> bool:
        """Check if value is numeric"""
        if isinstance(value, (int, float)):
            return True
        if isinstance(value, str):
            try:
                float(value.replace('%', '').replace('H', '').replace('V', ''))
                return True
            except ValueError:
                return False
        return False

    @staticmethod
    def _is_negative_value(value: Any) -> bool:
        """Check if value is negative"""
        try:
            num_val = float(str(value).replace('%', '').replace('H', '').replace('V', ''))
            return num_val < 0
        except (ValueError, TypeError):
            return False

    def _export_to_csv(self):
        """Export current visible table(s) to CSV and show in dialog"""
        if not self.current_run_data:
            QMessageBox.warning(self, "Export Error", "No data to export")
            return

        # Determine which table(s) to export
        category = self.category_combo.currentText()

        try:
            # Build CSV content in memory
            csv_lines = []
            csv_lines.append(f"# Hawkeye Report Export")

            # Check if multi-run mode
            if self.multiple_runs_data:
                csv_lines.append(f"# Multi-Run Comparison: {len(self.multiple_runs_data)} runs")
                csv_lines.append(f"# Mode: {self.comparison_mode}")
            else:
                csv_lines.append(f"# Run: {self.current_run_data.get('run_path', 'N/A')}")
                csv_lines.append(f"# Task: {self.current_run_data.get('task_name', 'N/A')}")

            csv_lines.append(f"# Category: {category}")
            csv_lines.append("")

            # Export based on mode
            if self.multiple_runs_data:
                # Multi-run mode: export tables from splitter
                for i in range(self.splitter.count()):
                    table = self.splitter.widget(i)
                    if table and isinstance(table, QTableWidget) and table.isVisible():
                        # Get table title from window title or create generic one
                        section_name = f"Table {i+1}"
                        csv_lines.append(f"## {section_name}")
                        self._append_table_to_csv_lines(table, csv_lines)
                        csv_lines.append("")
            else:
                # Single run mode: original behavior
                if category == "All Metrics":
                    tables = [
                        (self.sta_table, "STA Timing"),
                        (self.violation_table, "Violations"),
                        (self.vth_table, "VTH Ratio"),
                        (self.cell_usage_table, "Cell Usage"),
                        (self.pv_drc_table, "PV - DRC"),
                        (self.pv_lvs_table, "PV - LVS"),
                        (self.pv_flipchip_table, "PV - FlipChip"),
                        (self.pv_perc_table, "PV - PERC"),
                        (self.apr_timing_table, "APR Timing"),
                        (self.apr_congestion_table, "APR Congestion")
                    ]
                else:
                    # Map category to table widget - use _category_to_table_widget for consistency
                    table_widget = self._category_to_table_widget(category)
                    if table_widget:
                        tables = [(table_widget, category)]
                    else:
                        tables = []

                for table, section_name in tables:
                    if table is None or table.rowCount() == 0:
                        continue

                    csv_lines.append(f"## {section_name}")
                    self._append_table_to_csv_lines(table, csv_lines)
                    csv_lines.append("")

            csv_content = '\n'.join(csv_lines)

            # Show CSV in dialog
            self._show_csv_dialog(csv_content)

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to generate CSV:\n{str(e)}")

    def _show_csv_dialog(self, csv_content: str):
        """Show CSV content in a dialog with copy button"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Export to CSV")
        dialog.setModal(True)
        dialog.resize(800, 600)

        layout = QVBoxLayout(dialog)

        # Info label
        info_label = QLabel("CSV data ready. Copy to clipboard or save to file:")
        layout.addWidget(info_label)

        # Text editor with CSV content
        text_edit = QTextEdit()
        text_edit.setPlainText(csv_content)
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Courier", 9))
        layout.addWidget(text_edit)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(lambda: self._copy_to_clipboard(csv_content, dialog))
        button_layout.addWidget(copy_btn)

        save_btn = QPushButton("Save to File...")
        save_btn.clicked.connect(lambda: self._save_csv_to_file(csv_content, dialog))
        button_layout.addWidget(save_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        dialog.exec_()

    def _copy_to_clipboard(self, text: str, dialog: QDialog):
        """Copy text to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(dialog, "Copied", "CSV data copied to clipboard!")

    def _save_csv_to_file(self, csv_content: str, dialog: QDialog):
        """Save CSV content to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            dialog,
            "Save CSV File",
            f"hawkeye_report_{self.current_run_data.get('task_name', 'export')}.csv",
            "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(csv_content)
                QMessageBox.information(dialog, "Saved", f"CSV saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to save file:\n{str(e)}")

    @staticmethod
    def _append_table_to_csv_lines(table: QTableWidget, csv_lines: List[str]):
        """Append table data to CSV lines list"""
        # Write headers
        headers = []
        for col in range(table.columnCount()):
            headers.append(table.horizontalHeaderItem(col).text())
        csv_lines.append(','.join(f'"{h}"' for h in headers))

        # Write rows
        for row in range(table.rowCount()):
            row_data = []
            for col in range(table.columnCount()):
                item = table.item(row, col)
                value = item.text() if item else ''
                row_data.append(f'"{value}"')
            csv_lines.append(','.join(row_data))