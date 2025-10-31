# Hawkeye Archive Orphan Data Fix

## Problem
Newly archived JSON data files were created in `hawkeye_archive/data/` but were not visible in the Hawkeye Web Dashboard, even after restarting the web server and refreshing the browser.

## Root Causes

### 1. Changed JSON Structure Not Handled
The archive system was expecting a flat structure:
```json
{
  "tasks": {
    "DRC": { "keywords": {...} }
  }
}
```

But the actual data now has a nested structure:
```json
{
  "path": "/mnt/data/prjs/ANA6716/...",
  "jobs": {
    "pv": {
      "tasks": {
        "DRC": { "keywords": {...} }
      }
    }
  }
}
```

### 2. Auto-Repair Only Ran on Empty Database
The `_auto_repair_metadata()` function only ran when `entry_count == 0`, meaning:
- If you had old entries in the database, new orphaned files would never be detected
- Auto-repair wouldn't run even though new data files existed

## Solution

### Changes to `hawkeye_archive.py`

#### 1. Fixed Keyword Counting (Lines 356-370)
**Before:**
```python
keyword_count = 0
for task_data in run_data.get('tasks', {}).values():
    keyword_count += len(task_data.get('keywords', {}))
```

**After:**
```python
# Handle both old (direct tasks) and new (jobs->tasks) structure
keyword_count = 0
tasks_dict = {}

if 'jobs' in run_data:
    # New structure: jobs->job_name->tasks
    for job_name, job_data in run_data['jobs'].items():
        if 'tasks' in job_data:
            tasks_dict.update(job_data['tasks'])
elif 'tasks' in run_data:
    # Old structure: direct tasks
    tasks_dict = run_data['tasks']

for task_data in tasks_dict.values():
    keyword_count += len(task_data.get('keywords', {}))
```

#### 2. Fixed Task Insertion (Lines 450-477)
Now handles both flat and nested task structures when inserting into the database.

#### 3. Fixed Path Extraction in Auto-Repair (Lines 896-916)
Added checks for `path` at the root level of JSON (where new structure has it):
```python
# Check root level first (new structure)
if 'path' in run_data:
    full_path = run_data['path']
    path_source = "root.path"
elif 'full_path' in run_data:
    full_path = run_data['full_path']
    path_source = "root.full_path"
# ... then check other locations
```

#### 4. Fixed Orphan Detection (Lines 866-889)
**Before:** Only ran repair if `entry_count == 0`

**After:** Always checks for orphaned files by comparing data files against database entries:
```python
# Find orphaned data files (files not in database)
orphaned_files = []
if len(data_files) > 0:
    if self.use_sqlite:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT data_hash, run_version FROM archive_entries')
            db_entries = cursor.fetchall()
            # Create set of expected filenames
            expected_files = {f"{row[1]}_{row[0][:8]}.json" for row in db_entries}
            orphaned_files = [f for f in data_files if f not in expected_files]
```

### Changes to Web Server

#### 1. Added Repair API Endpoint (`api.py` Lines 320-344)
```python
@api_bp.route('/repair-archive', methods=['POST'])
def repair_archive():
    """Force archive repair to detect and import orphaned data files"""
    archive = get_archive()
    archive._auto_repair_metadata()
    stats = archive.get_statistics()
    return jsonify({'success': True, 'statistics': stats})
```

#### 2. Added "Repair Archive" Button to Dashboard
- Added orange "Repair Archive" button next to "Change Project" button
- Button triggers the repair API endpoint
- Shows "Repairing..." status while running
- Reloads runs and statistics after repair completes

## Usage

### Automatic (on server restart)
When you restart the Hawkeye web server, it will now:
1. Initialize the archive
2. Automatically detect orphaned data files
3. Import them into the database
4. Display them in the dashboard

### Manual (via UI button)
1. Open the Hawkeye Dashboard in your browser
2. Click the orange "**Repair Archive**" button in the top-right
3. Wait for the repair to complete
4. The page will automatically reload with the new data

### Command Line Test
Use the test script to verify repair works:
```bash
python test_archive_repair.py /mnt/data/prjs/ANA6716/hawkeye_archive
```

## Files Modified

1. **hawkeye_archive.py**
   - Lines 356-370: Keyword counting with nested structure support
   - Lines 450-477: Task insertion with nested structure support
   - Lines 866-899: Orphan detection logic (always runs, not just on empty DB)
   - Lines 896-916: Path extraction checks root level first

2. **hawkeye_web_server/routes/api.py**
   - Lines 320-344: New `/api/repair-archive` endpoint

3. **hawkeye_web_server/templates/dashboard.html**
   - Lines 36-45: Added "Repair Archive" button

4. **hawkeye_web_server/static/js/dashboard.js**
   - Lines 61-99: Added `repairArchive()` function

5. **test_archive_repair.py** (new file)
   - Test script to verify archive repair functionality

## Backward Compatibility

All changes are **backward compatible**:
- ✅ Old flat `tasks` structure still works
- ✅ New nested `jobs->tasks` structure works
- ✅ Handles both `path` at root and in nested locations
- ✅ Existing archived data remains accessible

## Testing

After these changes:
1. ✅ Restart web server → auto-repair runs on startup
2. ✅ Click "Repair Archive" button → manual repair works
3. ✅ New data files automatically detected and imported
4. ✅ Both old and new JSON structures handled correctly
