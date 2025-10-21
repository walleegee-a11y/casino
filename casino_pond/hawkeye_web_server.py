#!/usr/local/bin/python3.12
"""
Hawkeye Web Server for CASINO Project Analysis
Provides REST API and web interface for archived analysis data
"""

import os
import json
from datetime import datetime
#from flask import Flask, jsonify, request, render_template_string, send_from_directory
from flask import Flask, jsonify, request, render_template_string, send_from_directory, session, redirect, url_for

# Try to import sqlite3, but don't fail if not available
try:
    import sqlite3
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False
    print("Warning: SQLite not available. Some features may be limited.")

from hawkeye_archive import HawkeyeArchive

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management


# Initialize archive system
archive = None
available_projects = []



def discover_projects():
    """Discover available projects in casino_prj_base"""
    global available_projects

    casino_prj_base = os.getenv('casino_prj_base')
    if not casino_prj_base or not os.path.exists(casino_prj_base):
        return []

    projects = []
    try:
        for item in os.listdir(casino_prj_base):
            project_path = os.path.join(casino_prj_base, item)
            if os.path.isdir(project_path):
                # Check if hawkeye_archive exists
                archive_path = os.path.join(project_path, 'hawkeye_archive')
                has_archive = os.path.exists(archive_path)

                # Get archive statistics if available
                archive_info = {
                    'name': item,
                    'path': project_path,
                    'archive_path': archive_path,
                    'has_archive': has_archive,
                    'run_count': 0,
                    'last_updated': None
                }

                if has_archive:
                    try:
                        temp_archive = HawkeyeArchive(archive_path)
                        stats = temp_archive.get_statistics()
                        archive_info['run_count'] = stats.get('total_entries', 0)
                        # Get latest timestamp from runs
                        runs = temp_archive.get_archived_runs()
                        if runs:
                            latest = max(runs, key=lambda x: x.get('archive_timestamp', ''))
                            archive_info['last_updated'] = latest.get('archive_timestamp')
                    except Exception as e:
                        print(f"Error reading archive for {item}: {e}")

                projects.append(archive_info)
    except Exception as e:
        print(f"Error discovering projects: {e}")

    available_projects = sorted(projects, key=lambda x: x['name'])
    return available_projects

def init_archive(project_name=None):
    """Initialize archive for selected project"""
    global archive

    if project_name:
        casino_prj_base = os.getenv('casino_prj_base')
        if casino_prj_base:
            archive_path = os.path.join(casino_prj_base, project_name, 'hawkeye_archive')
            print(f"DEBUG: Looking for archive at: {archive_path}")
            print(f"DEBUG: Archive exists: {os.path.exists(archive_path)}")

            if os.path.exists(archive_path):
                try:
                    archive = HawkeyeArchive(archive_path)
                    print(f"DEBUG: Archive initialized successfully")
                    return True
                except Exception as e:
                    print(f"ERROR: Failed to initialize archive: {e}")
                    import traceback
                    traceback.print_exc()
                    return False
            else:
                print(f"ERROR: Archive path does not exist: {archive_path}")

    return False


# HTML template for the web interface
HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CASINO Hawkeye Analysis Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
            background: #f5f5f5;
            min-height: 100vh;
            padding: 10px;
            color: #333;
            font-size: 10px;
            line-height: 1.0;
        }

        .container {
            width: 100%;
            max-width: none;
            margin: 0 auto;
            background: white;
            border: 1px solid #ddd;
            overflow: visible;
        }

/* Dynamic colspan for details rows */
        .details-cell {
            /* Cell will span remaining columns automatically */
            grid-column: 1 / -1;
        }

        /* Fix for details row to span all columns */
        tr[id^="details-"] td {
            display: table-cell;
        }



        /* Responsive design for different screen sizes */
        @media (min-width: 1200px) {
            .container { max-width: 98vw; }
            body { padding: 8px; }
        }

        @media (max-width: 1199px) and (min-width: 768px) {
            .container { max-width: 99vw; }
            body { padding: 5px; }
        }

        @media (max-width: 767px) {
            .container { max-width: 100vw; margin: 0; border: none; }
            body { padding: 0; }
        }

        .header {
            background: #2c3e50;
            color: white;
            padding: 10px 15px;
            text-align: center;
            border-bottom: 1px solid #34495e;
        }

        .header h1 {
            font-size: 1.4em;
            margin-bottom: 5px;
            font-weight: normal;
        }

        .header p {
            font-size: 0.9em;
            margin: 0;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 6px;
            padding: 8px;
            background: #f8f9fa;
        }

        .stat-card {
            background: white;
            padding: 4px;
            border: 1px solid #ddd;
            text-align: center;
            line-height: 1.0;
        }

        .stat-card:hover {
            background: #f9f9f9;
        }

        .stat-content {
            font-size: 1.1em;
            font-weight: normal;
            color: #2c3e50;
            line-height: 1.0;
            font-size: 10px;
        }

        .stat-label {
            color: #666;
            font-weight: normal;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            font-size: 10px;
        }

        .stat-number {
            color: #2c3e50;
            font-weight: bold;
        }

        .tabs {
            display: flex;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }

        .tab-btn {
            padding: 2px 6px;
            background: none;
            border: none;
            cursor: pointer;
            font-size: 10px;
            color: #6c757d;
            border-bottom: 2px solid transparent;
            transition: all 0.3s ease;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        }

        .tab-btn.active {
            color: #3498db;
            border-bottom-color: #3498db;
            background: white;
        }

        .tab-btn:hover {
            color: #2980b9;
            background: rgba(52, 152, 219, 0.1);
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        .controls {
            padding: 8px 15px;
            background: white;
            border-top: 1px solid #ecf0f1;
            position: sticky;
            top: 0;
            z-index: 9999;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        /* Responsive controls and mobile optimization */
        @media (max-width: 767px) {
            .controls { padding: 10px; }
            .header { padding: 10px; }
            .header h1 { font-size: 10px; }
            .header p { font-size: 10px; }

            /* Stack search and buttons vertically on mobile */
            .controls > div:first-child {
                flex-direction: column !important;
                gap: 5px !important;
            }

            .controls input[type="text"] {
                width: 100% !important;
                flex: none !important;
            }

            .controls button {
                width: 100% !important;
                margin: 0 !important;
            }
        }

        .filter-row {
            display: flex;
            gap: 8px;
            margin-bottom: 5px;
            flex-wrap: wrap;
            position: sticky;
            top: 0;
            z-index: 10002;
            background: #f8f9fa;
            padding: 6px 10px;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .filter-group {
            flex: 1;
            min-width: 120px;
        }

        .filter-group label {
            display: block;
            margin-bottom: 3px;
            font-weight: normal;
            color: #2c3e50;
            font-size: 10px;
        }

        .filter-group input, .filter-group select {
            width: 100%;
            padding: 6px;
            border: 1px solid #ecf0f1;
            border-radius: 3px;
            font-size: 10px;
            transition: border-color 0.3s ease;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        }

        .filter-group input:focus, .filter-group select:focus {
            outline: none;
            border-color: #3498db;
        }

        /* Auto-filter dropdown styles */
        .filter-dropdown {
            position: relative;
            display: inline-block;
            width: 100%;
            z-index: 10000;
        }

        .filter-dropdown-content {
            display: none;
            position: absolute;
            background-color: white;
            min-width: 200px;
            box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
            z-index: 99999;
            max-height: 200px; /* Default height, will be adjusted dynamically */
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            top: 100%;
            left: 0;
            right: 0;
        }

        .filter-dropdown-content.show-all {
            max-height: none;
            overflow-y: visible;
        }

        .filter-dropdown-content.show {
            display: block;
        }

        .filter-dropdown.active {
            z-index: 100000;
        }

        .filter-dropdown.active .filter-dropdown-content {
            z-index: 100001;
        }

        /* Ensure filter dropdowns are not clipped by any parent containers */
        .filter-dropdown-content {
            position: absolute !important;
            z-index: 99999 !important;
        }

        .filter-dropdown.active .filter-dropdown-content {
            position: absolute !important;
            z-index: 100001 !important;
        }

        .filter-dropdown-content a {
            color: black;
            padding: 2px 6px;
            text-decoration: none;
            display: block;
            font-size: 10px;
            border-bottom: 1px solid #f0f0f0;
        }

        .filter-dropdown-content a:hover {
            background-color: #f1f1f1;
        }

        .filter-dropdown-content a.selected {
            background-color: #3498db;
            color: white;
        }

        .filter-dropdown-content .filter-search {
            padding: 2px 6px;
            border: none;
            border-bottom: 1px solid #ddd;
            width: 100%;
            box-sizing: border-box;
            font-size: 10px;
        }

        .filter-dropdown-content .filter-search:focus {
            outline: none;
            border-bottom-color: #3498db;
        }

        .filter-dropdown-content .filter-actions {
            padding: 2px 6px;
            border-top: 1px solid #ddd;
            background-color: #f8f9fa;
        }

        .filter-dropdown-content .filter-actions button {
            background: none;
            border: none;
            color: #3498db;
            cursor: pointer;
            font-size: 10px;
            margin-right: 10px;
        }

        .filter-dropdown-content .filter-actions button:hover {
            text-decoration: underline;
        }

        .filter-dropdown-content .filter-actions button.clear-all {
            color: #e74c3c;
        }

        .filter-dropdown-content .filter-actions button.select-all {
            color: #27ae60;
        }

        .filter-button {
            background: #f8f9fa;
            border: 1px solid #ddd;
            padding: 6px 8px;
            cursor: pointer;
            font-size: 10px;
            border-radius: 3px;
            width: 100%;
            text-align: left;
            position: relative;
        }

        .filter-button:hover {
            background: #e9ecef;
        }

        .filter-button::after {
            content: 'v';
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 10px;
            color: #666;
            transition: transform 0.3s ease;
        }

        .filter-button.active::after {
            transform: translateY(-50%) rotate(180deg);
        }

        .filter-button.has-filters {
            background: #3498db;
            color: white;
            border-color: #3498db;
        }

        .filter-button.has-filters::after {
            color: white;
        }

        .btn {
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            border: none;
            padding: 2px 6px;
            border-radius: 2px;
            cursor: pointer;
            font-size: 10px;
            font-weight: normal;
            transition: all 0.3s ease;
            margin-right: 3px;
            margin-bottom: 3px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        }

        .btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 3px 8px rgba(52, 152, 219, 0.4);
        }

        .btn-secondary {
            background: linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%);
        }

        .btn-success {
            background: linear-gradient(135deg, #27ae60 0%, #229954 100%);
        }

        .data-table {
            margin: 10px 0;
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 4px;
            overflow: visible;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            font-size: 10px;
            line-height: 1.0;
        }

        th, td {
            padding: 1px 2px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
            line-height: 1.0;
            height: auto;
            min-height: 12px;
        }

        th {
            background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%);
            color: white;
            font-weight: normal;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            font-size: 10px;
            padding: 8px 6px;
            border-right: 1px solid rgba(255,255,255,0.1);
            position: relative;
        }

        th:hover {
            background: linear-gradient(135deg, #2c3e50 0%, #1a252f 100%);
        }

        th[onclick] {
            cursor: pointer;
            user-select: none;
        }

        th[onclick]:active {
            transform: scale(0.98);
        }


        tr:hover {
            background: #f8f9fa;
        }

        tbody tr:nth-child(even) {
            background: #f8f9fa;
        }

        tbody tr:nth-child(odd) {
            background: white;
        }

        tbody tr:hover {
            background: #e3f2fd !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.2s ease;
        }


        td[style*="color: #2c3e50"] {
            font-weight: 500;
        }

        td[style*="color: #7f8c8d"] {
            opacity: 0.7;
            font-style: italic;
        }

        td:not(.sticky-column):not([colspan]):hover {
            background: #fff3cd !important;
            cursor: auto;
            position: relative;
            outline: 1px solid #ffc107;
        }

        /* Highlight numeric cells */
        td:not(.sticky-column):not([colspan]) {
            transition: all 0.2s ease;
        }

        .loading {
            text-align: center;
            padding: 40px 20px;
            color: #7f8c8d;
            font-style: italic;
            font-size: 10px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
        }

        .loading::before {
            content: '';
            display: block;
            width: 40px;
            height: 40px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .error {
            background: #e74c3c;
            color: white;
            padding: 8px;
            border-radius: 3px;
            margin: 10px 0;
            font-size: 10px;
        }


        .success {
            background: #27ae60;
            color: white;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }

        .footer {
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 10px;
        }

        /* Responsive table styles */
        @media (max-width: 1024px) {
            /* Reduce table text size on tablets */
            table {
                font-size: 10px;
            }

            table th, table td {
                padding: 1px 2px !important;
                min-height: 12px;
            }
        }

        @media (max-width: 767px) {
            /* Mobile table optimization */
            table {
                font-size: 10px;
                display: block;
                overflow-x: auto;
                white-space: nowrap;
            }

            table th, table td {
                padding: 1px 3px !important;
                min-width: 80px;
            }

            /* Hide less important columns on mobile */
            .mobile-hide {
                display: none;
            }

            /* Responsive comparison table */
            #comparison-section table {
                min-width: 100%;
            }

            /* Responsive search input */
            input[type="text"] {
                font-size: 16px; /* Prevents zoom on iOS */
            }

            /* Dynamic colspan for mobile */
            .details-cell {
                display: table-cell !important;
            }

            /* Mobile-friendly rotated headers */
            .rotated-header {
                writing-mode: horizontal-tb !important;
                text-orientation: initial !important;
                min-width: 60px !important;
                font-size: 10px !important;
                word-break: break-word;
            }
        }

        /* Flexible layout for wide screens */
        @media (min-width: 1400px) {
            .controls {
                padding: 20px 30px;
            }
        }

        /* Graph View Styles */
        .graph-container {
            padding: 15px;
            background: white;
        }

        .graph-canvas {
            position: relative;
            overflow: visible;
        }

        .graph-node {
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .graph-node:hover {
            stroke-width: 3px;
        }

        .graph-node.selected {
            stroke: #e74c3c;
            stroke-width: 3px;
        }

        .graph-edge {
            stroke: #bdc3c7;
            stroke-width: 1px;
            opacity: 0.6;
            transition: all 0.3s ease;
        }

        .graph-edge:hover {
            stroke: #3498db;
            stroke-width: 2px;
            opacity: 1;
        }

        .graph-edge.highlighted {
            stroke: #e74c3c;
            stroke-width: 3px;
            opacity: 1;
        }

        .graph-tooltip {
            position: absolute;
            background: rgba(44, 62, 80, 0.9);
            color: white;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            pointer-events: none;
            z-index: 1000;
            max-width: 250px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }

        .graph-legend {
            position: absolute;
            top: 10px;
            right: 10px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            font-size: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .legend-item {
            display: flex;
            align-items: center;
            margin-bottom: 5px;
        }

        .legend-color {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }

        /* Column dragging styles */
        .column-drag-handle {
            transition: all 0.2s ease;
        }

        .column-drag-handle:hover {
            color: #3498db;
            transform: scale(1.1);
        }

        th[draggable="true"] {
            cursor: move;
            transition: all 0.2s ease;
        }

        th[draggable="true"]:hover {
            background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%) !important;
        }

        th[draggable="true"]:active {
            transform: scale(0.98);
        }

        /* Handle rotated headers in transposed view */
        .rotated-header .column-drag-handle {
            transform: rotate(90deg);
            top: 50%;
            right: -10px;
            transform-origin: center;
        }

        .rotated-header .column-drag-handle:hover {
            transform: rotate(90deg) scale(1.1);
        }

        /* Ensure search and button row takes full width */
        .controls > div:first-child {
            width: 100%;
        }

        @media (max-width: 768px) {
            .filter-row {
                flex-direction: column;
            }

            .header h1 {
                font-size: 2em;
            }

            .stats-grid {
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">

        <div class="header" style="display: flex; justify-content: space-between; align-items: center; padding: 10px 20px;">
            <div>
                <h1 style="margin: 0;">CASINO Hawkeye Dashboard</h1>
                <p id="current-project-name" style="margin: 5px 0 0 0; font-size: 0.9em; opacity: 0.9;">
                    Loading... | <span id="total-runs-inline">-</span> runs | <span id="archive-size-inline">-</span> MB
                </p>
            </div>
            <button onclick="window.location.href='/select-project'"
                    class="btn btn-secondary" style="white-space: nowrap;">
                Change Project
            </button>
        </div>
        <div class="view-mode-badge" id="view-mode-indicator" style="
            position: fixed;
            top: 80px;
            right: 20px;
            background: #3498db;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: bold;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            z-index: 9998;
            display: none;
        ">
            <span id="mode-text">NORMAL VIEW</span>
        </div>

        <div class="controls">


            <div class="filter-row">
                <div class="filter-group">
                    <label for="filter-run">Run Version:</label>
                    <div class="filter-dropdown">
                        <button class="filter-button" onclick="toggleFilterDropdown('run-version')" id="filter-run-btn">
                            All Run Versions
                        </button>
                        <div class="filter-dropdown-content" id="run-version-dropdown">
                            <input type="text" class="filter-search" placeholder="Search run versions..." onkeyup="filterDropdownItems('run-version')">
                            <div id="run-version-options"></div>
                            <div class="filter-actions">
                                <button type="button" onclick="selectAllFilterOptions('run-version')" class="select-all">Select All</button>
                                <button type="button" onclick="clearAllFilterOptions('run-version')" class="clear-all">Clear All</button>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="filter-group">
                    <label for="filter-user">User:</label>
                    <div class="filter-dropdown">
                        <button class="filter-button" onclick="toggleFilterDropdown('user')" id="filter-user-btn">
                            All Users
                        </button>
                        <div class="filter-dropdown-content" id="user-dropdown">
                            <input type="text" class="filter-search" placeholder="Search users..." onkeyup="filterDropdownItems('user')">
                            <div id="user-options"></div>
                            <div class="filter-actions">
                                <button type="button" onclick="selectAllFilterOptions('user')" class="select-all">Select All</button>
                                <button type="button" onclick="clearAllFilterOptions('user')" class="clear-all">Clear All</button>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="filter-group">
                    <label for="filter-block">Block:</label>
                    <div class="filter-dropdown">
                        <button class="filter-button" onclick="toggleFilterDropdown('block')" id="filter-block-btn">
                            All Blocks
                        </button>
                        <div class="filter-dropdown-content" id="block-dropdown">
                            <input type="text" class="filter-search" placeholder="Search blocks..." onkeyup="filterDropdownItems('block')">
                            <div id="block-options"></div>
                            <div class="filter-actions">
                                <button type="button" onclick="selectAllFilterOptions('block')" class="select-all">Select All</button>
                                <button type="button" onclick="clearAllFilterOptions('block')" class="clear-all">Clear All</button>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="filter-group">
                    <label for="filter-dk">DK Ver/Tag:</label>
                    <div class="filter-dropdown">
                        <button class="filter-button" onclick="toggleFilterDropdown('dk')" id="filter-dk-btn">
                            All DK Versions
                        </button>
                        <div class="filter-dropdown-content" id="dk-dropdown">
                            <input type="text" class="filter-search" placeholder="Search DK versions..." onkeyup="filterDropdownItems('dk')">
                            <div id="dk-options"></div>
                            <div class="filter-actions">
                                <button type="button" onclick="selectAllFilterOptions('dk')" class="select-all">Select All</button>
                                <button type="button" onclick="clearAllFilterOptions('dk')" class="clear-all">Clear All</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <button class="btn" onclick="loadRuns()">Search Runs</button>
            <button class="btn btn-secondary" onclick="clearFilters()">Clear Filters</button>

            <!-- Table action buttons with search positioned on the right -->
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <label style="font-weight: normal; color: #2c3e50; font-size: 10px;">Filter Run Version:</label>
                    <input type="text" id="run-version-search" placeholder="Search run versions..."
                           style="padding: 2px 6px; border: 1px solid #ccc; border-radius: 3px; font-size: 10px; width: 150px;"
                           oninput="filterByRunVersion()">
                </div>
                <div style="display: flex; gap: 8px;">
                    <button onclick="selectAllRuns()" class="btn" style="background: #2c3e50; white-space: nowrap; font-size: 10px; padding: 4px 8px;">
                    Select All
                </button>
                <button onclick="compareSelectedRuns()" class="btn" style="background: #c0392b; white-space: nowrap; font-size: 10px; padding: 4px 8px;">
                    Compare
                </button>
                <button onclick="exportSelectedRuns()" class="btn" style="background: #2980b9; white-space: nowrap; font-size: 10px; padding: 4px 8px;">
                    Export Selected
                </button>
            </div>
        </div>

        <!-- Table View -->
        <div id="table-view" class="data-table">
            <div id="loading" class="loading">Loading data...</div>
            <div id="runs-table"></div>
        </div>

        <!-- Graph View -->
        <div id="graph-view" class="graph-container" style="display: none;">
            <div id="graph-loading" class="loading">Loading graph...</div>
            <div id="graph-controls" style="margin-bottom: 15px; display: none;">
                <button class="btn" onclick="resetGraphView()">Reset View</button>
                <button class="btn" onclick="exportGraphImage()">Export Image</button>
                <button class="btn" onclick="testGraph()" style="background: #e67e22;">Debug</button>
                <span id="graph-info" style="margin-left: 15px; color: #666; font-size: 10px;"></span>
            </div>
            <div id="graph-canvas" style="width: 100%; height: 70vh; border: 1px solid #ddd; background: #f8f9fa;"></div>
        </div>

        <!-- Comparison Section -->
        <div id="comparison-section" style="display: none; margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px;">
            <h3 style="color: #2c3e50; margin-bottom: 20px;">Keyword Comparison</h3>
            <div id="comparison-content"></div>
        </div>

        <div class="footer">
            <p>CASINO Hawkeye Analysis Dashboard - Powered by Flask & SQLite</p>
            <p>Last updated: <span id="last-update">-</span></p>
        </div>
    </div>

    <script>
        // Load statistics on page load
        document.addEventListener('DOMContentLoaded', function() {
            // Load current project name and statistics together
            Promise.all([
                fetch('/api/current-project').then(r => r.json()),
                fetch('/api/statistics').then(r => r.json())
            ]).then(([projectData, stats]) => {
                if (projectData.project) {
                    document.getElementById('current-project-name').innerHTML =
                        'Project: ' + projectData.project +
                        ' | <span id="total-runs-inline">' + stats.total_entries + '</span> runs' +
                        ' | <span id="archive-size-inline">' + stats.archive_size_mb + '</span> MB';
                }
                document.getElementById('last-update').textContent = new Date().toLocaleString();
            }).catch(error => {
                console.error('Error loading project info:', error);
            });

            loadRuns();
            initializeAutoFilters();
        });

        let allRunVersions = [];
        let allKeywords = [];
        let allRuns = [];
        let activeFilters = {
            'run-version': [],
            'user': [],
            'block': [],
            'dk': []
        };

        // Graph view variables
        let currentView = 'table';
        let graphData = null;
        let selectedNode = null;
        let graphSimulation = null;


        async function loadStatistics() {
            try {
                const response = await fetch('/api/statistics');
                const stats = await response.json();

                document.getElementById('total-runs-inline').textContent = stats.total_entries;
                document.getElementById('archive-size-inline').textContent = stats.archive_size_mb;
                document.getElementById('last-update').textContent = new Date().toLocaleString();
            } catch (error) {
                console.error('Error loading statistics:', error);
            }
        }

        async function loadRuns() {
            const loading = document.getElementById('loading');
            const table = document.getElementById('runs-table');

            loading.style.display = 'block';
            table.innerHTML = '';

            try {
                // Get all runs and keywords for filtering
                const [runsResponse, keywordsResponse] = await Promise.all([
                    fetch('/api/runs'),
                    fetch('/api/keywords')
                ]);

                allRuns = await runsResponse.json();
                originalAllRuns = [...allRuns]; // Store original copy
                allKeywords = await keywordsResponse.json();

                // Group keywords by run version
                const keywordsByRun = {};
                allKeywords.forEach(keyword => {
                    if (!keywordsByRun[keyword.run_version]) {
                        keywordsByRun[keyword.run_version] = {};
                    }
                    if (!keywordsByRun[keyword.run_version][keyword.task_name]) {
                        keywordsByRun[keyword.run_version][keyword.task_name] = [];
                    }
                    keywordsByRun[keyword.run_version][keyword.task_name].push(keyword);
                });

                // Create run versions with keyword data
                allRunVersions = allRuns.map(run => ({
                    ...run,
                    keywords: keywordsByRun[run.run_version] || {}
                }));

                // Apply auto-filters
                const filteredRuns = applyAutoFilters(allRunVersions);

                loading.style.display = 'none';

                if (filteredRuns.length === 0) {
                    table.innerHTML = '<div class="loading">No runs found matching the criteria.</div>';
                    return;
                }

                // Store filtered runs for sorting functionality
                window.filteredRuns = filteredRuns;

                // Use updateTableWithRuns to render the table consistently
                updateTableWithRuns(filteredRuns);

            } catch (error) {
                loading.style.display = 'none';
                table.innerHTML = '<div class="error">Error loading runs: ' + error.message + '</div>';
            }
        }

        async function exportCSV() {
            try {
                const response = await fetch('/api/export/csv');
                const blob = await response.blob();

                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'hawkeye_archive_export.csv';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                // Show success message
                const table = document.getElementById('runs-table');
                table.insertAdjacentHTML('beforebegin', '<div class="success">CSV export downloaded successfully!</div>');
                setTimeout(() => {
                    const successDiv = document.querySelector('.success');
                    if (successDiv) successDiv.remove();
                }, 3000);

            } catch (error) {
                const table = document.getElementById('runs-table');
                table.insertAdjacentHTML('beforebegin', '<div class="error">Export failed: ' + error.message + '</div>');
            }
        }



        function toggleRunDetails(index) {
            const detailsRow = document.getElementById(`details-${index}`);
            const toggleIcon = document.getElementById(`toggle-icon-${index}`);
            const contentDiv = document.getElementById(`details-content-${index}`);

            if (detailsRow.style.display === 'none') {
                // Show details
                detailsRow.style.display = 'table-row';
                toggleIcon.textContent = 'Hide';

                // Load details content
                const run = allRunVersions[index];
                let html = '';

                if (Object.keys(run.keywords).length === 0) {
                    html = '<p style="color: #7f8c8d; font-style: italic;">No keywords found for this run.</p>';
                } else {
                    Object.entries(run.keywords).forEach(([taskName, keywords]) => {
                        html += `
                            <div style="margin-bottom: 20px; border: 1px solid #ddd; border-radius: 6px; overflow: hidden;">
                                <div style="background: #34495e; color: white; padding: 2px 6px; font-weight: normal;">
                                    ${taskName} (${keywords.length} keywords)
                                </div>
                                <div style="padding: 10px;">
                                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 10px;">
                        `;

                        keywords.forEach(keyword => {
                            const value = keyword.keyword_value;
                            const unit = keyword.keyword_unit;
                            const displayValue = unit ? `${value} ${unit}` : value;

                            html += `
                                <div style="background: white; border: 1px solid #e0e6ed; border-radius: 4px; padding: 8px;">
                                    <div style="font-weight: normal; color: #2c3e50; margin-bottom: 4px;">${keyword.keyword_name}</div>
                                    <div style="color: #e74c3c; font-weight: normal;">${displayValue}</div>
                                </div>
                            `;
                        });

                        html += `
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                }

                contentDiv.innerHTML = html;
            } else {
                // Hide details
                detailsRow.style.display = 'none';
                toggleIcon.textContent = 'Details';
            }
        }

        // Global sorting state
        let currentSortColumn = null;
        let currentSortDirection = 'asc';

        // Add at line 1015, REPLACE entire sortTable function:
        function sortTable(column) {
            // Prevent sorting in transposed view - different structure
            if (isTransposed) {
                alert('Sorting is only available in Normal View. Please switch views to sort data.');
                return;
            }

            // Update visual indicators
            document.querySelectorAll('.sort-indicator').forEach(indicator => {
                indicator.classList.remove('sort-asc', 'sort-desc');
                indicator.innerHTML = '#';
            });

            const currentIndicator = document.getElementById(`${column}-sort`);
            if (currentSortColumn === column) {
                currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                currentSortColumn = column;
                currentSortDirection = 'asc';
            }

            // Update indicator with text symbols
            if (currentIndicator) {
                currentIndicator.classList.add(currentSortDirection === 'asc' ? 'sort-asc' : 'sort-desc');
                currentIndicator.innerHTML = currentSortDirection === 'asc' ? '^' : 'v';
            }

            // Only sort if we have valid filtered runs
            if (window.filteredRuns && window.filteredRuns.length > 0) {
                window.filteredRuns.sort((a, b) => {
                    let aVal, bVal;

                    switch (column) {
                        case 'run_version':
                            aVal = (a.run_version || '').toString();
                            bVal = (b.run_version || '').toString();
                            break;
                        case 'user_name':
                            aVal = (a.user_name || '').toString();
                            bVal = (b.user_name || '').toString();
                            break;
                        case 'block_name':
                            aVal = (a.block_name || '').toString();
                            bVal = (b.block_name || '').toString();
                            break;
                        case 'dk_ver_tag':
                            aVal = (a.dk_ver_tag || '').toString();
                            bVal = (b.dk_ver_tag || '').toString();
                            break;
                        case 'task_count':
                            aVal = Object.keys(a.keywords || {}).length;
                            bVal = Object.keys(b.keywords || {}).length;
                            break;
                        case 'keyword_count':
                            aVal = Object.values(a.keywords || {}).flat().length;
                            bVal = Object.values(b.keywords || {}).flat().length;
                            break;
                        case 'completion':
                            aVal = parseFloat(a.completion_rate || 0);
                            bVal = parseFloat(b.completion_rate || 0);
                            break;
                        case 'archive_timestamp':
                            aVal = new Date(a.archive_timestamp || 0).getTime();
                            bVal = new Date(b.archive_timestamp || 0).getTime();
                            break;
                        default:
                            return 0;
                    }

                    if (typeof aVal === 'number' && typeof bVal === 'number') {
                        return currentSortDirection === 'asc' ? aVal - bVal : bVal - aVal;
                    } else {
                        const aStr = String(aVal);
                        const bStr = String(bVal);
                        return currentSortDirection === 'asc' ?
                            aStr.localeCompare(bStr, undefined, { numeric: true, sensitivity: 'base' }) :
                            bStr.localeCompare(aStr, undefined, { numeric: true, sensitivity: 'base' });
                    }
                });

                updateTableWithRuns(window.filteredRuns);
            }
        }


        function calculateCompletionPercentage(run) {
            // This is a placeholder - implement actual completion calculation
            return 100; // For now, assume 100% complete
        }

        function filterByRunVersion() {
            const searchTerm = document.getElementById('run-version-search').value.toLowerCase().trim();

            if (!searchTerm) {
                loadRuns(); // Reload with current filters
                return;
            }

            // Start with original unfiltered data, then apply auto-filters
            let baseFiltered = applyAutoFilters([...originalAllRuns]);

            // Filter runs that match the run version search term
            const filteredRuns = baseFiltered.filter(run => {
                return run.run_version.toLowerCase().includes(searchTerm);
            });

            // Group ALL keywords by run version (not just matching ones)
            const keywordsByRun = {};
            allKeywords.forEach(keyword => {
                if (!keywordsByRun[keyword.run_version]) {
                    keywordsByRun[keyword.run_version] = {};
                }
                if (!keywordsByRun[keyword.run_version][keyword.task_name]) {
                    keywordsByRun[keyword.run_version][keyword.task_name] = [];
                }
                keywordsByRun[keyword.run_version][keyword.task_name].push(keyword);
            });

            // Add complete keyword data to filtered runs
            const filtered = filteredRuns.map(run => ({
                ...run,
                keywords: keywordsByRun[run.run_version] || {}
            }));

            // Update the table with filtered results
            updateTableWithRuns(filtered);
        }

        function updateTableWithRuns(runs) {
            const table = document.getElementById('runs-table');

            if (runs.length === 0) {
                table.innerHTML = '<div class="loading">No runs found matching the criteria.</div>';
                return;
            }

            // Store filtered runs for sorting functionality
            window.filteredRuns = runs;

            // Build table
            let html = `
                <table>
                    <thead>
                        <tr>
                            <th style="width: 4%;">
                                <input type="checkbox" id="select-all-runs-checkbox" onchange="toggleAllRuns()">
                            </th>
                            <th style="width: 6%;">Details</th>
                                <th onclick="sortTable('run_version')" style="cursor: pointer; user-select: none;" title="Click to sort by Run Version">
                                    Run Version <span id="run_version-sort" class="sort-indicator">#</span>
                                </th>
                                <th onclick="sortTable('user_name')" style="cursor: pointer; user-select: none;" title="Click to sort by User">
                                    User <span id="user_name-sort" class="sort-indicator">#</span>
                                </th>
                                <th onclick="sortTable('block_name')" style="cursor: pointer; user-select: none;" title="Click to sort by Block">
                                    Block <span id="block_name-sort" class="sort-indicator">#</span>
                                </th>
                                <th onclick="sortTable('dk_ver_tag')" style="cursor: pointer; user-select: none;" title="Click to sort by DK Ver/Tag">
                                    DK Ver/Tag <span id="dk_ver_tag-sort" class="sort-indicator">#</span>
                                </th>
                                <th onclick="sortTable('task_count')" style="cursor: pointer; user-select: none;" title="Click to sort by Tasks">
                                    Tasks <span id="task_count-sort" class="sort-indicator">#</span>
                                </th>
                                <th onclick="sortTable('keyword_count')" style="cursor: pointer; user-select: none;" title="Click to sort by Keywords">
                                    Keywords <span id="keyword_count-sort" class="sort-indicator">#</span>
                                </th>
                                <th onclick="sortTable('completion')" style="cursor: pointer; user-select: none;" title="Click to sort by Completion %">
                                    Completion % <span id="completion-sort" class="sort-indicator">#</span>
                                </th>
                                <th onclick="sortTable('archive_timestamp')" style="cursor: pointer; user-select: none;" title="Click to sort by Archived Date">
                                    Archived <span id="archive_timestamp-sort" class="sort-indicator">#</span>
                                </th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            runs.forEach((run, index) => {
                const archiveDate = new Date(run.archive_timestamp).toLocaleString('en-US', {
                    month: '2-digit',
                    day: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: false
                });
                const taskCount = Object.keys(run.keywords).length;
                const keywordCount = Object.values(run.keywords).flat().length;

                    html += `
                        <tr data-index="${index}" data-run-id="${run.run_version}">
                            <td style="text-align: center;">
                                <input type="checkbox" class="run-checkbox" data-run-id="${run.run_version}" data-run-version="${run.run_version}">
                            </td>
                        <td style="text-align: center;">
                            <button onclick="toggleRunDetails(${index})"
                                    style="padding: 2px 4px; background: #2980b9; color: white; border: 1px solid #2980b9; cursor: pointer; font-size: 10px; border-radius: 3px;">
                                <span id="toggle-icon-${index}">Details</span>
                            </button>
                        </td>
                        <td><strong>${run.run_version}</strong></td>
                        <td>${run.user_name}</td>
                        <td>${run.block_name}</td>
                        <td>${run.dk_ver_tag}</td>
                        <td style="text-align: center;"><span style="background: #27ae60; color: white; padding: 2px 6px; border-radius: 3px;">${taskCount}</span></td>
                        <td style="text-align: center;"><span style="background: #c0392b; color: white; padding: 2px 6px; border-radius: 3px;">${keywordCount}</span></td>
                        <td>${run.completion_rate}%</td>
                        <td>${archiveDate}</td>
                                                    <td>
                                <button class="btn" onclick="viewRunDetails('${run.run_version}')" style="padding: 2px 6px; font-size: 10px;">
                                    Open
                                </button>
                            </td>
                    </tr>
                    <tr id="details-${index}" style="display: none; background: #f8f9fa;">
                        <td class="details-cell" style="padding: 0;">

                            <div style="padding: 15px;">
                                <h4 style="margin: 0 0 10px 0; color: #2c3e50;">Tasks & Keywords for ${run.run_version}</h4>
                                <div id="details-content-${index}"></div>
                            </div>
                        </td>
                    </tr>
                `;
            });

            html += '</tbody></table>';
            table.innerHTML = html;
        }

        function toggleAllRuns() {
            const selectAllCheckbox = document.getElementById('select-all-runs-checkbox');
            const checkboxes = document.querySelectorAll('.run-checkbox');

            checkboxes.forEach(checkbox => {
                checkbox.checked = selectAllCheckbox.checked;
            });
        }

        function selectAllRuns() {
            const checkboxes = document.querySelectorAll('.run-checkbox');

            checkboxes.forEach(checkbox => {
                checkbox.checked = true;
            });

            document.getElementById('select-all-runs-checkbox').checked = true;
        }




        function clearFilters() {
            // Clear all auto-filters
            Object.keys(activeFilters).forEach(filterType => {
                activeFilters[filterType] = [];
            });

            // Clear search inputs
            const runVersionSearch = document.getElementById('run-version-search');
            if (runVersionSearch) {
                runVersionSearch.value = '';
            }

            // Update filter buttons
            updateFilterButtons();

            // Clear all checkboxes
            const checkboxes = document.querySelectorAll('.run-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = false;
            });
            document.getElementById('select-all-runs-checkbox').checked = false;

            // Hide comparison section if visible
            document.getElementById('comparison-section').style.display = 'none';

            // Reload runs with cleared filters
            loadRuns();
        }

        function compareSelectedRuns() {
            const checkboxes = document.querySelectorAll('.run-checkbox:checked');

            if (checkboxes.length < 2) {
                alert('Please select at least 2 run versions to compare.');
                return;
            }

            console.log('Compare button clicked, found checkboxes:', checkboxes.length);
            console.log('allRunVersions length:', allRunVersions.length);
            console.log('Active filters:', activeFilters);

            const selectedRuns = [];
            checkboxes.forEach(checkbox => {
                const runVersion = checkbox.dataset.runId; // This now contains run_version
                console.log('Looking for run with version:', runVersion);
                console.log('Available runs:', allRunVersions.map(r => r.run_version));

                const run = allRunVersions.find(r => r.run_version === runVersion);
                console.log('Selected run with version', runVersion, ':', run);
                console.log('Checkbox data attributes:', {
                    runId: checkbox.dataset.runId,
                    runVersion: checkbox.dataset.runVersion,
                    index: checkbox.dataset.index
                });

                // Ensure we have the complete run data with keywords
                if (run && run.keywords) {
                    // Verify the keywords structure
                    const taskCount = Object.keys(run.keywords).length;
                    const keywordCount = Object.values(run.keywords).flat().length;
                    console.log(`Run ${run.run_version}: ${taskCount} tasks, ${keywordCount} keywords`);

                    selectedRuns.push(run);
                } else if (!run) {
                    console.error('Run not found for version:', runVersion);
                    alert(`Warning: Run version "${runVersion}" not found in available runs.`);
                } else {
                    console.error('Run missing keywords data:', run);
                    alert(`Warning: Run ${run.run_version} has no keyword data.`);
                }
            });

            if (selectedRuns.length === 0) {
                alert('No valid runs with keyword data found for comparison.');
                return;
            }

            console.log('Selected runs for comparison:', selectedRuns);
            showComparison(selectedRuns);
        }


        function showComparison(runs) {
            console.log('=== showComparison called ===');
            console.log('Runs received:', runs.length);

            if (!runs || runs.length === 0) {
                alert('No runs selected for comparison.');
                return;
            }

            currentComparisonRuns = runs;
            isTransposed = false;

            const allKeywordNames = new Set();
            const keywordsByRun = {};  // Changed from {} to object literal

            runs.forEach(function(run) {  // Changed arrow function to regular function
                console.log('Processing run:', run.run_version);
                console.log('Run keywords structure:', run.keywords);

                keywordsByRun[run.run_version] = [];

                if (run.keywords) {
                    if (Array.isArray(run.keywords)) {
                        run.keywords.forEach(function(keyword) {
                            if (keyword && keyword.keyword_name) {
                                allKeywordNames.add(keyword.keyword_name);
                                keywordsByRun[run.run_version].push(keyword);
                            }
                        });
                    } else if (typeof run.keywords === 'object') {
                        Object.entries(run.keywords).forEach(function(entry) {
                            var taskName = entry[0];
                            var keywords = entry[1];

                            if (Array.isArray(keywords)) {
                                keywords.forEach(function(keyword) {
                                    if (keyword && keyword.keyword_name) {
                                        allKeywordNames.add(keyword.keyword_name);
                                        var keywordCopy = {};
                                        for (var key in keyword) {
                                            keywordCopy[key] = keyword[key];
                                        }
                                        keywordCopy.task_name = keyword.task_name || taskName;
                                        keywordsByRun[run.run_version].push(keywordCopy);
                                    }
                                });
                            }
                        });
                    }
                }
            });

            console.log('Total unique keywords found:', allKeywordNames.size);

            if (allKeywordNames.size === 0) {
                alert('No keywords found in the selected runs.');
                return;
            }

            var formattedRuns = runs.map(function(run) {
                var formattedRun = {
                    run_version: run.run_version,
                    user_name: run.user_name,
                    block_name: run.block_name,
                    dk_ver_tag: run.dk_ver_tag,
                    completion_rate: run.completion_rate,
                    archive_timestamp: run.archive_timestamp,
                    keywords: {}
                };

                var runKeywords = keywordsByRun[run.run_version] || [];
                runKeywords.forEach(function(keyword) {
                    var taskName = keyword.task_name || 'unknown';
                    if (!formattedRun.keywords[taskName]) {
                        formattedRun.keywords[taskName] = [];
                    }
                    formattedRun.keywords[taskName].push(keyword);
                });

                return formattedRun;
            });

            var comparisonData = {
                runs: formattedRuns,
                keywords: Array.from(allKeywordNames).sort(),
                originalKeywords: Array.from(allKeywordNames).sort(),
                isTransposed: false,
                timestamp: new Date().toISOString(),
                comparisonId: 'comparison_' + Date.now(),
                runCount: formattedRuns.length,
                keywordCount: allKeywordNames.size
            };

            console.log('Final comparison data:', comparisonData);

            try {
                var dataString = JSON.stringify(comparisonData);
                console.log('Data string length:', dataString.length);
                sessionStorage.setItem('hawkeyeComparisonData', dataString);
                console.log('Successfully stored in sessionStorage');

                var stored = sessionStorage.getItem('hawkeyeComparisonData');
                console.log('Verification - stored data exists:', !!stored);
            } catch (error) {
                console.error('Error storing in sessionStorage:', error);
                alert('Error preparing comparison data: ' + error.message);
                return;
            }

            cleanupComparisonInterface();

            var timestamp = new Date().getTime();
            var windowName = 'hawkeye_comparison_' + timestamp;

            console.log('Opening new window...');
            var newWindow = window.open(
                '/comparison-view',
                windowName,
                'width=1400,height=900,scrollbars=yes,resizable=yes,toolbar=no,menubar=no'
            );

            if (!newWindow || newWindow.closed || typeof newWindow.closed === 'undefined') {
                console.warn('Popup blocked, trying _blank');
                window.open('/comparison-view', '_blank');
            } else {
                console.log('New window opened successfully');
            }
        }


        function hideComparison() {
            document.getElementById('comparison-section').style.display = 'none';
        }

        // Keyword grouping function
        function groupKeywordsByConvention(keywords) {
            const groups = {};

            keywords.forEach(keyword => {
                let groupName = 'Other Keywords';

                // Get group from YAML configuration only
                if (keywordGroupConfig && keywordGroupConfig.tasks) {
                    for (const taskName in keywordGroupConfig.tasks) {
                        const task = keywordGroupConfig.tasks[taskName];
                        if (task.keywords) {
                            for (const keywordConfig of task.keywords) {
                                if (keywordConfig.name === keyword && keywordConfig.group) {
                                    groupName = keywordConfig.group;
                                    break;
                                }
                                if (keywordConfig.group && keyword.startsWith(keywordConfig.name + '_')) {
                                    groupName = keywordConfig.group;
                                    break;
                                }
                            }
                        }
                        if (groupName !== 'Other Keywords') break;
                    }
                }

                if (!groups[groupName]) {
                    groups[groupName] = [];
                }
                groups[groupName].push(keyword);
            });

            // Sort keywords within each group
            Object.keys(groups).forEach(group => {
                groups[group].sort();
            });

            // Sort groups
            const sortedGroups = {};
            const groupOrder = ['err/warn', 'timing', 'utilization', 'congestion', 'drc'];

            groupOrder.forEach(groupName => {
                if (groups[groupName]) {
                    sortedGroups[groupName] = groups[groupName];
                }
            });

            Object.keys(groups).sort().forEach(groupName => {
                if (!groupOrder.includes(groupName) && groupName !== 'Other Keywords') {
                    sortedGroups[groupName] = groups[groupName];
                }
            });

            if (groups['Other Keywords']) {
                sortedGroups['Other Keywords'] = groups['Other Keywords'];
            }

            return sortedGroups;
        }


        // Keyword selection functions
        function selectAllKeywords() {
            const checkboxes = document.querySelectorAll('.keyword-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = true;
            });
            updateKeywordCount();
        }

        function clearAllKeywords() {
            const checkboxes = document.querySelectorAll('.keyword-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = false;
            });
            updateKeywordCount();
        }

        function updateKeywordCount() {
            const checkboxes = document.querySelectorAll('.keyword-checkbox:checked');
            const totalKeywords = document.querySelectorAll('.keyword-checkbox').length;
            document.getElementById('selected-keyword-count').textContent = checkboxes.length;

            // Store current selection state
            if (checkboxes.length > 0) {
                window.lastSelectedKeywords = Array.from(checkboxes).map(cb => cb.value);
            }
        }

        function applyKeywordSelection() {
            const selectedKeywords = Array.from(document.querySelectorAll('.keyword-checkbox:checked'))
                .map(checkbox => checkbox.value);

            if (selectedKeywords.length === 0) {
                alert('Please select at least one keyword to compare.');
                return;
            }

            // Store selection state for future use
            window.lastSelectedKeywords = selectedKeywords;

            // Open comparison in new window/tab
            openComparisonInNewWindow(currentComparisonRuns, selectedKeywords, false);
        }

        function populateComparisonTable(selectedKeywords) {
            const tableBody = document.getElementById('comparison-table-body');
            let html = '';

            selectedKeywords.forEach(keywordName => {
                html += `
                    <tr style="border-bottom: 1px solid #ddd;">
                        <td style="padding: 2px 4px; border: 1px solid #ddd; font-weight: normal; background: #f8f9fa; position: sticky; left: 0;">${keywordName}</td>
                `;

                currentComparisonRuns.forEach(run => {
                    // Find this keyword in this run
                    let keywordValue = '-';
                    let cellStyle = 'padding: 2px 4px; border: 1px solid #ddd; text-align: center; color: #7f8c8d;';

                    Object.values(run.keywords).flat().forEach(keyword => {
                        if (keyword.keyword_name === keywordName) {
                            const unit = keyword.keyword_unit;
                            keywordValue = unit ? `${keyword.keyword_value} ${unit}` : keyword.keyword_value;
                            cellStyle = 'padding: 2px 4px; border: 1px solid #ddd; text-align: center; font-weight: normal; color: #2c3e50;';
                        }
                    });

                    html += `<td style="${cellStyle}">${keywordValue}</td>`;
                });

                html += `</tr>`;
            });

            tableBody.innerHTML = html;

            // Make columns draggable after populating
            makeColumnsDraggable();
        }

        let isTransposed = false;
        let currentComparisonRuns = [];

        function transposeTable() {
            if (currentComparisonRuns.length === 0) {
                alert('No comparison data available to transpose.');
                return;
            }

            // Get current keyword selection
            let selectedKeywords = Array.from(document.querySelectorAll('.keyword-checkbox:checked'))
                .map(checkbox => checkbox.value);

            // If no keywords selected, try to restore from stored state
            if (selectedKeywords.length === 0 && window.lastSelectedKeywords) {
                selectedKeywords = window.lastSelectedKeywords;
                // Restore checkbox states
                document.querySelectorAll('.keyword-checkbox').forEach(checkbox => {
                    checkbox.checked = selectedKeywords.includes(checkbox.value);
                });
            }

            // If still no keywords, select all
            if (selectedKeywords.length === 0) {
                selectAllKeywords();
                selectedKeywords = Array.from(document.querySelectorAll('.keyword-checkbox:checked'))
                    .map(checkbox => checkbox.value);
            }

            // Store current selection
            window.lastSelectedKeywords = selectedKeywords;

            // Open comparison in new window/tab
            openComparisonInNewWindow(currentComparisonRuns, selectedKeywords, true);
        }

        function openComparisonInNewWindow(runs, selectedKeywords, isTransposed = false) {
            // Always select all available keywords for comparison
            const allKeywords = getAllAvailableKeywords(runs);

            // Create comparison data with all keywords
            const comparisonData = {
                runs: runs,
                keywords: allKeywords,
                originalKeywords: selectedKeywords, // Keep original selection for reference
                isTransposed: isTransposed,
                timestamp: new Date().toISOString()
            };

            // Store data in sessionStorage for the new window
            sessionStorage.setItem('hawkeyeComparisonData', JSON.stringify(comparisonData));

            // Clean up any existing comparison interface in main window
            cleanupComparisonInterface();

            // Open new window with comparison
            const newWindow = window.open(
                '/comparison-view',
                'hawkeye_comparison',
                'width=1200,height=800,scrollbars=yes,resizable=yes,toolbar=no,menubar=no'
            );

            // Fallback: if popup blocked, open in new tab
            if (!newWindow || newWindow.closed || typeof newWindow.closed === 'undefined') {
                window.open('/comparison-view', '_blank');
            }
        }

        function getAllAvailableKeywords(runs) {
            const allKeywords = new Set();

            runs.forEach(run => {
                if (run.keywords) {
                    Object.values(run.keywords).flat().forEach(k => {
                        if (k.keyword_name) {
                            allKeywords.add(k.keyword_name);
                        }
                    });
                }
            });

            return Array.from(allKeywords).sort();
        }

        function cleanupComparisonInterface() {
            // Hide comparison section in main window
            const comparisonSection = document.getElementById('comparison-section');
            if (comparisonSection) {
                comparisonSection.style.display = 'none';
            }

            // Reset any comparison state
            if (window.lastSelectedKeywords) {
                delete window.lastSelectedKeywords;
            }
        }

        function showTransposedComparison(runs, selectedKeywords = null) {
            const comparisonContent = document.getElementById('comparison-content');

            // Check if comparison interface exists, if not recreate it
            if (!comparisonContent || comparisonContent.children.length === 0) {
                // Recreate the comparison interface first
                showComparison(currentComparisonRuns);
                // Then switch to transposed view
                setTimeout(() => {
                    showTransposedComparison(runs, selectedKeywords);
                }, 100);
                return;
            }

            // Use provided selectedKeywords or get from checkboxes
            if (!selectedKeywords) {
                selectedKeywords = Array.from(document.querySelectorAll('.keyword-checkbox:checked'))
                    .map(checkbox => checkbox.value);

                // If no keywords selected, try to get from previous state or select all
                if (selectedKeywords.length === 0) {
                    // Check if we have stored selection state
                    if (window.lastSelectedKeywords && window.lastSelectedKeywords.length > 0) {
                        selectedKeywords = window.lastSelectedKeywords;
                        // Restore checkbox states
                        document.querySelectorAll('.keyword-checkbox').forEach(checkbox => {
                            checkbox.checked = selectedKeywords.includes(checkbox.value);
                        });
                    } else {
                        // Fallback: select all keywords
                        selectAllKeywords();
                        selectedKeywords = Array.from(document.querySelectorAll('.keyword-checkbox:checked'))
                            .map(checkbox => checkbox.value);
                    }
                }
            }

            // Store current selection for future use
            window.lastSelectedKeywords = selectedKeywords;

            let html = `
                <div id="comparison-table-container" style="display: block;">
                    <div style="overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                            <thead>
                                <tr style="background: #34495e; color: white;">
                                    <th style="padding: 2px 4px; border: 1px solid #ddd; position: sticky; left: 0; background: #34495e;">Run Version</th>
            `;

            // Keywords as column headers (transposed view)
            selectedKeywords.forEach(keywordName => {
                html += `<th style="padding: 2px 4px; border: 1px solid #ddd; min-width: 120px; writing-mode: vertical-rl; text-orientation: mixed;" class="rotated-header">${keywordName}</th>`;
            });

            html += `
                            </tr>
                        </thead>
                        <tbody>
            `;

            // Create rows for each run
            runs.forEach(run => {
                html += `
                    <tr style="border-bottom: 1px solid #ddd;">
                        <td style="padding: 2px 4px; border: 1px solid #ddd; font-weight: normal; background: #f8f9fa; position: sticky; left: 0;">${run.run_version}</td>
                `;

                selectedKeywords.forEach(keywordName => {
                    // Find this keyword in this run
                    let keywordValue = '-';
                    let cellStyle = 'padding: 2px 4px; border: 1px solid #ddd; text-align: center; color: #7f8c8d;';

                    Object.values(run.keywords).flat().forEach(keyword => {
                        if (keyword.keyword_name === keywordName) {
                            const unit = keyword.keyword_unit;
                            keywordValue = unit ? `${keyword.keyword_value} ${unit}` : keyword.keyword_value;
                            cellStyle = 'padding: 2px 4px; border: 1px solid #ddd; text-align: center; font-weight: normal; color: #2c3e50;';
                        }
                    });

                    html += `<td style="${cellStyle}">${keywordValue}</td>`;
                });

                html += `</tr>`;
            });

            html += `
                        </tbody>
                    </table>
                </div>
                <div id="comparison-controls" style="margin-top: 15px; display: block;">
                                           <button onclick="transposeTable()"
                               style="padding: 8px 16px; background: #d35400; color: white; border: 1px solid #d35400; cursor: pointer; margin-right: 10px;">
                           Open Comparison in New Window
                       </button>
                    <button onclick="resetColumnOrder()"
                            style="padding: 8px 16px; background: #e67e22; color: white; border: 1px solid #e67e22; cursor: pointer; margin-right: 10px;">
                        Reset Column Order
                    </button>
                    <button onclick="hideComparison()"
                            style="padding: 8px 16px; background: #7f8c8d; color: white; border: 1px solid #7f8c8d; cursor: pointer;">
                        Close Comparison
                    </button>
                </div>
            `;

            comparisonContent.innerHTML = html;

            // Make columns draggable in transposed view
            makeColumnsDraggable();
        }

        function exportSelectedRuns() {
            const checkboxes = document.querySelectorAll('.run-checkbox:checked');

            if (checkboxes.length === 0) {
                alert('Please select at least one run version to export.');
                return;
            }

            console.log('Exporting selected runs:', checkboxes.length, 'checkboxes found');
            console.log('Active filters:', activeFilters);

            // Get selected runs and all available keywords
            const selectedRuns = [];
            const allKeywords = new Set();

            checkboxes.forEach(checkbox => {
                const runVersion = checkbox.dataset.runId; // This now contains run_version
                console.log('Looking for run with version:', runVersion);

                const run = allRunVersions.find(r => r.run_version === runVersion);
                if (run) {
                    console.log('Processing run:', run.run_version, 'with keywords:', Object.keys(run.keywords || {}));
                    console.log('Checkbox data attributes:', {
                        runId: checkbox.dataset.runId,
                        runVersion: checkbox.dataset.runVersion,
                        index: checkbox.dataset.index
                    });
                    selectedRuns.push(run);
                } else {
                    console.error('Run not found for version:', runVersion);
                    alert(`Warning: Run version "${runVersion}" not found in available runs.`);
                }

                // Collect all keywords from selected runs
                if (run.keywords) {
                    Object.values(run.keywords).flat().forEach(keyword => {
                        if (keyword && keyword.keyword_name) {
                            allKeywords.add(keyword.keyword_name);
                        }
                    });
                }
            });

            console.log('Total keywords found:', allKeywords.size);
            console.log('Selected runs:', selectedRuns.map(r => r.run_version));

            if (allKeywords.size === 0) {
                alert('No keywords found in selected runs. Please check if the runs have keyword data.');
                return;
            }

            // Export exactly as displayed in the main dashboard table: Keywords as rows, Runs as columns
            const sortedKeywords = Array.from(allKeywords).sort();
            console.log('Sorted keywords for export:', sortedKeywords);

            // Create TSV content matching the table display exactly
            let csvContent = 'Keyword';

            // Add run versions as headers
            selectedRuns.forEach(run => {
                csvContent += `\t${run.run_version}`;
            });
            csvContent += '\n';

            console.log('Header row created:', csvContent);

            // Add data rows (one per keyword)
            sortedKeywords.forEach(keywordName => {
                csvContent += `"${keywordName}"`;

                selectedRuns.forEach(run => {
                    let value = '--';
                    if (run.keywords) {
                        Object.values(run.keywords).flat().forEach(keyword => {
                            if (keyword && keyword.keyword_name === keywordName) {
                                value = keyword.keyword_unit ? `${keyword.keyword_value} ${keyword.keyword_unit}` : keyword.keyword_value;
                            }
                        });
                    }
                    csvContent += `\t"${value}"`;
                });

                csvContent += '\n';
            });

            console.log('Export content created, length:', csvContent.length);
            console.log('First 200 characters:', csvContent.substring(0, 200));

            // Download TSV (Tab-Separated Values)
            const blob = new Blob([csvContent], { type: 'text/tab-separated-values' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `hawkeye_main_dashboard_${new Date().toISOString().split('T')[0]}.tsv`;
            a.click();
            window.URL.revokeObjectURL(url);

            const runNames = selectedRuns.map(r => r.run_version);
            alert(`Exported ${sortedKeywords.length} keywords from ${runNames.length} runs.\\n\\nThe TSV matches exactly what you see in the main dashboard table.\\n\\nRuns: ${runNames.join(', ')}`);
        }

        async function viewRunDetails(runVersion) {
            try {
                // Find the run in allRunVersions by run_version
                const run = allRunVersions.find(r => r.run_version === runVersion);
                if (!run) {
                    alert('Run not found: ' + runVersion);
                    return;
                }

                // For now, just show the run data we already have
                const runData = run;

                // Create a new window with run details
                const newWindow = window.open('', '_blank', 'width=800,height=600');
                newWindow.document.write(`
                    <html>
                        <head>
                            <title>Run Details - ${runData.run_version || 'Unknown'}</title>
                            <style>
                                body { font-family: 'Segoe UI', sans-serif; padding: 20px; }
                                .header { background: #3498db; color: white; padding: 20px; margin: -20px -20px 20px -20px; }
                                .task { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }
                                .keyword { margin: 5px 0; padding: 5px; background: white; border-radius: 3px; }
                                pre { background: #2c3e50; color: white; padding: 15px; border-radius: 5px; overflow: auto; }
                            </style>
                        </head>
                        <body>
                            <div class="header">
                                <h1>? Run Details</h1>
                                <p>Run Version: ${runData.run_version || 'Unknown'}</p>
                            </div>
                            <pre>${JSON.stringify(runData, null, 2)}</pre>
                        </body>
                    </html>
                `);

            } catch (error) {
                alert('Error loading run details: ' + error.message);
            }
        }

        // Auto-filter functionality
        async function initializeAutoFilters() {
            try {
                const response = await fetch('/api/runs');
                const runs = await response.json();

                // Extract unique values for each filter
                const runVersions = [...new Set(runs.map(r => r.run_version).filter(Boolean))].sort();
                const users = [...new Set(runs.map(r => r.user_name).filter(Boolean))].sort();
                const blocks = [...new Set(runs.map(r => r.block_name).filter(Boolean))].sort();
                const dkVersions = [...new Set(runs.map(r => r.dk_ver_tag).filter(Boolean))].sort();

                // Populate filter options
                populateFilterOptions('run-version', runVersions);
                populateFilterOptions('user', users);
                populateFilterOptions('block', blocks);
                populateFilterOptions('dk', dkVersions);

            } catch (error) {
                console.error('Error initializing auto-filters:', error);
            }
        }

        function populateFilterOptions(filterType, options) {
            const optionsContainer = document.getElementById(`${filterType}-options`);
            if (!optionsContainer) return;

            optionsContainer.innerHTML = '';

            options.forEach(option => {
                const link = document.createElement('a');
                link.href = '#';
                link.textContent = option;
                link.onclick = (e) => {
                    e.preventDefault();
                    toggleFilterOption(filterType, option);
                };
                optionsContainer.appendChild(link);
            });

            // Apply dynamic height based on number of items
            applyDynamicDropdownHeight(filterType, options.length);
        }

        function applyDynamicDropdownHeight(filterType, itemCount) {
            const dropdown = document.getElementById(`${filterType}-dropdown`);
            if (!dropdown) return;

            // Remove any existing height classes
            dropdown.classList.remove('show-all');

            // If 10 or fewer items, show all without scrolling
            if (itemCount <= 10) {
                dropdown.classList.add('show-all');
            }
        }

        function toggleFilterDropdown(filterType) {
            const dropdown = document.getElementById(`${filterType}-dropdown`);
            const button = document.getElementById(`filter-${filterType.split('-')[0]}-btn`);
            const dropdownContainer = dropdown.closest('.filter-dropdown');

            // Close all other dropdowns
            document.querySelectorAll('.filter-dropdown-content').forEach(d => {
                if (d !== dropdown) {
                    d.classList.remove('show');
                }
            });

            // Remove active class from all dropdown containers
            document.querySelectorAll('.filter-dropdown').forEach(container => {
                container.classList.remove('active');
            });

            // Toggle current dropdown
            dropdown.classList.toggle('show');

            // Add active class to current dropdown container if open
            if (dropdown.classList.contains('show')) {
                dropdownContainer.classList.add('active');
            }

            // Update button state
            document.querySelectorAll('.filter-button').forEach(b => {
                if (b !== button) {
                    b.classList.remove('active');
                }
            });
            button.classList.toggle('active');
            // Ensure dynamic height is applied when dropdown opens
            if (dropdown.classList.contains('show')) {
                const optionsContainer = document.getElementById(`${filterType}-options`);
                if (optionsContainer) {
                    const itemCount = optionsContainer.querySelectorAll('a').length;
                    applyDynamicDropdownHeight(filterType, itemCount);
                }
            }
        }

        function filterDropdownItems(filterType) {
            const searchTerm = document.querySelector(`#${filterType}-dropdown .filter-search`).value.toLowerCase();
            let options;

            if (filterType === 'task') {
                options = document.querySelectorAll(`#${filterType}-options a`);
            } else {
                options = document.querySelectorAll(`#${filterType}-options a`);
            }

            options.forEach(option => {
                const text = option.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    option.style.display = 'block';
                } else {
                    option.style.display = 'none';
                }
            });
        }



        function toggleFilterOption(filterType, option) {
            const index = activeFilters[filterType].indexOf(option);

            if (index > -1) {
                activeFilters[filterType].splice(index, 1);
            } else {
                activeFilters[filterType].push(option);
            }

            updateFilterOptions(filterType);
            updateFilterButtons();
            loadRuns();
        }

        function updateFilterOptions(filterType) {
            const optionsContainer = document.getElementById(`${filterType}-options`);
            if (!optionsContainer) return;

            const links = optionsContainer.querySelectorAll('a');
            links.forEach(link => {
                if (activeFilters[filterType].includes(link.textContent)) {
                    link.classList.add('selected');
                } else {
                    link.classList.remove('selected');
                }
            });
        }

        function updateFilterButtons() {
            const filterTypes = ['run-version', 'user', 'block', 'dk'];
            const buttonLabels = {
                'run-version': 'Run Version',
                'user': 'User',
                'block': 'Block',
                'dk': 'DK Ver/Tag'
            };

            filterTypes.forEach(filterType => {
                const button = document.getElementById(`filter-${filterType.split('-')[0]}-btn`);
                if (!button) return;

                const filters = activeFilters[filterType];
                if (filters.length === 0) {
                    button.textContent = `All ${buttonLabels[filterType]}s`;
                    button.classList.remove('has-filters');
                } else if (filters.length === 1) {
                    button.textContent = filters[0];
                    button.classList.add('has-filters');
                } else {
                    button.textContent = `${filters.length} ${buttonLabels[filterType]}s selected`;
                    button.classList.add('has-filters');
                }
            });
        }

        function filterDropdownItems(filterType) {
            const searchInput = document.querySelector(`#${filterType}-dropdown .filter-search`);
            const searchTerm = searchInput.value.toLowerCase();
            const optionsContainer = document.getElementById(`${filterType}-options`);

            if (!optionsContainer) return;

            const links = optionsContainer.querySelectorAll('a');
            let visibleCount = 0;
            links.forEach(link => {
                const text = link.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    link.style.display = 'block';
                    visibleCount++;
                } else {
                    link.style.display = 'none';
                }
            });

            // Update dropdown height based on visible items
            applyDynamicDropdownHeight(filterType, visibleCount);
        }

        function selectAllFilterOptions(filterType) {
            const optionsContainer = document.getElementById(`${filterType}-options`);
            if (!optionsContainer) return;

            const links = optionsContainer.querySelectorAll('a');
            links.forEach(link => {
                if (link.style.display !== 'none') {
                    const option = link.textContent;
                    if (!activeFilters[filterType].includes(option)) {
                        activeFilters[filterType].push(option);
                    }
                }
            });

            updateFilterOptions(filterType);
            updateFilterButtons();
            loadRuns();
        }

        function clearAllFilterOptions(filterType) {
            activeFilters[filterType] = [];
            updateFilterOptions(filterType);
            updateFilterButtons();
            loadRuns();
        }

        function applyAutoFilters(runs) {
            return runs.filter(run => {
                // Check run version filter
                if (activeFilters['run-version'].length > 0 &&
                    !activeFilters['run-version'].includes(run.run_version)) {
                    return false;
                }

                // Check user filter
                if (activeFilters['user'].length > 0 &&
                    !activeFilters['user'].includes(run.user_name)) {
                    return false;
                }

                // Check block filter
                if (activeFilters['block'].length > 0 &&
                    !activeFilters['block'].includes(run.block_name)) {
                    return false;
                }

                // Check DK version filter
                if (activeFilters['dk'].length > 0 &&
                    !activeFilters['dk'].includes(run.dk_ver_tag)) {
                    return false;
                }

                return true;
            });
        }

        // Close dropdowns when clicking outside
        document.addEventListener('click', function(event) {
            if (!event.target.closest('.filter-dropdown')) {
                document.querySelectorAll('.filter-dropdown-content').forEach(dropdown => {
                    dropdown.classList.remove('show');
                });
                document.querySelectorAll('.filter-button').forEach(button => {
                    button.classList.remove('active');
                });
                document.querySelectorAll('.filter-dropdown').forEach(container => {
                    container.classList.remove('active');
                });
            }
        });


        async function loadGraphData() {
            const loading = document.getElementById('graph-loading');
            const controls = document.getElementById('graph-controls');

            loading.style.display = 'block';
            controls.style.display = 'none';

            try {
                // Check if D3.js is loaded and functional
                if (typeof d3 === 'undefined' || typeof d3.forceSimulation === 'undefined') {
                    console.warn('D3.js not available, will use fallback visualization');
                }

                // Get all runs and keywords
                const [runsResponse, keywordsResponse] = await Promise.all([
                    fetch('/api/runs'),
                    fetch('/api/keywords')
                ]);

                const runs = await runsResponse.json();
                const keywords = await keywordsResponse.json();

                console.log('Loaded runs:', runs.length);
                console.log('Loaded keywords:', keywords.length);

                // Process data for graph
                graphData = processGraphData(runs, keywords);

                console.log('Processed graph data:', graphData);

                loading.style.display = 'none';
                controls.style.display = 'block';

                renderGraph();

            } catch (error) {
                loading.style.display = 'none';
                console.error('Error loading graph data:', error);

                                 // Show error message in the graph canvas
                 const canvas = document.getElementById('graph-canvas');
                 canvas.innerHTML = `
                     <div style="padding: 20px; text-align: center; color: #e74c3c;">
                         <h3>Error Loading Graph</h3>
                         <p>${error.message}</p>
                         <p>Falling back to enhanced visualization mode...</p>
                         <button onclick="loadGraphData()" class="btn" style="margin-top: 10px;">Retry</button>
                     </div>
                 `;

                 // Try to render with fallback anyway
                 setTimeout(() => {
                     if (graphData) {
                         renderEnhancedFallbackGraph();
                     }
                 }, 1000);
            }
        }

        function processGraphData(runs, keywords) {
            // Group keywords by run version
            const keywordsByRun = {};
            keywords.forEach(keyword => {
                if (!keywordsByRun[keyword.run_version]) {
                    keywordsByRun[keyword.run_version] = new Set();
                }
                keywordsByRun[keyword.run_version].add(keyword.keyword_name);
            });

            // Create nodes (runs)
            const nodes = runs.map(run => ({
                id: run.run_version,
                label: run.run_version,
                user: run.user_name,
                completion: run.completion_rate,
                keywords: keywordsByRun[run.run_version] || new Set(),
                size: Math.max(10, Math.min(30, run.completion_rate / 3)),
                color: getNodeColor(run.completion_rate)
            }));

            // Create edges (shared keywords)
            const edges = [];
            const processedPairs = new Set();

            for (let i = 0; i < nodes.length; i++) {
                for (let j = i + 1; j < nodes.length; j++) {
                    const node1 = nodes[i];
                    const node2 = nodes[j];

                    // Find shared keywords
                    const sharedKeywords = new Set([...node1.keywords].filter(x => node2.keywords.has(x)));

                    if (sharedKeywords.size > 0) {
                        const pairKey = `${node1.id}-${node2.id}`;
                        if (!processedPairs.has(pairKey)) {
                            edges.push({
                                source: node1.id,
                                target: node2.id,
                                weight: sharedKeywords.size,
                                sharedKeywords: Array.from(sharedKeywords)
                            });
                            processedPairs.add(pairKey);
                        }
                    }
                }
            }

            return { nodes, edges };
        }

        function getNodeColor(completionRate) {
            if (completionRate >= 90) return '#27ae60'; // Green
            if (completionRate >= 70) return '#f39c12'; // Orange
            if (completionRate >= 50) return '#e67e22'; // Dark Orange
            return '#e74c3c'; // Red
        }

        function renderGraph() {
            if (!graphData) {
                console.error('No graph data available');
                return;
            }

            console.log('Rendering graph with data:', graphData);

            const canvas = document.getElementById('graph-canvas');
            canvas.innerHTML = '';

            // Check if D3.js is available and properly loaded
            if (typeof d3 === 'undefined' || typeof d3.forceSimulation === 'undefined' || typeof d3.select === 'undefined') {
                console.warn('D3.js not available, using enhanced fallback visualization');
                renderEnhancedFallbackGraph();
                return;
            }

            try {
                // Create SVG
                const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                svg.setAttribute('width', '100%');
                svg.setAttribute('height', '100%');
                svg.style.background = '#f8f9fa';
                canvas.appendChild(svg);

                // Add legend
                const legend = createLegend();
                canvas.appendChild(legend);

                // Create tooltip
                const tooltip = document.createElement('div');
                tooltip.className = 'graph-tooltip';
                tooltip.style.display = 'none';
                canvas.appendChild(tooltip);

                // Get canvas dimensions
                const rect = canvas.getBoundingClientRect();
                const width = rect.width;
                const height = rect.height;

                // Create force simulation
                graphSimulation = d3.forceSimulation(graphData.nodes)
                    .force('link', d3.forceLink(graphData.edges).id(d => d.id).distance(100))
                    .force('charge', d3.forceManyBody().strength(-300))
                    .force('center', d3.forceCenter(width / 2, height / 2))
                    .force('collision', d3.forceCollide().radius(d => d.size + 5));

                // Create edges
                const edges = svg.append('g')
                    .selectAll('line')
                    .data(graphData.edges)
                    .enter().append('line')
                    .attr('class', 'graph-edge')
                    .style('stroke-width', d => Math.max(1, Math.min(5, d.weight)));

                // Create nodes
                const nodes = svg.append('g')
                    .selectAll('circle')
                    .data(graphData.nodes)
                    .enter().append('circle')
                    .attr('class', 'graph-node')
                    .attr('r', d => d.size)
                    .style('fill', d => d.color)
                    .style('stroke', '#2c3e50')
                    .style('stroke-width', 2)
                    .on('mouseover', function(event, d) {
                        showTooltip(event, d);
                        d3.select(this).style('stroke-width', 3);
                    })
                    .on('mouseout', function() {
                        hideTooltip();
                        d3.select(this).style('stroke-width', 2);
                    })
                    .on('click', function(event, d) {
                        selectNode(d);
                    });

                // Add node labels
                const labels = svg.append('g')
                    .selectAll('text')
                    .data(graphData.nodes)
                    .enter().append('text')
                    .text(d => d.label.length > 15 ? d.label.substring(0, 12) + '...' : d.label)
                    .attr('text-anchor', 'middle')
                    .attr('dy', '.35em')
                    .style('font-size', '10px')
                    .style('font-weight', 'bold')
                    .style('fill', '#2c3e50')
                    .style('pointer-events', 'none');

                // Update positions on simulation tick
                graphSimulation.on('tick', () => {
                    edges
                        .attr('x1', d => d.source.x)
                        .attr('y1', d => d.source.y)
                        .attr('x2', d => d.target.x)
                        .attr('y2', d => d.target.y);

                    nodes
                        .attr('cx', d => d.x)
                        .attr('cy', d => d.y);

                    labels
                        .attr('x', d => d.x)
                        .attr('y', d => d.y);
                });

                // Update info
                updateGraphInfo();

            } catch (error) {
                console.error('Error rendering D3.js graph:', error);
                renderEnhancedFallbackGraph();
            }
        }

        function createLegend() {
            const legend = document.createElement('div');
            legend.className = 'graph-legend';
            legend.innerHTML = `
                <div style="font-weight: normal; margin-bottom: 8px;">Completion Rate</div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #27ae60;"></div>
                    <span>90-100%</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #f39c12;"></div>
                    <span>70-89%</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #e67e22;"></div>
                    <span>50-69%</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #e74c3c;"></div>
                    <span>&lt;50%</span>
                </div>
                <div style="margin-top: 8px; font-size: 10px; color: #666;">
                    Node size = completion rate<br>
                    Edge thickness = shared keywords
                </div>
            `;
            return legend;
        }

        function showTooltip(event, node) {
            const tooltip = document.querySelector('.graph-tooltip');
            const sharedKeywords = selectedNode ?
                [...node.keywords].filter(k => selectedNode.keywords.has(k)) :
                [];

            tooltip.innerHTML = `
                <div style="font-weight: normal; margin-bottom: 5px;">${node.label}</div>
                <div>User: ${node.user}</div>
                <div>Completion: ${node.completion}%</div>
                <div>Keywords: ${node.keywords.size}</div>
                ${selectedNode ? `<div style="margin-top: 5px; color: #3498db;">Shared: ${sharedKeywords.length} keywords</div>` : ''}
            `;

            tooltip.style.display = 'block';
            tooltip.style.left = event.pageX + 10 + 'px';
            tooltip.style.top = event.pageY - 10 + 'px';
        }

        function hideTooltip() {
            const tooltip = document.querySelector('.graph-tooltip');
            tooltip.style.display = 'none';
        }

        function selectNode(node) {
            if (selectedNode === node) {
                // Deselect
                selectedNode = null;
                document.querySelectorAll('.graph-node').forEach(n => n.classList.remove('selected'));
                document.querySelectorAll('.graph-edge').forEach(e => e.classList.remove('highlighted'));
            } else {
                // Select new node
                selectedNode = node;
                document.querySelectorAll('.graph-node').forEach(n => n.classList.remove('selected'));
                document.querySelectorAll('.graph-edge').forEach(e => e.classList.remove('highlighted'));

                // Highlight selected node
                document.querySelectorAll('.graph-node').forEach(n => {
                    if (n.__data__ && n.__data__.id === node.id) {
                        n.classList.add('selected');
                    }
                });

                // Highlight connected edges
                document.querySelectorAll('.graph-edge').forEach(e => {
                    if (e.__data__ && (e.__data__.source.id === node.id || e.__data__.target.id === node.id)) {
                        e.classList.add('highlighted');
                    }
                });
            }
        }

        function resetGraphView() {
            selectedNode = null;
            document.querySelectorAll('.graph-node').forEach(n => n.classList.remove('selected'));
            document.querySelectorAll('.graph-edge').forEach(e => e.classList.remove('highlighted'));
            hideTooltip();
        }

        function updateGraphInfo() {
            const info = document.getElementById('graph-info');
            if (graphData) {
                info.textContent = `${graphData.nodes.length} runs, ${graphData.edges.length} connections`;
            }
        }

                function renderEnhancedFallbackGraph() {
            const canvas = document.getElementById('graph-canvas');

            let html = `
                <div style="padding: 20px;">
                    <h3 style="color: #2c3e50; margin-bottom: 15px;">Hawkeye Graph View (Enhanced Mode)</h3>
                    <p style="color: #7f8c8d; margin-bottom: 20px;">
                        <strong>Note:</strong> Using enhanced visualization mode. All data relationships are preserved and fully functional.
                    </p>

                    <div style="margin-bottom: 20px; padding: 15px; background: #e8f4fd; border-radius: 8px; border-left: 4px solid #3498db;">
                        <h4 style="margin: 0 0 10px 0; color: #2c3e50;">Graph Information</h4>
                        <p style="margin: 5px 0; font-size: 10px;"><strong>Total Runs:</strong> ${graphData.nodes.length}</p>
                        <p style="margin: 5px 0; font-size: 10px;"><strong>Total Connections:</strong> ${graphData.edges.length}</p>
                        <p style="margin: 5px 0; font-size: 10px;"><strong>Average Connections per Run:</strong> ${(graphData.edges.length * 2 / graphData.nodes.length).toFixed(1)}</p>
                    </div>

                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 15px;">
            `;

             graphData.nodes.forEach(node => {
                 const connections = graphData.edges.filter(edge =>
                     edge.source === node.id || edge.target === node.id
                 ).length;

                 // Get connected run names and shared keywords
                 const connectedRuns = graphData.edges
                     .filter(edge => edge.source === node.id || edge.target === node.id)
                     .map(edge => {
                         const targetId = edge.source === node.id ? edge.target : edge.source;
                         const sharedKeywords = edge.sharedKeywords || [];
                         return {
                             id: targetId,
                             keywords: sharedKeywords
                         };
                     })
                     .slice(0, 3); // Show first 3 connections

                 html += `
                     <div style="border: 2px solid ${node.color}; border-radius: 8px; padding: 15px; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: all 0.3s ease;"
                          onmouseover="this.style.transform='scale(1.02)'"
                          onmouseout="this.style.transform='scale(1)'">
                         <h4 style="margin: 0 0 8px 0; color: #2c3e50; font-size: 10px;">${node.label}</h4>
                         <p style="margin: 5px 0; font-size: 10px;"><strong>User:</strong> ${node.user}</p>
                         <p style="margin: 5px 0; font-size: 10px;"><strong>Completion:</strong> <span style="color: ${node.color}; font-weight: normal;">${node.completion}%</span></p>
                         <p style="margin: 5px 0; font-size: 10px;"><strong>Keywords:</strong> ${node.keywords.size}</p>
                         <p style="margin: 5px 0; font-size: 10px;"><strong>Connections:</strong> ${connections}</p>
                         ${connectedRuns.length > 0 ? `
                             <div style="margin-top: 8px; padding: 8px; background: #f8f9fa; border-radius: 4px;">
                                 <p style="margin: 0 0 5px 0; font-size: 10px; color: #666;"><strong>Connected to:</strong></p>
                                 ${connectedRuns.map(conn => `
                                     <div style="margin: 2px 0; font-size: 10px;">
                                         <span style="color: #3498db;">${conn.id}</span>
                                         ${conn.keywords.length > 0 ? `<span style="color: #666;"> (${conn.keywords.length} shared)</span>` : ''}
                                     </div>
                                 `).join('')}
                                 ${connections > 3 ? `<p style="margin: 2px 0; font-size: 10px; color: #999;">... and ${connections - 3} more</p>` : ''}
                             </div>
                         ` : ''}
                     </div>
                 `;
             });

             html += `
                     </div>

                     <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                         <h4 style="margin: 0 0 10px 0; color: #2c3e50;">Connection Analysis</h4>
                         <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                             <div style="padding: 10px; background: white; border-radius: 4px;">
                                 <p style="margin: 0; font-size: 10px;"><strong>Most Connected:</strong> ${getMostConnectedRun()}</p>
                             </div>
                             <div style="padding: 10px; background: white; border-radius: 4px;">
                                 <p style="margin: 0; font-size: 10px;"><strong>Highest Completion:</strong> ${getHighestCompletionRun()}</p>
                             </div>
                             <div style="padding: 10px; background: white; border-radius: 4px;">
                                 <p style="margin: 0; font-size: 10px;"><strong>Most Keywords:</strong> ${getMostKeywordsRun()}</p>
                             </div>
                         </div>
                     </div>
                 </div>
             `;

             canvas.innerHTML = html;
         }

         function getMostConnectedRun() {
             const connectionCounts = {};
             graphData.edges.forEach(edge => {
                 connectionCounts[edge.source] = (connectionCounts[edge.source] || 0) + 1;
                 connectionCounts[edge.target] = (connectionCounts[edge.target] || 0) + 1;
             });
             const mostConnected = Object.entries(connectionCounts).reduce((a, b) => a[1] > b[1] ? a : b);
             return mostConnected ? mostConnected[0] : 'None';
         }

         function getHighestCompletionRun() {
             const highest = graphData.nodes.reduce((a, b) => a.completion > b.completion ? a : b);
             return highest ? `${highest.label} (${highest.completion}%)` : 'None';
         }

                 function getMostKeywordsRun() {
            const mostKeywords = graphData.nodes.reduce((a, b) => a.keywords.size > b.keywords.size ? a : b);
            return mostKeywords ? `${mostKeywords.label} (${mostKeywords.size})` : 'None';
        }

        // Column dragging functionality
        function makeColumnsDraggable() {
            const table = document.querySelector('#comparison-table-container table');
            if (!table) return;

            const headerRow = table.querySelector('thead tr');
            const headerCells = headerRow.querySelectorAll('th');

            // Drag handles removed for cleaner display
            headerCells.forEach(headerCell => {
                // Remove existing event listeners by cloning the element
                const newHeaderCell = headerCell.cloneNode(true);
                headerCell.parentNode.replaceChild(newHeaderCell, headerCell);
            });

            // Get fresh reference after cloning
            const freshHeaderCells = table.querySelectorAll('thead th');

            // Add drag handles and make headers draggable
            freshHeaderCells.forEach((headerCell, index) => {
                if (index === 0) return; // Skip the first column (Keyword/Run Version column)

                // Add drag handle
                const dragHandle = document.createElement('div');
                                    dragHandle.innerHTML = '::';
                dragHandle.style.cssText = `
                    position: absolute;
                    top: 2px;
                    right: 2px;
                    cursor: move;
                    font-size: 10px;
                    color: #666;
                    user-select: none;
                    padding: 2px;
                    z-index: 10;
                `;
                dragHandle.className = 'column-drag-handle';

                // Make header cell relative positioned for drag handle
                headerCell.style.position = 'relative';
                headerCell.appendChild(dragHandle);

                // Add drag event listeners
                headerCell.draggable = true;
                headerCell.dataset.columnIndex = index;

                headerCell.addEventListener('dragstart', handleDragStart);
                headerCell.addEventListener('dragover', handleDragOver);
                headerCell.addEventListener('drop', handleDrop);
                headerCell.addEventListener('dragenter', handleDragEnter);
                headerCell.addEventListener('dragleave', handleDragLeave);
            });
        }

        let draggedColumn = null;
        let draggedColumnIndex = null;

        function handleDragStart(e) {
            draggedColumn = e.target;
            draggedColumnIndex = parseInt(e.target.dataset.columnIndex);
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/html', e.target.outerHTML);

            // Add visual feedback
            e.target.style.opacity = '0.5';
        }

        function handleDragOver(e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
        }

        function handleDragEnter(e) {
            e.preventDefault();
            if (e.target.tagName === 'TH' && e.target !== draggedColumn) {
                e.target.style.borderLeft = '3px solid #3498db';
            }
        }

        function handleDragLeave(e) {
            if (e.target.tagName === 'TH') {
                e.target.style.borderLeft = '';
            }
        }

        function handleDrop(e) {
            e.preventDefault();

            if (e.target.tagName === 'TH' && e.target !== draggedColumn) {
                const targetColumnIndex = parseInt(e.target.dataset.columnIndex);

                // Remove visual feedback
                draggedColumn.style.opacity = '';
                e.target.style.borderLeft = '';

                // Reorder columns
                reorderColumns(draggedColumnIndex, targetColumnIndex);
            }
        }

        function reorderColumns(fromIndex, toIndex) {
            const table = document.querySelector('#comparison-table-container table');
            if (!table) return;

            const rows = table.querySelectorAll('tr');

            rows.forEach(row => {
                const cells = row.querySelectorAll('td, th');
                if (cells.length <= Math.max(fromIndex, toIndex)) return;

                // Get the cell to move
                const cellToMove = cells[fromIndex];

                if (fromIndex < toIndex) {
                    // Moving right: insert after target
                    row.insertBefore(cellToMove, cells[toIndex + 1]);
                } else {
                    // Moving left: insert before target
                    row.insertBefore(cellToMove, cells[toIndex]);
                }
            });

            // Update column indices
            updateColumnIndices();

            // Show success message
            showColumnReorderMessage(`Column moved from position ${fromIndex + 1} to ${toIndex + 1}`);
        }

        function updateColumnIndices() {
            const table = document.querySelector('#comparison-table-container table');
            if (!table) return;

            const headerCells = table.querySelectorAll('thead th');
            headerCells.forEach((headerCell, index) => {
                headerCell.dataset.columnIndex = index;
            });
        }

        function showColumnReorderMessage(message) {
            // Create or update message element
            let messageElement = document.getElementById('column-reorder-message');
            if (!messageElement) {
                messageElement = document.createElement('div');
                messageElement.id = 'column-reorder-message';
                messageElement.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #27ae60;
                    color: white;
                    padding: 10px 15px;
                    border-radius: 4px;
                    font-size: 10px;
                    z-index: 1000;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                    transition: opacity 0.3s ease;
                `;
                document.body.appendChild(messageElement);
            }

            messageElement.textContent = message;
            messageElement.style.opacity = '1';

            // Hide message after 3 seconds
            setTimeout(() => {
                messageElement.style.opacity = '0';
                setTimeout(() => {
                    if (messageElement.parentNode) {
                        messageElement.parentNode.removeChild(messageElement);
                    }
                }, 300);
            }, 3000);
        }

        function resetColumnOrder() {
            // Get current keyword selection
            let selectedKeywords = Array.from(document.querySelectorAll('.keyword-checkbox:checked'))
                .map(checkbox => checkbox.value);

            // If no keywords selected, try to restore from stored state
            if (selectedKeywords.length === 0 && window.lastSelectedKeywords) {
                selectedKeywords = window.lastSelectedKeywords;
                // Restore checkbox states
                document.querySelectorAll('.keyword-checkbox').forEach(checkbox => {
                    checkbox.checked = selectedKeywords.includes(checkbox.value);
                });
            }

            if (selectedKeywords.length > 0) {
                if (isTransposed) {
                    // Reset transposed view with current selection
                    showTransposedComparison(currentComparisonRuns, selectedKeywords);
                } else {
                    // Reset normal view with current selection
                    showComparisonTableOnly(selectedKeywords);
                }
                showColumnReorderMessage('Column order reset to original');
            } else {
                alert('No keywords selected. Please select keywords first.');
            }
        }

        function validateComparisonInterface() {
            // Check if all required elements exist
            const comparisonSection = document.getElementById('comparison-section');
            const comparisonContent = document.getElementById('comparison-content');
            const comparisonTableContainer = document.getElementById('comparison-table-container');
            const comparisonControls = document.getElementById('comparison-controls');
            const keywordCheckboxes = document.querySelectorAll('.keyword-checkbox');

            // Basic validation
            if (!comparisonSection || !comparisonContent) {
                return false;
            }

            // Check if interface has content
            if (comparisonContent.children.length === 0) {
                return false;
            }

            // Check if keyword checkboxes exist
            if (keywordCheckboxes.length === 0) {
                return false;
            }

            return true;
        }

        function showComparisonTableOnly(selectedKeywords = null) {
            // Use provided selectedKeywords or get from checkboxes
            if (!selectedKeywords) {
                selectedKeywords = Array.from(document.querySelectorAll('.keyword-checkbox:checked'))
                    .map(checkbox => checkbox.value);

                if (selectedKeywords.length === 0) {
                    // Check if we have stored selection state
                    if (window.lastSelectedKeywords && window.lastSelectedKeywords.length > 0) {
                        selectedKeywords = window.lastSelectedKeywords;
                        // Restore checkbox states
                        document.querySelectorAll('.keyword-checkbox').forEach(checkbox => {
                            checkbox.checked = selectedKeywords.includes(checkbox.value);
                        });
                    } else {
                        // Fallback: select all keywords
                        selectAllKeywords();
                        selectedKeywords = Array.from(document.querySelectorAll('.keyword-checkbox:checked'))
                            .map(checkbox => checkbox.value);
                    }
                }
            }

            // Store current selection for future use
            window.lastSelectedKeywords = selectedKeywords;

            // Ensure the comparison section is visible
            const comparisonSection = document.getElementById('comparison-section');
            if (comparisonSection.style.display === 'none') {
                comparisonSection.style.display = 'block';
            }

            // Check if comparison interface exists, if not recreate it
            const comparisonContent = document.getElementById('comparison-content');
            if (!comparisonContent || comparisonContent.children.length === 0) {
                // Recreate the comparison interface
                showComparison(currentComparisonRuns);
                return;
            }

            // Show the comparison table container and controls
            document.getElementById('comparison-table-container').style.display = 'block';
            document.getElementById('comparison-controls').style.display = 'block';

            // Populate the table with selected keywords
            populateComparisonTable(selectedKeywords);

            // Update the keyword count
            updateKeywordCount();
        }

        function exportGraphImage() {
            const canvas = document.getElementById('graph-canvas');
            html2canvas(canvas).then(canvas => {
                const link = document.createElement('a');
                link.download = `hawkeye-graph-${new Date().toISOString().split('T')[0]}.png`;
                link.href = canvas.toDataURL();
                link.click();
            });
        }

        // Test function to verify graph functionality
        function testGraph() {
            console.log('Testing graph functionality...');
            console.log('D3.js available:', typeof d3 !== 'undefined');
            console.log('Current view:', currentView);
            console.log('Graph data:', graphData);

            if (currentView === 'graph') {
                const canvas = document.getElementById('graph-canvas');
                console.log('Graph canvas:', canvas);
                console.log('Canvas content:', canvas.innerHTML);
            }
        }
    </script>

    <script>
        // Keyboard shortcuts for main dashboard
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + F: Focus search
            if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
                e.preventDefault();
                const searchInput = document.getElementById('run-version-search');
                if (searchInput) searchInput.focus();
            }

            // Ctrl/Cmd + E: Export
            if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
                e.preventDefault();
                exportCSV();
            }

            // Escape: Clear filters
            if (e.key === 'Escape') {
                const searchInput = document.getElementById('run-version-search');
                if (searchInput && searchInput.value) {
                    clearFilters();
                }
            }

            // Ctrl/Cmd + A: Select all runs
            if ((e.ctrlKey || e.metaKey) && e.key === 'a' && e.target.tagName !== 'INPUT') {
                e.preventDefault();
                selectAllRuns();
            }
        });
    </script>

    <!-- D3.js for graph visualization -->
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script>
        // Check if D3.js loaded successfully
        if (typeof d3 === 'undefined') {
            console.warn('D3.js failed to load from CDN, trying alternative source...');
            // Try alternative CDN
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js';
            script.onload = function() {
                console.log('D3.js loaded from alternative CDN');
            };
            script.onerror = function() {
                console.warn('D3.js failed to load from all CDNs, using fallback visualization');
            };
            document.head.appendChild(script);
        }
    </script>

    <!-- html2canvas for graph export -->
    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>

    <!-- Minimal D3.js fallback if CDN fails -->
    <script>
        // Create a minimal D3.js-like object if the real D3.js fails to load
        if (typeof d3 === 'undefined') {
            console.log('Creating minimal D3.js fallback');
            window.d3 = {
                forceSimulation: function(nodes) {
                    return {
                        force: function() { return this; },
                        on: function() { return this; }
                    };
                },
                forceLink: function() {
                    return {
                        id: function() { return this; },
                        distance: function() { return this; }
                    };
                },
                forceManyBody: function() {
                    return {
                        strength: function() { return this; }
                    };
                },
                forceCenter: function() { return {}; },
                forceCollide: function() {
                    return {
                        radius: function() { return this; }
                    };
                },
                select: function() {
                    return {
                        selectAll: function() {
                            return {
                                data: function() {
                                    return {
                                        enter: function() {
                                            return {
                                                append: function() {
                                                    return {
                                                        attr: function() { return this; },
                                                        style: function() { return this; },
                                                        on: function() { return this; },
                                                        text: function() { return this; }
                                                    };
                                                }
                                            };
                                        }
                                    };
                                }
                            };
                        }
                    };
                }
            };
        }
    </script>
</body>
</html>
"""

# Comparison template for new window/tab
COMPARISON_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CASINO Hawkeye Analysis Dashboard - Comparison View</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
            background: #f5f5f5;
            min-height: 100vh;
            padding: 10px;
            color: #333;
            font-size: 10px;
            line-height: 1.0;
        }

        /* Column resize cursor */
        th {
            position: relative;
            user-select: none;
        }

        .resize-handle {
            position: absolute;
            top: 0;
            right: 0;
            width: 1px;
            height: 100%;
            cursor: col-resize;
            z-index: 100;
            background: transparent;
        }

        .resize-handle:hover {
            background: rgba(52, 152, 219, 0.8);
        }

        .resize-handle::after {
            content: '';
            position: absolute;
            right: -1px;
            top: 15%;
            bottom: 15%;
            width: 1px;
            background: rgba(52, 152, 219, 0.6);
        }

        .resize-handle:hover::after {
            background: rgba(52, 152, 219, 1);
        }

        .resizing {
            cursor: col-resize !important;
            user-select: none !important;
        }

        .container {
            width: 100%;
            max-width: none;
            margin: 0 auto;
            background: white;
            border: 1px solid #ddd;
            overflow: visible;
        }

        /* Responsive design for different screen sizes */
        @media (min-width: 1200px) {
            .container { max-width: 98vw; }
            body { padding: 8px; }
        }

        @media (max-width: 1199px) and (min-width: 768px) {
            .container { max-width: 99vw; }
            body { padding: 5px; }
        }

        @media (max-width: 767px) {
            .container { max-width: 100vw; margin: 0; border: none; }
            body { padding: 0; }
        }

        .header {
            background: #2c3e50;
            color: white;
            padding: 15px;
            text-align: center;
            border-bottom: 1px solid #34495e;
        }

        .header h1 {
            font-size: 1.4em;
            margin-bottom: 5px;
            font-weight: normal;
        }

        .header p {
            font-size: 0.9em;
            margin: 0;
        }

        .controls {
            padding: 6px;
            background: #f8f9fa;
            border-bottom: 1px solid #ddd;
            display: flex;
            gap: 4px;
            position: sticky;
            top: 0;
            z-index: 9999;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            align-items: center;
            flex-wrap: wrap;
        }

        .btn {
            background: #3498db;
            color: white;
            border: none;
            padding: 2px 6px;
            border-radius: 2px;
            cursor: pointer;
            font-size: 10px;
            font-weight: normal;
            transition: all 0.3s ease;
            border: 1px solid #3498db;
        }

        .btn:hover {
            background: #2980b9;
            transform: translateY(-1px);
        }

        .btn-secondary {
            background: #95a5a6;
            border-color: #95a5a6;
        }

        .btn-secondary:hover {
            background: #7f8c8d;
        }

        .btn-success {
            background: #27ae60;
            border-color: #27ae60;
        }

        .btn-success:hover {
            background: #229954;
        }

        .btn-warning {
            background: #f39c12;
            border-color: #f39c12;
        }

        .btn-warning:hover {
            background: #e67e22;
        }

        .btn-info {
            background: #17a2b8;
            border-color: #17a2b8;
        }

        .btn-info:hover {
            background: #138496;
        }


        /* Filter system styles - matching main dashboard */
        .filter-group {
            flex: 1;
            min-width: 120px;
        }

        .filter-group label {
            display: block;
            margin-bottom: 3px;
            font-weight: normal;
            color: #2c3e50;
            font-size: 10px;
        }

        .filter-dropdown {
            position: relative;
            display: inline-block;
            width: 100%;
            z-index: 10000;
        }

        .filter-dropdown-content {
            display: none;
            position: absolute !important;
            background-color: white;
            min-width: 200px;
            box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
            z-index: 99999 !important;
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            top: 100%;
            left: 0;
            right: 0;
        }

        .filter-dropdown-content.show {
            display: block;
        }

        .filter-dropdown-content a {
            color: black;
            padding: 2px 6px;
            text-decoration: none;
            display: block;
            font-size: 10px;
            border-bottom: 1px solid #f0f0f0;
            cursor: pointer;
        }

        .filter-dropdown-content a:hover {
            background-color: #f1f1f1;
        }

        .filter-dropdown-content a.selected {
            background-color: #3498db;
            color: white;
        }

        .filter-dropdown-content .filter-search {
            padding: 2px 6px;
            border: none;
            border-bottom: 1px solid #ddd;
            width: 100%;
            box-sizing: border-box;
            font-size: 10px;
        }

        .filter-dropdown-content .filter-search:focus {
            outline: none;
            border-bottom-color: #3498db;
        }

        .filter-dropdown-content .filter-actions {
            padding: 2px 6px;
            border-top: 1px solid #ddd;
            background-color: #f8f9fa;
        }

        .filter-dropdown-content .filter-actions button {
            background: none;
            border: none;
            color: #3498db;
            cursor: pointer;
            font-size: 10px;
            margin-right: 10px;
        }

        .filter-dropdown-content .filter-actions button:hover {
            color: #2980b9;
        }

        .filter-dropdown-content .filter-actions button.select-all {
            color: #27ae60;
        }

        .filter-dropdown-content .filter-actions button.select-all:hover {
            color: #229954;
        }

        .filter-dropdown-content .filter-actions button.clear-all {
            color: #e74c3c;
        }

        .filter-dropdown-content .filter-actions button.clear-all:hover {
            color: #c0392b;
        }

        .filter-button {
            background: white;
            border: 1px solid #ecf0f1;
            border-radius: 3px;
            padding: 2px 6px;
            cursor: pointer;
            font-size: 10px;
            width: 100%;
            text-align: left;
            position: relative;
            transition: all 0.3s ease;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        }

        .filter-button:hover {
            border-color: #3498db;
            background-color: #f8f9fa;
        }

        .filter-button::after {
            content: 'v';
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 10px;
            color: #7f8c8d;
            transition: transform 0.3s ease;
        }

        .filter-button.active::after {
            transform: translateY(-50%) rotate(180deg);
        }

        .filter-button.has-filters {
            background-color: #e8f4fd;
            border-color: #3498db;
            color: #2980b9;
        }

        .filter-button.has-filters::after {
            content: 'v';
            color: #3498db;
        }


        .comparison-table {
            overflow-x: auto;
            overflow-y: auto;
            margin-top: 0;
            position: relative;
            max-height: calc(100vh - 100px);
            border: 3px solid #000;
            background: white;
            isolation: isolate;
        }

        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            background: white;
            border: none;
            margin-bottom: 0;
            position: relative;
        }

        th, td {
            padding: 1px 2px;
            text-align: left;
            border: none;              /* Remove all borders by default */
            border-right: 1px solid #f5f5f5;    /* Only right border, very light */
            border-bottom: 1px solid #f5f5f5;   /* Only bottom border, very light */
            font-size: 10px;
            line-height: 1.0;
            overflow: hidden;
            position: relative;
            height: auto;
            min-height: 12px;
        }

        th {
            background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%);
            color: white;
            font-weight: normal;
            position: sticky;
            top: 0;
            z-index: 10;
            padding: 2px 4px;
            border: 1px solid #555;    /* Override with visible borders for headers */
            border-right: 1px solid rgba(255,255,255,0.1);
        }

        /* Sticky column headers */
        th[style*="position: sticky"][style*="left"] {
            z-index: 30 !important;
            background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%);
            border: 1px solid #555;
        }

        th:hover {
            background: linear-gradient(135deg, #2c3e50 0%, #1a252f 100%);
        }

        th[onclick] {
            cursor: pointer;
            user-select: none;
        }

        th[onclick]:active {
            transform: scale(0.98);
        }

        tr:hover {
            background: #f8f9fa;
        }

        tbody tr:nth-child(even) {
            background: #f8f9fa;
        }

        tbody tr:nth-child(odd) {
            background: white;
        }

        tbody tr:hover {
            background: #e3f2fd !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.2s ease;
        }

        tbody tr {
            position: relative;
            z-index: 1;
        }

        .sticky-column {
            position: sticky;
            left: 0;
            background: #f8f9fa;
            z-index: 20;
            font-weight: normal;
            border-right: 2px solid #555 !important;  /* Strong border for sticky columns */
        }

        .sticky-column th {
            background: #34495e;
            z-index: 30;
            border: 1px solid #555;
        }

        .sticky-column::after {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            bottom: 0;
            width: 2px;
            background: linear-gradient(to bottom,
                rgba(52, 152, 219, 0) 0%,
                rgba(52, 152, 219, 0.3) 20%,
                rgba(52, 152, 219, 0.5) 50%,
                rgba(52, 152, 219, 0.3) 80%,
                rgba(52, 152, 219, 0) 100%
            );
            box-shadow: 2px 0 4px rgba(0,0,0,0.1);
        }

        td[style*="color: #2c3e50"] {
            font-weight: 500;
        }

        td[style*="color: #7f8c8d"] {
            opacity: 0.7;
            font-style: italic;
        }

        td:not(.sticky-column):not([colspan]):hover {
            background: #fff3cd !important;
            cursor: auto;
            position: relative;
            // outline: 1px solid #ffc107;
            box-shadow: inset 0 0 0 0.5px #ffc107;
        }

        td:not(.sticky-column):not([colspan]) {
            transition: all 0.2s ease;
        }

        .loading {
            text-align: center;
            padding: 40px 20px;
            color: #7f8c8d;
            font-style: italic;
            font-size: 10px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
        }

        .loading::before {
            content: '';
            display: block;
            width: 40px;
            height: 40px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .error {
            background: #e74c3c;
            color: white;
            padding: 15px;
            border-radius: 4px;
            margin: 20px;
            text-align: center;
            border: 1px solid #c0392b;
        }

        .info-panel {
            background: #e8f4fd;
            border: 1px solid #3498db;
            border-radius: 4px;
            padding: 15px;
            margin: 20px;
        }

        .info-panel h3 {
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 10px;
        }

        .info-panel p {
            margin: 5px 0;
            color: #34495e;
            font-size: 10px;
        }

        .column-drag-handle {
            cursor: move;
            color: #666;
            margin-left: 8px;
            font-size: 10px;
        }

        th[draggable="true"] {
            cursor: move;
        }

        th[draggable="true"]:hover {
            background: #2c3e50;
        }

        .rotated-header {
            writing-mode: vertical-rl;
            text-orientation: mixed;
            min-height: 120px;
            text-align: center;
        }

        .rotated-header .column-drag-handle {
            transform: rotate(90deg);
            margin-top: 10px;
        }

        .view-info {
            margin-left: auto;
            color: #666;
            font-size: 10px;
            background: #ecf0f1;
            padding: 2px 6px;
            border-radius: 4px;
            border: 1px solid #bdc3c7;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
            gap: 2px;
            padding: 4px;
            background: #f8f9fa;
            border-bottom: 1px solid #ddd;
        }

        .stat-card {
            background: white;
            padding: 2px;
            border: 1px solid #ddd;
            text-align: center;
            line-height: 1.0;
        }

        .stat-card:hover {
            background: #f9f9f9;
        }

        .stat-number {
            font-size: 10px;
            font-weight: normal;
            color: #2c3e50;
            margin-bottom: 0;
        }

        .stat-label {
            font-size: 10px;
            color: #7f8c8d;
        }

        .sort-indicator {
            font-size: 10px;
            opacity: 0.6;
            margin-left: 4px;
            font-family: monospace;
        }

        th:hover .sort-indicator {
            opacity: 1;
        }

        .sort-asc .sort-indicator::after {
            content: ' ^';
        }

        .sort-desc .sort-indicator::after {
            content: ' v';
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Hawkeye Comparison Analysis</h1>
            <p id="comparison-description">Comparison View - Loading...</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-content">
                    <span class="stat-label">Runs</span> : <span class="stat-number" id="runs-count">-</span>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-content">
                    <span class="stat-label">Keywords</span> : <span class="stat-number" id="keywords-count">-</span>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-content">
                    <span class="stat-label">Data Points</span> : <span class="stat-number" id="data-points">-</span>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-content">
                    <span class="stat-label">View Mode</span> : <span class="stat-number" id="view-type">Normal</span>
                </div>
            </div>
        </div>

        <div class="view-mode-badge" id="view-mode-indicator" style="
            position: fixed;
            top: 80px;
            right: 20px;
            background: #3498db;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: bold;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            z-index: 9998;
            display: none;
        ">
            <span id="mode-text">NORMAL VIEW</span>
        </div>

        <div class="tabs">

        <div class="controls">

            <button class="btn btn-warning" onclick="toggleView()" id="toggle-btn">
                Switch to Normal View
            </button>
            <button class="btn btn-secondary" onclick="resetColumnOrder()">
                Reset Column Order
            </button>

            <button class="btn btn-info" onclick="toggleEmptyRowsAndColumns()" id="hide-empty-btn">
                Hide Empty Rows and Columns
            </button>
            <button class="btn btn-success" onclick="exportComparison()">
                Export CSV
            </button>

            <button class="btn btn-secondary" onclick="window.close()">
                Close Window
            </button>
            <div class="view-info" id="view-info">
                Loading comparison data...
            </div>
        </div>

        <div class="keyword-filter-section" style="padding: 8px; background: #ecf0f1; border-bottom: 1px solid #ddd;">
                    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <label style="font-weight: normal; color: #2c3e50; font-size: 10px;">Run Version:</label>
                            <input type="text" id="comparison-search" placeholder="Search run versions..."
                                   style="flex: 1; min-width: 200px; padding: 2px 6px; border: 1px solid #ccc; border-radius: 3px; font-size: 10px;">
                        </div>
                        <div style="display: flex; align-items: center; gap: 4px;">
                            <button id="sort-toggle-btn" onclick="toggleRunVersionSort()" style="padding: 4px 8px; border: 1px solid #ccc; border-radius: 3px; font-size: 10px; background: white; cursor: pointer;" title="Click to toggle Run Version sort">
                                Run Version: A -> Z
                            </button>
                        </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <label for="keyword-search" style="font-weight: normal; color: #2c3e50; font-size: 10px;">Filter Keywords:</label>
                    <input type="text" id="keyword-search" placeholder="Type to filter keywords..."
                           style="padding: 4px 8px; border: 1px solid #bdc3c7; border-radius: 3px; font-size: 10px; width: 180px;">
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <label for="filter-group" style="font-weight: normal; color: #2c3e50; font-size: 10px;">Group:</label>
                    <div class="filter-dropdown" style="min-width: 200px;">
                        <button class="filter-button" onclick="toggleFilterDropdown('group')" id="filter-group-btn">
                            All Groups
                        </button>
                        <div class="filter-dropdown-content" id="group-dropdown">
                            <input type="text" class="filter-search" placeholder="Search groups..." onkeyup="filterDropdownItems('group')">
                            <div id="group-options"></div>
                            <div class="filter-actions">
                                <button type="button" onclick="selectAllFilterOptions('group')" class="select-all">Select All</button>
                                <button type="button" onclick="clearAllFilterOptions('group')" class="clear-all">Clear All</button>
                            </div>
                        </div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <label for="task-filter" style="font-weight: normal; color: #2c3e50; font-size: 10px;">Task:</label>
                    <div class="filter-dropdown" style="min-width: 200px;">
                        <button class="filter-button" onclick="toggleFilterDropdown('task')" id="filter-task-btn">
                            All Tasks
                        </button>
                        <div class="filter-dropdown-content" id="task-dropdown">
                            <input type="text" class="filter-search" placeholder="Search tasks..." onkeyup="filterDropdownItems('task')">
                            <div id="task-options"></div>
                            <div class="filter-actions">
                                <button type="button" onclick="selectAllTaskOptions()" class="select-all">Select All</button>
                                <button type="button" onclick="clearAllTaskOptions()" class="clear-all">Clear All</button>
                            </div>
                        </div>
                    </div>
                </div>
                <button class="btn btn-secondary" onclick="clearKeywordFilters()" style="padding: 4px 8px; font-size: 10px;">
                    Clear Filters
                </button>
                <div style="margin-left: auto; color: #666; font-size: 10px;">
                    <span id="filtered-keywords-count">-</span> keywords shown |
                    <span id="filtered-tasks-count">-</span> tasks shown
                </div>
            </div>
        </div>

        <div class="comparison-table">
            <div id="loading" class="loading">Loading comparison data...</div>
            <div id="comparison-content" style="display: none;"></div>
        </div>
    </div>

    <script>
        // Debug logging FIRST - before any variables
        console.log('=== COMPARISON WINDOW SCRIPT LOADED ===');
        console.log('Current URL:', window.location.href);
        console.log('Opener exists:', !!window.opener);
        console.log('sessionStorage available:', typeof(Storage) !== 'undefined');

        if (typeof(Storage) !== 'undefined') {
            console.log('sessionStorage keys:', Object.keys(sessionStorage));
            const data = sessionStorage.getItem('hawkeyeComparisonData');
            console.log('hawkeyeComparisonData exists:', !!data);
            if (data) {
                console.log('Data length:', data.length);
                console.log('First 500 chars:', data.substring(0, 500));
                try {
                    const parsed = JSON.parse(data);
                    console.log('Parsed successfully');
                    console.log('Runs count:', parsed.runs ? parsed.runs.length : 'N/A');
                    console.log('Keywords count:', parsed.keywords ? parsed.keywords.length : 'N/A');
                } catch (e) {
                    console.error('Failed to parse:', e);
                }
            }
        } else {
            console.error('sessionStorage not available!');
        }

        // THEN declare variables
        let comparisonData = null;
        let isTransposed = true;  // Default to Transposed View
        let currentView = 'transposed';
        let filteredKeywords = [];
        let filteredTasks = [];
        let hideEmptyColumns = false;
        let keywordGroups = {};
        let taskGroups = {};
        let selectedTasks = new Set();
        let taskOrderFromYAML = []; // Global variable to store task order from YAML

        // Load comparison data from sessionStorage
        window.addEventListener('load', function() {
            console.log('=== Window load event fired ===');
        // Check if sessionStorage is available
        // ... rest of the code

            // Check if sessionStorage is available
            if (typeof(Storage) === 'undefined') {
                showError('Browser storage not available. Please use a modern browser.');
                return;
            }

            // Check if data exists
            const rawData = sessionStorage.getItem('hawkeyeComparisonData');
            if (!rawData) {
                showError('No comparison data found in browser storage. Please try comparing runs again from the main dashboard.');
                return;
            }

            console.log('Found data, length:', rawData.length);

            // Try to parse the data
            try {
                const testParse = JSON.parse(rawData);
                console.log('Data parsed successfully');
                console.log('Contains runs:', !!testParse.runs);
                console.log('Contains keywords:', !!testParse.keywords);
            } catch (error) {
                console.error('Parse error:', error);
                showError('Invalid comparison data format: ' + error.message);
                return;
            }

            // All checks passed, load the data
            loadComparisonData();

            // Add event listeners
            const searchInput = document.getElementById('comparison-search');
            if (searchInput) {
                searchInput.addEventListener('input', filterComparisonData);
            }

            const keywordSearchInput = document.getElementById('keyword-search');
            if (keywordSearchInput) {
                keywordSearchInput.addEventListener('input', applyKeywordFilters);
            }


            console.log('Event listeners added');
        });

        // Function to extract task order from YAML configuration
        function extractTaskOrderFromYAML(yamlConfig) {
            const taskOrder = [];

            if (yamlConfig && yamlConfig.jobs) {
                // Extract tasks from jobs in the order they appear in YAML
                Object.entries(yamlConfig.jobs).forEach(([jobName, jobConfig]) => {
                    if (jobConfig.tasks && Array.isArray(jobConfig.tasks)) {
                        jobConfig.tasks.forEach(taskName => {
                            if (!taskOrder.includes(taskName)) {
                                taskOrder.push(taskName);
                            }
                        });
                    }
                });
            }

            // Add any remaining tasks from the tasks section
            if (yamlConfig && yamlConfig.tasks) {
                Object.keys(yamlConfig.tasks).forEach(taskName => {
                    if (!taskOrder.includes(taskName)) {
                        taskOrder.push(taskName);
                    }
                });
            }

            return taskOrder;
        }

        // Function to sort tasks based on YAML order
        function sortTasksByYAMLOrder(tasks) {
            if (taskOrderFromYAML.length === 0) {
                return tasks.sort(); // Fallback to alphabetical if no YAML order
            }

            return tasks.sort((a, b) => {
                const indexA = taskOrderFromYAML.indexOf(a);
                const indexB = taskOrderFromYAML.indexOf(b);

                // If both tasks are in YAML order, sort by their YAML position
                if (indexA !== -1 && indexB !== -1) {
                    return indexA - indexB;
                }

                // If only one task is in YAML order, prioritize it
                if (indexA !== -1 && indexB === -1) {
                    return -1;
                }
                if (indexA === -1 && indexB !== -1) {
                    return 1;
                }

                // If neither task is in YAML order, sort alphabetically
                return a.localeCompare(b);
            });
        }

        async function loadComparisonData() {
            console.log('=== loadComparisonData START ===');

            try {
                // Get data from sessionStorage
                const dataString = sessionStorage.getItem('hawkeyeComparisonData');
                if (!dataString) {
                    throw new Error('No data in sessionStorage');
                }

                // Parse the data
                comparisonData = JSON.parse(dataString);
                console.log('Parsed comparisonData:', comparisonData);

                // Basic validation
                if (!comparisonData.runs || !Array.isArray(comparisonData.runs)) {
                    throw new Error('Invalid data: runs is not an array');
                }

                if (!comparisonData.keywords || !Array.isArray(comparisonData.keywords)) {
                    throw new Error('Invalid data: keywords is not an array');
                }

                console.log(`Data validated: ${comparisonData.runs.length} runs, ${comparisonData.keywords.length} keywords`);

                // Store original copy
                window.originalComparisonData = JSON.parse(dataString);

                // Extract keyword units
                comparisonData.keywordUnits = extractKeywordUnits(comparisonData.runs);
                console.log('Extracted units:', Object.keys(comparisonData.keywordUnits).length);

                // Update description
                updateComparisonDescription();

                // CRITICAL: Load YAML config FIRST before initializing filters
                try {
                    await loadKeywordGroupConfig();
                    console.log('YAML config loaded successfully');
                } catch (error) {
                    console.warn('YAML config load failed:', error);
                }

                // NOW initialize filters AFTER YAML is loaded
                try {
                    initializeFilters();
                    console.log('Filters initialized successfully');
                } catch (error) {
                    console.error('Filter initialization error:', error);
                }

                // Render immediately
                console.log('Calling renderComparison...');
                renderComparison();
                console.log('=== loadComparisonData COMPLETE ===');

            } catch (error) {
                console.error('=== loadComparisonData ERROR ===', error);
                showError('Failed to load comparison data: ' + error.message);
            }
        }


        function extractKeywordUnits(runs) {
            const keywordUnits = {};

            if (!Array.isArray(runs)) {
                console.error('extractKeywordUnits: runs is not an array');
                return keywordUnits;
            }

            runs.forEach(run => {
                if (run && run.keywords && typeof run.keywords === 'object') {
                    try {
                        Object.values(run.keywords).flat().forEach(k => {
                            if (k && k.keyword_name && k.keyword_unit && !keywordUnits[k.keyword_name]) {
                                keywordUnits[k.keyword_name] = k.keyword_unit;
                            }
                        });
                    } catch (error) {
                        console.error('Error extracting units from run:', run.run_version, error);
                    }
                }
            });

            return keywordUnits;
        }

        function updateComparisonDescription() {
            if (comparisonData) {
                const description = document.getElementById('comparison-description');
                const timestamp = new Date(comparisonData.timestamp).toLocaleString();

                description.innerHTML = `Comparison View - Created: ${timestamp}`;

                // Update page title with comparison info
                document.title = `Hawkeye Comparison - ${comparisonData.runs.length} runs`;
            }
        }

        function initializeFilters() {

            console.log('=== initializeFilters START ===');
            console.log('keywordGroupConfig available:', !!keywordGroupConfig);

            if (!comparisonData || !comparisonData.keywords || !comparisonData.runs) {
                console.error('Cannot initialize filters: invalid comparison data');
                return;
            }

            try {
                // Initialize filtered keywords with all keywords
                filteredKeywords = Array.isArray(comparisonData.keywords) ?
                    [...comparisonData.keywords] : [];

                console.log('Initialized filteredKeywords:', filteredKeywords.length);

                // Initialize filtered tasks with all tasks
                filteredTasks = extractAllTasks(comparisonData.runs);
                console.log('Initialized filteredTasks:', filteredTasks.length);

                // Create keyword groups only if we have keywords
                if (filteredKeywords.length > 0) {
                    keywordGroups = groupKeywordsByConvention(comparisonData.keywords);
                    console.log('Created keyword groups:', Object.keys(keywordGroups));
                    console.log('Group details:', keywordGroups);
                } else {
                    keywordGroups = {};
                }

                // Use flat task list
                taskGroups = null;

                // Populate filter dropdowns
                try {
                    populateGroupFilter();
                    populateTaskFilter();
                } catch (error) {
                    console.error('Error populating filters:', error);
                }

                // Add event listeners for filtering
                const keywordSearch = document.getElementById('keyword-search');
                if (keywordSearch) {
                    keywordSearch.addEventListener('input', applyKeywordFilters);
                }

                // Update filtered counts
                updateFilteredCount();
                updateTaskFilteredCount();

                console.log('Filters initialized successfully');
            } catch (error) {
                console.error('Error in initializeFilters:', error);
                throw error;
            }
        }

        function extractAllTasks(runs) {
            const allTasks = new Set();

            if (!Array.isArray(runs)) {
                console.error('extractAllTasks: runs is not an array');
                return [];
            }

            runs.forEach(run => {
                if (run && run.keywords && typeof run.keywords === 'object') {
                    Object.keys(run.keywords).forEach(taskName => {
                        if (taskName && typeof taskName === 'string') {
                            allTasks.add(taskName);
                        }
                    });
                }
            });

            // Convert to array and sort using YAML order
            const tasksArray = Array.from(allTasks);
            return sortTasksByYAMLOrder(tasksArray);
        }

        function groupTasksByConvention(tasks) {
            const groups = {};

            tasks.forEach(task => {
                let groupName = 'Other Tasks';

                // Group by common task naming patterns
                if (task.includes('_')) {
                    const parts = task.split('_');
                    if (parts.length >= 2) {
                        const firstPart = parts[0].toLowerCase();
                        const secondPart = parts[1].toLowerCase();

                        if (['place', 'init', 'cts', 'route', 'postroute'].includes(firstPart)) {
                            groupName = 'APR Tasks';
                        } else if (['sta', 'timing'].includes(firstPart)) {
                            groupName = 'Timing Analysis';
                        } else if (['power', 'pwr'].includes(firstPart)) {
                            groupName = 'Power Analysis';
                        } else if (['drc', 'lvs', 'pv'].includes(firstPart)) {
                            groupName = 'Physical Verification';
                        } else if (['syn', 'synthesis'].includes(firstPart)) {
                            groupName = 'Synthesis';
                        } else if (['sim', 'simulation'].includes(firstPart)) {
                            groupName = 'Simulation';
                        } else {
                            groupName = firstPart.charAt(0).toUpperCase() + firstPart.slice(1) + ' Tasks';
                        }
                    }
                } else if (['placement', 'routing', 'synthesis', 'verification'].some(keyword =>
                    task.toLowerCase().includes(keyword))) {
                    if (task.toLowerCase().includes('placement')) {
                        groupName = 'APR Tasks';
                    } else if (task.toLowerCase().includes('routing')) {
                        groupName = 'APR Tasks';
                    } else if (task.toLowerCase().includes('synthesis')) {
                        groupName = 'Synthesis';
                    } else if (task.toLowerCase().includes('verification')) {
                        groupName = 'Physical Verification';
                    }
                }

                if (!groups[groupName]) {
                    groups[groupName] = [];
                }
                groups[groupName].push(task);
            });

            // Sort tasks within each group
            Object.keys(groups).forEach(group => {
                groups[group].sort();
            });

            return groups;
        }

        function populateTaskFilter() {
            const taskOptions = document.getElementById('task-options');
            if (!taskOptions) return;

            // Use YAML-ordered list of tasks
            const allTasks = extractAllTasks(comparisonData.runs); // This now returns YAML-ordered tasks

            taskOptions.innerHTML = '';
            allTasks.forEach(taskName => {
                const link = document.createElement('a');
                link.href = '#';
                link.textContent = taskName;
                link.style.paddingLeft = '10px';
                link.onclick = function(e) {
                    e.preventDefault();
                    toggleTaskSelection(taskName, this);
                };
                taskOptions.appendChild(link);
            });
        }


        function toggleTaskSelection(taskName, element) {
            if (selectedTasks.has(taskName)) {
                selectedTasks.delete(taskName);
                element.classList.remove('selected');
            } else {
                selectedTasks.add(taskName);
                element.classList.add('selected');
            }

            updateTaskFilterButtonState();
            applyTaskFilters();
        }

        function updateTaskFilterButtonState() {
            const button = document.getElementById('filter-task-btn');
            if (selectedTasks.size === 0) {
                button.textContent = 'All Tasks';
                button.classList.remove('has-filters');
            } else if (selectedTasks.size === 1) {
                button.textContent = Array.from(selectedTasks)[0];
                button.classList.add('has-filters');
            } else {
                button.textContent = `${selectedTasks.size} Tasks Selected`;
                button.classList.add('has-filters');
            }
        }

        function applyTaskFilters() {
            // Filter tasks based on selection
            if (selectedTasks.size > 0) {
                // Sort selected tasks using YAML order
                filteredTasks = sortTasksByYAMLOrder(Array.from(selectedTasks));
            } else {
                // Get all tasks and sort them using YAML order
                filteredTasks = extractAllTasks(comparisonData.runs);
            }

            updateTaskFilteredCount();
            renderComparison();
        }

        function clearTaskFilters() {
            selectedTasks.clear();

            // Clear visual selection
            document.querySelectorAll('#task-options a').forEach(link => {
                link.classList.remove('selected');
            });

            updateTaskFilterButtonState();
            applyTaskFilters();
        }

        function updateTaskFilteredCount() {
            const countElement = document.getElementById('filtered-tasks-count');
            if (countElement) {
                countElement.textContent = filteredTasks.length;
            }
        }

        function selectAllTaskOptions() {
            selectedTasks.clear();
            // Get all tasks from the flat list
            const allTasks = extractAllTasks(comparisonData.runs);
            allTasks.forEach(taskName => {
                selectedTasks.add(taskName);
            });

            // Update visual state
            document.querySelectorAll('#task-options a').forEach(link => {
                link.classList.add('selected');
            });

            updateTaskFilterButtonState();
            applyTaskFilters();
        }

        function selectAllFilterOptions(filterType) {
            if (filterType === 'group') {
                // existing group logic
                selectedGroups.clear();
                Object.keys(keywordGroups).forEach(groupName => {
                    selectedGroups.add(groupName);
                });

                document.querySelectorAll('#group-options a').forEach(link => {
                    link.classList.add('selected');
                });

                updateFilterButtonState();
                applyKeywordFilters();
            }
        }

        function clearAllTaskOptions() {
            selectedTasks.clear();

            document.querySelectorAll('#task-options a').forEach(link => {
                link.classList.remove('selected');
            });

            updateTaskFilterButtonState();
            applyTaskFilters();
        }

        function clearAllFilterOptions(filterType) {
            if (filterType === 'group') {
                // existing group logic
                selectedGroups.clear();

                document.querySelectorAll('#group-options a').forEach(link => {
                    link.classList.remove('selected');
                });

                updateFilterButtonState();
                applyKeywordFilters();
            }
        }


        function populateGroupFilter() {
            const groupOptions = document.getElementById('group-options');
            if (!groupOptions) return;

            const groupNames = Object.keys(keywordGroups).sort();

            groupOptions.innerHTML = '';
            groupNames.forEach(groupName => {
                const link = document.createElement('a');
                link.href = '#';
                link.textContent = groupName;
                link.onclick = function(e) {
                    e.preventDefault();
                    toggleGroupSelection(groupName, this);
                };
                groupOptions.appendChild(link);
            });
        }

        // Load keyword groups from YAML configuration
        let keywordGroupConfig = null;

        async function loadKeywordGroupConfig() {
            try {
                const response = await fetch('/api/vista_config');
                if (response.ok) {
                    const config = await response.json();
                    keywordGroupConfig = config;
                    console.log('Loaded YAML config with tasks:', Object.keys(config.tasks || {}).length);
                    return config;
                } else {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
            } catch (error) {
                console.warn('Could not load YAML config, using fallback grouping:', error);
                keywordGroupConfig = null;
                throw error;
            }
        }

        function groupKeywordsByConvention(keywords) {
            const groups = {};

            keywords.forEach(keyword => {
                let groupName = 'Other Keywords';

                // Get group from YAML configuration
                if (keywordGroupConfig && keywordGroupConfig.tasks) {
                    // Search through all tasks for this keyword
                    for (const taskName in keywordGroupConfig.tasks) {
                        const task = keywordGroupConfig.tasks[taskName];
                        if (task.keywords) {
                            for (const keywordConfig of task.keywords) {
                                // Exact match
                                if (keywordConfig.name === keyword && keywordConfig.group) {
                                    groupName = keywordConfig.group;
                                    break;
                                }
                                // Match derived keywords (e.g., s_tns_all from s_tns)
                                if (keywordConfig.group && keyword.startsWith(keywordConfig.name + '_')) {
                                    groupName = keywordConfig.group;
                                    break;
                                }
                            }
                        }
                        if (groupName !== 'Other Keywords') break;
                    }
                }

                if (!groups[groupName]) {
                    groups[groupName] = [];
                }
                groups[groupName].push(keyword);
            });

            // Sort keywords within each group
            Object.keys(groups).forEach(group => {
                groups[group].sort();
            });

            // Sort groups by name (YAML-defined groups first, then Other Keywords)
            const sortedGroups = {};
            const groupOrder = ['err/warn', 'timing', 'utilization', 'congestion', 'drc'];

            // Add known groups in order
            groupOrder.forEach(groupName => {
                if (groups[groupName]) {
                    sortedGroups[groupName] = groups[groupName];
                }
            });

            // Add any additional groups found in YAML (not in predefined order)
            Object.keys(groups).sort().forEach(groupName => {
                if (!groupOrder.includes(groupName) && groupName !== 'Other Keywords') {
                    sortedGroups[groupName] = groups[groupName];
                }
            });

            // Add "Other Keywords" last
            if (groups['Other Keywords']) {
                sortedGroups['Other Keywords'] = groups['Other Keywords'];
            }

            return sortedGroups;
        }


        function renderComparison() {
            if (!comparisonData) return;

            const loading = document.getElementById('loading');
            const content = document.getElementById('comparison-content');
            const viewInfo = document.getElementById('view-info');

            loading.style.display = 'none';
            content.style.display = 'block';

            // Update stats grid
            updateStatsGrid();

            if (isTransposed) {
                renderTransposedView();
                viewInfo.textContent = 'Transposed View (Keywords as Columns)';
                document.getElementById('view-type').textContent = 'Transposed';
            } else {
                renderNormalView();
                viewInfo.textContent = 'Normal View (Keywords as Rows)';
                document.getElementById('view-type').textContent = 'Normal';
            }

            // Make columns draggable
            makeColumnsDraggable();

            // Enable column resize - ADD THIS LINE
            enableColumnResize();

            // Recalculate column widths after rendering is complete
            setTimeout(() => {
                applyCalculatedColumnWidths();
            }, 50);
        }

        function updateStatsGrid() {
            if (!comparisonData) return;

            const { runs } = comparisonData;

            // Get visible data counts based on current view and empty data hiding
            let visibleRuns, visibleKeywords;
            if (isTransposed) {
                ({ visibleRuns, visibleKeywords } = getVisibleDataForTransposedView(runs, filteredKeywords));
            } else {
                ({ visibleRuns, visibleKeywords } = getVisibleDataForNormalView(runs, filteredKeywords));
            }

            // Count total data points for visible keywords
            let totalDataPoints = 0;
            visibleRuns.forEach(run => {
                if (run.keywords) {
                    Object.values(run.keywords).flat().forEach(k => {
                        if (visibleKeywords.includes(k.keyword_name)) {
                            totalDataPoints++;
                        }
                    });
                }
            });

            // Update stats
            document.getElementById('runs-count').textContent = visibleRuns.length;
            document.getElementById('keywords-count').textContent = visibleKeywords.length;
            document.getElementById('data-points').textContent = totalDataPoints;
        }

        function applyKeywordFilters() {
            const searchTerm = document.getElementById('keyword-search').value.toLowerCase();

            // Start with all keywords
            let filtered = [...comparisonData.keywords];

            // Apply text search filter
            if (searchTerm) {
                filtered = filtered.filter(keyword =>
                    keyword.toLowerCase().includes(searchTerm)
                );
            }

            // Apply group filter (multiple groups can be selected)
            if (selectedGroups.size > 0) {
                filtered = filtered.filter(keyword => {
                    return Array.from(selectedGroups).some(groupName =>
                        keywordGroups[groupName] && keywordGroups[groupName].includes(keyword)
                    );
                });
            }

            // Update filtered keywords
            filteredKeywords = filtered;

            // Update filtered count
            updateFilteredCount();

            // Re-render comparison with filtered keywords
            renderComparison();
        }

        function filterComparisonData() {
            const searchTerm = document.getElementById('comparison-search').value.toLowerCase().trim();

            if (!searchTerm) {
                // If no search term, reset to original data
                if (window.originalComparisonData) {
                    comparisonData.runs = JSON.parse(JSON.stringify(window.originalComparisonData.runs));
                }
                updateFilteredCount();
                updateTaskFilteredCount();
                renderComparison();
                return;
            }

            // Filter runs based on run version only
            if (window.originalComparisonData) {
                const filteredRuns = window.originalComparisonData.runs.filter(run => {
                    // Safely check run_version (handle null/undefined)
                    const runVersion = run.run_version || '';
                    return runVersion.toLowerCase().includes(searchTerm);
                });

                console.log('Run Version Filter:', searchTerm);
                console.log('Filtered runs:', filteredRuns.map(r => r.run_version));

                // Update the comparison data with filtered runs
                comparisonData.runs = filteredRuns;
            }

            // Apply sorting to filtered results
            applySorting();

            // Update filtered counts
            updateFilteredCount();
            updateTaskFilteredCount();
        }

        // Global sort state
        let currentSortDirection = 'asc';

        function toggleRunVersionSort() {
            // Toggle sort direction
            currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';

            // Update button text
            const button = document.getElementById('sort-toggle-btn');
            button.textContent = currentSortDirection === 'asc' ? 'Run Version: A -> Z' : 'Run Version: Z <- A';

            // Apply sorting
            applySorting();
        }

        function applySorting() {
            if (window.originalComparisonData && comparisonData) {
                let sortedRuns = [...window.originalComparisonData.runs];

                // Apply search filter first
                const searchTerm = document.getElementById('comparison-search').value.toLowerCase().trim();
                if (searchTerm) {
                    sortedRuns = sortedRuns.filter(run => {
                        const runVersion = run.run_version || '';
                        return runVersion.toLowerCase().includes(searchTerm);
                    });
                }

                // Apply sorting
                if (currentSortDirection === 'asc') {
                    sortedRuns.sort((a, b) => {
                        const aVer = (a.run_version || '').toString();
                        const bVer = (b.run_version || '').toString();
                        return aVer.localeCompare(bVer, undefined, { numeric: true, sensitivity: 'base' });
                    });
                } else {
                    sortedRuns.sort((a, b) => {
                        const aVer = (a.run_version || '').toString();
                        const bVer = (b.run_version || '').toString();
                        return bVer.localeCompare(aVer, undefined, { numeric: true, sensitivity: 'base' });
                    });
                }

                comparisonData.runs = sortedRuns;
                renderComparison();
            }
        }

        function clearKeywordFilters() {
            document.getElementById('keyword-search').value = '';
            document.getElementById('comparison-search').value = '';

            // Reset sort order to default
            currentSortDirection = 'asc';
            const button = document.getElementById('sort-toggle-btn');
            if (button) {
                button.textContent = 'Run Version: A -> Z';
            }

            // Clear group selections
            selectedGroups.clear();
            document.querySelectorAll('#group-options a').forEach(link => {
                link.classList.remove('selected');
            });
            updateFilterButtonState();

            // Clear task selections
            selectedTasks.clear();
            document.querySelectorAll('#task-options a').forEach(link => {
                link.classList.remove('selected');
            });
            updateTaskFilterButtonState();

            // Reset all filtered data
            filteredKeywords = [...comparisonData.keywords];
            filteredTasks = extractAllTasks(comparisonData.runs);
            updateFilteredCount();
            updateTaskFilteredCount();
            renderComparison();
        }

        function updateFilteredCount() {
            const countElement = document.getElementById('filtered-keywords-count');
            if (countElement) {
                countElement.textContent = filteredKeywords.length;
            }
        }

        // Filter system functions - matching main dashboard
        let selectedGroups = new Set();
        let activeFilters = {};

        function toggleFilterDropdown(filterType) {
            const dropdown = document.getElementById(`${filterType}-dropdown`);
            const button = document.getElementById(`filter-${filterType}-btn`);
            const dropdownContainer = dropdown.closest('.filter-dropdown');

            // Close all other dropdowns
            document.querySelectorAll('.filter-dropdown-content').forEach(d => {
                if (d !== dropdown) {
                    d.classList.remove('show');
                }
            });

            // Remove active class from all dropdown containers
            document.querySelectorAll('.filter-dropdown').forEach(container => {
                container.classList.remove('active');
            });

            // Toggle current dropdown
            dropdown.classList.toggle('show');

            // Add active class to current dropdown container if open
            if (dropdown.classList.contains('show')) {
                dropdownContainer.classList.add('active');
            }

            // Update button state
            document.querySelectorAll('.filter-button').forEach(b => {
                if (b !== button) {
                    b.classList.remove('active');
                }
            });
            button.classList.toggle('active');
        }

        function toggleGroupSelection(groupName, element) {
            if (selectedGroups.has(groupName)) {
                selectedGroups.delete(groupName);
                element.classList.remove('selected');
            } else {
                selectedGroups.add(groupName);
                element.classList.add('selected');
            }

            updateFilterButtonState();
            applyKeywordFilters();
        }

        function updateFilterButtonState() {
            const button = document.getElementById('filter-group-btn');
            if (selectedGroups.size === 0) {
                button.textContent = 'All Groups';
                button.classList.remove('has-filters');
            } else if (selectedGroups.size === 1) {
                button.textContent = Array.from(selectedGroups)[0];
                button.classList.add('has-filters');
            } else {
                button.textContent = `${selectedGroups.size} Groups Selected`;
                button.classList.add('has-filters');
            }
        }

        function selectAllFilterOptions(filterType) {
            if (filterType === 'group') {
                selectedGroups.clear();
                Object.keys(keywordGroups).forEach(groupName => {
                    selectedGroups.add(groupName);
                });

                // Update visual state
                document.querySelectorAll('#group-options a').forEach(link => {
                    link.classList.add('selected');
                });

                updateFilterButtonState();
                applyKeywordFilters();
            }
        }

        function clearAllFilterOptions(filterType) {
            if (filterType === 'group') {
                selectedGroups.clear();

                // Update visual state
                document.querySelectorAll('#group-options a').forEach(link => {
                    link.classList.remove('selected');
                });

                updateFilterButtonState();
                applyKeywordFilters();
            }
        }

        function filterDropdownItems(filterType) {
            if (filterType === 'group') {
                const searchTerm = document.querySelector(`#${filterType}-dropdown .filter-search`).value.toLowerCase();
                const options = document.querySelectorAll(`#${filterType}-options a`);

                options.forEach(option => {
                    const text = option.textContent.toLowerCase();
                    if (text.includes(searchTerm)) {
                        option.style.display = 'block';
                    } else {
                        option.style.display = 'none';
                    }
                });
            }
        }

        // Close dropdowns when clicking outside
        document.addEventListener('click', function(event) {
            if (!event.target.closest('.filter-dropdown')) {
                document.querySelectorAll('.filter-dropdown-content').forEach(dropdown => {
                    dropdown.classList.remove('show');
                });
                document.querySelectorAll('.filter-button').forEach(button => {
                    button.classList.remove('active');
                });
                document.querySelectorAll('.filter-dropdown').forEach(container => {
                    container.classList.remove('active');
                });
            }
        });

        function toggleEmptyRowsAndColumns() {
            hideEmptyColumns = !hideEmptyColumns;
            const button = document.getElementById('hide-empty-btn');

            if (hideEmptyColumns) {
                button.textContent = 'Show All Rows and Columns';
                button.className = 'btn btn-warning';
            } else {
                button.textContent = 'Hide Empty Rows and Columns';
                button.className = 'btn btn-info';
            }

            renderComparison();
        }


        function renderNormalView() {
            const content = document.getElementById('comparison-content');
            const { runs } = comparisonData;

            // Filter runs based on selected tasks
            const taskFilteredRuns = filterRunsByTasks(runs, filteredTasks);

            // Get visible runs and keywords based on empty data hiding
            let { visibleRuns, visibleKeywords } = getVisibleDataForNormalView(taskFilteredRuns, filteredKeywords);

            // Calculate appropriate column widths
            const columnWidths = calculateColumnWidths();

            let html = '<table><thead><tr>';
            html += '<th style="background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%); color: white; position: sticky; left: 0; top: 0; z-index: 30; min-width: ' + columnWidths.firstColumn + 'px; max-width: ' + (columnWidths.firstColumn + 50) + 'px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; border-right: 2px solid #555;">Run Version</th>';
            html += '<th style="background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%); color: white; position: sticky; left: ' + columnWidths.firstColumn + 'px; top: 0; z-index: 30; min-width: ' + columnWidths.secondColumn + 'px; max-width: ' + (columnWidths.secondColumn + 50) + 'px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; border-right: 2px solid #555; box-shadow: 2px 0 4px rgba(0,0,0,0.2);">Task</th>';

            visibleRuns.forEach(run => {
                html += `<th style="background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%); color: white; position: sticky; top: 0; z-index: 10;">${run.run_version}</th>`;
            });

            html += '</tr></thead><tbody>';

            visibleKeywords.forEach(keyword => {
                const unit = comparisonData.keywordUnits && comparisonData.keywordUnits[keyword] ? ` <span style="color: #ccc;">[${comparisonData.keywordUnits[keyword]}]</span>` : '';

                // Collect all unique tasks for this keyword across all runs
                const allTasksForKeyword = new Set();
                visibleRuns.forEach(run => {
                    Object.values(run.keywords || {}).flat().forEach(k => {
                        if (k.keyword_name === keyword && !isValueEmpty(k.keyword_value)) {
                            const taskName = k.task_name || 'unknown';
                            allTasksForKeyword.add(taskName);
                        }
                    });
                });

                // If no tasks found, show one row with "--"
                if (allTasksForKeyword.size === 0) {
                    html += '<tr>';
                    html += '<td style="font-weight: normal; background: #f8f9fa; position: sticky; left: 0; z-index: 20; min-width: ' + columnWidths.firstColumn + 'px; max-width: ' + (columnWidths.firstColumn + 50) + 'px; border-right: 2px solid #555;">' + keyword + unit + '</td>';
                    html += '<td style="font-weight: normal; background: #f8f9fa; color: #7f8c8d; position: sticky; left: ' + columnWidths.firstColumn + 'px; z-index: 20; min-width: ' + columnWidths.secondColumn + 'px; max-width: ' + (columnWidths.secondColumn + 50) + 'px; border-right: 2px solid #555; box-shadow: 2px 0 4px rgba(0,0,0,0.1);">--</td>';

                    visibleRuns.forEach(run => {
                        html += '<td style="color: #7f8c8d;">--</td>';
                    });
                    html += '</tr>';
                } else {
                    // Sort tasks using YAML order before displaying
                    const sortedTasks = sortTasksByYAMLOrder(Array.from(allTasksForKeyword));

                    // Show one row for each task in YAML order
                    sortedTasks.forEach(taskName => {
                        html += '<tr>';
                        html += '<td style="font-weight: normal; background: #f8f9fa; position: sticky; left: 0; z-index: 20; min-width: ' + columnWidths.firstColumn + 'px; max-width: ' + (columnWidths.firstColumn + 50) + 'px; border-right: 2px solid #555;">' + keyword + unit + '</td>';
                        html += '<td style="font-weight: normal; background: #f8f9fa; color: #2c3e50; position: sticky; left: ' + columnWidths.firstColumn + 'px; z-index: 20; min-width: ' + columnWidths.secondColumn + 'px; max-width: ' + (columnWidths.secondColumn + 50) + 'px; border-right: 2px solid #555; box-shadow: 2px 0 4px rgba(0,0,0,0.1);">' + taskName + '</td>';

                        visibleRuns.forEach(run => {
                            let value = '--';
                            let style = 'color: #7f8c8d;';

                            // Find keyword value for this specific task
                            Object.values(run.keywords || {}).flat().forEach(k => {
                                if (k.keyword_name === keyword && k.task_name === taskName && !isValueEmpty(k.keyword_value)) {
                                    value = k.keyword_value;
                                    style = 'color: #2c3e50; font-weight: normal;';
                                }
                            });

                            html += `<td style="${style}">${value}</td>`;
                        });

                        html += '</tr>';
                    });
                }
            });

            html += '</tbody></table>';
            content.innerHTML = html;
        }
        function isValueEmpty(value) {
            if (value === null || value === undefined) return true;
            if (value === '-') return true;
            if (value === 'null') return true;
            if (value === 'NULL') return true;
            if (value === 'None') return true;
            if (value === '') return true;
            return false;
        }


        function getVisibleDataForNormalView(runs, keywords) {
            if (!hideEmptyColumns) {
                return { visibleRuns: runs, visibleKeywords: keywords };
            }

            // Filter runs that have at least one non-empty value for filtered keywords
            const visibleRuns = runs.filter(run => {
                if (!run.keywords) return false;

                return keywords.some(keyword => {
                    for (const taskKeywords of Object.values(run.keywords)) {
                        if (Array.isArray(taskKeywords)) {
                            for (const k of taskKeywords) {
                                if (k.keyword_name === keyword && !isValueEmpty(k.keyword_value)) {
                                    return true;
                                }
                            }
                        }
                    }
                    return false;
                });
            });

            // Filter keywords that have at least one non-empty value across visible runs
            const visibleKeywords = keywords.filter(keyword => {
                return visibleRuns.some(run => {
                    if (!run.keywords) return false;

                    for (const taskKeywords of Object.values(run.keywords)) {
                        if (Array.isArray(taskKeywords)) {
                            for (const k of taskKeywords) {
                                if (k.keyword_name === keyword && !isValueEmpty(k.keyword_value)) {
                                    return true;
                                }
                            }
                        }
                    }
                    return false;
                });
            });

            return { visibleRuns, visibleKeywords };
        }

        function renderTransposedView() {
            const content = document.getElementById('comparison-content');
            const { runs } = comparisonData;

            console.log('Transposed view - filteredTasks:', filteredTasks);
            console.log('Transposed view - runs before filter:', runs.length);

            // Filter runs based on selected tasks
            const taskFilteredRuns = filterRunsByTasks(runs, filteredTasks);

            console.log('Transposed view - runs after filter:', taskFilteredRuns.length);

            // Remove runs that have no keywords after task filtering
            const validFilteredRuns = taskFilteredRuns.filter(run => {
                if (!run.keywords) return false;
                const hasValidKeywords = Object.keys(run.keywords).length > 0;
                return hasValidKeywords;
            });

            console.log('Transposed view - valid runs after removing empty:', validFilteredRuns.length);

            // Get visible runs and keywords based on empty data hiding
            let { visibleRuns, visibleKeywords } = getVisibleDataForTransposedView(validFilteredRuns, filteredKeywords);

            console.log('Transposed view - visible runs:', visibleRuns.length);

            // Calculate appropriate column widths
            const columnWidths = calculateColumnWidths();

            // let html = '<div style="overflow-x: auto; position: relative;"><table style="position: relative;"><thead><tr>';

            let html = '<table><thead><tr>';

            // Both columns sticky with proper positioning
            html += '<th style="background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%); color: white; position: sticky; left: 0; top: 0; z-index: 30; min-width: ' + columnWidths.firstColumn + 'px; max-width: ' + (columnWidths.firstColumn + 50) + 'px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; border-right: 2px solid #555;">Run Version</th>';
            html += '<th style="background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%); color: white; position: sticky; left: ' + columnWidths.firstColumn + 'px; top: 0; z-index: 30; min-width: ' + columnWidths.secondColumn + 'px; max-width: ' + (columnWidths.secondColumn + 50) + 'px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; border-right: 2px solid #555; box-shadow: 2px 0 4px rgba(0,0,0,0.2);">Task</th>';

            visibleKeywords.forEach(keyword => {
                const unit = comparisonData.keywordUnits && comparisonData.keywordUnits[keyword] ? ` <span style="color: #ccc;">[${comparisonData.keywordUnits[keyword]}]</span>` : '';
                html += `<th class="rotated-header" style="background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%); color: white; position: sticky; top: 0; z-index: 10;">${keyword}${unit}</th>`;
            });

            html += '</tr></thead><tbody>';

            // For transposed view, we need to show each run with its task combinations
            const runTaskCombinations = [];
            visibleRuns.forEach(run => {
                const tasksForRun = new Set();
                visibleKeywords.forEach(keyword => {
                    Object.values(run.keywords || {}).flat().forEach(k => {
                        if (k.keyword_name === keyword && !isValueEmpty(k.keyword_value)) {
                            const taskName = k.task_name || 'unknown';
                            tasksForRun.add(taskName);
                        }
                    });
                });

                if (tasksForRun.size === 0) {
                    runTaskCombinations.push({ run, task: null });
                } else {
                    const sortedTasks = sortTasksByYAMLOrder(Array.from(tasksForRun));
                    sortedTasks.forEach(task => {
                        runTaskCombinations.push({ run, task });
                    });
                }
            });

            runTaskCombinations.forEach(({ run, task }) => {
                html += '<tr>';

                // First sticky column - Run Version
                html += '<td style="font-weight: normal; background: #f8f9fa; position: sticky; left: 0; z-index: 20; min-width: ' + columnWidths.firstColumn + 'px; max-width: ' + (columnWidths.firstColumn + 50) + 'px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; border-right: 2px solid #555;" title="' + run.run_version + '">' + run.run_version + '</td>';

                // Second sticky column - Task
                html += '<td style="font-weight: normal; background: #f8f9fa; color: #2c3e50; position: sticky; left: ' + columnWidths.firstColumn + 'px; z-index: 20; min-width: ' + columnWidths.secondColumn + 'px; max-width: ' + (columnWidths.secondColumn + 50) + 'px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; border-right: 2px solid #555; box-shadow: 2px 0 4px rgba(0,0,0,0.1);" title="' + (task || '--') + '">' + (task || '--') + '</td>';

                visibleKeywords.forEach(keyword => {
                    let value = '--';
                    let style = 'color: #7f8c8d; position: relative; z-index: 1; background: white;';

                    if (task) {
                        Object.values(run.keywords || {}).flat().forEach(k => {
                            if (k.keyword_name === keyword && k.task_name === task && !isValueEmpty(k.keyword_value)) {
                                value = k.keyword_value;
                                style = 'color: #2c3e50; font-weight: normal; position: relative; z-index: 1; background: white;';
                            }
                        });
                    }

                    html += `<td style="${style}">${value}</td>`;
                });

                html += '</tr>';
            });

            // html += '</tbody></table></div>';
            html += '</tbody></table>';
            content.innerHTML = html;
        }

        function filterRunsByTasks(runs, allowedTasks) {
            if (!Array.isArray(allowedTasks) || allowedTasks.length === 0) {
                return runs; // No task filter, return all runs
            }

            return runs.map(run => {
                const filteredRun = { ...run };

                if (run.keywords && typeof run.keywords === 'object') {
                    const filteredKeywords = {};

                    // Only include keywords from allowed tasks
                    Object.entries(run.keywords).forEach(([taskName, keywords]) => {
                        if (allowedTasks.includes(taskName)) {
                            filteredKeywords[taskName] = keywords;
                        }
                    });

                    filteredRun.keywords = filteredKeywords;
                } else {
                    filteredRun.keywords = {};
                }

                return filteredRun;
            }).filter(run => {
                // Remove runs that have no keywords after task filtering
                return run.keywords &&
                       typeof run.keywords === 'object' &&
                       Object.keys(run.keywords).length > 0;
            });
        }

        function getVisibleDataForTransposedView(runs, keywords) {
            if (!hideEmptyColumns) {
                return { visibleRuns: runs, visibleKeywords: keywords };
            }

            // For Transposed view: runs are rows, keywords are columns
            // Hide rows (runs) that have only empty values
            const visibleRuns = runs.filter(run => {
                return keywords.some(keyword => {
                    let hasValue = false;
                    Object.values(run.keywords || {}).flat().forEach(k => {
                        if (k.keyword_name === keyword && !isValueEmpty(k.keyword_value)) {
                            hasValue = true;
                        }
                    });
                    return hasValue;
                });
            });

            // Hide columns (keywords) that have only empty values across visible runs
            const visibleKeywords = keywords.filter(keyword => {
                return visibleRuns.some(run => {
                    let hasValue = false;
                    Object.values(run.keywords || {}).flat().forEach(k => {
                        if (k.keyword_name === keyword && !isValueEmpty(k.keyword_value)) {
                            hasValue = true;
                        }
                    });
                    return hasValue;
                });
            });

            return { visibleRuns, visibleKeywords };
        }

        function toggleView() {
            isTransposed = !isTransposed;
            currentView = isTransposed ? 'transposed' : 'normal';

            // Update view type in stats
            document.getElementById('view-type').textContent = isTransposed ? 'Transposed' : 'Normal';

            // Update button text
            const toggleBtn = document.getElementById('toggle-btn');
            if (toggleBtn) {
                toggleBtn.textContent = isTransposed ? 'Switch to Normal View' : 'Switch to Transposed View';
            }

            // Reset any active sorting state when switching views
            currentSortColumn = null;
            currentSortDirection = 'asc';

            // Reset column resize state
            document.querySelectorAll('th').forEach(header => {
                header.style.width = '';
                header.style.minWidth = '';
                header.style.maxWidth = '';
            });

            // Clear existing table content first
            const content = document.getElementById('comparison-content');
            content.innerHTML = '<div id="loading" class="loading">Switching view...</div>';

            // Use setTimeout to ensure DOM is cleared before rendering
            setTimeout(() => {
                renderComparison();
            }, 10);
        }

        function makeColumnsDraggable() {
            const table = document.querySelector('table');
            if (!table) return;

            const headerRow = table.querySelector('thead tr');
            const headerCells = headerRow.querySelectorAll('th');

            headerCells.forEach((headerCell, index) => {
                if (index === 0) return; // Skip first column

                // Drag handles removed for cleaner display

                // Make draggable
                headerCell.draggable = true;
                headerCell.dataset.columnIndex = index;

                // Add event listeners
                headerCell.addEventListener('dragstart', handleDragStart);
                headerCell.addEventListener('dragover', handleDragOver);
                headerCell.addEventListener('drop', handleDrop);
            });
        }

        let draggedColumn = null;
        let draggedColumnIndex = null;

        // Column auto-fit and resize functionality
        function enableColumnResize() {
            const table = document.querySelector('table');
            if (!table) return;

            const headers = table.querySelectorAll('th');

            headers.forEach((header, index) => {
                // Skip sticky columns
                if (header.classList.contains('sticky-column')) return;

                // Add resize handle
                const resizeHandle = document.createElement('div');
                resizeHandle.className = 'resize-handle';
                header.appendChild(resizeHandle);

                // Double-click to auto-fit
                resizeHandle.addEventListener('dblclick', (e) => {
                    e.stopPropagation();
                    autoFitColumn(index);
                });

                // Manual resize (drag)
                let isResizing = false;
                let startX, startWidth;

                resizeHandle.addEventListener('mousedown', (e) => {
                    isResizing = true;
                    startX = e.pageX;
                    startWidth = header.offsetWidth;

                    document.body.classList.add('resizing');
                    e.preventDefault();
                });

                document.addEventListener('mousemove', (e) => {
                    if (!isResizing) return;

                    const width = startWidth + (e.pageX - startX);
                    if (width > 50) { // Minimum width
                        header.style.width = width + 'px';
                        header.style.minWidth = width + 'px';
                        header.style.maxWidth = width + 'px';
                    }
                });

                document.addEventListener('mouseup', () => {
                    if (isResizing) {
                        isResizing = false;
                        document.body.classList.remove('resizing');
                    }
                });
            });
        }

        function autoFitColumn(columnIndex) {
            const table = document.querySelector('table');
            if (!table) return;

            const rows = table.querySelectorAll('tr');
            let maxWidth = 0;

            // Create a temporary element to measure text width
            const measureElement = document.createElement('span');
            measureElement.style.visibility = 'hidden';
            measureElement.style.position = 'absolute';
            measureElement.style.whiteSpace = 'nowrap';
            measureElement.style.fontSize = '10px';
            measureElement.style.fontFamily = getComputedStyle(table).fontFamily;
            document.body.appendChild(measureElement);

            // Measure all cells in this column
            rows.forEach(row => {
                const cells = row.querySelectorAll('td, th');
                if (cells[columnIndex]) {
                    const cell = cells[columnIndex];
                    measureElement.textContent = cell.textContent;
                    const width = measureElement.offsetWidth + 30; // Add padding
                    maxWidth = Math.max(maxWidth, width);
                }
            });

            document.body.removeChild(measureElement);

            // Apply the width to all cells in this column
            rows.forEach(row => {
                const cells = row.querySelectorAll('td, th');
                if (cells[columnIndex]) {
                    cells[columnIndex].style.width = maxWidth + 'px';
                    cells[columnIndex].style.minWidth = maxWidth + 'px';
                    cells[columnIndex].style.maxWidth = maxWidth + 'px';
                }
            });

            // Show feedback
            showColumnResizeMessage(`Column auto-fitted to ${maxWidth}px`);
        }
        // Calculate appropriate column widths based on content
        function calculateColumnWidths() {
            const table = document.querySelector('table');
            if (!table) return { firstColumn: 120, secondColumn: 100 };

            const rows = table.querySelectorAll('tr');
            let firstColMax = 0;
            let secondColMax = 0;

            // Create a temporary element to measure text width
            const measureElement = document.createElement('span');
            measureElement.style.visibility = 'hidden';
            measureElement.style.position = 'absolute';
            measureElement.style.whiteSpace = 'nowrap';
            measureElement.style.fontSize = '10px';
            measureElement.style.fontFamily = getComputedStyle(table).fontFamily;
            document.body.appendChild(measureElement);

            // Measure all cells in first two columns
            rows.forEach(row => {
                const cells = row.querySelectorAll('td, th');
                if (cells[0]) {
                    measureElement.textContent = cells[0].textContent;
                    firstColMax = Math.max(firstColMax, measureElement.offsetWidth + 20);
                }
                if (cells[1]) {
                    measureElement.textContent = cells[1].textContent;
                    secondColMax = Math.max(secondColMax, measureElement.offsetWidth + 20);
                }
            });

            document.body.removeChild(measureElement);

            // Ensure minimum widths but keep them flexible
            return {
                firstColumn: Math.max(firstColMax, 80),
                secondColumn: Math.max(secondColMax, 80)
            };
        }

        // Apply calculated column widths to existing table
        function applyCalculatedColumnWidths() {
            const table = document.querySelector('table');
            if (!table) return;

            const columnWidths = calculateColumnWidths();

            // Update header cells
            const headerRow = table.querySelector('thead tr');
            const headers = headerRow.querySelectorAll('th');

            if (headers[0]) {
                headers[0].style.minWidth = columnWidths.firstColumn + 'px';
                headers[0].style.maxWidth = (columnWidths.firstColumn + 50) + 'px';
            }
            if (headers[1]) {
                headers[1].style.left = columnWidths.firstColumn + 'px';
                headers[1].style.minWidth = columnWidths.secondColumn + 'px';
                headers[1].style.maxWidth = (columnWidths.secondColumn + 50) + 'px';
            }

            // Update all body cells
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const cells = row.querySelectorAll('td');
                if (cells[0]) {
                    cells[0].style.minWidth = columnWidths.firstColumn + 'px';
                    cells[0].style.maxWidth = (columnWidths.firstColumn + 50) + 'px';
                }
                if (cells[1]) {
                    cells[1].style.left = columnWidths.firstColumn + 'px';
                    cells[1].style.minWidth = columnWidths.secondColumn + 'px';
                    cells[1].style.maxWidth = (columnWidths.secondColumn + 50) + 'px';
                }
            });
        }


        function showColumnResizeMessage(message) {
            let messageElement = document.getElementById('column-resize-message');
            if (!messageElement) {
                messageElement = document.createElement('div');
                messageElement.id = 'column-resize-message';
                messageElement.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #3498db;
                    color: white;
                    padding: 10px 15px;
                    border-radius: 4px;
                    font-size: 12px;
                    z-index: 10000;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                    transition: opacity 0.3s ease;
                `;
                document.body.appendChild(messageElement);
            }

            messageElement.textContent = message;
            messageElement.style.opacity = '1';

            setTimeout(() => {
                messageElement.style.opacity = '0';
                setTimeout(() => {
                    if (messageElement.parentNode) {
                        messageElement.parentNode.removeChild(messageElement);
                    }
                }, 300);
            }, 2000);
        }

        // Auto-fit all columns
        function autoFitAllColumns() {
            const table = document.querySelector('table');
            if (!table) return;

            const headerRow = table.querySelector('thead tr');
            const headers = headerRow.querySelectorAll('th');

            headers.forEach((header, index) => {
                if (!header.classList.contains('sticky-column')) {
                    autoFitColumn(index);
                }
            });

            showColumnResizeMessage('All columns auto-fitted');
        }

        function handleDragStart(e) {
            draggedColumn = e.target;
            draggedColumnIndex = parseInt(e.target.dataset.columnIndex);
            e.dataTransfer.effectAllowed = 'move';
            e.target.style.opacity = '0.5';
        }

        function handleDragOver(e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
        }

        function handleDrop(e) {
            e.preventDefault();

            if (e.target.tagName === 'TH' && e.target !== draggedColumn) {
                const targetColumnIndex = parseInt(e.target.dataset.columnIndex);

                // Remove visual feedback
                draggedColumn.style.opacity = '';

                // Reorder columns
                reorderColumns(draggedColumnIndex, targetColumnIndex);
            }
        }

        function reorderColumns(fromIndex, toIndex) {
            const table = document.querySelector('table');
            if (!table) return;

            const rows = table.querySelectorAll('tr');

            rows.forEach(row => {
                const cells = row.querySelectorAll('td, th');
                if (cells.length <= Math.max(fromIndex, toIndex)) return;

                const cellToMove = cells[fromIndex];

                if (fromIndex < toIndex) {
                    row.insertBefore(cellToMove, cells[toIndex + 1]);
                } else {
                    row.insertBefore(cellToMove, cells[toIndex]);
                }
            });

            // Update column indices
            updateColumnIndices();
        }

        function updateColumnIndices() {
            const table = document.querySelector('table');
            if (!table) return;

            const headerCells = table.querySelectorAll('thead th');
            headerCells.forEach((headerCell, index) => {
                headerCell.dataset.columnIndex = index;
            });
        }

        function resetColumnOrder() {
            renderComparison();
        }

        function exportComparison() {
            if (!comparisonData) return;

            const { runs } = comparisonData;

            // Get visible data based on current view and empty data hiding
            let visibleRuns, visibleKeywords;
            if (isTransposed) {
                ({ visibleRuns, visibleKeywords } = getVisibleDataForTransposedView(runs, filteredKeywords));
            } else {
                ({ visibleRuns, visibleKeywords } = getVisibleDataForNormalView(runs, filteredKeywords));
            }

            // Export exactly as displayed in the table - using tabs as separators
            let csvContent = '';

            if (isTransposed) {
                // TRANSPOSED VIEW: Run-Task combinations as rows, Keywords as columns (as shown in table)
                csvContent = 'Run Version\tTask';

                // Add keywords as headers with units
                visibleKeywords.forEach(keyword => {
                    const unit = comparisonData.keywordUnits && comparisonData.keywordUnits[keyword] ? ` (${comparisonData.keywordUnits[keyword]})` : '';
                    csvContent += `\t${keyword}${unit}`;
                });
                csvContent += '\n';

                // Collect all unique task combinations for each run
                const runTaskCombinations = [];
                visibleRuns.forEach(run => {
                    const tasksForRun = new Set();
                    visibleKeywords.forEach(keyword => {
                        Object.values(run.keywords || {}).flat().forEach(k => {
                            if (k.keyword_name === keyword && !isValueEmpty(k.keyword_value)) {
                                const taskName = k.task_name || 'unknown';
                                tasksForRun.add(taskName);
                            }
                        });
                    });

                    if (tasksForRun.size === 0) {
                        // No tasks found for this run
                        runTaskCombinations.push({ run, task: null });
                } else {
                    // Sort tasks using YAML order before adding to export
                    const sortedTasks = sortTasksByYAMLOrder(Array.from(tasksForRun));
                    sortedTasks.forEach(task => {
                            runTaskCombinations.push({ run, task });
                        });
                    }
                });

                // Add data rows (one per run-task combination)
                runTaskCombinations.forEach(({ run, task }) => {
                    csvContent += `"${run.run_version}"\t"${task || '--'}"`;

                    visibleKeywords.forEach(keyword => {
                        let value = '--';

                        if (task) {
                            // Find keyword value for this specific task
                            Object.values(run.keywords || {}).flat().forEach(k => {
                                if (k.keyword_name === keyword && k.task_name === task && !isValueEmpty(k.keyword_value)) {
                                    value = k.keyword_value;
                                }
                            });
                        }

                        csvContent += `\t"${value}"`;
                    });

                    csvContent += '\n';
                });

                filename = `hawkeye_comparison_transposed_${new Date().toISOString().split('T')[0]}.tsv`;
            } else {
                // NORMAL VIEW: Keywords as rows, Task column, Runs as columns (as shown in table)
                csvContent = 'Keyword\tTask';

                // Add run versions as headers
                visibleRuns.forEach(run => {
                    csvContent += `\t${run.run_version}`;
                });
                csvContent += '\n';

                // Add data rows (one per keyword-task combination)
                visibleKeywords.forEach(keyword => {
                    const unit = comparisonData.keywordUnits && comparisonData.keywordUnits[keyword] ? ` (${comparisonData.keywordUnits[keyword]})` : '';

                    // Collect all unique tasks for this keyword across all runs
                    const allTasksForKeyword = new Set();
                    visibleRuns.forEach(run => {
                        Object.values(run.keywords || {}).flat().forEach(k => {
                            if (k.keyword_name === keyword && !isValueEmpty(k.keyword_value)) {
                                const taskName = k.task_name || 'unknown';
                                allTasksForKeyword.add(taskName);
                            }
                        });
                    });

                    // If no tasks found, show one row with "--"
                    if (allTasksForKeyword.size === 0) {
                        csvContent += `"${keyword}${unit}"\t"--"`;
                        visibleRuns.forEach(run => {
                            csvContent += '\t"--"';
                        });
                        csvContent += '\n';
                } else {
                    // Sort tasks using YAML order before export
                    const sortedTasks = sortTasksByYAMLOrder(Array.from(allTasksForKeyword));
                    sortedTasks.forEach(taskName => {
                            csvContent += `"${keyword}${unit}"\t"${taskName}"`;

                            visibleRuns.forEach(run => {
                                let value = '--';

                                // Find keyword value for this specific task
                                Object.values(run.keywords || {}).flat().forEach(k => {
                                    if (k.keyword_name === keyword && k.task_name === taskName && !isValueEmpty(k.keyword_value)) {
                                        value = k.keyword_value;
                                    }
                                });

                                csvContent += `\t"${value}"`;
                            });

                            csvContent += '\n';
                        });
                    }
                });

                filename = `hawkeye_comparison_normal_${new Date().toISOString().split('T')[0]}.tsv`;
            }

            // Download TSV (Tab-Separated Values)
            const blob = new Blob([csvContent], { type: 'text/tab-separated-values' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            window.URL.revokeObjectURL(url);

            // Show confirmation
            const viewType = isTransposed ? 'Transposed view' : 'Normal view';
            alert(`Exported ${visibleKeywords.length} keywords from ${visibleRuns.length} runs in ${viewType} format.\\n\\nFilename: ${filename}\\n\\nThe TSV matches exactly what you see in the table with tab separators.`);
        }

        function showError(message) {
            console.error('showError called:', message);
            const loading = document.getElementById('loading');
            const content = document.getElementById('comparison-content');

            if (loading) {
                loading.style.display = 'none';
            }

            if (content) {
                content.style.display = 'block';
                content.innerHTML = `
                    <div class="error">
                        <h3>Error Loading Comparison</h3>
                        <p>${message}</p>
                        <button class="btn" onclick="window.close()" style="margin-top: 10px;">Close Window</button>
                        <button class="btn btn-secondary" onclick="window.location.reload()" style="margin-top: 10px;">Retry</button>
                    </div>
                `;
            } else {
                // Fallback if elements don't exist
                document.body.innerHTML = `
                    <div style="padding: 40px; text-align: center;">
                        <h2 style="color: #e74c3c;">Error</h2>
                        <p>${message}</p>
                        <button onclick="window.close()" style="padding: 10px 20px; margin: 10px;">Close Window</button>
                    </div>
                `;
            }
        }

    </script>
</body>
</html>
"""
# Project Selection Page Template
PROJECT_SELECTOR_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hawkeye - Select Project</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }


        .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: none;        /* Changed from 900px */
            width: 95%;             /* 95% width with 5% margin total */
            margin: 0 auto;
            overflow: hidden;
        }

        .header {
            background: #2c3e50;
            color: white;
            padding: 20px, 20px;
            text-align: center;
        }

        .header h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }

        .header p {
            opacity: 0.9;
            font-size: 1.1em;
        }

        .content {
            padding: 15px;
        }

        .info-box {
            background: #e8f4fd;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin-bottom: 25px;
            border-radius: 4px;
        }

        .info-box p {
            color: #2c3e50;
            line-height: 1.6;
        }

        .projects-grid {
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-top: 20px;
        }

        .project-card {
            background: #f8f9fa;
            border: 2px solid #e0e6ed;
            border-radius: 8px;
            padding: 10x 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .project-card:hover {
            transform: translateX(4px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            border-color: #3498db;
        }

        .project-card.no-archive {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .project-card.no-archive:hover {
            transform: none;
            box-shadow: none;
        }

        .project-info {
            flex: 1;
        }

        .project-name {
            font-size: 1.3em;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 5px;
        }

        .project-stats {
            display: flex;
            gap: 10px;
            align-items: center;
        }

        .stat-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9em;
        }

        .stat-label {
            color: #7f8c8d;
        }

        .stat-value {
            color: #2c3e50;
            font-weight: 500;
        }

        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 500;
        }

        .badge-success {
            background: #d4edda;
            color: #155724;
        }

        .badge-warning {
            background: #fff3cd;
            color: #856404;
        }

        .no-projects {
            text-align: center;
            padding: 40px;
            color: #7f8c8d;
        }

        .current-project {
            background: #d4edda;
            border: 2px solid #28a745;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }

        .current-project h3 {
            color: #155724;
            margin-bottom: 8px;
        }

        .btn {
            display: inline-block;
            padding: 10px 20px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s ease;
            text-decoration: none;
        }

        .btn:hover {
            background: #2980b9;
            transform: translateY(-2px);
        }

        .btn-secondary {
            background: #95a5a6;
        }

        .btn-secondary:hover {
            background: #7f8c8d;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>? Hawkeye Analysis Dashboard</h1>
            <p>Select a project to analyze</p>
        </div>

        <div class="content">
            {% if projects %}
            <div class="projects-grid">
                {% for project in projects %}
                <div class="project-card {% if not project.has_archive %}no-archive{% endif %}"
                     {% if project.has_archive %}onclick="selectProject('{{ project.name }}')"{% endif %}>

                    <div class="project-info">
                        <div class="project-name">{{ project.name }}</div>
                        <div class="project-stats">
                            {% if project.has_archive %}
                                <div class="stat-item">
                                    <span class="stat-label">Runs:</span>
                                    <span class="stat-value">{{ project.run_count }}</span>
                                </div>
                                {% if project.last_updated %}
                                <div class="stat-item">
                                    <span class="stat-label">Updated:</span>
                                    <span class="stat-value">{{ project.last_updated[:10] }}</span>
                                </div>
                                {% endif %}
                            {% else %}
                                <span style="color: #856404; font-size: 0.9em;">No archive available</span>
                            {% endif %}
                        </div>
                    </div>

                    {% if project.has_archive %}
                        <span class="badge badge-success">Archive Available</span>
                    {% else %}
                        <span class="badge badge-warning">No Archive</span>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            {% else %}
            <div class="no-projects">
                <p>No projects found in {{ casino_prj_base }}</p>
            </div>
            {% endif %}
        </div>

    </div>
    <script>
        function selectProject(projectName) {
            console.log('Selecting project:', projectName);

            fetch('/api/select-project', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ project: projectName })
            })
            .then(response => {
                console.log('Response status:', response.status);
                console.log('Response headers:', response.headers);

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Response data:', data);
                if (data.success) {
                    window.location.href = '/';
                } else {
                    alert('Error selecting project: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Fetch error:', error);
                alert('Error selecting project: ' + error.message + '\n\nCheck browser console for details.');
            });
        }
    </script>
</body>
</html>
"""

# Routes
@app.route('/select-project')
def select_project():
    """Show project selection page"""
    projects = discover_projects()
    casino_prj_base = os.getenv('casino_prj_base', 'Not set')
    current_project = session.get('current_project')

    return render_template_string(
        PROJECT_SELECTOR_TEMPLATE,
        projects=projects,
        casino_prj_base=casino_prj_base,
        current_project=current_project
    )

@app.route('/api/select-project', methods=['POST'])
def api_select_project():
    """API endpoint to select a project"""
    print(f"=== API select-project called ===")

    try:
        data = request.get_json()
        print(f"Request data: {data}")

        project_name = data.get('project') if data else None

        if not project_name:
            return jsonify({'success': False, 'error': 'No project specified'}), 400

        # Initialize archive first
        if init_archive(project_name):
            # Then set session variables
            session['current_project'] = project_name
            casino_prj_base = os.getenv('casino_prj_base')
            archive_path = os.path.join(casino_prj_base, project_name, 'hawkeye_archive')
            session['archive_path'] = archive_path

            print(f"SUCCESS: Project {project_name} selected")
            return jsonify({'success': True, 'project': project_name})
        else:
            print(f"ERROR: Failed to initialize archive for {project_name}")
            return jsonify({'success': False, 'error': 'Failed to initialize archive'}), 500

    except Exception as e:
        print(f"EXCEPTION: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/')
def index():
    """Main dashboard - requires project selection"""
    if 'current_project' not in session or archive is None:
        return redirect(url_for('select_project'))

    return render_template_string(HTML_TEMPLATE)

@app.route('/api/current-project')
def get_current_project():
    """Get currently selected project"""
    return jsonify({
        'project': session.get('current_project'),
        'archive_path': session.get('archive_path')
    })

# Continue with other API routes...

# API Routes
@app.route('/api/vista_config')
def get_vista_config():
    """Get vista_casino.yaml configuration"""
    try:
        import yaml
        import os

        config_path = os.path.join(os.path.dirname(__file__), 'vista_casino.yaml')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return jsonify(config)
        else:
            return jsonify({'error': 'vista_casino.yaml not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics')
def get_statistics():
    """Get archive statistics"""
    try:
        stats = archive.get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/runs')
def get_runs():
    """Get list of archived runs with optional filtering"""
    try:
        # Build filters from query parameters
        filters = {}

        if request.args.get('run_version'):
            filters['run_version'] = request.args.get('run_version')
        if request.args.get('user_name'):
            filters['user_name'] = request.args.get('user_name')
        if request.args.get('base_dir'):
            filters['base_dir'] = request.args.get('base_dir')
        if request.args.get('date_from'):
            filters['date_from'] = request.args.get('date_from')
        if request.args.get('date_to'):
            filters['date_to'] = request.args.get('date_to')

        runs = archive.get_archived_runs(filters)

        # Remove duplicates - keep only the latest entry for each run_version
        unique_runs = {}
        for run in runs:
            run_key = (run['run_version'], run['base_dir'], run['top_name'],
                      run['user_name'], run['block_name'], run['dk_ver_tag'])

            if run_key not in unique_runs or run['archive_timestamp'] > unique_runs[run_key]['archive_timestamp']:
                unique_runs[run_key] = run

        # Convert back to list and sort by timestamp (newest first)
        result = sorted(unique_runs.values(), key=lambda x: x['archive_timestamp'], reverse=True)

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/runs/<int:run_id>')
def get_run_details(run_id):
    """Get detailed data for a specific run"""
    try:
        run_data = archive.get_run_data(run_id)
        if run_data is None:
            return jsonify({'error': 'Run not found'}), 404
        return jsonify(run_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/keywords')
def get_keywords():
    """Get all keywords across all runs with their values"""
    try:
        keywords_data = []

        # Get all archived runs
        runs = archive.get_archived_runs()

        for run in runs:
            run_id = run.get('id')
            run_version = run.get('run_version', 'Unknown')

            # Get detailed run data
            run_data = archive.get_run_data(run_id)
            if run_data:
                # Handle nested structure: check for jobs->job_name->tasks or direct tasks
                tasks_data = {}

                if 'jobs' in run_data:
                    # New structure: jobs->job_name->tasks
                    for job_name, job_data in run_data['jobs'].items():
                        if 'tasks' in job_data:
                            tasks_data.update(job_data['tasks'])
                elif 'tasks' in run_data:
                    # Old structure: direct tasks
                    tasks_data = run_data['tasks']

                for task_name, task_data in tasks_data.items():
                    if 'keywords' in task_data:
                        for keyword_name, keyword_info in task_data['keywords'].items():
                            keywords_data.append({
                                'run_version': run_version,
                                'run_id': run_id,
                                'task_name': task_name,
                                'keyword_name': keyword_name,
                                'keyword_value': keyword_info.get('value', ''),
                                'keyword_unit': keyword_info.get('unit', ''),
                                'keyword_type': keyword_info.get('type', ''),
                                'source_file': keyword_info.get('source_file', ''),
                                'user_name': run.get('user_name', ''),
                                'archive_timestamp': run.get('archive_timestamp', '')
                            })

        return jsonify(keywords_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/keywords/summary')
def get_keywords_summary():
    """Get summary of all unique keywords and their statistics"""
    try:
        keywords_summary = {}

        # Get all archived runs
        runs = archive.get_archived_runs()

        for run in runs:
            run_id = run.get('id')

            # Get detailed run data
            run_data = archive.get_run_data(run_id)
            if run_data:
                # Handle nested structure: check for jobs->job_name->tasks or direct tasks
                tasks_data = {}

                if 'jobs' in run_data:
                    # New structure: jobs->job_name->tasks
                    for job_name, job_data in run_data['jobs'].items():
                        if 'tasks' in job_data:
                            tasks_data.update(job_data['tasks'])
                elif 'tasks' in run_data:
                    # Old structure: direct tasks
                    tasks_data = run_data['tasks']

                for task_name, task_data in tasks_data.items():
                    if 'keywords' in task_data:
                        for keyword_name, keyword_info in task_data['keywords'].items():
                            if keyword_name not in keywords_summary:
                                keywords_summary[keyword_name] = {
                                    'keyword_name': keyword_name,
                                    'count': 0,
                                    'tasks': set(),
                                    'runs': set(),
                                    'units': set(),
                                    'sample_values': []
                                }

                            summary = keywords_summary[keyword_name]
                            summary['count'] += 1
                            summary['tasks'].add(task_name)
                            summary['runs'].add(run.get('run_version', 'Unknown'))

                            unit = keyword_info.get('unit', '')
                            if unit:
                                summary['units'].add(unit)

                            value = keyword_info.get('value', '')
                            if value and len(summary['sample_values']) < 5:
                                summary['sample_values'].append(str(value))

        # Convert sets to lists for JSON serialization
        result = []
        for keyword_name, summary in keywords_summary.items():
            result.append({
                'keyword_name': keyword_name,
                'count': summary['count'],
                'tasks': sorted(list(summary['tasks'])),
                'runs': sorted(list(summary['runs'])),
                'units': sorted(list(summary['units'])),
                'sample_values': summary['sample_values']
            })

        # Sort by count (most frequent first)
        result.sort(key=lambda x: x['count'], reverse=True)

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/csv')
def export_csv():
    """Export archived data to CSV"""
    try:
        import tempfile
        import os
        from flask import send_file

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file.close()

        # Export to CSV
        success = archive.export_to_csv(temp_file.name)

        if not success:
            os.unlink(temp_file.name)
            return jsonify({'error': 'Export failed'}), 500

        # Send file
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=f'hawkeye_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            mimetype='text/csv'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/archive', methods=['POST'])
def trigger_archive():
    """Trigger archiving of new data (for integration)"""
    try:
        # This would integrate with hawkeyes_casino.py
        # For now, return a placeholder response
        return jsonify({
            'message': 'Archive trigger received',
            'status': 'Use the Archive button in Hawkeye GUI to archive data'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/comparison-view')
def comparison_view():
    """Serve the comparison view in a new window/tab"""
    return render_template_string(COMPARISON_TEMPLATE)
def main():
    """Run the web server"""
    import argparse

    parser = argparse.ArgumentParser(description="Hawkeye Web Server")
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    print(f"- Starting Hawkeye Web Server...")
    print(f"- Project Selector: http://{args.host}:{args.port}/select-project")
    print(f"- casino_prj_base: {os.getenv('casino_prj_base')}")

    # Discover available projects at startup
    projects = discover_projects()
    print(f"? Found {len(projects)} projects")

    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()
