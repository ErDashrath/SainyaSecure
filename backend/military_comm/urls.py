"""
Military Communication System - Main URL Configuration

This module defines the main URL routing for the entire military communication system.
Organizes API endpoints by functional modules with proper namespacing.

API Structure:
- /admin/ - Django admin interface
- /api/ - Main API root with browsable interface
- /users/ - User management and authentication
- /messaging/ - Secure messaging and conversations
- /blockchain/ - Blockchain logging and integrity
- /p2p/ - Peer-to-peer synchronization
- /ai/ - AI anomaly detection and threat intelligence
- /dashboard/ - Command dashboard and reporting
- /docs/ - API documentation
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.views.generic import TemplateView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from . import views


@api_view(['GET'])
def api_root(request):
    """
    Military Communication System API Root
    
    Welcome to the Secure AI-Powered Battlefield Messenger API.
    This system provides military-grade secure communication with:
    - End-to-end encrypted messaging
    - Blockchain audit trails  
    - AI anomaly detection
    - Offline-first P2P sync
    - Command dashboard
    """
    return Response({
        'system': 'Secure AI-Powered Battlefield Messenger',
        'version': '1.0.0',
        'status': 'active',
        'modules': {
            'users': request.build_absolute_uri('/users/api/'),
            'messaging': request.build_absolute_uri('/messaging/api/'),
            'blockchain': request.build_absolute_uri('/blockchain/api/'),
            'p2p_sync': request.build_absolute_uri('/p2p/api/'),
            'ai_anomaly': request.build_absolute_uri('/ai/api/'),
            'dashboard': request.build_absolute_uri('/dashboard/api/'),
        },
        'documentation': request.build_absolute_uri('/docs/'),
        'admin': request.build_absolute_uri('/admin/'),
    })


urlpatterns = [
    # Frontend URLs
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'), 
    path('dashboard/', views.dashboard, name='dashboard'),
    path('join/<str:join_token>/', views.device_join, name='device_join'),
    
    # Main API root endpoint
    path('api/', api_root, name='api-root'),
    
    # Django admin interface
    path('admin/', admin.site.urls),
    
    # Core module API endpoints
    path('users/', include('users.urls')),
    path('messaging/', include('messaging.urls')),
    path('blockchain/', include('blockchain.urls')),
    path('p2p/', include('p2p_sync.urls')),
    path('ai/', include('ai_anomaly.urls')),
    path('dashboard/', include('dashboard.urls')),
    
    # API documentation and browsable interface
    path('docs/', include('rest_framework.urls', namespace='rest_framework')),
    
    # Health check endpoint
    path('health/', lambda request: JsonResponse({
        'status': 'healthy',
        'system': 'Military Communication System',
        'timestamp': '2025-09-13T00:00:00Z'
    }), name='health-check'),
    
    # System status endpoint  
    path('status/', lambda request: JsonResponse({
        'system': 'online',
        'modules': {
            'users': 'active',
            'messaging': 'active', 
            'blockchain': 'active',
            'p2p_sync': 'active',
            'ai_anomaly': 'active',
            'dashboard': 'active'
        },
        'security_level': 'military-grade',
        'encryption': 'AES-256-GCM'
    }), name='system-status'),
]
