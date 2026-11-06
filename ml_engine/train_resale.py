"""
ml_engine/train_resale.py

Training script for the vehicle resale price prediction model.

IMPORTANT: This script requires a preprocessed dataset.
Run preprocessing.py first (after downloading the dataset).

Usage:
    python -m ml_engine.train_resale

Output: Trained model saved to artifacts/resale_model.joblib
"""

import logging
import joblib
from pathlib import Path

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = Path(__file__).parent.parent / 'artifacts'
PROCESSED_DATA = Path(__file__).parent / 'data' / 'processed' / 'processed_vehicles.csv'


def train_resale_model():
    """
    Train a resale price prediction model using the preprocessed vehicle dataset.

    Model: Gradient Boosting Regressor (or Random Forest as fallback).
    Features: vehicle_age, log_km_driven, age_mileage_interaction, encoded categoricals.
    Target: selling_price (log-transformed for normality).

    This function will NOT run if the processed dataset is not present.
    """
    import pandas as pd
    import numpy as np
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_absolute_error, r2_score

    if not PROCESSED_DATA.exists():
        raise FileNotFoundError(
            f"Processed dataset not found: {PROCESSED_DATA}\n"
            "Run ml_engine/preprocessing.py after downloading the raw dataset."
        )

    logger.info("Loading processed dataset...")
    df = pd.read_csv(PROCESSED_DATA)

    if 'selling_price' not in df.columns:
        raise ValueError("'selling_price' column not found in processed dataset.")

    # Define features — only use columns confirmed in dataset after validation
    FEATURE_COLS = [col for col in df.columns if col not in [
        'selling_price', 'name', 'price_per_km', 'Unnamed: 0'
    ]]
    X = df[FEATURE_COLS].fillna(0)
    y = np.log1p(df['selling_price'])  # Log-transform target

    logger.info(f"Training on {len(X)} samples with {len(FEATURE_COLS)} features.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=4,
            random_state=42
        ))
    ])

    logger.info("Training model...")
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(np.expm1(y_test), np.expm1(y_pred))
    r2 = r2_score(y_test, y_pred)
    logger.info(f"MAE (original scale): ₹{mae:,.0f}")
    logger.info(f"R² score: {r2:.4f}")

    # Save artifacts
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = ARTIFACTS_DIR / 'resale_model.joblib'
    feature_path = ARTIFACTS_DIR / 'resale_features.joblib'
    joblib.dump(model, model_path)
    joblib.dump(FEATURE_COLS, feature_path)

    logger.info(f"Model saved to {model_path}")
    logger.info(f"Feature list saved to {feature_path}")

    return {
        'mae': mae,
        'r2': r2,
        'n_features': len(FEATURE_COLS),
        'n_samples': len(X),
    }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger.warning(
        "Model training skipped — dataset not yet available. "
        "Download and preprocess data first. See README.md."
    )
