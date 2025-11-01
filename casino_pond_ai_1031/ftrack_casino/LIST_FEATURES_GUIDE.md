# List Features Guide

## Three Types of Lists

FastTrack rich text editor now has three list types with enhanced keyboard support.

---

## 1. [-] Bullet List

**Creates:** Bulleted list with disc markers

**How to use:**
1. Click `[-] Bullet List` button
2. Type first item
3. Press **Enter** → next bullet appears automatically
4. Press **Enter twice** to exit list

**Keyboard shortcuts:**
- **Tab** → Indent (create sub-item)
- **Shift+Tab** → Outdent (move back to parent level)

**Example:**
```
- Main item
  - Sub item (indented with Tab)
  - Another sub item
- Back to main level (Shift+Tab)
```

---

## 2. [1] Numbered List

**Creates:** Numbered list with automatic numbering

**How to use:**
1. Click `[1] Numbered List` button
2. Type first item
3. Press **Enter** → next number appears automatically
4. Press **Enter twice** to exit list

**Keyboard shortcuts:**
- **Tab** → Indent (create sub-item with sub-numbering)
- **Shift+Tab** → Outdent (move back to parent level)

**Example:**
```
1. Main item
   1. Sub item (indented with Tab)
   2. Another sub item
2. Back to main level (Shift+Tab)
```

---

## 3. [ ] Task Item (Interactive Checklist)

**Creates:** Interactive checkbox items (NO bullet markers)

**How to use:**
1. Click `[ ] Task Item` button → inserts `[ ] `
2. Type first task
3. Press **Enter** → next checkbox appears automatically!
4. Keep typing tasks and pressing Enter
5. Press **Enter twice** on empty checkbox to exit
6. **Click on `[ ]` to toggle** → becomes `[v]`

**Keyboard shortcuts:**
- **Enter** → Auto-creates next checkbox (like bullet list!)
- **Enter Enter** → Exit checkbox mode (on empty line)
- **Tab** → Indent checkbox (add 2 spaces)
- **Shift+Tab** → Outdent checkbox (remove 2 spaces)
- **Click checkbox** → Toggle `[ ]` ↔ `[v]`

**Special behaviors:**
- **No bullet symbol** (clean checkbox-only format)
- **Auto-continues like lists** - press Enter for next checkbox
- **Indenting supported** - use Tab/Shift+Tab

**Example workflow:**
```
1. Click `[ ] Task Item` button
2. Type "Setup database"
3. Press Enter → next checkbox appears!
4. Type "Create API"
5. Press Enter → next checkbox appears!
6. Type "Deploy"
7. Press Enter twice to finish
```

**Result:**
```
[ ] Setup database
[ ] Create API
[ ] Deploy
```

**Click checkboxes to mark complete:**
```
[v] Setup database    ← clicked!
[v] Create API        ← clicked!
[ ] Deploy           ← not done yet
```

**With indenting (Tab/Shift+Tab):**
```
[ ] Main task
  [ ] Sub-task 1    ← indented with Tab
  [ ] Sub-task 2
[ ] Another main task ← Shift+Tab to outdent
```

---

## Keyboard Shortcuts Summary

| Key | Bullet List | Numbered List | Task Item |
|-----|-------------|---------------|-----------|
| **Enter** | Next bullet | Next number | **Next checkbox** |
| **Enter Enter** | Exit list | Exit list | **Exit checkbox mode** |
| **Tab** | Indent (sub-item) | Indent (sub-item) | **Indent (add 2 spaces)** |
| **Shift+Tab** | Outdent (parent) | Outdent (parent) | **Outdent (remove 2 spaces)** |
| **Click checkbox** | - | - | **Toggle [ ] ↔ [v]** |

---

## Common Workflows

### Creating a Multi-Level Outline

**Using Bullet List:**
```
1. Click `[-] Bullet List`
2. Type "Main Topic 1"
3. Press Enter
4. Press Tab → indent
5. Type "Sub-topic A"
6. Press Enter → "Sub-topic B"
7. Press Shift+Tab → back to main level
8. Type "Main Topic 2"
```

**Result:**
```
- Main Topic 1
  - Sub-topic A
  - Sub-topic B
- Main Topic 2
```

### Creating a TODO List

**Using Task Item (works just like Bullet List now!):**
```
1. Click `[ ] Task Item` button
2. Type "Setup database"
3. Press Enter → next checkbox auto-appears!
4. Type "Create API endpoints"
5. Press Enter → next checkbox auto-appears!
6. Type "Write tests"
7. Press Enter twice to finish
```

**Result:**
```
[ ] Setup database
[ ] Create API endpoints
[ ] Write tests
```

**As you complete tasks, click the checkboxes:**
```
[v] Setup database      ← clicked
[v] Create API endpoints ← clicked
[ ] Write tests         ← not done yet
```

**Much faster than before!** No need to click button repeatedly.

### Creating Numbered Steps with Sub-Steps

**Using Numbered List:**
```
1. Click `[1] Numbered List`
2. Type "Install dependencies"
3. Press Enter
4. Press Tab
5. Type "npm install"
6. Press Enter → "pip install requirements.txt"
7. Press Shift+Tab
8. Type "Run tests"
```

**Result:**
```
1. Install dependencies
   1. npm install
   2. pip install requirements.txt
2. Run tests
```

---

## Tips & Tricks

### Bullet/Numbered Lists

1. **Indent/Outdent anytime:** Press Tab/Shift+Tab on any list item to change its level
2. **Exit list quickly:** Press Enter twice on an empty list item
3. **Convert between types:** Select list, then click different list button

### Task Items

1. **Works like bullet lists:** Press Enter to auto-create next checkbox!
2. **Exit with double Enter:** Press Enter twice on empty checkbox to stop
3. **Click anywhere near checkbox:** Don't need to be precise - clicking near `[ ]` or `[v]` toggles it
4. **Indent with Tab:** Use Tab/Shift+Tab to create sub-tasks
5. **Manual entry works too:** You can also type `[ ] ` manually anywhere
6. **Toggle anytime:** Click checkbox to mark complete `[v]` or incomplete `[ ]`

### All Lists

1. **Combine with formatting:** You can make list items **bold**, *italic*, or colored
2. **Tables in lists:** Yes, you can put tables inside list items!
3. **Copy/paste lists:** Lists preserve their structure when copied

---

## Differences Between List Types

| Feature | Bullet | Numbered | Task Item |
|---------|--------|----------|-----------|
| **Marker** | Bullet (•) | Numbers (1, 2, 3) | Checkbox ([ ], [v]) |
| **Auto-continues** | Yes (Enter) | Yes (Enter) | **Yes (Enter)** ✓ |
| **Indenting** | Yes (Tab/Shift+Tab) | Yes (Tab/Shift+Tab) | **Yes (Tab/Shift+Tab)** ✓ |
| **Interactive** | No | No | **Yes (clickable)** ✓ |
| **List structure** | Yes (QTextList) | Yes (QTextList) | No (plain text)* |

\* Task items use plain text with smart Enter/Tab handling instead of QTextList structure (to avoid bullet markers)

---

## Why Task Items Are Different

**Design decision:** Task items are **not a QTextList structure** to avoid the bullet marker, but they **behave like lists** through smart keyboard handling.

**How it works:**
- Uses plain text format (just `[ ]` characters)
- Event filter intercepts Enter/Tab keys on checkbox lines
- Automatically adds next checkbox when Enter pressed
- Automatically indents/outdents when Tab/Shift+Tab pressed

**Benefits:**
- ✅ Clean look (no bullets, just checkboxes)
- ✅ Simple plain text format
- ✅ Interactive (clickable to toggle)
- ✅ Works like bullet lists (Enter auto-continues!)
- ✅ Indenting supported (Tab/Shift+Tab)
- ✅ Works everywhere (portable to other editors)

**No trade-offs!** You get all the benefits of lists without the bullet marker.

**Technical implementation:**
- Bullet/Numbered lists: Use `QTextListFormat` (has visible markers)
- Task items: Plain text + keyboard event handling (no markers)

---

## Summary

**Choose the right list type for your needs:**

- **Bullet List** → General outlines, multi-level lists
- **Numbered List** → Sequential steps, ordered procedures
- **Task Item** → Interactive TODO lists, progress tracking

**All three support keyboard shortcuts for efficient editing!**

Enjoy your enhanced list editing experience! 🎉
