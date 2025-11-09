# Fix for sta_pt Task Failing Due to Background Process Launch

## Problem Summary
The `_run_sta_pt.csh` script in `common_casino/globals/pi/sta_pt/` launches multiple xterm/pt_shell processes in the background with `&`, then exits immediately. The flow manager (`fm_casino.py`) sees the script exit quickly (after ~5 seconds) and marks it as "Failed", causing 3 automatic retries.

## Root Cause Analysis

### Current Behavior (lines 48-81 of _run_sta_pt.csh)
```csh
foreach mode ( ${sta_pt_modes} )
    foreach corner ( ${sta_pt_corners} )
        if !(${corner} == "") then
            # ... setup directories ...

            # Launches xterm in background - script doesn't wait
            xterm -T ${run_ver}/sta_pt/${mode}/${corner} -e 'pt_shell -f run_sta_pt.tcl -output_log_file ./logs/sta_pt.log' &

            cd ${RUN_PATH}/sta_pt
        endif
    end
end

#TODO: wait & monitoring status   # <-- This feature was never implemented!
```

### Why It Fails
1. Script spawns background xterm processes using `&`
2. Script exits immediately after spawning (no wait mechanism)
3. Flow manager's wrapper sees exit code 0 (success) initially
4. But monitoring detects the main csh process died too quickly
5. Flow manager marks it as "Failed" or "Interrupted"
6. Automatically retries 3 times (configured in fm_casino.py)

### The TODO Comment
Line 81 has `#TODO: wait & monitoring status` - this feature was never implemented.

## Solution: Add Wait Loop with Process Monitoring

### Changes Needed to _run_sta_pt.csh

**Step 1: Initialize PID tracking arrays (after line 45)**
```csh
# Initialize arrays to store background process PIDs and job names
set xterm_pids = ()
set job_list = ()
```

**Step 2: Capture PIDs when launching xterms (replace line 70)**
```csh
# OLD:
xterm -T ${run_ver}/sta_pt/${mode}/${corner} -e 'pt_shell -f run_sta_pt.tcl -output_log_file ./logs/sta_pt.log' &

# NEW:
# Launch xterm in background and capture its PID
xterm -T ${run_ver}/sta_pt/${mode}/${corner} -e 'pt_shell -f run_sta_pt.tcl -output_log_file ./logs/sta_pt.log' &
set xterm_pids = ($xterm_pids $!)
set job_list = ($job_list "${mode}.${corner}")
```

**Step 3: Replace TODO comment with wait loop (replace lines 81-82)**
```csh
# Wait for all background processes to complete and monitor their status
echo ""
echo "=================================================="
echo "Launched ${#xterm_pids} pt_shell jobs in background"
echo "Waiting for all jobs to complete..."
echo "=================================================="

set return_value = 0
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
			# Process completed - check its log file for status
			set job_name = $job_list[$idx]
			echo "`date`: Job ${job_name} (PID: ${pid}) completed"
			@ completed_count++

			# Check log file for errors (optional - can be enhanced)
			set mode_corner = `echo $job_name | sed 's/\./ /g'`
			set log_file = "${RUN_PATH}/sta_pt/${mode_corner}/logs/sta_pt.log"
			if ( -e $log_file ) then
				# Check for critical errors in log
				grep -qi "error" $log_file
				if ( $status == 0 ) then
					echo "  WARNING: Found errors in ${log_file}"
					@ failed_count++
					set return_value = 1
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

# Exit with appropriate code
exit $return_value
```

## How the Fix Works

1. **PID Collection**: When each xterm is launched with `&`, capture its PID using `$!` and store in array
2. **Job Tracking**: Store corresponding job names (mode.corner) for status reporting
3. **Wait Loop**: Continuously check if each PID is still running using `ps -p $pid`
4. **Progress Reporting**: Report when jobs complete, show count of running vs completed
5. **Error Detection**: Check log files for "error" keyword when jobs complete
6. **Proper Exit Code**: Return 0 for success, 1 if any errors found in logs

## Benefits

- ✅ Flow manager sees script running until all pt_shell jobs complete
- ✅ No more premature "Failed" status and unnecessary retries
- ✅ Progress monitoring shows which jobs are still running
- ✅ Error detection from log files
- ✅ Proper exit codes for flow manager to interpret

## Manual Application Steps

**Backup the original:**
```bash
cd D:/CASINO/casino_pond_ai/common_casino/globals/pi/sta_pt
cp _run_sta_pt.csh _run_sta_pt.csh.backup_before_fix
```

**Apply the fix:**
1. Open `_run_sta_pt.csh` in an editor
2. After line 45 (the `endif` for RUN_STA_PT_TCL), add the PID array initialization
3. On line 70, modify the xterm launch to capture PID
4. Replace the TODO comment (lines 81-82) with the complete wait loop

**Or use the complete fixed version in:**
`STA_PT_FIXED_SCRIPT.csh` (see next section)

## Testing

After applying the fix:
```bash
cd /mnt/data/prjs/ANA6716/works_rachel.han/ANA6716/pi___net-2.1_dk-2.2_tag-0.0/runs/01_net-02_FP-fe00_te00_pv00
python3.12 $casino_pond/fm_casino.py -only sta_pt -y
```

Expected behavior:
- Script will show "Launched N pt_shell jobs in background"
- Progress updates every 10 seconds showing completed/running jobs
- Script waits until all xterm windows close
- Returns proper exit code
- No more premature failures and retries

## Files Modified

- `common_casino/globals/pi/sta_pt/_run_sta_pt.csh` - Main script with wait loop added

## Backup Location

Original script backed up to:
- `common_casino/globals/pi/sta_pt/_run_sta_pt.csh.backup_before_fix`
