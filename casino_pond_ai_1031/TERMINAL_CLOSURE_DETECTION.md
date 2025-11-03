# Terminal Closure Detection - Fast Detection Fix

## Problem
When a task terminal window is accidentally closed (clicking "X"), the flow manager console doesn't detect it for **10+ minutes**, leaving users unaware that their task was interrupted.

## Root Cause
The original detection was too conservative to avoid false positives with EDA tools:
- Checked process health every **5 minutes**
- Required **10 minutes** of stale status before declaring process dead
- Result: Users see no feedback for 10+ minutes after closing terminal

## Solution: Multi-Layer Detection

### Layer 1: FAST Terminal Death Detection (10 seconds)
**NEW** - Checks if terminal window process died every 10 seconds:
```python
# Check terminal process death every 10 seconds
if detect_terminal_closed_fast(process, task_name):
    # Terminal window closed - check if task is still alive
    if not check_task_process_alive(pid_file, task_name):
        # Task is dead - mark as INTERRUPTED immediately
        return "Interrupted"
```

**Detection Time**: **10 seconds** (down from 10+ minutes)

### Layer 2: Deep Process Check (5 minutes, only if status stale)
Keeps the conservative deep checks for long-running EDA tools:
```python
# Only if status file hasn't updated in 10 minutes
if current_time - last_status_update > 600:
    if detect_accidental_closure_csh_relaxed(pid_file, task_name):
        return "Interrupted"
```

## Detection Timeline

| Event | Old Behavior | New Behavior |
|-------|-------------|--------------|
| User closes task terminal | No detection for 10+ minutes | Detected in **10 seconds** |
| EDA tool running normally | (Avoided false positives) | (Still avoids false positives) |
| Process becomes zombie | Detected in 10+ minutes | Detected in 10 seconds |

## Console Output

When you close a task terminal, you'll now see within **10 seconds**:

```
WARNING: Terminal window for place_inn was closed!
Checking if task process is still alive...
CONFIRMED: Task process is dead - marking as INTERRUPTED
Cleaning up orphaned processes for task: place_inn
Task place_inn was interrupted - execution will stop
```

## Special Cases

### Case 1: Task Detaches from Terminal (Background Execution)
Some tasks may legitimately detach from the terminal and continue running:
```
WARNING: Terminal window for place_inn was closed!
Checking if task process is still alive...
INFO: Task process still running despite terminal closure (background execution)
```
Flow manager continues monitoring the task.

### Case 2: EDA Tool Long-Running (No Terminal Closure)
If status file updates normally:
- Fast terminal check: Passes (terminal alive)
- Deep process check: Not triggered (status file updating)
- No false positives

## Files Modified

- `fm_casino.py`:
  - Line 1059-1143: Enhanced `monitor_with_process_tree_csh()` with fast detection
  - Line 1146-1159: Added `detect_terminal_closed_fast()` function
  - Line 1161-1188: Added `check_task_process_alive()` function

## Testing

Test the fix:
```bash
# Start a flow
fm_casino.py -start place_inn -end route_inn -monitor

# Wait for a task to start running
# Close the task terminal window (click X)
# Watch console output - should detect within 10 seconds
```

Expected console output:
```
Monitoring task completion for place_inn - checking status file + terminal + process health...
Task place_inn is running...
WARNING: Terminal window for place_inn was closed!
Checking if task process is still alive...
CONFIRMED: Task process is dead - marking as INTERRUPTED
```

## Benefits

1. **Fast Feedback**: Users know immediately (10s) when they make a mistake
2. **No False Positives**: Deep checks still use conservative 10-minute grace period
3. **Clear Messages**: Console shows exactly what happened
4. **Automatic Cleanup**: Orphaned processes cleaned up immediately
5. **Execution Stops**: Prevents wasting time on dependent tasks
