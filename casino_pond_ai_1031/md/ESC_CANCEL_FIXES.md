# ESC Cancel and Context Menu Fixes

## Overview

Two issues have been resolved:

1. **Fixed broken Due Date display when ESC cancels Modify Status**
2. **Simplified context menu text markers from [X] to -**

---

## 1. Due Date Display Fix

### Problem

When pressing ESC to cancel Modify Status, the Due Date column displayed incorrectly - showing a broken widget or empty cell instead of the original date/time value.

### Root Cause

**Why it happened:**

During modification mode (`on_modify()`), the Due Date cell (column 6) gets replaced with a **complex QWidget** containing:
- A QVBoxLayout
- A label showing "Original:"
- Date/Time edit widgets (QDateEdit and QTimeEdit)

This is set using `tbl.setCellWidget(r, 6, date_time_widget)`.

When ESC is pressed, the `on_cancel_modify()` function tried to restore the original value using:
```python
tbl.setItem(r, 6, QTableWidgetItem(d.get('due_date', '')))
```

**The bug:** QTableWidget cells can have EITHER:
- A **QTableWidgetItem** (text/data), OR
- A **QWidget** (custom UI component)

But **NOT BOTH**. When a cell has a widget set via `setCellWidget()`, calling `setItem()` doesn't properly replace it - the widget remains and blocks the item from displaying.

### The Fix

**Solution:** Clear all cell widgets BEFORE setting items.

**File:** `ftrack_casino/gui.py` (Lines 1410-1412)

```python
# Clear all cell widgets first (important for Due Date and other complex widgets)
for c in [3, 4, 6, 7, 8, 9]:  # Columns that may have widgets
    tbl.removeCellWidget(r, c)

# Now set the items (this will work correctly)
tbl.setItem(r, 3, QTableWidgetItem(d.get('assignee', '')))
tbl.setItem(r, 4, QTableWidgetItem(d.get('status', '')))
tbl.setItem(r, 6, QTableWidgetItem(d.get('due_date', '')))
# ... etc
```

### Columns Affected

All columns that get replaced with widgets during modification:

| Column | Field | Widget Type |
|--------|-------|-------------|
| 3 | Assignee | QComboBox |
| 4 | Status | QComboBox |
| 6 | Due Date | QWidget (complex layout with QDateEdit + QTimeEdit) |
| 7 | Severity | QComboBox |
| 8 | Stage | QComboBox (editable) |
| 9 | Blocks | QListWidget |

### Technical Details

**QTableWidget cell behavior:**
```python
# Setting a widget
tbl.setCellWidget(row, col, widget)  # Cell shows the widget

# Setting an item (only works if no widget)
tbl.setItem(row, col, item)  # Cell shows text from item

# PROBLEM: If widget exists, setItem() doesn't work properly
tbl.setCellWidget(row, col, widget)  # Widget is displayed
tbl.setItem(row, col, item)          # Item is set BUT NOT VISIBLE (widget blocks it)

# SOLUTION: Remove widget first
tbl.removeCellWidget(row, col)       # Remove widget
tbl.setItem(row, col, item)          # Now item displays correctly
```

### Why Save Changes Works

When you click "Save Changes" (`on_save()`), the function:
1. Reads values from the widgets
2. Saves to YAML files
3. Calls `populate()` which completely rebuilds the table from scratch
4. `populate()` creates fresh QTableWidgetItems for all cells

The complete rebuild naturally removes all widgets and creates new items, which is why saving works fine.

ESC cancel needs to do the same cleanup without rebuilding the entire table.

### Visual Comparison

**Before fix:**
```
┌──────────────────────────────────────────┐
│ ID  │ Due Date                           │
├──────────────────────────────────────────┤
│ 001 │ 2025-01-15 14:30                   │  ← Normal display
│     │ [Modify Status clicked]            │
│ 001 │ Original:                          │  ← Widget with editors
│     │ [2025-01-15] [14:30]               │
│     │ [Press ESC]                        │
│ 001 │ [BROKEN - empty or corrupted]      │  ❌ BUG!
└──────────────────────────────────────────┘
```

**After fix:**
```
┌──────────────────────────────────────────┐
│ ID  │ Due Date                           │
├──────────────────────────────────────────┤
│ 001 │ 2025-01-15 14:30                   │  ← Normal display
│     │ [Modify Status clicked]            │
│ 001 │ Original:                          │  ← Widget with editors
│     │ [2025-01-15] [14:30]               │
│     │ [Press ESC]                        │
│ 001 │ 2025-01-15 14:30                   │  ✓ Restored correctly!
└──────────────────────────────────────────┘
```

---

## 2. Context Menu Text Simplification

### Problem

Context menu used bracket notation like `[*]`, `[S]`, `[A]` which could be confused with keyboard shortcuts (like `[Ctrl+S]`), but these were just text markers.

### Change

Simplified all context menu items to use simple dash prefix `-` for clarity.

**File:** `ftrack_casino/gui.py` (Lines 2219-2228)

**Before:**
```python
modify_action = menu.addAction("[*] Modify Status")
save_action = menu.addAction("[S] Save Changes")
attach_action = menu.addAction("[A] Check Attachments")
delete_action = menu.addAction("[X] Delete Issue")
restore_action = menu.addAction("[R] Restore Issue")
refresh_action = menu.addAction("[F5] Refresh")
export_action = menu.addAction("[H] Export HTML")
```

**After:**
```python
modify_action = menu.addAction("- Modify Status")
save_action = menu.addAction("- Save Changes")
attach_action = menu.addAction("- Check Attachments")
delete_action = menu.addAction("- Delete Issue")
restore_action = menu.addAction("- Restore Issue")
refresh_action = menu.addAction("- Refresh")
export_action = menu.addAction("- Export HTML")
```

### Rationale

**Why dash prefix?**
- **Clarity:** No confusion with keyboard shortcuts
- **Simplicity:** Standard menu item marker
- **Consistency:** Common pattern in text-based interfaces
- **Clean:** Minimal visual noise

**The bracket notation was misleading because:**
- `[S]` looks like it might be a shortcut key (but it's not)
- `[F5]` looks like F5 key works (but context menu doesn't have shortcuts)
- `[*]` and `[X]` are just symbols with no functional meaning

**Dash prefix is clear:**
- `-` is a standard bullet/list marker
- Doesn't imply keyboard shortcuts
- Works well in all environments
- Simple and professional

### Visual Comparison

**Before:**
```
┌──────────────────────────┐
│ [*] Modify Status        │  ← Looks like a shortcut?
│ [S] Save Changes         │  ← Press 'S' key?
│ ────────────────────     │
│ [A] Check Attachments    │
│ ────────────────────     │
│ [X] Delete Issue         │
│ [R] Restore Issue        │
│ ────────────────────     │
│ [F5] Refresh             │  ← Press F5?
│ [H] Export HTML          │
└──────────────────────────┘
```

**After:**
```
┌──────────────────────────┐
│ - Modify Status          │  ← Clear: menu item
│ - Save Changes           │  ← Clear: menu item
│ ────────────────────     │
│ - Check Attachments      │
│ ────────────────────     │
│ - Delete Issue           │
│ - Restore Issue          │
│ ────────────────────     │
│ - Refresh                │
│ - Export HTML            │
└──────────────────────────┘
```

### Note on Keyboard Shortcuts

Context menu items currently **do not have keyboard shortcuts** associated with them. They are mouse-only actions.

If keyboard shortcuts are added in the future, Qt automatically displays them on the right side:
```
┌──────────────────────────────────┐
│ - Modify Status                  │
│ - Save Changes          Ctrl+S   │  ← Qt adds this automatically
│ ────────────────────────────────│
│ - Refresh               F5       │  ← If shortcut is set
└──────────────────────────────────┘
```

---

## Summary of Changes

### File Modified
`ftrack_casino/gui.py`

### Changes

| Lines | Change | Issue Fixed |
|-------|--------|-------------|
| 1410-1412 | Added `removeCellWidget()` loop | Due Date display bug |
| 2219-2228 | Changed `[X]` to `-` prefix | Context menu clarity |

### Code Additions

**Clear widgets before restoring:**
```python
# Clear all cell widgets first (important for Due Date and other complex widgets)
for c in [3, 4, 6, 7, 8, 9]:  # Columns that may have widgets
    tbl.removeCellWidget(r, c)
```

**Simplified menu text:**
```python
"- Modify Status"    # Instead of "[*] Modify Status"
"- Save Changes"     # Instead of "[S] Save Changes"
# ... etc
```

---

## Testing Checklist

### Due Date Fix
- [ ] Open Issue Status Viewer
- [ ] Select an issue row
- [ ] Click "Modify Status"
- [ ] Verify Due Date shows widget with date/time editors
- [ ] Press ESC key
- [ ] **Verify Due Date displays correctly** (e.g., "2025-01-15 14:30")
- [ ] Verify no broken widgets or empty cells
- [ ] Verify all other fields restored correctly

### Context Menu Text
- [ ] Right-click on any issue row
- [ ] Verify all items show "- ItemName" format
- [ ] Verify no bracket notation like [X]
- [ ] Verify text is clear and not confusing
- [ ] Verify items still function correctly when clicked

---

## Related Issues

### Other Columns Also Fixed

While the bug was most visible in Due Date (complex widget), the fix also prevents potential issues in:
- **Assignee** (QComboBox)
- **Status** (QComboBox)
- **Severity** (QComboBox)
- **Stage** (QComboBox)
- **Blocks** (QListWidget)

All these columns are now properly cleaned up when ESC is pressed.

### Why Didn't We See This Bug in Other Columns?

**Status column** is the most commonly edited, but the bug was less obvious there because:
- QComboBox renders more like text
- Less complex than Due Date's layout
- Might appear to work but still have underlying widget/item conflict

**Due Date** made it obvious because:
- Complex widget with multiple sub-widgets
- Layout that clearly shows it's broken
- Empty space when widget/item conflict occurs

---

## Technical Explanation Summary

### The Widget vs Item Problem

QTableWidget cells have two parallel systems:
1. **Item system:** `setItem()` / `item()` - for text/data
2. **Widget system:** `setCellWidget()` / `cellWidget()` - for custom UI

**Only ONE can be active at a time:**
- If you set a widget, the item is hidden (even if set)
- If you remove the widget, the item becomes visible again

**Our fix:** Always remove widgets before setting items to ensure clean state.

### Qt Documentation Reference

From Qt documentation:
> "The table takes ownership of the widget. If cell widget A is replaced with cell widget B, cell widget A will be deleted. [...] If you want to reuse cell widget A, you can remove it from the cell before calling setCellWidget()."

This confirms that widgets must be explicitly removed when switching back to items.

---

*Fixes Applied: 2025-01-28*
*FastTrack Version: 2.0*
*File Modified: ftrack_casino/gui.py*
*Lines Changed: 1410-1412, 2219-2228*
