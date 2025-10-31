# -*- coding: utf-8 -*-
"""Keyword grouping logic based on YAML configuration

This module provides functions to group keywords based on their definitions
in vista_casino.yaml configuration file.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Set, Optional


def natural_sort_key(text: str):
    """Generate a key for natural (alphanumeric) sorting with prefix priority

    For STA keywords (containing mode_corner patterns), sorts by prefix first:
    - Example: "misn_ff_A.._max_cap_num" -> prioritize "misn_ff_A.." over "_max_cap_num"
    - Result: Groups by mode/corner (A, B) before grouping by metric (num, worst)

    For other keywords, splits into text and number parts for proper numeric ordering.
    - Example: "s_wns_2" comes before "s_wns_10" (not after)

    Args:
        text: String to generate sort key for

    Returns:
        Tuple of (prefix_key, suffix_key) for sorting
    """
    def atoi(s):
        return int(s) if s.isdigit() else s.lower()

    # Check if this looks like an STA keyword with mode_corner pattern
    # Pattern: {mode}_{corner}_{metric}_{type}
    # Examples: misn_ff_0p99v_m40c_Cbest_s_wns_all, misn_ff_A.._max_cap_num

    # Look for common STA metric patterns at the end
    sta_metric_patterns = [
        '_max_cap_num', '_max_cap_worst',
        '_max_tran_num', '_max_tran_worst',
        '_noise_above_low_num', '_noise_above_low_worst',
        '_noise_below_high_num', '_noise_below_high_worst',
        '_s_wns_', '_s_tns_', '_s_num_',
        '_h_wns_', '_h_tns_', '_h_num_'
    ]

    # Try to find a matching pattern
    prefix_end = -1
    matched_suffix = None

    for pattern in sta_metric_patterns:
        if pattern in text:
            idx = text.rfind(pattern)
            if idx > prefix_end:
                prefix_end = idx
                matched_suffix = text[idx:]

    if prefix_end > 0:
        # Split into prefix (mode_corner) and suffix (metric)
        prefix = text[:prefix_end]
        suffix = matched_suffix

        # Apply natural sort to both parts
        prefix_key = [atoi(c) for c in re.split(r'(\d+)', prefix)]
        suffix_key = [atoi(c) for c in re.split(r'(\d+)', suffix)]

        # Return tuple: sort by prefix first, then suffix
        return (prefix_key, suffix_key)

    # For non-STA keywords, use simple natural sort
    simple_key = [atoi(c) for c in re.split(r'(\d+)', text)]
    return (simple_key, [])  # Empty suffix so non-STA keywords sort together


def load_yaml_config(config_path: Optional[str] = None) -> Optional[Dict]:
    """Load YAML configuration file

    Args:
        config_path: Path to YAML configuration file. If None, looks for vista_casino.yaml
                    in the project root directory.

    Returns:
        Parsed YAML configuration as dictionary, or None if loading fails
    """
    if config_path is None:
        # Try to find vista_casino.yaml in project root
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / "vista_casino.yaml"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            print(f"Loaded YAML config from: {config_path}")
            return config
    except FileNotFoundError:
        print(f"WARNING: YAML config not found at: {config_path}")
        return None
    except yaml.YAMLError as e:
        print(f"ERROR: Failed to parse YAML config: {e}")
        return None
    except Exception as e:
        print(f"ERROR: Unexpected error loading YAML config: {e}")
        return None


def matches_template(keyword: str, template_name: str) -> bool:
    """Check if keyword matches a template-based pattern

    Templates use placeholders like {mode}, {corner}, {path_type}, etc.

    Args:
        keyword: Keyword name to check
        template_name: Template pattern to match against

    Returns:
        True if keyword matches the template pattern

    Examples:
        >>> matches_template("misn_ff_0p99v_m40c_Cbest_s_wns_all", "{mode}_{corner}_s_wns_{path_type}")
        True
        >>> matches_template("hotspot_Max", "hotspot")
        False
    """
    # Check if template contains variables
    if '{' not in template_name:
        return False

    # Convert template to regex pattern
    # Replace template variables with regex patterns
    pattern = template_name
    pattern = pattern.replace('{mode}', r'[^_]+')                # mode: any non-underscore chars
    pattern = pattern.replace('{corner}', r'[^_]+(?:_[^_]+)*')   # corner: can have underscores
    pattern = pattern.replace('{path_type}', r'[^_]+')           # path_type: reg2reg, all, etc.
    pattern = pattern.replace('{noise_type}', r'[^_]+')          # noise_type: above_low, below_high
    pattern = pattern.replace('{task_name}', r'[^_]+')           # task_name: place, route, etc.

    # Escape special regex characters in the rest of the string
    pattern = pattern.replace('.', r'\.')

    # Create regex with anchors
    regex = re.compile(f'^{pattern}$')

    return bool(regex.match(keyword))


def get_group_order_from_yaml(config: Dict) -> List[str]:
    """Get group order dynamically from YAML configuration

    Args:
        config: Parsed YAML configuration dictionary

    Returns:
        List of group names in preferred order
    """
    group_set = set()

    # Preferred order for common groups
    preferred_order = ['err/warn', 'timing', 'congestion', 'utilization']

    # Extract all unique groups from YAML configuration
    # Check both 'tasks' and 'task_templates' sections
    if config:
        # Check tasks section
        if 'tasks' in config:
            for task_name, task_config in config['tasks'].items():
                if task_config and 'keywords' in task_config:
                    for keyword_config in task_config['keywords']:
                        if 'group' in keyword_config:
                            group_set.add(keyword_config['group'])

        # Check task_templates section
        if 'task_templates' in config:
            for template_name, template_config in config['task_templates'].items():
                if template_config and 'keywords' in template_config:
                    for keyword_config in template_config['keywords']:
                        if 'group' in keyword_config:
                            group_set.add(keyword_config['group'])

    # Build ordered list: preferred groups first, then remaining alphabetically
    group_order = []

    # Add preferred groups if they exist in YAML
    for group in preferred_order:
        if group in group_set:
            group_order.append(group)
            group_set.remove(group)

    # Add remaining groups alphabetically
    remaining_groups = sorted(list(group_set))
    group_order.extend(remaining_groups)

    return group_order


def group_keywords_by_yaml(keywords: List[str], config: Optional[Dict] = None) -> Dict[str, List[str]]:
    """Group keywords by their YAML-defined groups

    Args:
        keywords: List of keyword names to group
        config: Parsed YAML configuration. If None, attempts to load it.

    Returns:
        Dictionary mapping group names to lists of keywords

    Example:
        {
            'timing': ['s_wns_all', 's_tns_reg2reg', 'h_wns_all'],
            'err/warn': ['error', 'warning'],
            'Other Keywords': ['custom_metric']
        }
    """
    if config is None:
        config = load_yaml_config()
        if config is None:
            # Fallback: all keywords in "Other Keywords" group
            return {'Other Keywords': sorted(keywords, key=natural_sort_key)}

    groups = {}

    for keyword in keywords:
        group_name = 'Other Keywords'

        # Search through tasks section
        if 'tasks' in config:
            for task_name, task_config in config['tasks'].items():
                if not task_config or 'keywords' not in task_config:
                    continue

                for keyword_config in task_config['keywords']:
                    # Try exact match first
                    if keyword_config.get('name') == keyword and 'group' in keyword_config:
                        group_name = keyword_config['group']
                        break

                    # Try prefix match for derived keywords (e.g., s_tns_all from s_tns)
                    kw_name = keyword_config.get('name', '')
                    if ('{' not in kw_name and 'group' in keyword_config and
                        keyword.startswith(kw_name + '_')):
                        group_name = keyword_config['group']
                        break

                    # Try template match for template-based keywords
                    if 'group' in keyword_config and matches_template(keyword, kw_name):
                        group_name = keyword_config['group']
                        break

                if group_name != 'Other Keywords':
                    break

        # If not found in tasks, search through task_templates section
        if group_name == 'Other Keywords' and 'task_templates' in config:
            for template_name, template_config in config['task_templates'].items():
                if not template_config or 'keywords' not in template_config:
                    continue

                for keyword_config in template_config['keywords']:
                    # Try exact match first
                    if keyword_config.get('name') == keyword and 'group' in keyword_config:
                        group_name = keyword_config['group']
                        break

                    # Try prefix match for derived keywords
                    kw_name = keyword_config.get('name', '')
                    if ('{' not in kw_name and 'group' in keyword_config and
                        keyword.startswith(kw_name + '_')):
                        group_name = keyword_config['group']
                        break

                    # Try template match for template-based keywords
                    if 'group' in keyword_config and matches_template(keyword, kw_name):
                        group_name = keyword_config['group']
                        break

                if group_name != 'Other Keywords':
                    break

        # Add keyword to its group
        if group_name not in groups:
            groups[group_name] = []
        groups[group_name].append(keyword)

    # Sort keywords within each group using natural sort with prefix priority
    for group in groups:
        groups[group].sort(key=natural_sort_key)

    # Sort groups according to YAML order
    sorted_groups = {}
    group_order = get_group_order_from_yaml(config)

    # Add groups in YAML-defined order
    for group_name in group_order:
        if group_name in groups:
            sorted_groups[group_name] = groups[group_name]

    # Add any additional groups found in data but not in YAML
    for group_name in sorted(groups.keys()):
        if group_name not in group_order and group_name != 'Other Keywords':
            sorted_groups[group_name] = groups[group_name]

    # Add "Other Keywords" last
    if 'Other Keywords' in groups:
        sorted_groups['Other Keywords'] = groups['Other Keywords']

    return sorted_groups


def extract_all_groups_from_yaml(config: Optional[Dict] = None) -> List[str]:
    """Extract all unique group names from YAML configuration

    Args:
        config: Parsed YAML configuration. If None, attempts to load it.

    Returns:
        List of all unique group names in YAML-defined order
    """
    if config is None:
        config = load_yaml_config()
        if config is None:
            return []

    return get_group_order_from_yaml(config)


# Example usage and testing
if __name__ == "__main__":
    # Test template matching
    print("Testing template matching:")
    print(matches_template("misn_ff_0p99v_m40c_Cbest_s_wns_all", "{mode}_{corner}_s_wns_{path_type}"))  # True
    print(matches_template("misn_ff_0p99v_m40c_Cbest_s_wns_all", "s_wns"))  # False
    print(matches_template("hotspot_Max", "hotspot"))  # False

    # Test YAML loading
    print("\nTesting YAML loading:")
    config = load_yaml_config()
    if config:
        print(f"Loaded config with {len(config.get('tasks', {}))} tasks")

        # Test grouping
        test_keywords = [
            'error', 'warning', 's_wns_all', 's_tns_reg2reg',
            'hotspot_Max', 'overflow_H', 'utilization'
        ]
        groups = group_keywords_by_yaml(test_keywords, config)
        print("\nGrouped keywords:")
        for group_name, kw_list in groups.items():
            print(f"  {group_name}: {kw_list}")

