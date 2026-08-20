"""
Precomputes every chart the dashboard needs, as small JSON files, by
reproducing each analysis section of the case-study notebook. Run after
train_model.py (or independently) whenever the source CSV changes:

    python -m ml.precompute_dashboard /path/to/survey_results_public.csv
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

from ml.data_prep import (
    COUNTRY_LABELS, FRICTION_MAP, MODEL_LANGUAGES, TOP5_COUNTRIES,
    add_language_flags, load_and_preprocess_data,
)

OUT_DIR = Path(__file__).parent.parent / 'data' / 'dashboard'
RNG = np.random.default_rng(42)


def save(name, payload):
    with open(OUT_DIR / f'{name}.json', 'w') as f:
        json.dump(payload, f, indent=2, default=_default)
    print(f'  wrote {name}.json')


def _default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(f'not serializable: {type(o)}')


def section_overview(df_clean: pd.DataFrame, initial_count: int, prof_count: int):
    missing = df_clean.isna().sum()
    missing_pct = (missing / len(df_clean) * 100).round(1)

    def hist(series, bins):
        counts, edges = np.histogram(series.dropna(), bins=bins)
        centers = ((edges[:-1] + edges[1:]) / 2).round(2)
        return {'counts': counts.tolist(), 'bin_edges': edges.round(2).tolist(), 'bin_centers': centers.tolist()}

    top10 = df_clean['Country'].value_counts().head(10)

    save('overview', {
        'audit': {
            'total_raw_responses': int(initial_count),
            'professional_developers': int(prof_count),
            'professional_pct': round(prof_count / initial_count * 100, 1),
            'cleaned_rows': int(len(df_clean)),
        },
        'missing_values': {
            col: {'missing': int(missing[col]), 'pct': float(missing_pct[col])}
            for col in df_clean.columns if missing[col] > 0
        },
        'numeric_summary': {
            'comp': df_clean['ConvertedCompYearly'].describe().round(1).to_dict(),
            'experience': df_clean['YearsCodePro_num'].describe().round(1).to_dict(),
        },
        'top10_countries': {k: int(v) for k, v in top10.items()},
        'remote_work_distribution': {k: int(v) for k, v in df_clean['RemoteWork'].value_counts(dropna=False).items()},
        'ed_level_distribution': {k: int(v) for k, v in df_clean['EdLevel'].value_counts(dropna=False).items()},
        'histograms': {
            'comp_raw': hist(df_clean['ConvertedCompYearly'], 60),
            'comp_log10': hist(df_clean['LogComp'], 60),
            'experience_years': hist(df_clean['YearsCodePro_num'], 40),
        },
    })


def section_pay_by_country(df_clean: pd.DataFrame):
    df_top = df_clean[df_clean['Country'].isin(TOP5_COUNTRIES)].copy()

    scatter = {}
    trendlines = {}
    for country in TOP5_COUNTRIES:
        sub = df_top[df_top['Country'] == country]
        sample = sub.sample(min(300, len(sub)), random_state=42) if len(sub) > 300 else sub
        scatter[COUNTRY_LABELS[country]] = [
            {'x': round(float(r.YearsCodePro_num), 1), 'y': round(float(r.ConvertedCompYearly), 0)}
            for r in sample.itertuples()
        ]
        if len(sub) >= 2:
            lr = LinearRegression().fit(sub[['YearsCodePro_num']], sub['ConvertedCompYearly'])
            x_range = [float(sub['YearsCodePro_num'].min()), float(sub['YearsCodePro_num'].max())]
            y_range = lr.predict(np.array(x_range).reshape(-1, 1)).round(0).tolist()
            trendlines[COUNTRY_LABELS[country]] = [
                {'x': x_range[0], 'y': y_range[0]}, {'x': x_range[1], 'y': y_range[1]}
            ]

    median_by_country = df_top.groupby('Country')['ConvertedCompYearly'].median()
    median_by_country.index = median_by_country.index.map(COUNTRY_LABELS)

    us = df_clean[df_clean['Country'] == 'United States of America']
    remote_us = us.groupby('RemoteWork').agg(
        median_comp=('ConvertedCompYearly', 'median'),
        median_exp=('YearsCodePro_num', 'median'),
    ).round(1)

    remote_pooled = df_top.groupby('RemoteWork').agg(
        median_comp=('ConvertedCompYearly', 'median'),
        median_exp=('YearsCodePro_num', 'median'),
    ).round(1)

    save('pay_by_country', {
        'scatter_by_country': scatter,
        'trendline_by_country': trendlines,
        'median_pay_by_country': median_by_country.round(0).to_dict(),
        'remote_work_us': remote_us.reset_index().to_dict(orient='records'),
        'remote_work_pooled_top5': remote_pooled.reset_index().to_dict(orient='records'),
    })


def section_languages(df_clean: pd.DataFrame):
    df_langs = df_clean.dropna(subset=['LanguageHaveWorkedWith']).copy()
    df_langs['Language'] = df_langs['LanguageHaveWorkedWith'].str.split(';')
    df_exploded = df_langs.explode('Language')

    top_langs = df_exploded['Language'].value_counts().head(20).index
    lang_stats = df_exploded[df_exploded['Language'].isin(top_langs)].groupby('Language').agg(
        median_comp=('ConvertedCompYearly', 'median'),
        median_exp=('YearsCodePro_num', 'median'),
        developer_count=('ResponseId', 'count'),
    ).round(1).reset_index().sort_values('median_comp', ascending=False)

    save('languages', {'language_stats': lang_stats.to_dict(orient='records')})


def section_satisfaction(df_clean: pd.DataFrame):
    df_f = df_clean.dropna(subset=['JobSat', 'Knowledge_2', 'Knowledge_4']).copy()
    df_f['JobSat_num'] = df_f['JobSat']
    df_f['Silos_Friction'] = df_f['Knowledge_2'].map(FRICTION_MAP)
    df_f['Search_Friction'] = df_f['Knowledge_4'].map(FRICTION_MAP)

    corr_cols = ['JobSat_num', 'LogComp', 'Silos_Friction', 'Search_Friction', 'YearsCodePro_num']
    corr_matrix = df_f[corr_cols].corr().round(3)

    top_ctry = df_f['Country'].value_counts().head(15).index.tolist()
    df_f['Country_Grouped'] = df_f['Country'].apply(lambda x: x if x in top_ctry else 'Other')
    country_dummies = pd.get_dummies(df_f['Country_Grouped'], prefix='ctry', drop_first=True)

    control_cols = ['LogComp', 'Silos_Friction', 'Search_Friction', 'YearsCodePro_num']
    scaler = StandardScaler()
    X_scaled = pd.DataFrame(scaler.fit_transform(df_f[control_cols]), columns=control_cols, index=df_f.index)
    X_full = pd.concat([X_scaled, country_dummies.astype(float)], axis=1)
    y_sat = df_f['JobSat_num']

    model = LinearRegression().fit(X_full, y_sat)
    controlled = pd.Series(model.coef_, index=X_full.columns)[control_cols]
    raw_corr = df_f[['JobSat_num'] + control_cols].corr()['JobSat_num'][control_cols]
    r2 = model.score(X_full, y_sat)

    labels = ['Pay (log)', 'Knowledge silos', 'Search friction', 'Experience']
    save('satisfaction', {
        'n': int(len(df_f)),
        'correlation_matrix': {
            'labels': ['Job satisfaction', 'Pay (log)', 'Knowledge silos', 'Search friction', 'Experience'],
            'matrix': corr_matrix.values.tolist(),
        },
        'raw_vs_controlled': {
            'labels': labels,
            'raw_correlation': raw_corr.round(3).tolist(),
            'controlled_coefficient': controlled.round(3).tolist(),
        },
        'controlled_r2': round(float(r2), 3),
    })


def section_model_insights(metadata_path: Path):
    with open(metadata_path) as f:
        meta = json.load(f)

    importance = meta['feature_importance']
    label_map = {
        'YearsCodePro_num': 'Experience (years)', 'Country_Grouped': 'Country',
        'EdLevel': 'Education', 'RemoteWork': 'Remote status',
    }
    for l in MODEL_LANGUAGES:
        label_map[f'lang_{l}'] = l

    named_importance = {label_map.get(k, k): v for k, v in importance.items()}

    save('model_insights', {
        'metrics': meta['metrics'],
        'feature_importance': named_importance,
        'is_language': {label_map.get(f'lang_{l}', l): True for l in MODEL_LANGUAGES},
        'mape_by_country': {
            COUNTRY_LABELS.get(k, k): v for k, v in meta.get('mape_by_country', {}).items()
        },
    })


def main(csv_path: str):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f'Loading raw survey for audit counts ...')
    raw = pd.read_csv(csv_path, usecols=['MainBranch'])
    initial_count = len(raw)
    prof_count = int((raw['MainBranch'] == 'I am a developer by profession').sum())

    print('Cleaning ...')
    df_clean = load_and_preprocess_data(csv_path)

    print('Computing dashboard sections ...')
    section_overview(df_clean, initial_count, prof_count)
    section_pay_by_country(df_clean)
    section_languages(df_clean)
    section_satisfaction(df_clean)

    metadata_path = Path(__file__).parent / 'artifacts' / 'metadata.json'
    if metadata_path.exists():
        section_model_insights(metadata_path)
    else:
        print('  skipping model_insights.json (run train_model.py first)')

    print(f'Done. Dashboard JSON written to {OUT_DIR}')


if __name__ == '__main__':
    csv = sys.argv[1] if len(sys.argv) > 1 else 'survey_results_public.csv'
    main(csv)
