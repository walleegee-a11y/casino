/**
 * dashboard.js - Main dashboard functionality for Hawkeye
 * Dependencies: utils.js, modal.js, sorting.js, filters.js, grouping.js
 */

// Global variables
let allRunVersions = [];
let allKeywords = [];
let allRuns = [];
let originalAllRuns = [];
let currentComparisonRuns = [];
let graphData = null;
let selectedNode = null;
let graphSimulation = null;
let currentView = 'table';
let activeFilters = {
    'run-version': [],
    'user': [],
    'block': [],
    'dk': []
};
let jobsConfig = null;  // Store jobs configuration from vista_casino.yaml
let currentViewMode = 'task';  // 'task', 'job', or 'both'

/**
 * Aggregate multiple tasks into a job-level aggregate
 * @param {Object} tasks - Dictionary of task_name -> array of keyword objects
 * @returns {Array} - Array of aggregated keyword objects
 */
function aggregateTasksToJob(tasks) {
    if (!tasks || Object.keys(tasks).length === 0) {
        return [];
    }

    // Aggregate keywords - tasks is { "DRC": [...keywords...], "LVS": [...keywords...] }
    const aggregateKeywords = {};
    for (const taskName in tasks) {
        const keywordsArray = tasks[taskName];  // This is an ARRAY of keyword objects

        if (!Array.isArray(keywordsArray)) {
            console.warn('Task keywords is not an array:', taskName, keywordsArray);
            continue;
        }

        // Iterate through the array of keywords for this task
        keywordsArray.forEach(kwData => {
            const kwName = kwData.keyword_name;

            if (!aggregateKeywords[kwName]) {
                // First occurrence - initialize
                aggregateKeywords[kwName] = {
                    values: [],
                    unit: kwData.keyword_unit || '',
                    type: kwData.keyword_type || ''
                };
            }

            // Collect value
            const value = kwData.keyword_value;
            if (value !== null && value !== undefined && value !== '' && value !== '--') {
                // Try to parse as number
                const numValue = parseFloat(value);
                if (!isNaN(numValue)) {
                    aggregateKeywords[kwName].values.push(numValue);
                } else {
                    aggregateKeywords[kwName].values.push(value);
                }
            }
        });
    }

    // Compute aggregate values for each keyword
    const finalKeywordsArray = [];
    for (const kwName in aggregateKeywords) {
        const kwInfo = aggregateKeywords[kwName];
        const values = kwInfo.values;

        if (!values || values.length === 0) {
            continue;
        }

        // Determine aggregation strategy based on keyword type
        if (values.every(v => typeof v === 'number')) {
            // Numeric values - choose aggregation strategy
            let aggregateValue;

            if (kwName.toLowerCase().includes('error') ||
                kwName.toLowerCase().includes('warning') ||
                kwName.toLowerCase().includes('_num') ||
                kwName.toLowerCase().includes('count')) {
                // Sum for counts and violations
                aggregateValue = values.reduce((a, b) => a + b, 0);
            } else if (kwName.toLowerCase().includes('wns')) {
                // WNS (Worst Negative Slack): take MIN (most negative = worst)
                aggregateValue = Math.min(...values);
            } else if (kwName.toLowerCase().includes('tns')) {
                // TNS (Total Negative Slack): SUM all slack violations
                aggregateValue = values.reduce((a, b) => a + b, 0);
            } else if (kwName.toLowerCase().includes('nov')) {
                // NOV (Number of Violations): SUM
                aggregateValue = values.reduce((a, b) => a + b, 0);
            } else if (kwName.toLowerCase().includes('cpu_time') ||
                       kwName.toLowerCase().includes('real_time') ||
                       kwName.toLowerCase().includes('runtime')) {
                // Runtime: SUM
                aggregateValue = values.reduce((a, b) => a + b, 0);
            } else if (kwName.toLowerCase().includes('area') ||
                       kwName.toLowerCase().includes('utilization') ||
                       kwName.toLowerCase().includes('density')) {
                // Area/utilization: use LAST value (final stage)
                aggregateValue = values[values.length - 1];
            } else if (kwName.toLowerCase().includes('overflow') ||
                       kwName.toLowerCase().includes('hotspot')) {
                // Congestion: take MAX (worst)
                aggregateValue = Math.max(...values);
            } else {
                // Default: AVERAGE for other metrics
                aggregateValue = values.reduce((a, b) => a + b, 0) / values.length;
            }

            finalKeywordsArray.push({
                keyword_name: kwName,
                keyword_value: aggregateValue,
                keyword_unit: kwInfo.unit,
                keyword_type: kwInfo.type
            });
        } else if (values.every(v => typeof v === 'string')) {
            // String values - concatenate or pick representative
            const uniqueValues = [...new Set(values)];
            if (uniqueValues.length === 1) {
                // All same - use that value
                finalKeywordsArray.push({
                    keyword_name: kwName,
                    keyword_value: values[0],
                    keyword_unit: kwInfo.unit,
                    keyword_type: kwInfo.type
                });
            } else {
                // Different values - show "MIXED"
                finalKeywordsArray.push({
                    keyword_name: kwName,
                    keyword_value: "MIXED",
                    keyword_unit: kwInfo.unit,
                    keyword_type: kwInfo.type
                });
            }
        }
    }

    return finalKeywordsArray;
}

/**
 * Load jobs configuration from vista_casino.yaml
 */
async function loadJobsConfig() {
    try {
        const response = await fetch('/api/jobs');
        if (response.ok) {
            jobsConfig = await response.json();
            console.log('Loaded jobs config:', Object.keys(jobsConfig || {}).length, 'jobs');
        } else {
            console.warn('Failed to load jobs config');
        }
    } catch (error) {
        console.error('Error loading jobs config:', error);
    }
}

/**
 * Compute aggregates for a run's keywords
 * @param {Object} runKeywords - Run's keywords grouped by task
 * @returns {Object} - Keywords with aggregates added
 */
function computeAggregatesForRun(runKeywords) {
    if (!jobsConfig || !runKeywords) {
        return runKeywords;
    }

    const result = { ...runKeywords };

    // For each job, compute aggregate if all tasks are present
    for (const jobName in jobsConfig) {
        const job = jobsConfig[jobName];
        const tasksList = job.tasks || [];

        // Collect tasks for this job
        const jobTasks = {};
        let allTasksPresent = true;

        for (const taskName of tasksList) {
            if (runKeywords[taskName]) {
                jobTasks[taskName] = runKeywords[taskName];
            } else {
                // Task missing - can't compute aggregate
                allTasksPresent = false;
                break;
            }
        }

        // Compute aggregate if all tasks present
        if (allTasksPresent && Object.keys(jobTasks).length > 0) {
            const aggregateKeywordsArray = aggregateTasksToJob(jobTasks);
            const aggregateName = `${jobName}_all`;

            // Add task_name property to each keyword
            aggregateKeywordsArray.forEach(kw => {
                kw.task_name = aggregateName;
            });

            result[aggregateName] = aggregateKeywordsArray;
        }
    }

    return result;
}

// Load statistics on page load
document.addEventListener('DOMContentLoaded', function() {
    // Load current project name, statistics, and jobs config together
    Promise.all([
        fetch('/api/current-project').then(r => r.json()),
        fetch('/api/statistics').then(r => r.json()),
        loadJobsConfig()
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

/**
 * Load statistics from API
 */
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

/**
 * Repair archive - detect and import orphaned data files
 */
async function repairArchive() {
    const button = event.target;
    const originalText = button.textContent;

    button.disabled = true;
    button.textContent = 'Repairing...';
    button.style.opacity = '0.6';

    try {
        const response = await fetch('/api/repair-archive', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            alert('Archive repair completed!\n\nReloading data...');

            // Reload statistics and runs
            await loadStatistics();
            await loadRuns();
        } else {
            alert('Archive repair failed: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error repairing archive:', error);
        alert('Error repairing archive: ' + error.message);
    } finally {
        button.disabled = false;
        button.textContent = originalText;
        button.style.opacity = '1';
    }
}

/**
 * Load runs from API and populate table
 */
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

/**
 * Update table with filtered runs
 * @param {Array} runs - Array of run objects to display
 */
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
                        <th onclick="sortTable('archive_timestamp')" style="cursor: pointer; user-select: none;" title="Click to sort by Archived Date">
                            Archived <span id="archive_timestamp-sort" class="sort-indicator">#</span>
                        </th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    `;

    runs.forEach((run, index) => {
        const archiveDate = formatDate(run.archive_timestamp);
        const taskCount = Object.keys(run.keywords).length;
        const keywordCount = Object.values(run.keywords).flat().length;

            html += `
                <tr data-index="${index}" data-run-id="${run.run_version}">
                    <td style="text-align: center;">
                        <input type="checkbox" class="run-checkbox" data-run-id="${run.run_version}" data-run-version="${run.run_version}">
                    </td>
                <td style="text-align: center;">
                    <button onclick="showRunDetailsModal(${index})"
                            style="padding: 2px 4px; background: #2980b9; color: white; border: 1px solid #2980b9; cursor: pointer; font-size: 10px; border-radius: 3px;">
                        Details
                    </button>
                </td>
                <td><strong>${run.run_version}</strong></td>
                <td>${run.user_name}</td>
                <td>${run.block_name}</td>
                <td>${run.dk_ver_tag}</td>
                <td style="text-align: center;"><span style="background: #27ae60; color: white; padding: 2px 6px; border-radius: 3px;">${taskCount}</span></td>
                <td style="text-align: center;"><span style="background: #c0392b; color: white; padding: 2px 6px; border-radius: 3px;">${keywordCount}</span></td>
                <td>${archiveDate}</td>
                                            <td>
                        <button class="btn" onclick="viewRunDetails('${run.run_version}')" style="padding: 2px 6px; font-size: 10px;">
                            Open
                        </button>
                    </td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    table.innerHTML = html;
}

/**
 * Toggle all run checkboxes
 */
function toggleAllRuns() {
    const selectAllCheckbox = document.getElementById('select-all-runs-checkbox');
    const checkboxes = document.querySelectorAll('.run-checkbox');

    checkboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
}

/**
 * Select all visible runs
 */
function selectAllRuns() {
    const checkboxes = document.querySelectorAll('.run-checkbox');

    checkboxes.forEach(checkbox => {
        checkbox.checked = true;
    });

    document.getElementById('select-all-runs-checkbox').checked = true;
}

/**
 * Filter runs by run version search term with AND/OR/NOT logic
 * Uses matchesFilterExpression() from utils.js for consistent filtering
 * Supports:
 * - OR logic with ',' (comma): "PI,FE" matches PI OR FE
 * - AND logic with '+' (plus): "PI+PD" matches runs containing BOTH PI AND PD
 * - NOT logic with '!' or '-': "!error" excludes runs containing "error"
 * - Combined: "PI+PD,FE,!error" = (PI AND PD) OR FE, BUT NOT error
 */
function filterByRunVersion() {
    const searchTerm = document.getElementById('run-version-search').value.trim();

    if (!searchTerm) {
        loadRuns(); // Reload with current filters
        return;
    }

    // Start with original unfiltered data, then apply auto-filters
    let baseFiltered = applyAutoFilters([...originalAllRuns]);

    // Filter runs using matchesFilterExpression() for AND/OR/NOT logic
    const filteredRuns = baseFiltered.filter(run => {
        return matchesFilterExpression(run.run_version, searchTerm);
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

/**
 * Clear all filters and reset view
 */
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

/**
 * Compare selected runs in a new window
 */
function compareSelectedRuns() {
    const checkboxes = document.querySelectorAll('.run-checkbox:checked');

    if (checkboxes.length < 1) {
        alert('Please select at least 1 run version to compare.');
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

/**
 * Show comparison in new window
 * @param {Array} runs - Array of run objects to compare
 */
function showComparison(runs) {
    console.log('=== showComparison called ===');
    console.log('Runs received:', runs.length);

    if (!runs || runs.length === 0) {
        alert('No runs selected for comparison.');
        return;
    }

    currentComparisonRuns = runs;

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

        // Compute aggregates for this run (pv_all, sta_pt_all, apr_inn_all, etc.)
        formattedRun.keywords = computeAggregatesForRun(formattedRun.keywords);

        return formattedRun;
    });

    // Recollect all keyword names including aggregates
    var allKeywordNamesWithAggregates = new Set();
    formattedRuns.forEach(function(run) {
        Object.values(run.keywords).forEach(function(taskKeywords) {
            if (Array.isArray(taskKeywords)) {
                taskKeywords.forEach(function(keyword) {
                    if (keyword && keyword.keyword_name) {
                        allKeywordNamesWithAggregates.add(keyword.keyword_name);
                    }
                });
            }
        });
    });

    var comparisonData = {
        runs: formattedRuns,
        keywords: Array.from(allKeywordNamesWithAggregates).sort(),
        originalKeywords: Array.from(allKeywordNamesWithAggregates).sort(),
        isTransposed: false,
        timestamp: new Date().toISOString(),
        comparisonId: 'comparison_' + Date.now(),
        runCount: formattedRuns.length,
        keywordCount: allKeywordNamesWithAggregates.size
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

/**
 * Cleanup comparison interface
 */
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

/**
 * Export selected runs to CSV
 */
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

/**
 * View run details in new window
 * @param {string} runVersion - Run version to display
 */
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
                        <h1>Run Details</h1>
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

// Global sorting state
let currentSortColumn = null;
let currentSortDirection = 'asc';
let isTransposed = false;

/**
 * Sort table by column
 * @param {string} column - Column name to sort by
 */
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

/**
 * Export all data to CSV
 */
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

/**
 * Get all available keywords from runs
 * @param {Array} runs - Array of run objects
 * @returns {Array<string>} - Sorted array of unique keyword names
 */
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

/**
 * Open comparison in new window
 * @param {Array} runs - Array of run objects
 * @param {Array<string>} selectedKeywords - Array of selected keyword names
 * @param {boolean} isTransposed - Whether to show transposed view
 */
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

// ====================
// AUTO-FILTER FUNCTIONS
// ====================

/**
 * Initialize auto-filters
 */
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

/**
 * Populate filter options in dropdown
 * @param {string} filterType - Type of filter
 * @param {Array} options - Array of option values
 */
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

/**
 * Apply dynamic dropdown height based on item count
 * @param {string} filterType - Type of filter
 * @param {number} itemCount - Number of items
 */
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

/**
 * Toggle filter dropdown visibility
 * @param {string} filterType - Type of filter
 */
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

/**
 * Filter dropdown items based on search
 * @param {string} filterType - Type of filter
 */
function filterDropdownItems(filterType) {
    const searchTerm = document.querySelector(`#${filterType}-dropdown .filter-search`).value.toLowerCase();
    let options;

    if (filterType === 'task') {
        options = document.querySelectorAll(`#${filterType}-options a`);
    } else {
        options = document.querySelectorAll(`#${filterType}-options a`);
    }

    let visibleCount = 0;
    options.forEach(option => {
        const text = option.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
            option.style.display = 'block';
            visibleCount++;
        } else {
            option.style.display = 'none';
        }
    });

    // Update dropdown height based on visible items
    applyDynamicDropdownHeight(filterType, visibleCount);
}

/**
 * Toggle filter option selection
 * @param {string} filterType - Type of filter
 * @param {string} option - Option value
 */
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

/**
 * Update filter options visual state
 * @param {string} filterType - Type of filter
 */
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

/**
 * Update filter buttons text and state
 */
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

/**
 * Select all filter options for a given filter type
 * @param {string} filterType - Type of filter
 */
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

/**
 * Clear all filter options for a given filter type
 * @param {string} filterType - Type of filter
 */
function clearAllFilterOptions(filterType) {
    activeFilters[filterType] = [];
    updateFilterOptions(filterType);
    updateFilterButtons();
    loadRuns();
}

/**
 * Apply auto-filters to runs array
 * @param {Array} runs - Array of run objects
 * @returns {Array} - Filtered array of runs
 */
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

