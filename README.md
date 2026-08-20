# Stacked

A web application built on top of the case study **"Stack, or Where You're Stacked?"**, analyzing developer compensation, work arrangements, programming language, and workplace satisfaction from the 2024 Stack Overflow Developer Survey (19,990 professional developers across 185 countries).

Dataset source: [Stack Overflow Annual Developer Survey 2024 (Kaggle)](https://www.kaggle.com/datasets/berkayalan/stack-overflow-annual-developer-survey-2024)

## Application Pages

- **Summary / Insights (`/`)**: Summary of the insights obtained in the case study.
- **Predict (`/predict`)**: Input a profile (years of experience, country, education, work arrangement, languages used) to compute an estimated salary range using a Random Forest model trained on the survey data.
- **Dashboard (`/dashboard`)**: Interactive charts organized by section (Overview, Pay by Country, Languages, Satisfaction, and The Model).

## Project Structure

```
stacked/
├── stack_overflow_analysis.ipynb   Original Jupyter analysis notebook
├── README.md
└── backend/
    ├── app.py                      Flask app setup & route registration
    ├── config.py                   Path configurations
    ├── requirements.txt            Python dependencies
    ├── run.py                      Entry point script
    ├── routes/
    │   ├── insights.py             /insights route (Summary page)
    │   ├── predict.py              /predict page & /api/predict endpoints
    │   └── dashboard.py            /dashboard page & /api/dashboard/<section>
    ├── services/
    │   ├── model_service.py        Handles model loading, validation, & inference
    │   └── dashboard_service.py    Serves precomputed JSON chart data
    ├── ml/
    │   ├── data_prep.py            Shared data cleaning & preprocessing logic
    │   ├── train_model.py          Trains Ridge & Random Forest models, outputs artifacts
    │   ├── precompute_dashboard.py Generates JSON chart payloads for the dashboard
    │   └── artifacts/
    │       ├── model.joblib        Fitted Random Forest pipeline
    │       └── metadata.json       Dropdown options, metrics, and feature importance
    ├── data/
    │   └── dashboard/*.json        Precomputed chart data files
    ├── static/
    │   ├── css/                    Design tokens and component styling
    │   └── js/                     Fetch helper, Chart.js configuration, page scripts
    └── templates/
        ├── base.html               Main layout shell & navigation
        ├── insights.html           Summary page template
        ├── predict.html            Salary predictor template
        └── dashboard.html          Interactive charts dashboard template
```

## Prerequisites
- Python 3.9+

## Setup & Run

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the Flask app:
   ```bash
   python app.py
   ```

4. Open `http://localhost:5000` in your browser.

> Note: The pre-trained model (`model.joblib`) and precomputed dashboard data are included under `ml/artifacts/` and `data/dashboard/`, so you can run the app immediately without processing the raw CSV.

## Retraining & Precomputing Data

To retrain the model and regenerate dashboard JSON payloads from fresh survey data:

```bash
cd backend
python -m ml.train_model /path/to/survey_results_public.csv
python -m ml.precompute_dashboard /path/to/survey_results_public.csv
```

- `ml/data_prep.py` acts as the single source of truth for preprocessing across model training and dashboard chart generation.
- Model architecture: `RandomForestRegressor` (`n_estimators=300`, `max_depth=8`) predicting $\log_{10}(\text{ConvertedCompYearly})$.
- Features include numeric experience (`YearsCodePro_num`), grouped country labels, education level, remote work status, and language indicators.
