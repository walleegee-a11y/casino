"""
Data models for memo system.
Provides type-safe representations of directory memos and metadata.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import getpass


@dataclass
class Memo:
    """Represents a memo attached to a directory."""

    text: str
    user: str = field(default_factory=getpass.getuser)
    timestamp: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None
    priority: int = 0  # 0=normal, 1=high, -1=low

    @property
    def formatted_timestamp(self) -> str:
        """Get formatted timestamp string."""
        return self.timestamp.strftime("%Y-%m-%d %H:%M")

    @property
    def is_current_user(self) -> bool:
        """Check if memo belongs to current user."""
        return self.user == getpass.getuser()

    def to_dict(self) -> Dict:
        """Convert memo to dictionary for serialization."""
        return {
            'text': self.text,
            'user': self.user,
            'timestamp': self.formatted_timestamp,
            'tags': self.tags,
            'category': self.category,
            'priority': self.priority
        }

    @classmethod
    def from_dict(cls, data) -> 'Memo':
        """Create memo from dictionary."""
        # Handle legacy format and new format
        if isinstance(data, str):
            # Legacy format: just a string
            return cls(text=data, user="unknown", timestamp=datetime.now())

        # Handle timestamp parsing
        timestamp_str = data.get('timestamp', '')
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            timestamp = datetime.now()

        return cls(
            text=data.get('text', ''),
            user=data.get('user', 'unknown'),
            timestamp=timestamp,
            tags=data.get('tags', []),
            category=data.get('category'),
            priority=data.get('priority', 0)
        )

    def update_text(self, new_text: str):
        """Update memo text and timestamp."""
        self.text = new_text
        self.timestamp = datetime.now()
        self.user = getpass.getuser()


@dataclass
class MemoCollection:
    """Collection of memos with management capabilities."""

    memos: Dict[Path, Memo] = field(default_factory=dict)

    def add_memo(self, path: Path, memo):
        """Add or update a memo for a directory."""
        if isinstance(memo, str):
            memo = Memo(text=memo)
        self.memos[path] = memo

    def get_memo(self, path: Path) -> Optional[Memo]:
        """Get memo for a directory."""
        return self.memos.get(path)

    def remove_memo(self, path: Path) -> bool:
        """Remove memo for a directory."""
        if path in self.memos:
            del self.memos[path]
            return True
        return False

    def has_memo(self, path: Path) -> bool:
        """Check if directory has a memo."""
        return path in self.memos

    def get_all_paths_with_memos(self) -> List[Path]:
        """Get all directory paths that have memos."""
        return list(self.memos.keys())

    def search_memos(self, query: str) -> List[Path]:
        """Search for directories with memos containing query."""
        results = []
        query_lower = query.lower()

        for path, memo in self.memos.items():
            if query_lower in memo.text.lower():
                results.append(path)

        return results

    def to_dict(self) -> Dict:
        """Convert collection to dictionary for serialization."""
        return {
            str(path): memo.to_dict()
            for path, memo in self.memos.items()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'MemoCollection':
        """Create collection from dictionary."""
        collection = cls()

        for path_str, memo_data in data.items():
            path = Path(path_str)
            memo = Memo.from_dict(memo_data)
            collection.memos[path] = memo

        return collection

    def cleanup_invalid_paths(self) -> int:
        """Remove memos for paths that no longer exist."""
        invalid_paths = [
            path for path in self.memos.keys()
            if not path.exists()
        ]

        for path in invalid_paths:
            del self.memos[path]

        return len(invalid_paths)
