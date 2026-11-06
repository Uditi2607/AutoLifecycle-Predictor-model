"""
Vehicle model — stores all vehicle data for lifecycle analysis.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Vehicle(models.Model):
    """Represents a vehicle registered for lifecycle assessment."""

    # Fuel type choices
    FUEL_PETROL = 'petrol'
    FUEL_DIESEL = 'diesel'
    FUEL_HYBRID = 'hybrid'
    FUEL_ELECTRIC = 'electric'
    FUEL_CNG = 'cng'
    FUEL_CHOICES = [
        (FUEL_PETROL, 'Petrol'),
        (FUEL_DIESEL, 'Diesel'),
        (FUEL_HYBRID, 'Hybrid'),
        (FUEL_ELECTRIC, 'Electric'),
        (FUEL_CNG, 'CNG'),
    ]

    # Transmission choices
    TRANS_MANUAL = 'manual'
    TRANS_AUTO = 'automatic'
    TRANS_CVT = 'cvt'
    TRANS_CHOICES = [
        (TRANS_MANUAL, 'Manual'),
        (TRANS_AUTO, 'Automatic'),
        (TRANS_CVT, 'CVT'),
    ]

    # --- Vehicle Identity ---
    brand = models.CharField(max_length=100, help_text="Vehicle manufacturer (e.g. Toyota)")
    model = models.CharField(max_length=100, help_text="Vehicle model name (e.g. Camry)")
    manufacturing_year = models.PositiveIntegerField(
        validators=[MinValueValidator(1980), MaxValueValidator(2030)],
        help_text="Year the vehicle was manufactured"
    )

    # --- Financial ---
    purchase_price = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Original purchase price (in your currency)"
    )

    # --- Usage ---
    current_mileage = models.PositiveIntegerField(
        help_text="Current odometer reading in kilometres"
    )
    annual_km_driven = models.PositiveIntegerField(
        help_text="Average kilometres driven per year"
    )

    # --- Specifications ---
    fuel_type = models.CharField(
        max_length=20, choices=FUEL_CHOICES, default=FUEL_PETROL
    )
    transmission = models.CharField(
        max_length=20, choices=TRANS_CHOICES, default=TRANS_MANUAL
    )

    # --- Maintenance & Health ---
    repair_expenditure = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
        help_text="Total money spent on repairs (lifetime, in your currency)"
    )
    service_records_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of documented service/maintenance records"
    )
    months_since_last_service = models.PositiveIntegerField(
        default=0,
        help_text="Number of months since the last recorded service"
    )

    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicles'

    def __str__(self):
        return f"{self.manufacturing_year} {self.brand} {self.model}"

    @property
    def age_years(self):
        """Current age of the vehicle in full years."""
        from datetime import date
        return date.today().year - self.manufacturing_year

    @property
    def display_name(self):
        return f"{self.brand} {self.model} ({self.manufacturing_year})"
