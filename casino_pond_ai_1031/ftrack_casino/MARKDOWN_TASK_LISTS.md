# Markdown Task Lists (Checkboxes)

## Overview

The Description Editor now supports **GitHub-flavored markdown task lists** with visual checkbox rendering in the preview.

## How to Use Task Lists

### Syntax

**Unchecked task:**
```markdown
- [ ] This is an incomplete task
```

**Checked task:**
```markdown
- [v] This is a completed task
- [X] This also works (capital X)
```

### Quick Insert Button

Use the **[ ] Task** button in the formatting toolbar to quickly insert an unchecked task item.

**Workflow:**
1. Click `[ ] Task` button → Inserts `- [ ] ` at cursor
2. Type your task description
3. Press Enter to add another task
4. To mark as complete, change `[ ]` to `[v]`

## Example

**Markdown Input:**
```markdown
## Project TODO

- [v] Setup development environment
- [v] Create basic UI layout
- [ ] Implement markdown editor
  - [v] Add formatting toolbar
  - [v] Add preview tab
  - [ ] Add image upload
- [ ] Write documentation
- [ ] Deploy to production
```

**Preview Output:**
```
## Project TODO

☑ Setup development environment
☑ Create basic UI layout
☐ Implement markdown editor
  ☑ Add formatting toolbar
  ☑ Add preview tab
  ☐ Add image upload
☐ Write documentation
☐ Deploy to production
```

The preview will show actual HTML checkboxes (disabled, read-only).

## Nested Task Lists

You can indent tasks to create hierarchical lists:

```markdown
- [v] Main task
  - [v] Subtask 1
  - [ ] Subtask 2
    - [v] Sub-subtask 1
    - [ ] Sub-subtask 2
```

## Toolbar Buttons Reference

| Button | Shortcut | Inserts |
|--------|----------|---------|
| **Bold** | - | `**text**` |
| *Italic* | - | `*text*` |
| `Code` | - | `` `text` `` |
| ## H2 | - | `## ` (heading) |
| - List | - | `- ` (bullet) |
| [ ] Task | - | `- [ ] ` (checkbox) |

## Preview Behavior

- **Edit Tab**: Shows raw markdown with `- [ ]` and `- [v]` syntax
- **Preview Tab**: Renders HTML checkboxes (disabled, non-interactive)
- Checkboxes are for visual reference only in preview mode
- To change checkbox state, edit the markdown in the Edit tab

## Technical Details

### Implementation

The editor pre-processes markdown text before rendering:

1. **Pattern matching**: Uses regex to find task list patterns
   - `- [ ]` → Unchecked checkbox HTML
   - `- [v]` or `- [X]` → Checked checkbox HTML

2. **HTML conversion**:
   ```markdown
   - [ ] Task  →  - <input type="checkbox" disabled> Task
   - [v] Done  →  - <input type="checkbox" disabled checked> Done
   ```

3. **CSS styling**: Checkboxes are styled with proper spacing and disabled state

### Code Location

- **File**: `ftrack_casino/gui.py`
- **Class**: `MarkdownDescriptionEditor`
- **Method**: `update_preview()` (lines 215-298)
- **Regex patterns**: Lines 223-225
- **CSS styles**: Lines 276-286

## Use Cases

### 1. Issue Requirements Tracking

```markdown
## Requirements

- [v] User authentication
- [v] Dashboard view
- [ ] Data export
- [ ] Email notifications
```

### 2. Testing Checklist

```markdown
## Test Plan

- [ ] Unit tests
  - [v] Database layer
  - [v] API endpoints
  - [ ] UI components
- [ ] Integration tests
- [ ] Performance tests
```

### 3. Review Checklist

```markdown
## Code Review

- [v] Code follows style guide
- [v] All tests pass
- [ ] Documentation updated
- [ ] Performance acceptable
- [ ] Security review completed
```

### 4. Project Milestones

```markdown
## Release v1.0

- [v] Feature freeze
- [v] Beta testing
- [ ] Bug fixes
  - [v] Critical bugs
  - [ ] Minor bugs
- [ ] Final release
```

## Tips

1. **Use for actionable items**: Task lists work best for tracking concrete action items
2. **Keep descriptions short**: Each task should be a single line for clean rendering
3. **Use nesting sparingly**: Deep nesting (>3 levels) can become hard to read
4. **Update regularly**: Mark tasks as complete `[v]` to track progress
5. **Combine with headings**: Use `##` headings to group related tasks

## Limitations

- Checkboxes in preview are **read-only** (by design)
- To change state, must edit markdown in Edit tab
- No automatic date/time stamps for completion
- No assignee tracking (use text for this)

## Integration with FastTrack

Task lists are automatically saved with the issue description when you click `[Save]`.

**Workflow:**
1. Open issue description → Click `[Modify]`
2. Add task list items in markdown
3. Switch to `[Preview]` tab to verify rendering
4. Click `[Save]` to persist changes
5. Task list is stored in YAML and versioned in history

**Version history** will show checkbox state changes in diffs:
```diff
- - [ ] Implement feature X
+ - [v] Implement feature X
```

## Summary

Task list checkboxes provide a **simple, visual way** to track actionable items directly in issue descriptions without needing separate task tracking systems.

**Benefits:**
- ✓ Visual clarity (checkboxes vs. plain text)
- ✓ Standard markdown syntax (GitHub-compatible)
- ✓ One-click insertion via toolbar button
- ✓ Automatic rendering in preview
- ✓ Version tracked in history
