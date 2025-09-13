"""
Military Communication System - AI Anomaly Detection Models

This module defines models for AI-powered anomaly detection:
- ML model management and versioning
- Real-time threat detection
- Behavioral analysis and scoring
- Alert management and escalation
"""

from django.db import models
from django.utils import timezone
from users.models import MilitaryUser, Device
from messaging.models import Message, Conversation
import uuid
import json


class AnomalyDetectionModel(models.Model):
    """
    AI/ML models used for anomaly detection
    
    Features:
    - Model versioning and deployment
    - Performance tracking
    - Model training and updates
    - A/B testing support
    """
    
    MODEL_TYPES = [
        ('DISTILBERT', 'DistilBERT NLP Model'),
        ('LSTM', 'LSTM Neural Network'),
        ('TRANSFORMER', 'Transformer Model'),
        ('RANDOM_FOREST', 'Random Forest'),
        ('SVM', 'Support Vector Machine'),
        ('ENSEMBLE', 'Ensemble Model'),
        ('RULE_BASED', 'Rule-Based System'),
    ]
    
    MODEL_STATUS = [
        ('TRAINING', 'Training in Progress'),
        ('TRAINED', 'Training Complete'),
        ('TESTING', 'Under Testing'),
        ('DEPLOYED', 'Deployed in Production'),
        ('DEPRECATED', 'Deprecated'),
        ('FAILED', 'Training/Deployment Failed'),
    ]
    
    # Model identification
    model_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=100, help_text="Human-readable model name")
    version = models.CharField(max_length=20, help_text="Model version (e.g., v1.2.3)")
    model_type = models.CharField(max_length=15, choices=MODEL_TYPES)
    
    # Model metadata
    description = models.TextField(help_text="Model description and purpose")
    training_objective = models.TextField(help_text="What this model is trained to detect")
    supported_languages = models.JSONField(default=list, help_text="Supported languages for NLP models")
    
    # Training information
    training_dataset_size = models.IntegerField(default=0, help_text="Number of training samples")
    training_started_at = models.DateTimeField(null=True, blank=True)
    training_completed_at = models.DateTimeField(null=True, blank=True)
    training_duration_hours = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Model configuration
    hyperparameters = models.JSONField(default=dict, help_text="Model hyperparameters")
    feature_config = models.JSONField(default=dict, help_text="Feature extraction configuration")
    preprocessing_steps = models.JSONField(default=list, help_text="Data preprocessing pipeline")
    
    # Model storage
    model_file_path = models.TextField(help_text="Path to serialized model file")
    model_size_bytes = models.BigIntegerField(default=0)
    checksum = models.CharField(max_length=64, help_text="Model file checksum")
    
    # Performance metrics
    accuracy = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    precision = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    recall = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    f1_score = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    false_positive_rate = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    false_negative_rate = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    
    # Deployment status
    status = models.CharField(max_length=10, choices=MODEL_STATUS, default='TRAINING')
    is_active = models.BooleanField(default=False, help_text="Currently active in production")
    deployment_priority = models.IntegerField(default=0, help_text="Deployment priority (higher = more priority)")
    
    # Usage statistics
    total_predictions = models.BigIntegerField(default=0)
    total_anomalies_detected = models.BigIntegerField(default=0)
    average_inference_time_ms = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deployed_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    # Model provenance
    trained_by = models.ForeignKey(MilitaryUser, on_delete=models.SET_NULL, null=True, blank=True)
    parent_model = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='derived_models')
    
    class Meta:
        db_table = 'anomaly_detection_models'
        verbose_name = 'Anomaly Detection Model'
        verbose_name_plural = 'Anomaly Detection Models'
        ordering = ['-version', '-created_at']
        indexes = [
            models.Index(fields=['model_type', 'status']),
            models.Index(fields=['is_active', 'deployment_priority']),
            models.Index(fields=['version']),
        ]
    
    def __str__(self):
        return f"{self.name} v{self.version} ({self.model_type})"
    
    def get_performance_summary(self):
        """Get formatted performance metrics"""
        return {
            'accuracy': float(self.accuracy or 0),
            'precision': float(self.precision or 0),
            'recall': float(self.recall or 0),
            'f1_score': float(self.f1_score or 0),
        }
    
    def is_production_ready(self):
        """Check if model meets production deployment criteria"""
        min_accuracy = 0.85
        min_precision = 0.80
        max_false_positive_rate = 0.05
        
        return (self.status == 'TRAINED' and
                (self.accuracy or 0) >= min_accuracy and
                (self.precision or 0) >= min_precision and
                (self.false_positive_rate or 1) <= max_false_positive_rate)


class AnomalyAlert(models.Model):
    """
    Anomaly detection alerts and notifications
    
    Features:
    - Multi-level threat classification
    - Alert escalation workflows
    - False positive tracking
    - Response and mitigation tracking
    """
    
    ALERT_TYPES = [
        ('CONTENT_ANOMALY', 'Suspicious Message Content'),
        ('BEHAVIORAL_ANOMALY', 'Unusual User Behavior'),
        ('TIMING_ANOMALY', 'Unusual Communication Timing'),
        ('VOLUME_ANOMALY', 'Abnormal Message Volume'),
        ('NETWORK_ANOMALY', 'Network Pattern Anomaly'),
        ('SPOOFING_ATTEMPT', 'Potential Identity Spoofing'),
        ('MALICIOUS_CONTENT', 'Potentially Malicious Content'),
        ('INFORMATION_LEAK', 'Potential Information Leak'),
        ('UNAUTHORIZED_ACCESS', 'Unauthorized Access Attempt'),
        ('SYSTEM_COMPROMISE', 'Potential System Compromise'),
    ]
    
    SEVERITY_LEVELS = [
        ('INFO', 'Informational'),
        ('LOW', 'Low Risk'),
        ('MEDIUM', 'Medium Risk'),
        ('HIGH', 'High Risk'),
        ('CRITICAL', 'Critical Threat'),
    ]
    
    ALERT_STATUS = [
        ('NEW', 'New Alert'),
        ('ACKNOWLEDGED', 'Acknowledged'),
        ('INVESTIGATING', 'Under Investigation'),
        ('RESOLVED', 'Resolved'),
        ('FALSE_POSITIVE', 'False Positive'),
        ('ESCALATED', 'Escalated'),
        ('SUPPRESSED', 'Suppressed'),
    ]
    
    # Alert identification
    alert_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    severity = models.CharField(max_length=8, choices=SEVERITY_LEVELS, default='MEDIUM')
    
    # Associated entities
    message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, blank=True, related_name='anomaly_alerts')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, null=True, blank=True, related_name='anomaly_alerts')
    user = models.ForeignKey(MilitaryUser, on_delete=models.CASCADE, null=True, blank=True, related_name='anomaly_alerts')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, null=True, blank=True, related_name='anomaly_alerts')
    
    # Detection information
    detected_by_model = models.ForeignKey(AnomalyDetectionModel, on_delete=models.CASCADE, related_name='alerts')
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4, help_text="Model confidence (0.0-1.0)")
    anomaly_score = models.DecimalField(max_digits=8, decimal_places=4, help_text="Anomaly score from model")
    detection_threshold = models.DecimalField(max_digits=5, decimal_places=4, help_text="Threshold used for detection")
    
    # Alert details
    title = models.CharField(max_length=200, help_text="Brief alert description")
    description = models.TextField(help_text="Detailed alert description")
    evidence = models.JSONField(default=dict, help_text="Supporting evidence and analysis")
    affected_entities = models.JSONField(default=list, help_text="List of affected users, devices, messages")
    
    # Context information
    detection_context = models.JSONField(default=dict, help_text="Context at time of detection")
    related_patterns = models.JSONField(default=list, help_text="Related anomalous patterns")
    risk_factors = models.JSONField(default=list, help_text="Identified risk factors")
    
    # Response and handling
    status = models.CharField(max_length=15, choices=ALERT_STATUS, default='NEW')
    assigned_to = models.ForeignKey(MilitaryUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_alerts')
    response_actions = models.JSONField(default=list, help_text="Actions taken in response")
    resolution_notes = models.TextField(blank=True)
    
    # Escalation
    escalation_level = models.IntegerField(default=0, help_text="Current escalation level")
    escalated_to = models.ForeignKey(MilitaryUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='escalated_alerts')
    auto_escalation_enabled = models.BooleanField(default=True)
    escalation_deadline = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    detected_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    
    # Impact assessment
    potential_impact = models.CharField(max_length=8, choices=SEVERITY_LEVELS, default='MEDIUM')
    business_impact_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    affects_mission_critical = models.BooleanField(default=False)
    
    # Machine learning feedback
    is_true_positive = models.BooleanField(null=True, blank=True, help_text="Human feedback for model training")
    feedback_provided_by = models.ForeignKey(MilitaryUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='provided_feedback')
    feedback_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'anomaly_alerts'
        verbose_name = 'Anomaly Alert'
        verbose_name_plural = 'Anomaly Alerts'
        ordering = ['-severity', '-detected_at']
        indexes = [
            models.Index(fields=['alert_type', 'severity']),
            models.Index(fields=['status', 'detected_at']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['detected_by_model', 'detected_at']),
            models.Index(fields=['affects_mission_critical', 'severity']),
        ]
    
    def __str__(self):
        return f"Alert {self.alert_id} - {self.title} ({self.severity})"
    
    def is_overdue(self):
        """Check if alert response is overdue"""
        if self.escalation_deadline and self.status in ['NEW', 'ACKNOWLEDGED']:
            return timezone.now() > self.escalation_deadline
        return False
    
    def calculate_priority_score(self):
        """Calculate overall priority score for alert triaging"""
        severity_weights = {'INFO': 1, 'LOW': 2, 'MEDIUM': 3, 'HIGH': 4, 'CRITICAL': 5}
        base_score = severity_weights.get(self.severity, 3)
        
        # Adjust for confidence
        confidence_multiplier = float(self.confidence_score)
        
        # Adjust for mission criticality
        mission_critical_bonus = 2 if self.affects_mission_critical else 0
        
        # Adjust for age (older alerts get higher priority)
        hours_old = (timezone.now() - self.detected_at).total_seconds() / 3600
        age_bonus = min(hours_old / 24, 1.0)  # Max 1.0 bonus after 24 hours
        
        return (base_score * confidence_multiplier) + mission_critical_bonus + age_bonus
    
    def get_recommended_actions(self):
        """Get recommended response actions based on alert type and severity"""
        actions = []
        
        if self.severity in ['HIGH', 'CRITICAL']:
            actions.extend([
                'Immediate investigation required',
                'Notify security team',
                'Consider communication isolation',
            ])
        
        if self.alert_type == 'SPOOFING_ATTEMPT':
            actions.extend([
                'Verify user identity',
                'Check device authentication',
                'Review recent access logs',
            ])
        elif self.alert_type == 'MALICIOUS_CONTENT':
            actions.extend([
                'Quarantine message',
                'Scan for malware',
                'Alert recipients',
            ])
        
        return actions


class BehavioralProfile(models.Model):
    """
    User behavioral profiles for anomaly detection
    
    Features:
    - Communication pattern analysis
    - Baseline behavior establishment
    - Drift detection over time
    - Privacy-preserving analytics
    """
    
    # Profile identification
    profile_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.OneToOneField(MilitaryUser, on_delete=models.CASCADE, related_name='behavioral_profile')
    
    # Profile period
    profile_start_date = models.DateTimeField()
    profile_end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    # Communication patterns
    avg_messages_per_day = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    avg_message_length = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    peak_activity_hours = models.JSONField(default=list, help_text="Hours of peak activity")
    typical_contacts = models.JSONField(default=list, help_text="Frequently contacted users")
    
    # Content patterns (privacy-preserving)
    common_keywords = models.JSONField(default=dict, help_text="Common keyword frequencies (anonymized)")
    message_types_distribution = models.JSONField(default=dict, help_text="Distribution of message types")
    conversation_types_distribution = models.JSONField(default=dict, help_text="Distribution of conversation types")
    
    # Device and location patterns
    primary_devices = models.JSONField(default=list, help_text="Most frequently used devices")
    typical_locations = models.JSONField(default=list, help_text="Common location patterns")
    mobility_patterns = models.JSONField(default=dict, help_text="Movement and mobility analysis")
    
    # Response patterns
    avg_response_time_seconds = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    response_time_distribution = models.JSONField(default=dict, help_text="Response time percentiles")
    online_hours_distribution = models.JSONField(default=dict, help_text="Online activity distribution")
    
    # Security patterns
    authentication_methods = models.JSONField(default=dict, help_text="Preferred authentication methods")
    security_events_frequency = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    suspicious_activity_baseline = models.DecimalField(max_digits=5, decimal_places=4, default=0.0)
    
    # Profile statistics
    total_messages_analyzed = models.BigIntegerField(default=0)
    profile_confidence_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    last_updated_at = models.DateTimeField(auto_now=True)
    
    # Drift detection
    profile_drift_score = models.DecimalField(max_digits=5, decimal_places=4, default=0.0)
    significant_drift_detected = models.BooleanField(default=False)
    last_drift_check = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'behavioral_profiles'
        verbose_name = 'Behavioral Profile'
        verbose_name_plural = 'Behavioral Profiles'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['profile_start_date', 'profile_end_date']),
            models.Index(fields=['significant_drift_detected']),
        ]
    
    def __str__(self):
        return f"Profile for {self.user.get_display_name()} ({self.profile_start_date.date()})"
    
    def is_current_profile(self):
        """Check if this is the current active profile for the user"""
        return self.is_active and timezone.now().date() <= self.profile_end_date.date()
    
    def needs_update(self, days_threshold=7):
        """Check if profile needs updating based on age"""
        days_since_update = (timezone.now() - self.last_updated_at).days
        return days_since_update >= days_threshold
    
    def calculate_deviation_score(self, current_behavior):
        """Calculate how much current behavior deviates from this profile"""
        # This would contain complex statistical analysis
        # For now, return a placeholder
        return 0.0


class ThreatIntelligence(models.Model):
    """
    External threat intelligence integration
    
    Features:
    - IOC (Indicators of Compromise) tracking
    - Threat actor profiling  
    - Attack pattern recognition
    - Intelligence source management
    """
    
    INTEL_TYPES = [
        ('IOC', 'Indicator of Compromise'),
        ('ATTACK_PATTERN', 'Attack Pattern'),
        ('THREAT_ACTOR', 'Threat Actor'),
        ('MALWARE', 'Malware Signature'),
        ('VULNERABILITY', 'Security Vulnerability'),
        ('TECHNIQUE', 'Attack Technique'),
    ]
    
    CONFIDENCE_LEVELS = [
        ('LOW', 'Low Confidence'),
        ('MEDIUM', 'Medium Confidence'),
        ('HIGH', 'High Confidence'),
        ('CONFIRMED', 'Confirmed'),
    ]
    
    # Intelligence identification
    intel_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    intel_type = models.CharField(max_length=15, choices=INTEL_TYPES)
    name = models.CharField(max_length=200, help_text="Threat intelligence name/title")
    
    # Intelligence content
    description = models.TextField()
    indicators = models.JSONField(default=list, help_text="List of indicators (hashes, IPs, domains, etc.)")
    tactics_techniques = models.JSONField(default=list, help_text="MITRE ATT&CK tactics and techniques")
    
    # Source information
    source_name = models.CharField(max_length=100, help_text="Intelligence source")
    source_reliability = models.CharField(max_length=10, choices=CONFIDENCE_LEVELS, default='MEDIUM')
    external_references = models.JSONField(default=list, help_text="External reference links")
    
    # Relevance and applicability
    confidence_level = models.CharField(max_length=10, choices=CONFIDENCE_LEVELS, default='MEDIUM')
    threat_level = models.CharField(max_length=8, choices=AnomalyAlert.SEVERITY_LEVELS, default='MEDIUM')
    applicability_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.5)
    
    # Detection rules
    detection_rules = models.JSONField(default=list, help_text="Automated detection rules")
    yara_rules = models.TextField(blank=True, help_text="YARA detection rules")
    regex_patterns = models.JSONField(default=list, help_text="Regular expression patterns")
    
    # Usage statistics
    times_matched = models.IntegerField(default=0)
    last_matched_at = models.DateTimeField(null=True, blank=True)
    false_positive_count = models.IntegerField(default=0)
    
    # Lifecycle management
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Related alerts
    related_alerts = models.ManyToManyField(AnomalyAlert, blank=True, related_name='related_intelligence')
    
    class Meta:
        db_table = 'threat_intelligence'
        verbose_name = 'Threat Intelligence'
        verbose_name_plural = 'Threat Intelligence'
        ordering = ['-threat_level', '-updated_at']
        indexes = [
            models.Index(fields=['intel_type', 'is_active']),
            models.Index(fields=['threat_level', 'confidence_level']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.intel_type}) - {self.threat_level}"
    
    def is_expired(self):
        """Check if intelligence has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def get_detection_effectiveness(self):
        """Calculate detection effectiveness ratio"""
        total_matches = self.times_matched
        if total_matches == 0:
            return 0.0
        return (total_matches - self.false_positive_count) / total_matches


class ModelPerformanceMetrics(models.Model):
    """
    Track model performance over time
    
    Features:
    - Performance trend analysis
    - Model drift detection
    - Comparative analysis
    - Automated retraining triggers
    """
    
    # Metrics identification
    metrics_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    model = models.ForeignKey(AnomalyDetectionModel, on_delete=models.CASCADE, related_name='performance_metrics')
    
    # Time period
    measurement_date = models.DateTimeField(auto_now_add=True)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Basic performance metrics
    total_predictions = models.BigIntegerField(default=0)
    true_positives = models.BigIntegerField(default=0)
    false_positives = models.BigIntegerField(default=0)
    true_negatives = models.BigIntegerField(default=0)
    false_negatives = models.BigIntegerField(default=0)
    
    # Calculated metrics
    accuracy = models.DecimalField(max_digits=5, decimal_places=4, default=0.0)
    precision = models.DecimalField(max_digits=5, decimal_places=4, default=0.0)
    recall = models.DecimalField(max_digits=5, decimal_places=4, default=0.0)
    f1_score = models.DecimalField(max_digits=5, decimal_places=4, default=0.0)
    specificity = models.DecimalField(max_digits=5, decimal_places=4, default=0.0)
    
    # Performance trends
    accuracy_trend = models.CharField(max_length=10, choices=[
        ('IMPROVING', 'Improving'),
        ('STABLE', 'Stable'),
        ('DECLINING', 'Declining'),
    ], default='STABLE')
    
    # Operational metrics
    average_inference_time_ms = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    max_inference_time_ms = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    throughput_per_second = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    
    # Resource utilization
    cpu_usage_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    memory_usage_mb = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    gpu_usage_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Model drift indicators
    data_drift_score = models.DecimalField(max_digits=5, decimal_places=4, default=0.0)
    concept_drift_score = models.DecimalField(max_digits=5, decimal_places=4, default=0.0)
    drift_detected = models.BooleanField(default=False)
    
    # Quality indicators
    user_satisfaction_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    alert_quality_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    
    # Retraining indicators
    needs_retraining = models.BooleanField(default=False)
    retraining_priority = models.CharField(max_length=8, choices=[
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ], default='LOW')
    
    class Meta:
        db_table = 'model_performance_metrics'
        verbose_name = 'Model Performance Metrics'
        verbose_name_plural = 'Model Performance Metrics'
        ordering = ['-measurement_date']
        indexes = [
            models.Index(fields=['model', 'measurement_date']),
            models.Index(fields=['drift_detected']),
            models.Index(fields=['needs_retraining', 'retraining_priority']),
        ]
    
    def __str__(self):
        return f"Metrics for {self.model.name} - {self.measurement_date.date()}"
    
    def calculate_metrics(self):
        """Calculate derived metrics from confusion matrix"""
        total = self.true_positives + self.false_positives + self.true_negatives + self.false_negatives
        
        if total > 0:
            self.accuracy = (self.true_positives + self.true_negatives) / total
        
        if (self.true_positives + self.false_positives) > 0:
            self.precision = self.true_positives / (self.true_positives + self.false_positives)
        
        if (self.true_positives + self.false_negatives) > 0:
            self.recall = self.true_positives / (self.true_positives + self.false_negatives)
        
        if self.precision and self.recall and (self.precision + self.recall) > 0:
            self.f1_score = 2 * (self.precision * self.recall) / (self.precision + self.recall)
        
        if (self.true_negatives + self.false_positives) > 0:
            self.specificity = self.true_negatives / (self.true_negatives + self.false_positives)
    
    def is_performance_degraded(self, threshold=0.05):
        """Check if performance has degraded significantly"""
        return (self.drift_detected or 
                self.accuracy_trend == 'DECLINING' or
                float(self.data_drift_score) > threshold)
