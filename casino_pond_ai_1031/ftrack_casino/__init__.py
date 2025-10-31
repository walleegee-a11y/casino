"""
FastTrack Issue Management System

A comprehensive issue tracking system with advanced features including:
- SQLite database with full-text search
- Activity tracking and comments
- Smart attachment management
- Analytics and reporting
- Multi-format export
- Filter presets
- Dark mode theme
- Keyboard shortcuts
"""

__version__ = "2.0.0"
__author__ = "FastTrack Development Team"

# Import main components for easy access
from .gui import FastTrackGUI, launch_ftrack
from .database import IssueDatabase
from .search import AdvancedSearch
from .activity import ActivityTracker, NotificationSystem
from .attachments import AttachmentManager
from .analytics import IssueDashboard
from .export import IssueExporter
from .themes import ThemeManager

__all__ = [
    'FastTrackGUI',
    'launch_ftrack',
    'IssueDatabase',
    'AdvancedSearch',
    'ActivityTracker',
    'NotificationSystem',
    'AttachmentManager',
    'IssueDashboard',
    'IssueExporter',
    'ThemeManager',
]
