#!/usr/local/bin/python3.12
"""
Hawkeye Archive System for CASINO Project Analysis
Stores and manages analyzed data with run version-based organization
"""

import os
import json
import yaml
import datetime
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import hashlib

# Try to import sqlite3, fall back to JSON-only mode if not available
try:
    import sqlite3
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False
    print("Warning: SQLite not available. Archive will use JSON-only mode.")


class HawkeyeArchive:
    """Archive system for storing Hawkeye analysis results"""


    def __init__(self, archive_base_path: str = None):
        """Initialize the archive system

        Args:
            archive_base_path: Base path for archive storage. If None, uses environment variable
        """
        if archive_base_path:
            self.archive_base = archive_base_path
        else:
            # Priority order for archive location
            casino_prj_base = os.getenv('casino_prj_base')
            casino_prj_name = os.getenv('casino_prj_name')

            if casino_prj_base and casino_prj_name:
                # Standard: $casino_prj_base/$casino_prj_name/hawkeye_archive
                self.archive_base = os.path.join(casino_prj_base, casino_prj_name, 'hawkeye_archive')
            elif os.getenv('HAWKEYE_ARCHIVE_BASE'):
                # Explicit override
                self.archive_base = os.getenv('HAWKEYE_ARCHIVE_BASE')
            else:
                # Fallback to current directory
                self.archive_base = './hawkeye_archive'

        print(f"Archive initialized with path: {self.archive_base}")
        print(f"Archive absolute path: {os.path.abspath(self.archive_base)}")

        self.db_path = os.path.join(self.archive_base, 'hawkeye_archive.db')
        self.metadata_json_path = os.path.join(self.archive_base, 'metadata.json')

        # Track if we're using SQLite or JSON-only mode
        self.use_sqlite = SQLITE_AVAILABLE

        # Create archive directory structure
        self._setup_archive_structure()

        # Initialize database or JSON metadata
        if self.use_sqlite:
            self._init_database()
        else:
            self._init_json_metadata()

        # Auto-repair: Check if metadata is missing but data files exist
        self._auto_repair_metadata()


    def _setup_archive_structure(self):
        """Create the archive directory structure"""
        # Ensure archive_base is absolute path for better reliability
        self.archive_base = os.path.abspath(self.archive_base)

        directories = [
            self.archive_base,
            os.path.join(self.archive_base, 'data'),
            os.path.join(self.archive_base, 'metadata'),
            os.path.join(self.archive_base, 'exports'),
            os.path.join(self.archive_base, 'web_cache')
        ]

        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
            except PermissionError:
                print(f"Warning: Permission denied creating directory: {directory}")
            except Exception as e:
                print(f"Error creating directory {directory}: {e}")

        print(f"Archive structure initialized at: {self.archive_base}")
        print(f"Archive resolved to: {os.path.abspath(self.archive_base)}")

    def _init_database(self):
        """Initialize SQLite database for metadata"""
        print(f"Initializing database at: {self.db_path}")
        print(f"Database file exists: {os.path.exists(self.db_path)}")
        print(f"Database directory exists: {os.path.exists(os.path.dirname(self.db_path))}")
        print(f"Database directory writable: {os.access(os.path.dirname(self.db_path), os.W_OK)}")

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Archive entries table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS archive_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        run_version TEXT NOT NULL,
                        base_dir TEXT NOT NULL,
                        top_name TEXT NOT NULL,
                        user_name TEXT NOT NULL,
                        block_name TEXT NOT NULL,
                        dk_ver_tag TEXT NOT NULL,
                        full_path TEXT NOT NULL,
                        archive_timestamp DATETIME NOT NULL,
                        data_hash TEXT NOT NULL,
                        file_size INTEGER,
                        task_count INTEGER,
                        keyword_count INTEGER,
                        completion_rate REAL,
                        status TEXT DEFAULT 'active',
                        notes TEXT,
                        UNIQUE(run_version, base_dir, top_name, user_name, block_name, dk_ver_tag)
                    )
                ''')

                # Task results table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS task_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        archive_entry_id INTEGER,
                        task_name TEXT NOT NULL,
                        job_name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        execution_time DATETIME,
                        log_files TEXT,
                        report_files TEXT,
                        FOREIGN KEY (archive_entry_id) REFERENCES archive_entries (id)
                    )
                ''')

                # Keyword results table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS keyword_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_result_id INTEGER,
                        keyword_name TEXT NOT NULL,
                        keyword_value TEXT,
                        keyword_unit TEXT,
                        keyword_type TEXT,
                        source_file TEXT,
                        FOREIGN KEY (task_result_id) REFERENCES task_results (id)
                    )
                ''')

                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_run_version ON archive_entries (run_version)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_archive_timestamp ON archive_entries (archive_timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_name ON task_results (task_name)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_keyword_name ON keyword_results (keyword_name)')

                conn.commit()

            print(f"Database initialized successfully at: {self.db_path}")

            # Test database connection and basic operations
            try:
                with sqlite3.connect(self.db_path) as test_conn:
                    test_cursor = test_conn.cursor()
                    test_cursor.execute("SELECT COUNT(*) FROM archive_entries")
                    entry_count = test_cursor.fetchone()[0]
                    print(f"Database test successful. Current archive entries: {entry_count}")
            except Exception as test_error:
                print(f"Database test failed: {test_error}")

        except sqlite3.Error as db_error:
            print(f"SQLite error during database initialization: {db_error}")
            print(f"SQLite version: {sqlite3.sqlite_version}")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Archive base permissions: {oct(os.stat(self.archive_base).st_mode) if os.path.exists(self.archive_base) else 'Directory does not exist'}")
            raise
        except Exception as e:
            print(f"General error during database initialization: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            print(f"Traceback:\n{traceback.format_exc()}")
            raise


    def _init_json_metadata(self):
        """Initialize JSON metadata file for fallback mode when SQLite is not available"""
        if not os.path.exists(self.metadata_json_path):
            metadata = {
                "created": datetime.datetime.now().isoformat(),
                "archive_entries": [],
                "task_results": [],
                "keyword_results": []
            }
            with open(self.metadata_json_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"JSON metadata initialized at: {self.metadata_json_path}")
        else:
            print(f"JSON metadata exists at: {self.metadata_json_path}")

    def archive_analysis_data(self, analyzer_instance, run_filter: str = None) -> Dict[str, Any]:
        """Archive analysis data from HawkeyeAnalyzer instance

        Args:
            analyzer_instance: Instance of HawkeyeAnalyzer with analysis_results
            run_filter: Optional filter for specific run version

        Returns:
            Dictionary with archive results and statistics
        """
        if not hasattr(analyzer_instance, 'analysis_results'):
            raise ValueError("Analyzer instance must have analysis_results")

        results = {
            'archived_entries': 0,
            'skipped_entries': 0,
            'errors': [],
            'archived_runs': []
        }

        analysis_data = analyzer_instance.analysis_results

        if not analysis_data:
            print("No analysis data found to archive")
            return results

        for run_path, run_data in analysis_data.items():
            try:
                # Parse run path components
                path_parts = Path(run_path).parts

                # Improved path parsing using hierarchy pattern
                if len(path_parts) < 1:
                    results['errors'].append(f"Path too short: {run_path} (need at least 1 component)")
                    continue

                # Parse according to your pattern:
                # end = Run Version, end-1 = runs (skip), end-2 = DK Ver/Tag, end-3 = Block, end-4 = User (remove "works_")
                run_version = path_parts[-1]  # Always the last component

                if len(path_parts) >= 5:
                    # Full hierarchy available (accounting for 'runs' directory)
                    # Skip 'runs' directory if present
                    if path_parts[-2] == 'runs':
                        dk_ver_tag = path_parts[-3]   # pd___rtl_3.0_dk_3.1_tag_2.0
                        block_name = path_parts[-4]   # clk_gen or row_drv
                        user_part = path_parts[-5]    # works_scott.lee
                    else:
                        # No 'runs' directory
                        dk_ver_tag = path_parts[-2]   # pd___rtl_3.0_dk_3.1_tag_2.0
                        block_name = path_parts[-3]   # clk_gen or row_drv
                        user_part = path_parts[-4]    # works_scott.lee

                    user_name = user_part.replace('works_', '') if user_part.startswith('works_') else user_part

                    # Extract additional info if path is longer
                    base_dir = path_parts[0] if len(path_parts) > 5 else 'unknown'
                    top_name = path_parts[1] if len(path_parts) > 6 else 'unknown'

                    run_info = {
                        'base_dir': base_dir,
                        'top_name': top_name,
                        'user_name': user_name,
                        'block_name': block_name,
                        'dk_ver_tag': dk_ver_tag,
                        'run_version': run_version,
                        'full_path': run_path
                    }

                    print(f"Parsed path hierarchy for {run_version}: User={user_name}, Block={block_name}, DK={dk_ver_tag}")
                elif len(path_parts) >= 4:
                    # Partial hierarchy - extract what we can (accounting for possible 'runs' dir)
                    if path_parts[-2] == 'runs' and len(path_parts) >= 4:
                        dk_ver_tag = path_parts[-3] if len(path_parts) >= 3 else 'unknown'
                        block_name = path_parts[-4] if len(path_parts) >= 4 else 'unknown'
                        user_name = 'unknown'
                    else:
                        dk_ver_tag = path_parts[-2] if len(path_parts) >= 2 else 'unknown'
                        block_name = path_parts[-3] if len(path_parts) >= 3 else 'unknown'
                        user_name = 'unknown'
                else:
                    # Very short path
                    dk_ver_tag = 'unknown'
                    block_name = 'unknown'
                    user_name = 'unknown'

                    run_info = {
                        'base_dir': 'unknown',
                        'top_name': 'unknown',
                        'user_name': user_name,
                        'block_name': block_name,
                        'dk_ver_tag': dk_ver_tag,
                        'run_version': run_version,
                        'full_path': run_path
                    }

                    print(f"Warning: Partial path parsing for {run_path} ({len(path_parts)} components)")

                # Apply run filter if specified
                if run_filter and run_filter not in run_info['run_version']:
                    results['skipped_entries'] += 1
                    continue

                # Archive the run data (overwriting is now enabled)
                print(f"Attempting to archive: {run_info['run_version']} from {run_path}")
                success = self._archive_run_data(run_info, run_data)
                if success:
                    results['archived_entries'] += 1
                    results['archived_runs'].append(run_info['run_version'])
                    print(f"- Archived: {run_info['run_version']}")
                else:
                    error_msg = f"Failed to archive: {run_info['run_version']}"
                    results['errors'].append(error_msg)
                    print(f"- {error_msg}")

            except Exception as e:
                results['errors'].append(f"Error processing {run_path}: {str(e)}")

        return results

    def _is_already_archived(self, run_info: Dict[str, str]) -> bool:
        """Check if run is already archived - DISABLED to allow overwriting"""
        # Always return False to allow re-archiving/overwriting
        return False

    def _archive_run_data(self, run_info: Dict[str, str], run_data: Dict[str, Any]) -> bool:
        """Archive a single run's data"""
        try:
            # Calculate data hash for integrity
            data_json = json.dumps(run_data, sort_keys=True)
            data_hash = hashlib.sha256(data_json.encode()).hexdigest()

            # Save JSON data file
            data_filename = f"{run_info['run_version']}_{data_hash[:8]}.json"
            data_filepath = os.path.join(self.archive_base, 'data', data_filename)

            with open(data_filepath, 'w') as f:
                json.dump(run_data, f, indent=2, default=str)

            file_size = os.path.getsize(data_filepath)

            # Extract summary statistics
            summary = run_data.get('summary', {})
            task_count = summary.get('total_tasks', 0)
            completion_rate = summary.get('completion_rate', 0.0)

            # Count keywords
            keyword_count = 0
            for task_data in run_data.get('tasks', {}).values():
                keyword_count += len(task_data.get('keywords', {}))

            # Insert into database or JSON metadata
            if self.use_sqlite:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    # Check if entry already exists
                    cursor.execute('''
                        SELECT id, data_hash FROM archive_entries
                        WHERE run_version = ? AND base_dir = ? AND top_name = ?
                        AND user_name = ? AND block_name = ? AND dk_ver_tag = ?
                    ''', (
                        run_info['run_version'], run_info['base_dir'], run_info['top_name'],
                        run_info['user_name'], run_info['block_name'], run_info['dk_ver_tag']
                    ))
                    existing_entry = cursor.fetchone()

                    if existing_entry:
                        # Update existing entry and clean up old data file
                        archive_entry_id = existing_entry[0]
                        old_data_hash = existing_entry[1]

                        print(f"DEBUG: Updating existing entry ID {archive_entry_id}")
                        print(f"DEBUG: Old hash: {old_data_hash[:8]}, New hash: {data_hash[:8]}")

                        # Remove old data file if hash is different
                        if old_data_hash != data_hash:
                            old_data_filename = f"{run_info['run_version']}_{old_data_hash[:8]}.json"
                            old_data_filepath = os.path.join(self.archive_base, 'data', old_data_filename)
                            if os.path.exists(old_data_filepath):
                                try:
                                    os.remove(old_data_filepath)
                                    print(f"DEBUG: Removed old data file: {old_data_filename}")
                                except Exception as e:
                                    print(f"DEBUG: Failed to remove old data file: {e}")

                        cursor.execute('''
                            UPDATE archive_entries SET
                                full_path = ?, archive_timestamp = ?, data_hash = ?,
                                file_size = ?, task_count = ?, keyword_count = ?, completion_rate = ?, status = 'active'
                            WHERE id = ?
                        ''', (
                            run_info['full_path'], datetime.datetime.now(), data_hash,
                            file_size, task_count, keyword_count, completion_rate, archive_entry_id
                        ))

                        # Delete existing task and keyword results for this entry
                        cursor.execute('DELETE FROM keyword_results WHERE task_result_id IN (SELECT id FROM task_results WHERE archive_entry_id = ?)', (archive_entry_id,))
                        cursor.execute('DELETE FROM task_results WHERE archive_entry_id = ?', (archive_entry_id,))

                        print(f"DEBUG: Updated existing entry and cleared old task/keyword data")







                        # Delete existing task and keyword results for this entry
                        cursor.execute('DELETE FROM keyword_results WHERE task_result_id IN (SELECT id FROM task_results WHERE archive_entry_id = ?)', (archive_entry_id,))
                        cursor.execute('DELETE FROM task_results WHERE archive_entry_id = ?', (archive_entry_id,))
                    else:
                        # Insert new entry

                        cursor.execute('''
                            INSERT INTO archive_entries (
                                run_version, base_dir, top_name, user_name, block_name, dk_ver_tag,
                                full_path, archive_timestamp, data_hash, file_size, task_count,
                                keyword_count, completion_rate
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            run_info['run_version'], run_info['base_dir'], run_info['top_name'],
                            run_info['user_name'], run_info['block_name'], run_info['dk_ver_tag'],
                            run_info['full_path'], datetime.datetime.now(), data_hash,
                            file_size, task_count, keyword_count, completion_rate
                        ))

                        archive_entry_id = cursor.lastrowid

                    # Insert task results
                    for task_name, task_data in run_data.get('tasks', {}).items():
                        cursor.execute('''
                            INSERT INTO task_results (
                                archive_entry_id, task_name, job_name, status,
                                log_files, report_files
                            ) VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            archive_entry_id, task_name,
                            task_data.get('job', 'unknown'),
                            task_data.get('status', 'unknown'),
                            json.dumps(task_data.get('log_files', [])),
                            json.dumps(task_data.get('report_files', []))
                        ))

                        task_result_id = cursor.lastrowid

#### 0930
# Insert keyword results
                        for keyword_name, keyword_data in task_data.get('keywords', {}).items():
                            # Handle both old and new keyword structures
                            keyword_value = keyword_data.get('value')

                            # Convert value to string for storage
                            if keyword_value is not None:
                                if isinstance(keyword_value, dict):
                                    # Old structure - shouldn't happen with dynamic_table_row
                                    value_str = json.dumps(keyword_value)
                                elif isinstance(keyword_value, list):
                                    # multiple_values type - store as JSON array
                                    value_str = json.dumps(keyword_value)
                                else:
                                    # Single value (number, string, etc.)
                                    value_str = str(keyword_value)
                            else:
                                value_str = ''

                            cursor.execute('''
                                INSERT INTO keyword_results (
                                    task_result_id, keyword_name, keyword_value,
                                    keyword_unit, keyword_type, source_file
                                ) VALUES (?, ?, ?, ?, ?, ?)
                            ''', (
                                task_result_id,
                                keyword_name,
                                value_str,
                                keyword_data.get('unit', ''),
                                keyword_data.get('type', ''),
                                keyword_data.get('file_name', '')
                            ))

                    conn.commit()
            else:
                # JSON fallback: update metadata file
                try:
                    with open(self.metadata_json_path, 'r') as f:
                        metadata = json.load(f)
                except FileNotFoundError:
                    metadata = {"archive_entries": [], "task_results": [], "keyword_results": []}

                # Check if entry already exists and remove it
                existing_entries = metadata.get("archive_entries", [])
                metadata["archive_entries"] = [
                    entry for entry in existing_entries
                    if not (entry.get("run_version") == run_info['run_version'] and
                           entry.get("base_dir") == run_info['base_dir'] and
                           entry.get("top_name") == run_info['top_name'] and
                           entry.get("user_name") == run_info['user_name'] and
                           entry.get("block_name") == run_info['block_name'] and
                           entry.get("dk_ver_tag") == run_info['dk_ver_tag'])
                ]

                # Add new/updated archive entry to JSON
                entry = {
                    "run_version": run_info['run_version'],
                    "base_dir": run_info['base_dir'],
                    "top_name": run_info['top_name'],
                    "user_name": run_info['user_name'],
                    "block_name": run_info['block_name'],
                    "dk_ver_tag": run_info['dk_ver_tag'],
                    "full_path": run_info['full_path'],
                    "archive_timestamp": datetime.datetime.now().isoformat(),
                    "data_hash": data_hash,
                    "file_size": file_size,
                    "task_count": task_count,
                    "keyword_count": keyword_count,
                    "completion_rate": completion_rate,
                    "data_file": data_filename
                }
                metadata["archive_entries"].append(entry)


                with open(self.metadata_json_path, 'w') as f:
                    json.dump(metadata, f, indent=2)

            return True

        except Exception as e:
            print(f"Error archiving run data: {e}")
            return False

    def get_archived_runs(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get list of archived runs with optional filtering

        Args:
            filters: Dictionary with filter criteria

        Returns:
            List of archived run information
        """
        if not self.use_sqlite:
            # JSON fallback: read from metadata file
            try:
                with open(self.metadata_json_path, 'r') as f:
                    metadata = json.load(f)

                entries = metadata.get('archive_entries', [])

                # Apply filters if provided
                if filters:
                    filtered_entries = []
                    for entry in entries:
                        match = True

                        if 'run_version' in filters and filters['run_version']:
                            if filters['run_version'] not in entry.get('run_version', ''):
                                match = False

                        if 'user_name' in filters and filters['user_name']:
                            if entry.get('user_name', '') != filters['user_name']:
                                match = False

                        if 'base_dir' in filters and filters['base_dir']:
                            if entry.get('base_dir', '') != filters['base_dir']:
                                match = False

                        if 'date_from' in filters and filters['date_from']:
                            if entry.get('archive_timestamp', '') < filters['date_from']:
                                match = False

                        if 'date_to' in filters and filters['date_to']:
                            if entry.get('archive_timestamp', '') > filters['date_to']:
                                match = False

                        if match:
                            filtered_entries.append(entry)

                    entries = filtered_entries

                # Sort by archive_timestamp descending
                entries.sort(key=lambda x: x.get('archive_timestamp', ''), reverse=True)
                return entries

            except FileNotFoundError:
                return []

        query = '''
            SELECT * FROM archive_entries
            WHERE status = 'active'
        '''
        params = []

        if filters:
            if 'run_version' in filters:
                query += ' AND run_version LIKE ?'
                params.append(f"%{filters['run_version']}%")
            if 'user_name' in filters:
                query += ' AND user_name = ?'
                params.append(filters['user_name'])
            if 'base_dir' in filters:
                query += ' AND base_dir = ?'
                params.append(filters['base_dir'])
            if 'date_from' in filters:
                query += ' AND archive_timestamp >= ?'
                params.append(filters['date_from'])
            if 'date_to' in filters:
                query += ' AND archive_timestamp <= ?'
                params.append(filters['date_to'])

        query += ' ORDER BY archive_timestamp DESC'

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_run_data(self, archive_entry_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve full run data by archive entry ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get archive entry
            cursor.execute('SELECT * FROM archive_entries WHERE id = ?', (archive_entry_id,))
            entry = cursor.fetchone()

            if not entry:
                return None

            # Load data file
            data_filename = f"{entry['run_version']}_{entry['data_hash'][:8]}.json"
            data_filepath = os.path.join(self.archive_base, 'data', data_filename)

            try:
                with open(data_filepath, 'r') as f:
                    return json.load(f)
            except FileNotFoundError:
                print(f"Data file not found: {data_filepath}")
                return None

    def export_to_csv(self, output_path: str, filters: Dict[str, Any] = None) -> bool:
        """Export archived data to CSV format"""
        try:
            import pandas as pd

            # Get archived runs
            runs = self.get_archived_runs(filters)

            if not runs:
                print("No runs found to export")
                return False

            # Create DataFrame
            df = pd.DataFrame(runs)

            # Save to CSV
            df.to_csv(output_path, index=False)
            print(f"Exported {len(runs)} runs to: {output_path}")
            return True

        except ImportError:
            print("pandas required for CSV export")
            return False
        except Exception as e:
            print(f"Export error: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get archive statistics"""
        if not self.use_sqlite:
            # JSON fallback: calculate stats from metadata
            try:
                with open(self.metadata_json_path, 'r') as f:
                    metadata = json.load(f)

                entries = metadata.get('archive_entries', [])
                total_entries = len(entries)

                # Calculate basic stats from JSON
                total_tasks = sum(entry.get('task_count', 0) for entry in entries)
                total_keywords = sum(entry.get('keyword_count', 0) for entry in entries)

                # Recent entries (last 7 days)
                from datetime import datetime, timedelta
                recent_cutoff = datetime.now() - timedelta(days=7)
                recent_entries = 0
                completion_rates = []

                for entry in entries:
                    if 'archive_timestamp' in entry:
                        try:
                            entry_date = datetime.fromisoformat(entry['archive_timestamp'].replace('Z', '+00:00'))
                            if entry_date >= recent_cutoff:
                                recent_entries += 1
                        except:
                            pass

                    if 'completion_rate' in entry and entry['completion_rate'] is not None:
                        completion_rates.append(entry['completion_rate'])

                avg_completion_rate = sum(completion_rates) / len(completion_rates) if completion_rates else 0.0

                return {
                    'total_entries': total_entries,
                    'total_tasks': total_tasks,
                    'total_keywords': total_keywords,
                    'recent_entries': recent_entries,
                    'average_completion_rate': round(avg_completion_rate, 2),
                    'archive_size_mb': self._get_archive_size_mb()
                }

            except FileNotFoundError:
                return {
                    'total_entries': 0,
                    'total_tasks': 0,
                    'total_keywords': 0,
                    'recent_entries': 0,
                    'average_completion_rate': 0.0,
                    'archive_size_mb': 0.0
                }

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total entries
            cursor.execute("SELECT COUNT(*) FROM archive_entries WHERE status = 'active'")
            total_entries = cursor.fetchone()[0]

            # Total tasks
            cursor.execute('''
                SELECT COUNT(*) FROM task_results tr
                JOIN archive_entries ae ON tr.archive_entry_id = ae.id
                WHERE ae.status = 'active'
            ''')
            total_tasks = cursor.fetchone()[0]

            # Total keywords
            cursor.execute('''
                SELECT COUNT(*) FROM keyword_results kr
                JOIN task_results tr ON kr.task_result_id = tr.id
                JOIN archive_entries ae ON tr.archive_entry_id = ae.id
                WHERE ae.status = 'active'
            ''')
            total_keywords = cursor.fetchone()[0]

            # Recent entries (last 7 days)
            cursor.execute('''
                SELECT COUNT(*) FROM archive_entries
                WHERE status = 'active' AND archive_timestamp >= datetime('now', '-7 days')
            ''')
            recent_entries = cursor.fetchone()[0]

            # Average completion rate
            cursor.execute('''
                SELECT AVG(completion_rate) FROM archive_entries
                WHERE status = 'active' AND completion_rate IS NOT NULL
            ''')
            avg_completion_rate = cursor.fetchone()[0] or 0.0

            return {
                'total_entries': total_entries,
                'total_tasks': total_tasks,
                'total_keywords': total_keywords,
                'recent_entries': recent_entries,
                'average_completion_rate': round(avg_completion_rate, 2),
                'archive_size_mb': self._get_archive_size_mb()
            }

    def _get_archive_size_mb(self) -> float:
        """Calculate total archive size in MB"""
        total_size = 0
        data_dir = os.path.join(self.archive_base, 'data')

        if os.path.exists(data_dir):
            for filename in os.listdir(data_dir):
                filepath = os.path.join(data_dir, filename)
                if os.path.isfile(filepath):
                    total_size += os.path.getsize(filepath)

        return round(total_size / (1024 * 1024), 2)

    def cleanup_old_entries(self, days_old: int = 90) -> int:
        """Mark old entries as inactive (soft delete)

        Args:
            days_old: Number of days after which entries are considered old

        Returns:
            Number of entries marked as inactive
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE archive_entries
                SET status = 'inactive'
                WHERE status = 'active'
                AND archive_timestamp < datetime('now', '-{} days')
            '''.format(days_old))

            cleaned_count = cursor.rowcount
            conn.commit()

            print(f"Marked {cleaned_count} entries as inactive (older than {days_old} days)")
            return cleaned_count

    def _auto_repair_metadata(self):
        """Automatically repair metadata if data files exist but metadata is empty"""
        try:
            # Check if we have any entries in metadata
            if self.use_sqlite:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM archive_entries")
                    entry_count = cursor.fetchone()[0]
            else:
                try:
                    with open(self.metadata_json_path, 'r') as f:
                        metadata = json.load(f)
                    entry_count = len(metadata.get('archive_entries', []))
                except FileNotFoundError:
                    entry_count = 0

            # Check if data files exist
            data_dir = os.path.join(self.archive_base, 'data')
            data_files = []
            if os.path.exists(data_dir):
                try:
                    all_files = os.listdir(data_dir)
                    data_files = [f for f in all_files if f.endswith('.json')]
                except:
                    pass

            # If no metadata entries but data files exist, repair
            if entry_count == 0 and len(data_files) > 0:
                print(f"- Auto-repair: Found {len(data_files)} orphaned data files, restoring metadata...")

                repaired_count = 0
                for data_file in data_files:
                    try:
                        file_path = os.path.join(data_dir, data_file)

                        # Load the data
                        with open(file_path, 'r') as f:
                            run_data = json.load(f)

                        # Extract run info from filename
                        parts = data_file.replace('.json', '').split('_')
                        if len(parts) >= 2:
                            run_version = parts[0]
                        else:
                            run_version = data_file.replace('.json', '')

                        # Get path information from the run_data
                        full_path = None

                        # Check multiple possible locations for path info
                        summary = run_data.get('summary', {})

                        # Try to find the full path in various places
                        full_path = None
                        path_source = None

                        if 'full_path' in summary:
                            full_path = summary['full_path']
                            path_source = "summary.full_path"
                        elif 'path' in summary:
                            full_path = summary['path']
                            path_source = "summary.path"
                        elif 'run_info' in run_data and isinstance(run_data['run_info'], dict):
                            if 'full_path' in run_data['run_info']:
                                full_path = run_data['run_info']['full_path']
                                path_source = "run_info.full_path"
                        elif 'analysis_info' in run_data and isinstance(run_data['analysis_info'], dict):
                            if 'path' in run_data['analysis_info']:
                                full_path = run_data['analysis_info']['path']
                                path_source = "analysis_info.path"

                        # Check if path info is stored in the tasks data
                        if not full_path and 'tasks' in run_data:
                            for task_name, task_data in run_data['tasks'].items():
                                if isinstance(task_data, dict):
                                    if 'path' in task_data:
                                        full_path = task_data['path']
                                        path_source = f"tasks.{task_name}.path"
                                        break
                                    elif 'run_path' in task_data:
                                        full_path = task_data['run_path']
                                        path_source = f"tasks.{task_name}.run_path"
                                        break

                        # Try to reconstruct from run_version and known pattern
                        if not full_path:
                            # Look for any path-like strings in the data
                            def find_paths_in_dict(d, prefix=""):
                                paths = []
                                if isinstance(d, dict):
                                    for k, v in d.items():
                                        if isinstance(v, str) and '/' in v and len(v) > 20:
                                            paths.append((f"{prefix}.{k}" if prefix else k, v))
                                        elif isinstance(v, dict):
                                            paths.extend(find_paths_in_dict(v, f"{prefix}.{k}" if prefix else k))
                                return paths

                            possible_paths = find_paths_in_dict(run_data)
                            if possible_paths:
                                # Use the first path that looks reasonable
                                for path_key, path_val in possible_paths:
                                    if run_version in path_val:
                                        full_path = path_val
                                        path_source = f"found_in_{path_key}"
                                        break

                        # Parse path hierarchy if we found a path
                        if full_path and '/' in full_path:
                            path_parts = full_path.strip('/').split('/')

                            # Parse according to your pattern:
                            # end = Run Version, end-1 = runs (skip), end-2 = DK Ver/Tag, end-3 = Block, end-4 = User (remove "works_")
                            if len(path_parts) >= 5:
                                run_version = path_parts[-1]  # PI-PD-fe00_te00_pv00

                                # Skip 'runs' directory if present
                                if path_parts[-2] == 'runs':
                                    dk_ver_tag = path_parts[-3]   # pd___rtl_3.0_dk_3.1_tag_2.0
                                    block_name = path_parts[-4]   # clk_gen or row_drv
                                    user_part = path_parts[-5]    # works_scott.lee
                                else:
                                    # No 'runs' directory
                                    dk_ver_tag = path_parts[-2]   # pd___rtl_3.0_dk_3.1_tag_2.0
                                    block_name = path_parts[-3]   # clk_gen or row_drv
                                    user_part = path_parts[-4]    # works_scott.lee

                                user_name = user_part.replace('works_', '') if user_part.startswith('works_') else user_part

                                # Extract additional info if path is longer
                                base_dir = path_parts[0] if len(path_parts) > 5 else 'unknown'
                                top_name = path_parts[1] if len(path_parts) > 6 else 'unknown'

                                run_info = {
                                    'run_version': run_version,
                                    'base_dir': base_dir,
                                    'top_name': top_name,
                                    'user_name': user_name,
                                    'block_name': block_name,
                                    'dk_ver_tag': dk_ver_tag,
                                    'full_path': full_path
                                }

                                # Path parsing successful - info stored in run_info
                            elif len(path_parts) >= 4:
                                # Partial hierarchy - extract what we can (accounting for possible 'runs' dir)
                                if path_parts[-2] == 'runs' and len(path_parts) >= 4:
                                    dk_ver_tag = path_parts[-3] if len(path_parts) >= 3 else 'unknown'
                                    block_name = path_parts[-4] if len(path_parts) >= 4 else 'unknown'
                                    user_name = 'unknown'
                                else:
                                    dk_ver_tag = path_parts[-2] if len(path_parts) >= 2 else 'unknown'
                                    block_name = path_parts[-3] if len(path_parts) >= 3 else 'unknown'
                                    user_name = 'unknown'

                                run_info = {
                                    'run_version': run_version,
                                    'base_dir': 'unknown',
                                    'top_name': 'unknown',
                                    'user_name': user_name,
                                    'block_name': block_name,
                                    'dk_ver_tag': dk_ver_tag,
                                    'full_path': full_path
                                }
                            else:
                                # Very short path - fallback
                                run_info = {
                                    'run_version': run_version,
                                    'base_dir': 'unknown',
                                    'top_name': 'unknown',
                                    'user_name': 'unknown',
                                    'block_name': 'unknown',
                                    'dk_ver_tag': 'unknown',
                                    'full_path': full_path
                                }
                        else:
                            # No path found - try to extract info from run_version pattern

                            # Try to extract user and other info from run_version or filename patterns
                            user_name = 'unknown'
                            block_name = 'unknown'
                            dk_ver_tag = 'unknown'

                            # Check if we can infer some info from the run_version
                            if 'PI-PD' in run_version:
                                # This looks like a PI-PD run, try some common patterns
                                if any(keyword in data_file.lower() for keyword in ['scott', 'lee']):
                                    user_name = 'scott.lee'

                                # Try to extract block info from common patterns
                                if 'rcp' in run_version.lower() or 'recipe' in run_version.lower():
                                    block_name = 'row_drv'  # Common block for recipes

                                # Try to extract DK version from common patterns
                                if 'rtl' in data_file.lower() or 'dk' in data_file.lower():
                                    dk_ver_tag = 'pi___rtl_3.0_dk_3.1_tag_2.0'  # Common pattern

                            run_info = {
                                'run_version': run_version,
                                'base_dir': 'mnt',
                                'top_name': 'data',
                                'user_name': user_name,
                                'block_name': block_name,
                                'dk_ver_tag': dk_ver_tag,
                                'full_path': f'auto_repaired_{data_file}'
                            }

                            # Pattern-based extraction completed

                        # Re-archive this data
                        success = self._archive_run_data(run_info, run_data)
                        if success:
                            repaired_count += 1

                    except Exception as e:
                        print(f"   - Failed to repair {data_file}: {e}")

                if repaired_count > 0:
                    print(f"- Auto-repair completed: {repaired_count}/{len(data_files)} entries restored")
                else:
                    print(f"- Auto-repair failed: No entries could be restored")

            elif entry_count > 0:
                print(f"- Archive metadata OK: {entry_count} entries found")

        except Exception as e:
            print(f"Auto-repair error: {e}")


def cleanup_orphaned_data_files(self):
    """Clean up orphaned data files that are no longer referenced in the database"""
    if not self.use_sqlite:
        return

    try:
        # Get all data hashes from database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT data_hash, run_version FROM archive_entries WHERE status = "active"')
            db_hashes = {f"{row[1]}_{row[0][:8]}.json" for row in cursor.fetchall()}

        # Get all data files
        data_dir = os.path.join(self.archive_base, 'data')
        if os.path.exists(data_dir):
            data_files = {f for f in os.listdir(data_dir) if f.endswith('.json')}

            # Find orphaned files
            orphaned_files = data_files - db_hashes

            if orphaned_files:
                print(f"Found {len(orphaned_files)} orphaned data files:")
                for orphaned_file in orphaned_files:
                    orphaned_path = os.path.join(data_dir, orphaned_file)
                    print(f"  Removing: {orphaned_file}")
                    os.remove(orphaned_path)
                print(f"Cleanup completed: removed {len(orphaned_files)} orphaned files")
            else:
                print("No orphaned files found")

    except Exception as e:
        print(f"Error during cleanup: {e}")


def get_default_archive_path():
    """Get default archive path using the same logic as the main system"""
    # Try environment variable first
    archive_path = os.getenv('HAWKEYE_ARCHIVE_BASE')

    if not archive_path:
        # Try casino_prj_name and casino_prj_base
        casino_prj_name = os.getenv('casino_prj_name')
        casino_prj_base = os.getenv('casino_prj_base')

        if casino_prj_name and casino_prj_base:
            archive_path = os.path.join(casino_prj_base, casino_prj_name, 'hawkeye_archive')
        elif casino_prj_name:
            archive_path = os.path.join(casino_prj_name, 'hawkeye_archive')
        else:
            # Fallback using casino_pond
            casino_pond_path = os.getenv('casino_pond', '')
            if casino_pond_path:
                project_base = os.path.dirname(casino_pond_path)
                project_name = os.getenv('casino_prj_name', 'unknown')
                archive_path = os.path.join(project_base, project_name, 'hawkeye_archive')
            else:
                archive_path = './hawkeye_archive'

    return archive_path

def main():
    """CLI interface for archive operations"""
    import argparse

    parser = argparse.ArgumentParser(description="Hawkeye Archive Management")
    parser.add_argument('--archive-path', help='Archive base path')
    parser.add_argument('--stats', action='store_true', help='Show archive statistics')
    parser.add_argument('--list', action='store_true', help='List archived runs')
    parser.add_argument('--export-csv', help='Export to CSV file')
    parser.add_argument('--cleanup', type=int, metavar='DAYS', help='Cleanup entries older than N days')

    args = parser.parse_args()

    # Initialize archive
    archive = HawkeyeArchive(args.archive_path)

    if args.stats:
        stats = archive.get_statistics()
        print("\n=== Hawkeye Archive Statistics ===")
        for key, value in stats.items():
            print(f"{key.replace('_', ' ').title()}: {value}")

    if args.list:
        runs = archive.get_archived_runs()
        print(f"\n=== Archived Runs ({len(runs)}) ===")
        for run in runs[:10]:  # Show first 10
            print(f"{run['archive_timestamp'][:10]} - {run['run_version']} ({run['user_name']})")
        if len(runs) > 10:
            print(f"... and {len(runs) - 10} more")

    if args.export_csv:
        success = archive.export_to_csv(args.export_csv)
        if success:
            print(f"Exported to: {args.export_csv}")

    if args.cleanup:
        cleaned = archive.cleanup_old_entries(args.cleanup)
        print(f"Cleaned up {cleaned} old entries")

if __name__ == "__main__":
    # Add cleanup command
    if len(sys.argv) > 1 and sys.argv[1] == 'cleanup':
        archive_path = get_default_archive_path()
        print(f"Using archive path: {archive_path}")
        archive = HawkeyeArchive(archive_path)
        archive.cleanup_orphaned_data_files()
    else:
        main()

