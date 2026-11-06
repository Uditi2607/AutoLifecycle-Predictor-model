# AutoLifecycle Predictor

**AI-Powered Vehicle Lifecycle, Resale Value Prediction, Depreciation Forecasting and Exchange Recommendation Platform**

---

## Overview

AutoLifecycle Predictor helps vehicle owners determine whether to **KEEP**, **MONITOR**, **SELL** or **EXCHANGE** their vehicle by analysing seven key signals through a modular ML pipeline.

---

## Quick Start

```bash
# 1. Navigate into the project
cd AutoLifecycle-Predictor

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate       # Mac/Linux
# venv\Scripts\activate        # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create environment file
cp .env.example .env

# 5. Apply database migrations
python manage.py migrate

# 6. Create a superuser (optional)
python manage.py createsuperuser

# 7. Start the development server
python manage.py runserver
```

Then open: http://127.0.0.1:8000

---

## Project Structure

```
AutoLifecycle-Predictor/
├── config/                  Django settings, URL root, ASGI/WSGI
├── apps/
│   ├── core/                Landing page, Dashboard, How It Works
│   ├── vehicles/            Vehicle model, registration, CRUD
│   └── analytics/           Vehicle Outlook, Fleet Insights
├── ml_engine/
│   ├── data/raw/            Raw dataset (not committed)
│   ├── data/processed/      Cleaned features (not committed)
│   ├── notebooks/           Exploratory notebooks
│   ├── preprocessing.py     Data cleaning and feature engineering
│   ├── train_resale.py      Resale model training script
│   ├── resale_predictor.py  Resale value inference
│   ├── depreciation.py      Depreciation curve forecasting
│   ├── health_score.py      Vehicle health scoring
│   ├── maintenance.py       Maintenance risk and cost estimation
│   ├── decision_engine.py   KEEP/MONITOR/SELL/EXCHANGE decision
│   └── evaluation.py        Model evaluation utilities
├── artifacts/               Trained model files (not committed)
├── templates/               Django HTML templates
├── static/                  CSS, JS, images
├── tests/                   Test suite
├── manage.py
├── requirements.txt
└── .env.example
```

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, Django 4.2 |
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5 |
| ML | Pandas, NumPy, Scikit-learn, Statsmodels, Joblib |
| Visualisation | Plotly |
| Database | SQLite (development) |

---

## ML Engine — Data Ingestion

### Candidate Dataset

**Mendeley Vehicle Sales Dataset** — DOI: [10.17632/8d38h82fyt.2](https://data.mendeley.com/datasets/8d38h82fyt/2)

Expected columns (verify after download):

| Column | Description |
|--------|-------------|
| `name` | Vehicle brand and model |
| `year` | Manufacturing year |
| `selling_price` | Transaction selling price |
| `km_driven` | Odometer reading (km) |
| `fuel` | Fuel type (Petrol/Diesel/CNG/etc.) |
| `seller_type` | Individual/Dealer/Trustmark |
| `transmission` | Manual/Automatic |
| `owner` | Ownership count |

### Validation Process

1. Download the dataset from the Mendeley link above.
2. Place the CSV file at `ml_engine/data/raw/vehicles.csv`.
3. Run column validation:
   ```bash
   python -c "from ml_engine.preprocessing import load_raw_data, validate_columns; df = load_raw_data('vehicles.csv'); print(df.columns.tolist())"
   ```
4. Verify that actual columns match the expected list above.
5. If column names differ, update `preprocessing.py` accordingly.

### Training the Resale Model

```bash
# Step 1: Preprocess
python -m ml_engine.preprocessing

# Step 2: Train
python -m ml_engine.train_resale

# Step 3: Evaluate
python -c "from ml_engine.evaluation import evaluate_resale_model; print(evaluate_resale_model())"
```

> **Important:** Do not claim the model is trained until these steps have been completed and the evaluation report confirms acceptable MAE and R² scores.

---

## ML Module Status

| Module | Method | Status |
|--------|--------|--------|
| Resale Price Predictor | Gradient Boosting (ML) | ⏳ Awaiting training data |
| Depreciation Forecaster | Declining Balance (rule-based) | ✅ Active |
| Health Scorer | Weighted rules | ✅ Active |
| Maintenance Risk Assessor | Rule-based heuristics | ✅ Active |
| Ownership Cost Estimator | Rule-based | ✅ Active |
| Decision Engine | Multi-signal weighted logic | ✅ Active |

---

## Pages

| URL | Page |
|-----|------|
| `/` | Landing page |
| `/dashboard/` | Fleet dashboard |
| `/vehicles/` | Vehicle list |
| `/vehicles/register/` | Register a vehicle |
| `/vehicles/<id>/` | Vehicle detail |
| `/analytics/vehicle/<id>/` | Vehicle Outlook (analysis) |
| `/analytics/fleet/` | Fleet Insights |
| `/how-it-works/` | Methodology page |
| `/admin/` | Django admin |

---

## Running Tests

```bash
python manage.py test tests/
```

---

## Git & GitHub

Repository: https://github.com/Uditi2607/AutoLifecycle-Predictor (private)

---

## License

Private — All rights reserved.
