"""Core functionality for Hawkeye Web Server"""

from .app import create_app
from .archive_manager import discover_projects, init_archive, get_archive, get_available_projects

__all__ = ['create_app', 'discover_projects', 'init_archive', 'get_archive', 'get_available_projects']
