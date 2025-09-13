"""
Military Communication System - Dashboard URLs

This module defines the URL routing for command dashboard API endpoints.
Uses Django REST Framework's DefaultRouter for automatic ViewSet routing.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import ViewSets (to be created)
# from .views import (
#     CommandWidgetViewSet,
#     OperationalReportViewSet,
#     SystemMetricsViewSet,
#     AlertSummaryViewSet,
# )

# Create router and register ViewSets
router = DefaultRouter(trailing_slash=False)

# Register ViewSets (uncomment when views are created)
# router.register(r'widgets', CommandWidgetViewSet, basename='commandwidget')
# router.register(r'reports', OperationalReportViewSet, basename='operationalreport')
# router.register(r'metrics', SystemMetricsViewSet, basename='systemmetrics')
# router.register(r'alerts', AlertSummaryViewSet, basename='alertsummary')

# URL patterns
urlpatterns = [
    # API root and ViewSet URLs
    path('api/', include(router.urls)),
    
    # Command widget endpoints (to be automatically generated):
    # GET /api/widgets/ - List dashboard widgets
    # POST /api/widgets/ - Create widget
    # GET /api/widgets/{id}/ - Get widget details
    # PUT/PATCH /api/widgets/{id}/ - Update widget
    # DELETE /api/widgets/{id}/ - Delete widget
    # POST /api/widgets/{id}/configure/ - Configure widget
    # POST /api/widgets/{id}/refresh/ - Refresh widget data
    # GET /api/widgets/active/ - Get active widgets
    # GET /api/widgets/user/ - Get user's widgets
    
    # Operational report endpoints (to be automatically generated):
    # GET /api/reports/ - List operational reports
    # POST /api/reports/ - Create report
    # GET /api/reports/{id}/ - Get report details
    # PUT/PATCH /api/reports/{id}/ - Update report
    # DELETE /api/reports/{id}/ - Delete report
    # POST /api/reports/{id}/generate/ - Generate report
    # POST /api/reports/{id}/export/ - Export report
    # GET /api/reports/{id}/data/ - Get report data
    # GET /api/reports/scheduled/ - Get scheduled reports
    # GET /api/reports/recent/ - Get recent reports
    
    # System metrics endpoints (to be automatically generated):
    # GET /api/metrics/ - List system metrics
    # POST /api/metrics/ - Create metric
    # GET /api/metrics/{id}/ - Get metric details
    # PUT/PATCH /api/metrics/{id}/ - Update metric
    # DELETE /api/metrics/{id}/ - Delete metric
    # POST /api/metrics/{id}/collect/ - Collect metric data
    # GET /api/metrics/{id}/history/ - Get metric history
    # GET /api/metrics/realtime/ - Get realtime metrics
    # GET /api/metrics/summary/ - Get metrics summary
    # GET /api/metrics/alerts/ - Get metric alerts
    
    # Alert summary endpoints (to be automatically generated):
    # GET /api/alerts/ - List alert summaries
    # POST /api/alerts/ - Create alert summary
    # GET /api/alerts/{id}/ - Get alert details
    # PUT/PATCH /api/alerts/{id}/ - Update alert
    # DELETE /api/alerts/{id}/ - Delete alert
    # POST /api/alerts/{id}/acknowledge/ - Acknowledge alert
    # GET /api/alerts/active/ - Get active alerts
    # GET /api/alerts/critical/ - Get critical alerts
    # GET /api/alerts/summary/ - Get alerts summary
    # GET /api/alerts/trends/ - Get alert trends
    
    # Additional dashboard endpoints:
    # GET /api/dashboard/overview/ - Get dashboard overview
    # GET /api/dashboard/status/ - Get system status
    # GET /api/dashboard/health/ - Get system health
    # POST /api/dashboard/customize/ - Customize dashboard
]

# Add router URLs to urlpatterns
urlpatterns += router.urls