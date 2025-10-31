/**
 * comparison.js - Main comparison view logic
 *
 * This file contains the core comparison view functionality:
 * - Global variables (comparisonData, isTransposed, currentView, etc.)
 * - Window load event listener
 * - loadComparisonData: Main data loading function
 * - renderComparison: Main render function
 * - renderNormalView: Render keywords-as-rows view
 * - renderTransposedView: Render runs-as-rows view
 * - getVisibleDataFor* functions: Filter visible data based on hideEmpty setting
 * - toggleView: Switch between normal and transposed views
 * - Column dragging/resizing functions
 * - exportComparison: Export data to TSV
 */

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

// Load comparison data from sessionStorage
window.addEventListener('load', function() {
    console.log('=== Window load event fired ===');

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

/**
 * Load comparison data from sessionStorage
 */
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

            // Extract task order from YAML after loading config
            if (keywordGroupConfig) {
                taskOrderFromYAML = extractTaskOrderFromYAML(keywordGroupConfig);
                console.log('Extracted task order from YAML:', taskOrderFromYAML.length, 'tasks');
            }
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

/**
 * Render the comparison view based on current settings
 */
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

    // Enable column resize
    enableColumnResize();

    // Recalculate column widths after rendering is complete
    setTimeout(() => {
        applyCalculatedColumnWidths();
    }, 50);
}

/**
 * Render normal view (keywords as rows)
 */
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
    html += '<th style="background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%); color: white; position: sticky; left: 0; top: 0; z-index: 30; min-width: ' + columnWidths.firstColumn + 'px; max-width: ' + (columnWidths.firstColumn + 50) + 'px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; border-right: 2px solid #555;">Keyword</th>';
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

/**
 * Get visible data for normal view (respects hideEmptyColumns setting)
 * @param {Array} runs - Array of run objects
 * @param {Array<string>} keywords - Array of keyword names
 * @returns {Object} - Object with visibleRuns and visibleKeywords arrays
 */
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

/**
 * Render transposed view (runs as rows)
 */
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

    html += '</tbody></table>';
    content.innerHTML = html;
}

/**
 * Get visible data for transposed view (respects hideEmptyColumns setting)
 * @param {Array} runs - Array of run objects
 * @param {Array<string>} keywords - Array of keyword names
 * @returns {Object} - Object with visibleRuns and visibleKeywords arrays
 */
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

/**
 * Toggle between normal and transposed views
 */
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

// ====================
// COLUMN DRAGGING
// ====================

let draggedColumn = null;
let draggedColumnIndex = null;

/**
 * Make table columns draggable
 */
function makeColumnsDraggable() {
    const table = document.querySelector('table');
    if (!table) return;

    const headerRow = table.querySelector('thead tr');
    const headerCells = headerRow.querySelectorAll('th');

    headerCells.forEach((headerCell, index) => {
        if (index === 0) return; // Skip first column

        // Make draggable
        headerCell.draggable = true;
        headerCell.dataset.columnIndex = index;

        // Add event listeners
        headerCell.addEventListener('dragstart', handleDragStart);
        headerCell.addEventListener('dragover', handleDragOver);
        headerCell.addEventListener('drop', handleDrop);
    });
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

// ====================
// COLUMN RESIZING
// ====================

/**
 * Enable column resizing functionality
 */
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

/**
 * Calculate appropriate column widths based on content
 * @returns {Object} - Object with firstColumn and secondColumn width values
 */
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

/**
 * Apply calculated column widths to existing table
 */
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

/**
 * Auto-fit all columns
 */
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

// ====================
// EXPORT FUNCTIONALITY
// ====================

/**
 * Export comparison data to TSV file
 */
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
    alert(`Exported ${visibleKeywords.length} keywords from ${visibleRuns.length} runs in ${viewType} format.\n\nFilename: ${filename}\n\nThe TSV matches exactly what you see in the table with tab separators.`);
}
