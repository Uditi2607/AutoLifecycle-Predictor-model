"""
AutoLifecycle Predictor — Test Suite

Tests:
  - Django project integrity check
  - Landing page loads (HTTP 200)
  - Dashboard loads
  - Vehicle registration (GET and POST)
  - Vehicle detail view
  - Analytics vehicle outlook view
  - Fleet insights view
  - Vehicle model creation and retrieval
"""
from django.test import TestCase, Client
from django.urls import reverse
from apps.vehicles.models import Vehicle


class ProjectIntegrityTest(TestCase):
    """Basic Django project integrity tests."""

    def test_django_check_passes(self):
        """Django system check should pass without errors."""
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        # If this raises SystemCheckError, the test fails
        call_command('check', stdout=out)
        self.assertIn('no issues', out.getvalue().lower() if out.getvalue() else '', msg="Django check reported issues")


class CorePageTests(TestCase):
    """Tests for core app pages."""

    def setUp(self):
        self.client = Client()

    def test_landing_page_loads(self):
        response = self.client.get(reverse('core:landing'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AutoLifecycle')

    def test_dashboard_loads(self):
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_how_it_works_loads(self):
        response = self.client.get(reverse('core:how_it_works'))
        self.assertEqual(response.status_code, 200)


class VehicleTests(TestCase):
    """Tests for vehicle registration and retrieval."""

    def setUp(self):
        self.client = Client()
        self.vehicle_data = {
            'brand': 'Toyota',
            'model': 'Camry',
            'manufacturing_year': 2019,
            'purchase_price': '1200000.00',
            'current_mileage': 65000,
            'annual_km_driven': 15000,
            'fuel_type': 'petrol',
            'transmission': 'automatic',
            'repair_expenditure': '45000.00',
            'service_records_count': 8,
            'months_since_last_service': 3,
        }

    def test_vehicle_register_get(self):
        """Registration form page should load."""
        response = self.client.get(reverse('vehicles:vehicle_register'))
        self.assertEqual(response.status_code, 200)

    def test_vehicle_register_post_valid(self):
        """Valid vehicle data should create a vehicle and redirect."""
        response = self.client.post(
            reverse('vehicles:vehicle_register'),
            self.vehicle_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Vehicle.objects.count(), 1)
        vehicle = Vehicle.objects.first()
        self.assertEqual(vehicle.brand, 'Toyota')
        self.assertEqual(vehicle.model, 'Camry')

    def test_vehicle_list_loads(self):
        """Vehicle list page should load."""
        response = self.client.get(reverse('vehicles:vehicle_list'))
        self.assertEqual(response.status_code, 200)

    def test_vehicle_model_creation(self):
        """Vehicle model should be creatable via ORM."""
        v = Vehicle.objects.create(
            brand='Honda',
            model='City',
            manufacturing_year=2020,
            purchase_price=900000,
            current_mileage=40000,
            annual_km_driven=12000,
            fuel_type='petrol',
            transmission='manual',
            repair_expenditure=15000,
            service_records_count=4,
            months_since_last_service=2,
        )
        self.assertEqual(str(v), '2020 Honda City')
        self.assertEqual(v.age_years, __import__('datetime').date.today().year - 2020)

    def test_vehicle_detail_loads(self):
        """Vehicle detail page should load for an existing vehicle."""
        v = Vehicle.objects.create(
            brand='Maruti', model='Swift', manufacturing_year=2018,
            purchase_price=600000, current_mileage=55000, annual_km_driven=12000,
            fuel_type='petrol', transmission='manual',
            repair_expenditure=20000, service_records_count=6,
            months_since_last_service=4,
        )
        response = self.client.get(reverse('vehicles:vehicle_detail', args=[v.pk]))
        self.assertEqual(response.status_code, 200)

    def test_vehicle_404_for_invalid_id(self):
        """Vehicle detail should return 404 for non-existent vehicle."""
        response = self.client.get(reverse('vehicles:vehicle_detail', args=[99999]))
        self.assertEqual(response.status_code, 404)


class AnalyticsTests(TestCase):
    """Tests for analytics views."""

    def setUp(self):
        self.client = Client()
        self.vehicle = Vehicle.objects.create(
            brand='Hyundai', model='i20', manufacturing_year=2017,
            purchase_price=700000, current_mileage=85000, annual_km_driven=15000,
            fuel_type='diesel', transmission='manual',
            repair_expenditure=35000, service_records_count=7,
            months_since_last_service=5,
        )

    def test_vehicle_outlook_loads(self):
        """Vehicle outlook analytics page should load."""
        response = self.client.get(
            reverse('analytics:vehicle_outlook', args=[self.vehicle.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_fleet_insights_loads(self):
        """Fleet insights page should load."""
        response = self.client.get(reverse('analytics:fleet_insights'))
        self.assertEqual(response.status_code, 200)


class MLModuleTests(TestCase):
    """Tests for ML engine modules (rule-based, no trained models required)."""

    def test_health_score_calculation(self):
        """Health score should return a valid 0–100 value."""
        from ml_engine.health_score import calculate_health_score
        result = calculate_health_score(
            vehicle_age=5, current_mileage=60000, annual_km_driven=12000,
            purchase_price=800000, repair_expenditure=30000,
            service_records_count=5, months_since_last_service=4
        )
        self.assertGreaterEqual(result.total_score, 0)
        self.assertLessEqual(result.total_score, 100)
        self.assertIsInstance(result.grade, str)

    def test_depreciation_forecast(self):
        """Depreciation should produce descending values."""
        from ml_engine.depreciation import declining_balance_depreciation
        result = declining_balance_depreciation(
            purchase_price=1000000, vehicle_age=3, fuel_type='petrol', n_years=5
        )
        values = result['values']
        # Values should be descending (each year worth less)
        for i in range(len(values) - 1):
            self.assertGreaterEqual(values[i], values[i + 1])

    def test_maintenance_risk_assessment(self):
        """Maintenance risk should return a valid risk level."""
        from ml_engine.maintenance import assess_maintenance_risk
        result = assess_maintenance_risk(
            vehicle_age=8, current_mileage=100000, months_since_last_service=14,
            service_records_count=5, repair_expenditure=80000,
            purchase_price=600000
        )
        self.assertIn(result.risk_level, ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
        self.assertGreater(result.estimated_annual_cost, 0)

    def test_decision_engine(self):
        """Decision engine should return valid recommendation."""
        from ml_engine.decision_engine import make_decision
        result = make_decision(
            health_score=75, vehicle_age=4, residual_value_pct=55,
            maintenance_risk_level='LOW', annual_maintenance_cost=9000,
            purchase_price=1000000, repair_expenditure=40000
        )
        self.assertIn(result.decision, ['KEEP', 'MONITOR', 'SELL', 'EXCHANGE'])
        self.assertIsInstance(result.reasons, list)
        self.assertGreater(len(result.reasons), 0)

    def test_resale_model_unavailable_returns_none(self):
        """Resale predictor should gracefully return None when untrained."""
        from ml_engine.resale_predictor import predict_resale_value
        result = predict_resale_value({'vehicle_age': 5, 'km_driven': 60000})
        self.assertIsNone(result)
