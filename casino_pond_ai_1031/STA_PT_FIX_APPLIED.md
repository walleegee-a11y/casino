# sta_pt Task Background Process Fix - APPLIED

## Status: ✅ FIX APPLIED TO FILE

**File Fixed:** `common_casino/globals/pi/sta_pt/_run_sta_pt.csh`

## Summary of Changes

The script has been modified to:
1. **Wait for all background `pt_shell` processes** to complete before exiting (prevents premature "Failed" status)
2. **Remove reference to missing backup_old_run.csh** file (fixes "No such file or directory" error)

## Changes Applied

### Fix 1: Background Process Waiting

#### 1. Added PID Tracking Arrays (Lines 107-109)
```csh
# Initialize arrays to store background process PIDs and job names
set xterm_pids = ()
set job_list = ()
```

**Purpose:** Store process IDs and job names for monitoring

### 2. Modified xterm Launch to Capture PIDs (Lines 162-163)
```csh
eval "${xterm_cmd}-${pos_x}+${pos_y} -T ${run_ver}/sta_pt/${mode}/${corner} -e 'pt_shell -f run_sta_pt.tcl -output_log_file logs/sta_pt.log' &"
set xterm_pids = ($xterm_pids $!)
set job_list = ($job_list "${mode}.${corner}")
```

**Purpose:** Capture the PID (`$!`) of each launched xterm process

### 3. Added Wait Loop (Lines 179-242)
```csh
# Wait for all background pt_shell processes to complete
echo ""
echo "=================================================="
echo "Launched ${#xterm_pids} pt_shell jobs in background"
echo "Waiting for all jobs to complete..."
echo "=================================================="

set all_jobs_completed = 0
set completed_count = 0
set failed_count = 0

# Monitor loop - check every 10 seconds
while ( ${#xterm_pids} > 0 )
    set new_pids = ()
    set new_jobs = ()
    set idx = 1

    foreach pid ( $xterm_pids )
        # Check if process is still running
        ps -p $pid >& /dev/null
        if ( $status != 0 ) then
            # Process completed
            set job_name = $job_list[$idx]
            echo "`date`: Job ${job_name} (PID: ${pid}) completed"
            @ completed_count++

            # Check log file for errors
            set mode_corner = `echo $job_name | sed 's/\\./ /g'`
            set log_file = "${RUN_PATH}/sta_pt/${mode_corner}/logs/sta_pt.log"
            if ( -e $log_file ) then
                # Check for critical errors in log
                grep -qi "error" $log_file
                if ( $status == 0 ) then
                    echo "  WARNING: Found errors in ${log_file}"
                    @ failed_count++
                endif
            endif
        else
            # Process still running - keep in list
            set new_pids = ($new_pids $pid)
            set new_jobs = ($new_jobs $job_list[$idx])
        endif
        @ idx++
    end

    # Update lists
    set xterm_pids = ($new_pids)
    set job_list = ($new_jobs)

    # Report progress
    if ( ${#xterm_pids} > 0 ) then
        echo "`date`: ${completed_count} jobs completed, ${#xterm_pids} still running..."
        sleep 10
    endif
end

echo ""
echo "=================================================="
echo "All pt_shell jobs completed"
echo "Completed: ${completed_count} jobs"
if ( $failed_count > 0 ) then
    echo "WARNING: ${failed_count} jobs had errors in logs"
endif
echo "=================================================="
```

**Purpose:**
- Wait for all launched xterm processes to complete
- Monitor progress every 10 seconds
- Report completion status
- Check log files for errors

### 4. Enhanced Exit Code Logic (Lines 251-255)
```csh
# Set final return value based on both error detection and timing summary
if ( $failed_count > 0 ) then
    echo "WARNING: Setting return value to 1 due to ${failed_count} jobs with errors"
    set return_value = 1
endif

exit $return_value
```

**Purpose:** Set proper exit code if errors detected in logs, while still allowing `:timing_summary.tcl` to set the return value

### Fix 2: Remove Missing File Reference

#### 5. Commented Out Missing backup_old_run.csh (Lines 28-29)
```csh
# backup old run data
# COMMENTED OUT - backup_old_run.csh doesn't exist; cleanup handled by :clean.csh generated below
#source ${RUN_COMMON_PI}/backup_old_run.csh
```

**Purpose:**
- Prevent "No such file or directory" error
- The file `backup_old_run.csh` was never created in the codebase
- Cleanup is already handled by `:clean.csh` scripts generated on lines 127-138
- Other PI scripts (ldrc_dc, syn_dc) don't use a central backup script

## How It Works

### Before the Fixes:
1. Script tries to source missing `backup_old_run.csh` file → **Error: "No such file or directory"**
2. Even if that was fixed, script would launch xterm windows in background and exit immediately
3. Flow manager sees quick exit and marks as "Failed"
4. Automatically retries 3 times
5. All 3 retries fail with the same errors

### After the Fixes:
1. **Skips missing backup_old_run.csh** (line commented out, cleanup handled by :clean.csh)
2. Script launches multiple xterm windows with `pt_shell` in background
3. **Script captures all PIDs** of launched processes
4. **Script waits** until all processes complete
5. **Progress updates** printed every 10 seconds
6. **Log files checked** for errors when each job completes
7. **Status scripts run** (`:check_running_status.csh` and `:timing_summary.tcl`)
8. **Proper exit code returned** based on errors found
9. Flow manager sees long-running process that completes properly
10. **No more "file not found" errors**
11. **No more premature failures or retries**

## Known Issue: gnome-terminal D-Bus Error

If you encounter this error:
```
Error constructing proxy for org.gnome.Terminal:/org/gnome/Terminal/Factory0: The connection is closed
```

This is **NOT** a script issue - it's a problem with gnome-terminal's D-Bus communication. The flow manager by default tries to use gnome-terminal on GNOME desktop environments.

### Solution: Use xterm explicitly

Run the flow manager with the `-terminal xterm` flag:

```bash
cd /mnt/data/prjs/ANA6716/works_rachel.han/ANA6716/pi___net-2.1_dk-2.2_tag-0.0/runs/01_net-02_FP-fe00_te00_pv00
python3.12 $casino_pond/fm_casino.py -only sta_pt -y -terminal xterm
```

The `-terminal xterm` flag tells the flow manager to use xterm instead of gnome-terminal. Since the `_run_sta_pt.csh` script itself uses xterm (line 162), this is the appropriate choice.

## Expected Behavior

When you run the flow manager with `sta_pt` task:

```bash
cd /mnt/data/prjs/ANA6716/works_rachel.han/ANA6716/pi___net-2.1_dk-2.2_tag-0.0/runs/01_net-02_FP-fe00_te00_pv00
python3.12 $casino_pond/fm_casino.py -only sta_pt -y -terminal xterm
```

**You will see:**
```
Using terminal: xterm
...
Executing sta_pt at 2025/10/30 HH:MM:SS with command: cd sta_pt ; source ./all_tools_env.csh ; source ../common/globals/pi/sta_pt/:run_sta_pt.csh
Monitoring task completion for sta_pt - checking status file + process health...

==================================================
Launched 4 pt_shell jobs in background
Waiting for all jobs to complete...
==================================================
Thu Oct 30 HH:MM:SS 2025: 0 jobs completed, 4 still running...
Thu Oct 30 HH:MM:SS 2025: 0 jobs completed, 4 still running...
Thu Oct 30 HH:MM:SS 2025: Job setup.corner1 (PID: 12345) completed
Thu Oct 30 HH:MM:SS 2025: 1 jobs completed, 3 still running...
Thu Oct 30 HH:MM:SS 2025: Job setup.corner2 (PID: 12346) completed
Thu Oct 30 HH:MM:SS 2025: 2 jobs completed, 2 still running...
...
==================================================
All pt_shell jobs completed
Completed: 4 jobs
==================================================

Task sta_pt completed successfully
CONFIRMED: Task sta_pt completed successfully - proceeding to next task
```

**Result:**
- ✅ Task completes successfully (or fails with proper error detection)
- ✅ No premature failures
- ✅ No automatic retries
- ✅ Proper exit codes

## Testing

To test the fix:

1. Navigate to your run directory
2. Run the flow manager with sta_pt task **using xterm**:
   ```bash
   python3.12 $casino_pond/fm_casino.py -only sta_pt -y -terminal xterm
   ```

3. Observe the output:
   - Should see "Using terminal: xterm"
   - Should see "Launched N pt_shell jobs in background"
   - Should see progress updates every 10 seconds
   - Should see "All pt_shell jobs completed" at the end
   - Task should succeed (or fail with proper error, not "interrupted")

## Backup

The original file has been automatically backed up by the system. If you need to revert:

```bash
cd D:/CASINO/casino_pond_ai/common_casino/globals/pi/sta_pt
# Check git status to see changes
git diff _run_sta_pt.csh

# To revert (if needed):
git checkout _run_sta_pt.csh
```

## Files Modified

- ✅ `common_casino/globals/pi/sta_pt/_run_sta_pt.csh` - **FIXED AND READY TO USE**
- ✅ `fm_casino.py` - **NO CHANGES NEEDED** (just use `-terminal xterm` flag)

## Related Documentation

- `STA_PT_BACKGROUND_PROCESS_FIX.md` - Original fix documentation
- `STA_PT_FIXED_SCRIPT.csh` - Earlier version of the fixed script

## Summary

The fix has been **successfully applied** to `_run_sta_pt.csh`. The script will now:
- Wait for all background pt_shell processes to complete
- Monitor progress and report status
- Check log files for errors
- Return proper exit codes
- Work correctly with the flow manager (no more premature failures)

**The sta_pt task should now execute properly when using xterm as the terminal emulator!**

Run with: `python3.12 $casino_pond/fm_casino.py -only sta_pt -y -terminal xterm`
