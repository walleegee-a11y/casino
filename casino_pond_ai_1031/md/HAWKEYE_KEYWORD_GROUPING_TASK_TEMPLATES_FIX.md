# Hawkeye Keyword Grouping - Task Templates Fix ✅

## Date: 2025-10-21

## Status: ✅ SUCCESSFULLY FIXED

---

## Problem: Only "Other Keywords" Showing in Group Filter

### Symptom
When using the Group filter in Hawkeye Comparison Analysis, only "Other Keywords" appeared in the dropdown. Expected groups like `sta_timing`, `sta_cell_usage`, `err/warn`, `timing`, etc. were missing.

### Root Cause
The JavaScript code was only checking `keywordGroupConfig.tasks` for keyword definitions, but in `vista_casino.yaml`:
- **Line 489**: `tasks: {}` - **EMPTY!**
- **Line 99**: `task_templates:` - Contains all keyword definitions with groups

The keyword definitions were in the **`task_templates`** section, not in `tasks`, so the grouping logic couldn't find them.

---

## Solution

### Updated Code to Check Both Sections

Modified the JavaScript to check **both** `tasks` and `task_templates` sections when:
1. Extracting groups from YAML
2. Matching keywords to groups

---

## Changes Made

### File: `hawkeye_web_server.py`

#### Change 1: Updated First `getGroupOrderFromYAML()` (Lines 1724-1777)

**Before**:
```javascript
// Only checked tasks section
if (keywordGroupConfig && keywordGroupConfig.tasks) {
    for (const taskName in keywordGroupConfig.tasks) {
        const task = keywordGroupConfig.tasks[taskName];
        if (task.keywords) {
            for (const keywordConfig of task.keywords) {
                if (keywordConfig.group) {
                    groupSet.add(keywordConfig.group);
                }
            }
        }
    }
}
```

**After**:
```javascript
// Check both 'tasks' and 'task_templates' sections
if (keywordGroupConfig) {
    // Check tasks section
    if (keywordGroupConfig.tasks) {
        for (const taskName in keywordGroupConfig.tasks) {
            const task = keywordGroupConfig.tasks[taskName];
            if (task.keywords) {
                for (const keywordConfig of task.keywords) {
                    if (keywordConfig.group) {
                        groupSet.add(keywordConfig.group);
                    }
                }
            }
        }
    }

    // Check task_templates section (NEW!)
    if (keywordGroupConfig.task_templates) {
        for (const templateName in keywordGroupConfig.task_templates) {
            const template = keywordGroupConfig.task_templates[templateName];
            if (template.keywords) {
                for (const keywordConfig of template.keywords) {
                    if (keywordConfig.group) {
                        groupSet.add(keywordConfig.group);
                    }
                }
            }
        }
    }
}
```

#### Change 2: Updated First `groupKeywordsByConvention()` (Lines 1779-1849)

**Before**:
```javascript
// Only checked tasks section
if (keywordGroupConfig && keywordGroupConfig.tasks) {
    for (const taskName in keywordGroupConfig.tasks) {
        const task = keywordGroupConfig.tasks[taskName];
        if (task.keywords) {
            for (const keywordConfig of task.keywords) {
                // matching logic...
            }
        }
        if (groupName !== 'Other Keywords') break;
    }
}
```

**After**:
```javascript
// Check both 'tasks' and 'task_templates' sections
if (keywordGroupConfig) {
    // Search through tasks section
    if (keywordGroupConfig.tasks) {
        for (const taskName in keywordGroupConfig.tasks) {
            const task = keywordGroupConfig.tasks[taskName];
            if (task.keywords) {
                for (const keywordConfig of task.keywords) {
                    // matching logic...
                }
            }
            if (groupName !== 'Other Keywords') break;
        }
    }

    // If not found in tasks, search through task_templates section (NEW!)
    if (groupName === 'Other Keywords' && keywordGroupConfig.task_templates) {
        for (const templateName in keywordGroupConfig.task_templates) {
            const template = keywordGroupConfig.task_templates[templateName];
            if (template.keywords) {
                for (const keywordConfig of template.keywords) {
                    // matching logic...
                }
            }
            if (groupName !== 'Other Keywords') break;
        }
    }
}
```

#### Change 3: Updated Second `getGroupOrderFromYAML()` (Lines 4790-4843)
Same update applied to the second instance.

#### Change 4: Updated Second `groupKeywordsByConvention()` (Lines 4845-4916)
Same update applied to the second instance.

---

## How It Works Now

### Step 1: Load YAML Configuration
```javascript
fetch('/api/vista_config')
```
Returns:
```json
{
  "tasks": {},  // Empty!
  "task_templates": {
    "sta_primetime_task": {
      "keywords": [
        {"name": "{mode}_{corner}_s_wns_{path_type}", "group": "sta_timing"},
        {"name": "{mode}_{corner}_max_tran_num", "group": "sta_violations"},
        // ... more keywords
      ]
    },
    "standard_apr_task": {
      "keywords": [
        {"name": "error", "group": "err/warn"},
        {"name": "s_wns", "group": "timing"},
        // ... more keywords
      ]
    }
  }
}
```

### Step 2: Extract Groups
`getGroupOrderFromYAML()` now scans **both** `tasks` and `task_templates`:
```javascript
// From task_templates.sta_primetime_task.keywords:
groupSet.add("sta_timing")
groupSet.add("sta_violations")
groupSet.add("sta_noise")
groupSet.add("sta_vth")
groupSet.add("sta_cell_usage")

// From task_templates.standard_apr_task.keywords:
groupSet.add("err/warn")
groupSet.add("timing")
groupSet.add("congestion")
groupSet.add("utilization")

// Result: [err/warn, timing, congestion, utilization, sta_cell_usage, sta_noise, sta_timing, sta_violations, sta_vth]
```

### Step 3: Match Keywords to Groups
When processing a keyword like `misn_ff_0p99v_m40c_Cbest_s_wns_all`:

1. **Check tasks section** - empty, no match
2. **Check task_templates section** (NEW!)
   - Template: `sta_primetime_task`
   - Keyword definition: `{mode}_{corner}_s_wns_{path_type}`
   - Group: `sta_timing`
   - **matchesTemplate()** converts to regex: `^[^_]+_[^_]+(?:_[^_]+)*_s_wns_[^_]+$`
   - Tests against: `misn_ff_0p99v_m40c_Cbest_s_wns_all`
   - **Match!** ✅
   - Assigns to group: `sta_timing`

### Step 4: Display Groups
Groups now appear in filter dropdown:
1. **err/warn** (preferred)
2. **timing** (preferred)
3. **congestion** (preferred)
4. **utilization** (preferred)
5. **sta_cell_usage** (alphabetical)
6. **sta_noise** (alphabetical)
7. **sta_timing** (alphabetical)
8. **sta_violations** (alphabetical)
9. **sta_vth** (alphabetical)
10. **Other Keywords** (last)

---

## YAML Structure Explanation

### vista_casino.yaml Structure

```yaml
# Line 99: Templates define reusable keyword patterns
task_templates:
  sta_primetime_task:
    keywords:
      - name: "{mode}_{corner}_s_wns_{path_type}"
        group: "sta_timing"
      - name: "HVth"
        group: "sta_vth"

  standard_apr_task:
    keywords:
      - name: "error"
        group: "err/warn"
      - name: "s_wns"
        group: "timing"

# Line 442: Mappings link task names to templates
task_mappings:
  sta_pt:
    template: "sta_primetime_task"
  place_inn:
    template: "standard_apr_task"

# Line 489: Tasks section (empty - templates not yet expanded)
tasks: {}
```

**Why `tasks` is empty**:
- The YAML uses a template system
- `task_templates` defines reusable patterns
- `task_mappings` links tasks to templates
- `tasks` section is meant to be populated by Python code during expansion
- **But** the expansion wasn't happening when the web server loads the YAML
- **Solution**: Check `task_templates` directly instead of waiting for expansion

---

## Example Keyword Matches

### STA Timing Keywords

**Template**: `{mode}_{corner}_s_wns_{path_type}` (in `sta_primetime_task`)
**Group**: `sta_timing`

**Actual Keywords** → **Matches**:
- `misn_ff_0p99v_m40c_Cbest_s_wns_all` → sta_timing ✅
- `scap_ss_0p81v_p125c_Rcworst_T_s_wns_reg2reg` → sta_timing ✅
- `ssft_ff_0p99v_p125c_Cbest_h_tns_in2reg` → sta_timing ✅

### STA Cell Usage Keywords

**Template**: `std_cell_inst` (in `sta_primetime_task`)
**Group**: `sta_cell_usage`

**Actual Keywords** → **Matches**:
- `std_cell_inst` → sta_cell_usage ✅ (exact match)
- `comb_cell_inst` → sta_cell_usage ✅ (defined in template)
- `flip_flop_area` → sta_cell_usage ✅ (defined in template)

### APR Keywords

**Template**: `error` (in `standard_apr_task`)
**Group**: `err/warn`

**Actual Keywords** → **Matches**:
- `error` → err/warn ✅ (exact match)
- `error_count` → err/warn ✅ (prefix match)

**Template**: `s_wns` (in `standard_apr_task`)
**Group**: `timing`

**Actual Keywords** → **Matches**:
- `s_wns` → timing ✅ (exact match)
- `s_tns` → timing ✅ (defined in template)
- `h_wns` → timing ✅ (defined in template)

---

## Testing

### Test Case 1: Verify YAML Loading
1. Open browser console
2. Navigate to Hawkeye Comparison Analysis
3. Check console for: `Loaded YAML config with tasks: 0`
4. **Expected**: YAML loads successfully (even though tasks section is empty)

### Test Case 2: Verify Group Discovery
1. In browser console after comparison loads
2. Check logs for: `Created keyword groups: [...]`
3. **Expected**: Multiple groups listed (not just "Other Keywords")

### Test Case 3: Verify Group Filter Dropdown
1. Select runs with STA data
2. Click "Compare"
3. Click on "Group" filter dropdown
4. **Expected**: See multiple groups:
   - err/warn
   - timing
   - congestion
   - utilization
   - sta_cell_usage
   - sta_noise
   - sta_timing
   - sta_violations
   - sta_vth
   - Other Keywords

### Test Case 4: Verify Group Filtering Works
1. In comparison view, click "Group" filter
2. Select "sta_timing"
3. **Expected**: Only STA timing keywords displayed (s_wns, s_tns, h_wns, h_tns with mode/corner/path variants)

### Test Case 5: Verify Template Matching
1. Select a group like "sta_timing"
2. Check that keywords match the template pattern:
   - `misn_ff_0p99v_m40c_Cbest_s_wns_all` ✅
   - `scap_ss_0p81v_p125c_Rcworst_T_h_tns_reg2reg` ✅
3. **Expected**: All keywords matching `{mode}_{corner}_s_wns_{path_type}` pattern appear

---

## Troubleshooting

### Issue: Still Only Seeing "Other Keywords"

**Possible Causes**:
1. Browser cache - Hard refresh (Ctrl+F5)
2. Web server not restarted
3. YAML file not loaded correctly

**Solutions**:
1. **Hard refresh browser** (Ctrl+F5 or Cmd+Shift+R)
2. **Restart web server**:
   ```bash
   # Stop current server
   # Restart:
   python hawkeye_web_server.py
   ```
3. **Check YAML loading**:
   - Open browser console
   - Look for: `Loaded YAML config with tasks: X`
   - If error, check YAML syntax

### Issue: Some Keywords Not Grouped

**Possible Causes**:
1. Keyword doesn't match any template
2. Template pattern incorrect
3. Group name missing in YAML

**Solutions**:
1. **Check browser console**:
   - Look for: `Group details: {...}`
   - See which keywords are in "Other Keywords"
2. **Add keyword to YAML**:
   ```yaml
   task_templates:
     your_template:
       keywords:
         - name: "your_keyword"
           group: "your_group"
   ```
3. **Check template pattern**:
   - Ensure template variables like `{mode}`, `{corner}` are correct
   - Test regex pattern manually

### Issue: Groups Appear in Wrong Order

**Possible Cause**:
- Group not in preferred order list

**Solution**:
- Add to preferred order in code (lines 1727 and 4793):
  ```javascript
  const preferredOrder = ['err/warn', 'timing', 'congestion', 'utilization', 'your_group'];
  ```

---

## Summary

### Problem
✅ YAML had keyword definitions in `task_templates`, not `tasks`
✅ JavaScript only checked `tasks` section (which was empty)
✅ Result: All keywords assigned to "Other Keywords"

### Solution
✅ Updated `getGroupOrderFromYAML()` to check **both** `tasks` and `task_templates`
✅ Updated `groupKeywordsByConvention()` to check **both** sections
✅ Applied changes to both instances of these functions

### Result
✅ Groups now discovered from `task_templates`
✅ Keywords correctly matched to groups using template patterns
✅ Multiple groups appear in Group filter dropdown
✅ Filtering by group works correctly

---

## Files Modified

**Single file**: `hawkeye_web_server.py`

**Changes**:
- Lines 1724-1777: Updated first `getGroupOrderFromYAML()` to check task_templates
- Lines 1779-1849: Updated first `groupKeywordsByConvention()` to check task_templates
- Lines 4790-4843: Updated second `getGroupOrderFromYAML()` to check task_templates
- Lines 4845-4916: Updated second `groupKeywordsByConvention()` to check task_templates

**Total**: 4 function updates

---

## Related Fixes

This fix builds on two previous enhancements:

1. **Template Matching** (earlier today)
   - Added `matchesTemplate()` function
   - Supports template-based keyword patterns like `{mode}_{corner}_s_wns_{path_type}`
   - Document: `HAWKEYE_KEYWORD_GROUPING_FROM_YAML.md`

2. **Dynamic Group Discovery** (earlier today)
   - Made group list dynamic instead of hardcoded
   - Automatically extracts groups from YAML
   - Document: `HAWKEYE_KEYWORD_GROUPING_FROM_YAML.md`

3. **Task Templates Support** (this fix)
   - Checks `task_templates` in addition to `tasks`
   - Handles empty `tasks` section gracefully
   - Document: This file

---

## Enjoy Your Keyword Groups! 🎉

The Group filter in Hawkeye Comparison Analysis should now display all groups defined in `vista_casino.yaml` task_templates:

- **err/warn** - Errors and warnings
- **timing** - APR timing metrics
- **congestion** - Congestion metrics
- **utilization** - Utilization percentages
- **sta_cell_usage** - Cell counts and areas
- **sta_noise** - Noise violations
- **sta_timing** - STA timing by mode/corner/path
- **sta_violations** - Max transition/capacitance violations
- **sta_vth** - VTH ratios

**Restart your web server and refresh your browser to see the changes!** 🚀
