"""
Military Communication System - Users Serializers

This module defines the DRF serializers for user-related models.
Handles data serialization/deserialization with validation and security features.
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import MilitaryUser, Device, UserSession, SecurityEvent


class MilitaryUserSerializer(serializers.ModelSerializer):
    """Serializer for MilitaryUser model with security considerations"""
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    private_key_encrypted = serializers.CharField(write_only=True)
    
    class Meta:
        model = MilitaryUser
        fields = [
            'id', 'username', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'full_name',
            'military_id', 'rank', 'unit', 'branch', 'clearance_level',
            'secure_phone', 'emergency_contact', 'current_deployment',
            'public_key', 'private_key_encrypted', 'last_key_rotation',
            'is_active_duty', 'is_deployed', 'last_seen',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_seen', 'created_at', 'updated_at', 'last_key_rotation']
        extra_kwargs = {
            'email': {'required': True},
            'military_id': {'required': True},
        }
    
    def validate(self, attrs):
        """Custom validation for password confirmation and military data"""
        if 'password' in attrs and 'confirm_password' in attrs:
            if attrs['password'] != attrs['confirm_password']:
                raise serializers.ValidationError("Password fields didn't match.")
        
        # Remove confirm_password from attrs as it's not a model field
        attrs.pop('confirm_password', None)
        return attrs
    
    def create(self, validated_data):
        """Create user with encrypted password and initialize security fields"""
        password = validated_data.pop('password')
        user = MilitaryUser.objects.create_user(**validated_data)
        user.set_password(password)
        user.last_key_rotation = timezone.now()
        user.save()
        return user
    
    def update(self, instance, validated_data):
        """Update user with password handling"""
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class MilitaryUserReadOnlySerializer(serializers.ModelSerializer):
    """Read-only serializer for public user information"""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = MilitaryUser
        fields = [
            'id', 'username', 'full_name', 'military_id', 'rank', 
            'unit', 'branch', 'clearance_level', 'is_active_duty', 
            'is_deployed', 'last_seen'
        ]
        read_only_fields = '__all__'


class DeviceSerializer(serializers.ModelSerializer):
    """Serializer for Device model with validation"""
    
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    device_type_display = serializers.CharField(source='get_device_type_display', read_only=True)
    
    class Meta:
        model = Device
        fields = [
            'id', 'device_id', 'name', 'device_type', 'device_type_display',
            'serial_number', 'owner', 'owner_name', 'assigned_unit',
            'hardware_fingerprint', 'firmware_version', 'encryption_capabilities',
            'supports_voice', 'supports_video', 'supports_text',
            'supports_file_transfer', 'supports_p2p',
            'last_known_latitude', 'last_known_longitude', 'last_known_location',
            'connectivity_status', 'status', 'status_display',
            'last_heartbeat', 'last_sync', 'battery_level',
            'registered_at', 'last_updated'
        ]
        read_only_fields = [
            'id', 'device_id', 'registered_at', 'last_updated',
            'owner_name', 'status_display', 'device_type_display'
        ]
    
    def validate_serial_number(self, value):
        """Ensure serial number uniqueness"""
        if self.instance:
            # Update case - exclude current instance from uniqueness check
            if Device.objects.exclude(pk=self.instance.pk).filter(serial_number=value).exists():
                raise serializers.ValidationError("Device with this serial number already exists.")
        else:
            # Create case
            if Device.objects.filter(serial_number=value).exists():
                raise serializers.ValidationError("Device with this serial number already exists.")
        return value
    
    def validate_battery_level(self, value):
        """Validate battery level range"""
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("Battery level must be between 0 and 100.")
        return value


class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer for UserSession model"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    device_name = serializers.CharField(source='device.name', read_only=True)
    login_method_display = serializers.CharField(source='get_login_method_display', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSession
        fields = [
            'id', 'session_id', 'user', 'user_name', 'device', 'device_name',
            'ip_address', 'user_agent', 'login_method', 'login_method_display',
            'is_active', 'started_at', 'last_activity', 'ended_at',
            'suspicious_activity', 'force_logout_reason', 'duration'
        ]
        read_only_fields = [
            'id', 'session_id', 'started_at', 'last_activity',
            'user_name', 'device_name', 'login_method_display', 'duration'
        ]
    
    def get_duration(self, obj):
        """Calculate session duration"""
        if obj.ended_at:
            return (obj.ended_at - obj.started_at).total_seconds()
        elif obj.is_active:
            return (timezone.now() - obj.started_at).total_seconds()
        return None


class SecurityEventSerializer(serializers.ModelSerializer):
    """Serializer for SecurityEvent model"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    device_name = serializers.CharField(source='device.name', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.get_full_name', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    resolution_time = serializers.SerializerMethodField()
    
    class Meta:
        model = SecurityEvent
        fields = [
            'id', 'event_type', 'event_type_display', 'severity', 'severity_display',
            'description', 'user', 'user_name', 'device', 'device_name',
            'session', 'ip_address', 'user_agent', 'additional_data',
            'is_resolved', 'resolved_by', 'resolved_by_name', 'resolution_notes',
            'timestamp', 'resolved_at', 'resolution_time'
        ]
        read_only_fields = [
            'id', 'timestamp', 'user_name', 'device_name', 'resolved_by_name',
            'event_type_display', 'severity_display', 'resolution_time'
        ]
    
    def get_resolution_time(self, obj):
        """Calculate time to resolve the event"""
        if obj.resolved_at:
            return (obj.resolved_at - obj.timestamp).total_seconds()
        return None


class LoginSerializer(serializers.Serializer):
    """Serializer for user authentication"""
    
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})
    device_id = serializers.UUIDField(required=False)
    
    def validate(self, attrs):
        """Authenticate user credentials"""
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            if user.account_locked_until and user.account_locked_until > timezone.now():
                raise serializers.ValidationError('Account is temporarily locked.')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include username and password.')


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""
    
    old_password = serializers.CharField(style={'input_type': 'password'})
    new_password = serializers.CharField(style={'input_type': 'password'}, validators=[validate_password])
    confirm_password = serializers.CharField(style={'input_type': 'password'})
    
    def validate(self, attrs):
        """Validate password change data"""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("New password fields didn't match.")
        return attrs
    
    def validate_old_password(self, value):
        """Validate the old password"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Invalid old password.')
        return value