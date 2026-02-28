/**
 * utils.js - Common utility functions used across the Hawkeye dashboard
 */

/**
 * Format a date string to locale date/time format
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date string
 */
function formatDate(dateString) {
    return new Date(dateString).toLocaleString('en-US', {
        month: '2-digit',
        day: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
}

/**
 * Check if a value is empty (null, undefined, '-', 'null', 'NULL', 'None', or empty string)
 * @param {*} value - Value to check
 * @returns {boolean} True if value is empty
 */
function isValueEmpty(value) {
    if (value === null || value === undefined) return true;
    if (value === '-') return true;
    if (value === 'null') return true;
    if (value === 'NULL') return true;
    if (value === 'None') return true;
    if (value === '') return true;
    return false;
}

/**
 * Helper function to match text against filter expression with AND/OR/NOT logic
 *
 * Syntax:
 * - Comma (,) = OR logic: "timing,power" matches "timing" OR "power"
 * - Plus (+) = AND logic: "timing+setup" matches text containing BOTH "timing" AND "setup"
 * - Exclamation (!) or Minus (-) = NOT/exclude logic: "!error,-warning" excludes "error" and "warning"
 * - Combined: "timing+setup,power,!error" = (timing AND setup) OR power, BUT NOT error
 *
 * @param {string} text - Text to match against
 * @param {string} filterExpression - Filter expression with AND/OR/NOT logic
 * @returns {boolean} - True if text matches the filter expression
 *
 * @example
 * matchesFilterExpression("timing_setup_wns", "timing+setup") // true - contains both
 * matchesFilterExpression("timing_hold_wns", "timing,power") // true - contains timing
 * matchesFilterExpression("error_count", "!error") // false - excluded
 * matchesFilterExpression("timing_setup", "timing,!error") // true - contains timing, no error
 * matchesFilterExpression("timing_error", "timing,!error") // false - contains error (excluded)
 */
function matchesFilterExpression(text, filterExpression) {
    if (!filterExpression || !text) {
        return true;
    }

    const textLower = text.toLowerCase();
    const filterLower = filterExpression.toLowerCase().trim();

    // First, extract all EXCLUDE terms (starting with ! or -)
    const excludeTerms = [];
    const includeGroups = [];

    // Split by comma to get all terms/groups
    const allTerms = filterLower.split(',')
        .map(term => term.trim())
        .filter(term => term.length > 0);

    // Separate exclude terms from include terms
    allTerms.forEach(term => {
        if (term.startsWith('!') || term.startsWith('-')) {
            // Remove the ! or - prefix and add to exclude list
            const excludeTerm = term.substring(1).trim();
            if (excludeTerm.length > 0) {
                excludeTerms.push(excludeTerm);
            }
        } else {
            // Regular include term
            includeGroups.push(term);
        }
    });

    // STEP 1: Check EXCLUDE terms first (NOT logic)
    // If text contains ANY exclude term, immediately return false
    for (const excludeTerm of excludeTerms) {
        if (textLower.includes(excludeTerm)) {
            return false; // Excluded!
        }
    }

    // STEP 2: If no include terms specified, and we passed exclude check, return true
    if (includeGroups.length === 0) {
        return true; // Only had exclude terms, and text doesn't contain them
    }

    // STEP 3: Check INCLUDE terms (AND/OR logic)
    // Text must match at least one include group
    return includeGroups.some(orGroup => {
        // Within each OR group, check for AND logic ('+' separator)
        if (orGroup.includes('+')) {
            // AND logic: text must contain ALL terms in this group
            const andTerms = orGroup.split('+')
                .map(term => term.trim())
                .filter(term => term.length > 0);

            // Text must contain ALL AND terms
            return andTerms.every(term => textLower.includes(term));
        } else {
            // Simple term: text must contain this term
            return textLower.includes(orGroup);
        }
    });
}

/**
 * Show a temporary message notification
 * @param {string} message - Message to display
 * @param {string} type - Message type ('success', 'error', 'info', 'warning')
 * @param {number} duration - Duration in milliseconds (default: 3000)
 */
function showMessage(message, type = 'info', duration = 3000) {
    const messageElement = document.createElement('div');
    messageElement.className = `message message-${type}`;

    const colors = {
        success: '#27ae60',
        error: '#e74c3c',
        info: '#3498db',
        warning: '#f39c12'
    };

    messageElement.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${colors[type] || colors.info};
        color: white;
        padding: 10px 15px;
        border-radius: 4px;
        font-size: 12px;
        z-index: 10000;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        transition: opacity 0.3s ease;
    `;

    messageElement.textContent = message;
    document.body.appendChild(messageElement);

    setTimeout(() => {
        messageElement.style.opacity = '0';
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.parentNode.removeChild(messageElement);
            }
        }, 300);
    }, duration);
}

/**
 * Extract unique keyword units from runs
 * @param {Array} runs - Array of run objects
 * @returns {Object} Map of keyword names to units
 */
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

/**
 * Get all available keywords from runs
 * @param {Array} runs - Array of run objects
 * @returns {Array} Sorted array of unique keyword names
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
 * Extract all unique tasks from runs
 * @param {Array} runs - Array of run objects
 * @returns {Array} Array of unique task names
 */
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

    return Array.from(allTasks);
}

/**
 * Update the comparison description header
 * Used by comparison.html
 */
function updateComparisonDescription() {
    if (comparisonData) {
        const description = document.getElementById('comparison-description');
        const timestamp = new Date(comparisonData.timestamp).toLocaleString();

        description.innerHTML = `Comparison View - Created: ${timestamp}`;

        // Update page title with comparison info
        document.title = `Hawkeye Comparison - ${comparisonData.runs.length} runs`;
    }
}

/**
 * Display error message to the user
 * Used by comparison.html
 * @param {string} message - Error message to display
 */
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

/**
 * Update the statistics grid with current data
 * Used by comparison.html
 */
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

