"""
Military Communication System - Users Models

This module defines the core user and device models for the military communication system.
Handles soldier profiles, device registration, authentication, and role-based access control.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid


class MilitaryUser(AbstractUser):
    """Extended User model for military personnel with additional security features"""
    
    # Military-specific fields
    military_id = models.CharField(max_length=20, unique=True, help_text="Military ID number")
    rank = models.CharField(max_length=50, help_text="Military rank (e.g., Lieutenant, Captain)")
    unit = models.CharField(max_length=100, help_text="Military unit/division")
    branch = models.CharField(max_length=50, choices=[
        ('ARMY', 'Army'),
        ('NAVY', 'Navy'),
        ('AIRFORCE', 'Air Force'),
        ('MARINES', 'Marines'),
        ('SPECIAL_FORCES', 'Special Forces'),
        ('INTELLIGENCE', 'Intelligence'),
    ])
    
    # Security clearance
    clearance_level = models.CharField(max_length=20, choices=[
        ('CONFIDENTIAL', 'Confidential'),
        ('SECRET', 'Secret'),
        ('TOP_SECRET', 'Top Secret'),
        ('TOP_SECRET_SCI', 'Top Secret/SCI'),
    ])
    
    # Contact and location
    secure_phone = models.CharField(max_length=20, blank=True, null=True)
    emergency_contact = models.CharField(max_length=100, blank=True, null=True)
    current_deployment = models.CharField(max_length=100, blank=True, null=True)
    
    # Security fields
    public_key = models.TextField(help_text="RSA public key for message encryption")
    private_key_encrypted = models.TextField(help_text="Encrypted private key")
    last_key_rotation = models.DateTimeField(default=timezone.now)
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    
    # Status tracking
    is_active_duty = models.BooleanField(default=True)
    is_deployed = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'military_users'
        verbose_name = 'Military User'
        verbose_name_plural = 'Military Users'
        indexes = [
            models.Index(fields=['military_id']),
            models.Index(fields=['unit', 'branch']),
            models.Index(fields=['clearance_level']),
        ]
    
    def __str__(self):
        return f"{self.rank} {self.get_full_name()} ({self.military_id})"


class Device(models.Model):
    """Military devices registered in the communication system"""
    
    DEVICE_TYPES = [
        ('RADIO', 'Military Radio'),
        ('TABLET', 'Military Tablet'),
        ('LAPTOP', 'Secure Laptop'),
        ('SMARTPHONE', 'Secure Smartphone'),
        ('DRONE', 'Drone Communication Unit'),
        ('VEHICLE', 'Vehicle Communication System'),
        ('AIRCRAFT', 'Aircraft Communication System'),
        ('SATELLITE', 'Satellite Terminal'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('COMPROMISED', 'Compromised'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('DECOMMISSIONED', 'Decommissioned'),
    ]
    
    # Basic device information
    device_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=100, help_text="Device name/identifier")
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    serial_number = models.CharField(max_length=100, unique=True)
    
    # Ownership and assignment
    owner = models.ForeignKey(MilitaryUser, on_delete=models.CASCADE, related_name='devices')
    assigned_unit = models.CharField(max_length=100)
    
    # Technical specifications
    hardware_fingerprint = models.TextField(help_text="Unique hardware identifier")
    firmware_version = models.CharField(max_length=50)
    encryption_capabilities = models.JSONField(default=dict, help_text="Supported encryption methods")
    
    # Communication capabilities
    supports_voice = models.BooleanField(default=True)
    supports_video = models.BooleanField(default=False)
    supports_text = models.BooleanField(default=True)
    supports_file_transfer = models.BooleanField(default=True)
    supports_p2p = models.BooleanField(default=True)
    
    # Location and connectivity
    last_known_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    last_known_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    last_known_location = models.CharField(max_length=200, blank=True)
    connectivity_status = models.CharField(max_length=20, choices=[
        ('ONLINE', 'Online'),
        ('OFFLINE', 'Offline'),
        ('LIMITED', 'Limited Connectivity'),
        ('JAMMED', 'Communication Jammed'),
    ], default='OFFLINE')
    
    # Security and status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    battery_level = models.IntegerField(null=True, blank=True, help_text="Battery percentage (0-100)")
    
    # Timestamps
    registered_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'devices'
        verbose_name = 'Military Device'
        verbose_name_plural = 'Military Devices'
        indexes = [
            models.Index(fields=['device_id']),
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['device_type', 'connectivity_status']),
            models.Index(fields=['last_heartbeat']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.device_type})"


class UserSession(models.Model):
    """Track user sessions for security auditing"""
    
    user = models.ForeignKey(MilitaryUser, on_delete=models.CASCADE, related_name='sessions')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='sessions')
    session_id = models.UUIDField(default=uuid.uuid4, unique=True)
    
    # Session details
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    login_method = models.CharField(max_length=20, choices=[
        ('PASSWORD', 'Password'),
        ('BIOMETRIC', 'Biometric'),
        ('SMART_CARD', 'Smart Card'),
        ('MULTI_FACTOR', 'Multi-Factor'),
    ])
    
    # Session state
    is_active = models.BooleanField(default=True)
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # Security flags
    suspicious_activity = models.BooleanField(default=False)
    force_logout_reason = models.CharField(max_length=200, blank=True)
    
    class Meta:
        db_table = 'user_sessions'
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['device', 'is_active']),
            models.Index(fields=['started_at']),
        ]
    
    def __str__(self):
        return f"Session {self.session_id}"


class SecurityEvent(models.Model):
    """Log security events for auditing and monitoring"""
    
    EVENT_TYPES = [
        ('LOGIN_SUCCESS', 'Successful Login'),
        ('LOGIN_FAILED', 'Failed Login'),
        ('LOGOUT', 'Logout'),
        ('PASSWORD_CHANGE', 'Password Changed'),
        ('ACCOUNT_LOCKED', 'Account Locked'),
        ('SUSPICIOUS_ACTIVITY', 'Suspicious Activity'),
        ('UNAUTHORIZED_ACCESS', 'Unauthorized Access Attempt'),
        ('KEY_ROTATION', 'Encryption Key Rotation'),
        ('DEVICE_REGISTERED', 'Device Registered'),
        ('DEVICE_COMPROMISED', 'Device Compromised'),
        ('MESSAGE_ANOMALY', 'Message Anomaly Detected'),
    ]
    
    SEVERITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    # Event details
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='LOW')
    description = models.TextField()
    
    # Associated entities
    user = models.ForeignKey(MilitaryUser, on_delete=models.CASCADE, null=True, blank=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, null=True, blank=True)
    session = models.ForeignKey(UserSession, on_delete=models.CASCADE, null=True, blank=True)
    
    # Context information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    additional_data = models.JSONField(default=dict, help_text="Additional event context")
    
    # Processing status
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(MilitaryUser, on_delete=models.SET_NULL, 
                                   null=True, blank=True, related_name='resolved_events')
    resolution_notes = models.TextField(blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'security_events'
        verbose_name = 'Security Event'
        verbose_name_plural = 'Security Events'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', 'severity']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['device', 'timestamp']),
            models.Index(fields=['is_resolved']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.severity}"
