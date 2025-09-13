"""
Command Center URL Configuration

Routes for master authority dashboard and API endpoints:
- Main command dashboard with real-time monitoring
- Blockchain ledger explorer for immutable audit trails  
- Encrypted message logs with access control
- Node connectivity monitoring and management
- Security alert management with AI anomaly integration
- Mission audit trails and replay capabilities
- API endpoints for real-time updates and synchronization
"""

from django.urls import path
from . import views

app_name = 'command_center'

urlpatterns = [
    # Main Command Center Views
    path('', views.CommandCenterDashboard.as_view(), name='dashboard'),
    path('ledger/', views.BlockchainLedgerView.as_view(), name='ledger_explorer'),
    path('messages/', views.MessageLogsView.as_view(), name='message_logs'),
    path('nodes/', views.NodeMonitoringView.as_view(), name='node_monitoring'),
    path('alerts/', views.AlertManagementView.as_view(), name='alert_management'),
    path('missions/', views.MissionAuditView.as_view(), name='mission_audit'),
    
    # API Endpoints for Real-time Updates
    path('api/stats/', views.api_dashboard_stats, name='api_stats'),
    path('api/sync/', views.api_sync_ledger, name='api_sync_ledger'),
    path('api/nodes/', views.api_node_status, name='api_node_status'),
    path('api/alerts/<uuid:alert_id>/resolve/', views.api_resolve_alert, name='api_resolve_alert'),
    
    # WebSocket endpoints will be added in consumers.py
    # ws/command_center/dashboard/ - Real-time dashboard updates
    # ws/command_center/alerts/ - Real-time alert notifications
    # ws/command_center/nodes/ - Real-time node status updates
]