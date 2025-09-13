"""
Military Communication System - Messaging Models

This module defines models for secure military messaging including:
- End-to-end encrypted messages (text, voice, video)
- Message threading and conversations
- File attachments and media
- Message delivery and read receipts
- Priority and classification levels
"""

from django.db import models
from django.utils import timezone
from users.models import MilitaryUser, Device
import uuid
import hashlib


class Conversation(models.Model):
    """
    Conversation thread between military personnel
    
    Features:
    - Group conversations and channels
    - Security classification levels
    - Conversation metadata and archiving
    """
    
    CONVERSATION_TYPES = [
        ('DIRECT', 'Direct Message'),
        ('GROUP', 'Group Conversation'),
        ('CHANNEL', 'Channel/Broadcast'),
        ('EMERGENCY', 'Emergency Channel'),
        ('COMMAND', 'Command Channel'),
    ]
    
    CLASSIFICATION_LEVELS = [
        ('UNCLASSIFIED', 'Unclassified'),
        ('CONFIDENTIAL', 'Confidential'),
        ('SECRET', 'Secret'),
        ('TOP_SECRET', 'Top Secret'),
    ]
    
    # Basic information
    conversation_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=200, help_text="Conversation name/title")
    description = models.TextField(blank=True, help_text="Conversation description")
    conversation_type = models.CharField(max_length=15, choices=CONVERSATION_TYPES, default='DIRECT')
    
    # Participants
    participants = models.ManyToManyField(MilitaryUser, related_name='conversations')
    admin_users = models.ManyToManyField(MilitaryUser, related_name='admin_conversations', blank=True)
    
    # Security
    classification_level = models.CharField(max_length=15, choices=CLASSIFICATION_LEVELS, default='UNCLASSIFIED')
    required_clearance = models.CharField(max_length=20, blank=True, help_text="Minimum clearance required")
    encryption_key_id = models.CharField(max_length=100, help_text="Conversation encryption key identifier")
    
    # Settings
    is_archived = models.BooleanField(default=False)
    is_muted = models.BooleanField(default=False)
    auto_delete_after = models.IntegerField(null=True, blank=True, help_text="Auto-delete messages after N days")
    
    # Metadata
    created_by = models.ForeignKey(MilitaryUser, on_delete=models.CASCADE, related_name='created_conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'conversations'
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'
        indexes = [
            models.Index(fields=['conversation_type', 'classification_level']),
            models.Index(fields=['created_by', 'created_at']),
            models.Index(fields=['last_message_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_conversation_type_display()})"
    
    def get_participant_count(self):
        """Get number of participants in conversation"""
        return self.participants.count()
    
    def can_user_access(self, user):
        """Check if user can access this conversation"""
        if not user.can_access_clearance_level(self.required_clearance):
            return False
        return user in self.participants.all()


class Message(models.Model):
    """
    Individual messages within conversations
    
    Features:
    - End-to-end encryption
    - Multiple message types (text, voice, video, file)
    - Priority levels and delivery tracking
    - Message threading and replies
    """
    
    MESSAGE_TYPES = [
        ('TEXT', 'Text Message'),
        ('VOICE', 'Voice Message'),
        ('VIDEO', 'Video Message'),
        ('FILE', 'File Attachment'),
        ('IMAGE', 'Image'),
        ('LOCATION', 'Location Share'),
        ('COMMAND', 'Command Message'),
        ('ALERT', 'Alert/Notification'),
    ]
    
    PRIORITY_LEVELS = [
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
        ('CRITICAL', 'Critical'),
    ]
    
    DELIVERY_STATUS = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('DELIVERED', 'Delivered'),
        ('READ', 'Read'),
        ('FAILED', 'Failed'),
    ]
    
    # Basic message information
    message_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(MilitaryUser, on_delete=models.CASCADE, related_name='sent_messages')
    sender_device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='sent_messages')
    
    # Message content (encrypted)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='TEXT')
    content_encrypted = models.TextField(help_text="Encrypted message content")
    content_hash = models.CharField(max_length=64, help_text="SHA-256 hash of original content")
    
    # Metadata
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='NORMAL')
    is_edited = models.BooleanField(default=False)
    edit_count = models.IntegerField(default=0)
    
    # Threading and replies
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    thread_id = models.UUIDField(null=True, blank=True, help_text="Thread identifier for message grouping")
    
    # File attachments
    has_attachments = models.BooleanField(default=False)
    attachment_count = models.IntegerField(default=0)
    
    # Location data (if applicable)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_name = models.CharField(max_length=200, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Message expiration time")
    
    # Delivery tracking
    delivery_status = models.CharField(max_length=10, choices=DELIVERY_STATUS, default='PENDING')
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Offline sync
    is_offline_message = models.BooleanField(default=False)
    offline_created_at = models.DateTimeField(null=True, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'messages'
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
            models.Index(fields=['message_type', 'priority']),
            models.Index(fields=['delivery_status']),
            models.Index(fields=['thread_id']),
        ]
    
    def __str__(self):
        return f"Message {self.message_id} from {self.sender.get_display_name()}"
    
    def save(self, *args, **kwargs):
        """Override save to update conversation last_message_at"""
        super().save(*args, **kwargs)
        self.conversation.last_message_at = self.created_at
        self.conversation.save(update_fields=['last_message_at'])
    
    def generate_content_hash(self, content):
        """Generate SHA-256 hash of message content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def is_expired(self):
        """Check if message has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class MessageAttachment(models.Model):
    """
    File attachments for messages
    
    Features:
    - Encrypted file storage
    - File type validation
    - Size limits and compression
    - Virus scanning integration
    """
    
    ATTACHMENT_TYPES = [
        ('DOCUMENT', 'Document'),
        ('IMAGE', 'Image'),
        ('VIDEO', 'Video'),
        ('AUDIO', 'Audio'),
        ('ARCHIVE', 'Archive'),
        ('OTHER', 'Other'),
    ]
    
    # Basic information
    attachment_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    
    # File information
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=ATTACHMENT_TYPES)
    mime_type = models.CharField(max_length=100)
    file_size = models.BigIntegerField(help_text="File size in bytes")
    
    # Encrypted file storage
    file_path_encrypted = models.TextField(help_text="Encrypted file path")
    encryption_key_id = models.CharField(max_length=100)
    file_hash = models.CharField(max_length=64, help_text="SHA-256 hash of original file")
    
    # Security scanning
    virus_scan_status = models.CharField(max_length=10, choices=[
        ('PENDING', 'Pending'),
        ('CLEAN', 'Clean'),
        ('INFECTED', 'Infected'),
        ('ERROR', 'Scan Error'),
    ], default='PENDING')
    scan_date = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    uploaded_by = models.ForeignKey(MilitaryUser, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    download_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'message_attachments'
        verbose_name = 'Message Attachment'
        verbose_name_plural = 'Message Attachments'
        indexes = [
            models.Index(fields=['message', 'file_type']),
            models.Index(fields=['virus_scan_status']),
        ]
    
    def __str__(self):
        return f"{self.filename} ({self.get_file_type_display()})"


class MessageDelivery(models.Model):
    """
    Track message delivery status for each recipient
    
    Features:
    - Per-recipient delivery tracking
    - Read receipts
    - Delivery failure handling
    - Offline delivery queuing
    """
    
    # Delivery information
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='deliveries')
    recipient = models.ForeignKey(MilitaryUser, on_delete=models.CASCADE, related_name='received_messages')
    recipient_device = models.ForeignKey(Device, on_delete=models.CASCADE, null=True, blank=True)
    
    # Delivery status
    status = models.CharField(max_length=10, choices=Message.DELIVERY_STATUS, default='PENDING')
    delivery_attempts = models.IntegerField(default=0)
    
    # Timestamps
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    failure_reason = models.CharField(max_length=200, blank=True)
    retry_after = models.DateTimeField(null=True, blank=True)
    
    # Offline handling
    is_offline_delivery = models.BooleanField(default=False)
    offline_queued_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'message_deliveries'
        verbose_name = 'Message Delivery'
        verbose_name_plural = 'Message Deliveries'
        unique_together = ('message', 'recipient')
        indexes = [
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['message', 'status']),
            models.Index(fields=['is_offline_delivery']),
        ]
    
    def __str__(self):
        return f"Delivery to {self.recipient.get_display_name()} - {self.status}"


class MessageReaction(models.Model):
    """
    Message reactions (like, acknowledge, etc.)
    
    Features:
    - Emoji reactions
    - Military-specific reactions (acknowledge, understood, etc.)
    - Reaction analytics
    """
    
    REACTION_TYPES = [
        ('LIKE', '👍'),
        ('DISLIKE', '👎'),
        ('ACKNOWLEDGE', '✅'),
        ('UNDERSTOOD', '👌'),
        ('URGENT', '🚨'),
        ('QUESTION', '❓'),
        ('IMPORTANT', '⚠️'),
        ('COMPLETED', '✔️'),
    ]
    
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(MilitaryUser, on_delete=models.CASCADE, related_name='message_reactions')
    reaction_type = models.CharField(max_length=12, choices=REACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'message_reactions'
        verbose_name = 'Message Reaction'
        verbose_name_plural = 'Message Reactions'
        unique_together = ('message', 'user', 'reaction_type')
        indexes = [
            models.Index(fields=['message', 'reaction_type']),
        ]
    
    def __str__(self):
        return f"{self.get_reaction_type_display()} by {self.user.get_display_name()}"
