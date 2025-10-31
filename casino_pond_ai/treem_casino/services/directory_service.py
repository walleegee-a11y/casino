"""
Fixed directory service with proper "Me only" filtering.
"""

import os
import shutil
import subprocess
import platform
import grp
from pathlib import Path
from typing import List, Dict, Optional, Union, Callable
from datetime import datetime  # ADD THIS LINE
from PyQt5.QtCore import QObject, pyqtSignal, QThread, QTimer

from ..models.directory import DirectoryHierarchy, DirectoryFilter, DirectoryInfo, SearchResult
from ..config.settings import AppConfig


class DirectoryScanner(QThread):
    """Background thread for scanning directory hierarchies with detailed progress reporting."""

    # Signals
    progress_updated = pyqtSignal(str, int)  # message, progress_percent
    scan_completed = pyqtSignal(DirectoryHierarchy)
    scan_error = pyqtSignal(str)

    def __init__(self, base_path: Path, max_depth: int = 6, fast_mode: bool = True):
        super().__init__()
        self.base_path = base_path
        self.max_depth = max_depth
        self.fast_mode = fast_mode  # Skip expensive metadata checks
        self._cancelled = False
        self.total_dirs_estimated = 0
        self.dirs_processed = 0
        self._visited_real_paths = set()  # Track visited real paths to prevent circular references

    def cancel(self):
        """Cancel the scanning operation."""
        self._cancelled = True

    def _estimate_directory_count(self, path: Path, current_depth: int = 0, visited: Optional[set] = None) -> int:
        """Estimate total number of directories to scan for progress calculation."""
        if current_depth >= self.max_depth or self._cancelled:
            return 0

        # Initialize visited set on first call
        if visited is None:
            visited = set()

        # Get real path to check for circular references
        try:
            real_path = path.resolve()
        except (OSError, PermissionError):
            return 0

        # Skip if already visited (prevents circular references)
        if real_path in visited:
            return 0

        visited.add(real_path)
        count = 1  # Count current directory

        try:
            for child_path in path.iterdir():
                if self._cancelled:
                    break

                if child_path.is_dir():
                    # Now recurse into ALL directories including symlinks
                    try:
                        count += self._estimate_directory_count(child_path, current_depth + 1, visited)
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            pass

        return count

    def _scan_with_progress(self, path: Path, max_depth: int, current_depth: int = 0) -> DirectoryHierarchy:
        """Scan directory hierarchy with progress reporting - OPTIMIZED."""
        if self._cancelled:
            return None

        # Check for circular references using real path
        try:
            real_path = path.resolve()
        except (OSError, PermissionError):
            return None

        # Skip if already visited (prevents circular references with symlinks)
        if real_path in self._visited_real_paths:
            return None

        self._visited_real_paths.add(real_path)

        # Update progress every 10 directories to reduce signal overhead
        self.dirs_processed += 1
        if self.dirs_processed % 10 == 0 or self.dirs_processed == 1:
            progress_percent = min(95, int((self.dirs_processed / max(self.total_dirs_estimated, 1)) * 100))
            dir_name = path.name if path.name else str(path)
            depth_info = f"depth {current_depth}/{max_depth}"
            message = f"Scanning {dir_name} ({depth_info}) - {self.dirs_processed}/{self.total_dirs_estimated} dirs"
            self.progress_updated.emit(message, progress_percent)

        # Create directory info
        root_info = DirectoryInfo(path)

        # OPTIMIZED: In fast mode, skip ALL metadata loading initially
        if self.fast_mode:
            # Mark as not loaded - will lazy load on demand
            root_info._metadata_loaded = False
        else:
            # Normal mode: load metadata
            root_info.ensure_metadata_loaded(check_empty=False)

        # Create hierarchy object
        hierarchy = DirectoryHierarchy(
            root=root_info,
            depth=current_depth,
            max_depth=max_depth
        )

        # Load children if within depth limit
        if current_depth < max_depth and not self._cancelled:
            self._load_children_with_progress(hierarchy, path, current_depth)

        return hierarchy

    def _load_children_with_progress(self, hierarchy: DirectoryHierarchy, path: Path, current_depth: int):
        """Load child directories with progress reporting - OPTIMIZED with os.scandir."""
        if self._cancelled:
            return

        try:
            child_paths = []

            # OPTIMIZED: Use os.scandir() instead of pathlib - much faster!
            import os
            with os.scandir(str(path)) as entries:
                for entry in entries:
                    if self._cancelled:
                        break

                    try:
                        # os.scandir caches stat info - very fast
                        # Include symlinks by checking is_dir with follow_symlinks=True
                        if entry.is_dir(follow_symlinks=True):
                            child_paths.append(Path(entry.path))
                    except (OSError, PermissionError):
                        continue  # Skip inaccessible entries

            # Process each child with progress updates
            for child_path in child_paths:
                if self._cancelled:
                    break

                try:
                    # Recurse into ALL directories (including symlinks)
                    # Circular reference protection is handled in _scan_with_progress
                    child_hierarchy = self._scan_with_progress(
                        child_path,
                        hierarchy.max_depth,
                        current_depth + 1
                    )
                    if child_hierarchy:
                        hierarchy.children[child_path] = child_hierarchy

                except (OSError, PermissionError):
                    continue  # Skip inaccessible directories

        except (OSError, PermissionError):
            pass  # Can't read directory

    def run(self):
        """Run the directory scanning in background with detailed progress."""
        try:
            self.progress_updated.emit("Initializing directory scan...", 0)

            if not self.base_path.exists():
                self.scan_error.emit(f"Directory does not exist: {self.base_path}")
                return

            # Skip estimation in fast mode - it's slow!
            if self.fast_mode:
                self.total_dirs_estimated = 1000  # Rough estimate to avoid division by zero
                self.progress_updated.emit("Starting fast directory scan...", 5)
            else:
                self.progress_updated.emit("Estimating scan scope...", 5)
                self.total_dirs_estimated = self._estimate_directory_count(self.base_path)

            if self._cancelled:
                return

            self.progress_updated.emit(f"Starting scan of {self.total_dirs_estimated} directories...", 10)
            self.dirs_processed = 0

            # Perform the actual scan
            hierarchy = self._scan_with_progress(
                self.base_path,
                max_depth=self.max_depth
            )

            if not self._cancelled and hierarchy:
                self.progress_updated.emit("Finalizing directory tree...", 98)
                # Small delay to show completion message
                self.msleep(200)

                self.progress_updated.emit("Directory scan completed successfully!", 100)
                self.scan_completed.emit(hierarchy)

        except Exception as e:
            if not self._cancelled:
                error_msg = f"Scan error: {str(e)}"
                self.scan_error.emit(error_msg)

class DirectoryService(QObject):
    """Service for directory operations and management."""

    # Signals
    hierarchy_updated = pyqtSignal(DirectoryHierarchy)
    operation_completed = pyqtSignal(str, bool)  # operation_name, success
    progress_updated = pyqtSignal(str, int)

    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self._current_hierarchy: Optional[DirectoryHierarchy] = None
        self._scanner: Optional[DirectoryScanner] = None

    def scan_directory_async(self, base_path: Path, fast_mode: bool = True):
        """Scan directory hierarchy asynchronously.

        Args:
            base_path: Directory to scan
            fast_mode: If True, skip expensive metadata checks (much faster)
        """
        if self._scanner and self._scanner.isRunning():
            self._scanner.cancel()
            self._scanner.wait()

        self._scanner = DirectoryScanner(
            base_path,
            self.config.ui.max_directory_depth,
            fast_mode=fast_mode
        )
        self._scanner.progress_updated.connect(self.progress_updated)
        self._scanner.scan_completed.connect(self._on_scan_completed)
        self._scanner.scan_error.connect(self._on_scan_error)
        self._scanner.start()

    def _on_scan_completed(self, hierarchy: DirectoryHierarchy):
        """Handle completed directory scan."""
        self._current_hierarchy = hierarchy
        self.hierarchy_updated.emit(hierarchy)
        self.operation_completed.emit("directory_scan", True)

    def _on_scan_error(self, error: str):
        """Handle directory scan error."""
        self.operation_completed.emit(f"directory_scan_error: {error}", False)

    def get_current_hierarchy(self) -> Optional[DirectoryHierarchy]:
        """Get the current directory hierarchy."""
        return self._current_hierarchy

    # Fix for directory_service.py - apply_filter method

    def apply_filter(
        self,
        hierarchy: DirectoryHierarchy,
        filter_config: DirectoryFilter
    ) -> DirectoryHierarchy:
        """Apply filter to directory hierarchy - FIXED for Me only mode."""

        def should_include_directory(dir_info: DirectoryInfo, is_root_level: bool = False) -> bool:
            """Determine if directory should be included - FIXED logic."""
            if not filter_config.show_only_user_workspace:
                # Show all directories when "Me only" is not selected
                return True

            dir_name = dir_info.name

            # At root level, apply the "Me only" filter
            if is_root_level:
                # FIXED: Always include allowed directories (outfeeds, FastTrack, dbs)
                if dir_name in filter_config.allowed_directories:
                    return True

                # Include current user's workspace
                if filter_config.user_name:
                    user_workspace = f"works_{filter_config.user_name}"
                    if dir_name == user_workspace:
                        return True

                # FIXED: Exclude other users' workspaces but allow non-workspace directories
                # Only filter out directories that start with "works_" but are NOT the current user's
                if dir_name.startswith("works_"):
                    # This is a workspace directory
                    if filter_config.user_name:
                        user_workspace = f"works_{filter_config.user_name}"
                        return dir_name == user_workspace
                    else:
                        return False  # No user specified, hide all workspaces

                # FIXED: Allow all other directories (like hawkeye_archive, etc.)
                # The "Me only" filter should only hide OTHER USERS' works_ directories
                return True

            # For subdirectories (not root level), include everything
            return True

        def filter_hierarchy_recursive(source_hierarchy: DirectoryHierarchy, is_root: bool = False) -> DirectoryHierarchy:
            """Recursively filter hierarchy."""
            # Create filtered hierarchy
            filtered = DirectoryHierarchy(
                root=source_hierarchy.root,
                depth=source_hierarchy.depth,
                max_depth=source_hierarchy.max_depth
            )

            # Filter children
            for path, child_hierarchy in source_hierarchy.children.items():
                if should_include_directory(child_hierarchy.root, is_root):
                    # Recursively filter child
                    filtered_child = filter_hierarchy_recursive(child_hierarchy, False)
                    filtered.children[path] = filtered_child

            return filtered

        return filter_hierarchy_recursive(hierarchy, True)

    def search_directories(
        self,
        query: str,
        hierarchy: Optional[DirectoryHierarchy] = None
    ) -> List[SearchResult]:
        """Search for directories matching query."""
        if hierarchy is None:
            hierarchy = self._current_hierarchy

        if not hierarchy:
            return []

        results = []
        query_lower = query.lower()

        # Search in current directory
        if query_lower in hierarchy.root.name.lower():
            results.append(SearchResult(
                path=hierarchy.root.path,
                name=hierarchy.root.name,
                match_type="name",
                relevance_score=self._calculate_relevance(query, hierarchy.root.name)
            ))

        # Search in children
        for child in hierarchy.children.values():
            results.extend(self.search_directories(query, child))

        # Sort by relevance
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results

    def _calculate_relevance(self, query: str, text: str) -> float:
        """Calculate relevance score for search results."""
        query_lower = query.lower()
        text_lower = text.lower()

        if text_lower == query_lower:
            return 1.0
        elif text_lower.startswith(query_lower):
            return 0.8
        elif query_lower in text_lower:
            return 0.6
        else:
            return 0.0

    def open_terminal(self, path: Path) -> bool:
        """Open terminal at specified path."""
        if platform.system() != "Linux":
            self.operation_completed.emit("Terminal opening only supported on Linux", False)
            return False

        try:
            current_gid = os.getgid()
            group_info = grp.getgrgid(current_gid)
            group_name = group_info.gr_name

            # Create terminal title
            path_parts = path.parts
            title_suffix = "/".join(path_parts[-4:]) if len(path_parts) >= 4 else str(path)
            terminal_title = f"GoGoGo - ({title_suffix})"

            # Terminal command
            terminal_command = f"cd {path}; newgrp {group_name} && exec csh"

            # Launch terminal with custom colors
            subprocess.Popen([
                "gnome-terminal",
                "--title", terminal_title,
                "--geometry", self.config.ui.terminal_geometry,
                "--working-directory", str(path),
                "--", "csh", "-c",
                f'printf "\\033]11;{self.config.ui.terminal_bg_color}\\007"; '
                f'printf "\\033]10;{self.config.ui.terminal_fg_color}\\007"; '
                f'{terminal_command}'
            ])

            self.operation_completed.emit("Terminal opened", True)
            return True

        except Exception as e:
            self.operation_completed.emit(f"terminal_error: {str(e)}", False)
            return False
