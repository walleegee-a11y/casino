"""
Memo service for managing directory memos.
Handles persistent storage, real-time sync, and memo operations.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QFileSystemWatcher, QTimer

from ..models.memo import Memo, MemoCollection
from ..config.settings import AppConfig


class MemoService(QObject):
    """Service for managing directory memos with real-time synchronization."""

    # Signals
    memo_added = pyqtSignal(Path, Memo)
    memo_updated = pyqtSignal(Path, Memo)
    memo_removed = pyqtSignal(Path)
    memos_loaded = pyqtSignal(MemoCollection)
    sync_error = pyqtSignal(str)

    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self.memo_collection = MemoCollection()
        self.file_watcher = QFileSystemWatcher()

        # Timer for debouncing file changes
        self.sync_timer = QTimer()
        self.sync_timer.setSingleShot(True)
        self.sync_timer.timeout.connect(self._reload_memos)

        # Setup file watching
        self._setup_file_watcher()

        # Load initial memos
        self.load_memos()

    def _setup_file_watcher(self):
        """Setup file system watcher for memo file."""
        memo_dir = self.config.paths.memo_file.parent

        # Ensure directory exists
        self.config.ensure_shared_directory()

        # Watch directory and file
        if memo_dir.exists():
            self.file_watcher.addPath(str(memo_dir))
            if self.config.paths.memo_file.exists():
                self.file_watcher.addPath(str(self.config.paths.memo_file))

        # Connect signals
        self.file_watcher.directoryChanged.connect(self._on_file_changed)
        self.file_watcher.fileChanged.connect(self._on_file_changed)

    def _on_file_changed(self, path: str):
        """Handle file system changes with debouncing."""
        # Debounce file changes to avoid multiple rapid reloads
        self.sync_timer.start(self.config.ui.file_watch_delay)

    def load_memos(self) -> bool:
        """Load memos from file."""
        try:
            if self.config.paths.memo_file.exists():
                with open(self.config.paths.memo_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}

                self.memo_collection = MemoCollection.from_dict(data)
                self.memos_loaded.emit(self.memo_collection)
                return True
            else:
                # Initialize empty collection
                self.memo_collection = MemoCollection()
                self.memos_loaded.emit(self.memo_collection)
                return True

        except Exception as e:
            self.sync_error.emit(f"Error loading memos: {e}")
            return False

    def _reload_memos(self):
        """Reload memos from file (called by timer)."""
        try:
            if self.config.paths.memo_file.exists():
                with open(self.config.paths.memo_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}

                new_collection = MemoCollection.from_dict(data)

                # Check for changes and emit appropriate signals
                self._detect_changes(new_collection)

                self.memo_collection = new_collection
        except Exception as e:
            self.sync_error.emit(f"Error reloading memos: {e}")

    def _detect_changes(self, new_collection: MemoCollection):
        """Detect changes between old and new memo collections."""
        old_paths = set(self.memo_collection.memos.keys())
        new_paths = set(new_collection.memos.keys())

        # Detect added memos
        for path in new_paths - old_paths:
            self.memo_added.emit(path, new_collection.memos[path])

        # Detect removed memos
        for path in old_paths - new_paths:
            self.memo_removed.emit(path)

        # Detect updated memos
        for path in old_paths & new_paths:
            old_memo = self.memo_collection.memos[path]
            new_memo = new_collection.memos[path]

            if old_memo.to_dict() != new_memo.to_dict():
                self.memo_updated.emit(path, new_memo)

    def save_memos(self) -> bool:
        """Save memos to file."""
        try:
            # Temporarily remove file watcher to avoid triggering our own changes
            if self.config.paths.memo_file.exists():
                self.file_watcher.removePath(str(self.config.paths.memo_file))

            # Ensure directory exists
            self.config.ensure_shared_directory()

            # Save memos
            with open(self.config.paths.memo_file, 'w', encoding='utf-8') as f:
                yaml.dump(
                    self.memo_collection.to_dict(),
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True
                )

            # Re-add file watcher
            if self.config.paths.memo_file.exists():
                self.file_watcher.addPath(str(self.config.paths.memo_file))

            return True

        except Exception as e:
            # Ensure watcher is re-added even on error
            if self.config.paths.memo_file.exists():
                self.file_watcher.addPath(str(self.config.paths.memo_file))

            self.sync_error.emit(f"Error saving memos: {e}")
            return False

    def add_memo(self, path: Path, text: str) -> bool:
        """Add or update a memo for a directory."""
        try:
            memo = Memo(text=text)
            self.memo_collection.add_memo(path, memo)

            if self.save_memos():
                self.memo_added.emit(path, memo)
                return True
            return False

        except Exception as e:
            self.sync_error.emit(f"Error adding memo: {e}")
            return False

    def update_memo(self, path: Path, text: str) -> bool:
        """Update an existing memo."""
        try:
            existing_memo = self.memo_collection.get_memo(path)
            if existing_memo:
                existing_memo.update_text(text)
            else:
                # Create new memo if it doesn't exist
                memo = Memo(text=text)
                self.memo_collection.add_memo(path, memo)

            if self.save_memos():
                self.memo_updated.emit(path, self.memo_collection.get_memo(path))
                return True
            return False

        except Exception as e:
            self.sync_error.emit(f"Error updating memo: {e}")
            return False

    def remove_memo(self, path: Path) -> bool:
        """Remove a memo for a directory."""
        try:
            if self.memo_collection.remove_memo(path):
                if self.save_memos():
                    self.memo_removed.emit(path)
                    return True
            return False

        except Exception as e:
            self.sync_error.emit(f"Error removing memo: {e}")
            return False

    def get_memo(self, path: Path) -> Optional[Memo]:
        """Get memo for a directory."""
        return self.memo_collection.get_memo(path)

    def has_memo(self, path: Path) -> bool:
        """Check if directory has a memo."""
        return self.memo_collection.has_memo(path)

    def search_memos(self, query: str) -> List[Path]:
        """Search for directories with memos containing query."""
        return self.memo_collection.search_memos(query)

    def get_all_memo_paths(self) -> List[Path]:
        """Get all directory paths that have memos."""
        return self.memo_collection.get_all_paths_with_memos()
