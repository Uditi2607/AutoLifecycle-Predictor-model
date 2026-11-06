"""
Vehicle app URL patterns.
"""
from django.urls import path
from . import views

app_name = 'vehicles'

urlpatterns = [
    path('', views.vehicle_list, name='vehicle_list'),
    path('register/', views.vehicle_register, name='vehicle_register'),
    path('<int:pk>/', views.vehicle_detail, name='vehicle_detail'),
    path('<int:pk>/delete/', views.vehicle_delete, name='vehicle_delete'),
]
