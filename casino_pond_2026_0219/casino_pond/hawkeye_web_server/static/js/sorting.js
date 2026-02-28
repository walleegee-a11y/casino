/**
 * sorting.js - Sorting logic for comparison view
 *
 * This file contains functions for sorting runs and tasks:
 * - extractTaskOrderFromYAML: Extracts task order from YAML configuration
 * - sortTasksByYAMLOrder: Sorts tasks based on YAML-defined order
 * - toggleRunVersionSort: Toggles run version sorting direction
 * - applySorting: Applies current sort settings to runs
 */

// Global variable to store task order from YAML
let taskOrderFromYAML = [];

// Global sort state
let currentSortDirection = 'asc';

/**
 * Function to extract task order from YAML configuration
 * @param {Object} yamlConfig - YAML configuration object
 * @returns {Array<string>} - Array of task names in order
 */
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

/**
 * Function to sort tasks based on YAML order
 * @param {Array<string>} tasks - Array of task names to sort
 * @returns {Array<string>} - Sorted array of task names
 */
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

/**
 * Toggle run version sort direction
 */
function toggleRunVersionSort() {
    // Toggle sort direction
    currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';

    // Update button text
    const button = document.getElementById('sort-toggle-btn');
    button.textContent = currentSortDirection === 'asc' ? 'Run Version: A -> Z' : 'Run Version: Z <- A';

    // Apply sorting
    applySorting();
}

/**
 * Apply current sorting to runs
 */
function applySorting() {
    if (window.originalComparisonData && comparisonData) {
        let sortedRuns = [...window.originalComparisonData.runs];

        // Apply search filter first with AND/OR logic
        const searchTerm = document.getElementById('comparison-search').value.trim();
        if (searchTerm) {
            sortedRuns = sortedRuns.filter(run => {
                const runVersion = run.run_version || '';
                return matchesFilterExpression(runVersion, searchTerm);
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
