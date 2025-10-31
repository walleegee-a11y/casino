# FastTrack Project Structure

## Overview

FastTrack has been reorganized to follow a clean package structure similar to Hawkeye Casino. All functional code is now in the `ftrack_casino/` package directory, with a simple entry point file at the root.

---

## Directory Structure

```
D:\CASINO\casino_pond_ai\
│
├── ftrack_casino.py                  ← Main entry point (simple launcher)
├── ftrack_casino.py.backup           ← Backup of original monolithic file
│
├── ftrack_casino/                    ← Package directory
│   ├── __init__.py                   ← Package initialization with exports
│   ├── gui.py                        ← Main GUI application
│   ├── database.py                   ← SQLite database layer
│   ├── search.py                     ← Advanced search engine
│   ├── activity.py                   ← Activity tracking & comments
│   ├── attachments.py                ← Attachment management
│   ├── analytics.py                  ← Dashboard analytics
│   ├── export.py                     ← Multi-format export
│   └── themes.py                     ← Theme management
│
└── Documentation Files
    ├── FASTTRACK_ENHANCEMENTS.md     ← Technical documentation
    ├── FASTTRACK_QUICKSTART.md       ← User quick start guide
    ├── FASTTRACK_STRUCTURE.md        ← This file
    └── KEYBOARD_SHORTCUTS.md         ← Keyboard shortcuts reference
```

---

## File Descriptions

### Entry Point

**`ftrack_casino.py`** (25 lines)
- Simple entry point that imports and launches the application
- Similar to `hawkeye_casino.py`
- Minimal code, just a launcher

```python
from ftrack_casino import launch_ftrack
launch_ftrack()
```

---

### Package Directory: `ftrack_casino/`

#### **`__init__.py`** (~40 lines)
- Package initialization
- Exports main components for easy importing
- Version information

#### **`gui.py`** (~2,434 lines)
- Complete GUI application (FastTrackGUI class)
- All PyQt5 widgets and dialogs
- Event handlers and UI logic
- Keyboard shortcuts
- Theme management
- Filter presets UI

**Key Classes:**
- `FastTrackGUI` - Main application window
- `DragDropListWidget` - Custom drag & drop widget
- `NoEscapeDialog` - Custom dialog class

#### **`database.py`** (~250 lines)
- SQLite database layer with FTS5 search
- Issue CRUD operations
- YAML synchronization
- Query and filter methods

**Key Class:**
- `IssueDatabase` - Database manager

#### **`search.py`** (~327 lines)
- Advanced search engine
- Query language parser
- Filter presets management
- Autocomplete suggestions

**Key Classes:**
- `AdvancedSearch` - Search engine
- `FilterPresetManager` - Preset management

#### **`activity.py`** (~367 lines)
- Activity tracking system
- Comment threads
- @mention support
- Notifications

**Key Classes:**
- `ActivityTracker` - Activity logging
- `NotificationSystem` - User notifications
- `Comment` - Comment dataclass
- `ActivityEvent` - Activity dataclass

#### **`attachments.py`** (~367 lines)
- Attachment management
- SHA256 deduplication
- Thumbnail generation
- Storage statistics

**Key Class:**
- `AttachmentManager` - Attachment handler

#### **`analytics.py`** (~202 lines)
- Dashboard analytics
- Metrics and trends
- Resolution time analysis
- Distribution reports

**Key Class:**
- `IssueDashboard` - Analytics engine

#### **`export.py`** (~232 lines)
- Multi-format export
- CSV, Excel, JIRA CSV, HTML formats
- Styled output

**Key Class:**
- `IssueExporter` - Export handler

#### **`themes.py`** (~250 lines)
- Theme management
- Light and dark mode definitions
- Button styling
- Table styling

**Key Class:**
- `ThemeManager` - Theme controller

---

## Import Patterns

### From External Code

**Simple import:**
```python
from ftrack_casino import launch_ftrack

# Launch application
launch_ftrack("/path/to/project")
```

**Import specific components:**
```python
from ftrack_casino import (
    FastTrackGUI,
    IssueDatabase,
    AdvancedSearch,
    AttachmentManager
)

# Use components directly
db = IssueDatabase("issues.db")
search = AdvancedSearch(db)
```

### Within Package (Internal)

**Relative imports:**
```python
# In gui.py
from .themes import ThemeManager
from .database import IssueDatabase

# In search.py
from .database import IssueDatabase
```

---

## Benefits of New Structure

### 1. **Better Organization**
- Clear separation of concerns
- Each module has a specific purpose
- Easy to navigate codebase

### 2. **Easier Maintenance**
- Changes isolated to specific modules
- Reduced risk of breaking changes
- Clear module boundaries

### 3. **Improved Imports**
- Clean package imports
- No circular dependencies
- Explicit API in `__init__.py`

### 4. **Scalability**
- Easy to add new modules
- Can split large modules further
- Supports plugins/extensions

### 5. **Consistency with Hawkeye**
- Same structure as `hawkeye_casino/`
- Familiar pattern for developers
- Easy to maintain both projects

---

## Migration Notes

### Old Import Patterns (No longer work)

```python
# ❌ OLD - These imports no longer work
from ftrack_database import IssueDatabase
from ftrack_search import AdvancedSearch
from ftrack_themes import ThemeManager
```

### New Import Patterns

```python
# ✅ NEW - Use these patterns
from ftrack_casino import IssueDatabase, AdvancedSearch, ThemeManager

# Or import the package
import ftrack_casino
db = ftrack_casino.IssueDatabase("issues.db")
```

### Running FastTrack

**No changes needed!**

```bash
# Still works the same way
python ftrack_casino.py

# Or from another script
python -c "from ftrack_casino import launch_ftrack; launch_ftrack()"
```

---

## Comparison with Hawkeye Structure

### Hawkeye Structure
```
hawkeye_casino.py              ← Entry point
hawkeye_casino/                ← Package
    __init__.py
    gui/                       ← GUI components
    report/                    ← Report generation
    utils/                     ← Utilities
```

### FastTrack Structure (New)
```
ftrack_casino.py               ← Entry point
ftrack_casino/                 ← Package
    __init__.py
    gui.py                     ← Main GUI
    database.py                ← Database layer
    search.py                  ← Search engine
    activity.py                ← Activity tracking
    attachments.py             ← Attachments
    analytics.py               ← Analytics
    export.py                  ← Export functions
    themes.py                  ← Theme management
```

**Key Similarities:**
- Simple entry point file at root
- Package directory with `__init__.py`
- Modular organization
- Clean imports

**Key Differences:**
- FastTrack: Flat package structure (all modules at same level)
- Hawkeye: Nested structure with subdirectories
- FastTrack: More specialized modules
- Both: Single responsibility principle

---

## Development Guidelines

### Adding New Features

1. **Determine the right module**
   - GUI changes → `gui.py`
   - Database queries → `database.py`
   - Search features → `search.py`
   - Analytics → `analytics.py`
   - Export formats → `export.py`

2. **Create new module if needed**
   ```python
   # ftrack_casino/notifications.py
   class EmailNotifier:
       pass
   ```

3. **Update `__init__.py`**
   ```python
   from .notifications import EmailNotifier
   __all__ = [..., 'EmailNotifier']
   ```

### Testing

```python
# Test individual modules
from ftrack_casino.database import IssueDatabase
db = IssueDatabase(":memory:")  # In-memory testing

# Test integration
from ftrack_casino import FastTrackGUI
app = QApplication([])
window = FastTrackGUI()
```

---

## Backup Information

The original monolithic file is preserved as:
- `ftrack_casino.py.backup` (104,336 bytes)

This backup can be used for:
- Reference during migration
- Rollback if needed
- Comparison with new structure

**Note:** The backup can be safely deleted once you verify everything works correctly.

---

## Future Improvements

### Potential Subdirectories

```
ftrack_casino/
    gui/                       ← GUI components
        __init__.py
        main_window.py
        dialogs.py
        widgets.py
    data/                      ← Data layer
        __init__.py
        database.py
        models.py
    features/                  ← Features
        __init__.py
        search.py
        analytics.py
        export.py
```

### Plugin System

```python
ftrack_casino/
    plugins/
        __init__.py
        jira_integration.py
        slack_notifications.py
        git_integration.py
```

---

## Summary

The FastTrack reorganization provides:

✅ Clean package structure matching Hawkeye
✅ Better code organization and maintainability
✅ Easier imports and API usage
✅ Scalable architecture for future growth
✅ No breaking changes for end users
✅ All functionality preserved

**Total Lines of Code:** ~3,000 lines across 9 modules
**Package Size:** Moderate, easy to understand
**Maintainability:** Excellent, modular design

---

*Last Updated: 2025-01-27*
*Version: 2.0*
