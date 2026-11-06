"""
Analytics app URL patterns.
"""
from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('vehicle/<int:pk>/', views.vehicle_outlook, name='vehicle_outlook'),
    path('fleet/', views.fleet_insights, name='fleet_insights'),
]
