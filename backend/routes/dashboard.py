from flask import Blueprint, jsonify, render_template

from services import dashboard_service

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html', sections=dashboard_service.list_sections())


@dashboard_bp.route('/api/dashboard/<section>')
def dashboard_section(section):
    try:
        data = dashboard_service.get_section(section)
    except dashboard_service.UnknownSectionError as e:
        return jsonify({'error': str(e)}), 404
    return jsonify(data)
