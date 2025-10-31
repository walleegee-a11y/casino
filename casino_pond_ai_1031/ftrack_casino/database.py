"""
SQLite database layer for FastTrack issue management

Provides fast querying, indexing, and search capabilities while keeping
YAML files as the primary data format for human readability.
"""

import sqlite3
import json
import yaml
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class IssueDatabase:
    """SQLite backend for faster querying and indexing"""

    def __init__(self, db_path: str):
        """Initialize database connection and create schema"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self.create_schema()

    def create_schema(self):
        """Create database tables and indexes"""
        cursor = self.conn.cursor()

        # Main issues table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS issues (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL,
                severity TEXT NOT NULL,
                stage TEXT,
                assignee TEXT,
                assigner TEXT,
                created_at TIMESTAMP NOT NULL,
                due_date TIMESTAMP,
                run_id TEXT,
                modules TEXT,  -- JSON array
                yaml_path TEXT NOT NULL,
                updated_at TIMESTAMP
            )
        """)

        # Attachments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_hash TEXT,
                file_size INTEGER,
                mime_type TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE
            )
        """)

        # Activity log table for tracking changes and comments
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_id TEXT NOT NULL,
                activity_type TEXT NOT NULL,  -- 'comment', 'status_change', 'field_change', 'created'
                user TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                field_name TEXT,  -- For field changes
                old_value TEXT,
                new_value TEXT,
                comment_text TEXT,  -- For comments
                mentions TEXT,  -- JSON array of @mentioned users
                FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE
            )
        """)

        # Create indexes for better query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON issues(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assignee ON issues(assignee)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_severity ON issues(severity)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stage ON issues(stage)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON issues(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_due_date ON issues(due_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_issue_activity ON activity_log(issue_id, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attachment_hash ON attachments(file_hash)")

        # Full-text search virtual table
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS issues_fts USING fts5(
                issue_id UNINDEXED,
                title,
                description,
                modules,
                content=issues,
                content_rowid=rowid
            )
        """)

        self.conn.commit()

    def sync_from_yaml(self, yaml_dir: str, force: bool = False):
        """Sync database from YAML files"""
        cursor = self.conn.cursor()

        # Get all YAML files
        yaml_files = []
        for fn in os.listdir(yaml_dir):
            if fn.endswith(('.yaml', '.yml')) and not fn.startswith('deleted_'):
                yaml_files.append(os.path.join(yaml_dir, fn))

        # Track existing issues in DB
        cursor.execute("SELECT id, yaml_path, updated_at FROM issues")
        existing_issues = {row['id']: (row['yaml_path'], row['updated_at']) for row in cursor.fetchall()}

        synced_count = 0
        for yaml_path in yaml_files:
            try:
                with open(yaml_path, 'r') as f:
                    data = yaml.safe_load(f)

                if not data or 'id' not in data:
                    continue

                issue_id = data['id']

                # Check if we need to update
                file_mtime = os.path.getmtime(yaml_path)
                file_mtime_dt = datetime.fromtimestamp(file_mtime)

                if issue_id in existing_issues and not force:
                    db_path, db_updated = existing_issues[issue_id]
                    if db_updated and file_mtime_dt <= datetime.fromisoformat(db_updated):
                        continue  # Skip, DB is up to date

                # Insert or update
                self.upsert_issue(data, yaml_path, file_mtime_dt)
                synced_count += 1

            except Exception as e:
                print(f"Error syncing {yaml_path}: {e}")

        # Remove issues that no longer have YAML files
        yaml_ids = {os.path.basename(f).replace('.yaml', '').replace('.yml', '').split('_')[0]
                    for f in yaml_files}
        for issue_id in existing_issues:
            if issue_id not in yaml_ids:
                cursor.execute("DELETE FROM issues WHERE id = ?", (issue_id,))

        self.conn.commit()
        return synced_count

    def upsert_issue(self, data: Dict[str, Any], yaml_path: str, updated_at: datetime = None):
        """Insert or update an issue"""
        cursor = self.conn.cursor()

        if updated_at is None:
            updated_at = datetime.now()

        # Convert modules list to JSON
        modules_json = json.dumps(data.get('modules', []))

        cursor.execute("""
            INSERT OR REPLACE INTO issues (
                id, title, description, status, severity, stage,
                assignee, assigner, created_at, due_date, run_id,
                modules, yaml_path, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['id'],
            data.get('title', ''),
            data.get('description', ''),
            data.get('status', 'Open'),
            data.get('severity', 'Minor'),
            data.get('stage', ''),
            data.get('assignee', ''),
            data.get('assigner', ''),
            data.get('created_at', datetime.now().isoformat()),
            data.get('due_date'),
            data.get('run_id', ''),
            modules_json,
            yaml_path,
            updated_at.isoformat()
        ))

        # Update FTS index
        cursor.execute("""
            INSERT OR REPLACE INTO issues_fts (rowid, issue_id, title, description, modules)
            SELECT rowid, id, title, description, modules FROM issues WHERE id = ?
        """, (data['id'],))

        # Sync attachments
        if 'attachments' in data:
            cursor.execute("DELETE FROM attachments WHERE issue_id = ?", (data['id'],))
            for attach_path in data['attachments']:
                if os.path.exists(attach_path):
                    self.add_attachment(
                        data['id'],
                        attach_path,
                        os.path.basename(attach_path),
                        os.path.getsize(attach_path)
                    )

        self.conn.commit()

    def search_issues(self, query: str) -> List[Dict[str, Any]]:
        """Full-text search across title, description, and modules"""
        cursor = self.conn.cursor()

        # FTS5 full-text search
        cursor.execute("""
            SELECT issues.* FROM issues
            JOIN issues_fts ON issues.id = issues_fts.issue_id
            WHERE issues_fts MATCH ?
            ORDER BY rank
        """, (query,))

        return [dict(row) for row in cursor.fetchall()]

    def filter_issues(self,
                      status: Optional[str] = None,
                      severity: Optional[str] = None,
                      assignee: Optional[str] = None,
                      stage: Optional[str] = None,
                      created_after: Optional[str] = None,
                      due_before: Optional[str] = None) -> List[Dict[str, Any]]:
        """Filter issues by multiple criteria"""
        cursor = self.conn.cursor()

        conditions = []
        params = []

        if status:
            conditions.append("status = ?")
            params.append(status)

        if severity:
            conditions.append("severity = ?")
            params.append(severity)

        if assignee:
            conditions.append("assignee = ?")
            params.append(assignee)

        if stage:
            conditions.append("stage = ?")
            params.append(stage)

        if created_after:
            conditions.append("created_at >= ?")
            params.append(created_after)

        if due_before:
            conditions.append("due_date <= ?")
            params.append(due_before)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        cursor.execute(f"""
            SELECT * FROM issues
            WHERE {where_clause}
            ORDER BY created_at DESC
        """, params)

        return [dict(row) for row in cursor.fetchall()]

    def get_issue(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """Get single issue by ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM issues WHERE id = ?", (issue_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_status_summary(self) -> Dict[str, int]:
        """Get count of issues by status"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM issues
            GROUP BY status
        """)

        return {row['status']: row['count'] for row in cursor.fetchall()}

    def get_assignee_workload(self) -> List[Dict[str, Any]]:
        """Get issue counts per assignee"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                assignee,
                COUNT(*) as total,
                SUM(CASE WHEN status IN ('Open', 'In Progress') THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN severity = 'Critical' THEN 1 ELSE 0 END) as critical
            FROM issues
            WHERE assignee != ''
            GROUP BY assignee
            ORDER BY active DESC, critical DESC
        """)

        return [dict(row) for row in cursor.fetchall()]

    def add_attachment(self, issue_id: str, file_path: str, file_name: str,
                       file_size: int, file_hash: str = None):
        """Add attachment record"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO attachments (issue_id, file_path, file_name, file_size, file_hash)
            VALUES (?, ?, ?, ?, ?)
        """, (issue_id, file_path, file_name, file_size, file_hash))
        self.conn.commit()

    def get_attachments(self, issue_id: str) -> List[Dict[str, Any]]:
        """Get all attachments for an issue"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM attachments WHERE issue_id = ? ORDER BY added_at
        """, (issue_id,))
        return [dict(row) for row in cursor.fetchall()]

    def find_duplicate_attachment(self, file_hash: str) -> Optional[str]:
        """Find existing attachment with same hash (for deduplication)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT file_path FROM attachments WHERE file_hash = ? LIMIT 1
        """, (file_hash,))
        row = cursor.fetchone()
        return row['file_path'] if row else None

    def log_activity(self, issue_id: str, activity_type: str, user: str,
                     field_name: str = None, old_value: str = None,
                     new_value: str = None, comment_text: str = None,
                     mentions: List[str] = None):
        """Log an activity event"""
        cursor = self.conn.cursor()
        mentions_json = json.dumps(mentions) if mentions else None

        cursor.execute("""
            INSERT INTO activity_log (
                issue_id, activity_type, user, field_name,
                old_value, new_value, comment_text, mentions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (issue_id, activity_type, user, field_name,
              old_value, new_value, comment_text, mentions_json))
        self.conn.commit()

    def get_activity(self, issue_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get activity log for an issue"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM activity_log
            WHERE issue_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (issue_id, limit))

        activities = []
        for row in cursor.fetchall():
            activity = dict(row)
            if activity['mentions']:
                activity['mentions'] = json.loads(activity['mentions'])
            activities.append(activity)

        return activities

    def get_overdue_issues(self) -> List[Dict[str, Any]]:
        """Get all overdue issues"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM issues
            WHERE due_date < datetime('now')
              AND status NOT IN ('Resolved', 'Closed')
            ORDER BY due_date
        """)
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        """Close database connection"""
        self.conn.close()
