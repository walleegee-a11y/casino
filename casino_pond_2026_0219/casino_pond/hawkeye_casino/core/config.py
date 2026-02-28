"""Configuration loading and management"""

import os
import yaml
import copy
from typing import Dict, Any


def substitute_template_vars(obj, variables):
    """Recursively substitute {var} placeholders in strings

    This function replaces template placeholders like {mode}, {corner}, {path_type}
    with actual values throughout nested data structures.

    Args:
        obj: Object to process (str, dict, list, or other)
        variables: Dict of {placeholder_name: value} mappings
                  Example: {'mode': 'misn', 'corner': 'ss_0p72v_m40c_Cmax'}

    Returns:
        Object with all {placeholder} strings replaced

    Example:
        >>> substitute_template_vars(
        ...     "{mode}_{corner}_s_wns",
        ...     {'mode': 'misn', 'corner': 'ss_0p72v_m40c_Cmax'}
        ... )
        'misn_ss_0p72v_m40c_Cmax_s_wns'
    """
    if isinstance(obj, str):
        # Replace all {key} placeholders in string
        for key, value in variables.items():
            obj = obj.replace(f"{{{key}}}", value)
        return obj
    elif isinstance(obj, dict):
        # Recursively process dictionary values
        return {k: substitute_template_vars(v, variables) for k, v in obj.items()}
    elif isinstance(obj, list):
        # Recursively process list items
        return [substitute_template_vars(item, variables) for item in obj]
    else:
        # Return other types unchanged
        return obj


def expand_task_template(template, task_name, overrides=None):
    """STAGE 1 EXPANSION: Substitute {task_name} in template

    This is the first stage of the two-stage expansion process.
    It replaces {task_name} placeholders in file paths and other fields.

    After this stage:
    - {task_name} is resolved (e.g., "place", "cts", "postcts")
    - {mode}, {corner}, {path_type} remain as placeholders (expanded in stage 2)

    Example:
        Input:  file_name: "report/{task_name}/{task_name}.summary.gz"
        Output: file_name: "report/place/place.summary.gz"

    Args:
        template: Task template dict from vista_casino.yaml
        task_name: Task name to substitute (e.g., "place", "cts")
        overrides: Optional dict to override log_files, report_files, keywords

    Returns:
        Expanded template with {task_name} resolved
    """
    expanded = copy.deepcopy(template)
    variables = {'task_name': task_name}
    expanded = substitute_template_vars(expanded, variables)

    # Apply overrides for special cases (e.g., init_inn has different paths)
    if overrides:
        if 'log_files' in overrides:
            expanded['log_files'] = overrides['log_files']
        if 'report_files' in overrides:
            expanded['report_files'] = overrides['report_files']
        if 'keywords' in overrides:
            override_keywords = {kw['name']: kw for kw in overrides['keywords']}
            for i, keyword in enumerate(expanded['keywords']):
                if keyword['name'] in override_keywords:
                    expanded['keywords'][i].update(override_keywords[keyword['name']])

    return expanded


def expand_yaml_templates(config):
    """Expand template-based task definitions"""
    templates = config.get('task_templates', {})
    mappings = config.get('task_mappings', {})

    if not mappings:
        # No templates to expand
        return config

    tasks = config.get('tasks', {})

    for task_key, mapping in mappings.items():
        template_name = mapping['template']
        task_name = mapping.get('task_name', task_key.replace('_inn', ''))
        overrides = mapping.get('overrides')

        if template_name in templates:
            template = templates[template_name]
            tasks[task_key] = expand_task_template(template, task_name, overrides)
            print(f"DEBUG: Expanded {task_key} from template {template_name}")

    config['tasks'] = tasks
    return config


def expand_sta_keywords(config, job_name=None):
    """Expand STA keyword templates for all mode/corner combinations

    Handles three types of keyword templates:
    1. Timing keywords: Expand with {mode}, {corner}, {path_type}, {path_type_pattern}
    2. Violation keywords: Expand with {mode}, {corner} only
    3. Noise keywords: Expand with {mode}, {corner}, {noise_type}

    Args:
        config: Configuration dictionary with sta_config and tasks
        job_name: Optional job name to check if STA keywords are needed for this job
                 If provided, only expands if job includes sta_pt task
                 If None, always expands (backward compatible)

    Returns:
        Configuration dictionary with expanded STA keywords
    """
    # NEW LOGIC: If job_name is provided, check if sta_pt is in the job's task list
    if job_name is not None:
        job_tasks = get_job_tasks_from_config(config, job_name)
        if 'sta_pt' not in job_tasks:
            print(f"DEBUG: Job '{job_name}' does not include sta_pt task, skipping STA keyword expansion")
            print(f"DEBUG: This avoids generating 228 unnecessary STA keywords for APR-only jobs")
            return config
        print(f"DEBUG: Job '{job_name}' includes sta_pt task, proceeding with STA keyword expansion")

    if 'sta_config' not in config:
        print("DEBUG: No sta_config found, skipping STA keyword expansion")
        return config

    if 'tasks' not in config or 'sta_pt' not in config['tasks']:
        print("DEBUG: No sta_pt task found, skipping STA keyword expansion")
        return config

    sta_config = config['sta_config']
    modes = sta_config.get('modes', [])
    corners = sta_config.get('corners', [])

    if not modes or not corners:
        print("DEBUG: No modes or corners defined in sta_config")
        return config

    sta_task = config['tasks']['sta_pt']
    keyword_templates = sta_task.get('keywords', [])

    if not keyword_templates:
        print("DEBUG: No keyword templates defined in sta_pt task")
        return config

    # Path type mappings: short name / pattern for report
    path_types = [
        ('total', 'Total'),
        ('reg2reg', 'reg->reg'),
        ('in2reg', 'in->reg'),
        ('reg2out', 'reg->out'),
        ('in2out', 'in->out')
    ]

    # Noise type mappings
    noise_types = [
        ('above_low', 'above_low'),
        ('below_high', 'below_high')
    ]

    expanded_keywords = []
    timing_count = 0
    violation_count = 0
    noise_count = 0

    # REORDERED LOOPS: Iterate mode/corner FIRST, then apply templates
    # This groups keywords by mode/corner instead of by metric type
    for mode in modes:
        for corner in corners:
            # For each mode/corner combination, expand all template types
            for template in keyword_templates:
                template_name = template.get('name', '')

                # Determine keyword type by checking for placeholders
                has_path_type = '{path_type}' in template_name
                has_noise_type = '{noise_type}' in template_name

                if has_path_type:
                    # TIMING KEYWORDS: Expand with mode/corner/path_type
                    for path_type_short, path_type_pattern in path_types:
                        expanded = copy.deepcopy(template)
                        variables = {
                            'mode': mode,
                            'corner': corner,
                            'path_type': path_type_short,
                            'path_type_pattern': path_type_pattern
                        }
                        expanded = substitute_template_vars(expanded, variables)
                        expanded['mode'] = mode
                        expanded['corner'] = corner
                        expanded['path_type'] = path_type_pattern
                        expanded_keywords.append(expanded)
                        timing_count += 1

                elif has_noise_type:
                    # NOISE KEYWORDS: Expand with mode/corner/noise_type
                    for noise_type_short, noise_type_pattern in noise_types:
                        expanded = copy.deepcopy(template)
                        variables = {
                            'mode': mode,
                            'corner': corner,
                            'noise_type': noise_type_short
                        }
                        expanded = substitute_template_vars(expanded, variables)
                        expanded['mode'] = mode
                        expanded['corner'] = corner
                        expanded['noise_type'] = noise_type_short
                        expanded_keywords.append(expanded)
                        noise_count += 1

                else:
                    # VIOLATION KEYWORDS: Expand with mode/corner only
                    expanded = copy.deepcopy(template)
                    variables = {
                        'mode': mode,
                        'corner': corner
                    }
                    expanded = substitute_template_vars(expanded, variables)
                    expanded['mode'] = mode
                    expanded['corner'] = corner
                    expanded_keywords.append(expanded)
                    violation_count += 1

    # Replace template keywords with expanded keywords
    sta_task['keywords'] = expanded_keywords

    print(f"DEBUG: Expanded {len(expanded_keywords)} STA keywords from {len(keyword_templates)} templates:")
    print(f"DEBUG:   - {timing_count} timing keywords (mode/corner/path_type)")
    print(f"DEBUG:   - {violation_count} violation keywords (mode/corner)")
    print(f"DEBUG:   - {noise_count} noise keywords (mode/corner/noise_type)")

    return config


def parse_apr_path_types_from_file(report_file_path):
    """Dynamically parse path types from an APR timing report file

    Args:
        report_file_path: Path to an Innovus .summary.gz report file

    Returns:
        List of tuples (name, pattern) for path types, or None if parsing fails
    """
    import gzip
    import re

    try:
        print(f"DEBUG: Attempting to parse path types from: {report_file_path}")

        # Read file (handle both .gz and regular files)
        if report_file_path.endswith('.gz'):
            with gzip.open(report_file_path, 'rt', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        else:
            with open(report_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

        # Find header line with path types
        # Format: |     Setup mode     |   all   | reg2reg |reg2cgate| in2reg  | reg2out | in2out  | default |
        # FIX: Use greedy match to capture ALL columns (was .+? which only got first column)
        header_pattern = r'\|\s+(Setup mode|Hold mode)\s+\|(.+)\|?\s*$'
        header_match = re.search(header_pattern, content, re.MULTILINE)

        if not header_match:
            print("DEBUG: Could not find timing mode header in report file")
            return None

        # Extract column names
        columns_str = header_match.group(2)
        columns = [col.strip() for col in columns_str.split('|') if col.strip()]

        print(f"DEBUG: Parsed {len(columns)} path types from report: {columns}")

        # Create path_types list as (name, pattern) tuples
        # IMPORTANT: Preserve original case - "Reg2Reg" and "reg2reg" are DIFFERENT path types!
        # Only normalize spaces and special chars, keep case sensitivity
        path_types = []
        seen_names = set()

        for col in columns:
            # Preserve case! Only replace spaces/special chars with underscores
            name = col.replace(' ', '_').replace('-', '_')
            pattern = col  # Keep original for exact matching

            # Check for exact duplicates (same name after char replacement)
            if name in seen_names:
                print(f"DEBUG:   ! Warning: Duplicate path_type name '{name}' detected")
                print(f"DEBUG:     This should not happen - check report file format")
            else:
                seen_names.add(name)

            path_types.append((name, pattern))
            print(f"DEBUG:   Path type: name='{name}', pattern='{pattern}'")

        return path_types

    except Exception as e:
        print(f"DEBUG: Error parsing path types from file: {e}")
        import traceback
        traceback.print_exc()
        return None


def expand_apr_keywords(config, job_name=None):
    """STAGE 2 EXPANSION: Expand APR keyword templates with mode/corner/path_type

    This is the second stage of APR keyword expansion (after expand_task_template).
    It performs a triple-nested loop expansion to generate all combinations:

        FOR each mode (3):
            FOR each corner (8):
                FOR each path_type (7):
                    Generate keyword: {mode}_{corner}_{timing}_{metric}_{path_type}

    Expansion Results:
    - Timing keywords: 3 x 8 x 7 x 6 = 1,008 keywords per task
    - Non-timing keywords: 8 keywords per task (error, warning, etc.)
    - Total per task: 1,016 keywords
    - For 6 APR tasks: 6,096 total keywords

    Example:
        Template: {mode}_{corner}_s_wns_{path_type}
        Expanded: misn_ss_0p72v_m40c_Cmax_s_wns_all

        With metadata:
            section_marker: misn_ss_0p72v_m40c_Cmax
            path_type_column: all
            file_name: report/place/place.summary.gz

    Args:
        config: Configuration dictionary with apr_config and tasks
        job_name: Optional job name to check if APR keywords are needed for this job

    Returns:
        Configuration dictionary with expanded APR keywords
    """
    # Check if job includes APR tasks
    if job_name is not None:
        job_tasks = get_job_tasks_from_config(config, job_name)
        apr_tasks = ['place_inn', 'cts_inn', 'postcts_inn', 'route_inn', 'postroute_inn', 'chipfinish_inn']
        if not any(task in job_tasks for task in apr_tasks):
            print(f"DEBUG: Job '{job_name}' does not include APR tasks, skipping APR keyword expansion")
            return config
        print(f"DEBUG: Job '{job_name}' includes APR tasks, proceeding with APR keyword expansion")

    if 'apr_config' not in config:
        print("DEBUG: No apr_config found, skipping APR keyword expansion")
        return config

    apr_config = config['apr_config']
    modes = apr_config.get('modes', [])
    corners = apr_config.get('corners', [])
    path_types_config = apr_config.get('path_types', [])
    use_dynamic_path_types = apr_config.get('use_dynamic_path_types', False)

    if not modes or not corners:
        print("DEBUG: No modes or corners defined in apr_config")
        return config

    # Try dynamic path type discovery if enabled
    path_types = None
    if use_dynamic_path_types:
        print("DEBUG: Dynamic path type discovery enabled, attempting to parse from report file...")
        # Try to find a sample report file to parse path types from
        # Look for any place/cts/route summary file in casino_prj_base
        casino_prj_base = os.getenv('casino_prj_base', '.')
        sample_report_patterns = [
            f"{casino_prj_base}/**/apr_inn/place_inn/report/place/place.summary.gz",
            f"{casino_prj_base}/**/apr_inn/cts_inn/report/cts/cts.summary.gz",
            f"{casino_prj_base}/**/apr_inn/route_inn/report/route/route.summary.gz",
        ]

        import glob
        for pattern in sample_report_patterns:
            matches = glob.glob(pattern, recursive=True)
            if matches:
                sample_file = matches[0]
                print(f"DEBUG: Found sample report file: {sample_file}")
                path_types = parse_apr_path_types_from_file(sample_file)
                if path_types:
                    print(f"DEBUG: Successfully parsed {len(path_types)} path types dynamically")
                    break

        if not path_types:
            print("DEBUG: Could not parse path types dynamically, falling back to config")

    # Fallback to config-based path types
    if not path_types:
        if not path_types_config:
            print("DEBUG: No path_types defined in apr_config")
            return config
        # Extract path type names and patterns
        path_types = [(pt['name'], pt['pattern']) for pt in path_types_config]
        print(f"DEBUG: Using {len(path_types)} path types from config")

    # APR tasks to expand
    apr_tasks = {
        'place_inn': 'place',
        'cts_inn': 'cts',
        'postcts_inn': 'postcts',
        'route_inn': 'route',
        'postroute_inn': 'postroute',
        'chipfinish_inn': 'chipfinish'
    }

    total_expanded = 0

    for task_key, task_name in apr_tasks.items():
        if task_key not in config.get('tasks', {}):
            continue

        task = config['tasks'][task_key]
        keyword_templates = task.get('keywords', [])

        if not keyword_templates:
            continue

        expanded_keywords = []

        for template in keyword_templates:
            template_name = template.get('name', '')

            # Check if this template needs expansion (has placeholders)
            has_mode = '{mode}' in template_name
            has_corner = '{corner}' in template_name
            has_path_type = '{path_type}' in template_name

            if has_mode and has_corner and has_path_type:
                # TIMING KEYWORDS: Double-nested loop expansion (mode x corner only)
                # Path types are extracted dynamically at runtime from file headers
                # NEW: 3 modes x 8 corners = 24 keywords per template (was 168)
                # Each keyword will extract ALL path_types from the file in one pass
                for mode in modes:
                    for corner in corners:
                        expanded = copy.deepcopy(template)

                        # Remove {path_type} from name - will be added dynamically
                        template_name_base = template.get('name', '').replace('_{path_type}', '')

                        # Substitute mode and corner only
                        variables = {
                            'task_name': task_name,      # Already substituted in Stage 1
                            'mode': mode,                 # e.g., 'misn', 'scap', 'ssft'
                            'corner': corner,             # e.g., 'ss_0p72v_m40c_Cmax'
                        }
                        # Update name without path_type
                        expanded['name'] = template_name_base
                        expanded = substitute_template_vars(expanded, variables)

                        # Store metadata for parser (used in _extract_apr_timing_section)
                        expanded['mode'] = mode
                        expanded['corner'] = corner
                        expanded['extract_all_path_types'] = True  # NEW: Runtime path_type extraction flag

                        expanded_keywords.append(expanded)
                        total_expanded += 1
            else:
                # NON-TIMING KEYWORDS: No expansion (error, warning, hotspot, etc.)
                # These are already task-specific from Stage 1
                # No mode/corner/path_type variants needed
                expanded = copy.deepcopy(template)
                variables = {'task_name': task_name}
                expanded = substitute_template_vars(expanded, variables)
                expanded_keywords.append(expanded)

        # Replace template keywords with expanded keywords
        task['keywords'] = expanded_keywords
        print(f"DEBUG: Expanded {len(expanded_keywords)} keywords for {task_key}")

    print(f"DEBUG: Total APR timing keywords expanded: {total_expanded}")

    return config


def load_config(config_file: str = None, job_name: str = None) -> Dict[str, Any]:
    """Load the vista_casino.yaml configuration file with template expansion

    Args:
        config_file: Path to config file, or None to use default
        job_name: Optional job name for selective keyword expansion

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid
    """
    if config_file is None:
        config_file = os.path.join(os.getenv('casino_pond', ''), 'vista_casino.yaml')

    try:
        print(f"DEBUG: Loading configuration from: {config_file}")
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)

        print(f"DEBUG: Successfully loaded configuration")

        # Expand templates if present
        config = expand_yaml_templates(config)

        # Expand STA keywords from templates (job-aware)
        config = expand_sta_keywords(config, job_name=job_name)

        # Expand APR keywords from templates (job-aware)
        config = expand_apr_keywords(config, job_name=job_name)

        return config

    except FileNotFoundError:
        print(f"Error: Configuration file {config_file} not found")
        raise
    except yaml.YAMLError as e:
        print(f"Error parsing YAML configuration: {e}")
        raise

def get_job_tasks_from_config(config: Dict[str, Any], job_name: str) -> list:
    """Get expected tasks for a job from configuration

    Args:
        config: Configuration dictionary
        job_name: Name of the job

    Returns:
        List of task names for this job
    """
    if 'jobs' in config:
        job_config = config['jobs'].get(job_name, {})
        return job_config.get('tasks', [])
    return []


def get_all_configured_jobs_and_tasks(config: Dict[str, Any]) -> Dict[str, list]:
    """Get all jobs and tasks defined in configuration

    Args:
        config: Configuration dictionary

    Returns:
        Dictionary mapping job names to lists of task names
    """
    configured_jobs = {}

    if 'jobs' in config:
        for job_name, job_config in config['jobs'].items():
            if 'tasks' in job_config:
                configured_jobs[job_name] = job_config['tasks']

    return configured_jobs

