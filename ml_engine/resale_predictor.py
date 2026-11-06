"""
ml_engine/resale_predictor.py

Resale price prediction for a given vehicle.

Usage:
    from ml_engine.resale_predictor import predict_resale_value
    result = predict_resale_value(vehicle_data)

NOTE: Returns None if no trained model is available.
      Train the model first using ml_engine/train_resale.py.
"""

import logging
import joblib
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = Path(__file__).parent.parent / 'artifacts'
MODEL_PATH = ARTIFACTS_DIR / 'resale_model.joblib'
FEATURES_PATH = ARTIFACTS_DIR / 'resale_features.joblib'


def model_is_available() -> bool:
    """Check whether a trained resale model exists in artifacts/."""
    return MODEL_PATH.exists() and FEATURES_PATH.exists()


def predict_resale_value(vehicle_data: dict) -> dict | None:
    """
    Predict the resale value of a vehicle using the trained model.

    Args:
        vehicle_data: Dictionary with vehicle attributes matching training features.
                      Keys must correspond to features used during training.

    Returns:
        Dictionary with:
            - predicted_price: Estimated resale value
            - confidence: Approximate confidence indicator
            - model_version: Identifier for reproducibility
        Returns None if no trained model is available.
    """
    if not model_is_available():
        logger.warning(
            "Resale model not found. Train the model first "
            "using ml_engine/train_resale.py."
        )
        return None

    model = joblib.load(MODEL_PATH)
    feature_cols = joblib.load(FEATURES_PATH)

    import pandas as pd
    df = pd.DataFrame([vehicle_data])

    # Align feature columns
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0
    df = df[feature_cols].fillna(0)

    log_price = model.predict(df)[0]
    predicted_price = np.expm1(log_price)

    return {
        'predicted_price': round(float(predicted_price), 2),
        'confidence': 'Model trained — see evaluation report for metrics.',
        'model_version': 'resale_v1',
    }
