"""Archive management for Hawkeye Web Server"""

import os
from hawkeye_archive import HawkeyeArchive


# Global state for archive system
archive = None
available_projects = []


def discover_projects():
    """Discover available projects in casino_prj_base"""
    global available_projects

    casino_prj_base = os.getenv('casino_prj_base')
    if not casino_prj_base or not os.path.exists(casino_prj_base):
        return []

    projects = []
    try:
        for item in os.listdir(casino_prj_base):
            project_path = os.path.join(casino_prj_base, item)
            if os.path.isdir(project_path):
                # Check if hawkeye_archive exists
                archive_path = os.path.join(project_path, 'hawkeye_archive')
                has_archive = os.path.exists(archive_path)

                # Get archive statistics if available
                archive_info = {
                    'name': item,
                    'path': project_path,
                    'archive_path': archive_path,
                    'has_archive': has_archive,
                    'run_count': 0,
                    'last_updated': None
                }

                if has_archive:
                    try:
                        temp_archive = HawkeyeArchive(archive_path)
                        stats = temp_archive.get_statistics()
                        archive_info['run_count'] = stats.get('total_entries', 0)
                        # Get latest timestamp from runs
                        runs = temp_archive.get_archived_runs()
                        if runs:
                            latest = max(runs, key=lambda x: x.get('archive_timestamp', ''))
                            archive_info['last_updated'] = latest.get('archive_timestamp')
                    except Exception as e:
                        print(f"Error reading archive for {item}: {e}")

                projects.append(archive_info)
    except Exception as e:
        print(f"Error discovering projects: {e}")

    available_projects = sorted(projects, key=lambda x: x['name'])
    return available_projects


def init_archive(project_name=None):
    """Initialize archive for selected project"""
    global archive

    if project_name:
        casino_prj_base = os.getenv('casino_prj_base')
        if casino_prj_base:
            archive_path = os.path.join(casino_prj_base, project_name, 'hawkeye_archive')
            print(f"DEBUG: Looking for archive at: {archive_path}")
            print(f"DEBUG: Archive exists: {os.path.exists(archive_path)}")

            if os.path.exists(archive_path):
                try:
                    archive = HawkeyeArchive(archive_path)
                    print(f"DEBUG: Archive initialized successfully")
                    return True
                except Exception as e:
                    print(f"ERROR: Failed to initialize archive: {e}")
                    import traceback
                    traceback.print_exc()
                    return False
            else:
                print(f"ERROR: Archive path does not exist: {archive_path}")

    return False


def get_archive():
    """Get the current archive instance"""
    return archive


def get_available_projects():
    """Get the list of available projects"""
    return available_projects
