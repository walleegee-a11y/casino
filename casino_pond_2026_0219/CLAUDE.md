# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**CASINO** is an Electronic Design Automation (EDA) project suite with a modular Python architecture for analyzing, visualizing, and managing design automation workflows. The codebase integrates multiple specialized tools with PyQt5 GUIs, Flask web services, and YAML-based configuration.

### Core Components

| Tool | Purpose | Entry Point | Interface |
|------|---------|-------------|-----------|
| **casino** | Main DK manager and task flow orchestrator | `casino.py` | Interactive CLI |
| **hawkeye_casino** | Run analysis and visualization engine | `hawkeye_casino.py` | PyQt5 GUI + CLI |
| **hawkeye_web_server** | REST API and web dashboard for analysis data | `hawkeye_web_server.py` | Flask (port 5021) |
| **treem_casino** | Directory and change tracking management | `treem_casino.py` | PyQt5 GUI |
| **fm_casino** | Flow/task execution with dependency resolution | `fm_casino.py` | CLI |
| **ftrack_casino** | Ftrack project tracking integration | `ftrack_casino.py` | CLI |
| **teco_casino, timer_casino, etc.** | Specialized EDA tools | Various | CLI |

## Project Structure

```
casino_pond/
├── casino.py                          # Main manager (DK/Flow)
├── hawkeye_casino.py                 # Analysis tool entry point
├── hawkeye_web_server.py             # Web server entry point
├── treem_casino.py                   # Directory management entry point
├── fm_casino.py                      # Flow/task execution
├── ftrack_casino.py                  # Ftrack integration
├── vista_casino.yaml                 # Hawkeye dashboard configuration (jobs & tasks)
├── common_casino/
│   ├── flow/flow_casino.yaml         # Task flow definitions with dependencies
│   └── globals/                      # Shared scripts (Tcl/Python for EDA tools)
├── hawkeye_casino/                   # Analysis engine package
│   ├── core/
│   │   ├── analyzer.py              # Main HawkeyeAnalyzer class
│   │   ├── file_utils.py            # File and regex-based analysis utilities
│   │   ├── keyword_parser.py        # Pattern extraction engine
│   │   ├── config.py                # YAML config loader
│   │   ├── constants.py             # Status values and enums
│   │   ├── keyword_groups.py        # Keyword categorization
│   │   └── report_table.py          # Table formatting for reports
│   ├── gui/                         # PyQt5 dashboard
│   │   ├── dashboard.py             # Main window and UI logic
│   │   ├── chart_utils.py           # Matplotlib chart generation
│   │   ├── table_utils.py           # PyQt5 table utilities
│   │   ├── dialogs.py               # UI dialogs
│   │   └── workers.py               # Background analysis threads
│   ├── workers/                     # Background task processing
│   │   └── background.py            # Worker threads
│   └── cli.py                       # CLI interface
├── hawkeye_web_server/              # Flask web application
│   ├── core/
│   │   ├── app.py                   # Flask app factory
│   │   ├── archive_manager.py       # Archive handling
│   │   └── __init__.py              # create_app() function
│   ├── routes/
│   │   ├── api.py                   # REST API endpoints
│   │   └── views.py                 # HTML template routes
│   ├── config/settings.py           # Flask configuration
│   └── templates/                   # Jinja2 HTML templates
├── treem_casino/                    # Directory management package
│   ├── ui/                          # PyQt5 UI modules
│   │   ├── main_window.py           # Main application window
│   │   ├── widgets.py               # Custom Qt widgets
│   │   ├── dialogs.py               # Dialog boxes
│   │   ├── history_widgets.py       # History view components
│   │   └── updated_dirs_widget.py   # Directory update tracking
│   ├── models/
│   │   ├── directory.py             # Directory data model
│   │   └── memo.py                  # Memo/note data model
│   ├── services/                    # Business logic
│   │   ├── directory_service.py     # Directory operations
│   │   ├── history_service.py       # History tracking
│   │   ├── memo_service.py          # Memo management
│   │   └── change_detection_service.py
│   ├── config/settings.py           # App configuration
│   └── utils/
│       ├── logger.py                # Logging setup
│       ├── tree_model.py            # Qt tree model helper
│       └── __init__.py
└── ftrack_casino/                   # Ftrack integration package
    └── [activity, analytics, attachments, database, search, themes, gui.py]
```

## Key Configuration Files

### vista_casino.yaml
Defines job configurations and STA (Static Timing Analysis) modes. Used by hawkeye_casino for:
- Job descriptions (syn_dc, apr_inn, apr_icc2, sta_pt, pex, pv, psi, etc.)
- Task mappings for each job
- STA corner and mode definitions

### flow_casino.yaml
Defines task execution flows with:
- Task name, dependencies, and priority
- Shell commands to execute (with environment sourcing)
- Subtask hierarchies for complex workflows

**Example structure:**
```yaml
tasks:
  - name: place_inn
    dependencies: [init_inn]
    command: "cd apr_inn; source all_tools_env.csh; innovus -log logs/place ..."
    priority: 1
```

## Development Commands

### Running Tools

```bash
# Main CASINO manager (interactive CLI)
python3 casino.py

# Hawkeye analysis (GUI discovery mode - recommended)
python3 hawkeye_casino.py                 # Start GUI

# Hawkeye analysis (specific run)
python3 hawkeye_casino.py -run /path/to/run -console

# Hawkeye web server (REST API + dashboard)
python3 hawkeye_web_server.py --host 0.0.0.0 --port 5021 --debug

# Treem directory management
python3 treem_casino.py

# Flow/task execution
python3 fm_casino.py -flow ./common_casino/flow/flow_casino.yaml -start init_inn -end chipfinish_inn

# List available run versions
python3 hawkeye_casino.py -list
```

### Environment Setup

The project relies on environment variables:
- `casino_prj_base` - Project base directory
- `casino_prj_name` - Project name
- `casino_pond` - CASINO tools directory (auto-detected if in path)

Environment variables are sourced from:
- Shell scripts in `common_casino/globals/`
- Project-specific `all_tools_env.csh` and `env_vars.csh`

### Testing/Verification

The project uses **Zero Script QA** methodology - testing via Docker log analysis rather than traditional test scripts. Check these files for testing patterns:
- `hawkeye_casino/core/file_utils.py` - File analysis and regex pattern testing
- `hawkeye_casino/core/analyzer.py` - Run discovery and analysis verification
- `hawkeye_casino/core/keyword_parser.py` - Keyword extraction testing

To verify code changes:
```bash
# Test individual modules
python3 -m pytest hawkeye_casino/tests/ -v

# Run linting
python3 -m pylint casino_pond/**/*.py

# Format code
python3 -m black casino_pond/
```

## Code Architecture

### Key Patterns

**1. Configuration-Driven Design**
- All job/task definitions in YAML (vista_casino.yaml, flow_casino.yaml)
- Loaded via `hawkeye_casino.core.config.load_config()`
- Reduces hardcoding and enables project portability

**2. Pattern-Based Analysis**
- Uses regex for keyword extraction from run outputs
- Pre-compiled patterns during initialization (performance optimization)
- See `hawkeye_casino.core.keyword_parser.py` for extraction logic
- Regex patterns configured in vista_casino.yaml under each task

**3. Multi-Interface Design**
Each tool supports multiple interfaces:
- **hawkeye_casino**: PyQt5 GUI (default), CLI, web server
- **treem_casino**: PyQt5 GUI (primary)
- **fm_casino**: CLI with argcomplete bash integration
- **casino.py**: Interactive menu-driven CLI

**4. Task Dependency Management**
- Flow execution respects dependency DAG (directed acyclic graph)
- `fm_casino.py` resolves dependencies before execution
- Supports parallel execution of independent tasks
- Task status tracked and can force re-execution with `-force` flag

**5. Worker Thread Architecture**
- `hawkeye_casino/gui/workers.py` - Background analysis threads
- Prevents UI blocking during long-running analyses
- Used by PyQt5 dashboard for responsive GUI

### Class Hierarchies

**HawkeyeAnalyzer** (hawkeye_casino/core/analyzer.py)
- Main analysis engine
- Methods:
  - `discover_runs()` - Find run versions in workspace
  - `analyze_run()` - Perform detailed analysis on specific run
  - `get_job_tasks()` - Retrieve task list from config
  - Pre-compiles regex patterns for performance (20-30% speedup)

**FileAnalyzer** (hawkeye_casino/core/file_utils.py)
- File content analysis utilities
- Pattern matching and keyword extraction
- Caching for performance optimization

**MainWindow** (treem_casino/ui/main_window.py)
- PyQt5 main application window
- Integrates directory tracking, memo management, history

## Common Development Tasks

### Adding a New EDA Job/Task

1. **Edit vista_casino.yaml:**
   ```yaml
   new_job:
     description: "Job description"
     tasks: ["task1", "task2"]
   ```

2. **Edit flow_casino.yaml:**
   ```yaml
   tasks:
     - name: task1
       dependencies: []
       command: "cd dir; source env; tool_command"
       priority: 1
   ```

3. **Add keyword extraction patterns** (if monitoring output):
   - Extend vista_casino.yaml or create task-specific config

### Modifying Analysis Patterns

Pattern extraction happens in `hawkeye_casino/core/keyword_parser.py`:
- Patterns compiled once in `HawkeyeAnalyzer._compile_regex_patterns()`
- Pattern definitions in vista_casino.yaml under task keywords
- Multi-line matching available via `re.MULTILINE` flag

### Updating GUI Elements

- **PyQt5 GUI updates**: Modify `hawkeye_casino/gui/` or `treem_casino/ui/`
- **Web dashboard updates**: Edit templates in `hawkeye_web_server/templates/`
- **Configuration changes**: Update `hawkeye_casino/core/config.py` or treem_casino/config/settings.py

### Adding Environment Variables

Environment variables passed to task execution in `flow_casino.yaml`:
```yaml
command: "cd dir; source env_vars.csh; source all_tools_env.csh; ..."
```

Add to appropriate `env_vars.csh` in `common_casino/globals/` subdirectories.

## Important Implementation Notes

1. **Python 3.12 Required** - All scripts use `#!/usr/local/bin/python3.12` shebang

2. **PyQt5 for GUIs** - Both hawkeye_casino and treem_casino use PyQt5:
   - Check `GUI_AVAILABLE` flag if GUI can gracefully degrade to CLI
   - hawkeye_casino.gui module: `from PyQt5.QtWidgets import ...`

3. **Configuration Loading** - Always use `load_config()` from hawkeye_casino.core.config:
   - Handles vista_casino.yaml parsing
   - Provides job/task metadata
   - Caches for performance

4. **Thread Safety** - GUI operations:
   - Use `QThread` for long-running tasks
   - Background threads in `hawkeye_casino/workers/background.py`
   - Never block main Qt event loop

5. **File Path Handling** - Use `pathlib.Path` consistently:
   - Available in hawkeye_casino/core/file_utils.py utilities
   - Cross-platform path handling (Windows/Linux)

6. **Status Tracking** - Task status defined in `hawkeye_casino/core/constants.py`:
   - Affects flow execution logic
   - Used by GUI to display run state

7. **Logging** - Structured logging with `treem_casino/utils/logger.py`:
   - Setup via `setup_logging()` call in main()
   - Used across PyQt5 and CLI tools

## Git Workflow Notes

The repository tracks:
- Python source files in `casino_pond/`
- YAML configurations in `common_casino/`
- Shared scripts in `common_casino/globals/`

Large binary artifacts (run directories, tool outputs) are typically excluded.

## Performance Considerations

1. **Regex Pattern Compilation** - Pre-compiled in `HawkeyeAnalyzer.__init__()` for 20-30% speedup
2. **File Caching** - Content cache cleared after each analysis session (`_file_cache` dict)
3. **Job Metadata Caching** - `_cached_jobs` speeds up repeated job/task lookups
4. **Discovery Mode** - `discover_runs(detailed_check=False)` for fast listing without full analysis

## Debugging Tips

- **Enable debug mode:** Add `--debug` flag to hawkeye_web_server.py
- **Console analysis:** Use `-console` flag for hawkeye_casino.py to bypass GUI
- **Pattern debugging:** Check regex patterns in vista_casino.yaml and keyword_parser.py
- **Environment issues:** Source all_tools_env.csh in flow commands to verify tool availability
