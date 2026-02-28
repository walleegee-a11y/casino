"""GUI components for Hawkeye"""

try:
    from .dashboard import HawkeyeDashboard
    from .workers import BackgroundWorker
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    HawkeyeDashboard = None
    BackgroundWorker = None

__all__ = ['HawkeyeDashboard', 'BackgroundWorker', 'GUI_AVAILABLE']
