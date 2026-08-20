from flask import Blueprint, jsonify, render_template, request

from services import model_service

predict_bp = Blueprint('predict', __name__)


@predict_bp.route('/predict')
def predict_page():
    return render_template('predict.html')


@predict_bp.route('/api/predict/options')
def predict_options():
    return jsonify(model_service.get_options())


@predict_bp.route('/api/predict', methods=['POST'])
def predict_salary():
    payload = request.get_json(silent=True) or {}
    try:
        result = model_service.predict(payload)
    except model_service.PredictionInputError as e:
        return jsonify({'error': str(e)}), 400
    except model_service.ModelUnavailableError as e:
        return jsonify({'error': str(e)}), 503
    except Exception as e:
        return jsonify({'error': f'Prediction error: {str(e)}'}), 500
    return jsonify(result)