"""
Serves precomputed dashboard chart data. Nothing here touches the raw CSV
or pandas at request time -- everything is precomputed by
ml/precompute_dashboard.py and just read + cached in memory here.
"""
import json

from config import DASHBOARD_DATA_DIR

VALID_SECTIONS = {'overview', 'pay_by_country', 'languages', 'satisfaction', 'model_insights'}

_cache = {}


class UnknownSectionError(ValueError):
    pass


def get_section(name: str) -> dict:
    if name not in VALID_SECTIONS:
        raise UnknownSectionError(f'unknown dashboard section: {name}')
    if name not in _cache:
        path = DASHBOARD_DATA_DIR / f'{name}.json'
        with open(path) as f:
            _cache[name] = json.load(f)
    return _cache[name]


def list_sections() -> list:
    return sorted(VALID_SECTIONS)
