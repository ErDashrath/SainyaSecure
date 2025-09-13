"""
Command Center Models - Master Authority Database Models

Core models for the central command system:
- Master blockchain ledger (source of truth)
- Node connectivity tracking
- Mission audit trails
- Command authority permissions
- Encrypted message logs with decryption capabilities
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
import uuid
from utils.military_crypto import military_crypto, military_blockchain


class CommandNode(models.Model):
    """
    Represents a military node in the communication network
    Tracks connectivity status and synchronization state
    """
    NODE_STATUS = [
        ('ONLINE', 'Online'),
        ('OFFLINE', 'Offline'), 
        ('RESYNC', 'Resynchronizing'),
        ('COMPROMISED', 'Compromised'),
        ('MAINTENANCE', 'Under Maintenance'),
    ]
    
    NODE_TYPES = [
        ('COMMAND', 'Command Center'),
        ('FIELD', 'Field Unit'),
        ('MOBILE', 'Mobile Device'),
        ('RELAY', 'Relay Station'),
        ('SATELLITE', 'Satellite Link'),
    ]
    
    node_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    node_name = models.CharField(max_length=100)
    node_type = models.CharField(max_length=20, choices=NODE_TYPES)
    status = models.CharField(max_length=20, choices=NODE_STATUS, default='OFFLINE')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    last_seen = models.DateTimeField(auto_now=True)
    public_key = models.TextField(help_text="RSA public key for encryption")
    lamport_clock = models.BigIntegerField(default=0)
    vector_clock = models.JSONField(default=dict, help_text="Vector clock for conflict resolution")
    location_lat = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    location_lon = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    assigned_personnel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'command_nodes'
        ordering = ['-last_seen']
        
    def __str__(self):
        return f"{self.node_name} ({self.get_node_type_display()}) - {self.get_status_display()}"
    
    @property
    def is_online(self):
        """Check if node is currently online"""
        if self.status != 'ONLINE':
            return False
        # Consider node offline if not seen in last 5 minutes
        return (timezone.now() - self.last_seen).total_seconds() < 300


class MasterLedger(models.Model):
    """
    Master blockchain ledger - Source of Truth for all communications
    Immutable once written, contains all validated message transactions
    """
    TRANSACTION_TYPES = [
        ('MESSAGE', 'Message Transaction'),
        ('SYNC', 'Ledger Sync'),
        ('KEY_EXCHANGE', 'Key Exchange'),
        ('SYSTEM', 'System Event'),
        ('AUDIT', 'Audit Event'),
    ]
    
    block_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    block_height = models.BigIntegerField(unique=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    sender_node = models.ForeignKey(CommandNode, on_delete=models.PROTECT, related_name='sent_transactions')
    receiver_node = models.ForeignKey(CommandNode, on_delete=models.PROTECT, related_name='received_transactions', null=True, blank=True)
    message_hash = models.CharField(max_length=64, help_text="SHA-256 hash of encrypted payload")
    payload_encrypted = models.TextField(help_text="AES encrypted message payload")
    payload_decrypted = models.TextField(blank=True, help_text="Decrypted payload for authorized personnel")
    previous_hash = models.CharField(max_length=64)
    merkle_root = models.CharField(max_length=64)
    nonce = models.BigIntegerField(default=0)
    difficulty = models.IntegerField(default=1)
    timestamp = models.DateTimeField(auto_now_add=True)
    lamport_timestamp = models.BigIntegerField()
    vector_timestamp = models.JSONField(default=dict)
    digital_signature = models.TextField(help_text="RSA signature for authentication")
    is_validated = models.BooleanField(default=False)
    is_synced = models.BooleanField(default=True, help_text="True if synced from local ledger")
    sync_conflicts = models.JSONField(default=list, help_text="List of conflict resolution details")
    
    class Meta:
        db_table = 'master_ledger'
        ordering = ['-block_height']
        indexes = [
            models.Index(fields=['sender_node', '-timestamp']),
            models.Index(fields=['receiver_node', '-timestamp']),
            models.Index(fields=['message_hash']),
            models.Index(fields=['-timestamp']),
        ]
    
    def __str__(self):
        return f"Block #{self.block_height}: {self.transaction_type} from {self.sender_node.node_name}"
    
    def calculate_hash(self):
        """Calculate SHA-256 hash of block contents using military crypto"""
        block_data = {
            'sender_node': str(self.sender_node.node_id),
            'receiver_node': str(self.receiver_node.node_id) if self.receiver_node else '',
            'message_hash': self.message_hash,
            'previous_hash': self.previous_hash,
            'lamport_timestamp': self.lamport_timestamp,
            'nonce': self.nonce
        }
        return military_blockchain.calculate_block_hash(block_data)
    
    def save(self, *args, **kwargs):
        if not self.block_height:
            # Auto-assign block height
            last_block = MasterLedger.objects.order_by('-block_height').first()
            self.block_height = (last_block.block_height + 1) if last_block else 0
        super().save(*args, **kwargs)


class DecryptedMessage(models.Model):
    """
    Decrypted message content accessible only to authorized command personnel
    Links to master ledger entry for full audit trail
    """
    CLASSIFICATION_LEVELS = [
        ('UNCLASSIFIED', 'Unclassified'),
        ('RESTRICTED', 'Restricted'), 
        ('CONFIDENTIAL', 'Confidential'),
        ('SECRET', 'Secret'),
        ('TOP_SECRET', 'Top Secret'),
    ]
    
    MESSAGE_TYPES = [
        ('TEXT', 'Text Message'),
        ('VOICE', 'Voice Message'),
        ('VIDEO', 'Video Message'),
        ('FILE', 'File Transfer'),
        ('COMMAND', 'Command Directive'),
        ('ALERT', 'Alert/Emergency'),
    ]
    
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ledger_entry = models.OneToOneField(MasterLedger, on_delete=models.CASCADE, related_name='decrypted_content')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    classification = models.CharField(max_length=20, choices=CLASSIFICATION_LEVELS, default='RESTRICTED')
    subject = models.CharField(max_length=200, blank=True)
    content = models.TextField(help_text="Decrypted message content")
    code_words_used = models.JSONField(default=list, help_text="List of military code words detected")
    media_attachments = models.JSONField(default=list, help_text="List of media file metadata")
    decrypted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    decrypted_at = models.DateTimeField(auto_now_add=True)
    access_log = models.JSONField(default=list, help_text="Log of who accessed this decrypted content")
    
    class Meta:
        db_table = 'decrypted_messages'
        ordering = ['-decrypted_at']
        permissions = [
            ('view_classified', 'Can view classified messages'),
            ('view_secret', 'Can view secret messages'),
            ('view_top_secret', 'Can view top secret messages'),
        ]
    
    def __str__(self):
        return f"{self.get_message_type_display()}: {self.subject[:50]}..."
    
    def log_access(self, user, action='VIEW'):
        """Log access to this decrypted message for audit purposes"""
        access_entry = {
            'user_id': user.id,
            'username': user.username,
            'action': action,
            'timestamp': timezone.now().isoformat(),
            'ip_address': getattr(user, 'last_login_ip', None)
        }
        if not self.access_log:
            self.access_log = []
        self.access_log.append(access_entry)
        self.save(update_fields=['access_log'])


class CommandAlert(models.Model):
    """
    System alerts for command center monitoring
    Includes AI anomaly detection results and system status alerts
    """
    ALERT_TYPES = [
        ('SECURITY', 'Security Alert'),
        ('ANOMALY', 'AI Anomaly Detection'),
        ('SYSTEM', 'System Alert'),
        ('NODE_OFFLINE', 'Node Disconnected'),
        ('SYNC_CONFLICT', 'Synchronization Conflict'),
        ('UNAUTHORIZED_ACCESS', 'Unauthorized Access Attempt'),
        ('MESSAGE_INTEGRITY', 'Message Integrity Violation'),
    ]
    
    SEVERITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    alert_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    title = models.CharField(max_length=200)
    description = models.TextField()
    source_node = models.ForeignKey(CommandNode, on_delete=models.CASCADE, null=True, blank=True)
    related_ledger_entry = models.ForeignKey(MasterLedger, on_delete=models.CASCADE, null=True, blank=True)
    ai_confidence_score = models.FloatField(null=True, blank=True, help_text="AI confidence score for anomaly alerts")
    metadata = models.JSONField(default=dict, help_text="Additional alert metadata")
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'command_alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['alert_type', '-created_at']),
            models.Index(fields=['severity', '-created_at']),
            models.Index(fields=['is_resolved', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_severity_display()} {self.get_alert_type_display()}: {self.title}"


class MissionAudit(models.Model):
    """
    Mission audit trails for command replay and historical analysis
    Links to related ledger entries for complete mission communication history
    """
    MISSION_STATUS = [
        ('PLANNING', 'Planning'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('ABORTED', 'Aborted'),
        ('CLASSIFIED', 'Classified'),
    ]
    
    audit_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mission_name = models.CharField(max_length=200)
    mission_code = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=MISSION_STATUS)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    commanding_officer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    participating_nodes = models.ManyToManyField(CommandNode, related_name='missions')
    related_ledger_entries = models.ManyToManyField(MasterLedger, related_name='mission_audits')
    objectives = models.TextField()
    outcomes = models.TextField(blank=True)
    classification_level = models.CharField(max_length=20, choices=DecryptedMessage.CLASSIFICATION_LEVELS)
    audit_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'mission_audits'
        ordering = ['-start_time']
    
    def __str__(self):
        return f"Mission {self.mission_code}: {self.mission_name}"
    
    @property
    def total_communications(self):
        """Get total number of communications for this mission"""
        return self.related_ledger_entries.count()
    
    @property
    def mission_duration(self):
        """Calculate mission duration"""
        if self.end_time:
            return self.end_time - self.start_time
        return timezone.now() - self.start_time