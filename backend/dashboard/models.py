"""
Military Communication System - Dashboard Models

This module defines models for command dashboard and analytics:
- Real-time system monitoring
- Mission analytics and reporting
- Command visibility and control
- Performance dashboards and KPIs
"""

from django.db import models
from django.utils import timezone
from users.models import MilitaryUser, Device
from messaging.models import Message, Conversation
from ai_anomaly.models import AnomalyAlert
import uuid
import json


class DashboardWidget(models.Model):
    """
    Configurable dashboard widgets for command center
    
    Features:
    - Customizable widget layouts
    - Real-time data visualization
    - Role-based widget access
    - Widget sharing and templates
    """
    
    WIDGET_TYPES = [
        ('MESSAGE_VOLUME', 'Message Volume Chart'),
        ('NETWORK_STATUS', 'Network Status Map'),
        ('ANOMALY_ALERTS', 'Security Alerts Panel'),
        ('DEVICE_STATUS', 'Device Status Grid'),
        ('USER_ACTIVITY', 'User Activity Timeline'),
        ('PERFORMANCE_METRICS', 'System Performance'),
        ('MISSION_PROGRESS', 'Mission Progress Tracker'),
        ('GEOGRAPHIC_MAP', 'Geographic Deployment Map'),
        ('COMMUNICATION_FLOW', 'Communication Flow Diagram'),
        ('THREAT_DASHBOARD', 'Threat Intelligence Dashboard'),
    ]
    
    WIDGET_SIZES = [
        ('SMALL', 'Small (1x1)'),
        ('MEDIUM', 'Medium (2x1)'),
        ('LARGE', 'Large (2x2)'),
        ('WIDE', 'Wide (3x1)'),
        ('EXTRA_LARGE', 'Extra Large (3x2)'),
    ]
    
    # Widget identification
    widget_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=100, help_text="Widget display name")
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    
    # Widget configuration
    title = models.CharField(max_length=200, help_text="Widget title displayed to users")
    description = models.TextField(blank=True, help_text="Widget description")
    size = models.CharField(max_length=12, choices=WIDGET_SIZES, default='MEDIUM')
    
    # Layout and positioning
    dashboard_row = models.IntegerField(default=0, help_text="Grid row position")
    dashboard_column = models.IntegerField(default=0, help_text="Grid column position")
    z_index = models.IntegerField(default=0, help_text="Layer order")
    
    # Widget data configuration
    data_source = models.CharField(max_length=100, help_text="Primary data source")
    data_filters = models.JSONField(default=dict, help_text="Data filtering configuration")
    refresh_interval_seconds = models.IntegerField(default=30, help_text="Auto-refresh interval")
    
    # Visualization settings
    chart_type = models.CharField(max_length=20, blank=True, help_text="Chart type for data visualization")
    color_scheme = models.CharField(max_length=20, default='military', help_text="Color scheme theme")
    display_options = models.JSONField(default=dict, help_text="Widget display customization")
    
    # Access control
    created_by = models.ForeignKey(MilitaryUser, on_delete=models.CASCADE, related_name='created_widgets')
    visible_to_roles = models.JSONField(default=list, help_text="Roles that can view this widget")
    required_clearance = models.CharField(max_length=20, blank=True, help_text="Minimum clearance required")
    
    # Widget state
    is_active = models.BooleanField(default=True)
    is_shared = models.BooleanField(default=False, help_text="Available to other users")
    last_data_update = models.DateTimeField(null=True, blank=True)
    
    # Performance tracking
    view_count = models.IntegerField(default=0)
    average_load_time_ms = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    error_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dashboard_widgets'
        verbose_name = 'Dashboard Widget'
        verbose_name_plural = 'Dashboard Widgets'
        ordering = ['dashboard_row', 'dashboard_column']
        indexes = [
            models.Index(fields=['widget_type', 'is_active']),
            models.Index(fields=['created_by', 'is_shared']),
            models.Index(fields=['dashboard_row', 'dashboard_column']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.widget_type})"
    
    def can_user_access(self, user):
        """Check if user has access to this widget"""
        if not user.can_access_clearance_level(self.required_clearance):
            return False
        
        if not self.visible_to_roles:
            return True  # No role restrictions
        
        # Check if user's role/branch is in allowed list
        return (user.branch in self.visible_to_roles or 
                user.rank in self.visible_to_roles)
    
    def get_current_data(self):
        """Get current widget data (to be implemented by specific widget types)"""
        # This would be implemented by widget-specific logic
        return {}


class SystemMetrics(models.Model):
    """
    System-wide performance and health metrics
    
    Features:
    - Real-time system monitoring
    - Performance trend analysis
    - Capacity planning support
    - Automated alerting thresholds
    """
    
    METRIC_CATEGORIES = [
        ('SYSTEM', 'System Performance'),
        ('NETWORK', 'Network Performance'),
        ('DATABASE', 'Database Performance'),
        ('MESSAGING', 'Messaging System'),
        ('SECURITY', 'Security Metrics'),
        ('USER_ACTIVITY', 'User Activity'),
        ('STORAGE', 'Storage Utilization'),
        ('BLOCKCHAIN', 'Blockchain Performance'),
    ]
    
    # Metrics identification
    metrics_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    category = models.CharField(max_length=15, choices=METRIC_CATEGORIES)
    metric_name = models.CharField(max_length=100, help_text="Specific metric name")
    
    # Measurement details
    timestamp = models.DateTimeField(auto_now_add=True)
    measurement_interval_seconds = models.IntegerField(default=60)
    
    # Metric values
    value = models.DecimalField(max_digits=20, decimal_places=6, help_text="Primary metric value")
    unit = models.CharField(max_length=20, help_text="Unit of measurement")
    min_value = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    max_value = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    avg_value = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    
    # Additional context
    device = models.ForeignKey(Device, on_delete=models.CASCADE, null=True, blank=True, related_name='system_metrics')
    tags = models.JSONField(default=dict, help_text="Additional metric tags")
    metadata = models.JSONField(default=dict, help_text="Additional metric metadata")
    
    # Alerting
    threshold_warning = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    threshold_critical = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    alert_triggered = models.BooleanField(default=False)
    
    # Data quality
    is_estimated = models.BooleanField(default=False, help_text="Value is estimated/interpolated")
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)
    
    class Meta:
        db_table = 'system_metrics'
        verbose_name = 'System Metrics'
        verbose_name_plural = 'System Metrics'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['category', 'metric_name', 'timestamp']),
            models.Index(fields=['device', 'timestamp']),
            models.Index(fields=['alert_triggered']),
        ]
    
    def __str__(self):
        return f"{self.category}: {self.metric_name} = {self.value} {self.unit}"
    
    def is_above_threshold(self, level='warning'):
        """Check if metric value exceeds threshold"""
        if level == 'warning' and self.threshold_warning:
            return float(self.value) > float(self.threshold_warning)
        elif level == 'critical' and self.threshold_critical:
            return float(self.value) > float(self.threshold_critical)
        return False
    
    def get_trend_indicator(self, previous_value):
        """Get trend indicator compared to previous value"""
        if previous_value is None:
            return 'stable'
        
        current = float(self.value)
        previous = float(previous_value)
        
        if current > previous * 1.05:  # 5% increase
            return 'increasing'
        elif current < previous * 0.95:  # 5% decrease
            return 'decreasing'
        else:
            return 'stable'


class MissionReport(models.Model):
    """
    Mission-specific communication reports and analytics
    
    Features:
    - Mission communication summaries
    - Operational effectiveness metrics
    - After-action reporting
    - Compliance and audit support
    """
    
    MISSION_STATUS = [
        ('PLANNING', 'Mission Planning'),
        ('ACTIVE', 'Mission Active'),
        ('COMPLETED', 'Mission Completed'),
        ('CANCELLED', 'Mission Cancelled'),
        ('ON_HOLD', 'Mission On Hold'),
    ]
    
    CLASSIFICATION_LEVELS = [
        ('UNCLASSIFIED', 'Unclassified'),
        ('CONFIDENTIAL', 'Confidential'),
        ('SECRET', 'Secret'),
        ('TOP_SECRET', 'Top Secret'),
    ]
    
    # Mission identification
    report_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    mission_name = models.CharField(max_length=200, help_text="Mission codename/identifier")
    mission_description = models.TextField(help_text="Mission description and objectives")
    
    # Mission details
    mission_commander = models.ForeignKey(MilitaryUser, on_delete=models.CASCADE, related_name='commanded_missions')
    participating_units = models.JSONField(default=list, help_text="Units involved in mission")
    mission_status = models.CharField(max_length=12, choices=MISSION_STATUS, default='PLANNING')
    classification_level = models.CharField(max_length=15, choices=CLASSIFICATION_LEVELS, default='CONFIDENTIAL')
    
    # Time period
    mission_start_time = models.DateTimeField()
    mission_end_time = models.DateTimeField(null=True, blank=True)
    report_period_start = models.DateTimeField()
    report_period_end = models.DateTimeField()
    
    # Communication statistics
    total_messages_sent = models.IntegerField(default=0)
    total_messages_received = models.IntegerField(default=0)
    voice_calls_count = models.IntegerField(default=0)
    video_calls_count = models.IntegerField(default=0)
    file_transfers_count = models.IntegerField(default=0)
    
    # Communication effectiveness
    message_delivery_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    average_response_time_seconds = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    communication_uptime_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    # Security metrics
    security_incidents_count = models.IntegerField(default=0)
    anomalies_detected_count = models.IntegerField(default=0)
    encryption_compliance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=100.0)
    
    # Network performance
    network_reliability_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    offline_periods_count = models.IntegerField(default=0)
    total_offline_duration_minutes = models.IntegerField(default=0)
    peer_connectivity_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    # Blockchain and audit
    blockchain_sync_success_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    audit_log_completeness = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    data_integrity_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    # Mission outcomes
    objectives_completed = models.IntegerField(default=0)
    total_objectives = models.IntegerField(default=0)
    mission_success_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    # Report metadata
    generated_by = models.ForeignKey(MilitaryUser, on_delete=models.CASCADE, related_name='generated_reports')
    generated_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(MilitaryUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_reports')
    approval_date = models.DateTimeField(null=True, blank=True)
    
    # Report content
    executive_summary = models.TextField(blank=True)
    key_findings = models.JSONField(default=list, help_text="Key findings and insights")
    recommendations = models.JSONField(default=list, help_text="Recommendations for improvement")
    lessons_learned = models.TextField(blank=True)
    
    # Attachments and evidence
    supporting_documents = models.JSONField(default=list, help_text="Supporting document references")
    data_sources = models.JSONField(default=list, help_text="Data sources used for report")
    
    class Meta:
        db_table = 'mission_reports'
        verbose_name = 'Mission Report'
        verbose_name_plural = 'Mission Reports'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['mission_commander', 'mission_status']),
            models.Index(fields=['mission_start_time', 'mission_end_time']),
            models.Index(fields=['classification_level']),
            models.Index(fields=['generated_at']),
        ]
    
    def __str__(self):
        return f"Mission Report: {self.mission_name} ({self.mission_status})"
    
    def calculate_overall_score(self):
        """Calculate overall mission communication effectiveness score"""
        scores = [
            float(self.message_delivery_rate),
            float(self.communication_uptime_percent),
            float(self.network_reliability_score),
            float(self.blockchain_sync_success_rate),
            float(self.data_integrity_score),
        ]
        
        # Filter out zero scores and calculate average
        valid_scores = [s for s in scores if s > 0]
        if valid_scores:
            return sum(valid_scores) / len(valid_scores)
        return 0.0
    
    def get_critical_issues(self):
        """Identify critical issues from the mission report"""
        issues = []
        
        if self.security_incidents_count > 0:
            issues.append(f"{self.security_incidents_count} security incidents")
        
        if float(self.communication_uptime_percent) < 95.0:
            issues.append(f"Low communication uptime: {self.communication_uptime_percent}%")
        
        if float(self.message_delivery_rate) < 90.0:
            issues.append(f"Low message delivery rate: {self.message_delivery_rate}%")
        
        if self.total_offline_duration_minutes > 30:
            issues.append(f"Extended offline periods: {self.total_offline_duration_minutes} minutes")
        
        return issues


class AlertSummary(models.Model):
    """
    Aggregated alert summaries for dashboard display
    
    Features:
    - Time-based alert aggregation
    - Trend analysis
    - Alert prioritization
    - Executive reporting
    """
    
    SUMMARY_PERIODS = [
        ('HOUR', 'Hourly'),
        ('DAY', 'Daily'),
        ('WEEK', 'Weekly'),
        ('MONTH', 'Monthly'),
    ]
    
    # Summary identification
    summary_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    period_type = models.CharField(max_length=5, choices=SUMMARY_PERIODS)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Alert counts by severity
    critical_alerts = models.IntegerField(default=0)
    high_alerts = models.IntegerField(default=0)
    medium_alerts = models.IntegerField(default=0)
    low_alerts = models.IntegerField(default=0)
    info_alerts = models.IntegerField(default=0)
    total_alerts = models.IntegerField(default=0)
    
    # Alert status breakdown
    new_alerts = models.IntegerField(default=0)
    acknowledged_alerts = models.IntegerField(default=0)
    investigating_alerts = models.IntegerField(default=0)
    resolved_alerts = models.IntegerField(default=0)
    false_positive_alerts = models.IntegerField(default=0)
    
    # Response metrics
    average_acknowledgment_time_minutes = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    average_resolution_time_minutes = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    overdue_alerts = models.IntegerField(default=0)
    
    # Alert types breakdown
    alert_types_distribution = models.JSONField(default=dict, help_text="Distribution by alert type")
    affected_systems = models.JSONField(default=list, help_text="Systems affected by alerts")
    top_alert_sources = models.JSONField(default=list, help_text="Top sources generating alerts")
    
    # Trend indicators
    alert_trend = models.CharField(max_length=10, choices=[
        ('INCREASING', 'Increasing'),
        ('STABLE', 'Stable'),
        ('DECREASING', 'Decreasing'),
    ], default='STABLE')
    
    severity_trend = models.CharField(max_length=10, choices=[
        ('ESCALATING', 'Escalating'),
        ('STABLE', 'Stable'),
        ('IMPROVING', 'Improving'),
    ], default='STABLE')
    
    # Performance indicators
    false_positive_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.0)
    alert_quality_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    response_efficiency_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    
    # Generation metadata
    generated_at = models.DateTimeField(auto_now_add=True)
    data_completeness_percent = models.DecimalField(max_digits=5, decimal_places=2, default=100.0)
    
    class Meta:
        db_table = 'alert_summaries'
        verbose_name = 'Alert Summary'
        verbose_name_plural = 'Alert Summaries'
        ordering = ['-period_start']
        unique_together = ('period_type', 'period_start', 'period_end')
        indexes = [
            models.Index(fields=['period_type', 'period_start']),
            models.Index(fields=['alert_trend', 'severity_trend']),
        ]
    
    def __str__(self):
        return f"Alert Summary {self.period_type} - {self.period_start.date()}"
    
    def calculate_alert_severity_score(self):
        """Calculate weighted alert severity score"""
        weights = {'critical': 5, 'high': 4, 'medium': 3, 'low': 2, 'info': 1}
        
        total_weighted = (
            self.critical_alerts * weights['critical'] +
            self.high_alerts * weights['high'] +
            self.medium_alerts * weights['medium'] +
            self.low_alerts * weights['low'] +
            self.info_alerts * weights['info']
        )
        
        if self.total_alerts > 0:
            return total_weighted / self.total_alerts
        return 0.0
    
    def get_priority_alerts_count(self):
        """Get count of high-priority alerts"""
        return self.critical_alerts + self.high_alerts
    
    def is_alert_storm(self, threshold_multiplier=3.0):
        """Detect if this period represents an alert storm"""
        # Compare with typical alert volume (would need historical data)
        # For now, use a simple threshold
        return self.total_alerts > (threshold_multiplier * 10)  # Placeholder logic


class UserActivitySummary(models.Model):
    """
    User activity summaries for dashboard analytics
    
    Features:
    - User engagement metrics
    - Communication patterns
    - Performance indicators
    - Behavioral insights
    """
    
    # Summary identification
    summary_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(MilitaryUser, on_delete=models.CASCADE, related_name='activity_summaries')
    
    # Time period
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    period_type = models.CharField(max_length=5, choices=AlertSummary.SUMMARY_PERIODS, default='DAY')
    
    # Communication activity
    messages_sent = models.IntegerField(default=0)
    messages_received = models.IntegerField(default=0)
    conversations_participated = models.IntegerField(default=0)
    voice_calls_made = models.IntegerField(default=0)
    voice_calls_received = models.IntegerField(default=0)
    files_shared = models.IntegerField(default=0)
    
    # Time metrics
    total_active_time_minutes = models.IntegerField(default=0)
    average_response_time_seconds = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    peak_activity_hour = models.IntegerField(null=True, blank=True)
    
    # Device usage
    primary_device_used = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True, 
                                          related_name='primary_usage_summaries')
    devices_used_count = models.IntegerField(default=0)
    device_switches = models.IntegerField(default=0)
    
    # Location and mobility
    locations_visited = models.IntegerField(default=0)
    total_distance_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    mobility_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    
    # Security and compliance
    security_events_count = models.IntegerField(default=0)
    failed_login_attempts = models.IntegerField(default=0)
    compliance_score = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)
    
    # Behavioral indicators
    communication_efficiency_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    collaboration_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    activity_pattern_consistency = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    
    # Anomaly indicators
    anomalous_behavior_detected = models.BooleanField(default=False)
    anomaly_score = models.DecimalField(max_digits=5, decimal_places=4, default=0.0)
    behavior_change_indicators = models.JSONField(default=list)
    
    # Generation metadata
    generated_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_activity_summaries'
        verbose_name = 'User Activity Summary'
        verbose_name_plural = 'User Activity Summaries'
        ordering = ['-period_start']
        unique_together = ('user', 'period_type', 'period_start')
        indexes = [
            models.Index(fields=['user', 'period_start']),
            models.Index(fields=['anomalous_behavior_detected']),
            models.Index(fields=['period_type', 'generated_at']),
        ]
    
    def __str__(self):
        return f"Activity Summary for {self.user.get_display_name()} - {self.period_start.date()}"
    
    def calculate_overall_activity_score(self):
        """Calculate overall user activity score"""
        # Weighted combination of different activity metrics
        message_score = min(self.messages_sent + self.messages_received, 100) / 100
        participation_score = min(self.conversations_participated, 10) / 10
        response_score = max(0, 1 - (float(self.average_response_time_seconds) / 3600))  # Normalize to 1 hour
        
        weights = {'messages': 0.4, 'participation': 0.3, 'responsiveness': 0.3}
        
        overall_score = (
            message_score * weights['messages'] +
            participation_score * weights['participation'] +
            response_score * weights['responsiveness']
        )
        
        return round(overall_score, 2)
    
    def get_activity_level(self):
        """Categorize user activity level"""
        total_communications = self.messages_sent + self.messages_received + self.voice_calls_made + self.voice_calls_received
        
        if total_communications >= 100:
            return 'very_high'
        elif total_communications >= 50:
            return 'high'
        elif total_communications >= 20:
            return 'medium'
        elif total_communications >= 5:
            return 'low'
        else:
            return 'very_low'
    
    def has_unusual_pattern(self):
        """Check for unusual activity patterns"""
        return (self.anomalous_behavior_detected or 
                self.anomaly_score > 0.7 or
                len(self.behavior_change_indicators) > 0)
