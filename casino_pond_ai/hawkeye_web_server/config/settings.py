"""Configuration settings for Hawkeye Web Server"""

import os


class Config:
    """Flask application configuration"""

    # Flask settings
    SECRET_KEY = os.urandom(24)  # For session management

    # Server settings
    HOST = '0.0.0.0'
    PORT = 5021
    DEBUG = True

    # Application settings
    CASINO_PRJ_BASE = os.getenv('casino_prj_base')

    # SQLite availability
    try:
        import sqlite3
        SQLITE_AVAILABLE = True
    except ImportError:
        SQLITE_AVAILABLE = False
        print("Warning: SQLite not available. Some features may be limited.")

    # Template and static folders
    TEMPLATE_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
    STATIC_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')

    @classmethod
    def init_app(cls, app):
        """Initialize app with configuration"""
        pass
