"""
Military Communication System - AI Anomaly URLs

This module defines the URL routing for AI anomaly detection API endpoints.
Uses Django REST Framework's DefaultRouter for automatic ViewSet routing.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import ViewSets (to be created)
# from .views import (
#     AnomalyModelViewSet,
#     ThreatAlertViewSet,
#     BehavioralPatternViewSet,
#     ModelTrainingViewSet,
#     ThreatIntelligenceViewSet,
# )

# Create router and register ViewSets
router = DefaultRouter(trailing_slash=False)

# Register ViewSets (uncomment when views are created)
# router.register(r'models', AnomalyModelViewSet, basename='anomalymodel')
# router.register(r'alerts', ThreatAlertViewSet, basename='threatalert')
# router.register(r'patterns', BehavioralPatternViewSet, basename='behavioralpattern')
# router.register(r'training', ModelTrainingViewSet, basename='modeltraining')
# router.register(r'intelligence', ThreatIntelligenceViewSet, basename='threatintelligence')

# URL patterns
urlpatterns = [
    # API root and ViewSet URLs
    path('api/', include(router.urls)),
    
    # AI Model endpoints (to be automatically generated):
    # GET /api/models/ - List AI models
    # POST /api/models/ - Create new model
    # GET /api/models/{id}/ - Get model details
    # PUT/PATCH /api/models/{id}/ - Update model
    # DELETE /api/models/{id}/ - Delete model
    # POST /api/models/{id}/train/ - Train model
    # POST /api/models/{id}/predict/ - Make prediction
    # POST /api/models/{id}/deploy/ - Deploy model
    # GET /api/models/{id}/performance/ - Get model performance
    # GET /api/models/active/ - Get active models
    
    # Threat alert endpoints (to be automatically generated):
    # GET /api/alerts/ - List threat alerts
    # POST /api/alerts/ - Create alert
    # GET /api/alerts/{id}/ - Get alert details
    # PUT/PATCH /api/alerts/{id}/ - Update alert
    # DELETE /api/alerts/{id}/ - Delete alert
    # POST /api/alerts/{id}/acknowledge/ - Acknowledge alert
    # POST /api/alerts/{id}/escalate/ - Escalate alert
    # POST /api/alerts/{id}/resolve/ - Resolve alert
    # GET /api/alerts/active/ - Get active alerts
    # GET /api/alerts/critical/ - Get critical alerts
    
    # Behavioral pattern endpoints (to be automatically generated):
    # GET /api/patterns/ - List behavioral patterns
    # POST /api/patterns/ - Create pattern
    # GET /api/patterns/{id}/ - Get pattern details
    # PUT/PATCH /api/patterns/{id}/ - Update pattern
    # DELETE /api/patterns/{id}/ - Delete pattern
    # POST /api/patterns/{id}/analyze/ - Analyze pattern
    # POST /api/patterns/detect/ - Detect new patterns
    # GET /api/patterns/anomalous/ - Get anomalous patterns
    # GET /api/patterns/baseline/ - Get baseline patterns
    
    # Model training endpoints (to be automatically generated):
    # GET /api/training/ - List training sessions
    # POST /api/training/ - Start training
    # GET /api/training/{id}/ - Get training details
    # PUT/PATCH /api/training/{id}/ - Update training
    # DELETE /api/training/{id}/ - Stop training
    # POST /api/training/{id}/pause/ - Pause training
    # POST /api/training/{id}/resume/ - Resume training
    # GET /api/training/{id}/progress/ - Get training progress
    # GET /api/training/active/ - Get active training sessions
    # GET /api/training/completed/ - Get completed training
    
    # Threat intelligence endpoints (to be automatically generated):
    # GET /api/intelligence/ - List threat intelligence
    # POST /api/intelligence/ - Create intelligence
    # GET /api/intelligence/{id}/ - Get intelligence details
    # PUT/PATCH /api/intelligence/{id}/ - Update intelligence
    # DELETE /api/intelligence/{id}/ - Delete intelligence
    # POST /api/intelligence/{id}/verify/ - Verify intelligence
    # POST /api/intelligence/analyze/ - Analyze threats
    # GET /api/intelligence/feeds/ - Get threat feeds
    # GET /api/intelligence/indicators/ - Get threat indicators
    # GET /api/intelligence/reports/ - Get intelligence reports
]

# Add router URLs to urlpatterns
urlpatterns += router.urls