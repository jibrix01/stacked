import json

import joblib
import pandas as pd

from config import METADATA_PATH, MODEL_PATH

_model = None
_metadata = None


class PredictionInputError(ValueError):
    """Raised when the request payload doesn't match what the model expects."""


class ModelUnavailableError(RuntimeError):
    """Raised when model.joblib can't be loaded (e.g. sklearn/numpy version mismatch)."""


def _load_metadata():
    global _metadata
    if _metadata is None:
        with open(METADATA_PATH) as f:
            _metadata = json.load(f)
    return _metadata


def _load_model():
    global _model
    if _model is None:
        try:
            _model = joblib.load(MODEL_PATH)
        except Exception as e:
            raise ModelUnavailableError(
                f'Could not load model.joblib ({e.__class__.__name__}: {e}). '
                'This usually means the installed scikit-learn/numpy version '
                'differs from what the model was trained with -- try '
                '`python -m ml.train_model <csv>` to retrain locally.'
            ) from e
    return _model


def get_options():
    metadata = _load_metadata()
    return {
        'options': metadata['options'],
        'defaults': metadata['defaults'],
    }


def get_model_metrics():
    metadata = _load_metadata()
    return {
        'metrics': metadata['metrics'],
        'training_rows': metadata['training_rows'],
        'model_type': metadata['model_type'],
    }


def _validate(payload: dict, metadata: dict):
    options = metadata['options']
    try:
        years = float(payload.get('years_experience'))
    except (TypeError, ValueError):
        raise PredictionInputError('years_experience must be a number')
    if not (0 <= years <= 50):
        raise PredictionInputError('years_experience must be between 0 and 50')

    country = payload.get('country')
    if country not in options['countries']:
        raise PredictionInputError(f'country must be one of: {options["countries"]}')

    ed_level = payload.get('ed_level')
    if ed_level not in options['ed_levels']:
        raise PredictionInputError(f'ed_level must be one of: {options["ed_levels"]}')

    remote_work = payload.get('remote_work')
    if remote_work not in options['remote_work']:
        raise PredictionInputError(f'remote_work must be one of: {options["remote_work"]}')

    languages = payload.get('languages', [])
    if not isinstance(languages, list):
        raise PredictionInputError('languages must be a list')
    unknown = set(languages) - set(options['languages'])
    if unknown:
        raise PredictionInputError(f'unknown languages: {sorted(unknown)}')

    return years, country, ed_level, remote_work, languages


def predict(payload: dict) -> dict:
    metadata = _load_metadata()
    years, country, ed_level, remote_work, languages = _validate(payload, metadata)
    model = _load_model()

    row = {
        'YearsCodePro_num': years,
        'Country_Grouped': country,
        'EdLevel': ed_level,
        'RemoteWork': remote_work,
    }
    for lang in metadata['options']['languages']:
        row[f'lang_{lang}'] = lang in languages

    X = pd.DataFrame([row])
    log_pred = model.predict(X)[0]
    dollar_pred = float(10 ** log_pred)

    mape = metadata['metrics']['random_forest']['mape']
    return {
        'predicted_salary_usd': round(dollar_pred, -2),
        'range_low_usd': round(dollar_pred * (1 - mape), -2),
        'range_high_usd': round(dollar_pred * (1 + mape), -2),
        'model_mape': mape,
        'model_r2': metadata['metrics']['random_forest']['r2'],
    }