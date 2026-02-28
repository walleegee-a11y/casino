"""
Enhanced attachment management for FastTrack

Features:
- File deduplication using SHA256 hashing
- Thumbnail generation for images
- Reference counting
- Automatic cleanup of orphaned files
"""

import os
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image


class AttachmentManager:
    """Centralized attachment handling with deduplication"""

    # Supported file types
    IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp'}
    TEXT_EXTS = {'.txt', '.py', '.c', '.cpp', '.h', '.hpp', '.log', '.rpt',
                 '.yaml', '.yml', '.json', '.md', '.cfg', '.conf', '.csh',
                 '.ini', '.xml', '.csv', '.tcl', '.sdc', '.v', '.sv'}

    def __init__(self, database, storage_dir: str):
        """
        Args:
            database: IssueDatabase instance
            storage_dir: Base directory for attachment storage
        """
        self.db = database
        self.storage_dir = Path(storage_dir)
        self.files_dir = self.storage_dir / 'files'
        self.thumbnails_dir = self.storage_dir / 'thumbnails'

        # Create directories
        self.files_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)

    def add_attachment(self, file_path: str, issue_id: str) -> Dict[str, any]:
        """
        Add attachment with deduplication

        Args:
            file_path: Source file path
            issue_id: Issue ID

        Returns:
            Dictionary with attachment info
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_hash = self.calculate_hash(file_path)

        # Check if file already exists (deduplication)
        existing_path = self.db.find_duplicate_attachment(file_hash)

        if existing_path and os.path.exists(existing_path):
            # File already exists, create reference
            stored_path = existing_path
            print(f"Deduplicated: {file_name} (existing file found)")
        else:
            # Store new file
            stored_path = self.store_file(file_path, file_hash)

        # Generate thumbnail for images
        thumbnail_path = None
        if self.is_image(file_path):
            thumbnail_path = self.generate_thumbnail(stored_path, file_hash)

        # Add to database
        self.db.add_attachment(
            issue_id=issue_id,
            file_path=str(stored_path),
            file_name=file_name,
            file_size=file_size,
            file_hash=file_hash
        )

        return {
            'path': str(stored_path),
            'name': file_name,
            'size': file_size,
            'hash': file_hash,
            'thumbnail': str(thumbnail_path) if thumbnail_path else None,
            'is_image': self.is_image(file_path),
            'is_text': self.is_text(file_path)
        }

    def calculate_hash(self, file_path: str) -> str:
        """
        Calculate SHA256 hash of file

        Args:
            file_path: Path to file

        Returns:
            Hex string of SHA256 hash
        """
        sha256 = hashlib.sha256()

        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)

        return sha256.hexdigest()

    def store_file(self, source_path: str, file_hash: str) -> Path:
        """
        Store file using hash-based naming

        Args:
            source_path: Source file path
            file_hash: SHA256 hash

        Returns:
            Path to stored file
        """
        ext = Path(source_path).suffix.lower()
        stored_path = self.files_dir / f"{file_hash}{ext}"

        # Copy file
        shutil.copy2(source_path, stored_path)

        return stored_path

    def generate_thumbnail(self, image_path: Path, file_hash: str, size: Tuple[int, int] = (200, 200)) -> Optional[Path]:
        """
        Generate thumbnail for image

        Args:
            image_path: Path to source image
            file_hash: File hash
            size: Thumbnail size (width, height)

        Returns:
            Path to thumbnail or None if failed
        """
        try:
            thumbnail_path = self.thumbnails_dir / f"{file_hash}_thumb.png"

            # Skip if thumbnail already exists
            if thumbnail_path.exists():
                return thumbnail_path

            # Open and resize image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary (for transparency)
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if 'A' in img.mode else None)
                    img = background

                # Resize maintaining aspect ratio
                img.thumbnail(size, Image.Resampling.LANCZOS)

                # Save thumbnail
                img.save(thumbnail_path, 'PNG', optimize=True)

            return thumbnail_path

        except Exception as e:
            print(f"Failed to generate thumbnail: {e}")
            return None

    def is_image(self, file_path: str) -> bool:
        """Check if file is an image"""
        ext = Path(file_path).suffix.lower()
        return ext in self.IMAGE_EXTS

    def is_text(self, file_path: str) -> bool:
        """Check if file is a text file"""
        ext = Path(file_path).suffix.lower()
        return ext in self.TEXT_EXTS

    def get_attachments(self, issue_id: str) -> List[Dict[str, any]]:
        """
        Get all attachments for an issue with metadata

        Args:
            issue_id: Issue ID

        Returns:
            List of attachment info dictionaries
        """
        attachments = self.db.get_attachments(issue_id)

        enriched = []
        for attach in attachments:
            file_path = attach['file_path']
            file_hash = attach['file_hash']

            # Check for thumbnail
            thumbnail_path = None
            if file_hash and self.is_image(file_path):
                thumb_path = self.thumbnails_dir / f"{file_hash}_thumb.png"
                if thumb_path.exists():
                    thumbnail_path = str(thumb_path)

            enriched.append({
                'id': attach['id'],
                'path': file_path,
                'name': attach['file_name'],
                'size': attach['file_size'],
                'hash': file_hash,
                'exists': os.path.exists(file_path),
                'thumbnail': thumbnail_path,
                'is_image': self.is_image(file_path),
                'is_text': self.is_text(file_path),
                'added_at': attach['added_at']
            })

        return enriched

    def remove_attachment(self, issue_id: str, attachment_id: int):
        """
        Remove attachment from issue

        Args:
            issue_id: Issue ID
            attachment_id: Attachment ID
        """
        # Get attachment info
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT file_hash FROM attachments WHERE id = ?", (attachment_id,))
        row = cursor.fetchone()

        if not row:
            return

        file_hash = row['file_hash']

        # Delete attachment record
        cursor.execute("DELETE FROM attachments WHERE id = ?", (attachment_id,))
        self.db.conn.commit()

        # Check if any other issues reference this file
        cursor.execute("SELECT COUNT(*) as count FROM attachments WHERE file_hash = ?", (file_hash,))
        ref_count = cursor.fetchone()['count']

        # If no more references, delete the actual file
        if ref_count == 0:
            self._delete_file(file_hash)

    def _delete_file(self, file_hash: str):
        """
        Delete file and thumbnail from storage

        Args:
            file_hash: File hash
        """
        # Find and delete file
        for file_path in self.files_dir.glob(f"{file_hash}.*"):
            try:
                file_path.unlink()
                print(f"Deleted orphaned file: {file_path}")
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")

        # Delete thumbnail
        thumbnail_path = self.thumbnails_dir / f"{file_hash}_thumb.png"
        if thumbnail_path.exists():
            try:
                thumbnail_path.unlink()
                print(f"Deleted thumbnail: {thumbnail_path}")
            except Exception as e:
                print(f"Failed to delete thumbnail: {e}")

    def cleanup_orphaned_files(self) -> Tuple[int, int]:
        """
        Remove files that are no longer referenced by any issue

        Returns:
            Tuple of (files_deleted, space_freed_bytes)
        """
        # Get all file hashes in database
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT DISTINCT file_hash FROM attachments WHERE file_hash IS NOT NULL")
        referenced_hashes = {row['file_hash'] for row in cursor.fetchall()}

        files_deleted = 0
        space_freed = 0

        # Check files directory
        for file_path in self.files_dir.iterdir():
            if file_path.is_file():
                # Extract hash from filename
                file_hash = file_path.stem

                if file_hash not in referenced_hashes:
                    # Orphaned file
                    size = file_path.stat().st_size
                    space_freed += size
                    file_path.unlink()
                    files_deleted += 1
                    print(f"Deleted orphaned file: {file_path.name}")

        # Check thumbnails directory
        for thumb_path in self.thumbnails_dir.iterdir():
            if thumb_path.is_file():
                # Extract hash from thumbnail filename
                file_hash = thumb_path.stem.replace('_thumb', '')

                if file_hash not in referenced_hashes:
                    size = thumb_path.stat().st_size
                    space_freed += size
                    thumb_path.unlink()
                    print(f"Deleted orphaned thumbnail: {thumb_path.name}")

        return files_deleted, space_freed

    def get_storage_stats(self) -> Dict[str, any]:
        """
        Get storage statistics

        Returns:
            Dictionary with storage stats
        """
        total_files = 0
        total_size = 0
        image_count = 0
        text_count = 0
        other_count = 0

        for file_path in self.files_dir.iterdir():
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size

                if self.is_image(str(file_path)):
                    image_count += 1
                elif self.is_text(str(file_path)):
                    text_count += 1
                else:
                    other_count += 1

        # Get unique file count (deduplication)
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT file_hash) as unique_files FROM attachments")
        unique_files = cursor.fetchone()['unique_files']

        cursor.execute("SELECT COUNT(*) as total_references FROM attachments")
        total_references = cursor.fetchone()['total_references']

        dedup_ratio = (1 - unique_files / total_references) * 100 if total_references > 0 else 0

        return {
            'total_files': total_files,
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'image_count': image_count,
            'text_count': text_count,
            'other_count': other_count,
            'unique_files': unique_files,
            'total_references': total_references,
            'deduplication_ratio': dedup_ratio
        }
