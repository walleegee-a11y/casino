# Web Server Job Aggregates Implementation

## Overview

Added job-level aggregate views (pv_all, sta_pt_all, apr_inn_all, etc.) to the hawkeye web server comparison view, matching the functionality implemented in the desktop GUI.

## Implementation Summary

### 1. Backend API Changes

**File**: `hawkeye_web_server/routes/api.py`

Added two new features:

#### a) `aggregate_tasks_to_job()` function (Lines 14-104)
Aggregates multiple task results into a single job-level aggregate using the same logic as the desktop GUI:

- **SUM**: errors, warnings, counts, TNS, NOV, runtime
- **MIN**: WNS (worst = most negative)
- **MAX**: overflow, hotspot (congestion)
- **LAST**: area, utilization, density
- **AVERAGE**: other metrics

#### b) `/api/jobs` endpoint (Lines 166-180)
New REST API endpoint that serves the jobs configuration from `vista_casino.yaml`:
```bash
GET /api/jobs
```

Returns:
```json
{
  "pv": {
    "description": "Physical Verification",
    "tasks": ["DRC", "LVS"]
  },
  "sta_pt": { ... },
  "apr_inn": { ... }
}
```

### 2. Frontend JavaScript Changes

**File**: `hawkeye_web_server/static/js/dashboard.js`

Added aggregate computation logic:

#### a) Global Variables (Lines 22-23)
```javascript
let jobsConfig = null;        // Store jobs from vista_casino.yaml
let currentViewMode = 'task';  // Future: 'task', 'job', or 'both'
```

#### b) `aggregateTasksToJob()` function (Lines 30-148)
JavaScript implementation of the aggregation algorithm (same logic as Python backend).

#### c) `loadJobsConfig()` function (Lines 153-164)
Loads jobs configuration from `/api/jobs` endpoint on page load.

#### d) `computeAggregatesForRun()` function (Lines 172-214)
Computes aggregates for each run based on jobs configuration:
- Checks if all tasks for a job are present
- Computes aggregate using `aggregateTasksToJob()`
- Adds aggregate task (e.g., `pv_all`, `apr_inn_all`) to run's keywords

#### e) Modified `showComparison()` (Line 685)
Integrated aggregate computation into comparison workflow:
```javascript
// Compute aggregates for this run (pv_all, sta_pt_all, apr_inn_all, etc.)
formattedRun.keywords = computeAggregatesForRun(formattedRun.keywords);
```

#### f) Recollect Keywords (Lines 690-702)
After computing aggregates, recollects all keyword names including new aggregate keywords.

### 3. Visual Styling Changes

**File**: `hawkeye_web_server/static/js/comparison.js`

Added visual distinction for aggregate task rows (Lines 270-276):

```javascript
const isAggregate = taskName.endsWith('_all');
const taskStyle = isAggregate
    ? 'font-weight: bold; background: #3498db; color: white; ...'  // Blue background, white text, bold
    : 'font-weight: normal; background: #f8f9fa; color: #2c3e50; ...';  // Normal styling
```

**Visual Appearance**:
- **Aggregate tasks** (pv_all, sta_pt_all, apr_inn_all): **Bold text, blue background (#3498db), white text**
- **Regular tasks** (DRC, LVS, place_inn): Normal text, light gray background

## How It Works

### Workflow

1. **Page Load**:
   - Load jobs configuration from `/api/jobs`
   - Store in `jobsConfig` global variable

2. **User Selects Runs for Comparison**:
   - User checks runs in main dashboard
   - Clicks "Compare Selected Runs" button

3. **Aggregate Computation**:
   - For each run, check if all tasks for each job are present
   - If yes, compute aggregate using aggregation rules
   - Add aggregate task (e.g., `pv_all`) to run's keywords

4. **Display in Comparison View**:
   - Aggregate tasks appear in task list
   - Styled with **bold text and blue background**
   - Values computed using aggregation strategies

### Example

For a run with tasks `DRC` and `LVS`:

**Input**:
```
DRC:
  error: 5
  warning: 10
  cpu_time: 100s

LVS:
  error: 3
  warning: 8
  cpu_time: 200s
```

**Output** (pv_all aggregate):
```
pv_all:
  error: 8        (SUM: 5 + 3)
  warning: 18     (SUM: 10 + 8)
  cpu_time: 300s  (SUM: 100 + 200)
```

## Aggregation Rules

See `AGGREGATION_RULES.md` for detailed aggregation strategies.

| Metric | Strategy | Reasoning |
|--------|----------|-----------|
| WNS | MIN | One critical path determines overall timing |
| TNS | SUM | All negative slack accumulates |
| Errors | SUM | Total error count across stages |
| Area | LAST | Final stage has authoritative value |
| Runtime | SUM | Total time spent |

## Configuration

Job definitions are read from `vista_casino.yaml`:

```yaml
jobs:
  pv:
    description: "Physical Verification"
    tasks: ["DRC", "LVS"]

  sta_pt:
    description: "Static Timing Analysis"
    tasks: ["sta_pt"]

  apr_inn:
    description: "Innovus APR"
    tasks: ["init_inn", "place_inn", "cts_inn", "postcts_inn",
            "route_inn", "postroute_inn", "chipfinish_inn"]
```

## Files Modified

1. **hawkeye_web_server/routes/api.py**
   - Added `aggregate_tasks_to_job()` function
   - Added `/api/jobs` endpoint

2. **hawkeye_web_server/static/js/dashboard.js**
   - Added `aggregateTasksToJob()` JavaScript function
   - Added `loadJobsConfig()` function
   - Added `computeAggregatesForRun()` function
   - Modified `showComparison()` to compute aggregates
   - Modified DOMContentLoaded to load jobs config

3. **hawkeye_web_server/static/js/comparison.js**
   - Added visual styling for aggregate task rows (bold, blue background)

## Testing

To test the aggregate functionality:

1. **Start web server**:
   ```bash
   python3.12 hawkeye_web_server.py
   ```

2. **Select project** in web browser

3. **Select multiple runs** that include:
   - DRC and LVS tasks → should see `pv_all` aggregate
   - APR tasks → should see `apr_inn_all` aggregate

4. **Click "Compare Selected Runs"**

5. **Verify** in comparison view:
   - Aggregate tasks appear in task list
   - Aggregate tasks have **bold text and blue background**
   - Aggregate values computed correctly (check against manual calculation)

## Comparison with Desktop GUI

The web server implementation matches the desktop GUI functionality:

| Feature | Desktop GUI | Web Server |
|---------|-------------|------------|
| Aggregate computation | ✅ Python | ✅ JavaScript |
| Jobs from vista_casino.yaml | ✅ Yes | ✅ Yes |
| Aggregation rules | ✅ Same | ✅ Same |
| Visual styling | ✅ Bold, blue background | ✅ Bold, blue background |
| View mode toggle | ✅ Task/Job/Both | ⚠️ Not yet (future) |

**Note**: View mode toggle (Task View / Job View / Both) is not implemented in the web server yet, but the aggregate computation infrastructure is ready for it.

## Benefits

1. **Consistent with Desktop GUI**: Same aggregation logic and visual styling
2. **Uses vista_casino.yaml**: Single source of truth for job definitions
3. **On-Demand Computation**: Aggregates computed in browser, not stored in archive
4. **Extensible**: Easy to add new jobs by updating vista_casino.yaml
5. **Visual Distinction**: Bold blue highlighting makes aggregates easy to identify

## Future Enhancements

1. **View Mode Toggle**: Add UI buttons to toggle between:
   - Task View (show only individual tasks)
   - Job View (show only aggregates)
   - Both (show tasks and aggregates together)

2. **Archive Integration**: Consider archiving aggregates for faster loading (though current on-demand approach is working well)

3. **Customizable Styling**: Allow users to customize aggregate row colors

4. **Export with Aggregates**: Ensure TSV export includes aggregate rows
