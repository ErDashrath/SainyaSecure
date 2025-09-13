"""
Military Communication System - Users Views

This module defines the DRF ViewSets for user-related operations.
Implements secure CRUD operations using ViewSets, mixins, and custom permissions.
"""

from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import login, logout
from django.utils import timezone
from django.db.models import Q
import logging

from .models import MilitaryUser, Device, UserSession, SecurityEvent
from .serializers import (
    MilitaryUserSerializer, MilitaryUserReadOnlySerializer,
    DeviceSerializer, UserSessionSerializer, SecurityEventSerializer,
    LoginSerializer, PasswordChangeSerializer
)
from .permissions import MilitaryPermission, ClearanceLevelPermission


logger = logging.getLogger(__name__)


class MilitaryUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for MilitaryUser CRUD operations with military-specific permissions
    """
    queryset = MilitaryUser.objects.all()
    serializer_class = MilitaryUserSerializer
    permission_classes = [permissions.IsAuthenticated, MilitaryPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['branch', 'unit', 'clearance_level', 'rank', 'is_active_duty', 'is_deployed']
    search_fields = ['username', 'first_name', 'last_name', 'military_id', 'email']
    ordering_fields = ['rank', 'last_seen', 'created_at']
    ordering = ['-last_seen']
    
    def get_serializer_class(self):
        """Use read-only serializer for list and retrieve actions for non-privileged users"""
        if self.action in ['list', 'retrieve'] and not self.request.user.has_perm('users.change_militaryuser'):
            return MilitaryUserReadOnlySerializer
        return super().get_serializer_class()
    
    def get_queryset(self):
        """Filter queryset based on user's clearance level and permissions"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Superusers and staff can see all users
        if user.is_superuser or user.is_staff:
            return queryset
        
        # Users can see others in same or lower clearance level
        clearance_hierarchy = {
            'CONFIDENTIAL': 1,
            'SECRET': 2,
            'TOP_SECRET': 3,
            'TOP_SECRET_SCI': 4
        }
        
        user_clearance = clearance_hierarchy.get(user.clearance_level, 0)
        accessible_clearances = [
            level for level, value in clearance_hierarchy.items() 
            if value <= user_clearance
        ]
        
        return queryset.filter(
            Q(clearance_level__in=accessible_clearances) |
            Q(id=user.id)  # Always include self
        )
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Get current user's profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        """Change user's password"""
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            # Log security event
            SecurityEvent.objects.create(
                event_type='PASSWORD_CHANGE',
                severity='MEDIUM',
                description=f'Password changed for user {user.username}',
                user=user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({'message': 'Password changed successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """Authenticate user and create session"""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            device_id = serializer.validated_data.get('device_id')
            
            # Get or create device
            device = None
            if device_id:
                try:
                    device = Device.objects.get(device_id=device_id, owner=user)
                except Device.DoesNotExist:
                    pass
            
            # Create authentication token
            token, created = Token.objects.get_or_create(user=user)
            
            # Create user session
            session = UserSession.objects.create(
                user=user,
                device=device,
                ip_address=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                login_method='PASSWORD'
            )
            
            # Reset failed login attempts
            user.failed_login_attempts = 0
            user.save(update_fields=['failed_login_attempts'])
            
            # Log successful login
            SecurityEvent.objects.create(
                event_type='LOGIN_SUCCESS',
                severity='LOW',
                description=f'Successful login for user {user.username}',
                user=user,
                device=device,
                session=session,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                'token': token.key,
                'user': MilitaryUserSerializer(user).data,
                'session_id': session.session_id
            })
        
        # Handle failed login
        username = request.data.get('username')
        if username:
            try:
                user = MilitaryUser.objects.get(username=username)
                user.failed_login_attempts += 1
                
                # Lock account after 3 failed attempts
                if user.failed_login_attempts >= 3:
                    user.account_locked_until = timezone.now() + timezone.timedelta(minutes=15)
                
                user.save(update_fields=['failed_login_attempts', 'account_locked_until'])
                
                # Log failed login
                SecurityEvent.objects.create(
                    event_type='LOGIN_FAILED',
                    severity='MEDIUM',
                    description=f'Failed login attempt for user {username}',
                    user=user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            except MilitaryUser.DoesNotExist:
                pass
        
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        """Logout user and end session"""
        # End active sessions
        UserSession.objects.filter(
            user=request.user,
            is_active=True
        ).update(
            is_active=False,
            ended_at=timezone.now()
        )
        
        # Delete auth token
        try:
            request.user.auth_token.delete()
        except:
            pass
        
        # Log logout
        SecurityEvent.objects.create(
            event_type='LOGOUT',
            severity='LOW',
            description=f'User {request.user.username} logged out',
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({'message': 'Successfully logged out'})


class DeviceViewSet(viewsets.ModelViewSet):
    """ViewSet for Device management"""
    
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated, MilitaryPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['device_type', 'status', 'connectivity_status', 'owner', 'assigned_unit']
    search_fields = ['name', 'serial_number', 'owner__username', 'assigned_unit']
    ordering_fields = ['name', 'registered_at', 'last_heartbeat']
    ordering = ['-last_heartbeat']
    
    def get_queryset(self):
        """Filter devices based on user permissions"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Superusers can see all devices
        if user.is_superuser:
            return queryset
        
        # Users can see their own devices and devices in their unit
        return queryset.filter(
            Q(owner=user) | Q(assigned_unit=user.unit)
        )
    
    def perform_create(self, serializer):
        """Set owner to current user if not specified"""
        if 'owner' not in serializer.validated_data:
            serializer.save(owner=self.request.user)
        else:
            serializer.save()
        
        # Log device registration
        device = serializer.instance
        SecurityEvent.objects.create(
            event_type='DEVICE_REGISTERED',
            severity='LOW',
            description=f'Device {device.name} registered',
            user=device.owner,
            device=device,
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
    
    @action(detail=True, methods=['post'])
    def heartbeat(self, request, pk=None):
        """Update device heartbeat and status"""
        device = self.get_object()
        device.last_heartbeat = timezone.now()
        device.connectivity_status = 'ONLINE'
        
        # Update battery level if provided
        battery_level = request.data.get('battery_level')
        if battery_level is not None:
            device.battery_level = battery_level
        
        # Update location if provided
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        if latitude and longitude:
            device.last_known_latitude = latitude
            device.last_known_longitude = longitude
        
        device.save()
        return Response({'message': 'Heartbeat received'})
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, ClearanceLevelPermission])
    def mark_compromised(self, request, pk=None):
        """Mark device as compromised"""
        device = self.get_object()
        device.status = 'COMPROMISED'
        device.save()
        
        # Log security event
        SecurityEvent.objects.create(
            event_type='DEVICE_COMPROMISED',
            severity='CRITICAL',
            description=f'Device {device.name} marked as compromised',
            user=request.user,
            device=device,
            additional_data=request.data,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({'message': 'Device marked as compromised'})


class UserSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only ViewSet for UserSession monitoring"""
    
    queryset = UserSession.objects.all()
    serializer_class = UserSessionSerializer
    permission_classes = [permissions.IsAuthenticated, MilitaryPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user', 'device', 'is_active', 'suspicious_activity']
    ordering_fields = ['started_at', 'last_activity']
    ordering = ['-started_at']
    
    def get_queryset(self):
        """Filter sessions based on user permissions"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Superusers can see all sessions
        if user.is_superuser or user.has_perm('users.view_all_sessions'):
            return queryset
        
        # Users can only see their own sessions
        return queryset.filter(user=user)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def active(self, request):
        """Get user's active sessions"""
        sessions = self.get_queryset().filter(user=request.user, is_active=True)
        serializer = self.get_serializer(sessions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        """Terminate a session"""
        session = self.get_object()
        
        # Only allow terminating own sessions unless admin
        if session.user != request.user and not request.user.is_superuser:
            return Response(
                {'error': 'Cannot terminate another user\'s session'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        session.is_active = False
        session.ended_at = timezone.now()
        session.force_logout_reason = 'Manually terminated'
        session.save()
        
        return Response({'message': 'Session terminated'})


class SecurityEventViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for security event monitoring and resolution"""
    
    queryset = SecurityEvent.objects.all()
    serializer_class = SecurityEventSerializer
    permission_classes = [permissions.IsAuthenticated, ClearanceLevelPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['event_type', 'severity', 'user', 'device', 'is_resolved']
    ordering_fields = ['timestamp', 'severity']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """Filter events based on clearance level"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Superusers can see all events
        if user.is_superuser:
            return queryset
        
        # High clearance users can see more events
        if user.clearance_level in ['TOP_SECRET', 'TOP_SECRET_SCI']:
            return queryset
        
        # Lower clearance users see limited events
        return queryset.filter(
            Q(user=user) | Q(severity__in=['LOW', 'MEDIUM'])
        )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, ClearanceLevelPermission])
    def resolve(self, request, pk=None):
        """Mark security event as resolved"""
        event = self.get_object()
        
        if event.is_resolved:
            return Response(
                {'error': 'Event already resolved'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        event.is_resolved = True
        event.resolved_by = request.user
        event.resolved_at = timezone.now()
        event.resolution_notes = request.data.get('resolution_notes', '')
        event.save()
        
        return Response({'message': 'Event marked as resolved'})
    
    @action(detail=False, methods=['get'])
    def unresolved(self, request):
        """Get unresolved security events"""
        events = self.get_queryset().filter(is_resolved=False)
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def critical(self, request):
        """Get critical security events"""
        events = self.get_queryset().filter(severity='CRITICAL')
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)
