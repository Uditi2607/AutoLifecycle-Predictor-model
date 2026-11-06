"""
ml_engine/decision_engine.py

KEEP / MONITOR / EXCHANGE / SELL decision engine.

Combines outputs from all ML/rule-based modules to produce a final
explainable recommendation for the vehicle owner.

Decision hierarchy:
1. KEEP     — Vehicle is healthy, low cost, good residual value.
2. MONITOR  — Borderline. Watch for deterioration triggers.
3. SELL     — Vehicle has reasonable residual value but rising costs.
4. EXCHANGE — Trade in now — depreciating fast, high risk, high cost.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class LifecycleDecision:
    """Container for the full lifecycle recommendation."""
    decision: str               # KEEP | MONITOR | SELL | EXCHANGE
    confidence: str             # HIGH | MEDIUM | LOW
    score: float                # Decision confidence score 0–100
    reasons: List[str]          # Explanation bullets
    next_review_months: int     # When to reassess
    summary: str


def make_decision(
    health_score: float,
    vehicle_age: int,
    residual_value_pct: float,
    maintenance_risk_level: str,
    annual_maintenance_cost: float,
    purchase_price: float,
    repair_expenditure: float,
) -> LifecycleDecision:
    """
    Produce a lifecycle decision based on aggregated vehicle signals.

    Args:
        health_score: 0–100 health score from health_score module.
        vehicle_age: Age in years.
        residual_value_pct: Remaining value as % of purchase price (0–100).
        maintenance_risk_level: 'LOW'|'MEDIUM'|'HIGH'|'CRITICAL'.
        annual_maintenance_cost: Estimated annual maintenance (₹).
        purchase_price: Original purchase price.
        repair_expenditure: Cumulative repair costs.

    Returns:
        LifecycleDecision with recommendation and explanation.
    """
    reasons = []
    negative_signals = 0
    positive_signals = 0

    # --- Signal 1: Health ---
    if health_score >= 75:
        positive_signals += 2
        reasons.append(f'✅ Strong vehicle health score ({health_score}/100).')
    elif health_score >= 55:
        positive_signals += 1
        reasons.append(f'📊 Moderate health score ({health_score}/100) — monitor trends.')
    elif health_score >= 35:
        negative_signals += 1
        reasons.append(f'⚠️ Below-average health score ({health_score}/100).')
    else:
        negative_signals += 2
        reasons.append(f'🔴 Poor health score ({health_score}/100) — high concern.')

    # --- Signal 2: Age ---
    if vehicle_age <= 3:
        positive_signals += 2
        reasons.append(f'✅ Vehicle is relatively new ({vehicle_age} years old).')
    elif vehicle_age <= 6:
        positive_signals += 1
        reasons.append(f'📊 Vehicle age is average ({vehicle_age} years).')
    elif vehicle_age <= 10:
        negative_signals += 1
        reasons.append(f'⚠️ Vehicle age ({vehicle_age} years) is increasing ownership risk.')
    else:
        negative_signals += 2
        reasons.append(f'🔴 Vehicle is {vehicle_age} years old — significant age-related risk.')

    # --- Signal 3: Residual Value ---
    if residual_value_pct >= 60:
        positive_signals += 2
        reasons.append(f'✅ Strong residual value ({residual_value_pct:.0f}% of purchase price).')
    elif residual_value_pct >= 40:
        positive_signals += 1
        reasons.append(f'📊 Moderate residual value ({residual_value_pct:.0f}%).')
    elif residual_value_pct >= 25:
        negative_signals += 1
        reasons.append(f'⚠️ Residual value declining ({residual_value_pct:.0f}%).')
    else:
        negative_signals += 2
        reasons.append(f'🔴 Residual value critically low ({residual_value_pct:.0f}%).')

    # --- Signal 4: Maintenance Risk ---
    risk_map = {'LOW': 2, 'MEDIUM': 1, 'HIGH': -1, 'CRITICAL': -2}
    risk_delta = risk_map.get(maintenance_risk_level, 0)
    if risk_delta > 0:
        positive_signals += risk_delta
        reasons.append(f'✅ Maintenance risk is {maintenance_risk_level}.')
    elif risk_delta < 0:
        negative_signals += abs(risk_delta)
        reasons.append(f'🔴 Maintenance risk is {maintenance_risk_level} — action required.')

    # --- Signal 5: Annual Cost Burden ---
    if purchase_price > 0:
        cost_pct = annual_maintenance_cost / purchase_price * 100
        if cost_pct < 3:
            positive_signals += 1
            reasons.append(f'✅ Annual maintenance cost is low ({cost_pct:.1f}% of purchase price).')
        elif cost_pct < 8:
            reasons.append(f'📊 Annual maintenance cost is moderate ({cost_pct:.1f}%).')
        else:
            negative_signals += 1
            reasons.append(f'⚠️ Annual maintenance cost is high ({cost_pct:.1f}% of purchase).')

    # --- Decision Logic ---
    net_score = positive_signals - negative_signals
    total_signals = positive_signals + negative_signals

    if net_score >= 4:
        decision = 'KEEP'
        confidence = 'HIGH'
        next_review = 12
        summary = 'Your vehicle is in good condition. Keep it and maintain regularly.'
    elif net_score >= 2:
        decision = 'KEEP'
        confidence = 'MEDIUM'
        next_review = 6
        summary = 'Vehicle is acceptable. Continue monitoring key metrics.'
    elif net_score >= 0:
        decision = 'MONITOR'
        confidence = 'MEDIUM'
        next_review = 3
        summary = 'Vehicle is borderline. Watch health, costs and service needs closely.'
    elif net_score >= -2:
        decision = 'SELL'
        confidence = 'MEDIUM'
        next_review = 1
        summary = 'Consider selling while residual value remains reasonable.'
    else:
        decision = 'EXCHANGE'
        confidence = 'HIGH'
        next_review = 0
        summary = 'Exchange or dispose now — multiple negative indicators detected.'

    score = max(0, min(100, 50 + (net_score * 10)))

    return LifecycleDecision(
        decision=decision,
        confidence=confidence,
        score=round(score, 1),
        reasons=reasons,
        next_review_months=next_review,
        summary=summary,
    )
