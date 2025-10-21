"""Configuration loading and management"""

import os
import yaml
import copy
from typing import Dict, Any


def substitute_template_vars(obj, variables):
    """Recursively substitute {var} placeholders in strings"""
    if isinstance(obj, str):
        for key, value in variables.items():
            obj = obj.replace(f"{{{key}}}", value)
        return obj
    elif isinstance(obj, dict):
        return {k: substitute_template_vars(v, variables) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [substitute_template_vars(item, variables) for item in obj]
    else:
        return obj


def expand_task_template(template, task_name, overrides=None):
    """Expand a task template with variable substitution"""
    expanded = copy.deepcopy(template)
    variables = {'task_name': task_name}
    expanded = substitute_template_vars(expanded, variables)

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

    for template in keyword_templates:
        template_name = template.get('name', '')

        # Determine keyword type by checking for placeholders
        has_path_type = '{path_type}' in template_name
        has_noise_type = '{noise_type}' in template_name

        if has_path_type:
            # TIMING KEYWORDS: Expand with mode/corner/path_type
            for mode in modes:
                for corner in corners:
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
            for mode in modes:
                for corner in corners:
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
            for mode in modes:
                for corner in corners:
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
