#!/usr/local/bin/python3.12
"""
Treem Casino - Enhanced Directory Management Application
Main entry point for the modular directory tracer application.
"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication

# Add the treem_casino package to the path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from treem_casino.ui.main_window import MainWindow
from treem_casino.config.settings import AppConfig
from treem_casino.utils.logger import setup_logging


def main():
    """Main entry point for the application."""
    # Setup logging
    setup_logging()

    # Initialize Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Treem Casino")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Casino Project")

    # Load configuration
    config = AppConfig()

    # Create and show main window
    window = MainWindow(config)
    window.show()

    # Start event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
