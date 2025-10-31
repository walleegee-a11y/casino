#!/usr/local/bin/python3.12
"""Test script to verify archive auto-repair with new JSON structure"""

import os
import sys

# Get archive path from command line or environment
if len(sys.argv) > 1:
    archive_path = sys.argv[1]
else:
    # Try to get from environment
    casino_prj_base = os.getenv('casino_prj_base')
    if not casino_prj_base:
        print("Error: Please provide archive path as argument or set casino_prj_base")
        sys.exit(1)

    # Assume ANA6716 project based on your example
    archive_path = os.path.join(casino_prj_base, 'ANA6716', 'hawkeye_archive')

print(f"Testing archive at: {archive_path}")
print(f"Archive exists: {os.path.exists(archive_path)}")

if not os.path.exists(archive_path):
    print("Error: Archive path does not exist")
    sys.exit(1)

# Import after path check
from hawkeye_archive import HawkeyeArchive

print("\n=== Initializing Archive (will trigger auto-repair) ===")
archive = HawkeyeArchive(archive_path)

print("\n=== Getting Archive Statistics ===")
stats = archive.get_statistics()
for key, value in stats.items():
    print(f"  {key}: {value}")

print("\n=== Listing Recent Runs (last 5) ===")
runs = archive.get_archived_runs()
print(f"Total runs found: {len(runs)}")

if runs:
    for i, run in enumerate(runs[:5]):
        print(f"\n  Run {i+1}:")
        print(f"    Version: {run['run_version']}")
        print(f"    User: {run['user_name']}")
        print(f"    Block: {run['block_name']}")
        print(f"    Timestamp: {run['archive_timestamp']}")
        print(f"    Tasks: {run['task_count']}")
        print(f"    Keywords: {run['keyword_count']}")
else:
    print("No runs found!")

print("\n=== Test Complete ===")
