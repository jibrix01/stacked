from flask import Blueprint, render_template

insights_bp = Blueprint('insights', __name__)


@insights_bp.route('/insights')
def insights_page():
    return render_template('insights.html')
