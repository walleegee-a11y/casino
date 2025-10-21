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
Executes task-based design flows defined in YAML files.

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

### 3. Timer Manager (`timer_casino.py`)
PyQt5 GUI for timing analysis visualization and comparison across runs.

### 4. Hawkeye Analysis Tool
Web-based dashboard for analyzing design run results.

**Launch**:
- Via `hawkeye_casino.py` (launches web server)
- Accessible via web browser at configured port

**Architecture**:
- `hawkeye_casino/core/`: Analysis engine, configuration, file utilities
- `hawkeye_casino/gui/`: Dashboard UI, charts, tables
- `hawkeye_casino/workers/`: Background processing
- Configuration via `vista_casino.yaml` for keyword extraction and report parsing

### 5. Treem Directory Manager
Modern PyQt5 directory browser with memo system.

**Architecture**:
- `treem_casino/config/`: Application settings and themes
- `treem_casino/models/`: Data models for directories and memos
- `treem_casino/services/`: Business logic for directory/memo operations
- `treem_casino/ui/`: Main window and widget components
- `treem_casino/utils/`: Tree model and logging utilities

## Design Flow Structure

Typical flow directories under `casino_prj_base`:
```
project_root/
├── apr_inn/          # Innovus place & route
├── apr_icc2/         # ICC2 place & route (alternative)
├── pex/              # Parasitic extraction
├── sta_pt/           # PrimeTime static timing analysis
├── pv/               # Physical verification (DRC, LVS, etc.)
├── psi/              # Power/signal integrity
├── lec_fm/           # Logic equivalence checking
├── ldrc_dc/          # Logical DRC
└── common/           # Symlinked to common_casino with global scripts
```

## Common Global Scripts

Located in `common_casino/globals/`, organized by tool domain:

### Physical Design (PD)
- `pd/apr_inn/`: Innovus APR flow scripts
  - `main_scripts/`: Sequential flow TCL scripts (01_init.tcl through 07_chipfinish.tcl)
  - `mode_scripts/`: Analysis options and mode configurations
  - `PYTHON/`: Python utilities for timing analysis

### Physical Verification (PV)
- `pv/`: Calibre run scripts for DRC, LVS, antenna, ESD, etc.

### Parasitic Extraction (PEX)
- `pex/`: StarRC extraction scripts

### Power/Signal Integrity (PSI)
- `psi/`: Scripts for static/dynamic IR drop and signal EM analysis

### Physical Implementation (PI)
- `pi/sta_pt/`: PrimeTime STA scripts
- `pi/lec_fm/`: Formality LEC scripts
- `pi/ldrc_dc/`: Design Compiler logical DRC

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
