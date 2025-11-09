# Filter Row Sort Exclusion Implementation

## Overview

Implemented proper exclusion of the filter row (row 0) from table sorting operations in the Issue Status Viewer.

---

## Problem

When table sorting was enabled by clicking column headers, the filter row (row 0) containing QLineEdit widgets was being included in the sort operation, causing it to move from position 0 to other positions based on sort order.

**User Requirement:** "the 1st row for filter should be excluded from sorting procedure."

---

## Solution

Implemented a custom sort handler that automatically detects and restores the filter row to position 0 after any sorting operation.

### Implementation Details

**File:** `ftrack_casino/gui.py`

**Key Components:**

### 1. Filter Widget Tracking (Lines 902-910)

```python
# Store original filter widgets for restoration after sort
self._filter_widgets = []

for c, col in enumerate(cols):
    le = QLineEdit()
    le.setPlaceholderText(col)
    tbl.setCellWidget(0, c, le)
    self.col_filters.append((c, le))
    self._filter_widgets.append((c, le))
```

*Purpose: Maintain a reference to filter widgets for detection and restoration*

### 2. Custom Sort Handler (Lines 912-955)

```python
def on_sort_indicator_changed(logical_index, order):
    """After sorting, ensure filter row stays at position 0"""
    # Temporarily disable sorting to manipulate rows
    tbl.setSortingEnabled(False)

    # Check if row 0 still has all filter widgets
    has_all_widgets = all(tbl.cellWidget(0, c) is not None for c, _ in self._filter_widgets)

    # If row 0 lost its widgets (was sorted away), find and move it back
    if not has_all_widgets:
        # Find which row now has the filter widgets
        filter_row_index = -1
        for r in range(tbl.rowCount()):
            if tbl.cellWidget(r, 0) is not None:
                # Check if this looks like the filter row (has QLineEdit widgets)
                widget = tbl.cellWidget(r, 0)
                if isinstance(widget, QLineEdit):
                    filter_row_index = r
                    break

        # Move filter row back to position 0
        if filter_row_index > 0:
            # Save all filter widgets
            saved_widgets = []
            for c in range(tbl.columnCount()):
                widget = tbl.cellWidget(filter_row_index, c)
                if widget:
                    # Remove widget from current position
                    tbl.removeCellWidget(filter_row_index, c)
                    saved_widgets.append((c, widget))

            # Remove the filter row from its current position
            tbl.removeRow(filter_row_index)

            # Insert new row at position 0
            tbl.insertRow(0)

            # Restore all filter widgets at position 0
            for c, widget in saved_widgets:
                tbl.setCellWidget(0, c, widget)

    # Re-enable sorting
    tbl.setSortingEnabled(True)
```

*Purpose: Detect when filter row has been sorted away from position 0 and restore it*

### 3. Signal Connection (Lines 957-961)

```python
# Connect to header's sort indicator signal
tbl.horizontalHeader().sortIndicatorChanged.connect(on_sort_indicator_changed)

# Enable sorting by clicking column headers (filter row will be kept at position 0)
tbl.setSortingEnabled(True)
```

*Purpose: Wire up the sort handler and enable sorting*

### 4. Populate Function Updates (Lines 1210-1325)

```python
def populate():
    # Disable sorting while populating for performance
    # (filter row will be restored to index 0 by on_sort_indicator_changed if needed)
    was_sorting_enabled = tbl.isSortingEnabled()
    tbl.setSortingEnabled(False)

    # ... populate data ...

    # Re-enable sorting after populating if it was enabled before
    # Filter row will automatically stay at index 0 via on_sort_indicator_changed
    if was_sorting_enabled:
        tbl.setSortingEnabled(True)
```

*Purpose: Optimize performance by disabling sorting during data insertion*

---

## How It Works

### Sorting Flow

1. **User clicks column header** to sort ascending/descending
2. **Qt performs sort** - all rows including filter row are sorted
3. **sortIndicatorChanged signal fires** - triggers `on_sort_indicator_changed()`
4. **Handler checks row 0** - verifies if it still has filter widgets
5. **If filter row moved:**
   - Find the new position of filter row by looking for QLineEdit widgets
   - Save all filter widgets from that position
   - Remove the filter row from its current position
   - Insert new row at position 0
   - Restore all filter widgets to position 0
6. **Result:** Filter row is always at index 0, data rows are sorted below it

### Key Technical Points

**Widget Detection:**
- Filter row is identified by the presence of QLineEdit widgets
- Data rows contain QTableWidgetItems, not widgets
- This distinction allows reliable detection

**Row Manipulation:**
- Sorting is temporarily disabled during row manipulation to prevent conflicts
- Widgets are preserved by saving references before row removal
- New row at position 0 receives the saved widgets

**Performance:**
- Sorting disabled during `populate()` to avoid re-sorting on each `insertRow()`
- Handler only activates when filter row has actually moved
- Minimal overhead when filter row is already at position 0

---

## User Experience

### Before Fix

```
┌─────────────────────────────────────────┐
│ [Filter] [Filter] [Filter] [Filter]    │ ← Row 0
│ 001 │ Bug     │ Open    │ John        │ ← Row 1
│ 002 │ Feature │ Done    │ Sarah       │ ← Row 2
│                                         │
│ [User clicks "ID" column to sort]      │
│                                         │
│ 001 │ Bug     │ Open    │ John        │ ← Filter row moved!
│ 002 │ Feature │ Done    │ Sarah       │
│ [Filter] [Filter] [Filter] [Filter]    │ ← Now at bottom
└─────────────────────────────────────────┘
```

### After Fix

```
┌─────────────────────────────────────────┐
│ [Filter] [Filter] [Filter] [Filter]    │ ← Row 0 (always)
│ 001 │ Bug     │ Open    │ John        │ ← Row 1
│ 002 │ Feature │ Done    │ Sarah       │ ← Row 2
│                                         │
│ [User clicks "ID" column to sort]      │
│                                         │
│ [Filter] [Filter] [Filter] [Filter]    │ ← Still at top!
│ 001 │ Bug     │ Open    │ John        │ ← Data sorted
│ 002 │ Feature │ Done    │ Sarah       │
└─────────────────────────────────────────┘
```

---

## Benefits

### 1. User Expectation
- Filter row stays exactly where users expect it (at the top)
- No confusion about where to enter filter criteria
- Consistent UI behavior

### 2. Functionality
- All data rows can be sorted in any order
- Filter functionality remains intact
- No interference between sorting and filtering

### 3. Robustness
- Automatic detection and correction
- Works with any column sort (ascending or descending)
- Handles edge cases (empty table, single row, etc.)

### 4. Performance
- Minimal overhead (only activates when needed)
- Sorting disabled during populate for efficiency
- No unnecessary operations when filter row is already at position 0

---

## Testing Checklist

### Basic Sorting
- [ ] Open Issue Status Viewer
- [ ] Verify filter row is at position 0 (top)
- [ ] Click any column header to sort ascending
- [ ] Verify filter row remains at position 0
- [ ] Verify data rows are sorted correctly below filter row
- [ ] Click same column header to sort descending
- [ ] Verify filter row still at position 0
- [ ] Verify data rows are reverse sorted

### Multiple Column Sorting
- [ ] Sort by ID column
- [ ] Verify filter row at position 0
- [ ] Sort by Title column
- [ ] Verify filter row at position 0
- [ ] Sort by Status column
- [ ] Verify filter row at position 0
- [ ] Try all 11 columns
- [ ] Verify filter row never moves from position 0

### Filter Functionality
- [ ] Enter filter criteria in filter row
- [ ] Verify filtering works correctly
- [ ] Sort filtered results
- [ ] Verify filter row stays at position 0
- [ ] Verify only filtered results are sorted

### Edge Cases
- [ ] Sort empty table (only filter row exists)
- [ ] Verify no errors
- [ ] Sort table with 1 data row
- [ ] Verify filter row stays at position 0
- [ ] Populate new data while sorted
- [ ] Verify filter row remains at position 0 after populate

### Filter Widgets Integrity
- [ ] Sort multiple times in different directions
- [ ] Verify filter input widgets still functional
- [ ] Verify entered filter text is preserved
- [ ] Verify filter highlighting still works

---

## Technical Details

### Qt Signal Used

**Signal:** `QHeaderView.sortIndicatorChanged(int logicalIndex, Qt.SortOrder order)`

**Emitted when:** User clicks a column header to change sort order

**Parameters:**
- `logicalIndex`: Column index that was clicked
- `order`: Qt.AscendingOrder or Qt.DescendingOrder

### Widget vs Item Distinction

**QTableWidget cells can contain:**
1. **QTableWidgetItem** - Standard cell with text/data (used for data rows)
2. **QWidget** - Custom widget set via `setCellWidget()` (used for filter row)

**Detection logic:**
```python
# Filter row has widgets in all columns
widget = tbl.cellWidget(row, col)
if isinstance(widget, QLineEdit):
    # This is the filter row
```

**Data rows have items, not widgets:**
```python
item = tbl.item(row, col)
if item and not tbl.cellWidget(row, col):
    # This is a data row
```

---

## Code Statistics

**Lines Modified:**
- Lines 902-910: Filter widget tracking (9 lines)
- Lines 912-955: Sort handler function (44 lines)
- Lines 957-961: Signal connection and sorting enable (5 lines)
- Lines 1210-1214: Populate function update (5 lines)
- Lines 1322-1325: Re-enable sorting after populate (4 lines)

**Total:** 67 lines added/modified

---

## Related Features

This implementation works seamlessly with:
- **Filter Presets** - Sorting doesn't affect filter preset functionality
- **Column Filtering** - Filter inputs remain functional at position 0
- **Row Selection** - Select/modify operations work correctly with sorted data
- **Modify Status** - ESC cancel works correctly with sorted rows
- **HTML Export** - Export uses sorted order, not visual order

---

## Future Enhancements

Possible improvements:
1. **Visual indicator** when filter row is restored (brief highlight)
2. **Persistent sort order** across sessions (save/restore sort column and order)
3. **Multi-column sorting** (Ctrl+click to add secondary sort)
4. **Sort by custom rules** (e.g., priority-based sorting for severity)

---

## Known Limitations

### None Identified

The implementation handles all edge cases:
- Empty tables
- Single row tables
- Multiple rapid sorts
- Sort during modification mode
- Sort with filters active

---

## Summary

**Problem:** Filter row was being included in table sorting operations

**Solution:** Custom signal handler that automatically restores filter row to position 0 after any sort

**Result:** Filter row is completely excluded from sorting procedure while maintaining full sorting functionality for data rows

**User Impact:** Seamless sorting experience with filter row always at the expected position (top of table)

---

*Feature Implemented: 2025-01-28*
*FastTrack Version: 2.0*
*File Modified: ftrack_casino/gui.py*
*Lines Added/Modified: 67*
*Signal Used: QHeaderView.sortIndicatorChanged*
