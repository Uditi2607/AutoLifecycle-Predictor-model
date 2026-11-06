"""
ml_engine/health_score.py

Vehicle health scoring module.

Produces a composite health score (0–100) based on:
- Vehicle age
- Mileage relative to age
- Service history regularity
- Repair expenditure relative to purchase price
- Months since last service

This is a rule-based system until sufficient health/maintenance data is available
to train a supervised ML model.
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class HealthScoreResult:
    """Container for the health score calculation results."""
    total_score: float
    grade: str
    components: dict
    flags: list
    summary: str


def calculate_health_score(
    vehicle_age: int,
    current_mileage: int,
    annual_km_driven: int,
    purchase_price: float,
    repair_expenditure: float,
    service_records_count: int,
    months_since_last_service: int,
) -> HealthScoreResult:
    """
    Calculate a composite vehicle health score.

    Score components (each 0–100, weighted):
    - Age score (20%): Newer = healthier
    - Mileage score (25%): Lower relative mileage = healthier
    - Service regularity (20%): More regular service = healthier
    - Repair burden (20%): Lower repair costs relative to price = healthier
    - Service recency (15%): Recent service = healthier

    Args:
        vehicle_age: Age in years.
        current_mileage: Odometer in km.
        annual_km_driven: Average annual km.
        purchase_price: Original purchase price.
        repair_expenditure: Total repair spend.
        service_records_count: Number of service records.
        months_since_last_service: Months since last service.

    Returns:
        HealthScoreResult with score, grade, components and flags.
    """
    flags = []

    # --- Age Score (20%) ---
    # Score declines linearly: 100 at age 0, 0 at age 20+
    age_score = max(0, 100 - (vehicle_age * 5))

    # --- Mileage Score (25%) ---
    # Compare to expected mileage (annual_km * age)
    expected_km = annual_km_driven * max(vehicle_age, 1)
    mileage_ratio = current_mileage / max(expected_km, 1)
    if mileage_ratio > 1.3:
        flags.append('⚠️ Mileage significantly higher than average for vehicle age.')
    mileage_score = max(0, 100 - (mileage_ratio * 50))

    # --- Service Regularity Score (20%) ---
    # Expect at least 1 service per year
    expected_services = max(vehicle_age, 1)
    service_ratio = service_records_count / expected_services
    service_score = min(100, service_ratio * 80)
    if service_records_count == 0:
        flags.append('⚠️ No service records found — history unknown.')

    # --- Repair Burden Score (20%) ---
    if purchase_price > 0:
        repair_pct = repair_expenditure / purchase_price
        repair_score = max(0, 100 - (repair_pct * 200))
        if repair_pct > 0.30:
            flags.append('⚠️ Repair costs exceed 30% of purchase price.')
    else:
        repair_score = 50  # Neutral if no purchase price given

    # --- Service Recency Score (15%) ---
    # Expect service every 6 months (12 = overdue, 24 = critically overdue)
    if months_since_last_service <= 6:
        recency_score = 100
    elif months_since_last_service <= 12:
        recency_score = 75
    elif months_since_last_service <= 18:
        recency_score = 50
        flags.append('⚠️ Service overdue by more than 6 months.')
    elif months_since_last_service <= 24:
        recency_score = 25
        flags.append('🔴 Service critically overdue — immediate attention needed.')
    else:
        recency_score = 0
        flags.append('🔴 No service in 2+ years — high risk.')

    # --- Weighted Total ---
    weights = {
        'age': 0.20,
        'mileage': 0.25,
        'service_regularity': 0.20,
        'repair_burden': 0.20,
        'service_recency': 0.15,
    }
    components = {
        'age': round(age_score, 1),
        'mileage': round(mileage_score, 1),
        'service_regularity': round(service_score, 1),
        'repair_burden': round(repair_score, 1),
        'service_recency': round(recency_score, 1),
    }
    total = sum(components[k] * weights[k] for k in weights)
    total = round(max(0, min(100, total)), 1)

    # --- Grade ---
    if total >= 80:
        grade = 'A — Excellent'
    elif total >= 65:
        grade = 'B — Good'
    elif total >= 50:
        grade = 'C — Fair'
    elif total >= 35:
        grade = 'D — Poor'
    else:
        grade = 'F — Critical'

    summary = (
        f"Health score: {total}/100 ({grade}). "
        f"{'No major flags.' if not flags else str(len(flags)) + ' flag(s) detected.'}"
    )

    return HealthScoreResult(
        total_score=total,
        grade=grade,
        components=components,
        flags=flags,
        summary=summary,
    )
