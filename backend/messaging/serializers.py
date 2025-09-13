"""
Military Communication System - Messaging Serializers

This module defines the DRF serializers for messaging-related models.
Handles secure message serialization with encryption and validation.
"""

from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from django.db import models

from .models import Conversation, Message, MessageAttachment, MessageDelivery, MessageReaction
from users.serializers import MilitaryUserReadOnlySerializer


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for Conversation model"""
    
    participants = MilitaryUserReadOnlySerializer(many=True, read_only=True)
    admin_users = MilitaryUserReadOnlySerializer(many=True, read_only=True)
    created_by = MilitaryUserReadOnlySerializer(read_only=True)
    participant_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    # Write-only fields for creating/updating participants
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of user IDs to add as participants"
    )
    admin_user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of user IDs to add as admins"
    )
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'conversation_id', 'name', 'description', 'conversation_type',
            'participants', 'admin_users', 'created_by', 'participant_count',
            'classification_level', 'required_clearance', 'encryption_key_id',
            'is_archived', 'is_muted', 'auto_delete_after',
            'created_at', 'updated_at', 'last_message_at', 'last_message',
            'unread_count', 'participant_ids', 'admin_user_ids'
        ]
        read_only_fields = [
            'id', 'conversation_id', 'created_by', 'created_at', 'updated_at',
            'last_message_at', 'participants', 'admin_users', 'participant_count',
            'last_message', 'unread_count'
        ]
    
    def get_participant_count(self, obj):
        """Get number of participants"""
        return obj.participants.count()
    
    def get_last_message(self, obj):
        """Get last message in conversation"""
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            return {
                'id': last_message.id,
                'message_type': last_message.message_type,
                'sender': last_message.sender.get_full_name(),
                'created_at': last_message.created_at,
                'priority': last_message.priority
            }
        return None
    
    def get_unread_count(self, obj):
        """Get unread message count for current user"""
        request = self.context.get('request')
        if request and request.user:
            # This would need to be implemented based on read receipt logic
            return 0
        return 0
    
    def create(self, validated_data):
        """Create conversation with participants"""
        participant_ids = validated_data.pop('participant_ids', [])
        admin_user_ids = validated_data.pop('admin_user_ids', [])
        
        with transaction.atomic():
            conversation = super().create(validated_data)
            
            # Add participants
            if participant_ids:
                conversation.participants.set(participant_ids)
            
            # Add admins
            if admin_user_ids:
                conversation.admin_users.set(admin_user_ids)
            
            # Add creator as participant and admin
            conversation.participants.add(conversation.created_by)
            conversation.admin_users.add(conversation.created_by)
        
        return conversation
    
    def update(self, instance, validated_data):
        """Update conversation with participants"""
        participant_ids = validated_data.pop('participant_ids', None)
        admin_user_ids = validated_data.pop('admin_user_ids', None)
        
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            
            # Update participants if provided
            if participant_ids is not None:
                instance.participants.set(participant_ids)
            
            # Update admins if provided
            if admin_user_ids is not None:
                instance.admin_users.set(admin_user_ids)
        
        return instance


class MessageAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for MessageAttachment model"""
    
    class Meta:
        model = MessageAttachment
        fields = [
            'id', 'attachment_id', 'filename', 'file_type', 'mime_type',
            'file_size', 'file_hash', 'virus_scan_status', 'scan_date',
            'uploaded_by', 'uploaded_at', 'download_count'
        ]
        read_only_fields = [
            'id', 'attachment_id', 'file_hash', 'virus_scan_status',
            'scan_date', 'uploaded_by', 'uploaded_at', 'download_count'
        ]


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model"""
    
    sender = MilitaryUserReadOnlySerializer(read_only=True)
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    reply_to_message = serializers.SerializerMethodField()
    delivery_count = serializers.SerializerMethodField()
    read_count = serializers.SerializerMethodField()
    reactions_summary = serializers.SerializerMethodField()
    
    # Write-only field for message content (will be encrypted)
    content = serializers.CharField(write_only=True, help_text="Message content (will be encrypted)")
    
    class Meta:
        model = Message
        fields = [
            'id', 'message_id', 'conversation', 'sender', 'sender_device',
            'message_type', 'content', 'content_encrypted', 'content_hash',
            'priority', 'is_edited', 'edit_count',
            'reply_to', 'reply_to_message', 'thread_id',
            'has_attachments', 'attachment_count', 'attachments',
            'latitude', 'longitude', 'location_name',
            'created_at', 'edited_at', 'expires_at',
            'delivery_status', 'delivered_at',
            'is_offline_message', 'offline_created_at', 'synced_at',
            'delivery_count', 'read_count', 'reactions_summary'
        ]
        read_only_fields = [
            'id', 'message_id', 'sender', 'content_encrypted', 'content_hash',
            'is_edited', 'edit_count', 'has_attachments', 'attachment_count',
            'created_at', 'edited_at', 'delivery_status', 'delivered_at',
            'synced_at', 'attachments', 'reply_to_message', 'delivery_count',
            'read_count', 'reactions_summary'
        ]
    
    def get_reply_to_message(self, obj):
        """Get basic info about replied-to message"""
        if obj.reply_to:
            return {
                'id': obj.reply_to.id,
                'message_type': obj.reply_to.message_type,
                'sender': obj.reply_to.sender.get_full_name(),
                'created_at': obj.reply_to.created_at
            }
        return None
    
    def get_delivery_count(self, obj):
        """Get number of successful deliveries"""
        return obj.deliveries.filter(status='DELIVERED').count()
    
    def get_read_count(self, obj):
        """Get number of read receipts"""
        return obj.deliveries.filter(status='READ').count()
    
    def get_reactions_summary(self, obj):
        """Get summary of message reactions"""
        reactions = obj.reactions.values('reaction_type').annotate(
            count=models.Count('id')
        ).order_by('-count')
        return {reaction['reaction_type']: reaction['count'] for reaction in reactions}
    
    def create(self, validated_data):
        """Create message with encryption"""
        content = validated_data.pop('content', '')
        
        # Here you would encrypt the content
        # For now, we'll store it as-is (in production, implement proper encryption)
        validated_data['content_encrypted'] = content  # TODO: Implement encryption
        validated_data['content_hash'] = self._generate_content_hash(content)
        
        # Set sender from request
        validated_data['sender'] = self.context['request'].user
        
        return super().create(validated_data)
    
    def _generate_content_hash(self, content):
        """Generate SHA-256 hash of content"""
        import hashlib
        return hashlib.sha256(content.encode('utf-8')).hexdigest()


class MessageDeliverySerializer(serializers.ModelSerializer):
    """Serializer for MessageDelivery model"""
    
    recipient = MilitaryUserReadOnlySerializer(read_only=True)
    message_info = serializers.SerializerMethodField()
    
    class Meta:
        model = MessageDelivery
        fields = [
            'id', 'message', 'message_info', 'recipient', 'recipient_device',
            'status', 'delivery_attempts', 'sent_at', 'delivered_at', 'read_at',
            'failed_at', 'failure_reason', 'retry_after',
            'is_offline_delivery', 'offline_queued_at'
        ]
        read_only_fields = [
            'id', 'message_info', 'recipient', 'delivery_attempts',
            'sent_at', 'delivered_at', 'failed_at', 'offline_queued_at'
        ]
    
    def get_message_info(self, obj):
        """Get basic message information"""
        return {
            'id': obj.message.id,
            'message_type': obj.message.message_type,
            'sender': obj.message.sender.get_full_name(),
            'created_at': obj.message.created_at,
            'priority': obj.message.priority
        }


class MessageReactionSerializer(serializers.ModelSerializer):
    """Serializer for MessageReaction model"""
    
    user = MilitaryUserReadOnlySerializer(read_only=True)
    reaction_display = serializers.CharField(source='get_reaction_type_display', read_only=True)
    
    class Meta:
        model = MessageReaction
        fields = [
            'id', 'message', 'user', 'reaction_type', 'reaction_display', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'reaction_display', 'created_at']
    
    def create(self, validated_data):
        """Create reaction with current user"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ConversationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for conversation lists"""
    
    participant_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'conversation_id', 'name', 'conversation_type',
            'classification_level', 'participant_count',
            'is_archived', 'is_muted', 'created_at', 'last_message_at',
            'last_message', 'unread_count'
        ]
    
    def get_participant_count(self, obj):
        return obj.participants.count()
    
    def get_last_message(self, obj):
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            return {
                'sender': last_message.sender.get_full_name(),
                'message_type': last_message.message_type,
                'created_at': last_message.created_at
            }
        return None
    
    def get_unread_count(self, obj):
        # TODO: Implement proper unread count logic
        return 0


class MessageListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for message lists"""
    
    sender = MilitaryUserReadOnlySerializer(read_only=True)
    reactions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'message_id', 'message_type', 'sender', 'priority',
            'has_attachments', 'created_at', 'delivery_status',
            'reactions_count'
        ]
    
    def get_reactions_count(self, obj):
        return obj.reactions.count()