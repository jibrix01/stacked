from pathlib import Path

BASE_DIR = Path(__file__).parent
ARTIFACTS_DIR = BASE_DIR / 'ml' / 'artifacts'
DASHBOARD_DATA_DIR = BASE_DIR / 'data' / 'dashboard'

MODEL_PATH = ARTIFACTS_DIR / 'model.joblib'
METADATA_PATH = ARTIFACTS_DIR / 'metadata.json'
