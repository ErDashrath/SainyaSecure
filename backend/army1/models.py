"""
Models for Army1 Frontend - Command Center Data Models
Supporting comprehensive CRUD operations for military operations
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class CommandMilitaryUser(models.Model):
    """Extended user model for military personnel with ranks and clearances"""
    RANK_CHOICES = [
        ('COMMAND', 'Command Authority'),
        ('OPERATIONS', 'Operations Officer'),
        ('INTELLIGENCE', 'Intelligence Officer'),  
        ('COMMUNICATIONS', 'Communications Specialist'),
        ('FIELD', 'Field Personnel'),
        ('EMERGENCY', 'Emergency Override'),
    ]
    
    CLEARANCE_LEVELS = [
        ('TOP_SECRET', 'Top Secret'),
        ('SECRET', 'Secret'),
        ('CONFIDENTIAL', 'Confidential'),
        ('RESTRICTED', 'Restricted'),
        ('UNCLASSIFIED', 'Unclassified'),
    ]
    
    BRANCHES = [
        ('ARMY', 'Army'),
        ('NAVY', 'Navy'),
        ('AIR_FORCE', 'Air Force'),
        ('MARINES', 'Marines'),
        ('COAST_GUARD', 'Coast Guard'),
        ('SPACE_FORCE', 'Space Force'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    military_id = models.CharField(max_length=20, unique=True)
    rank = models.CharField(max_length=20, choices=RANK_CHOICES, default='FIELD')
    branch = models.CharField(max_length=20, choices=BRANCHES, default='ARMY')
    clearance_level = models.CharField(max_length=20, choices=CLEARANCE_LEVELS, default='UNCLASSIFIED')
    unit = models.CharField(max_length=100, blank=True)
    deployment_status = models.CharField(max_length=50, default='ACTIVE')
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    requires_2fa = models.BooleanField(default=False)
    is_active_duty = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_rank_display()}"
    
    class Meta:
        db_table = 'command_military_users'
        verbose_name = 'Command Military User'
        verbose_name_plural = 'Command Military Users'


class CommandSecurityEvent(models.Model):
    """Security event logging for audit trails"""
    EVENT_TYPES = [
        ('LOGIN_SUCCESS', 'Login Success'),
        ('LOGIN_FAILED', 'Login Failed'),
        ('LOGOUT', 'Logout'),
        ('ACCESS_GRANTED', 'Access Granted'),
        ('ACCESS_DENIED', 'Access Denied'),
        ('SECURITY_VIOLATION', 'Security Violation'),
        ('PASSWORD_CHANGE', 'Password Change'),
        ('2FA_SUCCESS', '2FA Success'),
        ('2FA_FAILED', '2FA Failed'),
    ]
    
    SEVERITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='command_security_events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='LOW')
    description = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    module_accessed = models.CharField(max_length=50, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='command_resolved_events')
    
    def __str__(self):
        return f"{self.event_type} - {self.user.username} at {self.timestamp}"
    
    class Meta:
        db_table = 'command_security_events'
        ordering = ['-timestamp']
        verbose_name = 'Command Security Event'
        verbose_name_plural = 'Command Security Events'


class MilitaryMessage(models.Model):
    """Secure military messaging system"""
    PRIORITY_LEVELS = [
        ('LOW', 'Low Priority'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High Priority'),
        ('URGENT', 'Urgent'),
        ('FLASH', 'Flash Override'),
    ]
    
    CLASSIFICATION_LEVELS = [
        ('UNCLASSIFIED', 'Unclassified'),
        ('CONFIDENTIAL', 'Confidential'),
        ('SECRET', 'Secret'),
        ('TOP_SECRET', 'Top Secret'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent'),
        ('DELIVERED', 'Delivered'),
        ('READ', 'Read'),
        ('ARCHIVED', 'Archived'),
    ]
    
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_military_messages')
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='received_military_messages')
    subject = models.CharField(max_length=200)
    body = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='NORMAL')
    classification = models.CharField(max_length=15, choices=CLASSIFICATION_LEVELS, default='UNCLASSIFIED')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    is_encrypted = models.BooleanField(default=True)
    requires_receipt = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.subject} - {self.sender.username}"
    
    class Meta:
        db_table = 'military_messages'
        ordering = ['-created_at']
        verbose_name = 'Military Message'
        verbose_name_plural = 'Military Messages'


class Personnel(models.Model):
    """Personnel management and tracking"""
    STATUS_CHOICES = [
        ('ACTIVE', 'Active Duty'),
        ('DEPLOYED', 'Deployed'),
        ('RESERVE', 'Reserve'),
        ('TRAINING', 'Training'),
        ('MEDICAL', 'Medical Leave'),
        ('DISCHARGED', 'Discharged'),
    ]
    
    personnel_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    military_user = models.OneToOneField(CommandMilitaryUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    service_number = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField()
    enlistment_date = models.DateField()
    current_assignment = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ACTIVE')
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=20)
    medical_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.service_number})"
    
    class Meta:
        db_table = 'command_personnel'
        ordering = ['last_name', 'first_name']
        verbose_name = 'Personnel'
        verbose_name_plural = 'Personnel'


class MilitaryDevice(models.Model):
    """Device management for military equipment"""
    DEVICE_TYPES = [
        ('RADIO', 'Radio Equipment'),
        ('COMPUTER', 'Computer System'),
        ('PHONE', 'Secure Phone'),
        ('TABLET', 'Tablet Device'),
        ('SENSOR', 'Sensor Equipment'),
        ('VEHICLE', 'Vehicle System'),
        ('WEAPON', 'Weapon System'),
        ('OTHER', 'Other Equipment'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('REPAIR', 'Needs Repair'),
        ('RETIRED', 'Retired'),
        ('LOST', 'Lost/Stolen'),
    ]
    
    device_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    serial_number = models.CharField(max_length=50, unique=True)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    model = models.CharField(max_length=100)
    assigned_to = models.ForeignKey(Personnel, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ACTIVE')
    location = models.CharField(max_length=100)
    last_maintenance = models.DateField(null=True, blank=True)
    next_maintenance = models.DateField(null=True, blank=True)
    acquisition_date = models.DateField()
    acquisition_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_device_type_display()} - {self.serial_number}"
    
    class Meta:
        db_table = 'military_devices'
        ordering = ['-created_at']
        verbose_name = 'Military Device'
        verbose_name_plural = 'Military Devices'


class Mission(models.Model):
    """Mission planning and tracking"""
    STATUS_CHOICES = [
        ('PLANNING', 'Planning'),
        ('APPROVED', 'Approved'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('ON_HOLD', 'On Hold'),
    ]
    
    CLASSIFICATION_LEVELS = [
        ('UNCLASSIFIED', 'Unclassified'),
        ('CONFIDENTIAL', 'Confidential'),
        ('SECRET', 'Secret'),
        ('TOP_SECRET', 'Top Secret'),
    ]
    
    mission_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mission_name = models.CharField(max_length=200)
    mission_code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    classification = models.CharField(max_length=15, choices=CLASSIFICATION_LEVELS, default='UNCLASSIFIED')
    commander = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='commanded_missions')
    assigned_personnel = models.ManyToManyField(Personnel, related_name='assigned_missions')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PLANNING')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=200)
    objectives = models.TextField()
    resources_required = models.TextField()
    risk_assessment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.mission_name} ({self.mission_code})"
    
    class Meta:
        db_table = 'missions'
        ordering = ['-created_at']
        verbose_name = 'Mission'
        verbose_name_plural = 'Missions'


class SystemLog(models.Model):
    """Comprehensive system logging for command center"""
    LOG_LEVELS = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    CATEGORIES = [
        ('SYSTEM', 'System'),
        ('SECURITY', 'Security'),
        ('NETWORK', 'Network'),
        ('AUTH', 'Authentication'),
        ('APPLICATION', 'Application'),
        ('DATABASE', 'Database'),
    ]
    
    log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    level = models.CharField(max_length=10, choices=LOG_LEVELS, default='INFO')
    category = models.CharField(max_length=15, choices=CATEGORIES, default='SYSTEM')
    message = models.TextField()
    source = models.CharField(max_length=100)  # Module or component that generated the log
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    additional_data = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"[{self.level}] {self.category} - {self.message[:50]}"
    
    class Meta:
        db_table = 'command_system_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['level', 'category', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        verbose_name = 'System Log'
        verbose_name_plural = 'System Logs'


class OperationalLedger(models.Model):
    """Financial and resource tracking ledger"""
    TRANSACTION_TYPES = [
        ('BUDGET_ALLOCATION', 'Budget Allocation'),
        ('EQUIPMENT_PURCHASE', 'Equipment Purchase'),
        ('PERSONNEL_PAYMENT', 'Personnel Payment'),
        ('MAINTENANCE_COST', 'Maintenance Cost'),
        ('FUEL_EXPENSE', 'Fuel Expense'),
        ('TRAINING_COST', 'Training Cost'),
        ('OTHER', 'Other Expense'),
    ]
    
    ledger_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    authorized_by = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='authorized_transactions')
    cost_center = models.CharField(max_length=50)
    mission = models.ForeignKey(Mission, on_delete=models.SET_NULL, null=True, blank=True)
    device = models.ForeignKey(MilitaryDevice, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_date = models.DateField()
    fiscal_year = models.IntegerField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - ${self.amount}"
    
    class Meta:
        db_table = 'operational_ledger'
        ordering = ['-transaction_date']
        verbose_name = 'Operational Ledger Entry'
        verbose_name_plural = 'Operational Ledger'