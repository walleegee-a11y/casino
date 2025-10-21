"""
Complete directory history service for tracking navigation and operations.
Provides back/forward navigation and operation history with terminal operation tracking.
History files are stored in the casino project directory with user-specific naming.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal
import json
import getpass

from ..config.settings import AppConfig


@dataclass
class HistoryEntry:
    """Represents a single history entry with terminal operation support and user tracking."""

    path: Path
    timestamp: datetime
    operation: str = "navigate"  # navigate, clone, create_run, trash, restore, delete, terminal
    details: Optional[str] = None
    user: str = field(default_factory=getpass.getuser)  # Track which user created the entry

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'path': str(self.path),
            'timestamp': self.timestamp.isoformat(),
            'operation': self.operation,
            'details': self.details,
            'user': self.user
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HistoryEntry':
        """Create from dictionary."""
        return cls(
            path=Path(data['path']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            operation=data.get('operation', 'navigate'),
            details=data.get('details'),
            user=data.get('user', 'unknown')
        )

    @property
    def display_name(self) -> str:
        """Get display name for history entry."""
        name = self.path.name if self.path.name else str(self.path)
        if self.operation != "navigate":
            return f"{name} ({self.operation})"
        return name

    @property
    def tooltip_text(self) -> str:
        """Get tooltip text for history entry."""
        time_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        base_text = f"{self.operation.title()}: {self.path}\nTime: {time_str}\nUser: {self.user}"
        if self.details:
            base_text += f"\nDetails: {self.details}"
        return base_text

    @property
    def is_terminal_operation(self) -> bool:
        """Check if this is a terminal operation."""
        return self.operation == "terminal"


class DirectoryHistoryService(QObject):
    """Service for managing directory navigation and operation history with user-specific project storage."""

    # Signals
    history_changed = pyqtSignal()
    current_changed = pyqtSignal(Path, str)  # path, operation

    def __init__(self, config: AppConfig, max_history: int = 50):
        super().__init__()
        self.config = config
        self.max_history = max_history
        self.current_user = getpass.getuser()

        # History storage
        self.history: List[HistoryEntry] = []
        self.current_index: int = -1

        # Load user-specific history
        self.load_history()

    def get_history_file_path(self) -> Path:
        """Get user-specific history file path in project directory."""
        # Use project base directory: $casino_prj_base/$casino_prj_name
        if self.config.paths.base_directory.exists():
            # Store in project directory with user-specific filename
            return self.config.paths.base_directory / f".directory_history_{self.current_user}.json"
        else:
            # Fallback to user's home directory if project directory doesn't exist
            return Path.home() / f".treem_casino_history_{self.current_user}.json"

    def add_entry(self, path: Path, operation: str = "navigate", details: Optional[str] = None):
        """Add a new history entry with user information."""
        # Convert string path to Path object
        if isinstance(path, str):
            path = Path(path)

        # Don't add duplicate consecutive entries for navigation
        if (self.history and self.current_index >= 0 and
            self.current_index < len(self.history) and
            operation == "navigate" and
            self.history[self.current_index].path == path and
            self.history[self.current_index].operation == "navigate"):
            return

        # Create new entry with current user
        entry = HistoryEntry(
            path=path,
            timestamp=datetime.now(),
            operation=operation,
            details=details,
            user=self.current_user
        )

        # If we're in the middle of history, remove everything after current position
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]

        # Add new entry
        self.history.append(entry)
        self.current_index = len(self.history) - 1

        # Trim history if too long
        if len(self.history) > self.max_history:
            removed_count = len(self.history) - self.max_history
            self.history = self.history[removed_count:]
            self.current_index -= removed_count

        # Save and emit signals
        self.save_history()
        self.history_changed.emit()
        self.current_changed.emit(path, operation)

    def can_go_back(self) -> bool:
        """Check if we can go back in history."""
        return self.current_index > 0

    def can_go_forward(self) -> bool:
        """Check if we can go forward in history."""
        return self.current_index < len(self.history) - 1

    def go_back(self) -> Optional[HistoryEntry]:
        """Go back one step in history."""
        if self.can_go_back():
            self.current_index -= 1
            entry = self.history[self.current_index]
            self.history_changed.emit()
            self.current_changed.emit(entry.path, "navigate_back")
            return entry
        return None

    def go_forward(self) -> Optional[HistoryEntry]:
        """Go forward one step in history."""
        if self.can_go_forward():
            self.current_index += 1
            entry = self.history[self.current_index]
            self.history_changed.emit()
            self.current_changed.emit(entry.path, "navigate_forward")
            return entry
        return None

    def get_current_entry(self) -> Optional[HistoryEntry]:
        """Get current history entry."""
        if 0 <= self.current_index < len(self.history):
            return self.history[self.current_index]
        return None

    def get_back_entries(self, count: int = 10) -> List[HistoryEntry]:
        """Get recent back entries for dropdown menu."""
        if self.current_index <= 0:
            return []

        start_idx = max(0, self.current_index - count)
        return self.history[start_idx:self.current_index][::-1]  # Reverse for recent first

    def get_forward_entries(self, count: int = 10) -> List[HistoryEntry]:
        """Get forward entries for dropdown menu."""
        if self.current_index >= len(self.history) - 1:
            return []

        end_idx = min(len(self.history), self.current_index + count + 1)
        return self.history[self.current_index + 1:end_idx]

    def get_recent_operations(self, operation_type: str = None, count: int = 10, user_only: bool = True) -> List[HistoryEntry]:
        """Get recent operations of a specific type, optionally filtered by current user."""
        entries = []
        history_to_check = self.get_user_entries_only() if user_only else self.history

        for entry in reversed(history_to_check):
            if operation_type is None or entry.operation == operation_type:
                entries.append(entry)
                if len(entries) >= count:
                    break
        return entries

    def get_user_entries_only(self) -> List[HistoryEntry]:
        """Get only entries created by current user."""
        return [entry for entry in self.history if entry.user == self.current_user]

    def get_operation_history(self) -> List[HistoryEntry]:
        """Get all non-navigation operations."""
        return [entry for entry in self.history if entry.operation != "navigate"]

    def jump_to_entry(self, entry: HistoryEntry) -> bool:
        """Jump to a specific history entry."""
        try:
            index = self.history.index(entry)
            self.current_index = index
            self.history_changed.emit()
            self.current_changed.emit(entry.path, "navigate_jump")
            return True
        except ValueError:
            return False

    def clear_history(self):
        """Clear all history."""
        self.history.clear()
        self.current_index = -1
        self.save_history()
        self.history_changed.emit()

    def save_history(self):
        """Save user-specific history to project directory."""
        try:
            history_file = self.get_history_file_path()
            history_file.parent.mkdir(parents=True, exist_ok=True)

            # Save with user and project metadata
            data = {
                'user': self.current_user,
                'project_base': str(self.config.paths.project_base),
                'project_name': self.config.paths.project_name,
                'history': [entry.to_dict() for entry in self.history],
                'current_index': self.current_index,
                'saved_at': datetime.now().isoformat(),
                'version': '2.0'
            }

            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2)

            print(f"Saved {len(self.history)} history entries for user {self.current_user} to {history_file}")

        except Exception as e:
            print(f"Warning: Could not save history for user {self.current_user}: {e}")

    def load_history(self):
        """Load user-specific history from project directory."""
        try:
            history_file = self.get_history_file_path()
            if not history_file.exists():
                print(f"No history file found for user {self.current_user} at {history_file}")
                # Try to migrate from old shared location
                self.migrate_shared_history()
                return

            with open(history_file, 'r') as f:
                data = json.load(f)

            # Verify this history belongs to current user
            saved_user = data.get('user', 'unknown')
            if saved_user != self.current_user:
                print(f"Warning: History file belongs to {saved_user}, not {self.current_user}")
                # Start fresh for security
                return

            # Load history entries
            self.history = [HistoryEntry.from_dict(entry_data) for entry_data in data.get('history', [])]
            self.current_index = data.get('current_index', -1)

            # Validate current_index
            if self.current_index >= len(self.history):
                self.current_index = len(self.history) - 1

            print(f"Loaded {len(self.history)} history entries for user {self.current_user}")

        except Exception as e:
            print(f"Warning: Could not load history for user {self.current_user}: {e}")
            self.history = []
            self.current_index = -1

    def migrate_shared_history(self):
        """Migrate from old shared history location to project-specific location."""
        # Try old shared directory location
        old_shared_file = self.config.paths.shared_dir / "directory_history.json"
        if old_shared_file.exists():
            self._migrate_from_file(old_shared_file)
            return

        # Try old home directory location
        old_home_file = Path.home() / ".treem_casino_history.json"
        if old_home_file.exists():
            self._migrate_from_file(old_home_file)

    def _migrate_from_file(self, old_file: Path):
        """Migrate history from an old file location."""
        try:
            with open(old_file, 'r') as f:
                old_data = json.load(f)

            # Filter entries for current user or entries without user info
            old_entries = old_data.get('history', [])
            user_entries = []

            for entry_data in old_entries:
                entry = HistoryEntry.from_dict(entry_data)
                # Include entries that belong to current user or have no user info (legacy)
                if entry.user == self.current_user or entry.user == 'unknown':
                    entry.user = self.current_user  # Claim legacy entries
                    user_entries.append(entry)

            if user_entries:
                self.history = user_entries
                self.current_index = len(self.history) - 1
                self.save_history()
                print(f"Migrated {len(user_entries)} entries from {old_file} to user-specific project history")

        except Exception as e:
            print(f"Warning: Could not migrate history from {old_file}: {e}")

    # Operation-specific methods
    def add_navigation(self, path: Path):
        """Add navigation entry."""
        self.add_entry(path, "navigate")

    def add_terminal_operation(self, path: Path):
        """Add terminal operation entry with special details."""
        details = f"GoGoGo terminal opened at {path.name}"
        self.add_entry(path, "terminal", details)

    def add_clone_operation(self, source_path: Path, dest_path: Path):
        """Add clone operation entry."""
        details = f"Cloned to: {dest_path.name}"
        self.add_entry(source_path, "clone", details)
        # Also add navigation to destination
        self.add_entry(dest_path, "navigate")

    def add_create_run_operation(self, run_path: Path):
        """Add create run directory operation."""
        details = f"Created run directory: {run_path.name}"
        self.add_entry(run_path.parent, "create_run", details)
        # Also add navigation to new run directory
        self.add_entry(run_path, "navigate")

    def add_trash_operation(self, paths: List[Path], trash_path: Path):
        """Add trash operation entry."""
        details = f"Moved {len(paths)} items to trash"
        # Add entry for the parent directory where items were moved from
        if paths:
            self.add_entry(paths[0].parent, "trash", details)
        # Add navigation to trash bin
        self.add_entry(trash_path, "navigate")

    def add_restore_operation(self, paths: List[Path]):
        """Add restore operation entry."""
        details = f"Restored {len(paths)} items from trash"
        if paths:
            # Add entry for trash bin
            trash_bin = paths[0].parent
            self.add_entry(trash_bin, "restore", details)
            # Add navigation to restored location
            restored_location = trash_bin.parent
            self.add_entry(restored_location, "navigate")

    def add_delete_operation(self, paths: List[Path]):
        """Add delete operation entry with specific directory names."""
        if not paths:
            return

        # Create detailed list of deleted directories
        deleted_names = [path.name for path in paths]

        if len(deleted_names) == 1:
            details = f"Permanently deleted: {deleted_names[0]}"
        elif len(deleted_names) <= 3:
            details = f"Permanently deleted: {', '.join(deleted_names)}"
        else:
            details = f"Permanently deleted: {', '.join(deleted_names[:3])}, and {len(deleted_names) - 3} more"

        self.add_entry(paths[0].parent, "delete", details)
