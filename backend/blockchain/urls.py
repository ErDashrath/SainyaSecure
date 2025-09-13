"""
Military Communication System - Blockchain URLs

This module defines the URL routing for blockchain API endpoints.
Uses Django REST Framework's DefaultRouter for automatic ViewSet routing.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import ViewSets (to be created)
# from .views import (
#     LocalLedgerBlockViewSet,
#     BlockchainTransactionViewSet,
#     SyncStatusViewSet,
#     ConsensusRecordViewSet,
#     IntegrityVerificationViewSet,
# )

# Create router and register ViewSets
router = DefaultRouter(trailing_slash=False)

# Register ViewSets (uncomment when views are created)
# router.register(r'blocks', LocalLedgerBlockViewSet, basename='locallledgerblock')
# router.register(r'transactions', BlockchainTransactionViewSet, basename='blockchaintransaction')
# router.register(r'sync-status', SyncStatusViewSet, basename='syncstatus')
# router.register(r'consensus', ConsensusRecordViewSet, basename='consensusrecord')
# router.register(r'integrity', IntegrityVerificationViewSet, basename='integrityverification')

# URL patterns
urlpatterns = [
    # API root and ViewSet URLs
    path('api/', include(router.urls)),
    
    # Blockchain endpoints (to be automatically generated):
    # GET /api/blocks/ - List local ledger blocks
    # POST /api/blocks/ - Create new block
    # GET /api/blocks/{id}/ - Get block details
    # PUT/PATCH /api/blocks/{id}/ - Update block
    # DELETE /api/blocks/{id}/ - Delete block
    # POST /api/blocks/{id}/sync/ - Sync block to blockchain
    # POST /api/blocks/{id}/verify/ - Verify block integrity
    # GET /api/blocks/pending/ - Get pending blocks
    # GET /api/blocks/failed/ - Get failed sync blocks
    
    # Transaction endpoints (to be automatically generated):
    # GET /api/transactions/ - List blockchain transactions
    # POST /api/transactions/ - Create transaction
    # GET /api/transactions/{id}/ - Get transaction details
    # POST /api/transactions/{id}/verify/ - Verify transaction
    # GET /api/transactions/pending/ - Get pending transactions
    # GET /api/transactions/confirmed/ - Get confirmed transactions
    
    # Sync status endpoints (to be automatically generated):
    # GET /api/sync-status/ - List sync statuses
    # GET /api/sync-status/{id}/ - Get sync status details
    # POST /api/sync-status/{id}/retry/ - Retry failed sync
    # GET /api/sync-status/active/ - Get active syncs
    # GET /api/sync-status/failed/ - Get failed syncs
    
    # Consensus endpoints (to be automatically generated):
    # GET /api/consensus/ - List consensus records
    # POST /api/consensus/ - Create consensus record
    # GET /api/consensus/{id}/ - Get consensus details
    # POST /api/consensus/{id}/vote/ - Vote on consensus
    # GET /api/consensus/active/ - Get active consensus
    
    # Integrity verification endpoints (to be automatically generated):
    # GET /api/integrity/ - List integrity verifications
    # POST /api/integrity/ - Create verification
    # GET /api/integrity/{id}/ - Get verification details
    # POST /api/integrity/{id}/recheck/ - Recheck integrity
    # GET /api/integrity/alerts/ - Get integrity alerts
]

# Add router URLs to urlpatterns
urlpatterns += router.urls