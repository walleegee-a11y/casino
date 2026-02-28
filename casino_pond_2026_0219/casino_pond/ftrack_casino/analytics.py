"""
Dashboard analytics and visualizations for FastTrack

Provides metrics, trends, and insights on issue data
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import Counter


class IssueDashboard:
    """Analytics and visualizations"""

    def __init__(self, database):
        self.db = database

    def get_status_summary(self) -> Dict[str, int]:
        """Get issue counts by status"""
        return self.db.get_status_summary()

    def get_severity_breakdown(self) -> Dict[str, int]:
        """Get issue counts by severity"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT severity, COUNT(*) as count
            FROM issues
            GROUP BY severity
            ORDER BY
                CASE severity
                    WHEN 'Critical' THEN 1
                    WHEN 'Major' THEN 2
                    WHEN 'Minor' THEN 3
                    WHEN 'Enhancement' THEN 4
                    WHEN 'Info' THEN 5
                END
        """)
        return {row['severity']: row['count'] for row in cursor.fetchall()}

    def get_team_workload(self) -> List[Dict[str, any]]:
        """Get current workload per assignee"""
        return self.db.get_assignee_workload()

    def get_status_trend(self, days: int = 30) -> Dict[str, List[Tuple[str, int]]]:
        """
        Get issue status trend over time

        Returns dict with status names as keys and list of (date, count) tuples
        """
        cursor = self.db.conn.cursor()

        # Generate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        # Get daily counts
        cursor.execute("""
            SELECT
                DATE(created_at) as date,
                status,
                COUNT(*) as count
            FROM issues
            WHERE DATE(created_at) >= ?
            GROUP BY DATE(created_at), status
            ORDER BY date
        """, (start_date.isoformat(),))

        # Organize by status
        trends = {}
        for row in cursor.fetchall():
            status = row['status']
            if status not in trends:
                trends[status] = []
            trends[status].append((row['date'], row['count']))

        return trends

    def get_resolution_metrics(self) -> Dict[str, any]:
        """Get resolution time metrics"""
        cursor = self.db.conn.cursor()

        # Average resolution time by severity
        cursor.execute("""
            SELECT
                severity,
                AVG(julianday(updated_at) - julianday(created_at)) as avg_days,
                COUNT(*) as count
            FROM issues
            WHERE status IN ('Resolved', 'Closed')
            GROUP BY severity
        """)

        by_severity = {}
        for row in cursor.fetchall():
            by_severity[row['severity']] = {
                'avg_days': round(row['avg_days'], 1),
                'count': row['count']
            }

        # Overall stats
        cursor.execute("""
            SELECT
                AVG(julianday(updated_at) - julianday(created_at)) as avg_days,
                MIN(julianday(updated_at) - julianday(created_at)) as min_days,
                MAX(julianday(updated_at) - julianday(created_at)) as max_days
            FROM issues
            WHERE status IN ('Resolved', 'Closed')
        """)

        overall = cursor.fetchone()

        return {
            'by_severity': by_severity,
            'overall': {
                'avg_days': round(overall['avg_days'], 1) if overall['avg_days'] else 0,
                'min_days': round(overall['min_days'], 1) if overall['min_days'] else 0,
                'max_days': round(overall['max_days'], 1) if overall['max_days'] else 0
            }
        }

    def get_overdue_summary(self) -> Dict[str, any]:
        """Get summary of overdue issues"""
        overdue = self.db.get_overdue_issues()

        # Group by severity
        by_severity = Counter(issue['severity'] for issue in overdue)

        # Group by assignee
        by_assignee = Counter(issue['assignee'] for issue in overdue if issue['assignee'])

        return {
            'total': len(overdue),
            'by_severity': dict(by_severity),
            'by_assignee': dict(by_assignee.most_common(10))
        }

    def get_creation_trend(self, days: int = 30) -> List[Tuple[str, int]]:
        """Get daily issue creation count"""
        cursor = self.db.conn.cursor()

        start_date = (datetime.now().date() - timedelta(days=days)).isoformat()

        cursor.execute("""
            SELECT
                DATE(created_at) as date,
                COUNT(*) as count
            FROM issues
            WHERE DATE(created_at) >= ?
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (start_date,))

        return [(row['date'], row['count']) for row in cursor.fetchall()]

    def get_stage_distribution(self) -> Dict[str, int]:
        """Get issue distribution by stage"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT stage, COUNT(*) as count
            FROM issues
            WHERE stage != ''
            GROUP BY stage
            ORDER BY count DESC
        """)
        return {row['stage']: row['count'] for row in cursor.fetchall()}

    def get_module_distribution(self) -> Dict[str, int]:
        """Get issue distribution by module"""
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT modules FROM issues")

        module_counts = Counter()
        for row in cursor.fetchall():
            import json
            modules = json.loads(row['modules'])
            module_counts.update(modules)

        return dict(module_counts.most_common(20))

    def get_activity_heatmap(self, days: int = 30) -> Dict[str, int]:
        """Get activity by day of week"""
        cursor = self.db.conn.cursor()

        start_date = (datetime.now().date() - timedelta(days=days)).isoformat()

        cursor.execute("""
            SELECT
                CAST(strftime('%w', created_at) AS INTEGER) as dow,
                COUNT(*) as count
            FROM issues
            WHERE DATE(created_at) >= ?
            GROUP BY dow
        """, (start_date,))

        days_of_week = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        heatmap = {day: 0 for day in days_of_week}

        for row in cursor.fetchall():
            heatmap[days_of_week[row['dow']]] = row['count']

        return heatmap
