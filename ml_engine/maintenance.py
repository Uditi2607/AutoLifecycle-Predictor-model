"""
ml_engine/maintenance.py

Maintenance risk and cost estimation module.

Provides:
- Risk level assessment (LOW / MEDIUM / HIGH / CRITICAL)
- Estimated upcoming maintenance costs
- Recommended next service actions

This is a rule-based prototype until a labelled maintenance dataset is available.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class MaintenanceResult:
    """Container for maintenance assessment results."""
    risk_level: str
    risk_score: float          # 0–100 (100 = highest risk)
    estimated_annual_cost: float
    recommended_actions: List[str]
    summary: str


def assess_maintenance_risk(
    vehicle_age: int,
    current_mileage: int,
    months_since_last_service: int,
    service_records_count: int,
    repair_expenditure: float,
    purchase_price: float,
    fuel_type: str = 'petrol',
    transmission: str = 'manual',
) -> MaintenanceResult:
    """
    Assess maintenance risk and estimate upcoming costs.

    Risk factors:
    - Overdue service
    - Age and mileage
    - Poor service history
    - High cumulative repairs

    Args:
        vehicle_age: Age in years.
        current_mileage: Odometer in km.
        months_since_last_service: Months since last service.
        service_records_count: Number of documented services.
        repair_expenditure: Total repair costs to date.
        purchase_price: Original purchase price.
        fuel_type: Fuel type (affects servicing cost).
        transmission: Transmission type.

    Returns:
        MaintenanceResult with risk level, cost estimate and actions.
    """
    risk_points = 0.0
    actions = []

    # Overdue service risk
    if months_since_last_service > 24:
        risk_points += 35
        actions.append('🔴 URGENT: Schedule comprehensive service immediately.')
    elif months_since_last_service > 12:
        risk_points += 20
        actions.append('⚠️ Service overdue — book within 2–4 weeks.')
    elif months_since_last_service > 6:
        risk_points += 8
        actions.append('📅 Service approaching — plan within 1–2 months.')

    # Mileage risk
    if current_mileage > 150000:
        risk_points += 20
        actions.append('🔧 High mileage — inspect timing belt/chain, suspension, brakes.')
    elif current_mileage > 80000:
        risk_points += 10
        actions.append('🔧 Inspect brake pads, tyres and battery condition.')

    # Age risk
    if vehicle_age > 10:
        risk_points += 15
        actions.append('📋 Recommend full mechanical inspection — vehicle over 10 years old.')
    elif vehicle_age > 7:
        risk_points += 8

    # Service history risk
    expected_services = max(vehicle_age, 1)
    if service_records_count < expected_services * 0.5:
        risk_points += 15
        actions.append('📄 Incomplete service history — unknown maintenance gaps.')

    # Cumulative repair ratio
    if purchase_price > 0:
        repair_ratio = repair_expenditure / purchase_price
        if repair_ratio > 0.4:
            risk_points += 20
            actions.append('💰 Repair costs very high — evaluate cost of continued ownership.')
        elif repair_ratio > 0.2:
            risk_points += 10

    # Transmission risk factor
    if transmission == 'automatic' and vehicle_age > 8:
        risk_points += 5
        actions.append('⚙️ Automatic transmission — consider fluid service if not done recently.')

    # Normalise to 0–100
    risk_score = min(100, risk_points)

    # Risk level
    if risk_score >= 65:
        risk_level = 'CRITICAL'
    elif risk_score >= 45:
        risk_level = 'HIGH'
    elif risk_score >= 25:
        risk_level = 'MEDIUM'
    else:
        risk_level = 'LOW'

    # Estimated annual cost (rule-based approximation)
    base_service_cost = {
        'petrol': 8000,
        'diesel': 10000,
        'hybrid': 9000,
        'electric': 5000,
        'cng': 7000,
    }.get(fuel_type, 8000)

    age_multiplier = 1.0 + (vehicle_age * 0.05)
    mileage_multiplier = 1.0 + (current_mileage / 100000 * 0.3)
    estimated_annual_cost = base_service_cost * age_multiplier * mileage_multiplier

    if not actions:
        actions.append('✅ Vehicle appears well-maintained. Continue regular service schedule.')

    summary = (
        f"Maintenance Risk: {risk_level} (Score: {risk_score:.0f}/100). "
        f"Estimated annual maintenance: ₹{estimated_annual_cost:,.0f}."
    )

    return MaintenanceResult(
        risk_level=risk_level,
        risk_score=round(risk_score, 1),
        estimated_annual_cost=round(estimated_annual_cost, 2),
        recommended_actions=actions,
        summary=summary,
    )
