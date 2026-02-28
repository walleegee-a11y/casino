#!/usr/local/bin/python3.12
"""
Standalone history utilities for recording directory operations.
Can be used independently without GUI dependencies.

This module provides functions to update the directory history file
that is used by the Tree Manager (Treem Casino) to track operations
like run creation, terminal launches, directory cloning, etc.
"""
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
import json
import getpass
import os
import tempfile


def add_history_entry(
    operation: str,
    path: Path,
    details: Optional[str] = None,
    project_base: Optional[Path] = None,
    project_name: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Add a history entry to the user's directory history file.

    This function updates the .directory_history_{user}.json file that
    the Tree Manager uses to display recent operations in the GUI.

    Args:
        operation: Type of operation. Supported values:
            - "create_run": Run directory creation
            - "terminal": Terminal opened
            - "clone": Directory cloned
            - "trash": Moved to trash
            - "restore": Restored from trash
            - "delete": Permanently deleted
            - "navigate": Directory navigation
        path: Full path to the directory
        details: Optional details about the operation (e.g., "Created run directory: v1.0")
        project_base: Project base directory (auto-detected from $casino_prj_base if None)
        project_name: Project name (auto-detected from $casino_prj_name if None)

    Returns:
        Tuple of (success: bool, message: str)
        - success: True if history was updated successfully
        - message: Success message or error description

    Example:
        >>> from pathlib import Path
        >>> success, msg = add_history_entry(
        ...     operation="create_run",
        ...     path=Path("/project/runs/v1.0"),
        ...     details="Created run directory: v1.0"
        ... )
        >>> print(msg)
        History updated: /project/.directory_history_user.json
    """
    try:
        current_user = getpass.getuser()

        # Auto-detect project base from environment if not provided
        if project_base is None:
            prj_base_env = os.getenv('casino_prj_base')
            if prj_base_env:
                project_base = Path(prj_base_env)
            else:
                # Fallback to home directory
                project_base = Path.home()

        # Auto-detect project name if not provided
        if project_name is None:
            project_name = os.getenv('casino_prj_name', 'unknown')

        # Determine history file location
        # Format: .directory_history_{username}.json
        history_file = project_base / f".directory_history_{current_user}.json"

        # Load existing history or create new
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                # Corrupted file - backup and start fresh
                backup_file = history_file.with_suffix('.json.bak')
                if history_file.exists():
                    import shutil
                    shutil.copy2(history_file, backup_file)
                    print(f"Warning: Corrupted history file backed up to {backup_file}")
                history_data = _create_new_history_data(current_user, project_base, project_name)
        else:
            history_data = _create_new_history_data(current_user, project_base, project_name)

        # Create new history entry
        new_entry = {
            'path': str(path.absolute()),
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'details': details,
            'user': current_user
        }

        # Add to history list
        history_data['history'].append(new_entry)
        history_data['current_index'] = len(history_data['history']) - 1
        history_data['saved_at'] = datetime.now().isoformat()

        # Trim history if too long (keep last 50 entries)
        max_history = 50
        if len(history_data['history']) > max_history:
            removed = len(history_data['history']) - max_history
            history_data['history'] = history_data['history'][removed:]
            history_data['current_index'] -= removed

        # Save updated history (atomic write to prevent corruption)
        _save_history_atomic(history_file, history_data)

        return True, f"History updated: {history_file}"

    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"Failed to update history: {e}"


def _create_new_history_data(user: str, project_base: Path, project_name: str) -> dict:
    """
    Create a new history data structure.

    Args:
        user: Username
        project_base: Project base directory path
        project_name: Project name

    Returns:
        Dictionary with initialized history structure
    """
    return {
        'user': user,
        'project_base': str(project_base),
        'project_name': project_name,
        'history': [],
        'current_index': -1,
        'version': '2.0'
    }


def _save_history_atomic(history_file: Path, history_data: dict):
    """
    Save history file to trigger file watchers properly.

    Direct write (not atomic) to ensure QFileSystemWatcher detects the change.

    Args:
        history_file: Path to the history file
        history_data: History data dictionary to save

    Raises:
        IOError: If file cannot be written
    """
    # Ensure parent directory exists
    history_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Direct write to ensure file watcher triggers
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())  # Force write to disk

    except Exception as e:
        raise IOError(f"Failed to save history file: {e}")


def add_run_creation_history(
    run_path: Path,
    run_version: str,
    project_base: Optional[Path] = None,
    project_name: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Convenience function to add a run creation entry to history.

    This creates a "create_run" operation entry that will appear as a
    dark blue "Run" button in the Tree Manager's Recent area.

    Args:
        run_path: Full path to the created run directory
        run_version: Run version identifier (e.g., "FFN_fe00_te29_pv00")
        project_base: Project base directory (auto-detected from $casino_prj_base if None)
        project_name: Project name (auto-detected from $casino_prj_name if None)

    Returns:
        Tuple of (success: bool, message: str)

    Example:
        >>> from pathlib import Path
        >>> success, msg = add_run_creation_history(
        ...     run_path=Path("/project/runs/FFN_fe00_te29_pv00"),
        ...     run_version="FFN_fe00_te29_pv00"
        ... )
        >>> if success:
        ...     print("Run creation recorded in history")
    """
    details = f"Created run directory: {run_version}"
    return add_history_entry('create_run', run_path, details, project_base, project_name)


def add_terminal_operation(
    path: Path,
    project_base: Optional[Path] = None,
    project_name: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Convenience function to add a terminal operation entry to history.

    Args:
        path: Path where terminal was opened
        project_base: Project base directory (auto-detected if None)
        project_name: Project name (auto-detected if None)

    Returns:
        Tuple of (success: bool, message: str)
    """
    details = f"GoGoGo terminal opened at {path.name}"
    return add_history_entry('terminal', path, details, project_base, project_name)


# Example usage and testing
if __name__ == "__main__":
    import sys

    print("=" * 70)
    print("History Utils - Standalone Test")
    print("=" * 70)

    # Test 1: Create a test run creation entry
    print("\nTest 1: Adding run creation entry...")
    test_run_path = Path.home() / "test_runs" / "test_v1.0"
    test_run_path.mkdir(parents=True, exist_ok=True)

    success, message = add_run_creation_history(
        run_path=test_run_path,
        run_version="test_v1.0"
    )

    print(f"  Success: {success}")
    print(f"  Message: {message}")

    # Test 2: Add a terminal operation entry
    print("\nTest 2: Adding terminal operation entry...")
    success, message = add_terminal_operation(
        path=test_run_path
    )

    print(f"  Success: {success}")
    print(f"  Message: {message}")

    # Test 3: Show the history file location
    print("\nTest 3: History file location...")
    current_user = getpass.getuser()
    prj_base = Path(os.getenv('casino_prj_base', Path.home()))
    history_file = prj_base / f".directory_history_{current_user}.json"

    print(f"  History file: {history_file}")
    print(f"  Exists: {history_file.exists()}")

    if history_file.exists():
        print(f"  Size: {history_file.stat().st_size} bytes")

        # Show last 3 entries
        with open(history_file, 'r') as f:
            data = json.load(f)
            print(f"  Total entries: {len(data['history'])}")
            print("\n  Last 3 entries:")
            for entry in data['history'][-3:]:
                print(f"    - {entry['operation']}: {entry.get('details', entry['path'])}")

    print("\n" + "=" * 70)
    print("Test completed!")
    print("=" * 70)

