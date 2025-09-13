"""
Military Communication System - Messaging URLs

This module defines the URL routing for messaging API endpoints.
Uses Django REST Framework's DefaultRouter for automatic ViewSet routing.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ConversationViewSet,
    MessageViewSet,
    MessageAttachmentViewSet,
    MessageDeliveryViewSet,
    MessageReactionViewSet,
)

# Create router and register ViewSets
router = DefaultRouter(trailing_slash=False)
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'attachments', MessageAttachmentViewSet, basename='messageattachment')
router.register(r'deliveries', MessageDeliveryViewSet, basename='messagedelivery')
router.register(r'reactions', MessageReactionViewSet, basename='messagereaction')

# URL patterns
urlpatterns = [
    # API root and ViewSet URLs
    path('api/', include(router.urls)),
    
    # Conversation endpoints (automatically generated):
    # GET /api/conversations/ - List conversations
    # POST /api/conversations/ - Create conversation
    # GET /api/conversations/{id}/ - Get conversation details
    # PUT/PATCH /api/conversations/{id}/ - Update conversation
    # DELETE /api/conversations/{id}/ - Delete conversation
    # POST /api/conversations/{id}/add_participants/ - Add participants
    # POST /api/conversations/{id}/remove_participants/ - Remove participants
    # POST /api/conversations/{id}/archive/ - Archive conversation
    # POST /api/conversations/{id}/unarchive/ - Unarchive conversation
    # GET /api/conversations/archived/ - Get archived conversations
    
    # Message endpoints (automatically generated):
    # GET /api/messages/ - List messages
    # POST /api/messages/ - Send message
    # GET /api/messages/{id}/ - Get message details
    # PUT/PATCH /api/messages/{id}/ - Update message
    # DELETE /api/messages/{id}/ - Delete message
    # POST /api/messages/{id}/mark_read/ - Mark message as read
    # POST /api/messages/{id}/react/ - Add reaction to message
    # DELETE /api/messages/{id}/remove_reaction/ - Remove reaction
    # POST /api/messages/{id}/edit/ - Edit message content
    # GET /api/messages/unread/ - Get unread messages
    
    # Attachment endpoints (automatically generated):
    # GET /api/attachments/ - List attachments
    # GET /api/attachments/{id}/ - Get attachment details
    # POST /api/attachments/{id}/download/ - Track download
    
    # Delivery endpoints (automatically generated):
    # GET /api/deliveries/ - List deliveries
    # GET /api/deliveries/{id}/ - Get delivery details
    # GET /api/deliveries/failed/ - Get failed deliveries
    # GET /api/deliveries/pending/ - Get pending deliveries
    
    # Reaction endpoints (automatically generated):
    # GET /api/reactions/ - List reactions
    # POST /api/reactions/ - Create reaction
    # GET /api/reactions/{id}/ - Get reaction details
    # DELETE /api/reactions/{id}/ - Delete reaction
]

# Add router URLs to urlpatterns
urlpatterns += router.urls