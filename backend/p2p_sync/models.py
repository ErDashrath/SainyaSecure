"""
Military Communication System - P2P Sync Models

This module defines models for peer-to-peer synchronization and offline-first operation:
- Peer discovery and mesh networking
- Offline message queues
- Sync conflict resolution
- Network topology management
"""

from django.db import models
from django.utils import timezone
from users.models import MilitaryUser, Device
from messaging.models import Message, Conversation
import uuid
import json


class PeerConnection(models.Model):
    """
    Track peer-to-peer connections between devices
    
    Features:
    - Mesh network topology
    - Connection quality monitoring
    - Relay routing capabilities
    - Trust and security scoring
    """
    
    CONNECTION_TYPES = [
        ('DIRECT', 'Direct Connection'),
        ('RELAY', 'Relayed Connection'),
        ('MESH', 'Mesh Network'),
        ('SATELLITE', 'Satellite Link'),
        ('RADIO', 'Radio Frequency'),
    ]
    
    CONNECTION_STATUS = [
        ('CONNECTED', 'Connected'),
        ('CONNECTING', 'Connecting'),
        ('DISCONNECTED', 'Disconnected'),
        ('FAILED', 'Connection Failed'),
        ('BLOCKED', 'Blocked'),
    ]
    
    SECURITY_LEVELS = [
        ('TRUSTED', 'Fully Trusted'),
        ('VERIFIED', 'Verified'),
        ('UNVERIFIED', 'Unverified'),
        ('SUSPICIOUS', 'Suspicious'),
        ('BLOCKED', 'Blocked'),
    ]
    
    # Connection identification
    connection_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    # Connected devices
    local_device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='outgoing_connections')
    remote_device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='incoming_connections')
    
    # Connection details
    connection_type = models.CharField(max_length=10, choices=CONNECTION_TYPES, default='DIRECT')
    status = models.CharField(max_length=12, choices=CONNECTION_STATUS, default='CONNECTING')
    
    # Network information
    local_ip = models.GenericIPAddressField(null=True, blank=True)
    remote_ip = models.GenericIPAddressField(null=True, blank=True)
    local_port = models.IntegerField(null=True, blank=True)
    remote_port = models.IntegerField(null=True, blank=True)
    
    # Connection quality metrics
    latency_ms = models.IntegerField(null=True, blank=True, help_text="Round-trip latency in milliseconds")
    bandwidth_kbps = models.IntegerField(null=True, blank=True, help_text="Available bandwidth in Kbps")
    packet_loss_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    signal_strength = models.IntegerField(null=True, blank=True, help_text="Signal strength (0-100)")
    
    # Security and trust
    security_level = models.CharField(max_length=12, choices=SECURITY_LEVELS, default='UNVERIFIED')
    trust_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.0, help_text="Trust score (0.0-1.0)")
    encryption_enabled = models.BooleanField(default=True)
    certificate_verified = models.BooleanField(default=False)
    
    # Routing capabilities
    can_relay = models.BooleanField(default=True, help_text="Can this peer relay messages")
    max_relay_hops = models.IntegerField(default=3)
    relay_priority = models.IntegerField(default=1, help_text="Relay priority (1=highest)")
    
    # Statistics
    messages_sent = models.IntegerField(default=0)
    messages_received = models.IntegerField(default=0)
    bytes_sent = models.BigIntegerField(default=0)
    bytes_received = models.BigIntegerField(default=0)
    connection_attempts = models.IntegerField(default=0)
    successful_connections = models.IntegerField(default=0)
    
    # Timestamps
    first_connected_at = models.DateTimeField(null=True, blank=True)
    last_connected_at = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Geographic information
    distance_meters = models.IntegerField(null=True, blank=True, help_text="Approximate distance between devices")
    last_known_location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    last_known_location_lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    class Meta:
        db_table = 'peer_connections'
        verbose_name = 'Peer Connection'
        verbose_name_plural = 'Peer Connections'
        unique_together = ('local_device', 'remote_device')
        indexes = [
            models.Index(fields=['local_device', 'status']),
            models.Index(fields=['security_level', 'trust_score']),
            models.Index(fields=['connection_type', 'status']),
            models.Index(fields=['last_seen_at']),
        ]
    
    def __str__(self):
        return f"{self.local_device.name} -> {self.remote_device.name} ({self.status})"
    
    def is_active(self):
        """Check if connection is active"""
        return self.status == 'CONNECTED'
    
    def calculate_reliability_score(self):
        """Calculate connection reliability score based on metrics"""
        if self.connection_attempts == 0:
            return 0.0
        
        success_rate = self.successful_connections / self.connection_attempts
        latency_score = max(0, 1 - (self.latency_ms or 0) / 1000)  # Normalize latency
        packet_loss_score = max(0, 1 - float(self.packet_loss_percent) / 100)
        
        return (success_rate * 0.4) + (latency_score * 0.3) + (packet_loss_score * 0.3)
    
    def update_quality_metrics(self, latency=None, bandwidth=None, packet_loss=None, signal_strength=None):
        """Update connection quality metrics"""
        if latency is not None:
            self.latency_ms = latency
        if bandwidth is not None:
            self.bandwidth_kbps = bandwidth
        if packet_loss is not None:
            self.packet_loss_percent = packet_loss
        if signal_strength is not None:
            self.signal_strength = signal_strength
        self.save(update_fields=['latency_ms', 'bandwidth_kbps', 'packet_loss_percent', 'signal_strength'])


class OfflineMessageQueue(models.Model):
    """
    Queue messages for offline delivery and sync
    
    Features:
    - Priority-based queuing
    - Retry logic and backoff
    - Partial sync support
    - Conflict resolution
    """
    
    QUEUE_STATUS = [
        ('PENDING', 'Pending Sync'),
        ('SYNCING', 'Currently Syncing'),
        ('SYNCED', 'Successfully Synced'),
        ('FAILED', 'Sync Failed'),
        ('CONFLICT', 'Sync Conflict'),
        ('EXPIRED', 'Expired'),
    ]
    
    PRIORITY_LEVELS = [
        ('CRITICAL', 'Critical'),
        ('HIGH', 'High'),
        ('NORMAL', 'Normal'),
        ('LOW', 'Low'),
    ]
    
    # Queue entry identification
    queue_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    # Device and message information
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='offline_message_queue')
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='sync_queue_entries')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='sync_queue_entries')
    
    # Queue properties
    priority = models.CharField(max_length=8, choices=PRIORITY_LEVELS, default='NORMAL')
    status = models.CharField(max_length=8, choices=QUEUE_STATUS, default='PENDING')
    
    # Sync metadata
    sync_attempts = models.IntegerField(default=0)
    max_sync_attempts = models.IntegerField(default=5)
    retry_delay_seconds = models.IntegerField(default=60)
    
    # Conflict resolution
    has_conflict = models.BooleanField(default=False)
    conflict_resolution_strategy = models.CharField(max_length=20, choices=[
        ('LOCAL_WINS', 'Local Version Wins'),
        ('REMOTE_WINS', 'Remote Version Wins'),
        ('MERGE', 'Attempt Merge'),
        ('MANUAL', 'Manual Resolution'),
    ], default='MANUAL')
    
    # Timestamps
    queued_at = models.DateTimeField(auto_now_add=True)
    last_sync_attempt_at = models.DateTimeField(null=True, blank=True)
    next_sync_attempt_at = models.DateTimeField(null=True, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Error tracking
    last_error = models.TextField(blank=True)
    error_count = models.IntegerField(default=0)
    
    # Sync context
    sync_context = models.JSONField(default=dict, help_text="Additional sync context data")
    checksum = models.CharField(max_length=64, help_text="Message checksum for integrity verification")
    
    class Meta:
        db_table = 'offline_message_queue'
        verbose_name = 'Offline Message Queue Entry'
        verbose_name_plural = 'Offline Message Queue Entries'
        ordering = ['-priority', 'queued_at']
        indexes = [
            models.Index(fields=['device', 'status']),
            models.Index(fields=['priority', 'queued_at']),
            models.Index(fields=['next_sync_attempt_at']),
            models.Index(fields=['has_conflict']),
        ]
    
    def __str__(self):
        return f"Queue Entry {self.queue_id} - {self.status} ({self.priority})"
    
    def can_retry(self):
        """Check if sync can be retried"""
        return (self.sync_attempts < self.max_sync_attempts and 
                self.status in ['PENDING', 'FAILED'] and
                (self.expires_at is None or timezone.now() < self.expires_at))
    
    def calculate_next_retry_time(self):
        """Calculate next retry time with exponential backoff"""
        if not self.can_retry():
            return None
        
        # Exponential backoff: base_delay * (2 ^ attempt_number)
        delay = self.retry_delay_seconds * (2 ** self.sync_attempts)
        return timezone.now() + timezone.timedelta(seconds=min(delay, 3600))  # Max 1 hour
    
    def mark_sync_failed(self, error_message):
        """Mark sync attempt as failed"""
        self.sync_attempts += 1
        self.error_count += 1
        self.last_error = error_message
        self.last_sync_attempt_at = timezone.now()
        
        if self.can_retry():
            self.next_sync_attempt_at = self.calculate_next_retry_time()
            self.status = 'FAILED'
        else:
            self.status = 'EXPIRED'
            self.next_sync_attempt_at = None
        
        self.save()


class SyncConflict(models.Model):
    """
    Track and resolve synchronization conflicts
    
    Features:
    - Conflict detection and analysis
    - Multiple resolution strategies
    - Manual review workflow
    - Audit trail for decisions
    """
    
    CONFLICT_TYPES = [
        ('MESSAGE_EDIT', 'Message Edit Conflict'),
        ('MESSAGE_DELETE', 'Message Delete Conflict'),
        ('TIMESTAMP', 'Timestamp Conflict'),
        ('DUPLICATE', 'Duplicate Message'),
        ('ORDERING', 'Message Ordering'),
        ('PERMISSION', 'Permission Conflict'),
    ]
    
    RESOLUTION_STATUS = [
        ('DETECTED', 'Conflict Detected'),
        ('ANALYZING', 'Analyzing Conflict'),
        ('PENDING_REVIEW', 'Pending Manual Review'),
        ('RESOLVED_AUTO', 'Resolved Automatically'),
        ('RESOLVED_MANUAL', 'Resolved Manually'),
        ('UNRESOLVED', 'Unresolved'),
    ]
    
    # Conflict identification
    conflict_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    conflict_type = models.CharField(max_length=15, choices=CONFLICT_TYPES)
    
    # Conflicting entities
    local_message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='local_conflicts')
    remote_message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='remote_conflicts', null=True, blank=True)
    affected_devices = models.ManyToManyField(Device, related_name='sync_conflicts')
    
    # Conflict details
    local_version_data = models.JSONField(help_text="Local version of conflicting data")
    remote_version_data = models.JSONField(help_text="Remote version of conflicting data")
    conflict_description = models.TextField()
    
    # Resolution
    resolution_status = models.CharField(max_length=15, choices=RESOLUTION_STATUS, default='DETECTED')
    resolution_strategy = models.CharField(max_length=20, blank=True)
    resolved_version_data = models.JSONField(default=dict, help_text="Final resolved version")
    
    # Manual review
    assigned_reviewer = models.ForeignKey(MilitaryUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_conflicts')
    reviewer_notes = models.TextField(blank=True)
    review_priority = models.CharField(max_length=8, choices=OfflineMessageQueue.PRIORITY_LEVELS, default='NORMAL')
    
    # Timestamps
    detected_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    review_deadline = models.DateTimeField(null=True, blank=True)
    
    # Impact assessment
    affects_security = models.BooleanField(default=False)
    affects_mission_critical = models.BooleanField(default=False)
    estimated_impact_level = models.CharField(max_length=8, choices=[
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ], default='LOW')
    
    class Meta:
        db_table = 'sync_conflicts'
        verbose_name = 'Sync Conflict'
        verbose_name_plural = 'Sync Conflicts'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['conflict_type', 'resolution_status']),
            models.Index(fields=['assigned_reviewer', 'resolution_status']),
            models.Index(fields=['affects_mission_critical', 'detected_at']),
            models.Index(fields=['review_deadline']),
        ]
    
    def __str__(self):
        return f"Conflict {self.conflict_id} - {self.conflict_type} ({self.resolution_status})"
    
    def is_resolved(self):
        """Check if conflict is resolved"""
        return self.resolution_status in ['RESOLVED_AUTO', 'RESOLVED_MANUAL']
    
    def needs_manual_review(self):
        """Check if conflict needs manual review"""
        return self.resolution_status in ['PENDING_REVIEW', 'ANALYZING']
    
    def is_overdue(self):
        """Check if manual review is overdue"""
        if self.review_deadline:
            return timezone.now() > self.review_deadline
        return False


class NetworkTopology(models.Model):
    """
    Track mesh network topology and routing
    
    Features:
    - Network graph representation
    - Route optimization
    - Network partition detection
    - Performance monitoring
    """
    
    # Topology snapshot identification
    topology_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    snapshot_time = models.DateTimeField(auto_now_add=True)
    
    # Network information
    total_nodes = models.IntegerField(default=0)
    connected_nodes = models.IntegerField(default=0)
    total_connections = models.IntegerField(default=0)
    network_diameter = models.IntegerField(default=0, help_text="Maximum shortest path between any two nodes")
    average_path_length = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    # Network health metrics
    connectivity_ratio = models.DecimalField(max_digits=3, decimal_places=2, default=0.0, help_text="Connected nodes / total nodes")
    clustering_coefficient = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    network_resilience_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    
    # Partitioning information
    has_partitions = models.BooleanField(default=False)
    partition_count = models.IntegerField(default=1)
    largest_partition_size = models.IntegerField(default=0)
    isolated_nodes = models.IntegerField(default=0)
    
    # Performance metrics
    average_latency_ms = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    total_bandwidth_kbps = models.BigIntegerField(default=0)
    message_delivery_success_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    # Geographic distribution
    coverage_area_km2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    geographic_center_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    geographic_center_lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Topology data (stored as JSON for complex analysis)
    adjacency_matrix = models.JSONField(default=dict, help_text="Network adjacency matrix")
    routing_table = models.JSONField(default=dict, help_text="Optimal routing paths")
    critical_nodes = models.JSONField(default=list, help_text="Nodes critical for network connectivity")
    
    class Meta:
        db_table = 'network_topology'
        verbose_name = 'Network Topology'
        verbose_name_plural = 'Network Topologies'
        ordering = ['-snapshot_time']
        indexes = [
            models.Index(fields=['snapshot_time']),
            models.Index(fields=['has_partitions', 'partition_count']),
            models.Index(fields=['connectivity_ratio']),
        ]
    
    def __str__(self):
        return f"Network Topology {self.snapshot_time} - {self.connected_nodes}/{self.total_nodes} nodes"
    
    def calculate_network_health(self):
        """Calculate overall network health score"""
        connectivity_score = float(self.connectivity_ratio)
        resilience_score = float(self.network_resilience_score)
        delivery_score = float(self.message_delivery_success_rate) / 100
        
        # Weighted average of key metrics
        health_score = (connectivity_score * 0.4) + (resilience_score * 0.3) + (delivery_score * 0.3)
        return round(health_score, 2)
    
    def is_network_partitioned(self):
        """Check if network is partitioned"""
        return self.has_partitions or self.partition_count > 1
    
    def get_critical_failure_points(self):
        """Get nodes whose failure would partition the network"""
        return self.critical_nodes


class P2PSyncStatus(models.Model):
    """
    Track P2P synchronization status per device
    
    Features:
    - Sync progress monitoring
    - Performance metrics
    - Error tracking and recovery
    - Bandwidth utilization
    """
    
    # Device identification
    device = models.OneToOneField(Device, on_delete=models.CASCADE, related_name='p2p_sync_status')
    
    # Sync status
    is_syncing = models.BooleanField(default=False)
    sync_mode = models.CharField(max_length=15, choices=[
        ('FULL', 'Full Sync'),
        ('INCREMENTAL', 'Incremental Sync'),
        ('PRIORITY', 'Priority Sync Only'),
        ('EMERGENCY', 'Emergency Sync'),
    ], default='INCREMENTAL')
    
    # Progress tracking
    pending_messages = models.IntegerField(default=0)
    synced_messages = models.IntegerField(default=0)
    failed_messages = models.IntegerField(default=0)
    sync_progress_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    # Performance metrics
    messages_per_second = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    bytes_per_second = models.BigIntegerField(default=0)
    average_message_size = models.IntegerField(default=0)
    
    # Network utilization
    bandwidth_used_kbps = models.IntegerField(default=0)
    bandwidth_limit_kbps = models.IntegerField(null=True, blank=True)
    connection_count = models.IntegerField(default=0)
    active_peer_count = models.IntegerField(default=0)
    
    # Error tracking
    consecutive_failures = models.IntegerField(default=0)
    last_error_message = models.TextField(blank=True)
    last_error_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    last_sync_start = models.DateTimeField(null=True, blank=True)
    last_sync_complete = models.DateTimeField(null=True, blank=True)
    estimated_completion = models.DateTimeField(null=True, blank=True)
    
    # Configuration
    auto_sync_enabled = models.BooleanField(default=True)
    sync_priority_threshold = models.CharField(max_length=8, choices=OfflineMessageQueue.PRIORITY_LEVELS, default='NORMAL')
    
    class Meta:
        db_table = 'p2p_sync_status'
        verbose_name = 'P2P Sync Status'
        verbose_name_plural = 'P2P Sync Statuses'
    
    def __str__(self):
        return f"P2P Sync Status for {self.device.name} - {self.sync_progress_percent}%"
    
    def calculate_eta(self):
        """Calculate estimated time to completion"""
        if self.messages_per_second > 0 and self.pending_messages > 0:
            seconds_remaining = self.pending_messages / self.messages_per_second
            return timezone.now() + timezone.timedelta(seconds=seconds_remaining)
        return None
    
    def is_sync_healthy(self):
        """Check if sync is operating normally"""
        return (self.consecutive_failures < 3 and 
                self.active_peer_count > 0 and
                (self.last_error_at is None or 
                 timezone.now() - self.last_error_at > timezone.timedelta(minutes=5)))
