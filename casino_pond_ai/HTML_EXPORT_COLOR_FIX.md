# HTML Export Color Scheme Fix

## Issue Found

**Mismatch between GUI colors and HTML export colors**

The HTML export feature was using the **old pastel color scheme** while the GUI had been updated to use **classical professional colors**. This caused inconsistency between:
- What users see in the application
- What appears in exported HTML reports

---

## The Problem

### GUI Colors (Classical - Updated Earlier)

**Status Colors:**
```python
STATUS_COLORS = {
    "Open": QColor("#FFF4E6"),          # Light cream
    "In Progress": QColor("#E3F2FD"),   # Light blue
    "Resolved": QColor("#E8F5E9"),      # Light green
    "Closed": QColor("#F5F5F5")         # Light gray
}
```

**Severity Colors:**
```python
SEVERITY_COLORS = {
    "Critical": QColor("#D32F2F"),      # Deep Red
    "Major": QColor("#F57C00"),         # Deep Orange
    "Minor": QColor("#FBC02D"),         # Muted Yellow
    "Enhancement": QColor("#388E3C"),   # Forest Green
    "Info": QColor("#E0E0E0")           # Medium Gray
}
```

### HTML Export Colors (Pastel - OLD)

**Status Colors (BEFORE):**
```css
.status-open { background-color: #f8d7da; }           /* Pink-ish */
.status-in-progress { background-color: #fff3cd; }    /* Yellow */
.status-resolved { background-color: #d4edda; }       /* Light Green */
.status-closed { background-color: #d1ecf1; }         /* Light Blue */
```

**Severity Colors (BEFORE):**
```css
.severity-critical { background-color: #dc3545; }     /* Bright Red */
.severity-major { background-color: #fd7e14; }        /* Bright Orange */
.severity-minor { background-color: #ffc107; }        /* Bright Yellow */
.severity-enhancement { background-color: #28a745; }  /* Bright Green */
.severity-info { background-color: #e9ecef; }         /* Very Light Gray */
```

---

## The Fix

Updated HTML export CSS in `ftrack_casino/gui.py` (Lines 1981-1989) to match the classical color scheme.

### Status Colors (AFTER)

```css
.status-open { background-color: #FFF4E6; }           /* Light Cream */
.status-in-progress { background-color: #E3F2FD; }    /* Light Blue */
.status-resolved { background-color: #E8F5E9; }       /* Light Green */
.status-closed { background-color: #F5F5F5; }         /* Light Gray */
```

### Severity Colors (AFTER)

```css
.severity-critical { background-color: #D32F2F; }     /* Deep Red */
.severity-major { background-color: #F57C00; }        /* Deep Orange */
.severity-minor { background-color: #FBC02D; }        /* Muted Yellow */
.severity-enhancement { background-color: #388E3C; }  /* Forest Green */
.severity-info { background-color: #E0E0E0; }         /* Medium Gray */
```

---

## Comparison

### Before Fix

```
┌────────────────────────────────────────────┐
│ GUI:                                       │
│ Status: Classical (Cream, Blue, Green)     │
│ Severity: Classical (Deep Red, Orange)     │
├────────────────────────────────────────────┤
│ HTML Export:                               │
│ Status: Pastel (Pink, Yellow, Light Blue)  │ ← MISMATCH!
│ Severity: Bright (Bright Red, Orange)      │ ← MISMATCH!
└────────────────────────────────────────────┘
```

### After Fix

```
┌────────────────────────────────────────────┐
│ GUI:                                       │
│ Status: Classical (Cream, Blue, Green)     │
│ Severity: Classical (Deep Red, Orange)     │
├────────────────────────────────────────────┤
│ HTML Export:                               │
│ Status: Classical (Cream, Blue, Green)     │ ✓ MATCH!
│ Severity: Classical (Deep Red, Orange)     │ ✓ MATCH!
└────────────────────────────────────────────┘
```

---

## Impact

### What Changed

**File Modified:** `ftrack_casino/gui.py` (Lines 1981-1989)

**Lines Changed:** 9 CSS rules (4 status + 5 severity)

### Benefits

1. **Consistency**: HTML exports now match GUI appearance
2. **Professionalism**: Exported reports use classical colors
3. **Branding**: Unified color scheme across all outputs
4. **Documentation**: Screenshots and exports look identical
5. **User Experience**: No confusion between GUI and reports

---

## Testing

To verify the fix works:

1. **Create test issues** with different statuses and severities
2. **Export to HTML** (📄 Export HTML button or context menu)
3. **Compare colors** in HTML report with GUI display
4. **Verify** all status and severity colors match exactly

### Expected Results

| Element | GUI Color | HTML Color | Match |
|---------|-----------|------------|-------|
| **Status: Open** | #FFF4E6 | #FFF4E6 | ✅ |
| **Status: In Progress** | #E3F2FD | #E3F2FD | ✅ |
| **Status: Resolved** | #E8F5E9 | #E8F5E9 | ✅ |
| **Status: Closed** | #F5F5F5 | #F5F5F5 | ✅ |
| **Severity: Critical** | #D32F2F | #D32F2F | ✅ |
| **Severity: Major** | #F57C00 | #F57C00 | ✅ |
| **Severity: Minor** | #FBC02D | #FBC02D | ✅ |
| **Severity: Enhancement** | #388E3C | #388E3C | ✅ |
| **Severity: Info** | #E0E0E0 | #E0E0E0 | ✅ |

---

## Technical Details

### Location in Code

**File:** `ftrack_casino/gui.py`

**Function:** `_export_html()` method

**Lines:** 1981-1989 (HTML CSS styling)

### CSS Implementation

The HTML export uses inline CSS in the `<style>` tag within the generated HTML file. The CSS classes are applied to table cells based on status and severity values:

```html
<td class="status-{status.lower().replace(' ', '-')}">{status}</td>
<td class="severity-{severity.lower()}">{severity}</td>
```

---

## Related Changes

This fix completes the classical color scheme update that was previously applied to:

1. ✅ `BUTTON_STYLES` dictionary (gui.py)
2. ✅ `STATUS_COLORS` dictionary (gui.py)
3. ✅ `SEVERITY_COLORS` dictionary (gui.py)
4. ✅ `LIGHT_BUTTON_STYLES` (themes.py)
5. ✅ `DARK_BUTTON_STYLES` (themes.py)
6. ✅ Table styling (get_table_style in themes.py)
7. ✅ **HTML export CSS** (NOW FIXED)

---

## Summary

**Issue:** HTML exports used old pastel colors while GUI used new classical colors

**Root Cause:** HTML export CSS wasn't updated during the color scheme migration

**Solution:** Updated 9 CSS rules in the HTML export template to match classical scheme

**Result:** Perfect consistency between GUI and HTML exports

---

*Fix Applied: 2025-01-28*
*FastTrack Version: 2.0*
*File Modified: ftrack_casino/gui.py*
*Lines Changed: 1981-1989*
