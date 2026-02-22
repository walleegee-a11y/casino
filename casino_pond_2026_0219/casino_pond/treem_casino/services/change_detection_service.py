"""
Service for detecting directory changes between refreshes.
Tracks modification times and identifies newly updated directories.
"""

from pathlib import Path
from typing import Dict, List, Set, Optional
from datetime import datetime
from dataclasses import dataclass
from PyQt5.QtCore import QObject, pyqtSignal

from ..models.directory import DirectoryHierarchy


@dataclass
class DirectoryChange:
    """Represents a change in a directory."""
    path: Path
    old_mtime: Optional[datetime]
    new_mtime: datetime
    change_type: str  # "new", "modified", "unchanged"

    @property
    def is_updated(self) -> bool:
        """Check if directory was updated."""
        return self.change_type in ("new", "modified")


class ChangeDetectionService(QObject):
    """Service for detecting directory changes."""

    # Signals
    changes_detected = pyqtSignal(list)  # List[DirectoryChange]

    def __init__(self):
        super().__init__()
        self.previous_state: Dict[Path, datetime] = {}
        self.current_changes: List[DirectoryChange] = []

    def capture_state(self, hierarchy: DirectoryHierarchy) -> Dict[Path, datetime]:
        """Capture current state of directory hierarchy."""
        state = {}
        self._capture_recursive(hierarchy, state)
        return state

    def _capture_recursive(self, hierarchy: DirectoryHierarchy, state: Dict[Path, datetime]):
        """Recursively capture directory modification times."""
        dir_info = hierarchy.root
        if dir_info.modified_time:
            state[dir_info.path] = dir_info.modified_time

        for child in hierarchy.children.values():
            self._capture_recursive(child, state)

    def detect_changes(self, new_hierarchy: DirectoryHierarchy) -> List[DirectoryChange]:
        """Detect changes between previous and new state."""
        new_state = self.capture_state(new_hierarchy)
        changes = []

        # Find new and modified directories
        for path, new_mtime in new_state.items():
            old_mtime = self.previous_state.get(path)

            if old_mtime is None:
                # New directory
                change = DirectoryChange(
                    path=path,
                    old_mtime=None,
                    new_mtime=new_mtime,
                    change_type="new"
                )
                changes.append(change)
            elif new_mtime > old_mtime:
                # Modified directory
                change = DirectoryChange(
                    path=path,
                    old_mtime=old_mtime,
                    new_mtime=new_mtime,
                    change_type="modified"
                )
                changes.append(change)

        # Store current changes and state
        self.current_changes = changes
        self.previous_state = new_state

        # Emit signal
        if changes:
            self.changes_detected.emit(changes)

        return changes

    def get_updated_directories(self) -> List[Path]:
        """Get list of updated directory paths."""
        return [change.path for change in self.current_changes if change.is_updated]

    def clear_changes(self):
        """Clear stored changes."""
        self.current_changes.clear()

    def reset_state(self):
        """Reset the entire state."""
        self.previous_state.clear()
        self.current_changes.clear()
