# -*- coding: utf-8 -*-
"""Constants used throughout the application"""

class Columns:
    """Table column indices"""
    BASE_DIR = 0
    TOP_NAME = 1
    USER = 2
    BLOCK = 3
    DK_VER_TAG = 4
    RUN_VERSION = 5
    JOB = 6
    TASK = 7
    STATUS = 8
    PATH_COLUMN_COUNT = 9


class StatusValues:
    """Status string constants"""
    COMPLETED = "Completed"
    READY = "Ready"
    NO_FILES = "No Files"
    NO_JOB_DIR = "No Job Dir"
    NOT_CONFIGURED = "Not Configured"
    FAILED = "Failed"
    NOT_STARTED = "Not Started"


class Colors:
    """Color definitions for UI - Excel-like Professional Design"""

    # ============================================================================
    # EXCEL-LIKE PROFESSIONAL COLOR SCHEME
    # ============================================================================
    # Primary Colors
    PRIMARY_BLUE = "#0078D4"      # Microsoft Blue - Primary actions
    PRIMARY_BLUE_DARK = "#005A9E" # Darker Blue - Check Status, Gather Selected
    SECONDARY_GRAY = "#6C757D"    # Secondary actions
    SUCCESS_GREEN = "#107C10"     # Success/positive actions
    WARNING_ORANGE = "#FFB900"    # Warning/export actions
    DANGER_RED = "#D13438"        # Danger/delete actions
    CHART_RED = "#C7402A"         # Reddish - Create Chart/Table button
    INFO_CYAN = "#00BCF2"         # Info actions

    # Backgrounds
    NEUTRAL_LIGHT = "#F5F5F5"     # Light gray background
    NEUTRAL_WHITE = "#FFFFFF"     # White background
    ALT_ROW = "#F9F9F9"           # Alternating row background

    # Borders and Grid
    BORDER_GRAY = "#D1D1D1"       # Standard borders
    BORDER_DARK = "#C0C0C0"       # Darker borders

    # Hover and Selection States
    HOVER_BLUE = "#E7F3FF"        # Row hover - light blue
    HOVER_YELLOW = "#FFF4CE"      # Cell hover - Excel-like yellow
    SELECTED_BLUE = "#0078D4"     # Selected items (active/focused)
    SELECTED_GRAY = "#505050"     # Selected items (inactive/unfocused) - dark gray for contrast

    # Text Colors
    TEXT_BLACK = "#000000"        # Primary text
    TEXT_GRAY = "#6C757D"         # Secondary text
    TEXT_WHITE = "#FFFFFF"        # Text on dark backgrounds

    # ============================================================================
    # LEGACY COLORS (Kept for backward compatibility - use new colors above)
    # ============================================================================
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
    DEEP_PURPLE = "#6a1b9a"  # Special feature buttons (Mode/Corner Filter)


class FilePatterns:
    """Common file patterns"""
    LOG_EXTENSIONS = ['.log', '.out']
    REPORT_EXTENSIONS = ['.rpt', '.report']
    COMPRESSED_EXTENSIONS = ['.gz']

