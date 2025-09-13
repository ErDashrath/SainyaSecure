"""
Military Communication System - Custom Permissions

This module defines custom permission classes for military operations.
Implements clearance level-based access control and military-specific permissions.
"""

from rest_framework import permissions
from django.contrib.auth.models import AnonymousUser


class MilitaryPermission(permissions.BasePermission):
    """
    Base permission class for military operations.
    Ensures user is authenticated and is military personnel.
    """
    
    def has_permission(self, request, view):
        """Check if user has basic military access"""
        # Must be authenticated
        if not request.user or isinstance(request.user, AnonymousUser):
            return False
        
        # Must be active military personnel
        if not hasattr(request.user, 'is_active_duty'):
            return False
            
        return request.user.is_active_duty
    
    def has_object_permission(self, request, view, obj):
        """Check object-level permissions"""
        # Superusers have full access
        if request.user.is_superuser:
            return True
        
        # For GET, HEAD, OPTIONS - allow if has basic permission
        if request.method in permissions.SAFE_METHODS:
            return self.has_permission(request, view)
        
        # For modifications, check ownership or higher clearance
        if hasattr(obj, 'owner'):
            return obj.owner == request.user or self.has_higher_clearance(request.user, obj.owner)
        elif hasattr(obj, 'user'):
            return obj.user == request.user or self.has_higher_clearance(request.user, obj.user)
        
        return False
    
    def has_higher_clearance(self, user1, user2):
        """Check if user1 has higher clearance than user2"""
        clearance_levels = {
            'CONFIDENTIAL': 1,
            'SECRET': 2,
            'TOP_SECRET': 3,
            'TOP_SECRET_SCI': 4
        }
        
        user1_level = clearance_levels.get(getattr(user1, 'clearance_level', ''), 0)
        user2_level = clearance_levels.get(getattr(user2, 'clearance_level', ''), 0)
        
        return user1_level > user2_level


class ClearanceLevelPermission(permissions.BasePermission):
    """
    Permission class that checks minimum clearance level.
    Can be configured per view with required_clearance attribute.
    """
    
    def has_permission(self, request, view):
        """Check if user has required clearance level"""
        if not request.user or isinstance(request.user, AnonymousUser):
            return False
        
        # Superusers bypass clearance checks
        if request.user.is_superuser:
            return True
        
        # Get required clearance from view
        required_clearance = getattr(view, 'required_clearance', 'CONFIDENTIAL')
        
        clearance_levels = {
            'CONFIDENTIAL': 1,
            'SECRET': 2,
            'TOP_SECRET': 3,
            'TOP_SECRET_SCI': 4
        }
        
        user_level = clearance_levels.get(getattr(request.user, 'clearance_level', ''), 0)
        required_level = clearance_levels.get(required_clearance, 1)
        
        return user_level >= required_level


class SecretClearanceRequired(ClearanceLevelPermission):
    """Convenience class for SECRET clearance requirement"""
    
    def has_permission(self, request, view):
        view.required_clearance = 'SECRET'
        return super().has_permission(request, view)


class TopSecretClearanceRequired(ClearanceLevelPermission):
    """Convenience class for TOP SECRET clearance requirement"""
    
    def has_permission(self, request, view):
        view.required_clearance = 'TOP_SECRET'
        return super().has_permission(request, view)


class TopSecretSCIClearanceRequired(ClearanceLevelPermission):
    """Convenience class for TOP SECRET/SCI clearance requirement"""
    
    def has_permission(self, request, view):
        view.required_clearance = 'TOP_SECRET_SCI'
        return super().has_permission(request, view)


class UnitPermission(permissions.BasePermission):
    """
    Permission class that allows access based on military unit.
    Users can access resources within their unit or subordinate units.
    """
    
    def has_permission(self, request, view):
        """Basic unit permission check"""
        if not request.user or isinstance(request.user, AnonymousUser):
            return False
        
        return hasattr(request.user, 'unit') and request.user.unit
    
    def has_object_permission(self, request, view, obj):
        """Check if user can access object based on unit"""
        if request.user.is_superuser:
            return True
        
        # Check if object belongs to same unit
        if hasattr(obj, 'unit'):
            return obj.unit == request.user.unit
        elif hasattr(obj, 'assigned_unit'):
            return obj.assigned_unit == request.user.unit
        elif hasattr(obj, 'owner') and hasattr(obj.owner, 'unit'):
            return obj.owner.unit == request.user.unit
        elif hasattr(obj, 'user') and hasattr(obj.user, 'unit'):
            return obj.user.unit == request.user.unit
        
        return False


class DeploymentPermission(permissions.BasePermission):
    """
    Permission class for deployment-specific operations.
    Allows access based on deployment status and location.
    """
    
    def has_permission(self, request, view):
        """Check deployment-based permissions"""
        if not request.user or isinstance(request.user, AnonymousUser):
            return False
        
        # Must be deployed or have override permissions
        if not getattr(request.user, 'is_deployed', False):
            return request.user.is_superuser or request.user.is_staff
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """Check object-level deployment permissions"""
        if request.user.is_superuser:
            return True
        
        # Check if in same deployment area
        user_deployment = getattr(request.user, 'current_deployment', '')
        
        if hasattr(obj, 'current_deployment'):
            return obj.current_deployment == user_deployment
        elif hasattr(obj, 'owner') and hasattr(obj.owner, 'current_deployment'):
            return obj.owner.current_deployment == user_deployment
        elif hasattr(obj, 'user') and hasattr(obj.user, 'current_deployment'):
            return obj.user.current_deployment == user_deployment
        
        return False


class AdminOrOwnerPermission(permissions.BasePermission):
    """
    Permission that allows access to admins or object owners only.
    """
    
    def has_permission(self, request, view):
        """Basic authentication check"""
        return request.user and not isinstance(request.user, AnonymousUser)
    
    def has_object_permission(self, request, view, obj):
        """Check admin or ownership"""
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Check various ownership patterns
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        # For user objects themselves
        if obj == request.user:
            return True
        
        return False


class ReadOnlyOrAdminPermission(permissions.BasePermission):
    """
    Permission that allows read access to authenticated users,
    but write access only to admins.
    """
    
    def has_permission(self, request, view):
        """Check read-only or admin access"""
        if not request.user or isinstance(request.user, AnonymousUser):
            return False
        
        # Read access for all authenticated military personnel
        if request.method in permissions.SAFE_METHODS:
            return hasattr(request.user, 'is_active_duty') and request.user.is_active_duty
        
        # Write access only for admins
        return request.user.is_superuser or request.user.is_staff
    
    def has_object_permission(self, request, view, obj):
        """Object-level read-only or admin check"""
        return self.has_permission(request, view)


class DeviceOwnerPermission(permissions.BasePermission):
    """
    Permission for device operations.
    Allows access to device owner, unit members, or higher clearance users.
    """
    
    def has_permission(self, request, view):
        """Basic device permission check"""
        if not request.user or isinstance(request.user, AnonymousUser):
            return False
        
        return hasattr(request.user, 'is_active_duty') and request.user.is_active_duty
    
    def has_object_permission(self, request, view, obj):
        """Check device-specific permissions"""
        if request.user.is_superuser:
            return True
        
        # Device owner has full access
        if hasattr(obj, 'owner') and obj.owner == request.user:
            return True
        
        # Unit members have limited access
        if hasattr(obj, 'assigned_unit') and obj.assigned_unit == getattr(request.user, 'unit', ''):
            # Read access for unit members
            if request.method in permissions.SAFE_METHODS:
                return True
            # Write access only for higher clearance or device admin actions
            return self._has_device_admin_access(request.user, obj)
        
        return False
    
    def _has_device_admin_access(self, user, device):
        """Check if user has device admin access"""
        clearance_levels = {
            'CONFIDENTIAL': 1,
            'SECRET': 2,
            'TOP_SECRET': 3,
            'TOP_SECRET_SCI': 4
        }
        
        user_level = clearance_levels.get(getattr(user, 'clearance_level', ''), 0)
        owner_level = clearance_levels.get(getattr(device.owner, 'clearance_level', ''), 0)
        
        # Higher clearance can manage devices
        return user_level > owner_level


class SecurityEventPermission(permissions.BasePermission):
    """
    Permission for security event operations.
    Higher clearance users can see and manage more events.
    """
    
    def has_permission(self, request, view):
        """Basic security event access"""
        if not request.user or isinstance(request.user, AnonymousUser):
            return False
        
        # Must have at least SECRET clearance for security events
        clearance_levels = {
            'CONFIDENTIAL': 1,
            'SECRET': 2,
            'TOP_SECRET': 3,
            'TOP_SECRET_SCI': 4
        }
        
        user_level = clearance_levels.get(getattr(request.user, 'clearance_level', ''), 0)
        return user_level >= 2 or request.user.is_superuser  # SECRET or higher
    
    def has_object_permission(self, request, view, obj):
        """Check security event access by clearance and involvement"""
        if request.user.is_superuser:
            return True
        
        # Users can see events they're involved in
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        # Higher clearance users can see more events
        clearance_levels = {
            'CONFIDENTIAL': 1,
            'SECRET': 2,
            'TOP_SECRET': 3,
            'TOP_SECRET_SCI': 4
        }
        
        user_level = clearance_levels.get(getattr(request.user, 'clearance_level', ''), 0)
        
        # TOP_SECRET and above can see all events
        if user_level >= 3:
            return True
        
        # SECRET can see non-critical events
        if user_level >= 2 and hasattr(obj, 'severity') and obj.severity != 'CRITICAL':
            return True
        
        return False