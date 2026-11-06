"""
Vehicle admin registration.
"""
from django.contrib import admin
from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = [
        'display_name', 'brand', 'model', 'manufacturing_year',
        'fuel_type', 'transmission', 'current_mileage', 'created_at'
    ]
    list_filter = ['fuel_type', 'transmission', 'manufacturing_year']
    search_fields = ['brand', 'model']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Vehicle Identity', {
            'fields': ('brand', 'model', 'manufacturing_year')
        }),
        ('Financial', {
            'fields': ('purchase_price', 'repair_expenditure')
        }),
        ('Usage', {
            'fields': ('current_mileage', 'annual_km_driven', 'fuel_type', 'transmission')
        }),
        ('Maintenance', {
            'fields': ('service_records_count', 'months_since_last_service')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
