/**
 * grouping.js - Keyword and task grouping logic from YAML configuration
 *
 * This file contains functions for grouping keywords and tasks based on
 * the YAML configuration file (vista_casino.yaml):
 * - matchesTemplate: Checks if keyword matches a template pattern
 * - getGroupOrderFromYAML: Gets the group order from YAML config
 * - groupKeywordsByConvention: Groups keywords by their YAML-defined groups
 * - loadKeywordGroupConfig: Loads the YAML configuration
 * - populateGroupFilter: Populates the group filter dropdown
 * - groupTasksByConvention: Groups tasks by naming conventions
 */

// Global variable to store YAML configuration
let keywordGroupConfig = null;

/**
 * Load keyword groups from YAML configuration
 * @returns {Promise<Object>} - The loaded configuration
 */
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

/**
 * Helper function to check if keyword matches a template-based pattern
 * @param {string} keyword - Keyword to check
 * @param {string} templateName - Template pattern to match against
 * @returns {boolean} - True if keyword matches template
 */
function matchesTemplate(keyword, templateName) {
    // Check if template contains variables like {mode}, {corner}, etc.
    if (!templateName.includes('{')) {
        return false;
    }

    // Convert template to regex pattern
    // Replace template variables with regex patterns
    let pattern = templateName
        .replace(/\{mode\}/g, '[^_]+')              // mode: any non-underscore chars
        .replace(/\{corner\}/g, '[^_]+(?:_[^_]+)*') // corner: can have underscores (e.g., ss_0p81v_m40c_Cworst_T)
        .replace(/\{path_type\}/g, '[^_]+')         // path_type: reg2reg, all, etc.
        .replace(/\{noise_type\}/g, '[^_]+')        // noise_type: above_low, below_high
        .replace(/\{task_name\}/g, '[^_]+')         // task_name: place, route, etc.
        // Escape special regex characters in the rest of the string
        .replace(/\./g, '\\.');

    // Create regex with anchors
    const regex = new RegExp('^' + pattern + '$');

    return regex.test(keyword);
}

/**
 * Helper function to get group order dynamically from YAML configuration
 * @returns {Array<string>} - Array of group names in preferred order
 */
function getGroupOrderFromYAML() {
    const groupSet = new Set();
    const preferredOrder = ['err/warn', 'timing', 'congestion', 'utilization'];

    // Extract all unique groups from YAML configuration
    // Check both 'tasks' and 'task_templates' sections
    if (keywordGroupConfig) {
        // Check tasks section
        if (keywordGroupConfig.tasks) {
            for (const taskName in keywordGroupConfig.tasks) {
                const task = keywordGroupConfig.tasks[taskName];
                if (task.keywords) {
                    for (const keywordConfig of task.keywords) {
                        if (keywordConfig.group) {
                            groupSet.add(keywordConfig.group);
                        }
                    }
                }
            }
        }

        // Check task_templates section
        if (keywordGroupConfig.task_templates) {
            for (const templateName in keywordGroupConfig.task_templates) {
                const template = keywordGroupConfig.task_templates[templateName];
                if (template.keywords) {
                    for (const keywordConfig of template.keywords) {
                        if (keywordConfig.group) {
                            groupSet.add(keywordConfig.group);
                        }
                    }
                }
            }
        }
    }

    // Build ordered list: preferred groups first, then remaining alphabetically
    const groupOrder = [];

    // Add preferred groups if they exist in YAML
    preferredOrder.forEach(group => {
        if (groupSet.has(group)) {
            groupOrder.push(group);
            groupSet.delete(group);
        }
    });

    // Add remaining groups alphabetically
    const remainingGroups = Array.from(groupSet).sort();
    groupOrder.push(...remainingGroups);

    return groupOrder;
}

/**
 * Group keywords by their YAML-defined groups
 * @param {Array<string>} keywords - Array of keyword names
 * @returns {Object} - Object mapping group names to arrays of keywords
 */
function groupKeywordsByConvention(keywords) {
    const groups = {};

    keywords.forEach(keyword => {
        let groupName = 'Other Keywords';

        // Get group from YAML configuration
        // Check both 'tasks' and 'task_templates' sections
        if (keywordGroupConfig) {
            // Search through tasks section
            if (keywordGroupConfig.tasks) {
                for (const taskName in keywordGroupConfig.tasks) {
                    const task = keywordGroupConfig.tasks[taskName];
                    if (task.keywords) {
                        for (const keywordConfig of task.keywords) {
                            // Try exact match first
                            if (keywordConfig.name === keyword && keywordConfig.group) {
                                groupName = keywordConfig.group;
                                break;
                            }
                            // Try prefix match for derived keywords (e.g., s_tns_all from s_tns)
                            if (keywordConfig.group && !keywordConfig.name.includes('{') &&
                                keyword.startsWith(keywordConfig.name + '_')) {
                                groupName = keywordConfig.group;
                                break;
                            }
                            // Try template match for template-based keywords
                            if (keywordConfig.group && matchesTemplate(keyword, keywordConfig.name)) {
                                groupName = keywordConfig.group;
                                break;
                            }
                        }
                    }
                    if (groupName !== 'Other Keywords') break;
                }
            }

            // If not found in tasks, search through task_templates section
            if (groupName === 'Other Keywords' && keywordGroupConfig.task_templates) {
                for (const templateName in keywordGroupConfig.task_templates) {
                    const template = keywordGroupConfig.task_templates[templateName];
                    if (template.keywords) {
                        for (const keywordConfig of template.keywords) {
                            // Try exact match first
                            if (keywordConfig.name === keyword && keywordConfig.group) {
                                groupName = keywordConfig.group;
                                break;
                            }
                            // Try prefix match for derived keywords (e.g., s_tns_all from s_tns)
                            if (keywordConfig.group && !keywordConfig.name.includes('{') &&
                                keyword.startsWith(keywordConfig.name + '_')) {
                                groupName = keywordConfig.group;
                                break;
                            }
                            // Try template match for template-based keywords
                            if (keywordConfig.group && matchesTemplate(keyword, keywordConfig.name)) {
                                groupName = keywordConfig.group;
                                break;
                            }
                        }
                    }
                    if (groupName !== 'Other Keywords') break;
                }
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

    // Sort groups - dynamically extract order from vista_casino.yaml
    const sortedGroups = {};
    const groupOrder = getGroupOrderFromYAML();

    // Add groups in YAML-defined order
    groupOrder.forEach(groupName => {
        if (groups[groupName]) {
            sortedGroups[groupName] = groups[groupName];
        }
    });

    // Add any additional groups found in data but not in YAML (shouldn't happen but be safe)
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

/**
 * Populate the group filter dropdown
 */
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

/**
 * Group tasks by naming conventions
 * @param {Array<string>} tasks - Array of task names
 * @returns {Object} - Object mapping group names to arrays of tasks
 */
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
