# treem_casino/__init__.py
"""
Treem Casino - Enhanced Directory Management Application
A modern, type-safe directory browser with memo system and advanced operations.
"""

__version__ = "2.0.0"
__author__ = "Casino Project Team"
__description__ = "Enhanced directory management with modern PyQt5 architecture"

from .config.settings import AppConfig

# treem_casino/config/__init__.py
"""Configuration management module."""

from .settings import AppConfig, ColorScheme, FontConfig, PathConfig, UIConfig

__all__ = ['AppConfig', 'ColorScheme', 'FontConfig', 'PathConfig', 'UIConfig']

# treem_casino/models/__init__.py
"""Data models for the application."""

from .directory import DirectoryHierarchy, DirectoryInfo, DirectoryFilter, SearchResult
from .memo import Memo, MemoCollection, MemoStats

__all__ = [
    'DirectoryHierarchy', 'DirectoryInfo', 'DirectoryFilter', 'SearchResult',
    'Memo', 'MemoCollection', 'MemoStats'
]

# treem_casino/services/__init__.py
"""Business logic services."""

from .directory_service import DirectoryService
from .memo_service import MemoService

__all__ = ['DirectoryService', 'MemoService']

# treem_casino/ui/__init__.py
"""User interface components."""

from .main_window import MainWindow
from .widgets import (
    EnhancedTreeView, BlinkingDelegate, ProgressWidget, SearchWidget,
    MemoDialog, MemoViewerDialog, StatusWidget, FilterControlWidget,
    DepthControlWidget, ConfirmationDialog
)
from .dialogs import CloneDialog

__all__ = [
    'MainWindow', 'EnhancedTreeView', 'BlinkingDelegate', 'ProgressWidget',
    'SearchWidget', 'MemoDialog', 'MemoViewerDialog', 'StatusWidget',
    'FilterControlWidget', 'DepthControlWidget', 'ConfirmationDialog',
    'CloneDialog'
]

# treem_casino/utils/__init__.py
"""Utility modules."""

from .tree_model import DirectoryTreeModel, TreeItem
from .logger import setup_logging, get_logger

__all__ = ['DirectoryTreeModel', 'TreeItem', 'setup_logging', 'get_logger']
