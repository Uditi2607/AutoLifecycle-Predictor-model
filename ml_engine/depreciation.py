"""
ml_engine/depreciation.py

Depreciation forecasting module.

Provides future depreciation curves using:
- Declining balance model (rule-based)
- Regression-based depreciation (once trained on data)

This module can be used without a trained model using the rule-based fallback.
"""

import numpy as np
from typing import Optional


def declining_balance_depreciation(
    purchase_price: float,
    vehicle_age: int,
    fuel_type: str = 'petrol',
    n_years: int = 15,
) -> dict:
    """
    Estimate future resale values using declining balance depreciation.

    Rate assumptions (approximate Indian market):
    - Year 1: 15–20% (highest drop)
    - Years 2–5: 8–12%
    - Years 6+: 5–8%

    Args:
        purchase_price: Original purchase price.
        vehicle_age: Current age of the vehicle in years.
        fuel_type: Affects depreciation rate.
        n_years: Number of future years to forecast.

    Returns:
        Dictionary with 'years', 'values', 'rates', 'current_value'.
    """
    # Depreciation rates by year bracket
    def get_rate(year: int, fuel: str) -> float:
        electric_discount = -0.02 if fuel == 'electric' else 0
        if year == 0:
            return 0.18 + electric_discount
        elif year <= 4:
            return 0.10 + electric_discount
        elif year <= 8:
            return 0.07
        else:
            return 0.05

    # Depreciate to current age first
    current_value = purchase_price
    for y in range(vehicle_age):
        rate = get_rate(y, fuel_type)
        current_value = current_value * (1 - rate)

    # Project forward
    years = []
    values = []
    rates = []
    val = current_value
    for i in range(n_years + 1):
        years.append(vehicle_age + i)
        values.append(round(val, 2))
        rate = get_rate(vehicle_age + i, fuel_type)
        rates.append(round(rate * 100, 1))
        val = val * (1 - rate)

    return {
        'years': years,
        'values': values,
        'rates': rates,
        'current_value': round(current_value, 2),
        'purchase_price': purchase_price,
        'total_depreciation_pct': round(
            (1 - current_value / purchase_price) * 100, 1
        ) if purchase_price > 0 else 0,
        'method': 'rule_based_declining_balance',
    }


def estimate_exchange_window(
    purchase_price: float,
    vehicle_age: int,
    annual_km: int,
    repair_expenditure: float,
    fuel_type: str = 'petrol',
) -> dict:
    """
    Estimate the optimal window to sell or exchange the vehicle.

    Uses cost-of-ownership vs. residual value analysis.

    Args:
        purchase_price: Original purchase price.
        vehicle_age: Current age in years.
        annual_km: Annual kilometres driven.
        repair_expenditure: Total repair costs to date.
        fuel_type: Fuel type.

    Returns:
        Dictionary with exchange window recommendation.
    """
    dep = declining_balance_depreciation(purchase_price, vehicle_age, fuel_type, n_years=10)
    current_value = dep['current_value']
    residual_pct = current_value / purchase_price if purchase_price > 0 else 0

    # Heuristic exchange triggers
    triggers = []
    if residual_pct < 0.40:
        triggers.append('Residual value below 40% — depreciation curve flattening.')
    if vehicle_age >= 7:
        triggers.append('Vehicle exceeds 7 years — increasing maintenance risk.')
    if repair_expenditure > purchase_price * 0.25:
        triggers.append('Repair costs exceed 25% of purchase price.')
    if annual_km > 20000 and vehicle_age >= 5:
        triggers.append('High mileage acceleration — faster wear expected.')

    if len(triggers) >= 2:
        window = 'NOW — Multiple exchange triggers active.'
        urgency = 'high'
    elif len(triggers) == 1:
        window = 'SOON — Within the next 12–18 months.'
        urgency = 'medium'
    else:
        window = 'NOT YET — Vehicle still in viable ownership zone.'
        urgency = 'low'

    return {
        'exchange_window': window,
        'urgency': urgency,
        'triggers': triggers,
        'current_value': current_value,
        'residual_pct': round(residual_pct * 100, 1),
        'method': 'rule_based_heuristic',
    }
