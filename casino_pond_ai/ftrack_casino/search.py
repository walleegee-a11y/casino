"""
Advanced search and filtering for FastTrack

Supports:
- Full-text search
- Query language (field:value)
- Saved filter presets
- Quick filters
"""

import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path


class AdvancedSearch:
    """Enhanced search with query builder and presets"""

    def __init__(self, database):
        """
        Args:
            database: IssueDatabase instance
        """
        self.db = database
        self.presets_file = None

    def set_presets_file(self, file_path: str):
        """Set path for saved filter presets"""
        self.presets_file = file_path

    def parse_query(self, query: str) -> Dict[str, Any]:
        """
        Parse search query into structured format

        Supported syntax:
        - status:open
        - severity:critical OR severity:major
        - assignee:john
        - created:>2025-01-01
        - due:<today
        - text:"memory leak"
        - assignee:me (special keyword for current user)
        """
        parsed = {
            'text_search': [],
            'filters': {},
            'date_filters': {},
            'or_groups': []
        }

        # Split by OR first
        or_parts = re.split(r'\s+OR\s+', query, flags=re.IGNORECASE)

        for part in or_parts:
            part = part.strip()
            if not part:
                continue

            # Check for field:value patterns
            field_matches = re.findall(r'(\w+):((?:"[^"]*")|(?:[^\s]+))', part)

            if field_matches:
                for field, value in field_matches:
                    value = value.strip('"')

                    # Handle special date keywords
                    if value in ['today', 'yesterday', 'tomorrow']:
                        value = self._parse_date_keyword(value)

                    # Handle date comparisons
                    if field in ['created', 'due'] and value.startswith(('<', '>')):
                        operator = value[0]
                        date_value = value[1:]
                        if field not in parsed['date_filters']:
                            parsed['date_filters'][field] = []
                        parsed['date_filters'][field].append((operator, date_value))
                    else:
                        # Regular field filter
                        if field not in parsed['filters']:
                            parsed['filters'][field] = []
                        parsed['filters'][field].append(value)
            else:
                # Plain text search
                parsed['text_search'].append(part)

        return parsed

    def _parse_date_keyword(self, keyword: str) -> str:
        """Convert date keywords to ISO format"""
        today = datetime.now().date()

        if keyword == 'today':
            return today.isoformat()
        elif keyword == 'yesterday':
            return (today - timedelta(days=1)).isoformat()
        elif keyword == 'tomorrow':
            return (today + timedelta(days=1)).isoformat()
        elif keyword == 'monday':
            # Get Monday of current week
            days_since_monday = today.weekday()
            monday = today - timedelta(days=days_since_monday)
            return monday.isoformat()

        return keyword

    def search(self, query: str, current_user: str = None) -> List[Dict[str, Any]]:
        """
        Execute search query

        Args:
            query: Search query string
            current_user: Current username (for 'assignee:me')

        Returns:
            List of matching issues
        """
        if not query.strip():
            # Return all issues if no query
            return self.db.filter_issues()

        parsed = self.parse_query(query)

        # Handle special 'me' keyword
        if current_user and 'assignee' in parsed['filters']:
            parsed['filters']['assignee'] = [
                current_user if v == 'me' else v
                for v in parsed['filters']['assignee']
            ]

        # Start with full-text search if present
        if parsed['text_search']:
            text_query = ' '.join(parsed['text_search'])
            results = self.db.search_issues(text_query)
        else:
            results = self.db.filter_issues()

        # Apply field filters
        results = self._apply_filters(results, parsed)

        return results

    def _apply_filters(self, issues: List[Dict[str, Any]],
                       parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply parsed filters to issue list"""
        filtered = []

        for issue in issues:
            match = True

            # Check field filters
            for field, values in parsed['filters'].items():
                issue_value = issue.get(field, '')
                if isinstance(issue_value, list):
                    # For modules field (JSON array)
                    issue_value = ' '.join(issue_value)

                # Match any of the values (OR within field)
                if not any(str(v).lower() in str(issue_value).lower() for v in values):
                    match = False
                    break

            # Check date filters
            for field, comparisons in parsed['date_filters'].items():
                issue_date_str = issue.get(field)
                if not issue_date_str:
                    continue

                try:
                    issue_date = datetime.fromisoformat(issue_date_str.split()[0])

                    for operator, date_str in comparisons:
                        compare_date = datetime.fromisoformat(date_str)

                        if operator == '<' and issue_date >= compare_date:
                            match = False
                            break
                        elif operator == '>' and issue_date <= compare_date:
                            match = False
                            break
                except (ValueError, AttributeError):
                    pass

            if match:
                filtered.append(issue)

        return filtered

    def get_quick_filters(self, current_user: str = None) -> Dict[str, str]:
        """
        Get predefined useful filters

        Args:
            current_user: Current username

        Returns:
            Dictionary of filter name -> query string
        """
        quick_filters = {
            "All Open Issues": "status:Open",
            "All In Progress": "status:\"In Progress\"",
            "Critical Issues": "severity:Critical",
            "Overdue": f"status:Open due:<today",
            "Recently Created": f"created:>monday",
            "Resolved This Week": f"status:Resolved created:>monday",
        }

        if current_user:
            quick_filters.update({
                "My Open Issues": f"assignee:{current_user} status:Open",
                "Assigned to Me": f"assignee:{current_user}",
                "Created by Me": f"assigner:{current_user}",
            })

        return quick_filters

    def save_filter_preset(self, name: str, query: str, description: str = ""):
        """Save a filter preset for reuse"""
        if not self.presets_file:
            raise ValueError("Presets file not configured")

        presets = self.load_presets()
        presets[name] = {
            'query': query,
            'description': description,
            'created_at': datetime.now().isoformat()
        }

        with open(self.presets_file, 'w') as f:
            json.dump(presets, f, indent=2)

    def load_presets(self) -> Dict[str, Dict[str, str]]:
        """Load saved filter presets"""
        if not self.presets_file or not Path(self.presets_file).exists():
            return {}

        try:
            with open(self.presets_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def delete_preset(self, name: str):
        """Delete a saved preset"""
        if not self.presets_file:
            return

        presets = self.load_presets()
        if name in presets:
            del presets[name]
            with open(self.presets_file, 'w') as f:
                json.dump(presets, f, indent=2)

    def get_search_suggestions(self, partial_query: str) -> List[str]:
        """Get autocomplete suggestions for search queries"""
        suggestions = []

        # Field name suggestions
        fields = ['status', 'severity', 'assignee', 'assigner', 'stage', 'created', 'due']
        for field in fields:
            if partial_query.lower() in field.lower():
                suggestions.append(f"{field}:")

        # Value suggestions based on field
        if ':' in partial_query:
            field_part, value_part = partial_query.rsplit(':', 1)
            field = field_part.split()[-1].lower()

            if field == 'status':
                for status in ['Open', 'In Progress', 'Resolved', 'Closed']:
                    if value_part.lower() in status.lower():
                        suggestions.append(f"{field_part}:{status}")

            elif field == 'severity':
                for severity in ['Critical', 'Major', 'Minor', 'Enhancement', 'Info']:
                    if value_part.lower() in severity.lower():
                        suggestions.append(f"{field_part}:{severity}")

            elif field in ['created', 'due']:
                for keyword in ['today', 'yesterday', '<today', '>today', '>monday']:
                    if value_part.lower() in keyword.lower():
                        suggestions.append(f"{field_part}:{keyword}")

        return suggestions[:10]  # Limit suggestions


class FilterPresetManager:
    """Manage saved filter presets with UI integration"""

    def __init__(self, search_engine: AdvancedSearch):
        self.search = search_engine

    def create_preset_from_current(self, name: str, current_query: str):
        """Save current search as preset"""
        description = f"Saved on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        self.search.save_filter_preset(name, current_query, description)

    def get_preset_names(self) -> List[str]:
        """Get list of all preset names"""
        presets = self.search.load_presets()
        return sorted(presets.keys())

    def apply_preset(self, name: str) -> Optional[str]:
        """Get query string for a preset"""
        presets = self.search.load_presets()
        if name in presets:
            return presets[name]['query']
        return None

    def export_presets(self, file_path: str):
        """Export presets to file"""
        presets = self.search.load_presets()
        with open(file_path, 'w') as f:
            json.dump(presets, f, indent=2)

    def import_presets(self, file_path: str):
        """Import presets from file"""
        with open(file_path, 'r') as f:
            imported = json.load(f)

        existing = self.search.load_presets()
        existing.update(imported)

        with open(self.search.presets_file, 'w') as f:
            json.dump(existing, f, indent=2)
