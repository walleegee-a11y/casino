"""
Tree model implementation with FIXED color highlighting logic and memo tooltips.
Supports proper priority handling for overlapping patterns and recursive coloring.
"""

import getpass
from pathlib import Path
from typing import Optional, Any, Dict, List
from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt, QVariant
from PyQt5.QtGui import QFont, QColor, QBrush

from ..models.directory import DirectoryHierarchy, DirectoryFilter
from ..models.memo import MemoCollection
from ..config.settings import AppConfig


class TreeItem:
    """A tree item that holds directory information - with lazy loading optimization."""

    def __init__(self, directory_hierarchy: DirectoryHierarchy, parent: Optional['TreeItem'] = None):
        self.directory_hierarchy = directory_hierarchy
        self.parent_item = parent
        self.child_items: List['TreeItem'] = []
        self.memo_collection: Optional[MemoCollection] = None

        # OPTIMIZATION: Lazy loading - don't create children until needed
        self._children_loaded = False
        self._children_sorted = False  # Track if children have been sorted

        # Old code (removed):
        # for child_hierarchy in directory_hierarchy.children.values():
        #     child_item = TreeItem(child_hierarchy, self)
        #     self.child_items.append(child_item)

    def _ensure_children_loaded(self):
        """Ensure children are loaded. Called by all methods that access children."""
        if self._children_loaded:
            return  # Already loaded

        # Load children now
        for child_hierarchy in self.directory_hierarchy.children.values():
            child_item = TreeItem(child_hierarchy, self)
            if self.memo_collection:
                # Inherit memo collection from parent
                child_item.memo_collection = self.memo_collection
            # Inherit model reference for sorting
            if hasattr(self, '_model'):
                child_item._model = self._model
            self.child_items.append(child_item)

        # Mark as loaded BEFORE sorting to avoid recursion
        self._children_loaded = True

        # OPTIMIZATION: Defer sorting to avoid slowdown
        # Sort in a separate step, not during initial load
        # This is now called explicitly via _ensure_children_sorted()

    def _ensure_children_sorted(self):
        """Ensure children are sorted. Called separately from loading."""
        if not self._children_loaded:
            return  # Can't sort if not loaded yet

        if self._children_sorted:
            return  # Already sorted

        # Only sort if we have a model reference with filter config
        if hasattr(self, '_model') and self._model:
            try:
                sort_key = lambda item: self._model.filter_config.get_sort_key(item.directory_hierarchy.root)
                self.child_items.sort(key=sort_key)
                self._children_sorted = True  # Mark as sorted
            except Exception:
                pass  # If sorting fails, just leave unsorted

    def child(self, row: int) -> Optional['TreeItem']:
        """Get child item at row - loads and sorts children if needed."""
        self._ensure_children_loaded()  # Lazy load trigger
        self._ensure_children_sorted()  # Lazy sort trigger

        if 0 <= row < len(self.child_items):
            return self.child_items[row]
        return None

    def child_count(self) -> int:
        """Get number of child items - returns count without loading children."""
        # OPTIMIZATION: Can return count from hierarchy without creating TreeItems
        if not self._children_loaded:
            return len(self.directory_hierarchy.children)
        return len(self.child_items)

    def column_count(self) -> int:
        """Get number of columns."""
        return 1

    def data(self, column: int = 0) -> Any:
        """Get data for column."""
        if column == 0:
            name = self.directory_hierarchy.root.display_name
            # Add memo first line instead of "*"
            if self.memo_collection and self.memo_collection.has_memo(self.directory_hierarchy.root.path):
                memo = self.memo_collection.get_memo(self.directory_hierarchy.root.path)
                if memo:
                    # Get first line of memo text
                    first_line = memo.text.split('\n')[0].strip()
                    if len(first_line) > 50:  # Limit length
                        first_line = first_line[:47] + "..."
                    return f"{name} : {first_line}"
            return name
        return None

    def parent(self) -> Optional['TreeItem']:
        """Get parent item."""
        return self.parent_item

    def row(self) -> int:
        """Get row number in parent - loads parent's children if needed."""
        if self.parent_item:
            self.parent_item._ensure_children_loaded()  # Ensure parent has loaded us
            return self.parent_item.child_items.index(self)
        return 0

    def path(self) -> Path:
        """Get directory path."""
        return self.directory_hierarchy.root.path

    def set_memo_collection(self, memo_collection: MemoCollection):
        """Set memo collection for memo indicators - propagates to loaded children only."""
        self.memo_collection = memo_collection

        # Only propagate to children if they're already loaded
        # When children are loaded later, they'll inherit from parent
        if self._children_loaded:
            for child in self.child_items:
                child.set_memo_collection(memo_collection)
                # Also pass model reference if we have it
                if hasattr(self, '_model'):
                    child._model = self._model


class DirectoryTreeModel(QAbstractItemModel):
    """Qt model for directory tree display with proper color highlighting and memo tooltips."""

    def __init__(self, hierarchy: DirectoryHierarchy, filter_config: DirectoryFilter,
                 memo_collection: MemoCollection, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.filter_config = filter_config
        self.memo_collection = memo_collection

        # Create root item (with reference to model for lazy sorting)
        self.root_item = TreeItem(hierarchy)
        self.root_item.set_memo_collection(memo_collection)
        self.root_item._model = self  # Pass model reference for sorting

        # OPTIMIZATION: Don't sort upfront! Sorting will happen lazily when children are loaded
        # Old code (removed - this was causing the 95% hang):
        # self._sort_items()

        # Highlighting patterns with priorities
        self.highlight_patterns: Dict[str, Dict[str, Any]] = {}  # pattern -> {color: str, priority: int}

    def _sort_items(self):
        """Sort tree items according to filter configuration."""
        def sort_key(item: TreeItem):
            return self.filter_config.get_sort_key(item.directory_hierarchy.root)

        self._sort_item_recursive(self.root_item, sort_key)

    def _sort_item_recursive(self, item: TreeItem, sort_key_func):
        """Recursively sort tree items - loads children if needed."""
        # Trigger lazy loading before sorting
        item._ensure_children_loaded()

        # Sort the items
        item.child_items.sort(key=sort_key_func)
        item._children_sorted = True  # Mark as sorted

        # Recurse into children
        for child in item.child_items:
            self._sort_item_recursive(child, sort_key_func)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Get number of columns."""
        return 1

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """Get data for model index with FIXED tooltip behavior."""
        if not index.isValid():
            return QVariant()

        item = index.internalPointer()
        if not isinstance(item, TreeItem):
            return QVariant()

        if role == Qt.DisplayRole:
            return item.data(index.column())

        elif role == Qt.UserRole:
            # Return path as string for external use
            return str(item.path())

        elif role == Qt.FontRole:
            font = QFont(*self.config.fonts.get_font_tuple())
            item_text = item.data(index.column()) or ""

            # Check if this item has memo text (contains " : ")
            if " : " in item_text:
                # This has memo text - make the entire text smaller and italic
                font.setPointSize(font.pointSize() - 1)  # Smaller font
                font.setItalic(True)  # Italic font
                return font

            # Bold font ONLY for current user's workspace
            username = getpass.getuser()
            user_workspace_pattern = f"works_{username}"

            # Check if this is exactly the user's workspace (for exact match) or contains it
            dir_name_part = item_text.split(" : ")[0] if " : " in item_text else item_text
            if dir_name_part == user_workspace_pattern or user_workspace_pattern in dir_name_part:
                font.setBold(True)

            return font

        elif role == Qt.ForegroundRole:
            item_text = item.data(index.column()) or ""
            item_path = item.path()

            # Check if this is a symlink - give it special color (highest priority)
            if item.directory_hierarchy.root.is_symlink:
                # Symlinks shown in violet color
                return QBrush(QColor("#9932CC"))  # Violet color

            # Check if this item is under works_{whoami} directory
            is_under_user_workspace = False
            username = getpass.getuser()
            user_workspace_pattern = f"works_{username}"

            # Check if current item or any parent contains user workspace
            current_path = item_path
            while current_path != current_path.parent:
                if user_workspace_pattern in str(current_path):
                    is_under_user_workspace = True
                    break
                current_path = current_path.parent

            # Find the highest priority matching pattern
            best_match = None
            highest_priority = -1

            for pattern, pattern_info in self.highlight_patterns.items():
                is_exact_match = pattern_info.get('exact_match', False)

                # Check if pattern matches - handle memo format "name : memo text"
                pattern_matches = False
                if is_exact_match:
                    # For exact match, check the directory name part (before " : ")
                    dir_name_part = item_text.split(" : ")[0] if " : " in item_text else item_text
                    pattern_matches = (dir_name_part == pattern)
                else:
                    # For normal match, pattern can be contained in the directory name part
                    dir_name_part = item_text.split(" : ")[0] if " : " in item_text else item_text
                    pattern_matches = (pattern in dir_name_part)

                if pattern_matches:
                    priority = pattern_info.get('priority', 0)
                    if priority > highest_priority:
                        highest_priority = priority
                        best_match = pattern_info

            # Apply recursive brown color for items under user workspace
            if is_under_user_workspace and not best_match:
                # Apply brown color for items under user workspace that don't have other patterns
                color = QColor("brown")
                return QBrush(color)

            if best_match:
                color = QColor(best_match['color'])
                return QBrush(color)

            # Default text color
            default_color = QColor(self.config.colors.text_primary)
            return QBrush(default_color)

        elif role == Qt.ToolTipRole:
            # FIXED: Show ONLY memo information in tooltip when hovering
            item_path = item.path()

            if self.memo_collection.has_memo(item_path):
                memo = self.memo_collection.get_memo(item_path)
                if memo:
                    # Show only memo information - more concise
                    tooltip_parts = []
                    tooltip_parts.append(f"Memo by {memo.user} ({memo.formatted_timestamp}):")
                    tooltip_parts.append(memo.text)
                    return "\n".join(tooltip_parts)

            # No tooltip if no memo - let users hover only when needed
            return QVariant()

        return QVariant()

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """Get item flags."""
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        """Get header data."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole and section == 0:
            return "Directories"
        return QVariant()

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        """Create model index."""
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        else:
            return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        """Get parent model index."""
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent()

        if parent_item == self.root_item or parent_item is None:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Get number of rows."""
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        return parent_item.child_count()

    def highlight_pattern(self, pattern: str, color_string: str, priority: int = 1, exact_match: bool = False):
        """Add pattern highlighting with priority and exact match support."""
        self.highlight_patterns[pattern] = {
            'color': color_string,
            'priority': priority,
            'exact_match': exact_match
        }

        print(f"DEBUG: Added highlighting pattern '{pattern}' with color '{color_string}', priority {priority}, exact_match: {exact_match}")

        # Emit data changed for all items
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(self.rowCount() - 1, 0),
            [Qt.ForegroundRole, Qt.FontRole]
        )

    def clear_highlighting(self):
        """Clear all pattern highlighting."""
        self.highlight_patterns.clear()

        # Emit data changed for all items
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(self.rowCount() - 1, 0),
            [Qt.ForegroundRole, Qt.FontRole]
        )

    def find_pattern_indexes(self, pattern: str) -> List[QModelIndex]:
        """Find all indexes matching a pattern."""
        matches = []
        self._find_pattern_recursive(self.root_item, pattern, matches)
        return matches

    def find_pattern_index(self, pattern: str) -> Optional[QModelIndex]:
        """Find first index matching a pattern."""
        matches = self.find_pattern_indexes(pattern)
        return matches[0] if matches else None

    def _find_pattern_recursive(self, item: TreeItem, pattern: str, matches: List[QModelIndex]):
        """Recursively find pattern matches - loads children if needed."""
        # Trigger lazy loading before iterating
        item._ensure_children_loaded()

        for row, child in enumerate(item.child_items):
            child_text = child.data(0) or ""
            if pattern in child_text:
                index = self.createIndex(row, 0, child)
                matches.append(index)

            # Recurse into children
            self._find_pattern_recursive(child, pattern, matches)

    def find_path_index(self, target_path: Path) -> Optional[QModelIndex]:
        """Find index for a specific path."""
        return self._find_path_recursive(self.root_item, target_path)

    def _find_path_recursive(self, item: TreeItem, target_path: Path) -> Optional[QModelIndex]:
        """Recursively find path index - loads children if needed."""
        # Trigger lazy loading before iterating
        item._ensure_children_loaded()

        for row, child in enumerate(item.child_items):
            if child.path() == target_path:
                return self.createIndex(row, 0, child)

            # Recurse into children
            result = self._find_path_recursive(child, target_path)
            if result:
                return result

        return None

    def get_item_depth(self, index: QModelIndex) -> int:
        """Get depth of item in tree."""
        depth = 0
        current = index

        while current.isValid():
            current = self.parent(current)
            depth += 1

        return depth

    def expand_to_depth(self, tree_view, target_depth: int):
        """Expand tree view to specified depth."""
        tree_view.collapseAll()

        if target_depth <= 0:
            return

        # Expand items up to target depth
        self._expand_to_depth_recursive(tree_view, QModelIndex(), 0, target_depth)

    def _expand_to_depth_recursive(self, tree_view, parent_index: QModelIndex, current_depth: int, target_depth: int):
        """Recursively expand items to target depth."""
        if current_depth > target_depth:
            return

        # Expand current level
        if parent_index.isValid():
            tree_view.setExpanded(parent_index, True)

        # Process children
        row_count = self.rowCount(parent_index)
        for row in range(row_count):
            child_index = self.index(row, 0, parent_index)
            if child_index.isValid():
                # Check if we should expand this item
                item = child_index.internalPointer()
                if item:
                    item_text = item.data(0) or ""

                    # Special handling for user workspace
                    if current_depth == 0 and not item_text.startswith("works_"):
                        continue  # Skip non-workspace directories at root level

                    # Expand if within depth limit or if it's a runs directory
                    if current_depth < target_depth or "runs" in item_text:
                        self._expand_to_depth_recursive(tree_view, child_index, current_depth + 1, target_depth)

    def update_memo_collection(self, memo_collection: MemoCollection):
        """Update memo collection and refresh display."""
        self.memo_collection = memo_collection
        self.root_item.set_memo_collection(memo_collection)

        # Emit data changed to update memo indicators
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(self.rowCount() - 1, 0),
            [Qt.DisplayRole, Qt.ToolTipRole]
        )

