"""
ml_engine/evaluation.py

Model evaluation utilities for all trained ML models.

Usage:
    from ml_engine.evaluation import evaluate_resale_model
    report = evaluate_resale_model()
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = Path(__file__).parent.parent / 'artifacts'


def evaluate_resale_model() -> dict | None:
    """
    Evaluate the trained resale model against the test split.

    Returns:
        Dictionary with evaluation metrics, or None if model not trained.
    """
    model_path = ARTIFACTS_DIR / 'resale_model.joblib'
    features_path = ARTIFACTS_DIR / 'resale_features.joblib'
    processed_data = Path(__file__).parent / 'data' / 'processed' / 'processed_vehicles.csv'

    if not model_path.exists():
        logger.warning("Resale model not found. Train model first.")
        return None

    import joblib
    import pandas as pd
    import numpy as np
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.model_selection import train_test_split

    model = joblib.load(model_path)
    feature_cols = joblib.load(features_path)
    df = pd.read_csv(processed_data)

    X = df[feature_cols].fillna(0)
    y = np.log1p(df['selling_price'])

    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(np.expm1(y_test), np.expm1(y_pred))
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    report = {
        'model': 'resale_v1',
        'mae_original_scale': round(mae, 2),
        'rmse_log_scale': round(rmse, 4),
        'r2_score': round(r2, 4),
        'test_samples': len(X_test),
    }
    logger.info(f"Evaluation report: {report}")
    return report
