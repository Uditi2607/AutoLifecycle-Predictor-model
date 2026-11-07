# AutoLifecycle Predictor — Project Audit Report

**Generated:** 2026-11-07  
**Repository:** [AutoLifecycle-Predictor](https://github.com/Uditi2607/AutoLifecycle-Predictor) (private)  
**Audit Scope:** Full codebase — architecture, ML engine, Django application, security, testing

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Project Architecture Overview](#2-project-architecture-overview)
3. [Module-by-Module Audit](#3-module-by-module-audit)
   - 3.1 [Django Application Layer](#31-django-application-layer)
   - 3.2 [ML Engine — Rule-Based Modules](#32-ml-engine--rule-based-modules)
   - 3.3 [ML Engine — Training Pipeline](#33-ml-engine--training-pipeline)
4. [Data Model Audit](#4-data-model-audit)
5. [Security Audit](#5-security-audit)
6. [Test Suite Audit](#6-test-suite-audit)
7. [Configuration & Dependencies](#7-configuration--dependencies)
8. [Known Gaps & Limitations](#8-known-gaps--limitations)
9. [Recommendations & Priority Action Plan](#9-recommendations--priority-action-plan)
10. [ML Module Status Summary](#10-ml-module-status-summary)

---

## 1. Executive Summary

**AutoLifecycle Predictor** is a Django-based web application that helps vehicle owners decide whether to **KEEP**, **MONITOR**, **SELL**, or **EXCHANGE** their vehicle by running it through a 7-signal ML pipeline.

| Dimension | Status |
|-----------|--------|
| Django project structure | ✅ Well-organised |
| Rule-based ML modules | ✅ Functional & documented |
| ML model training | ⏳ Awaiting training dataset |
| Analytics views | ⚠️ Uses simplified prototype logic (not the ML engine) |
| Security posture | ⚠️ Dev-safe; not production-ready |
| Test coverage | ✅ Good breadth; some gaps noted |
| Documentation | ✅ README and inline docstrings are thorough |

**Overall Assessment:** The project has a **solid, well-structured foundation**. The rule-based modules are production-quality. The main gap is that `analytics/views.py` uses an inline prototype health/depreciation formula instead of calling the dedicated `ml_engine` modules — this should be the top priority fix before go-live.

---

## 2. Project Architecture Overview

```
AutoLifecycle-Predictor/
├── config/              # Django settings, URL root, ASGI/WSGI
├── apps/
│   ├── core/            # Landing, Dashboard, How It Works
│   ├── vehicles/        # Vehicle model, CRUD, registration form
│   └── analytics/       # Vehicle Outlook, Fleet Insights views
├── ml_engine/
│   ├── preprocessing.py    ← Feature engineering pipeline
│   ├── train_resale.py     ← GradientBoosting training script
│   ├── resale_predictor.py ← Inference wrapper (graceful fallback)
│   ├── depreciation.py     ← Declining-balance depreciation
│   ├── health_score.py     ← Weighted composite health scorer
│   ├── maintenance.py      ← Risk & cost estimator
│   ├── decision_engine.py  ← KEEP/MONITOR/SELL/EXCHANGE logic
│   └── evaluation.py       ← Model evaluation utilities
├── templates/           # Django HTML templates
├── static/              # CSS, JS
├── tests/               # Unified test suite
├── artifacts/           # Trained model files (gitignored)
└── manage.py
```

### Architecture Flow

```
User Input (Vehicle Form)
        │
        ▼
   Vehicle Model (ORM)
        │
        ▼
   analytics/views.py ──────────────────────────────────────────┐
        │                                                        │
        ▼ (should call)                                         ▼ (currently uses)
   ML Engine Modules                                   Inline Prototype Logic
   ├── health_score.py          ◄── ⚠️ Not wired yet        (simplified formulas)
   ├── depreciation.py          ◄── ⚠️ Not wired yet
   ├── maintenance.py           ◄── ⚠️ Not wired yet
   └── decision_engine.py       ◄── ⚠️ Not wired yet
        │
        ▼
   LifecycleDecision (KEEP / MONITOR / SELL / EXCHANGE)
        │
        ▼
   vehicle_outlook.html
```

---

## 3. Module-by-Module Audit

### 3.1 Django Application Layer

#### `apps/vehicles/models.py` — Vehicle Model

| Aspect | Assessment |
|--------|-----------|
| Field coverage | ✅ Covers identity, financial, usage, specs, maintenance |
| Validators | ✅ `MinValueValidator`, `MaxValueValidator` on numeric fields |
| Choices | ✅ Proper `FUEL_CHOICES` and `TRANS_CHOICES` constants |
| Computed properties | ✅ `age_years` and `display_name` as `@property` |
| Meta ordering | ✅ `-created_at` |
| Timestamps | ✅ `auto_now_add` / `auto_now` |

**Findings:**
- `age_years` recalculates on each call using `date.today().year`. This is correct but will be incorrect for vehicles manufactured late in the year (e.g., a December 2023 vehicle shows as 3 years old in January 2026). Consider storing `manufacture_date` (DateField) for precision.
- `purchase_price` and `repair_expenditure` use `DecimalField` — correct for financial data.
- No `owner` or `user` FK — vehicles are not tied to any user account. This is intentional for the prototype but limits multi-user deployments.

---

#### `apps/vehicles/views.py` — Vehicle CRUD

| Endpoint | Status |
|----------|--------|
| `vehicle_register` (GET/POST) | ✅ Form validation, success/error messages, redirect |
| `vehicle_list` | ✅ Ordered queryset |
| `vehicle_detail` | ✅ 404 handling |
| `vehicle_delete` | ✅ POST-only delete with confirmation |

**Findings:**
- No authentication/authorisation on any view. Any user can register, view, or delete any vehicle.
- `vehicle_delete` correctly guards against accidental GET-triggered deletion.

---

#### `apps/analytics/views.py` — Analytics Views ⚠️

> **WARNING:** This is the **most critical gap** in the codebase. `vehicle_outlook` implements its own inline health score and depreciation formula rather than calling the dedicated `ml_engine` modules. This means:
> - The dedicated `health_score.py` (5-component weighted scorer) is **never called**.
> - The dedicated `depreciation.py` (declining-balance with fuel-type-aware rates) is **never called**.
> - The dedicated `decision_engine.py` (7-signal decision logic) is **never called**.
> - The recommendation only produces `KEEP`, `MONITOR`, or `EXCHANGE` — the **`SELL` decision is missing** from the view.

**Current inline health formula (prototype):**
```python
health_score = max(0, min(100,
    100
    - (age * 3)
    - (mileage / 5000)
    - (vehicle.months_since_last_service * 1.5)
    - (float(vehicle.repair_expenditure) / 50000 * 5)
))
```

**What it should call:**
```python
from ml_engine.health_score import calculate_health_score
from ml_engine.depreciation import declining_balance_depreciation
from ml_engine.maintenance import assess_maintenance_risk
from ml_engine.decision_engine import make_decision
```

**`fleet_insights` view** passes all vehicles to the template but performs no aggregation. There is no fleet-level scoring, distribution charts, or summary statistics in the view — the template carries all the responsibility (not audited here).

---

### 3.2 ML Engine — Rule-Based Modules

#### `ml_engine/health_score.py` ✅

**Score components and weights:**

| Component | Weight | Scoring Logic |
|-----------|--------|---------------|
| Age | 20% | 100 − (age × 5), capped at 0 |
| Mileage | 25% | Based on ratio vs. expected mileage |
| Service regularity | 20% | Ratio of actual vs. expected annual services |
| Repair burden | 20% | 100 − (repair_ratio × 200) |
| Service recency | 15% | 4-tier bracket (≤6, ≤12, ≤18, ≤24 months) |

**Grade thresholds:** A (≥80), B (≥65), C (≥50), D (≥35), F (<35)

**Findings:**
- Weight sum = 1.0 ✅
- Output is clamped `[0, 100]` ✅
- Flags are actionable and emoji-labelled for UI use ✅
- **Issue:** `service_score = min(100, service_ratio * 80)` — maximum possible service score is **80** (not 100), even for perfect service history. Consider using `min(100, service_ratio * 100)` or documenting this intentional cap.

---

#### `ml_engine/depreciation.py` ✅

**Declining-balance rates:**

| Year bracket | Petrol/Diesel | Electric |
|-------------|---------------|----------|
| Year 0 (first year) | 18% | 16% |
| Years 1–4 | 10% | 8% |
| Years 5–8 | 7% | 7% |
| Years 9+ | 5% | 5% |

**Findings:**
- `estimate_exchange_window()` applies 4 trigger rules (residual <40%, age ≥7, repair >25%, high mileage + age ≥5) ✅
- Exchange urgency correctly escalates from LOW → MEDIUM → HIGH based on trigger count ✅
- **Issue:** CNG, Hybrid, and Diesel do not have differentiated depreciation rates. Indian market depreciation for Diesel vs. Petrol is notably different post-BS6.
- **Issue:** `electric_discount` applies only to years 0–4, not to years 5–8 or 9+ brackets — minor inconsistency.

---

#### `ml_engine/maintenance.py` ✅

**Risk factors and point allocation:**

| Trigger | Points |
|---------|--------|
| Service >24 months overdue | 35 |
| Service >12 months overdue | 20 |
| Service >6 months overdue | 8 |
| Mileage >150,000 km | 20 |
| Mileage >80,000 km | 10 |
| Age >10 years | 15 |
| Age >7 years | 8 |
| Service history <50% of expected | 15 |
| Repair ratio >40% | 20 |
| Repair ratio >20% | 10 |
| Auto transmission + age >8 | 5 |

**Risk level thresholds:** CRITICAL (≥65), HIGH (≥45), MEDIUM (≥25), LOW (<25)

**Findings:**
- Maximum possible raw points = 128 → clamped to 100 ✅
- Base annual service costs are hard-coded per fuel type (₹5,000–₹10,000 range) — appropriate for the Indian market ✅
- **Issue:** Mileage trigger points are **not mutually exclusive** — a vehicle at 160,000 km accumulates both the >150k (20pts) and >80k (10pts) thresholds simultaneously (30 pts total). May overpenalise.
- **Issue:** `age > 7` branch adds 8 points silently with **no corresponding `actions.append()`** — penalty with no user-visible explanation.

---

#### `ml_engine/decision_engine.py` ✅

**Signal summary:**

| Signal | Positive triggers | Negative triggers |
|--------|------------------|------------------|
| Health score | ≥75 → +2, ≥55 → +1 | ≥35 → −1, <35 → −2 |
| Vehicle age | ≤3yr → +2, ≤6yr → +1 | ≤10yr → −1, >10yr → −2 |
| Residual value % | ≥60% → +2, ≥40% → +1 | ≥25% → −1, <25% → −2 |
| Maintenance risk | LOW → +2, MEDIUM → +1 | HIGH → −1, CRITICAL → −2 |
| Annual cost burden | <3% of price → +1 | ≥8% → −1 |
| Cumulative repair | ≤20% → +1 | ≥40% → −1 |
| Residual trend | ≥40% → +1 | <25% → −1 |

**Decision thresholds:** net ≥4 → KEEP | net ≥1 → MONITOR | net ≥−2 → SELL | net <−2 → EXCHANGE

**Findings:**
- Signal logic is well-documented and explainable ✅
- Returns `LifecycleDecision` dataclass with `reasons`, `confidence`, `next_review_months`, `summary` ✅
- **Missing integration:** This module is never called from `analytics/views.py` — a critical wiring gap.
- `next_review_months` values (3/6/12/18) are hard-coded constants, not configurable.

---

### 3.3 ML Engine — Training Pipeline

#### `ml_engine/preprocessing.py`

| Function | Status |
|----------|--------|
| `load_raw_data()` | ✅ FileNotFoundError with actionable message |
| `validate_columns()` | ✅ Raises ValueError listing missing columns |
| `clean_data()` | ✅ Drops duplicates, removes negatives, drops NA in key cols |
| `engineer_features()` | ✅ age, log_km, interaction term, price_per_km |
| `encode_categoricals()` | ✅ One-hot encoding with `drop_first=True` |
| `run_pipeline()` | ✅ End-to-end orchestrator |

**Findings:**
- `engineer_features()` hard-codes `current_year=2024` as default — should use `datetime.date.today().year`.
- `price_per_km` is computed but excluded from training features (target leakage concern) — acceptable but should be documented.

---

#### `ml_engine/train_resale.py`

| Aspect | Assessment |
|--------|-----------|
| Algorithm | GradientBoostingRegressor (n_estimators=200, lr=0.05, depth=4) |
| Target | log1p(selling_price) — correct for right-skewed prices |
| Split | 80/20, random_state=42 |
| Pipeline | StandardScaler → GBR |
| Artifact output | `resale_model.joblib`, `resale_features.joblib` |

**Findings:**
- Graceful guard: raises `FileNotFoundError` if processed data not found ✅
- **Issue:** `StandardScaler` before `GradientBoostingRegressor` is unnecessary — tree-based models are scale-invariant.
- **Issue:** No hyperparameter tuning or cross-validation — acceptable for first version.

---

## 4. Data Model Audit

### `Vehicle` model — field completeness

| Field | Type | Validated | Notes |
|-------|------|-----------|-------|
| `brand` | CharField(100) | ✅ | — |
| `model` | CharField(100) | ✅ | — |
| `manufacturing_year` | PositiveIntegerField | ✅ 1980–2030 | — |
| `purchase_price` | DecimalField(12,2) | ✅ ≥0 | — |
| `current_mileage` | PositiveIntegerField | ✅ | — |
| `annual_km_driven` | PositiveIntegerField | ✅ | — |
| `fuel_type` | CharField(20) | ✅ choices | — |
| `transmission` | CharField(20) | ✅ choices | — |
| `repair_expenditure` | DecimalField(12,2) | ✅ ≥0 | default=0 |
| `service_records_count` | PositiveIntegerField | ✅ | default=0 |
| `months_since_last_service` | PositiveIntegerField | ✅ | default=0 |
| `created_at` / `updated_at` | DateTimeField | auto | — |

**Suggested future fields:**
- `owner_count` — number of previous owners (key resale signal)
- `registration_number` — real-world identification
- `insurance_expiry` — lifecycle signal
- `variant` / `trim_level` — significant resale differentiator

---

## 5. Security Audit

> **CAUTION:** The following items **must** be resolved before any production deployment.

| Issue | Severity | Location | Recommendation |
|-------|----------|----------|---------------|
| Hard-coded fallback `SECRET_KEY` in settings | 🔴 Critical | `config/settings.py:12` | Enforce from env; raise `ImproperlyConfigured` if missing |
| `DEBUG=True` by default | 🔴 Critical | `config/settings.py:13` | Default to `False` |
| No authentication on any view | 🟠 High | All `apps/` views | Add `@login_required` or session-based auth |
| `ALLOWED_HOSTS` defaults to localhost | 🟡 Medium | `config/settings.py:14` | Must be locked for production |
| No HTTPS enforcement | 🟡 Medium | `config/settings.py` | Add `SECURE_SSL_REDIRECT`, HSTS headers |
| SQLite in production | 🟡 Medium | `config/settings.py:48` | Migrate to PostgreSQL |
| No rate limiting on registration | 🟢 Low | `apps/vehicles/views.py` | Add throttling to prevent abuse |

---

## 6. Test Suite Audit

**File:** `tests/test_all.py` — **17 tests across 5 test classes**

| Test Class | Tests | Coverage |
|------------|-------|---------|
| `ProjectIntegrityTest` | 1 | Django system check |
| `CorePageTests` | 3 | Landing, Dashboard, How It Works |
| `VehicleTests` | 6 | Register GET/POST, List, ORM creation, Detail 200/404 |
| `AnalyticsTests` | 2 | Vehicle Outlook, Fleet Insights |
| `MLModuleTests` | 5 | Health score, Depreciation, Maintenance, Decision engine, Resale (None case) |

### Gaps identified

| Missing Test | Priority |
|-------------|---------|
| `vehicle_delete` POST — verify count decrements | High |
| `vehicle_delete` GET — confirm page loads, no deletion | High |
| Invalid `manufacturing_year` form submission | Medium |
| Negative price/expenditure form rejection | Medium |
| `estimate_exchange_window()` function | Medium |
| Health score edge cases: age=0, mileage=0 | Medium |
| **Bug in `test_django_check_passes`** (see below) | High |

> **WARNING — Test Bug:** `test_django_check_passes` asserts `'no issues' in out.getvalue()`. When Django check passes cleanly, `out.getvalue()` is **empty** (`''`), making `'no issues' in ''` → `False` → test **fails** on a clean project.
>
> **Fix:**
> ```python
> output = out.getvalue().lower()
> self.assertNotIn('error', output)
> self.assertNotIn('warning', output)
> ```

---

## 7. Configuration & Dependencies

### `requirements.txt` — Dependency Audit

| Package | Assessment |
|---------|-----------|
| `Django>=5.0,<5.3` | ✅ Appropriate range |
| `pandas>=2.1.0` | ✅ Modern version |
| `numpy>=1.26.0` | ✅ Compatible |
| `scikit-learn>=1.3.0` | ✅ Required estimators present |
| `statsmodels>=0.14.0` | ⚠️ **Not used anywhere in codebase** |
| `joblib>=1.3.0` | ✅ Used for model serialisation |
| `plotly>=5.18.0` | ✅ Used in templates |
| `python-dotenv>=1.0.0` | ✅ Used in settings |
| `Pillow>=10.0.0` | ⚠️ **Not used anywhere in codebase** |

**Unused dependencies:** `statsmodels`, `Pillow` — consider removing.

---

## 8. Known Gaps & Limitations

| Gap | Impact |
|-----|--------|
| ML engine not wired into analytics views | Users see prototype results, not actual ML engine output |
| Resale predictor awaiting training data | No ML-based price prediction available |
| `fleet_insights` has no aggregation logic | Template must handle all fleet analysis |
| No user authentication | All vehicles visible/editable by anyone |
| `age_years` is year-precision only | Off-by-up-to-11-months for newer vehicles |
| `SELL` decision missing from view | Only 3 of 4 possible recommendations shown |

---

## 9. Recommendations & Priority Action Plan

### 🔴 Priority 1 — Wire ML Engine into Analytics Views

Replace `analytics/views.py` inline prototype with actual ML engine calls:

```python
from ml_engine.health_score import calculate_health_score
from ml_engine.depreciation import declining_balance_depreciation
from ml_engine.maintenance import assess_maintenance_risk
from ml_engine.decision_engine import make_decision

def vehicle_outlook(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)

    health = calculate_health_score(
        vehicle_age=vehicle.age_years,
        current_mileage=vehicle.current_mileage,
        annual_km_driven=vehicle.annual_km_driven,
        purchase_price=float(vehicle.purchase_price),
        repair_expenditure=float(vehicle.repair_expenditure),
        service_records_count=vehicle.service_records_count,
        months_since_last_service=vehicle.months_since_last_service,
    )
    dep = declining_balance_depreciation(
        purchase_price=float(vehicle.purchase_price),
        vehicle_age=vehicle.age_years,
        fuel_type=vehicle.fuel_type,
    )
    maintenance = assess_maintenance_risk(
        vehicle_age=vehicle.age_years,
        current_mileage=vehicle.current_mileage,
        months_since_last_service=vehicle.months_since_last_service,
        service_records_count=vehicle.service_records_count,
        repair_expenditure=float(vehicle.repair_expenditure),
        purchase_price=float(vehicle.purchase_price),
        fuel_type=vehicle.fuel_type,
        transmission=vehicle.transmission,
    )
    decision = make_decision(
        health_score=health.total_score,
        vehicle_age=vehicle.age_years,
        residual_value_pct=dep['total_depreciation_pct'],
        maintenance_risk_level=maintenance.risk_level,
        annual_maintenance_cost=maintenance.estimated_annual_cost,
        purchase_price=float(vehicle.purchase_price),
        repair_expenditure=float(vehicle.repair_expenditure),
    )
    # Pass health, dep, maintenance, decision to template context
```

---

### 🔴 Priority 2 — Fix `test_django_check_passes` Logic Bug

```python
# Fix in tests/test_all.py:
output = out.getvalue().lower()
self.assertNotIn('error', output)
self.assertNotIn('warning', output)
```

---

### 🟠 Priority 3 — Harden Settings for Production

```python
# config/settings.py
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ImproperlyConfigured("SECRET_KEY environment variable is not set.")

DEBUG = os.getenv('DEBUG', 'False') == 'True'
```

---

### 🟠 Priority 4 — Fix Hard-Coded Year in `preprocessing.py`

```python
import datetime

def engineer_features(df, current_year=None):
    if current_year is None:
        current_year = datetime.date.today().year
    ...
```

---

### 🟡 Priority 5 — Remove `StandardScaler` from Training Pipeline

GBR is scale-invariant. Remove from pipeline in `train_resale.py`.

---

### 🟡 Priority 6 — Fix Service Score Cap in `health_score.py`

```python
# Fix: allow score to reach 100 for perfect service history
service_score = min(100, service_ratio * 100)
```

---

### 🟡 Priority 7 — Add Missing Action for Age >7 in `maintenance.py`

```python
elif vehicle_age > 7:
    risk_points += 8
    actions.append('📋 Vehicle age exceeds 7 years — increased mechanical wear expected.')
```

---

### 🟡 Priority 8 — Remove Unused Dependencies

Remove `statsmodels` and `Pillow` from `requirements.txt`.

---

### 🟢 Priority 9 — Add Fleet Aggregation to `fleet_insights` View

Compute summary statistics in the view: count by fuel type, average age, KEEP/MONITOR/SELL/EXCHANGE distribution.

---

## 10. ML Module Status Summary

| Module | Method | Status | Wired to UI? |
|--------|--------|--------|-------------|
| **Resale Price Predictor** | Gradient Boosting (ML) | ⏳ Awaiting training data | ❌ No |
| **Depreciation Forecaster** | Declining Balance (rule-based) | ✅ Active | ❌ Not wired (prototype used instead) |
| **Health Scorer** | Weighted rules (5 components) | ✅ Active | ❌ Not wired (prototype used instead) |
| **Maintenance Risk Assessor** | Rule-based heuristics | ✅ Active | ❌ Not wired |
| **Ownership Cost Estimator** | Rule-based | ✅ Active | ❌ Not wired |
| **Decision Engine** | Multi-signal weighted logic | ✅ Active | ❌ Not wired |

> **IMPORTANT:** All rule-based modules are **complete, tested, and production-quality**. The critical next step is wiring them into `analytics/views.py` so the UI reflects the actual ML engine output rather than the simplified prototype formulas.

---

*End of Audit Report — AutoLifecycle Predictor*  
*Audit conducted: 2026-11-07 | Scope: Full codebase static analysis*
