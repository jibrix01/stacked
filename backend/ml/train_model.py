"""
Trains the salary-prediction model exactly as in Section 4 of the case-study
notebook ("Building a Pay Model"), and saves the artifacts the Flask app needs:

  artifacts/model.joblib     - the fitted sklearn Pipeline (Random Forest)
  artifacts/metadata.json    - dropdown options, CV metrics, feature importance

Run this once (or whenever survey_results_public.csv changes):
    python -m ml.train_model /path/to/survey_results_public.csv
"""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, r2_score
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml.data_prep import MODEL_LANGUAGES, add_language_flags, load_and_preprocess_data

ARTIFACTS_DIR = Path(__file__).parent / 'artifacts'
CAT_COLS = ['Country_Grouped', 'EdLevel', 'RemoteWork']
TOP_N_COUNTRIES = 25


def build_pipeline(regressor):
    lang_cols = [f'lang_{l}' for l in MODEL_LANGUAGES]
    preprocessor = ColumnTransformer(transformers=[
        ('num', StandardScaler(), ['YearsCodePro_num']),
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CAT_COLS),
        ('lang', 'passthrough', lang_cols),
    ])
    return Pipeline(steps=[('preprocessor', preprocessor), ('regressor', regressor)])


def evaluate_cv(model, X, y, kf):
    oof_log_pred = cross_val_predict(model, X, y, cv=kf, n_jobs=-1)
    dollar_true = 10 ** y
    dollar_pred = 10 ** oof_log_pred
    return {
        'r2': round(float(r2_score(y, oof_log_pred)), 4),
        'mae_usd': round(float(mean_absolute_error(dollar_true, dollar_pred)), 2),
        'mape': round(float(mean_absolute_percentage_error(dollar_true, dollar_pred)), 4),
    }


def main(csv_path: str):
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    print(f'Loading + cleaning {csv_path} ...')
    df_clean = load_and_preprocess_data(csv_path)

    df_ml = df_clean.dropna(
        subset=['Country', 'EdLevel', 'RemoteWork', 'YearsCodePro_num', 'LanguageHaveWorkedWith']
    ).copy()

    top_countries_list = df_ml['Country'].value_counts().head(TOP_N_COUNTRIES).index.tolist()
    df_ml['Country_Grouped'] = df_ml['Country'].apply(lambda x: x if x in top_countries_list else 'Other')
    df_ml = add_language_flags(df_ml)
    lang_cols = [f'lang_{l}' for l in MODEL_LANGUAGES]

    X = df_ml[['YearsCodePro_num'] + CAT_COLS + lang_cols]
    y = df_ml['LogComp']

    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    ridge_model = build_pipeline(Ridge(alpha=1.0))
    rf_model = build_pipeline(RandomForestRegressor(n_estimators=300, max_depth=8, random_state=42, n_jobs=-1))

    print('Cross-validating Ridge ...')
    ridge_metrics = evaluate_cv(ridge_model, X, y, kf)
    print('Ridge:', ridge_metrics)

    print('Cross-validating Random Forest ...')
    rf_metrics = evaluate_cv(rf_model, X, y, kf)
    print('Random Forest:', rf_metrics)

    print('Computing out-of-fold error by country (mirrors notebook cell 27) ...')
    oof_log_pred = cross_val_predict(ridge_model, X, y, cv=kf, n_jobs=-1)
    df_ml = df_ml.copy()
    df_ml['_pred_dollar'] = 10 ** oof_log_pred
    mape_by_country = {}
    for c in ['United States of America', 'Germany', 'India']:
        sub = df_ml[df_ml['Country'] == c]
        if len(sub):
            mape_by_country[c] = round(
                float(mean_absolute_percentage_error(10 ** sub['LogComp'], sub['_pred_dollar'])), 4
            )

    print('Fitting final Random Forest on full data ...')
    rf_model.fit(X, y)

    # Feature importance, aggregated per original column (mirrors notebook cell 25)
    cat_feature_names = list(
        rf_model.named_steps['preprocessor'].named_transformers_['cat'].get_feature_names_out(CAT_COLS)
    )
    importances = rf_model.named_steps['regressor'].feature_importances_
    agg_importance = {'YearsCodePro_num': float(importances[0])}
    idx = 1
    for col in CAT_COLS:
        n_cats = len(
            rf_model.named_steps['preprocessor'].named_transformers_['cat']
            .categories_[CAT_COLS.index(col)]
        )
        agg_importance[col] = float(importances[idx:idx + n_cats].sum())
        idx += n_cats
    for lang_col in lang_cols:
        agg_importance[lang_col] = float(importances[idx])
        idx += 1

    joblib.dump(rf_model, ARTIFACTS_DIR / 'model.joblib')

    metadata = {
        'model_type': 'RandomForestRegressor',
        'target': 'log10(ConvertedCompYearly)',
        'training_rows': int(len(df_ml)),
        'metrics': {
            'ridge': ridge_metrics,
            'random_forest': rf_metrics,
        },
        'feature_importance': agg_importance,
        'mape_by_country': mape_by_country,
        'options': {
            'countries': sorted(top_countries_list) + ['Other'],
            'ed_levels': sorted(df_ml['EdLevel'].dropna().unique().tolist()),
            'remote_work': sorted(df_ml['RemoteWork'].dropna().unique().tolist()),
            'languages': MODEL_LANGUAGES,
        },
        'defaults': {
            'YearsCodePro_num': float(df_ml['YearsCodePro_num'].median()),
            'Country_Grouped': df_ml['Country_Grouped'].mode().iloc[0],
            'EdLevel': df_ml['EdLevel'].mode().iloc[0],
            'RemoteWork': df_ml['RemoteWork'].mode().iloc[0],
        },
    }
    with open(ARTIFACTS_DIR / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f'Saved model.joblib and metadata.json to {ARTIFACTS_DIR}')


if __name__ == '__main__':
    csv = sys.argv[1] if len(sys.argv) > 1 else 'survey_results_public.csv'
    main(csv)
