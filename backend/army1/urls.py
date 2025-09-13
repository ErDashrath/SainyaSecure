"""
URL configuration for army1 frontend app
"""
from django.urls import path
from . import views

urlpatterns = [
    # Main frontend pages
    path('', views.index, name='index'),
    path('login/', views.user_login, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Rank-based dashboard routes
    path('dashboard/command/', views.dashboard_command, name='dashboard_command'),
    path('dashboard/operations/', views.dashboard_operations, name='dashboard_operations'),
    path('dashboard/intelligence/', views.dashboard_intelligence, name='dashboard_intelligence'),
    path('dashboard/communications/', views.dashboard_communications, name='dashboard_communications'),
    path('dashboard/field/', views.dashboard_field, name='dashboard_field'),
    path('dashboard/emergency/', views.dashboard_emergency, name='dashboard_emergency'),
    
    path('join/', views.device_join, name='join'),
    path('logout/', views.user_logout, name='logout'),
    
    # API endpoints
    path('api/stats/', views.api_system_stats, name='api_system_stats'),
    
    # Module endpoints (to be implemented)
    path('modules/messaging/', views.module_messaging, name='module_messaging'),
    path('modules/p2p/', views.module_p2p, name='module_p2p'),
    path('modules/personnel/', views.module_personnel, name='module_personnel'),
    path('modules/devices/', views.module_devices, name='module_devices'),
    path('modules/security/', views.module_security, name='module_security'),
    path('modules/reports/', views.module_reports, name='module_reports'),
    path('modules/logs/', views.module_logs, name='module_logs'),
    path('modules/intel/', views.module_intel, name='module_intel'),
    path('modules/threats/', views.module_threats, name='module_threats'),
    path('modules/classified/', views.module_classified, name='module_classified'),
    path('modules/comms/', views.module_comms, name='module_comms'),
    path('modules/networks/', views.module_networks, name='module_networks'),
    path('modules/broadcast/', views.module_broadcast, name='module_broadcast'),
    path('modules/missions/', views.module_missions, name='module_missions'),
    path('modules/tactical/', views.module_tactical, name='module_tactical'),
    path('modules/operations/', views.module_operations, name='module_operations'),
    path('modules/equipment/', views.module_equipment, name='module_equipment'),
    path('modules/training/', views.module_training, name='module_training'),
    path('modules/emergency/', views.module_emergency, name='module_emergency'),
]