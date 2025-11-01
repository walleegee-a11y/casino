# Rich Text WYSIWYG Editor Guide

## Overview

The FastTrack issue tracking system now features a **full WYSIWYG (What You See Is What You Get) rich text editor** for issue descriptions, replacing the previous markdown-based editor.

## Key Features

### 1. **WYSIWYG Editing**
- See formatting as you type (like MS Word or Google Docs)
- No markdown syntax required
- Direct visual feedback

### 2. **Interactive Clickable Checkboxes**
- Insert checkboxes with `[☐] Checklist` button
- **Click checkboxes directly to toggle** between ☐ (unchecked) and ☑ (checked)
- Perfect for task tracking and TODO lists

### 3. **Tables with Visual Editing**
- Insert tables with `[Table]` button
- Specify rows and columns
- Edit cells directly
- Add/remove rows and columns
- Format cell borders and backgrounds

### 4. **Rich Text Formatting**
- **Bold** - `[B] Bold` button
- *Italic* - `[I] Italic` button
- <u>Underline</u> - `[U] Underline` button
- **Text Colors** - `[Color]` button opens color picker
- **Font Sizes** - Size dropdown (8-24pt)

### 5. **Lists**
- Bullet lists - `[•] Bullet List` button
- Numbered lists - `[1] Numbered List` button

### 6. **Dual Storage**
- Saves as **HTML** (full formatting preserved)
- Saves as **plain text** (for backward compatibility)
- Both stored in YAML file

## How to Use

### Opening the Editor

1. In Issue Status Viewer, click an issue title
2. Click `[Modify]` button
3. Rich text editor window opens

### Formatting Text

**To apply formatting:**
1. Select text you want to format
2. Click formatting button (e.g., `[B] Bold`)
3. Text is immediately formatted

**Or type then format:**
1. Type your text
2. Select it
3. Apply formatting

### Using Checkboxes

**To insert a checkbox:**
1. Click `[☐] Checklist` button
2. Checkbox character ☐ is inserted
3. Type task description after it

**To toggle checkbox:**
1. **Click directly on the checkbox character** (☐ or ☑)
2. It toggles: ☐ → ☑ or ☑ → ☐
3. No need to edit text manually!

**Example:**
```
☐ Implement feature A
☑ Test feature A
☐ Deploy feature A
```

Click the ☐ next to "Implement feature A" and it becomes ☑!

### Inserting Tables

**To create a table:**
1. Click `[Table]` button
2. Enter number of rows (e.g., 3)
3. Enter number of columns (e.g., 3)
4. Table is inserted at cursor
5. Click in cells to edit content

**Example table:**
| Feature | Status | Priority |
|---------|--------|----------|
| Editor  | Done   | High     |
| Tables  | Testing| Medium   |
| Export  | Pending| Low      |

### Changing Text Color

**To change color:**
1. Select text
2. Click `[Color]` button
3. Choose color from picker
4. Text changes to selected color

### Changing Font Size

**To change size:**
1. Select text
2. Choose size from dropdown (8, 10, 12, 14, 16, 18, 20, 24)
3. Text resizes immediately

### Clearing Formatting

**To remove all formatting:**
1. Select formatted text
2. Click `[Clear Format]` button
3. Text returns to plain style

### Saving Changes

1. Click `[Save]` button
2. Both HTML and plain text versions saved to YAML
3. New history entry created
4. Description window updates

## Toolbar Reference

### Row 1: Text Formatting

| Button | Function | Shortcut |
|--------|----------|----------|
| `[B] Bold` | Bold text | - |
| `[I] Italic` | Italic text | - |
| `[U] Underline` | Underline text | - |
| `[Color]` | Change text color | - |
| Size dropdown | Change font size (8-24pt) | - |
| Stats | Shows char/word/line count | - |

### Row 2: Structure & Lists

| Button | Function | Notes |
|--------|----------|-------|
| `[•] Bullet List` | Insert bullet list | Creates unordered list |
| `[1] Numbered List` | Insert numbered list | Creates ordered list |
| `[☐] Checklist` | Insert checkbox | **Clickable!** |
| `[Table]` | Insert table | Asks for dimensions |
| `[Clear Format]` | Remove formatting | Resets to plain text |

### Bottom: Actions

| Button | Function |
|--------|----------|
| `[Save]` | Save and close editor |
| `[Cancel]` | Discard changes and close |

## Data Storage Format

### YAML Structure

```yaml
id: ISSUE_001
title: Example Issue
description: "Plain text version for compatibility"
description_html: "<p><b>HTML</b> version with <i>full</i> formatting</p>"
description_history:
  - timestamp: "2025-11-01 10:00:00"
    user: scott
    old_description: "Previous plain text"
    old_description_html: "<p>Previous <b>HTML</b></p>"
```

### What Gets Saved

**On every save:**
1. **description** - Plain text (extracted from HTML)
2. **description_html** - Full HTML with formatting
3. **description_history** entry:
   - old_description - Previous plain text
   - old_description_html - Previous HTML
   - timestamp, user

## History Viewer Integration

### Viewing HTML History

1. Click `[History]` button
2. History dialog shows 3 columns:
   - Left: Version list
   - **Middle: Current version (HTML-rendered)**
   - Right: Selected version (HTML-rendered)

### Rich Content in Diffs

- Diffs compare plain text versions
- Full text view shows HTML-rendered content
- Checkboxes visible in historical versions
- Tables rendered properly

### Restoring Versions

1. Select historical version
2. View it in right panel (HTML-rendered)
3. Click `[Restore] Selected`
4. Restored version includes HTML formatting

## Use Cases

### Use Case 1: Task Tracking

**Scenario:** Track implementation tasks for a feature

**Steps:**
1. Open editor
2. Click `[☐] Checklist` 5 times
3. Type task descriptions
4. Click checkboxes as you complete tasks
5. Save periodically

**Result:** Live task list you can update with mouse clicks!

### Use Case 2: Formatted Requirements

**Scenario:** Document feature requirements with formatting

**Steps:**
1. Type heading, select it, increase font size
2. Add bullet list of requirements
3. **Bold** critical requirements
4. Use **red color** for breaking changes
5. Add table showing affected modules
6. Save

**Result:** Professional-looking requirements document!

### Use Case 3: Status Reports

**Scenario:** Weekly status update with tables

**Steps:**
1. Insert table (3 cols: Task, Status, Notes)
2. Fill in tasks
3. Use checkboxes for completion status
4. **Bold** completed items
5. Add colored notes (green=good, red=blocked)
6. Save

**Result:** Clear visual status report!

### Use Case 4: Meeting Notes

**Scenario:** Track action items from meeting

**Steps:**
1. Type meeting title (bold, large font)
2. Add checklist of action items
3. Assign to people with **bold names**
4. Click checkboxes as items complete
5. Update notes over time

**Result:** Living document tracking action items!

## Advanced Features

### Keyboard Workflow

While the editor is WYSIWYG, you can still use keyboard shortcuts:
- Standard copy/paste (Ctrl+C, Ctrl+V)
- Undo/Redo (Ctrl+Z, Ctrl+Y)
- Select all (Ctrl+A)

### Complex Formatting

**Combining styles:**
- Bold + Italic + Colored text all work together
- Can underline colored text
- Can make table cell text bold

**Nested lists:**
- Use Tab/Shift+Tab to indent list items
- Creates hierarchical lists automatically

### Table Editing

**Adding rows/columns:**
- Right-click in table (context menu may appear)
- Or manually select cells and use standard editing

**Cell formatting:**
- Select text in cell
- Apply any formatting (bold, color, etc.)
- Works like normal text

## Backward Compatibility

### Opening Old Markdown Descriptions

**What happens:**
- Old descriptions without `description_html` load as plain text
- You can edit them with rich text features
- On save, both HTML and plain text versions created

**Migration:**
- No manual migration needed
- Descriptions automatically upgraded on first edit
- Old plain text preserved for compatibility

### Mixed Environments

**If some users use old FastTrack version:**
- They see plain text version (description field)
- They won't see formatting
- No data loss - just no formatting visible

**If all users upgrade:**
- Everyone sees rich formatting
- Full WYSIWYG experience
- Checkboxes clickable for everyone

## Troubleshooting

### Checkbox Not Toggling

**Problem:** Clicking checkbox doesn't toggle it

**Solutions:**
- Make sure you click **directly on the checkbox character** (☐ or ☑)
- If you click next to it, cursor just moves
- Try clicking again directly on the checkbox

### Formatting Not Saving

**Problem:** Formatting disappears after save

**Solutions:**
- Check that `description_html` field exists in YAML
- Verify permissions to write YAML file
- Check for errors in save operation

### Table Looks Wrong

**Problem:** Table formatting off after reload

**Solutions:**
- Qt's rich text tables are basic
- Use simple tables (avoid complex merging)
- Keep table borders at 1px

### Colors Not Showing

**Problem:** Colored text appears black

**Solutions:**
- Make sure viewing HTML version not plain text
- Check if QTextBrowser supports color spans
- Try different colors (some may not render)

## Tips & Best Practices

### 1. Save Frequently

- Click `[Save]` periodically while editing
- Each save creates history entry
- Can restore if you make mistakes

### 2. Use Checkboxes for Tasks

- Checkboxes are **interactive** - click to toggle
- Much faster than editing text
- Visual completion tracking

### 3. Keep Tables Simple

- Use 2-5 columns maximum
- Avoid very large tables
- Simple borders work best

### 4. Use Colors Sparingly

- **Red** for critical/blocking issues
- **Green** for completed items
- Too many colors = hard to read

### 5. Format After Writing

- Type content first
- Apply formatting after
- Easier than formatting while typing

### 6. Test Checkboxes

- After inserting checkboxes, test clicking them
- Make sure they toggle correctly
- Helps verify they're properly formatted

## Technical Details

### Implementation

**Editor Class:** `RichTextDescriptionEditor` (gui.py:108-371)

**Key Components:**
- `QTextEdit` in rich text mode
- Event filter for checkbox clicking
- Dual output (HTML + plain text)

**Checkbox Toggle:**
- Event filter on editor viewport
- Detects clicks on ☐ or ☑ characters
- Swaps character on click

**Table Support:**
- Uses `QTextCursor.insertTable()`
- `QTextTableFormat` for styling
- Native Qt table rendering

### Data Flow

```
User Edit → QTextEdit → HTML + Plain Text → YAML → Database
                ↓                              ↓
          Live Preview              description + description_html
```

### HTML Generation

**Qt's toHtml():**
- Generates standard HTML
- Includes inline CSS styles
- Preserves all formatting

**Plain Text Extraction:**
- Uses `toPlainText()`
- Strips all formatting
- For backward compatibility

## Summary

The Rich Text WYSIWYG Editor provides:

✅ **No markdown syntax** - direct formatting
✅ **Interactive checkboxes** - click to toggle
✅ **Visual tables** - easy data presentation
✅ **Full formatting** - bold, italic, colors, sizes
✅ **Dual storage** - HTML + plain text
✅ **Backward compatible** - works with old data
✅ **History support** - HTML rendered in diffs
✅ **Easy to use** - familiar word processor interface

Perfect for managing issue descriptions with rich content, task lists, and formatted documentation!
