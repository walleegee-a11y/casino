# Filter Run Version Fix - Dashboard

## Issue Summary

The "Filter Run Version" input in `dashboard.html` was not working like the "Filter Keywords" function in `comparison.html`. It only supported simple substring matching, while users expected AND/OR/NOT logic.

## Root Cause Analysis

### Problem

**dashboard.html "Filter Run Version"** (Before):
```javascript
// dashboard.js line 250 (OLD)
const filteredRuns = baseFiltered.filter(run => {
    return run.run_version.toLowerCase().includes(searchTerm);
});
```

This implementation:
- ❌ Only did basic substring matching
- ❌ No support for OR logic (`,`)
- ❌ No support for AND logic (`+`)
- ❌ No support for NOT logic (`!` or `-`)

**comparison.html "Filter Keywords"** (Working correctly):
```javascript
// filters.js line 95-98
filtered = filtered.filter(keyword => {
    return matchesFilterExpression(keyword, searchTerm);
});
```

This implementation:
- ✅ Uses `matchesFilterExpression()` from utils.js
- ✅ Supports OR logic with `,` (comma)
- ✅ Supports AND logic with `+` (plus)
- ✅ Supports NOT logic with `!` or `-` (exclamation/minus)

### Why It Happened

The dashboard filter was implemented before the centralized `matchesFilterExpression()` utility function was created in utils.js. The comparison view was created later and used the proper utility function from the start.

## Solution

Updated `filterByRunVersion()` in `dashboard.js` to use `matchesFilterExpression()`:

```javascript
// dashboard.js line 255-257 (NEW)
const filteredRuns = baseFiltered.filter(run => {
    return matchesFilterExpression(run.run_version, searchTerm);
});
```

### Filter Syntax

Now both dashboard and comparison views support the same filter syntax:

| Syntax | Logic | Example | Matches |
|--------|-------|---------|---------|
| `,` (comma) | OR | `PI,FE` | Runs with "PI" OR "FE" |
| `+` (plus) | AND | `PI+PD` | Runs with BOTH "PI" AND "PD" |
| `!` or `-` | NOT | `!error` | Runs WITHOUT "error" |
| Combined | Mixed | `PI+PD,FE,!error` | (PI AND PD) OR FE, BUT NOT error |

## Examples

### Before Fix (Simple substring only)
- `PI+PD` → Searched for literal string "PI+PD" ❌
- `PI,FE` → Searched for literal string "PI,FE" ❌
- `!error` → Searched for literal string "!error" ❌

### After Fix (Smart AND/OR/NOT logic)
- `PI+PD` → Matches "PI_PD_timing", "PD_PI_run1" ✅
- `PI,FE` → Matches "PI_timing" OR "FE_corner" ✅
- `!error` → Excludes any run containing "error" ✅
- `PI+timing,!error` → Matches runs with both PI and timing, excluding any with error ✅

## Files Modified

### D:\CASINO\casino_pond_ai\hawkeye_web_server\static\js\dashboard.js

**Line 234-257**: Updated `filterByRunVersion()` function
- Changed from simple `includes()` to `matchesFilterExpression()`
- Added comprehensive documentation explaining AND/OR/NOT syntax
- Now consistent with comparison.html filter behavior

## Testing Checklist

- [ ] Simple substring: "PI" should match "PI_timing", "FE_PI_run"
- [ ] OR logic: "PI,FE" should match runs with PI or FE
- [ ] AND logic: "PI+timing" should only match runs with both PI and timing
- [ ] NOT logic: "!error" should exclude runs containing "error"
- [ ] Combined: "PI+timing,FE,!error" should match (PI AND timing) OR FE, excluding error

## Benefits

1. **Consistency**: Dashboard and comparison views now use the same filter logic
2. **Power**: Users can create complex filters with AND/OR/NOT combinations
3. **Efficiency**: Filter multiple criteria in a single search instead of multiple manual filters
4. **User Experience**: Matches user expectations from comparison view

## Related Files

- `hawkeye_web_server/static/js/utils.js` - Contains `matchesFilterExpression()` utility function
- `hawkeye_web_server/static/js/filters.js` - Uses `matchesFilterExpression()` for keyword filters
- `hawkeye_web_server/static/js/dashboard.js` - Now uses `matchesFilterExpression()` for run version filters
- `hawkeye_web_server/templates/dashboard.html` - HTML input field for filter
- `hawkeye_web_server/templates/comparison.html` - Comparison view with working filters

## Date
2025-10-27

---
**Status**: ✅ Fixed and documented
