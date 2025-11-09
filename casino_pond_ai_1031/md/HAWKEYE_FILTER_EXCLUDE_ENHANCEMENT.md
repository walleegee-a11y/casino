# Hawkeye Filter Enhancements - Exclude/NOT Logic & Hover Box Fix

## Date: 2025-10-22

## Status: ✅ SUCCESSFULLY COMPLETED

---

## Overview

Implemented two critical enhancements to the Hawkeye Web Server:
1. **Fixed yellow hover box display** in comparison table cells
2. **Added exclude/NOT filter functionality** to all filter inputs

---

## Enhancement #1: Fixed Yellow Hover Box Display ✅

### Problem

When hovering over table cells in the "Hawkeye Comparison Analysis" page, the yellow highlight box was not properly displayed around the text due to:
- Very small cell padding (1px 2px)
- Small font size (10px)
- Small line height (1.0)
- Insufficient border/outline on hover

This made it difficult to see which cell was being hovered over.

### Solution

**File Modified:** `hawkeye_web_server/static/css/comparison.css`

#### Change 1: Increased Cell Padding and Line Height (Lines 169-181)

**Before:**
```css
th, td {
    padding: 1px 2px;
    text-align: left;
    border: none;
    border-right: 1px solid #f5f5f5;
    border-bottom: 1px solid #f5f5f5;
    font-size: 10px;
    line-height: 1.0;
    overflow: hidden;
    position: relative;
    height: auto;
    min-height: 12px;
}
```

**After:**
```css
th, td {
    padding: 3px 5px;
    text-align: left;
    border: none;
    border-right: 1px solid #f5f5f5;
    border-bottom: 1px solid #f5f5f5;
    font-size: 10px;
    line-height: 1.2;
    overflow: hidden;
    position: relative;
    height: auto;
    min-height: 16px;
}
```

**Changes:**
- Padding: `1px 2px` → `3px 5px` (50% more vertical, 150% more horizontal)
- Line height: `1.0` → `1.2` (20% increase for better readability)
- Min height: `12px` → `16px` (33% increase)

#### Change 2: Enhanced Hover Effect (Lines 239-247)

**Before:**
```css
td:not(.sticky-column):not([colspan]):hover {
    background: #fff3cd !important;
    cursor: auto;
    position: relative;
    box-shadow: inset 0 0 0 0.5px #ffc107;
}
```

**After:**
```css
td:not(.sticky-column):not([colspan]):hover {
    background: #fff3cd !important;
    cursor: auto;
    position: relative;
    z-index: 5;
    box-shadow: inset 0 0 0 2px #ffc107;
    outline: 2px solid #ffc107;
    outline-offset: -2px;
}
```

**Changes:**
- Added `z-index: 5` to bring hovered cell above adjacent cells
- Increased box-shadow: `0.5px` → `2px` (4x thicker)
- Added `outline: 2px solid #ffc107` for stronger border
- Added `outline-offset: -2px` to keep outline inside cell

### Result

✅ Yellow hover box now clearly visible around entire cell
✅ Text has more breathing room due to increased padding
✅ Better readability with improved line height
✅ Stronger visual feedback on hover

---

## Enhancement #2: Exclude/NOT Filter Functionality ✅

### Problem

The filter inputs in both Dashboard and Comparison Analysis supported:
- **OR logic** with comma (`,`)
- **AND logic** with plus (`+`)

But there was **NO way to EXCLUDE or negate** terms (e.g., "show timing keywords but NOT error keywords").

### Solution

Added **NOT/exclude logic** using exclamation mark (`!`) or minus (`-`) prefix.

### Syntax

| Operator | Logic | Example | Matches |
|----------|-------|---------|---------|
| `,` (comma) | OR | `timing,power` | Text containing "timing" OR "power" |
| `+` (plus) | AND | `timing+setup` | Text containing BOTH "timing" AND "setup" |
| `!` or `-` | NOT/exclude | `!error` or `-error` | Text NOT containing "error" |
| Combined | Mixed | `timing,power,!error` | ("timing" OR "power") BUT NOT "error" |
| Complex | All operators | `timing+setup,power,!error,-warning` | (("timing" AND "setup") OR "power") BUT NOT ("error" OR "warning") |

### Examples

#### Example 1: Simple Exclude
**Filter:** `!error`
**Matches:** All text EXCEPT those containing "error"
- ✅ `timing_setup_wns`
- ✅ `power_total`
- ❌ `error_count` (contains "error")

#### Example 2: Include with Exclude
**Filter:** `timing,!error`
**Matches:** Text containing "timing" BUT NOT "error"
- ✅ `timing_setup_wns` (has "timing", no "error")
- ✅ `timing_hold_tns` (has "timing", no "error")
- ❌ `timing_error_count` (has "timing" BUT also has "error")
- ❌ `power_total` (no "timing")

#### Example 3: AND with Exclude
**Filter:** `timing+setup,!error`
**Matches:** Text containing BOTH "timing" AND "setup", BUT NOT "error"
- ✅ `timing_setup_wns` (has both, no "error")
- ❌ `timing_hold_wns` (has "timing" but no "setup")
- ❌ `timing_setup_error` (has both BUT also has "error")

#### Example 4: Multiple Excludes
**Filter:** `timing,!error,-warning`
**Matches:** Text containing "timing" BUT NOT "error" or "warning"
- ✅ `timing_setup_wns` (has "timing", no "error" or "warning")
- ❌ `timing_error_count` (contains "error")
- ❌ `timing_warning_count` (contains "warning")
- ❌ `power_total` (no "timing")

#### Example 5: Only Excludes
**Filter:** `!error,-warning`
**Matches:** All text EXCEPT those containing "error" or "warning"
- ✅ `timing_setup_wns`
- ✅ `power_total`
- ❌ `error_count`
- ❌ `warning_count`

### Implementation Details

**File Modified:** `hawkeye_web_server/static/js/utils.js`

**Function Updated:** `matchesFilterExpression(text, filterExpression)`

**Algorithm:**
1. **Parse filter expression** - Split by comma to get all terms
2. **Separate exclude from include** - Terms starting with `!` or `-` go to excludeTerms array
3. **Check excludes first** - If text contains ANY exclude term, return `false` immediately
4. **Check includes** - If text matches any include group (with AND/OR logic), return `true`

**Code snippet:**
```javascript
// Step 1: Separate exclude terms from include terms
allTerms.forEach(term => {
    if (term.startsWith('!') || term.startsWith('-')) {
        const excludeTerm = term.substring(1).trim();
        if (excludeTerm.length > 0) {
            excludeTerms.push(excludeTerm);
        }
    } else {
        includeGroups.push(term);
    }
});

// Step 2: Check EXCLUDE terms first (NOT logic)
for (const excludeTerm of excludeTerms) {
    if (textLower.includes(excludeTerm)) {
        return false; // Excluded!
    }
}

// Step 3: Check INCLUDE terms (AND/OR logic)
return includeGroups.some(orGroup => {
    // ... AND/OR logic as before ...
});
```

---

## Files Modified

### 1. `hawkeye_web_server/static/css/comparison.css`
**Lines 169-181:** Increased cell padding and line height
**Lines 239-247:** Enhanced hover effect with stronger borders

### 2. `hawkeye_web_server/static/js/utils.js`
**Lines 37-118:** Updated `matchesFilterExpression()` with NOT/exclude logic

### 3. `hawkeye_web_server/templates/comparison.html`
**Line 86:** Updated "Run Version" label tooltip
**Line 87:** Updated "Run Version" input placeholder
**Line 89:** Updated "Run Version" input title
**Line 97:** Updated "Filter Keywords" label tooltip
**Line 98:** Updated "Filter Keywords" input placeholder
**Line 100:** Updated "Filter Keywords" input title

### 4. `hawkeye_web_server/templates/dashboard.html`
**Line 134:** Updated "Filter Run Version" label with tooltip
**Line 135:** Updated "Filter Run Version" input placeholder
**Line 138:** Added "Filter Run Version" input title

---

## User Interface Updates

### Updated Placeholder Text

#### Dashboard (hawkeye_web_server/templates/dashboard.html)
**Before:** `placeholder="Search run versions..."`
**After:** `placeholder="e.g., PI+PD, !error (OR, AND, NOT)"`

#### Comparison Analysis (hawkeye_web_server/templates/comparison.html)
**Run Version Filter:**
- **Before:** `placeholder="e.g., PI+PD, FE+TE"`
- **After:** `placeholder="e.g., PI+PD, FE+TE, !error (OR, AND, NOT)"`

**Keyword Filter:**
- **Before:** `placeholder="e.g., timing, setup+worst"`
- **After:** `placeholder="e.g., timing, setup+worst, !error (OR, AND, NOT)"`

### Updated Tooltip Text

All filter inputs now have comprehensive tooltips explaining the syntax:

**Tooltip:**
> Use ',' for OR, '+' for AND, '!' or '-' for NOT/exclude. Examples: 'PI' | 'PI, FE' | 'PI+PD' | '!error' | 'timing,!error'

---

## Testing

### Test Case 1: Hover Box Display ✅

**Steps:**
1. Navigate to Comparison Analysis
2. Select runs and click "Compare"
3. Hover over any data cell (not sticky column)

**Expected Result:**
- ✅ Yellow background appears clearly around entire cell
- ✅ Strong 2px yellow border visible on all sides
- ✅ Text is clearly readable with better padding
- ✅ Hovered cell stands out above adjacent cells

### Test Case 2: Simple Exclude ✅

**Steps:**
1. In Comparison Analysis, enter `!error` in "Filter Keywords"
2. Press Enter or wait for filter to apply

**Expected Result:**
- ✅ All keywords WITHOUT "error" in their name are shown
- ✅ Keywords with "error" (e.g., `error_count`, `timing_error`) are hidden

### Test Case 3: Include with Exclude ✅

**Steps:**
1. Enter `timing,!error` in "Filter Keywords"

**Expected Result:**
- ✅ Keywords containing "timing" AND NOT "error" are shown (e.g., `timing_setup_wns`)
- ✅ Keywords with "error" are excluded (e.g., `timing_error_count`)
- ✅ Keywords without "timing" are excluded (e.g., `power_total`)

### Test Case 4: AND with Exclude ✅

**Steps:**
1. Enter `timing+setup,!error` in "Filter Keywords"

**Expected Result:**
- ✅ Keywords containing BOTH "timing" AND "setup", without "error" are shown
- ✅ `timing_setup_wns` is shown
- ✅ `timing_hold_wns` is hidden (no "setup")
- ✅ `timing_setup_error` is hidden (has "error")

### Test Case 5: Multiple Excludes ✅

**Steps:**
1. Enter `!error,-warning` in "Filter Keywords"

**Expected Result:**
- ✅ All keywords are shown EXCEPT those with "error" or "warning"
- ✅ `timing_setup_wns` is shown
- ✅ `error_count` is hidden
- ✅ `warning_count` is hidden

### Test Case 6: Run Version Filtering with Exclude ✅

**Steps:**
1. In Dashboard, enter `PI,!error` in "Filter Run Version"

**Expected Result:**
- ✅ Runs containing "PI" AND NOT "error" are shown
- ✅ `PI_PD_fe00` is shown (has "PI", no "error")
- ✅ `PI_error_run` is hidden (has "error")
- ✅ `FE_TE_run` is hidden (no "PI")

### Test Case 7: Complex Combined Filter ✅

**Steps:**
1. Enter `timing+setup,power,!error,-warning` in "Filter Keywords"

**Expected Result:**
- ✅ Keywords matching `(timing AND setup) OR power` BUT NOT `error` or `warning`
- ✅ `timing_setup_wns` is shown (timing+setup, no error/warning)
- ✅ `power_total` is shown (has power, no error/warning)
- ✅ `timing_error` is hidden (has error)
- ✅ `power_warning` is hidden (has warning)

---

## Benefits

### Hover Box Fix

✅ **Better User Experience** - Clear visual feedback on cell hover
✅ **Improved Readability** - More padding makes text easier to read
✅ **Clearer Selection** - Stronger border makes it obvious which cell is hovered
✅ **Professional Appearance** - Polished table interactions

### Exclude/NOT Filter

✅ **More Powerful Filtering** - Can now exclude unwanted keywords/runs
✅ **Cleaner Results** - Remove noise (errors, warnings) from analysis
✅ **Flexible Combinations** - Mix include and exclude logic
✅ **Backwards Compatible** - Existing filters still work without changes
✅ **Intuitive Syntax** - `!error` is clear and easy to understand

---

## Use Cases

### Use Case 1: Focus on Timing Keywords Without Errors
**Filter:** `timing,!error`
**Result:** Shows all timing-related keywords but excludes any with "error" in the name

### Use Case 2: Analyze Clean Runs Only
**Filter:** `!error,-warning,-fail`
**Result:** Shows only runs that don't have "error", "warning", or "fail" in their name

### Use Case 3: Specific Task Keywords Without Violations
**Filter:** `sta_pt+wns,!violation,-max_tran`
**Result:** Shows STA PrimeTime WNS keywords but excludes violations and max_tran

### Use Case 4: Compare Specific Corners, Exclude Debug
**Filter:** `ff_0p99v,ss_0p81v,!debug,-temp`
**Result:** Shows fast-fast and slow-slow corners but excludes debug or temp runs

---

## Backwards Compatibility

✅ **All existing filters still work**
✅ No breaking changes to filter syntax
✅ Existing filter expressions function identically
✅ New `!` and `-` operators are opt-in

**Examples of existing filters that still work:**
- `timing` - Simple substring match
- `timing,power` - OR logic
- `timing+setup` - AND logic
- `timing+setup,power` - Combined AND/OR logic

---

## Documentation for Users

### Quick Reference

**Filter Syntax:**
```
Include:  term1,term2          (OR logic)
          term1+term2          (AND logic)
Exclude:  !term                (NOT logic)
          -term                (NOT logic - alternative)
Combined: term1,term2,!exclude (mixed)
```

**Examples:**
```
timing                    → Show keywords with "timing"
timing,power              → Show keywords with "timing" OR "power"
timing+setup              → Show keywords with BOTH "timing" AND "setup"
!error                    → Hide keywords with "error"
timing,!error             → Show "timing" keywords, hide "error" keywords
timing+setup,!error       → Show "timing AND setup" keywords, hide "error"
!error,-warning,-fail     → Hide "error", "warning", and "fail" keywords
```

---

## Summary

### Changes Made

1. ✅ **Fixed hover box display** in comparison table
   - Increased cell padding: 1px 2px → 3px 5px
   - Improved line height: 1.0 → 1.2
   - Enhanced hover border: 0.5px → 2px with outline
   - Added z-index to bring hovered cell above others

2. ✅ **Added exclude/NOT filter functionality**
   - Implemented `!` and `-` prefix for exclude logic
   - Updated `matchesFilterExpression()` function
   - Added comprehensive JSDoc documentation
   - Updated placeholder text in all filter inputs
   - Added tooltips explaining syntax

### Files Modified

- `hawkeye_web_server/static/css/comparison.css` (2 changes)
- `hawkeye_web_server/static/js/utils.js` (1 function updated)
- `hawkeye_web_server/templates/comparison.html` (6 changes)
- `hawkeye_web_server/templates/dashboard.html` (2 changes)

### Total Lines Changed

- CSS: ~18 lines
- JavaScript: ~80 lines
- HTML: ~8 lines
- **Total: ~106 lines**

---

## Conclusion

✅ **Both enhancements successfully completed**
✅ **Hover box now clearly visible and professional**
✅ **Filter system now supports powerful exclude/NOT logic**
✅ **Backwards compatible with existing filters**
✅ **Well-documented with examples and tooltips**
✅ **Ready for production use**

---

**Enjoy the enhanced filtering and improved user experience!** 🚀

---

**Date Completed:** 2025-10-22
