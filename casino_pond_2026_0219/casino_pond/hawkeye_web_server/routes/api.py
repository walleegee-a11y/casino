"""API routes for Hawkeye Web Server"""

import os
import tempfile
import yaml
from datetime import datetime
from flask import Blueprint, jsonify, request, session, send_file
from hawkeye_web_server.core.archive_manager import init_archive, get_archive


api_bp = Blueprint('api', __name__)


def aggregate_tasks_to_job(tasks):
    """
    Aggregate multiple task results into a single job-level aggregate

    Args:
        tasks (dict): Dictionary of task_name -> task_data

    Returns:
        dict: Aggregated data dictionary with keywords
    """
    if not tasks:
        return {'keywords': {}}

    # Aggregate keywords
    aggregate_keywords = {}
    for task_name, task_data in tasks.items():
        for kw_name, kw_data in task_data.get('keywords', {}).items():
            if kw_name not in aggregate_keywords:
                # First occurrence - initialize
                aggregate_keywords[kw_name] = {
                    'values': [],
                    'unit': kw_data.get('unit', ''),
                    'type': kw_data.get('type', '')
                }

            # Collect value
            value = kw_data.get('value')
            if value is not None:
                aggregate_keywords[kw_name]['values'].append(value)

    # Compute aggregate values for each keyword
    final_keywords = {}
    for kw_name, kw_info in aggregate_keywords.items():
        values = kw_info['values']
        if not values:
            continue

        # Determine aggregation strategy based on keyword type
        if all(isinstance(v, (int, float)) for v in values):
            # Numeric values - choose aggregation strategy
            if 'error' in kw_name.lower() or 'warning' in kw_name.lower() or '_num' in kw_name.lower() or 'count' in kw_name.lower():
                # Sum for counts and violations
                aggregate_value = sum(values)
            elif 'wns' in kw_name.lower():
                # WNS (Worst Negative Slack): take MIN (most negative = worst)
                aggregate_value = min(values)
            elif 'tns' in kw_name.lower():
                # TNS (Total Negative Slack): SUM all slack violations
                aggregate_value = sum(values)
            elif 'nov' in kw_name.lower():
                # NOV (Number of Violations): SUM
                aggregate_value = sum(values)
            elif 'cpu_time' in kw_name.lower() or 'real_time' in kw_name.lower() or 'runtime' in kw_name.lower():
                # Runtime: SUM
                aggregate_value = sum(values)
            elif 'area' in kw_name.lower() or 'utilization' in kw_name.lower() or 'density' in kw_name.lower():
                # Area/utilization: use LAST value (final stage)
                aggregate_value = values[-1]
            elif 'overflow' in kw_name.lower() or 'hotspot' in kw_name.lower():
                # Congestion: take MAX (worst)
                aggregate_value = max(values)
            else:
                # Default: AVERAGE for other metrics
                aggregate_value = sum(values) / len(values)

            final_keywords[kw_name] = {
                'value': aggregate_value,
                'unit': kw_info['unit'],
                'type': kw_info['type']
            }
        elif all(isinstance(v, str) for v in values):
            # String values - concatenate or pick representative
            if len(set(values)) == 1:
                # All same - use that value
                final_keywords[kw_name] = {
                    'value': values[0],
                    'unit': kw_info['unit'],
                    'type': kw_info['type']
                }
            else:
                # Different values - show "MIXED"
                final_keywords[kw_name] = {
                    'value': "MIXED",
                    'unit': kw_info['unit'],
                    'type': kw_info['type']
                }

    return {
        'keywords': final_keywords,
        'task_count': len(tasks)
    }


@api_bp.route('/select-project', methods=['POST'])
def select_project():
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


@api_bp.route('/current-project')
def get_current_project():
    """Get currently selected project"""
    return jsonify({
        'project': session.get('current_project'),
        'archive_path': session.get('archive_path')
    })


@api_bp.route('/vista_config')
def get_vista_config():
    """Get vista_casino.yaml configuration"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'vista_casino.yaml')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return jsonify(config)
        else:
            return jsonify({'error': 'vista_casino.yaml not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/jobs')
def get_jobs():
    """Get jobs configuration from vista_casino.yaml"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'vista_casino.yaml')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            jobs = config.get('jobs', {})
            return jsonify(jobs)
        else:
            return jsonify({'error': 'vista_casino.yaml not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/statistics')
def get_statistics():
    """Get archive statistics"""
    try:
        archive = get_archive()
        if archive is None:
            return jsonify({'error': 'No archive initialized'}), 400

        stats = archive.get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/runs')
def get_runs():
    """Get list of archived runs with optional filtering"""
    try:
        archive = get_archive()
        if archive is None:
            return jsonify({'error': 'No archive initialized'}), 400

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


@api_bp.route('/runs/<int:run_id>')
def get_run_details(run_id):
    """Get detailed data for a specific run"""
    try:
        archive = get_archive()
        if archive is None:
            return jsonify({'error': 'No archive initialized'}), 400

        run_data = archive.get_run_data(run_id)
        if run_data is None:
            return jsonify({'error': 'Run not found'}), 404
        return jsonify(run_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/keywords')
def get_keywords():
    """Get all keywords across all runs with their values"""
    try:
        archive = get_archive()
        if archive is None:
            return jsonify({'error': 'No archive initialized'}), 400

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


@api_bp.route('/keywords/summary')
def get_keywords_summary():
    """Get summary of all unique keywords and their statistics"""
    try:
        archive = get_archive()
        if archive is None:
            return jsonify({'error': 'No archive initialized'}), 400

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


@api_bp.route('/export/csv')
def export_csv():
    """Export archived data to CSV"""
    try:
        archive = get_archive()
        if archive is None:
            return jsonify({'error': 'No archive initialized'}), 400

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


@api_bp.route('/archive', methods=['POST'])
def trigger_archive():
    """Trigger archiving of new data (for integration)"""
    try:
        # This would integrate with hawkeye_casino.py
        # For now, return a placeholder response
        return jsonify({
            'message': 'Archive trigger received',
            'status': 'Use the Archive button in Hawkeye GUI to archive data'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/repair-archive', methods=['POST'])
def repair_archive():
    """Force archive repair to detect and import orphaned data files"""
    try:
        archive = get_archive()
        if archive is None:
            return jsonify({'error': 'No archive initialized'}), 400

        # Force re-run auto-repair
        archive._auto_repair_metadata()

        # Get updated statistics
        stats = archive.get_statistics()

        return jsonify({
            'success': True,
            'message': 'Archive repair completed',
            'statistics': stats
        })
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

