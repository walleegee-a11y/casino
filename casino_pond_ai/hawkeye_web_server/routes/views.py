"""View routes for Hawkeye Web Server"""

import os
from flask import Blueprint, render_template, session, redirect, url_for
from hawkeye_web_server.core.archive_manager import discover_projects, get_archive


views_bp = Blueprint('views', __name__)


@views_bp.route('/select-project')
def select_project():
    """Show project selection page"""
    projects = discover_projects()
    casino_prj_base = os.getenv('casino_prj_base', 'Not set')
    current_project = session.get('current_project')

    return render_template(
        'project_selector.html',
        projects=projects,
        casino_prj_base=casino_prj_base,
        current_project=current_project
    )


@views_bp.route('/')
def index():
    """Main dashboard - requires project selection"""
    archive = get_archive()
    if 'current_project' not in session or archive is None:
        return redirect(url_for('views.select_project'))

    return render_template('dashboard.html')


@views_bp.route('/comparison-view')
def comparison_view():
    """Serve the comparison view in a new window/tab"""
    return render_template('comparison.html')
