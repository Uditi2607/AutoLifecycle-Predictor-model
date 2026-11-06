"""
ml_engine/preprocessing.py

Data cleaning and feature engineering for vehicle resale prediction.

This module prepares raw vehicle data for model training.
It should be run after a validated dataset has been placed in ml_engine/data/raw/.

Expected input: CSV file with columns documented in README.md (Data Ingestion section).
Output: Cleaned feature matrix saved to ml_engine/data/processed/.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

RAW_DATA_DIR = Path(__file__).parent / 'data' / 'raw'
PROCESSED_DATA_DIR = Path(__file__).parent / 'data' / 'processed'


def load_raw_data(filename: str) -> pd.DataFrame:
    """
    Load a raw CSV dataset from ml_engine/data/raw/.

    Args:
        filename: Name of the CSV file (e.g. 'vehicles.csv').

    Returns:
        Raw DataFrame.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    filepath = RAW_DATA_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(
            f"Raw data file not found: {filepath}\n"
            "Please download the dataset and place it in ml_engine/data/raw/. "
            "See README.md for instructions."
        )
    logger.info(f"Loading raw data from {filepath}")
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    return df


def validate_columns(df: pd.DataFrame, required_cols: list) -> bool:
    """
    Validate that required columns are present in the DataFrame.

    Args:
        df: Input DataFrame.
        required_cols: List of column names that must be present.

    Returns:
        True if all columns are present.

    Raises:
        ValueError: If any required column is missing.
    """
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns: {missing}\n"
            f"Available columns: {df.columns.tolist()}"
        )
    logger.info("Column validation passed.")
    return True


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply standard cleaning steps to the raw DataFrame.

    Steps:
    - Drop duplicate rows.
    - Drop rows with null values in critical columns.
    - Remove negative prices or mileage.
    - Convert types where needed.

    Args:
        df: Raw DataFrame.

    Returns:
        Cleaned DataFrame.
    """
    initial_len = len(df)
    df = df.drop_duplicates()
    logger.info(f"Dropped {initial_len - len(df)} duplicate rows.")

    # Remove clearly invalid rows
    for col in df.select_dtypes(include=[np.number]).columns:
        if 'price' in col.lower() or 'mileage' in col.lower() or 'km' in col.lower():
            df = df[df[col] >= 0]

    df = df.dropna(subset=['selling_price', 'year', 'km_driven'])
    logger.info(f"Cleaned dataset: {len(df)} rows remaining.")
    return df


def engineer_features(df: pd.DataFrame, current_year: int = 2024) -> pd.DataFrame:
    """
    Create derived features from raw columns.

    Features created:
    - vehicle_age: current_year - year
    - age_mileage_interaction: vehicle_age * km_driven / 1000
    - log_km_driven: log(km_driven + 1)
    - price_per_km: selling_price / (km_driven + 1)

    Args:
        df: Cleaned DataFrame.
        current_year: Reference year for age calculation.

    Returns:
        DataFrame with additional engineered features.
    """
    df = df.copy()

    if 'year' in df.columns:
        df['vehicle_age'] = current_year - df['year']

    if 'km_driven' in df.columns:
        df['log_km_driven'] = np.log1p(df['km_driven'])

    if 'vehicle_age' in df.columns and 'km_driven' in df.columns:
        df['age_mileage_interaction'] = df['vehicle_age'] * df['km_driven'] / 1000

    if 'selling_price' in df.columns and 'km_driven' in df.columns:
        df['price_per_km'] = df['selling_price'] / (df['km_driven'] + 1)

    logger.info(f"Feature engineering complete. Columns: {df.columns.tolist()}")
    return df


def encode_categoricals(df: pd.DataFrame, cat_cols: list) -> pd.DataFrame:
    """
    One-hot encode categorical columns.

    Args:
        df: Input DataFrame.
        cat_cols: List of categorical column names.

    Returns:
        DataFrame with encoded categories.
    """
    df = pd.get_dummies(df, columns=cat_cols, drop_first=True)
    logger.info(f"Encoded categoricals. Shape: {df.shape}")
    return df


def save_processed(df: pd.DataFrame, filename: str) -> Path:
    """
    Save processed DataFrame to ml_engine/data/processed/.

    Args:
        df: Processed DataFrame.
        filename: Output filename (e.g. 'processed_vehicles.csv').

    Returns:
        Path to saved file.
    """
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DATA_DIR / filename
    df.to_csv(out_path, index=False)
    logger.info(f"Saved processed data to {out_path}")
    return out_path


def run_pipeline(raw_filename: str = 'vehicles.csv') -> pd.DataFrame:
    """
    Run the full preprocessing pipeline.

    NOTE: This function requires a validated raw dataset in ml_engine/data/raw/.
    It will raise FileNotFoundError if the dataset is not present.
    Do not call this function until the dataset has been downloaded and validated.

    Args:
        raw_filename: Name of the raw CSV file.

    Returns:
        Processed DataFrame ready for model training.
    """
    # Columns expected from the Mendeley dataset (verify after download)
    REQUIRED_COLS = ['year', 'selling_price', 'km_driven', 'fuel', 'seller_type',
                     'transmission', 'owner']

    df = load_raw_data(raw_filename)
    validate_columns(df, REQUIRED_COLS)
    df = clean_data(df)
    df = engineer_features(df)
    df = encode_categoricals(df, cat_cols=['fuel', 'seller_type', 'transmission', 'owner'])
    save_processed(df, 'processed_vehicles.csv')

    return df


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger.warning(
        "Preprocessing pipeline not run — no dataset found in ml_engine/data/raw/. "
        "Download the dataset first. See README.md."
    )
