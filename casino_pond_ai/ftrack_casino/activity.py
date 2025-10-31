"""
Activity tracking and commenting system for FastTrack

Features:
- Comment threads on issues
- @mention notifications
- Activity history tracking
- Field change logging
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class Comment:
    """Represents a comment on an issue"""
    id: int
    issue_id: str
    user: str
    text: str
    timestamp: datetime
    mentions: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'issue_id': self.issue_id,
            'user': self.user,
            'text': self.text,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            'mentions': self.mentions
        }


@dataclass
class ActivityEvent:
    """Represents an activity event"""
    id: int
    issue_id: str
    activity_type: str  # 'comment', 'status_change', 'field_change', 'created', 'assigned'
    user: str
    timestamp: datetime
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    comment_text: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'issue_id': self.issue_id,
            'activity_type': self.activity_type,
            'user': self.user,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            'field_name': self.field_name,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'comment_text': self.comment_text
        }


class ActivityTracker:
    """Track all changes and activities on issues"""

    def __init__(self, database):
        """
        Args:
            database: IssueDatabase instance
        """
        self.db = database

    def add_comment(self, issue_id: str, user: str, text: str) -> Comment:
        """
        Add a comment to an issue

        Args:
            issue_id: Issue ID
            user: Username
            text: Comment text

        Returns:
            Comment object
        """
        # Extract @mentions from comment text
        mentions = self._extract_mentions(text)

        # Log activity
        self.db.log_activity(
            issue_id=issue_id,
            activity_type='comment',
            user=user,
            comment_text=text,
            mentions=mentions
        )

        # Get the comment we just added
        activities = self.db.get_activity(issue_id, limit=1)
        if activities:
            activity = activities[0]
            return Comment(
                id=activity['id'],
                issue_id=issue_id,
                user=user,
                text=text,
                timestamp=datetime.fromisoformat(activity['timestamp']),
                mentions=mentions
            )

        return None

    def _extract_mentions(self, text: str) -> List[str]:
        """Extract @mentions from text"""
        # Find all @username patterns
        mentions = re.findall(r'@(\w+)', text)
        return list(set(mentions))  # Remove duplicates

    def track_field_change(self, issue_id: str, user: str, field_name: str,
                          old_value: Any, new_value: Any):
        """
        Track a field change on an issue

        Args:
            issue_id: Issue ID
            user: Username who made the change
            field_name: Name of field that changed
            old_value: Previous value
            new_value: New value
        """
        # Convert values to strings for storage
        old_str = str(old_value) if old_value is not None else ""
        new_str = str(new_value) if new_value is not None else ""

        # Don't log if nothing changed
        if old_str == new_str:
            return

        # Determine activity type based on field
        activity_type = 'field_change'
        if field_name == 'status':
            activity_type = 'status_change'
        elif field_name == 'assignee':
            activity_type = 'assigned'

        self.db.log_activity(
            issue_id=issue_id,
            activity_type=activity_type,
            user=user,
            field_name=field_name,
            old_value=old_str,
            new_value=new_str
        )

    def track_issue_created(self, issue_id: str, user: str):
        """Track issue creation"""
        self.db.log_activity(
            issue_id=issue_id,
            activity_type='created',
            user=user
        )

    def get_activity_timeline(self, issue_id: str, limit: int = 50) -> List[ActivityEvent]:
        """
        Get activity timeline for an issue

        Args:
            issue_id: Issue ID
            limit: Maximum number of activities to return

        Returns:
            List of ActivityEvent objects
        """
        activities = self.db.get_activity(issue_id, limit)

        events = []
        for activity in activities:
            events.append(ActivityEvent(
                id=activity['id'],
                issue_id=activity['issue_id'],
                activity_type=activity['activity_type'],
                user=activity['user'],
                timestamp=datetime.fromisoformat(activity['timestamp']),
                field_name=activity.get('field_name'),
                old_value=activity.get('old_value'),
                new_value=activity.get('new_value'),
                comment_text=activity.get('comment_text')
            ))

        return events

    def get_comments(self, issue_id: str) -> List[Comment]:
        """Get all comments for an issue"""
        activities = self.db.get_activity(issue_id)

        comments = []
        for activity in activities:
            if activity['activity_type'] == 'comment':
                comments.append(Comment(
                    id=activity['id'],
                    issue_id=activity['issue_id'],
                    user=activity['user'],
                    text=activity['comment_text'],
                    timestamp=datetime.fromisoformat(activity['timestamp']),
                    mentions=activity.get('mentions', [])
                ))

        return comments

    def format_activity_for_display(self, event: ActivityEvent) -> str:
        """
        Format an activity event for display in UI

        Args:
            event: ActivityEvent object

        Returns:
            Formatted string
        """
        timestamp_str = event.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        user_str = event.user

        if event.activity_type == 'created':
            return f"[{timestamp_str}] {user_str} created this issue"

        elif event.activity_type == 'comment':
            return f"[{timestamp_str}] {user_str} commented:\n  {event.comment_text}"

        elif event.activity_type == 'status_change':
            return f"[{timestamp_str}] {user_str} changed status from '{event.old_value}' to '{event.new_value}'"

        elif event.activity_type == 'assigned':
            if event.old_value:
                return f"[{timestamp_str}] {user_str} reassigned from '{event.old_value}' to '{event.new_value}'"
            else:
                return f"[{timestamp_str}] {user_str} assigned to '{event.new_value}'"

        elif event.activity_type == 'field_change':
            field_display = event.field_name.replace('_', ' ').title()
            return f"[{timestamp_str}] {user_str} changed {field_display} from '{event.old_value}' to '{event.new_value}'"

        return f"[{timestamp_str}] {user_str} - {event.activity_type}"

    def get_user_mentions(self, username: str) -> List[Dict[str, Any]]:
        """
        Get all issues where user was mentioned

        Args:
            username: Username to search for

        Returns:
            List of issues with mention details
        """
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT
                issues.id,
                issues.title,
                activity_log.comment_text,
                activity_log.user as mentioned_by,
                activity_log.timestamp
            FROM issues
            JOIN activity_log ON issues.id = activity_log.issue_id
            WHERE activity_log.activity_type = 'comment'
              AND activity_log.mentions LIKE ?
            ORDER BY activity_log.timestamp DESC
        """, (f'%{username}%',))

        return [dict(row) for row in cursor.fetchall()]


class NotificationSystem:
    """Handle notifications for activity events"""

    def __init__(self, activity_tracker: ActivityTracker):
        self.tracker = activity_tracker
        self.notifications = []  # In-memory for now

    def notify_mention(self, username: str, issue_id: str, comment_text: str, mentioned_by: str):
        """
        Create notification for @mention

        Args:
            username: User being mentioned
            issue_id: Issue ID
            comment_text: Comment text
            mentioned_by: User who mentioned
        """
        notification = {
            'type': 'mention',
            'username': username,
            'issue_id': issue_id,
            'text': comment_text,
            'mentioned_by': mentioned_by,
            'timestamp': datetime.now(),
            'read': False
        }
        self.notifications.append(notification)

    def notify_assignment(self, username: str, issue_id: str, assigned_by: str):
        """
        Create notification for issue assignment

        Args:
            username: Assignee
            issue_id: Issue ID
            assigned_by: User who assigned
        """
        notification = {
            'type': 'assignment',
            'username': username,
            'issue_id': issue_id,
            'assigned_by': assigned_by,
            'timestamp': datetime.now(),
            'read': False
        }
        self.notifications.append(notification)

    def notify_status_change(self, username: str, issue_id: str, new_status: str, changed_by: str):
        """
        Create notification for status change on assigned issue

        Args:
            username: Assignee
            issue_id: Issue ID
            new_status: New status
            changed_by: User who changed status
        """
        notification = {
            'type': 'status_change',
            'username': username,
            'issue_id': issue_id,
            'new_status': new_status,
            'changed_by': changed_by,
            'timestamp': datetime.now(),
            'read': False
        }
        self.notifications.append(notification)

    def get_notifications(self, username: str, unread_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get notifications for a user

        Args:
            username: Username
            unread_only: If True, only return unread notifications

        Returns:
            List of notifications
        """
        user_notifications = [n for n in self.notifications if n['username'] == username]

        if unread_only:
            user_notifications = [n for n in user_notifications if not n['read']]

        return sorted(user_notifications, key=lambda x: x['timestamp'], reverse=True)

    def mark_as_read(self, notification_index: int):
        """Mark a notification as read"""
        if 0 <= notification_index < len(self.notifications):
            self.notifications[notification_index]['read'] = True

    def get_unread_count(self, username: str) -> int:
        """Get count of unread notifications"""
        return len(self.get_notifications(username, unread_only=True))
