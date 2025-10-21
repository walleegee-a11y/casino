"""
Data models for directory and file system operations.
Provides type-safe representations of directory hierarchies and metadata.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import os
import stat



@dataclass
class DirectoryInfo:
    """Information about a single directory."""

    path: Path
    name: str = field(init=False)
    size: Optional[int] = None
    modified_time: Optional[datetime] = None
    permissions: Optional[str] = None
    is_symlink: bool = False
    is_empty: bool = False
    _metadata_loaded: bool = field(default=False, init=False)

    def __post_init__(self):
        """Initialize computed fields."""
        self.name = self.path.name
        # Don't load metadata by default - do it lazily
        # self._update_metadata()

    def _update_metadata(self, check_empty: bool = False):
        """Update directory metadata from filesystem.

        Args:
            check_empty: If True, check if directory is empty (expensive operation)
        """
        try:
            if self.path.exists():
                stat_info = self.path.stat()
                self.modified_time = datetime.fromtimestamp(stat_info.st_mtime)
                self.permissions = stat.filemode(stat_info.st_mode)
                self.is_symlink = self.path.is_symlink()

                # Only check if directory is empty when explicitly requested
                if check_empty and self.path.is_dir():
                    try:
                        self.is_empty = not any(self.path.iterdir())
                    except PermissionError:
                        self.is_empty = False

                self._metadata_loaded = True
        except (OSError, PermissionError):
            pass  # Keep defaults if we can't access the directory

    def ensure_metadata_loaded(self, check_empty: bool = False):
        """Ensure metadata is loaded, load if not already loaded."""
        if not self._metadata_loaded:
            self._update_metadata(check_empty=check_empty)

    @property
    def display_name(self) -> str:
        """Get display name with empty indicator if needed."""
        # Only show empty indicator if we actually checked
        if self._metadata_loaded and self.is_empty:
            return f"{self.name} (Empty)"
        return self.name

    def refresh(self, check_empty: bool = False):
        """Refresh metadata from filesystem."""
        self._metadata_loaded = False
        self._update_metadata(check_empty=check_empty)

@dataclass
class DirectoryHierarchy:
    """Represents a hierarchical directory structure."""

    root: DirectoryInfo
    children: Dict[Path, 'DirectoryHierarchy'] = field(default_factory=dict)
    depth: int = 0
    max_depth: int = 6

    @classmethod
    def from_path(
        cls,
        path: Path,
        max_depth: int = 6,
        current_depth: int = 0
    ) -> 'DirectoryHierarchy':
        """Create hierarchy from a filesystem path."""
        root_info = DirectoryInfo(path)
        hierarchy = cls(
            root=root_info,
            depth=current_depth,
            max_depth=max_depth
        )

        if current_depth < max_depth:
            hierarchy._load_children()

        return hierarchy

    def _load_children(self):
        """Load child directories."""
        if not self.root.path.is_dir():
            return

        try:
            for child_path in self.root.path.iterdir():
                if child_path.is_dir() and not child_path.is_symlink():
                    try:
                        child_hierarchy = DirectoryHierarchy.from_path(
                            child_path,
                            self.max_depth,
                            self.depth + 1
                        )
                        self.children[child_path] = child_hierarchy
                    except (OSError, PermissionError):
                        continue  # Skip inaccessible directories
        except (OSError, PermissionError):
            pass  # Can't read directory

    def get_all_paths(self) -> List[Path]:
        """Get all directory paths in the hierarchy."""
        paths = [self.root.path]
        for child in self.children.values():
            paths.extend(child.get_all_paths())
        return paths

    def find_directory(self, target_path: Path) -> Optional['DirectoryHierarchy']:
        """Find a specific directory in the hierarchy."""
        if self.root.path == target_path:
            return self

        for child in self.children.values():
            result = child.find_directory(target_path)
            if result:
                return result

        return None

    def calculate_max_depth(self) -> int:
        """Calculate the maximum depth of this hierarchy."""
        if not self.children:
            return self.depth

        return max(child.calculate_max_depth() for child in self.children.values())

    def filter_by_pattern(self, pattern: str) -> List[Path]:
        """Find directories matching a pattern."""
        matches = []

        if pattern in self.root.name:
            matches.append(self.root.path)

        for child in self.children.values():
            matches.extend(child.filter_by_pattern(pattern))

        return matches

    def refresh(self):
        """Refresh the entire hierarchy from filesystem."""
        self.root.refresh()

        # Clear and reload children
        self.children.clear()
        if self.depth < self.max_depth:
            self._load_children()


@dataclass
class DirectoryFilter:
    """Filter configuration for directory listings."""

    show_only_user_workspace: bool = False
    user_name: Optional[str] = None
    allowed_directories: List[str] = field(default_factory=list)
    sort_by: str = "mtime"  # "mtime" or "name"
    pattern_highlight: Optional[str] = None
    environment_pattern: Optional[str] = None

    def __post_init__(self):
        """Set default allowed directories."""
        if not self.allowed_directories:
            self.allowed_directories = ["FastTrack", "dbs", "outfeeds"]

    def should_include(self, directory_info: DirectoryInfo) -> bool:
        """Determine if a directory should be included based on filter."""
        if not self.show_only_user_workspace:
            return True

        if self.user_name:
            user_workspace = f"works_{self.user_name}"
            if directory_info.name == user_workspace:
                return True

        return directory_info.name in self.allowed_directories

    def get_sort_key(self, directory_info: DirectoryInfo) -> Any:
        """Get sort key for a directory."""
        is_works = directory_info.name.startswith("works_")

        if self.sort_by == "mtime":
            mtime = directory_info.modified_time
            if mtime:
                key_val = -mtime.timestamp()  # Negative for reverse order
            else:
                key_val = 0
        else:  # sort by name
            key_val = directory_info.name.lower()

        # Works directories first, then by sort criteria
        return (0 if is_works else 1, key_val)


@dataclass
class SearchResult:
    """Result from directory search operation."""

    path: Path
    name: str
    match_type: str  # "name", "pattern", "memo"
    relevance_score: float = 0.0
    context: Optional[str] = None

    def __post_init__(self):
        """Set name from path if not provided."""
        if not self.name:
            self.name = self.path.name
