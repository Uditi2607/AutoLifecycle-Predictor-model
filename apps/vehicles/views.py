"""
Vehicle app views — registration, list, detail.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Vehicle
from .forms import VehicleRegistrationForm


def vehicle_register(request):
    """Register a new vehicle for lifecycle assessment."""
    if request.method == 'POST':
        form = VehicleRegistrationForm(request.POST)
        if form.is_valid():
            vehicle = form.save()
            messages.success(request, f'Vehicle "{vehicle}" registered successfully!')
            return redirect('vehicles:vehicle_detail', pk=vehicle.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = VehicleRegistrationForm()

    return render(request, 'vehicles/register.html', {'form': form})


def vehicle_list(request):
    """List all registered vehicles."""
    vehicles = Vehicle.objects.all().order_by('-created_at')
    return render(request, 'vehicles/list.html', {'vehicles': vehicles})


def vehicle_detail(request, pk):
    """Detail view for a single vehicle with basic analytics."""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    return render(request, 'vehicles/detail.html', {'vehicle': vehicle})


def vehicle_delete(request, pk):
    """Delete a vehicle record (POST only)."""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        name = str(vehicle)
        vehicle.delete()
        messages.success(request, f'Vehicle "{name}" removed.')
        return redirect('vehicles:vehicle_list')
    return render(request, 'vehicles/confirm_delete.html', {'vehicle': vehicle})
