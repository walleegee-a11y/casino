# Task Item Quick Guide

## ✅ Now Works Like Bullet List!

The `[ ] Task Item` button now works **exactly like** the `[-] Bullet List` button - with automatic continuation and indenting!

---

## Quick Start

### **Step 1: Click Button**
Click `[ ] Task Item` button → inserts `[ ] `

### **Step 2: Type & Press Enter**
```
[ ] Setup database ← type this and press Enter
[ ] ← next checkbox automatically appears!
```

### **Step 3: Keep Going**
```
[ ] Setup database
[ ] Create API ← type and press Enter
[ ] Write tests ← type and press Enter
[ ] ← ready for next task
```

### **Step 4: Exit**
Press **Enter twice** on empty checkbox to stop:
```
[ ] Setup database
[ ] Create API
[ ] Write tests
← cursor here, no more checkboxes
```

### **Step 5: Mark Complete**
**Click the checkboxes** to toggle them:
```
[v] Setup database    ← clicked!
[v] Create API        ← clicked!
[ ] Write tests       ← not done
```

---

## Keyboard Shortcuts

| Key | What It Does |
|-----|--------------|
| **Enter** | Create next checkbox (auto-continues!) |
| **Enter Enter** | Exit checkbox mode |
| **Tab** | Indent checkbox (add 2 spaces) |
| **Shift+Tab** | Outdent checkbox (remove 2 spaces) |
| **Click [ ]** | Toggle to [v] (mark complete) |
| **Click [v]** | Toggle to [ ] (mark incomplete) |

---

## Example: Creating a Multi-Level TODO

**Workflow:**
```
1. Click [ ] Task Item button
2. Type "Phase 1"
3. Press Enter
4. Press Tab → indent
5. Type "Task 1.1"
6. Press Enter → next indented checkbox
7. Type "Task 1.2"
8. Press Enter
9. Press Shift+Tab → back to main level
10. Type "Phase 2"
```

**Result:**
```
[ ] Phase 1
  [ ] Task 1.1
  [ ] Task 1.2
[ ] Phase 2
```

**Mark some complete:**
```
[v] Phase 1
  [v] Task 1.1
  [v] Task 1.2
[ ] Phase 2
```

---

## Comparison: All Three List Types

| Feature | Bullet | Numbered | Task Item |
|---------|--------|----------|-----------|
| Click button once | ✓ | ✓ | ✓ |
| Press Enter to continue | ✓ | ✓ | **✓ NEW!** |
| Tab/Shift+Tab to indent | ✓ | ✓ | **✓ NEW!** |
| Press Enter twice to exit | ✓ | ✓ | **✓ NEW!** |
| Interactive (clickable) | - | - | **✓ ONLY!** |

**Task Items = Bullet Lists + Clickable Checkboxes!**

---

## Tips

1. **Fast entry:** Click button once, then just type and press Enter repeatedly
2. **No bullet markers:** Clean checkbox-only format (no • or - symbols)
3. **Click anywhere near checkbox:** Don't need to be precise - clicking around `[ ]` or `[v]` toggles it
4. **Indent anytime:** Press Tab at any point to indent the current checkbox
5. **Manual entry works:** You can also type `[ ] ` manually anywhere and it will auto-continue

---

## Common Mistake

**DON'T DO THIS (old way):**
```
Click [ ] Task Item button
Type "Task 1"
Press Enter
Click [ ] Task Item button again ← unnecessary!
Type "Task 2"
```

**DO THIS INSTEAD (new way):**
```
Click [ ] Task Item button
Type "Task 1"
Press Enter ← automatically creates next checkbox!
Type "Task 2"
Press Enter ← automatically creates next checkbox!
Type "Task 3"
```

**Much faster!**

---

## Summary

The `[ ] Task Item` button now provides the **best of both worlds**:

✅ **Ease of use** - Works like bullet lists (Enter auto-continues)
✅ **Clean appearance** - No bullet markers, just checkboxes
✅ **Interactive** - Click to toggle completion
✅ **Indenting** - Tab/Shift+Tab for hierarchy
✅ **Portable** - Plain text format works everywhere

**Perfect for tracking TODO lists and task progress!** 🎉
