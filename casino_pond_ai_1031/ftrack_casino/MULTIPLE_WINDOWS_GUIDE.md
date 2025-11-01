# Multiple Non-Modal Windows Guide

## Overview

All FastTrack windows are now **non-modal**, allowing you to:
- Open multiple description windows
- Open multiple editors
- Open multiple history viewers
- Keep the Issue Status Viewer active
- Work on multiple issues simultaneously

## Window Hierarchy

```
[Issue Status Viewer] ← Main window, always active
  │
  ├─ [Description ISSUE_001] ← Non-modal, independent
  │    ├─ [Edit Description ISSUE_001] ← Non-modal, can have multiple
  │    └─ [History ISSUE_001] ← Non-modal, can have multiple
  │
  ├─ [Description ISSUE_002] ← Non-modal, independent
  │    ├─ [Edit Description ISSUE_002] ← Non-modal, can have multiple
  │    └─ [History ISSUE_002] ← Non-modal, can have multiple
  │
  └─ [Description ISSUE_003] ← Non-modal, independent
       ├─ [Edit Description ISSUE_003] ← Non-modal, can have multiple
       └─ [History ISSUE_003] ← Non-modal, can have multiple
```

**All windows can be open simultaneously!**

## What You Can Do Now

### 1. Open Multiple Descriptions

**Click on multiple issue titles:**
```
Issue Status Viewer
  Click ISSUE_001 → Description window opens
  Click ISSUE_002 → Another description opens
  Click ISSUE_003 → Another description opens
  ...all windows stay open
```

### 2. Edit Multiple Issues Simultaneously

**From each description window, click "Modify":**
```
Description ISSUE_001
  Click [Modify] → Editor opens
    Description ISSUE_002
      Click [Modify] → Another editor opens
        Description ISSUE_003
          Click [Modify] → Third editor opens
```

**Result:** 3 editors open, editing different issues!

### 3. View Multiple Histories

**From each description window, click "History":**
```
Description ISSUE_001
  Click [History] → History viewer opens
    Description ISSUE_002
      Click [History] → Another history viewer opens
```

**Result:** Multiple history viewers open for different issues!

### 4. Mix and Match

**Open whatever combination you need:**
```
- 5 description windows
- 3 editors (editing different issues)
- 2 history viewers (viewing history of different issues)
- Issue Status Viewer still active
```

**All at the same time!**

## Practical Workflows

### Workflow 1: Batch Editing Multiple Issues

**Scenario:** Need to update descriptions of 5 related bugs

**Steps:**
1. Open Issue Status Viewer
2. Click on issues 1, 2, 3, 4, 5 → 5 description windows open
3. In each description window, click [Modify] → 5 editors open
4. Edit all 5 descriptions in parallel
5. Save each one as you finish
6. All editors and descriptions remain open until you close them

**Benefit:** Edit multiple issues without switching back and forth!

### Workflow 2: Compare Histories

**Scenario:** Compare how two issues evolved over time

**Steps:**
1. Open descriptions for ISSUE_A and ISSUE_B
2. Click [History] in ISSUE_A → History viewer opens
3. Click [History] in ISSUE_B → Another history viewer opens
4. Arrange both history viewers side-by-side
5. Compare version timelines

**Benefit:** See evolution of both issues simultaneously!

### Workflow 3: Reference While Editing

**Scenario:** Need to reference multiple issues while editing current one

**Steps:**
1. Open description for ISSUE_CURRENT
2. Open descriptions for ISSUE_REF1, ISSUE_REF2, ISSUE_REF3
3. In ISSUE_CURRENT, click [Modify] → Editor opens
4. Arrange reference descriptions beside editor
5. Copy/reference info while editing

**Benefit:** All reference material visible while editing!

### Workflow 4: Parallel Review and Edit

**Scenario:** Review history and edit description of same issue

**Steps:**
1. Open description for ISSUE_001
2. Click [History] → History viewer opens
3. In same description window, click [Modify] → Editor opens
4. Arrange history and editor side-by-side
5. Reference history while editing

**Benefit:** See what changed historically while making new edits!

## Window Management Tips

### Arranging Windows

**Manual arrangement:**
- Drag windows to position them
- Resize windows as needed
- Use system window snapping (Windows Key + Arrow on Windows)

**Multi-monitor setup:**
- Monitor 1: Issue Status Viewer + Description windows
- Monitor 2: Editors and History viewers

### Keyboard Shortcuts

**Switching between windows:**
- `Alt+Tab` - Cycle through all open windows
- Click on window in taskbar

**Window operations:**
- Minimize - Click minimize button
- Maximize - Double-click title bar or click maximize button
- Close - Click X or [Close] button

### Closing Windows

**Individual windows:**
- Click X button on each window
- Click [Close] button (if available)

**Close all at once:**
- Close the Issue Status Viewer
- All child windows (descriptions, editors, histories) close automatically

## Technical Details

### Non-Modal Implementation

**All dialogs use:**
```python
window.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint)
window.show()  # Instead of window.exec_()
```

**Benefits:**
- Independent windows
- Don't block parent
- Standard window controls
- Taskbar entries
- Alt+Tab support

### Reference Management

**To prevent garbage collection:**
```python
description_dialogs = []  # Stores description windows
editor_dialogs = []       # Stores editor windows
history_dialogs = []      # Stores history windows

# Add when created
dialogs.append(window)

# Remove when closed
window.finished.connect(lambda: dialogs.remove(window))
```

**Memory management:**
- Windows tracked while open
- Removed from list when closed
- Python garbage collector cleans up
- No memory leaks

### Data Synchronization

**When editor saves:**
1. Updates YAML file
2. Updates description window
3. Updates Issue Status Viewer table
4. Reloads data for consistency

**When version restored in history:**
1. Updates YAML file
2. Refreshes history dialog
3. When history dialog closes, updates description window
4. Updates Issue Status Viewer table

## Limitations

### Current Limitations

**Same issue, multiple editors:**
- You CAN open multiple editors for same issue
- They will all edit the same underlying data
- **Last save wins** - be careful!
- Better to use one editor per issue

**Concurrent editing:**
- No locking mechanism
- If two people edit same issue file, last save wins
- Use communication to coordinate

**Window management:**
- Many windows can clutter screen
- Use minimize/close to manage
- Consider closing windows when done

## Best Practices

### 1. Close Windows When Done

**Don't accumulate windows:**
- Close descriptions you're done with
- Close editors after saving
- Close history viewers after reviewing

### 2. One Editor Per Issue

**Avoid confusion:**
- Don't open multiple editors for same issue
- If accidentally opened, close extras
- Use one editor, save, then close

### 3. Use Multiple Monitors

**If available:**
- Viewer on one monitor
- Work windows on another
- Easier to manage many windows

### 4. Organize by Task

**Group related windows:**
- Related issues near each other
- Editors on one side
- References on another

### 5. Save Frequently

**In editors:**
- Save as you complete sections
- Don't keep many unsaved changes
- Reduces risk if window accidentally closed

## Window States

### Description Window

| Element | Behavior |
|---------|----------|
| **Title** | "Description - ISSUE_XXX" |
| **Parent** | Issue Status Viewer |
| **Modal** | No - viewer stays active |
| **Multiple** | Yes - one per issue click |
| **Buttons** | Modify, History, Close |

### Editor Window

| Element | Behavior |
|---------|----------|
| **Title** | "Edit Description - ISSUE_XXX" |
| **Parent** | Description window |
| **Modal** | No - description stays active |
| **Multiple** | Yes - one per Modify click |
| **Tabs** | Edit, Preview |
| **Buttons** | Save, Cancel |

### History Window

| Element | Behavior |
|---------|----------|
| **Title** | "Description History - ISSUE_XXX" |
| **Parent** | Description window |
| **Modal** | No - description stays active |
| **Multiple** | Yes - one per History click |
| **Layout** | 3-column (list, current, selected) |
| **Buttons** | Toggle, Restore, Export, Close |

## Testing

### Test Scenario 1: Multiple Descriptions

1. Open Issue Status Viewer
2. Click 3 different issue titles
3. **Expected:** 3 description windows open
4. **Expected:** Viewer remains active and usable
5. **Expected:** Can click more titles to open more

### Test Scenario 2: Multiple Editors

1. Open 2 descriptions
2. Click [Modify] in first → Editor opens
3. Click [Modify] in second → Another editor opens
4. **Expected:** Both editors open and usable
5. **Expected:** Both description windows still visible

### Test Scenario 3: Multiple Histories

1. Open 2 descriptions
2. Click [History] in first → History opens
3. Click [History] in second → Another history opens
4. **Expected:** Both history viewers open
5. **Expected:** Can navigate both independently

### Test Scenario 4: Mixed Windows

1. Open 3 descriptions
2. Open 2 editors (from 2 descriptions)
3. Open 1 history viewer (from 1 description)
4. **Expected:** All 6 windows open (3 desc + 2 edit + 1 hist)
5. **Expected:** All functional and independent

### Test Scenario 5: Data Sync

1. Open description for ISSUE_001
2. Click [Modify], edit and save
3. **Expected:** Description window updates
4. **Expected:** Issue Status Viewer table updates
5. Open history for same issue
6. **Expected:** New version appears in history

## Troubleshooting

### Issue: Window disappears after creation

**Cause:** Window was garbage collected

**Solution:** Already handled - windows are stored in lists

### Issue: Can't interact with viewer

**Cause:** A modal dialog is open somewhere

**Solution:** Find and close the modal dialog, all should be non-modal now

### Issue: Multiple editors for same issue

**Cause:** Clicked [Modify] multiple times

**Solution:** Close extra editors, keep one

### Issue: Changes not reflecting

**Cause:** Another window has older data

**Solution:** Close and reopen windows to refresh data

## Summary

The multiple non-modal window feature provides:

✅ **Flexibility** - Open as many windows as needed
✅ **Productivity** - Work on multiple issues simultaneously
✅ **Comparison** - View multiple issues side-by-side
✅ **Freedom** - All windows stay active and usable
✅ **Organization** - Arrange windows however you want

No more blocking dialogs - work the way you want!
