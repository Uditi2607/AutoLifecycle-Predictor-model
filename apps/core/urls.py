"""
Core app URL patterns.
"""
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
]
