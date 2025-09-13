"""
Military Communication System - P2P Sync URLs

This module defines the URL routing for P2P synchronization API endpoints.
Uses Django REST Framework's DefaultRouter for automatic ViewSet routing.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import ViewSets (to be created)
# from .views import (
#     PeerNodeViewSet,
#     MeshNetworkViewSet,
#     SyncQueueViewSet,
#     ConflictResolutionViewSet,
#     NetworkTopologyViewSet,
# )

# Create router and register ViewSets
router = DefaultRouter(trailing_slash=False)

# Register ViewSets (uncomment when views are created)
# router.register(r'peers', PeerNodeViewSet, basename='peernode')
# router.register(r'networks', MeshNetworkViewSet, basename='meshnetwork')
# router.register(r'sync-queue', SyncQueueViewSet, basename='syncqueue')
# router.register(r'conflicts', ConflictResolutionViewSet, basename='conflictresolution')
# router.register(r'topology', NetworkTopologyViewSet, basename='networktopology')

# URL patterns
urlpatterns = [
    # API root and ViewSet URLs
    path('api/', include(router.urls)),
    
    # Peer node endpoints (to be automatically generated):
    # GET /api/peers/ - List peer nodes
    # POST /api/peers/ - Register new peer
    # GET /api/peers/{id}/ - Get peer details
    # PUT/PATCH /api/peers/{id}/ - Update peer info
    # DELETE /api/peers/{id}/ - Remove peer
    # POST /api/peers/{id}/connect/ - Connect to peer
    # POST /api/peers/{id}/disconnect/ - Disconnect from peer
    # POST /api/peers/{id}/ping/ - Ping peer
    # GET /api/peers/online/ - Get online peers
    # GET /api/peers/trusted/ - Get trusted peers
    
    # Mesh network endpoints (to be automatically generated):
    # GET /api/networks/ - List mesh networks
    # POST /api/networks/ - Create network
    # GET /api/networks/{id}/ - Get network details
    # PUT/PATCH /api/networks/{id}/ - Update network
    # DELETE /api/networks/{id}/ - Leave network
    # POST /api/networks/{id}/join/ - Join network
    # POST /api/networks/{id}/broadcast/ - Broadcast to network
    # GET /api/networks/{id}/members/ - Get network members
    # GET /api/networks/active/ - Get active networks
    
    # Sync queue endpoints (to be automatically generated):
    # GET /api/sync-queue/ - List sync queue items
    # POST /api/sync-queue/ - Add to sync queue
    # GET /api/sync-queue/{id}/ - Get queue item details
    # PUT/PATCH /api/sync-queue/{id}/ - Update queue item
    # DELETE /api/sync-queue/{id}/ - Remove from queue
    # POST /api/sync-queue/{id}/process/ - Process queue item
    # POST /api/sync-queue/{id}/retry/ - Retry failed sync
    # GET /api/sync-queue/pending/ - Get pending syncs
    # GET /api/sync-queue/failed/ - Get failed syncs
    
    # Conflict resolution endpoints (to be automatically generated):
    # GET /api/conflicts/ - List conflicts
    # POST /api/conflicts/ - Report conflict
    # GET /api/conflicts/{id}/ - Get conflict details
    # PUT/PATCH /api/conflicts/{id}/ - Update conflict
    # DELETE /api/conflicts/{id}/ - Delete conflict
    # POST /api/conflicts/{id}/resolve/ - Resolve conflict
    # POST /api/conflicts/{id}/escalate/ - Escalate conflict
    # GET /api/conflicts/unresolved/ - Get unresolved conflicts
    # GET /api/conflicts/critical/ - Get critical conflicts
    
    # Network topology endpoints (to be automatically generated):
    # GET /api/topology/ - List topology records
    # POST /api/topology/ - Create topology record
    # GET /api/topology/{id}/ - Get topology details
    # PUT/PATCH /api/topology/{id}/ - Update topology
    # POST /api/topology/discover/ - Discover network topology
    # POST /api/topology/optimize/ - Optimize network routes
    # GET /api/topology/map/ - Get network map
    # GET /api/topology/routes/ - Get routing table
]

# Add router URLs to urlpatterns
urlpatterns += router.urls