"""
Analytics app views — Vehicle Outlook and Fleet Insights.
"""
from django.shortcuts import render, get_object_or_404
from apps.vehicles.models import Vehicle
import json


def vehicle_outlook(request, pk):
    """
    Detailed analytics view for a single vehicle.
    Shows estimated health, depreciation curve and recommendation.
    NOTE: Until ML models are trained on real data, all scores shown here
    are rule-based estimates clearly labelled as such.
    """
    vehicle = get_object_or_404(Vehicle, pk=pk)

    # Rule-based estimates (prototype — replace with trained ML models)
    age = vehicle.age_years
    mileage = vehicle.current_mileage

    # Simple health score prototype (0–100)
    # Deduct points for age, high mileage, overdue service, high repairs
    health_score = max(0, min(100,
        100
        - (age * 3)
        - (mileage / 5000)
        - (vehicle.months_since_last_service * 1.5)
        - (float(vehicle.repair_expenditure) / 50000 * 5)
    ))

    # Depreciation curve data (simplified straight-line + curve)
    start_year = vehicle.manufacturing_year
    current_year = __import__('datetime').date.today().year
    years = list(range(0, 15))
    purchase_price = float(vehicle.purchase_price)
    # Approximate depreciation: 15% year 1, 10% subsequent years
    dep_values = []
    val = purchase_price
    for i, yr in enumerate(years):
        dep_values.append(round(val, 2))
        rate = 0.15 if i == 0 else 0.10
        val = val * (1 - rate)

    dep_chart_data = {
        'years': [start_year + y for y in years],
        'values': dep_values,
        'current_year': current_year,
    }

    # Recommendation logic (rule-based prototype)
    if health_score >= 70 and age <= 5:
        recommendation = 'KEEP'
        rec_color = 'emerald'
        rec_desc = 'Your vehicle is in good health. Continue regular maintenance.'
    elif health_score >= 45 or age <= 8:
        recommendation = 'MONITOR'
        rec_color = 'amber'
        rec_desc = 'Monitor closely. Watch for increasing repair costs.'
    else:
        recommendation = 'EXCHANGE'
        rec_color = 'red'
        rec_desc = 'Consider exchanging or selling. Depreciation and costs are significant.'

    context = {
        'vehicle': vehicle,
        'health_score': round(health_score, 1),
        'recommendation': recommendation,
        'rec_color': rec_color,
        'rec_desc': rec_desc,
        'dep_chart_data': json.dumps(dep_chart_data),
        'is_prototype': True,  # Flag: ML not yet trained
    }
    return render(request, 'analytics/vehicle_outlook.html', context)


def fleet_insights(request):
    """
    Fleet-level analytics across all registered vehicles.
    """
    vehicles = Vehicle.objects.all()
    total = vehicles.count()

    context = {
        'vehicles': vehicles,
        'total': total,
        'is_prototype': True,
    }
    return render(request, 'analytics/fleet_insights.html', context)
