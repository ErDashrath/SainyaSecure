"""
Military Communication System - Messaging Views

This module defines the DRF ViewSets for messaging operations.
Implements secure message handling with encryption and military permissions.
"""

from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q, Count, Max
from django.db import transaction

from .models import Conversation, Message, MessageAttachment, MessageDelivery, MessageReaction
from .serializers import (
    ConversationSerializer, ConversationListSerializer,
    MessageSerializer, MessageListSerializer,
    MessageAttachmentSerializer, MessageDeliverySerializer, MessageReactionSerializer
)
from users.permissions import MilitaryPermission, ClearanceLevelPermission


class ConversationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing conversations and channels"""
    
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated, MilitaryPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['conversation_type', 'classification_level', 'is_archived']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'last_message_at', 'name']
    ordering = ['-last_message_at']
    
    def get_serializer_class(self):
        """Use list serializer for list action"""
        if self.action == 'list':
            return ConversationListSerializer
        return super().get_serializer_class()
    
    def get_queryset(self):
        """Filter conversations based on user participation and clearance"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter by user participation
        queryset = queryset.filter(participants=user)
        
        # Filter by clearance level
        if not user.is_superuser:
            clearance_levels = {
                'CONFIDENTIAL': 1,
                'SECRET': 2,
                'TOP_SECRET': 3,
                'TOP_SECRET_SCI': 4
            }
            
            user_level = clearance_levels.get(getattr(user, 'clearance_level', ''), 0)
            accessible_levels = [
                level for level, value in clearance_levels.items()
                if value <= user_level
            ]
            
            queryset = queryset.filter(
                Q(classification_level__in=accessible_levels) |
                Q(required_clearance='') |
                Q(required_clearance__isnull=True)
            )
        
        return queryset.select_related('created_by').prefetch_related('participants', 'admin_users')
    
    def perform_create(self, serializer):
        """Create conversation with current user as creator"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_participants(self, request, pk=None):
        """Add participants to conversation"""
        conversation = self.get_object()
        user_ids = request.data.get('user_ids', [])
        
        # Check if user is admin of conversation
        if request.user not in conversation.admin_users.all() and not request.user.is_superuser:
            return Response(
                {'error': 'Only conversation admins can add participants'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Add participants
        conversation.participants.add(*user_ids)
        
        return Response({'message': f'Added {len(user_ids)} participants'})
    
    @action(detail=True, methods=['post'])
    def remove_participants(self, request, pk=None):
        """Remove participants from conversation"""
        conversation = self.get_object()
        user_ids = request.data.get('user_ids', [])
        
        # Check if user is admin of conversation
        if request.user not in conversation.admin_users.all() and not request.user.is_superuser:
            return Response(
                {'error': 'Only conversation admins can remove participants'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Remove participants (but not admins)
        for user_id in user_ids:
            if user_id not in conversation.admin_users.values_list('id', flat=True):
                conversation.participants.remove(user_id)
        
        return Response({'message': f'Removed {len(user_ids)} participants'})
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive conversation"""
        conversation = self.get_object()
        conversation.is_archived = True
        conversation.save()
        
        return Response({'message': 'Conversation archived'})
    
    @action(detail=True, methods=['post'])
    def unarchive(self, request, pk=None):
        """Unarchive conversation"""
        conversation = self.get_object()
        conversation.is_archived = False
        conversation.save()
        
        return Response({'message': 'Conversation unarchived'})
    
    @action(detail=False, methods=['get'])
    def archived(self, request):
        """Get archived conversations"""
        conversations = self.get_queryset().filter(is_archived=True)
        serializer = self.get_serializer(conversations, many=True)
        return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    """ViewSet for managing messages"""
    
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, MilitaryPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['conversation', 'message_type', 'priority', 'delivery_status']
    search_fields = ['content_encrypted']  # In production, this would be limited
    ordering_fields = ['created_at', 'priority']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Use list serializer for list action"""
        if self.action == 'list':
            return MessageListSerializer
        return super().get_serializer_class()
    
    def get_queryset(self):
        """Filter messages based on conversation participation"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter by conversations user participates in
        user_conversations = user.conversations.values_list('id', flat=True)
        queryset = queryset.filter(conversation__in=user_conversations)
        
        return queryset.select_related('sender', 'conversation', 'sender_device').prefetch_related('attachments', 'reactions')
    
    def perform_create(self, serializer):
        """Create message with delivery tracking"""
        with transaction.atomic():
            # Get user's device (for simplicity, get first active device)
            device = self.request.user.devices.filter(status='ACTIVE').first()
            
            message = serializer.save(
                sender=self.request.user,
                sender_device=device
            )
            
            # Create delivery records for all conversation participants
            conversation = message.conversation
            participants = conversation.participants.exclude(id=self.request.user.id)
            
            deliveries = []
            for participant in participants:
                deliveries.append(MessageDelivery(
                    message=message,
                    recipient=participant,
                    status='PENDING'
                ))
            
            MessageDelivery.objects.bulk_create(deliveries)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark message as read"""
        message = self.get_object()
        
        # Update delivery record
        delivery = MessageDelivery.objects.filter(
            message=message,
            recipient=request.user
        ).first()
        
        if delivery and delivery.status != 'READ':
            delivery.status = 'READ'
            delivery.read_at = timezone.now()
            delivery.save()
        
        return Response({'message': 'Message marked as read'})
    
    @action(detail=True, methods=['post'])
    def react(self, request, pk=None):
        """Add reaction to message"""
        message = self.get_object()
        reaction_type = request.data.get('reaction_type')
        
        if not reaction_type:
            return Response(
                {'error': 'reaction_type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create or update reaction
        reaction, created = MessageReaction.objects.get_or_create(
            message=message,
            user=request.user,
            reaction_type=reaction_type
        )
        
        if created:
            return Response({'message': 'Reaction added'})
        else:
            return Response({'message': 'Reaction already exists'})
    
    @action(detail=True, methods=['delete'])
    def remove_reaction(self, request, pk=None):
        """Remove reaction from message"""
        message = self.get_object()
        reaction_type = request.data.get('reaction_type')
        
        MessageReaction.objects.filter(
            message=message,
            user=request.user,
            reaction_type=reaction_type
        ).delete()
        
        return Response({'message': 'Reaction removed'})
    
    @action(detail=True, methods=['post'])
    def edit(self, request, pk=None):
        """Edit message content"""
        message = self.get_object()
        
        # Only sender can edit their own messages
        if message.sender != request.user:
            return Response(
                {'error': 'Can only edit your own messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if message is too old to edit (24 hours)
        if (timezone.now() - message.created_at).total_seconds() > 86400:
            return Response(
                {'error': 'Message too old to edit'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        new_content = request.data.get('content', '')
        if new_content:
            # TODO: Implement proper encryption
            message.content_encrypted = new_content
            message.content_hash = message.generate_content_hash(new_content)
            message.is_edited = True
            message.edit_count += 1
            message.edited_at = timezone.now()
            message.save()
            
            return Response({'message': 'Message updated'})
        
        return Response(
            {'error': 'Content is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread messages for current user"""
        unread_deliveries = MessageDelivery.objects.filter(
            recipient=request.user,
            status__in=['PENDING', 'DELIVERED']
        ).select_related('message', 'message__sender')
        
        messages = [delivery.message for delivery in unread_deliveries]
        serializer = MessageListSerializer(messages, many=True)
        return Response(serializer.data)


class MessageAttachmentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for message attachments (read-only)"""
    
    queryset = MessageAttachment.objects.all()
    serializer_class = MessageAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated, MilitaryPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['file_type', 'virus_scan_status']
    ordering_fields = ['uploaded_at', 'file_size']
    ordering = ['-uploaded_at']
    
    def get_queryset(self):
        """Filter attachments based on message access"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter by messages in conversations user participates in
        user_conversations = user.conversations.values_list('id', flat=True)
        queryset = queryset.filter(message__conversation__in=user_conversations)
        
        return queryset.select_related('message', 'uploaded_by')
    
    @action(detail=True, methods=['post'])
    def download(self, request, pk=None):
        """Track attachment download"""
        attachment = self.get_object()
        
        # Increment download count
        attachment.download_count += 1
        attachment.save(update_fields=['download_count'])
        
        # In production, this would return the actual file or a download URL
        return Response({
            'message': 'Download tracked',
            'filename': attachment.filename,
            'file_size': attachment.file_size
        })


class MessageDeliveryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for message delivery tracking"""
    
    queryset = MessageDelivery.objects.all()
    serializer_class = MessageDeliverySerializer
    permission_classes = [permissions.IsAuthenticated, MilitaryPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'recipient', 'is_offline_delivery']
    ordering_fields = ['sent_at', 'delivered_at']
    ordering = ['-sent_at']
    
    def get_queryset(self):
        """Filter deliveries based on user permissions"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Users can see deliveries for messages they sent or received
        queryset = queryset.filter(
            Q(message__sender=user) | Q(recipient=user)
        )
        
        return queryset.select_related('message', 'recipient', 'recipient_device')
    
    @action(detail=False, methods=['get'])
    def failed(self, request):
        """Get failed deliveries"""
        failed_deliveries = self.get_queryset().filter(status='FAILED')
        serializer = self.get_serializer(failed_deliveries, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending deliveries"""
        pending_deliveries = self.get_queryset().filter(status='PENDING')
        serializer = self.get_serializer(pending_deliveries, many=True)
        return Response(serializer.data)


class MessageReactionViewSet(viewsets.ModelViewSet):
    """ViewSet for message reactions"""
    
    queryset = MessageReaction.objects.all()
    serializer_class = MessageReactionSerializer
    permission_classes = [permissions.IsAuthenticated, MilitaryPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['message', 'reaction_type']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter reactions based on message access"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter by messages in conversations user participates in
        user_conversations = user.conversations.values_list('id', flat=True)
        queryset = queryset.filter(message__conversation__in=user_conversations)
        
        return queryset.select_related('message', 'user')
    
    def perform_create(self, serializer):
        """Create reaction with current user"""
        serializer.save(user=self.request.user)
