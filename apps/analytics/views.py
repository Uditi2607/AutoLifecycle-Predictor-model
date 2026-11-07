"""
Analytics app views — Vehicle Outlook and Fleet Insights.

Phase 1: ML engine modules wired into view logic.
All six rule-based modules are now the authoritative source of truth.
The resale predictor is called optionally; it returns None gracefully
when no trained model is present.
"""
import json
import logging
from datetime import date

from django.shortcuts import render, get_object_or_404

from apps.vehicles.models import Vehicle
from ml_engine.health_score import calculate_health_score
from ml_engine.depreciation import declining_balance_depreciation, estimate_exchange_window
from ml_engine.maintenance import assess_maintenance_risk
from ml_engine.decision_engine import make_decision
from ml_engine.resale_predictor import predict_resale_value

logger = logging.getLogger(__name__)

# CSS colour class per decision (matches .rec-badge.<decision> classes in main.css)
_DECISION_COLOUR = {
    'KEEP': 'keep',
    'MONITOR': 'monitor',
    'SELL': 'sell',
    'EXCHANGE': 'exchange',
}

# Text / theme colour per decision
_DECISION_TEXT_COLOUR = {
    'KEEP': 'emerald',
    'MONITOR': 'amber',
    'SELL': 'blue',
    'EXCHANGE': 'red',
}

# Bootstrap Icon name per decision
_DECISION_ICON = {
    'KEEP': 'check-circle-fill',
    'MONITOR': 'eye-fill',
    'SELL': 'currency-rupee',
    'EXCHANGE': 'arrow-left-right',
}


def vehicle_outlook(request, pk):
    """
    Detailed analytics view for a single vehicle.

    Uses the full ML engine pipeline:
      - health_score.py      → 5-component weighted health score (0–100)
      - depreciation.py      → Fuel-type-aware declining-balance depreciation
      - maintenance.py       → 11-factor risk scorer, cost estimator, action list
      - decision_engine.py   → 7-signal KEEP / MONITOR / SELL / EXCHANGE decision
      - resale_predictor.py  → ML resale price (None if model not yet trained)
    """
    vehicle = get_object_or_404(Vehicle, pk=pk)

    purchase_price = float(vehicle.purchase_price)
    repair_expenditure = float(vehicle.repair_expenditure)
    age = vehicle.age_years
    current_year = date.today().year

    # ── 1. Health Score ────────────────────────────────────────────
    health_result = calculate_health_score(
        vehicle_age=age,
        current_mileage=vehicle.current_mileage,
        annual_km_driven=vehicle.annual_km_driven,
        purchase_price=purchase_price,
        repair_expenditure=repair_expenditure,
        service_records_count=vehicle.service_records_count,
        months_since_last_service=vehicle.months_since_last_service,
    )

    # ── 2. Depreciation Curve ──────────────────────────────────────
    dep_result = declining_balance_depreciation(
        purchase_price=purchase_price,
        vehicle_age=age,
        fuel_type=vehicle.fuel_type,
        n_years=15,
    )

    # Full depreciation trajectory from Year 0 (purchase) into future years for Plotly chart
    full_curve = declining_balance_depreciation(
        purchase_price=purchase_price,
        vehicle_age=0,
        fuel_type=vehicle.fuel_type,
        n_years=max(15, age + 8),
    )
    start_year = vehicle.manufacturing_year
    dep_chart_data = {
        'years': [start_year + y for y in full_curve['years']],
        'values': full_curve['values'],
        'current_year': current_year,
    }

    # ── 3. Exchange Window ─────────────────────────────────────────
    exchange_window = estimate_exchange_window(
        purchase_price=purchase_price,
        vehicle_age=age,
        annual_km=vehicle.annual_km_driven,
        repair_expenditure=repair_expenditure,
        fuel_type=vehicle.fuel_type,
    )

    # ── 4. Maintenance Risk ────────────────────────────────────────
    maintenance_result = assess_maintenance_risk(
        vehicle_age=age,
        current_mileage=vehicle.current_mileage,
        months_since_last_service=vehicle.months_since_last_service,
        service_records_count=vehicle.service_records_count,
        repair_expenditure=repair_expenditure,
        purchase_price=purchase_price,
        fuel_type=vehicle.fuel_type,
        transmission=vehicle.transmission,
    )

    # ── 5. Lifecycle Decision ──────────────────────────────────────
    # dep_result['total_depreciation_pct'] = percentage of value LOST.
    # Decision engine expects residual_value_pct = percentage REMAINING.
    residual_pct = max(0.0, 100.0 - dep_result.get('total_depreciation_pct', 0))

    decision_result = make_decision(
        health_score=health_result.total_score,
        vehicle_age=age,
        residual_value_pct=residual_pct,
        maintenance_risk_level=maintenance_result.risk_level,
        annual_maintenance_cost=maintenance_result.estimated_annual_cost,
        purchase_price=purchase_price,
        repair_expenditure=repair_expenditure,
    )

    # ── 6. Resale Predictor (optional — None when untrained) ───────
    resale_prediction = None
    try:
        import numpy as np
        resale_prediction = predict_resale_value({
            'vehicle_age': age,
            'km_driven': vehicle.current_mileage,
            'log_km_driven': float(np.log1p(vehicle.current_mileage)),
            'age_mileage_interaction': age * vehicle.current_mileage / 1000,
        })
    except Exception as exc:  # noqa: BLE001
        logger.warning("Resale prediction skipped for vehicle %s: %s", pk, exc)

    # ── Derived display values ─────────────────────────────────────
    recommendation = decision_result.decision
    rec_color = _DECISION_COLOUR.get(recommendation, 'monitor')
    rec_text_color = _DECISION_TEXT_COLOUR.get(recommendation, 'amber')
    rec_icon = _DECISION_ICON.get(recommendation, 'question-circle')

    context = {
        # Vehicle
        'vehicle': vehicle,

        # Health
        'health_score': health_result.total_score,
        'health_grade': health_result.grade,
        'health_components': health_result.components,
        'health_flags': health_result.flags,
        'health_summary': health_result.summary,

        # Depreciation
        'dep_result': dep_result,
        'dep_chart_data': json.dumps(dep_chart_data),
        'current_value': dep_result['current_value'],
        'residual_pct': round(residual_pct, 1),
        'total_depreciation_pct': dep_result.get('total_depreciation_pct', 0),
        'exchange_window': exchange_window,

        # Maintenance
        'maintenance_risk_level': maintenance_result.risk_level,
        'maintenance_risk_score': maintenance_result.risk_score,
        'maintenance_annual_cost': maintenance_result.estimated_annual_cost,
        'maintenance_actions': maintenance_result.recommended_actions,
        'maintenance_summary': maintenance_result.summary,

        # Decision
        'recommendation': recommendation,
        'rec_color': rec_color,
        'rec_text_color': rec_text_color,
        'rec_icon': rec_icon,
        'rec_desc': decision_result.summary,
        'decision_confidence': decision_result.confidence,
        'decision_score': decision_result.score,
        'decision_reasons': decision_result.reasons,
        'next_review_months': decision_result.next_review_months,

        # Resale (optional)
        'resale_prediction': resale_prediction,

        # Status flags
        'is_prototype': False,
        'resale_model_ready': resale_prediction is not None,
    }
    return render(request, 'analytics/vehicle_outlook.html', context)


def fleet_insights(request):
    """
    Fleet-level analytics across all registered vehicles.
    Runs health scoring, maintenance assessment and decision engine for each vehicle.
    """
    vehicles = Vehicle.objects.all()
    total = vehicles.count()

    avg_age = None
    avg_mileage = None
    avg_repair = None
    avg_health = None
    decision_counts = {'KEEP': 0, 'MONITOR': 0, 'SELL': 0, 'EXCHANGE': 0}
    fleet_rows = []

    if total > 0:
        total_age = sum(v.age_years for v in vehicles)
        total_mileage = sum(v.current_mileage for v in vehicles)
        total_repair = sum(float(v.repair_expenditure) for v in vehicles)
        avg_age = round(total_age / total, 1)
        avg_mileage = round(total_mileage / total)
        avg_repair = round(total_repair / total)

        health_scores = []
        for v in vehicles:
            purchase_price = float(v.purchase_price)
            repair_expenditure = float(v.repair_expenditure)
            age = v.age_years
            try:
                h = calculate_health_score(
                    vehicle_age=age,
                    current_mileage=v.current_mileage,
                    annual_km_driven=v.annual_km_driven,
                    purchase_price=purchase_price,
                    repair_expenditure=repair_expenditure,
                    service_records_count=v.service_records_count,
                    months_since_last_service=v.months_since_last_service,
                )
                dep = declining_balance_depreciation(
                    purchase_price=purchase_price,
                    vehicle_age=age,
                    fuel_type=v.fuel_type,
                    n_years=1,
                )
                maint = assess_maintenance_risk(
                    vehicle_age=age,
                    current_mileage=v.current_mileage,
                    months_since_last_service=v.months_since_last_service,
                    service_records_count=v.service_records_count,
                    repair_expenditure=repair_expenditure,
                    purchase_price=purchase_price,
                    fuel_type=v.fuel_type,
                    transmission=v.transmission,
                )
                residual_pct = max(0.0, 100.0 - dep.get('total_depreciation_pct', 0))
                dec = make_decision(
                    health_score=h.total_score,
                    vehicle_age=age,
                    residual_value_pct=residual_pct,
                    maintenance_risk_level=maint.risk_level,
                    annual_maintenance_cost=maint.estimated_annual_cost,
                    purchase_price=purchase_price,
                    repair_expenditure=repair_expenditure,
                )
                health_scores.append(h.total_score)
                decision_counts[dec.decision] = decision_counts.get(dec.decision, 0) + 1
                fleet_rows.append({
                    'vehicle': v,
                    'health_score': h.total_score,
                    'health_grade': h.grade,
                    'risk_level': maint.risk_level,
                    'annual_cost': maint.estimated_annual_cost,
                    'decision': dec.decision,
                    'decision_color': _DECISION_COLOUR.get(dec.decision, 'monitor'),
                    'decision_text_color': _DECISION_TEXT_COLOUR.get(dec.decision, 'amber'),
                    'current_value': dep['current_value'],
                })
            except Exception as exc:  # noqa: BLE001
                logger.warning("Fleet scoring failed for vehicle %s: %s", v.pk, exc)
                fleet_rows.append({
                    'vehicle': v,
                    'health_score': None,
                    'health_grade': '—',
                    'risk_level': '—',
                    'annual_cost': None,
                    'decision': '—',
                    'decision_color': 'monitor',
                    'decision_text_color': 'amber',
                    'current_value': None,
                })

        if health_scores:
            avg_health = round(sum(health_scores) / len(health_scores), 1)

    context = {
        'vehicles': vehicles,
        'fleet_rows': fleet_rows,
        'total': total,
        'avg_age': avg_age,
        'avg_mileage': avg_mileage,
        'avg_repair': avg_repair,
        'avg_health': avg_health,
        'decision_counts': decision_counts,
        'is_prototype': False,
    }
    return render(request, 'analytics/fleet_insights.html', context)
