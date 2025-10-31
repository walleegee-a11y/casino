# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

CASINO is a comprehensive ASIC design flow management system that orchestrates various EDA tools and workflows for digital chip design. The system manages everything from design kit setup to physical verification, with interactive GUI tools for monitoring and analysis.

**Core Architecture**: CASINO operates as a "pond" environment where:
- A central launcher (`casino.py`) provides access to specialized manager scripts
- Manager scripts handle specific aspects of the design flow (design kit, flow execution, timing analysis, etc.)
- Common global scripts provide reusable TCL/Python code for different EDA tools
- Two major GUI applications (Hawkeye and Treem) provide visualization and analysis capabilities

## Environment Setup

CASINO relies on environment variables set via C-shell configuration files:

**Key Environment Variables** (set in `config_casino.csh`):
- `casino_pond`: Base directory for CASINO scripts and configurations
- `casino_prj_base`: Project working directory
- `casino_prj_name`: Project name
- `casino_design_ver`: Design version
- `casino_dk_ver`: Design kit version
- `casino_tag`: Project tag/identifier

**Tool Environment**: `all_tools_env.csh` sets up paths and licenses for EDA tools (Innovus, PrimeTime, Calibre, etc.)

## Key Manager Scripts

All manager scripts are Python-based and launched through `casino.py`:

### 1. Design Kit Manager (`dkm_casino.py`)
Manages design kit setup, version control, and linking.

**Common Options**:
- `-init_git`: Initialize Git repository for the project
- `-create_ver`: Create a new database version
- `-link_set <ver.make>`: Specify version make file (defines design, memory, PDK, std cells, IO, IP)
- `-link_ver <version>`: Link to a specific version

### 2. Flow Manager (`fm_casino.py`)
Executes task-based design flows defined in YAML files using DAG-based dependency resolution.

**Common Options**:
- `-start <task>`: Set starting task
- `-end <task>`: Set ending task
- `-only <subtask>`: Execute only specific subtasks
- `-force`: Force re-run of completed tasks
- `-flow <yaml_file>`: Specify flow configuration (default: `flow_casino.yaml`)
- `-singleTerm`: Execute all tasks in a single terminal
- `--interactive`: Handle interactive tasks

**Flow Configuration**: Tasks are defined in YAML files (`common_casino/flow/flow_casino.yaml` or `vista_casino.yaml`) with:
- Task names, dependencies, and priorities
- Commands to execute (typically sourcing tool environments and running TCL scripts)
- Subtasks for grouped operations (e.g., `apr_inn` includes init, place, CTS, route, etc.)

**Execution Model**:
- Uses topological sort (Kahn's algorithm) to resolve task dependencies
- Parallel execution via ThreadPoolExecutor for independent tasks
- Terminal multiplexing: Each task runs in a separate xterm/gnome-terminal window
- **Dual monitoring system**: Tracks both status files AND process trees to detect accidental terminal closures
- Status file state machine: `"" → "RUNNING" → "SUCCESS" | "FAILED" | "INTERRUPTED"`
- Completion tracking: `flow_log/completed_tasks___{range}_{execution_id}.yaml`
- Runtime history: `flow_log/runtime_history___{range}.yaml`

### 3. Timer Manager (`timer_casino.py`)
PyQt5 GUI for timing analysis visualization and comparison across runs.

### 4. Hawkeye Analysis Tool
PyQt5 desktop application for analyzing design run results (not web-based).

**Launch**:
```bash
python3.12 $casino_pond/hawkeye_casino.py
```

**Architecture**:
- `hawkeye_casino/core/`: Analysis engine, configuration, file utilities
  - `analyzer.py`: Run discovery + keyword extraction engine
  - `config.py`: YAML template expansion with variable substitution
  - `keyword_groups.py`: Dynamic grouping from vista_casino.yaml
- `hawkeye_casino/gui/`: Dashboard UI, charts, tables
  - Uses PyQt5 with custom delegates for right-aligned text elision
  - Matplotlib integration for metric plotting
- `hawkeye_casino/workers/`: Background QThread processing to prevent GUI freezes
- Configuration via `vista_casino.yaml` for keyword extraction and report parsing

**Run Discovery Pattern**:
```
{casino_prj_base}/{casino_prj_name}/works_{user}/{block}/{dk_ver_tag}/runs/{run_version}
```

**Keyword Extraction**:
- Template system uses YAML anchors and Python string formatting
- Auto-expands to 228+ keywords via Cartesian product of modes × corners × path types × metrics
- Example: `{mode}_{corner}_s_wns_{path_type}` → `misn_ff_0p99v_m40c_Cbest_s_wns_reg2reg`
- Lazy loading: "Discovery" mode finds runs quickly, "Gather Selected" analyzes on demand

### 5. Treem Directory Manager
Modern PyQt5 directory browser with memo system and terminal launch history tracking.

**Architecture** (MVC with service layer):
- `treem_casino/config/`: Application settings and themes
- `treem_casino/models/`: Data models for directories and memos
  - `directory.py`: Hierarchical tree structure with lazy metadata loading
  - `memo.py`: Annotation data model
- `treem_casino/services/`: Business logic
  - `directory_service.py`: Hierarchical scanning with `os.scandir()` optimization
  - `memo_service.py`: SQLite-backed annotation system
  - `history_service.py`: Terminal navigation tracking (JSON persistence)
  - `change_detection_service.py`: Filesystem modification monitoring
- `treem_casino/ui/`: Main window and widget components
  - Custom `QAbstractItemModel` for efficient tree rendering
  - Blinking delegate for visually highlighting updated directories
- `treem_casino/utils/`: Tree model and logging utilities

**Key Features**:
- **Lazy loading**: Only load children when directories are expanded
- **Fast mode**: Skip metadata (owner, size, mtime) during initial scan, load on demand
- **Change detection**: Visual feedback for modified/new/deleted items
- **Memo system**: Right-click to add SQLite-backed annotations
- **History tracking**: Records every terminal launch with timestamp and user

## Design Flow Structure

**Full Workspace Hierarchy** (defined in `ws_casino.hier`):
```
{casino_prj_base}/{casino_prj_name}/
├── FastTrack/                     # Quick reference links
├── outfeeds/                      # Deliverables
│   ├── {block_name}/              # Per-block outputs
│   └── ___BLK_INFO___/            # Block metadata
└── works_{user}/                  # User workspace
    └── {top_name}/                # Top-level design
        ├── {workspace_tag}/       # Workspace instance (e.g., "pi___net-0.0_dk-0.0_tag-0.0")
        │   ├── common/            # Symlink to common_casino
        │   └── runs/
        │       └── {run_ver}/     # Run version (e.g., "03_net-01_dk-02_tag-00")
        │           ├── common/    # Run-specific overrides (symlink chain)
        │           ├── apr_inn/   # Innovus APR
        │           ├── apr_icc2/  # ICC2 (alternative)
        │           ├── sta_pt/    # PrimeTime STA
        │           │   └── dmsa/  # DMSA sub-analysis
        │           ├── pex/       # Parasitic extraction
        │           ├── pv/        # Physical verification (DRC, LVS, antenna, ESD)
        │           ├── psi/       # Power/signal integrity
        │           ├── lec_fm/    # Logic equivalence checking
        │           └── ldrc_dc/   # Logical DRC
```

**Design Kit Hierarchy** (defined in `dk_casino.hier`):
```
{casino_prj_base}/dbs/
├── interface/                     # External data exchange
│   ├── from_customer/
│   ├── from_umc/
│   └── to_customer/
├── vers/                          # Version snapshots (symlinks)
│   └── {version}/                 # e.g., "v1.0"
│       ├── design → ../imported/design/{db_ver}
│       ├── std → ../imported/std/{db_ver}
│       ├── mem → ../imported/mem/{db_ver}
│       ├── pdk → ../imported/pdk/{db_ver}
│       └── io_ip → ../imported/io_ip/{db_ver}
└── imported/                      # Source libraries (category-based versioning)
    ├── design/{db_ver}/           # Design files (v, sdc, upf, def)
    ├── std/{db_ver}/              # Standard cells (lib, db, lef, gds_oas)
    ├── mem/{db_ver}/              # Memory compilers
    ├── pdk/{db_ver}/              # Process design kit (tech files, runsets, OCV)
    └── io_ip/{db_ver}/            # I/O and IP blocks
```

**Key Pattern - Hierarchical Override System**:
```
run/common → workspace/common → pond/common_casino/globals
```
Allows run-specific overrides while maintaining global defaults. Each level can override scripts from parent levels.

## Common Global Scripts

Located in `common_casino/globals/`, organized by tool domain:

### Physical Design (PD)
- `pd/apr_inn/`: Innovus APR flow scripts
  - `main_scripts/`: Sequential flow TCL (01_init.tcl → 02_place.tcl → 03_cts.tcl → 04_postcts.tcl → 05_route.tcl → 06_postroute.tcl → 07_chipfinish.tcl)
  - `mode_scripts/`: Configuration files (design_option.tcl, place_option.tcl, cts_option.tcl, route_option.tcl, analysis_option.tcl)
  - `util_scripts/`: Reusable utilities (powerplan.tcl, global_connect.tcl, vth.tcl, summary.tcl)
  - `user_scripts/`: Customization hooks (pre_place.tcl, post_place.tcl, pre_cts.tcl, post_cts.tcl, etc.)
  - `PYTHON/`: Python utilities for timing analysis

**Script Sourcing Pattern**:
```tcl
# In main scripts (e.g., 02_place.tcl):
source ../mode_scripts/design_option.tcl   # Load settings
source ../mode_scripts/place_option.tcl
source ../util_scripts/global_connect.tcl  # Utility functions
source ../user_scripts/pre_place.tcl       # User pre-hook
# ... main placement commands ...
source ../user_scripts/post_place.tcl      # User post-hook
source ../util_scripts/summary.tcl         # Report generation
```

### Physical Verification (PV)
- `pv/`: Calibre run scripts (`:RUN_GDS`, `:RUN_DRC`, `:RUN_LVS`, `:RUN_ANT`)
  - **Naming convention**: `:RUN_*` files are C-shell scripts (colon prevents accidental execution)

### Parasitic Extraction (PEX)
- `pex/`: StarRC extraction scripts

### Power/Signal Integrity (PSI)
- `psi/`: Scripts for static/dynamic IR drop and signal EM (`:RUN_STATIC`, `:RUN_DYNAMIC`, `:RUN_SIGEM`)

### Physical Implementation (PI)
- `pi/sta_pt/`: PrimeTime STA scripts (lib_setup.tcl, run_sta_pt.tcl, report_*.tcl, proc/*.tcl)
- `pi/lec_fm/`: Formality LEC scripts
- `pi/ldrc_dc/`: Design Compiler logical DRC
- `pi/syn_dc/`: Design Compiler synthesis scripts (run_syn_dc.tcl, syn_dc_setup.tcl, syn_dc_compile.tcl)

## Common Commands

### Running the Main Launcher
```bash
cd $casino_prj_base
python3.12 $casino_pond/casino.py
```
This presents an interactive menu to select which manager to run.

### Executing APR Flow
```bash
# Run full APR flow from placement to chip finishing
python3.12 $casino_pond/fm_casino.py -start place_inn -end chipfinish_inn

# Run only specific subtasks
python3.12 $casino_pond/fm_casino.py -only apr_inn

# Force re-run with custom flow
python3.12 $casino_pond/fm_casino.py -flow custom_flow.yaml -force
```

### Setting Up Design Kit
```bash
# Create new version and link design kit
python3.12 $casino_pond/dkm_casino.py -create_ver -link_set ver.make -link_ver v1.0
```

### Launching Analysis Tools
```bash
# Start Hawkeye web dashboard
python3.12 $casino_pond/hawkeye_casino.py

# Launch timing analysis GUI
python3.12 $casino_pond/timer_casino.py

# Open directory browser
python3.12 $casino_pond/treem_casino.py
```

## Analysis Configuration (vista_casino.yaml)

Defines how Hawkeye extracts metrics from log files:

**Key Sections**:
- `jobs`: Grouped tasks with descriptions
- `sta_config`: STA modes and corners for analysis
- `task_templates`: Reusable keyword/pattern definitions
- `task_mappings`: Map task names to templates with overrides

**Template System**: Uses YAML anchors and Python string formatting to generate dynamic keywords for:
- Timing metrics (WNS, TNS, violations) across modes/corners/path types
- Congestion (hotspot, overflow)
- Utilization and area
- Error/warning counts

## Development Notes

### Python Version
All scripts use Python 3.12 (`#!/usr/local/bin/python3.12`)

### Key Dependencies
- PyQt5 (GUI applications)
- PyYAML (configuration parsing)
- PrettyTable (formatted CLI output)
- pandas, matplotlib (data analysis and plotting)
- colorama (terminal colors)
- argcomplete (bash completion)

### C-shell Integration
Many scripts source C-shell environment files for EDA tool setup. Commands are executed via subprocess with `executable="/bin/csh"` or wrapped in `gnome-terminal`/`xterm` sessions.

### Flow Execution Model
The flow manager (`fm_casino.py`) implements:
- DAG-based task dependency resolution
- Parallel task execution with ThreadPoolExecutor
- Status tracking (pending/running/completed)
- Terminal multiplexing for interactive tools
- Automatic retry and error handling

### Hierarchical Configuration
Design kit hierarchies are defined in `.hier` files (e.g., `dk_casino.hier`, `ws_casino.hier`) using dash-prefixed notation to indicate directory depth.

**Hierarchy File Format**:
```
- (1 dash)  = level 1 (project root)
-- (2 dashes) = level 2 (dbs/)
--- (3 dashes) = level 3 (imported/design/std/mem/pdk/io_ip)
---- (4 dashes) = level 4 ({db_ver} placeholder directories)
```

**Variable Substitution in .hier Files**:
- `$prj` → `$casino_prj_name`
- `$whoami` → Current user (from `getpass.getuser()`)
- `$top_name` → `$casino_top_name`
- `$ws` → Workspace tag (e.g., "pi___net-0.0_dk-0.0_tag-0.0")
- `$run_ver` → Run version (e.g., "03_net-01_dk-02_tag-00")
- `$all_blks` → Space-separated block list
- `$db_ver` → Per-category version (user-provided during linking via `-link_set`)

### Category-Based Versioning (Design Kit)
Each IP category (design, std, mem, pdk, io_ip) can have independent version histories:
```bash
# Link different versions per category
python3.12 $casino_pond/dkm_casino.py -link_set ver.make -link_ver v1.0
# ver.make might specify: design=v1.5, std=v2.0, mem=v1.8, pdk=v3.2, io_ip=v2.1
```
This creates symlinks in `dbs/vers/v1.0/{category}` pointing to `dbs/imported/{category}/{db_ver}`.

## Key Architectural Patterns

### 1. Environment Variable Discovery (Launcher)
The launcher auto-discovers managers by convention:
```python
# Any env var ending in '_py' becomes a menu option
scripts = {key.replace('_py', ''): value
           for key, value in env_vars.items()
           if key.endswith('_py')}
```
Add new managers by setting `casino_new_manager_py` in `config_casino.csh`.

### 2. Dual Monitoring System (Flow Manager)
Flow manager uses two complementary methods to detect task completion:
- **Primary**: Status file write (`"" → "RUNNING" → "SUCCESS" | "FAILED" | "INTERRUPTED"`)
- **Secondary**: Process tree inspection (detects accidental terminal closure)
- **Decision**: Reconcile both sources to distinguish normal completion from zombie processes

### 3. Template Expansion with YAML Anchors (Hawkeye)
Hawkeye configuration uses YAML anchors and Python string formatting for massive keyword generation:
```yaml
task_templates:
  sta_base: &sta_base
    keywords:
      - name: "{mode}_{corner}_s_wns_{path_type}"
        pattern: "WNS.*{path_type_pattern}"

task_mappings:
  sta_pt:
    template: sta_base
    # Auto-expands via Cartesian product:
    # 3 modes × 4 corners × 5 path_types × 3 metrics = 180 keywords
```
Variables are expanded at runtime using `str.format()` with `sta_config` values.

### 4. Lazy Loading + Fast Mode (Treem)
Treem optimizes directory browsing with multi-level lazy loading:
```
Initial scan: Only directory names (os.scandir, ~10ms for 1000+ dirs)
On expand: Load immediate children
On demand: Load metadata (owner, size, mtime) via os.stat()
```
**Fast mode**: Skips metadata entirely during initial scan, loading only when needed.

### 5. Signal-Slot Asynchronous Analysis (Hawkeye)
Prevents GUI freezes during long-running analysis:
```python
worker = AnalysisWorker(runs)
worker.progress.connect(update_progress_bar)   # Real-time feedback
worker.finished.connect(populate_table)        # Completion handler
worker.error.connect(show_error_dialog)        # Error handling
worker.start()  # Non-blocking
```
Uses QThread with pyqtSignal for safe cross-thread communication.

### 6. Hierarchical Override System (Global Scripts)
Script resolution follows symlink chain with override capability:
```
run/common → workspace/common → pond/common_casino/globals
```
**Lookup order**: Check run-specific first, fall back to workspace, then to global defaults.
Allows per-run customization without modifying global templates.

### 7. Terminal Command Wrapper Pattern (Flow Manager)
Each task executes in a wrapper script that enables monitoring:
```csh
#!/usr/bin/csh -f
echo $$ > /tmp/task_pid_{task_id}.txt           # Process tracking
echo "RUNNING" > /tmp/task_status_{task_id}.txt # Status file
cd {job_dir}
source env_vars.csh
source all_tools_env.csh
{user_command}
if ($? == 0) then
    echo "SUCCESS" > /tmp/task_status_{task_id}.txt
else
    echo "FAILED" > /tmp/task_status_{task_id}.txt
endif
```
Enables parallel monitoring of multiple tasks without blocking.
