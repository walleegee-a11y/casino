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
    """Color definitions for UI"""
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
