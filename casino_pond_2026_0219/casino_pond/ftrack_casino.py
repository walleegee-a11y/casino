#! /usr/local/bin/python3.12 -u

"""
FastTrack Issue Management System - Main Entry Point

A comprehensive issue tracking system for software development projects.

Usage:
    python ftrack_casino.py

Or from code:
    from ftrack_casino import launch_ftrack
    launch_ftrack("/path/to/project")

For more information, see:
    - FASTTRACK_QUICKSTART.md - Quick start guide
    - FASTTRACK_ENHANCEMENTS.md - Technical documentation
    - KEYBOARD_SHORTCUTS.md - Keyboard shortcuts reference
"""

import sys
from ftrack_casino import launch_ftrack

if __name__ == "__main__":
    sys.exit(launch_ftrack())
