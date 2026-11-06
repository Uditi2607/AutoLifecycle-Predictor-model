"""
Vehicle registration and management forms.
"""
from django import forms
from .models import Vehicle


class VehicleRegistrationForm(forms.ModelForm):
    """Form for registering a new vehicle for lifecycle assessment."""

    class Meta:
        model = Vehicle
        fields = [
            'brand', 'model', 'manufacturing_year', 'purchase_price',
            'current_mileage', 'annual_km_driven', 'fuel_type', 'transmission',
            'repair_expenditure', 'service_records_count', 'months_since_last_service',
        ]
        widgets = {
            'brand': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. Toyota'
            }),
            'model': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. Camry'
            }),
            'manufacturing_year': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. 2019', 'min': 1980, 'max': 2030
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. 1200000', 'step': '0.01'
            }),
            'current_mileage': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. 65000'
            }),
            'annual_km_driven': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. 15000'
            }),
            'fuel_type': forms.Select(attrs={'class': 'form-select'}),
            'transmission': forms.Select(attrs={'class': 'form-select'}),
            'repair_expenditure': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. 45000', 'step': '0.01'
            }),
            'service_records_count': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. 8'
            }),
            'months_since_last_service': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. 3'
            }),
        }
        labels = {
            'brand': 'Vehicle Brand',
            'model': 'Vehicle Model',
            'manufacturing_year': 'Manufacturing Year',
            'purchase_price': 'Purchase Price (₹)',
            'current_mileage': 'Current Mileage (km)',
            'annual_km_driven': 'Annual Distance Driven (km)',
            'fuel_type': 'Fuel Type',
            'transmission': 'Transmission Type',
            'repair_expenditure': 'Total Repair Expenditure (₹)',
            'service_records_count': 'Number of Service Records',
            'months_since_last_service': 'Months Since Last Service',
        }
        help_texts = {
            'purchase_price': 'Original price paid when buying the vehicle.',
            'repair_expenditure': 'Total spent on all repairs since purchase.',
            'months_since_last_service': '0 means serviced this month.',
        }
