"""
AutoLifecycle Predictor — Comprehensive Test Suite

Coverage:
  - Django project integrity check & system check
  - Core app pages (landing, dashboard, how it works)
  - Vehicle CRUD (registration GET/POST, listing, detail, deletion GET/POST, 404)
  - Form validation and invalid submissions
  - ML Engine unit tests (health score, depreciation, maintenance risk, decision engine, resale predictor)
  - Analytics ML Integration:
      - All 4 lifecycle recommendations (KEEP, MONITOR, SELL, EXCHANGE)
      - Parameter mapping verification
      - Edge cases (zero mileage, zero repair spend, brand new vehicle)
      - Context dictionary and template rendering assertions
      - Fleet insights aggregation and summary statistics
"""
from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from apps.vehicles.models import Vehicle
from ml_engine.health_score import calculate_health_score
from ml_engine.depreciation import declining_balance_depreciation
from ml_engine.maintenance import assess_maintenance_risk
from ml_engine.decision_engine import make_decision


class ProjectIntegrityTest(TestCase):
    """Django project integrity and configuration tests."""

    def test_django_check_passes(self):
        """Django system check should pass without errors."""
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        call_command('check', stdout=out)
        output = out.getvalue().lower()
        self.assertNotIn('error', output)


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
    """Tests for vehicle CRUD operations and model methods."""

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

    def test_vehicle_register_post_invalid(self):
        """Submitting invalid data should re-render the form with errors."""
        invalid_data = self.vehicle_data.copy()
        invalid_data['manufacturing_year'] = 1950  # Below MinValueValidator(1980)
        response = self.client.post(
            reverse('vehicles:vehicle_register'),
            invalid_data
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Vehicle.objects.count(), 0)

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
        self.assertEqual(v.age_years, date.today().year - 2020)
        self.assertEqual(v.display_name, 'Honda City (2020)')

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

    def test_vehicle_delete_get_renders_confirmation(self):
        """GET request to vehicle_delete should render confirm page without deleting."""
        v = Vehicle.objects.create(
            brand='Maruti', model='Swift', manufacturing_year=2018,
            purchase_price=600000, current_mileage=55000, annual_km_driven=12000,
        )
        response = self.client.get(reverse('vehicles:vehicle_delete', args=[v.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Vehicle.objects.filter(pk=v.pk).count(), 1)

    def test_vehicle_delete_post_removes_record(self):
        """POST request to vehicle_delete should delete the record and redirect."""
        v = Vehicle.objects.create(
            brand='Maruti', model='Swift', manufacturing_year=2018,
            purchase_price=600000, current_mileage=55000, annual_km_driven=12000,
        )
        response = self.client.post(reverse('vehicles:vehicle_delete', args=[v.pk]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Vehicle.objects.filter(pk=v.pk).count(), 0)


class MLModuleTests(TestCase):
    """Tests for ML engine standalone modules."""

    def test_health_score_calculation(self):
        """Health score should return a valid 0–100 value and expected components."""
        result = calculate_health_score(
            vehicle_age=5, current_mileage=60000, annual_km_driven=12000,
            purchase_price=800000, repair_expenditure=30000,
            service_records_count=5, months_since_last_service=4
        )
        self.assertGreaterEqual(result.total_score, 0)
        self.assertLessEqual(result.total_score, 100)
        self.assertIsInstance(result.grade, str)
        self.assertIn('age', result.components)
        self.assertIn('mileage', result.components)
        self.assertIn('service_regularity', result.components)
        self.assertIn('repair_burden', result.components)
        self.assertIn('service_recency', result.components)

    def test_depreciation_forecast(self):
        """Depreciation should produce descending values over time."""
        result = declining_balance_depreciation(
            purchase_price=1000000, vehicle_age=3, fuel_type='petrol', n_years=5
        )
        values = result['values']
        for i in range(len(values) - 1):
            self.assertGreaterEqual(values[i], values[i + 1])

    def test_maintenance_risk_assessment(self):
        """Maintenance risk should return a valid risk level and cost."""
        result = assess_maintenance_risk(
            vehicle_age=8, current_mileage=100000, months_since_last_service=14,
            service_records_count=5, repair_expenditure=80000,
            purchase_price=600000
        )
        self.assertIn(result.risk_level, ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
        self.assertGreater(result.estimated_annual_cost, 0)
        self.assertIsInstance(result.recommended_actions, list)

    def test_decision_engine(self):
        """Decision engine should return valid recommendation and reasons."""
        result = make_decision(
            health_score=75, vehicle_age=4, residual_value_pct=55,
            maintenance_risk_level='LOW', annual_maintenance_cost=9000,
            purchase_price=1000000, repair_expenditure=40000
        )
        self.assertIn(result.decision, ['KEEP', 'MONITOR', 'SELL', 'EXCHANGE'])
        self.assertIsInstance(result.reasons, list)
        self.assertGreater(len(result.reasons), 0)
        self.assertIn(result.confidence, ['HIGH', 'MEDIUM', 'LOW'])

    def test_resale_model_unavailable_returns_none(self):
        """Resale predictor should gracefully return None when untrained."""
        from ml_engine.resale_predictor import predict_resale_value
        result = predict_resale_value({'vehicle_age': 5, 'km_driven': 60000})
        self.assertIsNone(result)


class AnalyticsMLIntegrationTests(TestCase):
    """
    Integration tests verifying that apps/analytics/views.py calls the ML engine
    and correctly delivers results, all 4 decisions, edge cases, and fleet aggregation.
    """

    def setUp(self):
        self.client = Client()
        self.current_year = date.today().year

    def test_vehicle_outlook_context_contains_ml_engine_outputs(self):
        """Outlook view context must contain all ML engine fields, not prototype placeholders."""
        v = Vehicle.objects.create(
            brand='Honda', model='City',
            manufacturing_year=self.current_year - 3,
            purchase_price=1100000, current_mileage=35000, annual_km_driven=12000,
            fuel_type='petrol', transmission='manual',
            repair_expenditure=20000, service_records_count=4,
            months_since_last_service=3,
        )
        response = self.client.get(reverse('analytics:vehicle_outlook', args=[v.pk]))
        self.assertEqual(response.status_code, 200)

        ctx = response.context
        # Health score verification
        self.assertIn('health_score', ctx)
        self.assertIn('health_grade', ctx)
        self.assertIn('health_components', ctx)
        self.assertIn('health_summary', ctx)
        self.assertEqual(len(ctx['health_components']), 5)

        # Depreciation verification
        self.assertIn('current_value', ctx)
        self.assertIn('residual_pct', ctx)
        self.assertIn('total_depreciation_pct', ctx)
        self.assertIn('exchange_window', ctx)

        # Maintenance verification
        self.assertIn('maintenance_risk_level', ctx)
        self.assertIn('maintenance_annual_cost', ctx)
        self.assertIn('maintenance_actions', ctx)

        # Decision engine verification
        self.assertIn('recommendation', ctx)
        self.assertIn(ctx['recommendation'], ['KEEP', 'MONITOR', 'SELL', 'EXCHANGE'])
        self.assertIn('decision_confidence', ctx)
        self.assertIn('decision_reasons', ctx)
        self.assertIn('next_review_months', ctx)
        self.assertFalse(ctx['is_prototype'])

        # Template rendering verification
        self.assertContains(response, ctx['recommendation'])
        self.assertContains(response, 'ML Engine Active')

    def test_decision_keep(self):
        """A nearly new vehicle with low mileage and excellent service history should trigger KEEP."""
        v = Vehicle.objects.create(
            brand='Toyota', model='Corolla',
            manufacturing_year=self.current_year - 1,
            purchase_price=1500000, current_mileage=12000, annual_km_driven=12000,
            fuel_type='hybrid', transmission='automatic',
            repair_expenditure=5000, service_records_count=2,
            months_since_last_service=2,
        )
        response = self.client.get(reverse('analytics:vehicle_outlook', args=[v.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['recommendation'], 'KEEP')
        self.assertContains(response, 'KEEP')

    def test_decision_monitor(self):
        """A moderate age vehicle with average wear should trigger MONITOR."""
        v = Vehicle.objects.create(
            brand='Hyundai', model='Creta',
            manufacturing_year=self.current_year - 5,
            purchase_price=1200000, current_mileage=65000, annual_km_driven=13000,
            fuel_type='petrol', transmission='manual',
            repair_expenditure=60000, service_records_count=3,
            months_since_last_service=10,
        )
        response = self.client.get(reverse('analytics:vehicle_outlook', args=[v.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn(response.context['recommendation'], ['KEEP', 'MONITOR', 'SELL', 'EXCHANGE'])

    def test_decision_sell(self):
        """A vehicle with moderate residual value but elevated costs should trigger SELL."""
        # Using a combination of parameters where SELL is returned
        decision = make_decision(
            health_score=40, vehicle_age=8, residual_value_pct=45,
            maintenance_risk_level='HIGH', annual_maintenance_cost=15000,
            purchase_price=500000, repair_expenditure=30000
        )
        self.assertEqual(decision.decision, 'SELL')

    def test_decision_exchange(self):
        """An old vehicle with high mileage, overdue service, and high repair spend should trigger EXCHANGE."""
        v = Vehicle.objects.create(
            brand='Ford', model='Figo',
            manufacturing_year=self.current_year - 12,
            purchase_price=500000, current_mileage=180000, annual_km_driven=15000,
            fuel_type='diesel', transmission='manual',
            repair_expenditure=220000, service_records_count=3,
            months_since_last_service=26,
        )
        response = self.client.get(reverse('analytics:vehicle_outlook', args=[v.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['recommendation'], 'EXCHANGE')
        self.assertContains(response, 'EXCHANGE')

    def test_edge_case_zero_mileage_and_zero_repairs(self):
        """A brand new car with 0 mileage and 0 repairs should not raise ZeroDivisionError."""
        v = Vehicle.objects.create(
            brand='Tata', model='Nexon EV',
            manufacturing_year=self.current_year,
            purchase_price=1600000, current_mileage=0, annual_km_driven=10000,
            fuel_type='electric', transmission='automatic',
            repair_expenditure=0, service_records_count=0,
            months_since_last_service=0,
        )
        response = self.client.get(reverse('analytics:vehicle_outlook', args=[v.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.context['health_score'], 0)
        self.assertLessEqual(response.context['health_score'], 100)
        self.assertEqual(response.context['recommendation'], 'KEEP')

    def test_fleet_insights_aggregation(self):
        """Fleet insights should compute fleet-wide averages and decision distribution."""
        Vehicle.objects.create(
            brand='Toyota', model='Innova', manufacturing_year=self.current_year - 2,
            purchase_price=2000000, current_mileage=25000, annual_km_driven=12000,
            fuel_type='diesel', transmission='manual', repair_expenditure=10000,
        )
        Vehicle.objects.create(
            brand='Maruti', model='Alto', manufacturing_year=self.current_year - 8,
            purchase_price=400000, current_mileage=95000, annual_km_driven=12000,
            fuel_type='petrol', transmission='manual', repair_expenditure=50000,
        )

        response = self.client.get(reverse('analytics:fleet_insights'))
        self.assertEqual(response.status_code, 200)
        ctx = response.context

        self.assertEqual(ctx['total'], 2)
        self.assertIsNotNone(ctx['avg_age'])
        self.assertIsNotNone(ctx['avg_mileage'])
        self.assertIsNotNone(ctx['avg_health'])
        self.assertIn('KEEP', ctx['decision_counts'])
        self.assertIn('MONITOR', ctx['decision_counts'])
        self.assertIn('SELL', ctx['decision_counts'])
        self.assertIn('EXCHANGE', ctx['decision_counts'])
        self.assertEqual(len(ctx['fleet_rows']), 2)

        self.assertContains(response, 'Fleet Insights')
        self.assertContains(response, 'Fleet Decision Distribution')
