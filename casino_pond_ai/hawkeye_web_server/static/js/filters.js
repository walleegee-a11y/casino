/**
 * filters.js - All filtering logic for the comparison view
 *
 * This file contains all filter-related functions:
 * - initializeFilters: Sets up filter system on page load
 * - applyKeywordFilters: Filters keywords based on search and group selection
 * - filterComparisonData: Filters runs based on search term
 * - Task filtering functions (populateTaskFilter, toggleTaskSelection, etc.)
 * - Filter dropdown management
 * - Toggle empty rows/columns functionality
 */

// Filter system state variables
let selectedGroups = new Set();
let activeFilters = {};

/**
 * Initialize the filter system
 */
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

        // Sort tasks using YAML order
        filteredTasks = sortTasksByYAMLOrder(filteredTasks);

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

/**
 * Apply keyword filters based on search term and group selection
 * Uses matchesFilterExpression() from utils.js for consistent AND/OR/NOT logic
 */
function applyKeywordFilters() {
    const searchTerm = document.getElementById('keyword-search').value.trim();

    // Start with all keywords
    let filtered = [...comparisonData.keywords];

    // Apply text search filter with AND/OR/NOT logic using matchesFilterExpression()
    // This ensures consistent behavior with "Run Version" filter
    if (searchTerm) {
        filtered = filtered.filter(keyword => {
            // Use the centralized filter function from utils.js
            // This supports: OR (,), AND (+), NOT (! or -)
            return matchesFilterExpression(keyword, searchTerm);
        });

        console.log('Keyword Filter:', searchTerm);
        console.log('Filtered keywords count:', filtered.length);
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

/**
 * Filter comparison data based on run version search
 */
function filterComparisonData() {
    const searchTerm = document.getElementById('comparison-search').value.trim();

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

    // Filter runs based on run version with AND/OR logic
    if (window.originalComparisonData) {
        const filteredRuns = window.originalComparisonData.runs.filter(run => {
            // Safely check run_version (handle null/undefined)
            const runVersion = run.run_version || '';
            return matchesFilterExpression(runVersion, searchTerm);
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

/**
 * Clear all keyword filters
 */
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
    filteredTasks = sortTasksByYAMLOrder(filteredTasks);
    updateFilteredCount();
    updateTaskFilteredCount();
    renderComparison();
}

/**
 * Update the filtered keywords count display
 */
function updateFilteredCount() {
    const countElement = document.getElementById('filtered-keywords-count');
    if (countElement) {
        countElement.textContent = filteredKeywords.length;
    }
}

// ====================
// TASK FILTER FUNCTIONS
// ====================

/**
 * Populate the task filter dropdown
 */
function populateTaskFilter() {
    const taskOptions = document.getElementById('task-options');
    if (!taskOptions) return;

    // Use YAML-ordered list of tasks
    const allTasks = extractAllTasks(comparisonData.runs);
    const sortedTasks = sortTasksByYAMLOrder(allTasks);

    taskOptions.innerHTML = '';
    sortedTasks.forEach(taskName => {
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

/**
 * Toggle task selection in the filter
 * @param {string} taskName - Name of the task to toggle
 * @param {HTMLElement} element - The clicked element
 */
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

/**
 * Update the task filter button state
 */
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

/**
 * Apply task filters
 */
function applyTaskFilters() {
    // Filter tasks based on selection
    if (selectedTasks.size > 0) {
        // Sort selected tasks using YAML order
        filteredTasks = sortTasksByYAMLOrder(Array.from(selectedTasks));
    } else {
        // Get all tasks and sort them using YAML order
        const allTasks = extractAllTasks(comparisonData.runs);
        filteredTasks = sortTasksByYAMLOrder(allTasks);
    }

    updateTaskFilteredCount();
    renderComparison();
}

/**
 * Clear task filters
 */
function clearTaskFilters() {
    selectedTasks.clear();

    // Clear visual selection
    document.querySelectorAll('#task-options a').forEach(link => {
        link.classList.remove('selected');
    });

    updateTaskFilterButtonState();
    applyTaskFilters();
}

/**
 * Update the filtered tasks count display
 */
function updateTaskFilteredCount() {
    const countElement = document.getElementById('filtered-tasks-count');
    if (countElement) {
        countElement.textContent = filteredTasks.length;
    }
}

/**
 * Select all task options
 */
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

/**
 * Clear all task options
 */
function clearAllTaskOptions() {
    selectedTasks.clear();

    document.querySelectorAll('#task-options a').forEach(link => {
        link.classList.remove('selected');
    });

    updateTaskFilterButtonState();
    applyTaskFilters();
}

// ====================
// GROUP FILTER FUNCTIONS
// ====================

/**
 * Toggle filter dropdown visibility
 * @param {string} filterType - Type of filter ('group' or 'task')
 */
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

/**
 * Toggle group selection
 * @param {string} groupName - Name of the group to toggle
 * @param {HTMLElement} element - The clicked element
 */
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

/**
 * Update the group filter button state
 */
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

/**
 * Select all filter options
 * @param {string} filterType - Type of filter ('group')
 */
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

/**
 * Clear all filter options
 * @param {string} filterType - Type of filter ('group')
 */
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

/**
 * Filter dropdown items based on search
 * @param {string} filterType - Type of filter ('group')
 */
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

/**
 * Toggle empty rows and columns visibility
 */
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

/**
 * Filter runs to only include specified tasks
 * @param {Array} runs - Array of run objects
 * @param {Array<string>} allowedTasks - Array of allowed task names
 * @returns {Array} - Filtered array of runs
 */
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
