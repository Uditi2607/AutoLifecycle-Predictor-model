"""
Core app views — Landing page, Dashboard, How It Works.
"""
from django.shortcuts import render
from apps.vehicles.models import Vehicle


def landing(request):
    """Landing/home page introducing AutoLifecycle Predictor."""
    return render(request, 'core/landing.html')


def dashboard(request):
    """Main dashboard with vehicle overview and summary stats."""
    vehicles = Vehicle.objects.all().order_by('-created_at')[:6]
    total_vehicles = Vehicle.objects.count()

    context = {
        'vehicles': vehicles,
        'total_vehicles': total_vehicles,
        # Demonstration data — replace with real ML output once models are trained
        'demo_data': True,
    }
    return render(request, 'core/dashboard.html', context)


def how_it_works(request):
    """Explains the AutoLifecycle methodology and ML pipeline."""
    return render(request, 'core/how_it_works.html')
