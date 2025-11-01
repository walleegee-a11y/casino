# Split-View History Interface Guide

## New Layout Design

The History dialog now uses a **vertical split-view** layout for easier version comparison:

```
┌─────────────────────────────────────────────────────────────────┐
│ Description History - ISSUE_001          [Search history...]    │
├──────────────────┬──────────────────────────────────────────────┤
│ VERSION LIST     │ CONTENT VIEWER                               │
│ (Left Panel)     │ (Right Panel)                                │
├──────────────────┤                                              │
│ [CURRENT] Version│ ┌────────────────────────────────────────┐  │
│                  │ │ [CURRENT] Version                      │  │
│ ────────────────│ │ Time: 2025-11-01 15:30 | User: scott   │  │
│ Version #5       │ └────────────────────────────────────────┘  │
│ 2025-11-01 14:30 │                                              │
│ User: scott      │ ┌────────────────────────────────────────┐  │
│                  │ │ Current description text appears here  │  │
│ ────────────────│ │ with full formatting and content...    │  │
│ Version #4       │ │                                        │  │
│ 2025-11-01 12:00 │ │ This is the actual content that will   │  │
│ User: alice      │ │ be displayed when you select a version │  │
│                  │ │ from the left panel.                   │  │
│ ────────────────│ │                                        │  │
│ Version #3       │ │ When historical versions are selected, │  │
│ 2025-11-01 10:15 │ │ you'll see color-coded diff view.      │  │
│ User: bob        │ └────────────────────────────────────────┘  │
│ [Restored]       │                                              │
│                  │ [[Toggle] Diff/Full] [[Restore] This Ver]   │
├──────────────────┴──────────────────────────────────────────────┤
│ [[Export] History]                              [[Close]]       │
└─────────────────────────────────────────────────────────────────┘
```

## Layout Components

### Left Panel: Version List

**Features:**
- **[CURRENT] Version** - Highlighted in green at top
- **Historical versions** - Listed in reverse chronological order
- **Hover highlighting** - Versions light up on mouse hover
- **Selection highlighting** - Selected version shown in blue
- **Version info display:**
  - Version number
  - Timestamp
  - User name
  - [Restored] badge if applicable

**Visual cues:**
- Current version: Green background (#e6ffec)
- Selected version: Blue background (#0969da)
- Hover: Light blue background (#e6f2ff)

### Right Panel: Content Viewer

**Components:**

1. **Info Header** (blue bar at top)
   - Shows selected version details
   - Format: `Version #X | Time: ... | User: ...`
   - Shows [Restored from...] info if applicable

2. **Content Display** (large white area)
   - **For Current Version:** Shows plain text content
   - **For Historical Versions:** Shows color-coded diff by default
     - Red lines: Content removed
     - Green lines: Content added
     - Gray lines: Unchanged content

3. **Action Buttons** (bottom)
   - `[Toggle] Diff/Full Text` - Switch between diff view and full text
   - `[Restore] This Version` - Restore selected version
   - Both disabled when current version selected

## How to Use

### Viewing Versions

1. **Click on any version** in the left panel list
2. **Right panel updates** to show that version's content
3. **Info header** displays version details

### Comparing Changes

**When historical version is selected:**
- Diff view shown automatically
- **Red background** = Lines that were removed (old content)
- **Green background** = Lines that were added (new content)
- **Gray text** = Unchanged lines

**Example diff display:**
```
Unified Diff View
Changes: +3 additions, -2 deletions

  This line stayed the same
− This line was removed (red)
− Another removed line (red)
+ This line was added (green)
+ Another new line (green)
  This line stayed the same
```

### Toggling Views

**Click `[Toggle] Diff/Full Text` button:**
- **Diff View** → Shows color-coded changes
- **Full Text View** → Shows complete text of that version

### Restoring Versions

1. **Select a historical version** from left panel
2. **Click `[Restore] This Version`** button
3. **Confirm** in dialog that appears
4. Version is restored and new history entry created

### Searching

**Use search box at top:**
- Type to filter versions
- Searches in: timestamp, user name, description content
- Matching versions stay visible
- Non-matching versions hidden
- Clear search to show all

## Key Improvements

### Before (Timeline View):
- ❌ Vertical scrolling through all versions
- ❌ Had to expand each version to see diff
- ❌ Difficult to compare versions
- ❌ Takes many clicks to navigate
- ❌ Can't see list and content simultaneously

### After (Split View):
- ✅ All versions visible in list at once
- ✅ Click once to see any version
- ✅ Diff shown automatically
- ✅ Easy to jump between versions
- ✅ List and content always visible
- ✅ Toggle diff/full text instantly
- ✅ More screen space efficient

## Keyboard Navigation

**In version list (left panel):**
- `↑` / `↓` - Navigate versions
- `Enter` - Select version
- `Home` - Go to current version
- `End` - Go to oldest version

**Global:**
- `Ctrl+F` - Focus search box
- `Esc` - Clear search / Close dialog

## Visual States

### Version List Items

**Current Version:**
```
┌──────────────────┐
│ [CURRENT] Version│ (Green background)
│                  │
└──────────────────┘
```

**Regular Version:**
```
┌──────────────────┐
│ Version #3       │ (White background)
│ 2025-11-01 12:00 │
│ User: alice      │
└──────────────────┘
```

**Selected Version:**
```
┌──────────────────┐
│ Version #3       │ (Blue background, white text)
│ 2025-11-01 12:00 │
│ User: alice      │
└──────────────────┘
```

**Restored Version:**
```
┌──────────────────┐
│ Version #2       │ (White background)
│ 2025-11-01 10:30 │
│ User: bob        │
│ [Restored]       │ (Shows badge)
└──────────────────┘
```

### Content Display States

**Viewing Current Version:**
- Info bar: `[CURRENT] Version | Time: ... | User: ...`
- Content: Plain text
- Buttons: Both disabled (grayed out)

**Viewing Historical Version (Diff Mode):**
- Info bar: `Version #X | Time: ... | User: ...`
- Content: Color-coded diff with statistics
- Buttons: Both enabled

**Viewing Historical Version (Full Text Mode):**
- Info bar: `Version #X | Time: ... | User: ...`
- Content: Plain text of that version
- Buttons: Both enabled

## Benefits of Split View

1. **Faster Navigation**
   - See all versions at a glance
   - One click to switch versions
   - No scrolling through expanded cards

2. **Better Comparison**
   - Easy to jump between versions
   - Diff shown immediately
   - Toggle between diff and full text

3. **More Screen Space**
   - Efficient use of horizontal space
   - Larger content display area
   - Better for wide monitors

4. **Clearer Organization**
   - Versions listed chronologically
   - Clear visual separation
   - Easy to scan version list

5. **Improved Workflow**
   - Less clicking needed
   - Faster version review
   - Better for auditing changes

## Testing

Run the test script to see the new split view:

```bash
cd /c/Users/SCOTT/projects/casino/casino_pond_ai_1031/ftrack_casino
python test_enhancements.py
```

Click `[TEST] History Dialog` button to see:
- Version list on the left
- Content viewer on the right
- Click different versions to see content change
- Try the `[Toggle]` button to switch between diff and full text
- Try the search box to filter versions
