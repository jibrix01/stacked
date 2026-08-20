"""
Shared data-loading and cleaning logic.

This mirrors the cleaning steps from the original case-study notebook
(stack_overflow_analysis.ipynb) exactly, so the trained model and the
dashboard stats are always computed from the same underlying dataset.
Both train_model.py and precompute_dashboard.py import from here instead
of duplicating this logic (DRY).
"""
import numpy as np
import pandas as pd

USE_COLS = [
    'ResponseId', 'MainBranch', 'Country', 'YearsCodePro', 'RemoteWork', 'EdLevel',
    'ConvertedCompYearly', 'LanguageHaveWorkedWith', 'AISent', 'AIAcc', 'AIThreat',
    'JobSat', 'Knowledge_2', 'Knowledge_4'
]

FRICTION_MAP = {
    'Strongly agree': 5,
    'Agree': 4,
    'Neither agree nor disagree': 3,
    'Disagree': 2,
    'Strongly disagree': 1
}

MODEL_LANGUAGES = ['JavaScript', 'Python', 'Java', 'TypeScript', 'C#', 'Go', 'Rust', 'SQL']

COUNTRY_LABELS = {
    'United States of America': 'United States',
    'United Kingdom of Great Britain and Northern Ireland': 'United Kingdom',
    'Germany': 'Germany',
    'Canada': 'Canada',
    'India': 'India',
}

TOP5_COUNTRIES = list(COUNTRY_LABELS.keys())


def _convert_years(val):
    if pd.isna(val):
        return np.nan
    if val == 'Less than 1 year':
        return 0.5
    if val == 'More than 50 years':
        return 50.0
    try:
        return float(val)
    except (TypeError, ValueError):
        return np.nan


def load_and_preprocess_data(filepath: str) -> pd.DataFrame:
    """Reproduces the notebook's Section: Data Cleaning."""
    df = pd.read_csv(filepath, usecols=USE_COLS)

    df_prof = df[df['MainBranch'] == 'I am a developer by profession'].copy()
    df_prof['YearsCodePro_num'] = df_prof['YearsCodePro'].apply(_convert_years)

    df_clean = df_prof[
        (df_prof['ConvertedCompYearly'] >= 5000) &
        (df_prof['ConvertedCompYearly'] <= 500000) &
        (df_prof['YearsCodePro_num'].notna())
    ].copy()

    df_clean['LogComp'] = np.log10(df_clean['ConvertedCompYearly'])
    return df_clean


def add_language_flags(df: pd.DataFrame, languages=MODEL_LANGUAGES) -> pd.DataFrame:
    df = df.copy()
    for language in languages:
        df[f'lang_{language}'] = df['LanguageHaveWorkedWith'].str.contains(language, regex=False)
    return df


def group_top_categories(series: pd.Series, top_n: int) -> pd.Series:
    top = series.value_counts().head(top_n).index.tolist()
    return series.apply(lambda x: x if x in top else 'Other'), top
