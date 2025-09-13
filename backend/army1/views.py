"""
Frontend views for SainyaSecure Military Communication System
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
from users.models import SecurityEvent, MilitaryUser


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_security_event(event_type, user, request, additional_data=None):
    """Log security events"""
    try:
        SecurityEvent.objects.create(
            event_type=event_type,
            user=user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            additional_data=additional_data or {},
            severity='MEDIUM' if 'FAILED' in event_type else 'LOW'
        )
    except Exception as e:
        print(f"Failed to log security event: {e}")


def validate_rank_access(user, selected_rank, otp_code):
    """Validate rank-based access requirements"""
    # Define rank requirements
    rank_requirements = {
        'COMMAND': {'min_clearance': 'TOP_SECRET', 'requires_2fa': True},
        'OPERATIONS': {'min_clearance': 'SECRET', 'requires_2fa': False},
        'INTELLIGENCE': {'min_clearance': 'TOP_SECRET_SCI', 'requires_2fa': True},
        'COMMUNICATIONS': {'min_clearance': 'SECRET', 'requires_2fa': False},
        'FIELD': {'min_clearance': 'CONFIDENTIAL', 'requires_2fa': False},
        'EMERGENCY': {'min_clearance': 'CONFIDENTIAL', 'requires_2fa': True},
    }
    
    if selected_rank not in rank_requirements:
        return {'valid': False, 'error_message': 'Invalid rank selection.'}
    
    requirements = rank_requirements[selected_rank]
    
    # Check clearance level (simplified - in real system would check user.clearance_level)
    # For demo, we'll allow all users but log the requirement
    
    # Check 2FA requirement
    if requirements['requires_2fa'] and not otp_code:
        return {'valid': False, 'error_message': 'Two-factor authentication required for this rank level.'}
    
    if requirements['requires_2fa'] and otp_code:
        # Simple OTP validation (in real system would verify against TOTP/SMS)
        if len(otp_code) != 6 or not otp_code.isdigit():
            return {'valid': False, 'error_message': 'Invalid two-factor authentication code.'}
    
    return {'valid': True}


def get_rank_dashboard_name(rank):
    """Get dashboard name based on rank"""
    dashboard_names = {
        'COMMAND': 'Command Center',
        'OPERATIONS': 'Operations Dashboard', 
        'INTELLIGENCE': 'Intelligence Portal',
        'COMMUNICATIONS': 'Communications Hub',
        'FIELD': 'Field Terminal',
        'EMERGENCY': 'Emergency Override Center'
    }
    return dashboard_names.get(rank, 'Military Dashboard')


def get_rank_dashboard_url(rank):
    """Get dashboard URL based on rank"""
    # For now, all redirect to main dashboard
    # Later we'll create specific dashboards for each rank
    dashboard_urls = {
        'COMMAND': 'dashboard_command',
        'OPERATIONS': 'dashboard_operations',
        'INTELLIGENCE': 'dashboard_intelligence', 
        'COMMUNICATIONS': 'dashboard_communications',
        'FIELD': 'dashboard_field',
        'EMERGENCY': 'dashboard_emergency'
    }
    return dashboard_urls.get(rank, 'dashboard')


def index(request):
    """
    Landing page for SainyaSecure system
    Redirects to dashboard if user is already logged in
    """
    if request.user.is_authenticated:
        # User is already logged in, redirect to their dashboard
        selected_rank = request.session.get('selected_rank', 'FIELD')
        return redirect(get_rank_dashboard_url(selected_rank))
    
    return render(request, 'index.html')


def user_login(request):
    """
    Enhanced login with rank-based access control
    Redirects to dashboard if user is already logged in
    """
    if request.user.is_authenticated:
        # User is already logged in, redirect to their dashboard
        selected_rank = request.session.get('selected_rank', 'FIELD')
        messages.info(request, 'You are already logged in.')
        return redirect(get_rank_dashboard_url(selected_rank))
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        selected_rank = request.POST.get('selected_rank')
        otp_code = request.POST.get('otp_code', '')
        remember_me = request.POST.get('remember_me')
        
        # Debug print to see what we're receiving
        print(f"DEBUG - Login attempt: username={username}, selected_rank={selected_rank}, has_password={bool(password)}")
        
        if username and password and selected_rank:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Verify rank-based access requirements
                rank_validation = validate_rank_access(user, selected_rank, otp_code)
                
                if rank_validation['valid']:
                    login(request, user)
                    
                    # Set session expiry based on remember_me
                    if remember_me:
                        request.session.set_expiry(30 * 24 * 60 * 60)  # 30 days
                    else:
                        request.session.set_expiry(0)  # Browser session
                    
                    # Store selected rank in session for dashboard customization
                    request.session['selected_rank'] = selected_rank
                    
                    # Log security event
                    log_security_event('LOGIN_SUCCESS', user, request, {
                        'rank': selected_rank,
                        'ip_address': get_client_ip(request),
                        'user_agent': request.META.get('HTTP_USER_AGENT', '')
                    })
                    
                    messages.success(request, f'Welcome to {get_rank_dashboard_name(selected_rank)}, {user.get_full_name() or user.username}!')
                    
                    # Always redirect to main dashboard for now
                    print(f"DEBUG - Redirecting to dashboard after successful login")
                    return redirect('dashboard')
                else:
                    messages.error(request, rank_validation['error_message'])
            else:
                # Log failed login attempt
                log_security_event('LOGIN_FAILED', None, request, {
                    'username': username,
                    'rank': selected_rank,
                    'ip_address': get_client_ip(request)
                })
                messages.error(request, 'Invalid credentials or insufficient clearance level.')
        else:
            messages.error(request, 'Please provide all required information including rank selection.')
    
    return render(request, 'login.html')


@login_required
def dashboard(request):
    """
    Main dashboard - redirects to appropriate rank-specific dashboard
    """
    selected_rank = request.session.get('selected_rank', 'FIELD')
    
    # Redirect to specific dashboard based on rank
    rank_dashboard_mapping = {
        'COMMAND': dashboard_command,
        'OPERATIONS': dashboard_operations,
        'INTELLIGENCE': dashboard_intelligence,
        'COMMUNICATIONS': dashboard_communications,
        'FIELD': dashboard_field,
        'EMERGENCY': dashboard_emergency,
    }
    
    dashboard_view = rank_dashboard_mapping.get(selected_rank, dashboard_field)
    return dashboard_view(request)


@login_required
def dashboard_command(request):
    """Command Authority Dashboard - Full system access"""
    context = {
        'user': request.user,
        'current_time': timezone.now(),
        'rank_title': 'Command Authority',
        'dashboard_type': 'COMMAND',
        'stats': {
            'total_personnel': 2847,
            'active_devices': 1567,
            'messages_today': 45234,
            'security_alerts': 3,
            'active_operations': 12,
            'deployment_zones': 8,
        },
        'modules': [
            {'name': 'Personnel Management', 'icon': 'users', 'url': 'personnel', 'description': 'Manage all military personnel'},
            {'name': 'Operations Control', 'icon': 'cogs', 'url': 'operations', 'description': 'Strategic operations management'},
            {'name': 'Intelligence Reports', 'icon': 'eye', 'url': 'intelligence', 'description': 'Intelligence analysis and reports'},
            {'name': 'Communications Hub', 'icon': 'satellite-dish', 'url': 'communications', 'description': 'All communication channels'},
            {'name': 'Device Management', 'icon': 'mobile-alt', 'url': 'devices', 'description': 'Military device registry'},
            {'name': 'Security Center', 'icon': 'shield-alt', 'url': 'security', 'description': 'System security monitoring'},
            {'name': 'Mission Planning', 'icon': 'map-marked-alt', 'url': 'missions', 'description': 'Strategic mission planning'},
            {'name': 'Resource Allocation', 'icon': 'chart-pie', 'url': 'resources', 'description': 'Resource management'},
        ]
    }
    return render(request, 'dashboard.html', context)


@login_required  
def dashboard_operations(request):
    """Operations Officer Dashboard - Tactical operations focus"""
    context = {
        'user': request.user,
        'current_time': timezone.now(),
        'rank_title': 'Operations Officer',
        'dashboard_type': 'OPERATIONS',
        'stats': {
            'active_missions': 5,
            'unit_personnel': 156,
            'messages_today': 1247,
            'security_alerts': 1,
        },
        'modules': [
            {'name': 'Mission Control', 'icon': 'crosshairs', 'url': 'missions', 'description': 'Active mission management'},
            {'name': 'Unit Communications', 'icon': 'comments', 'url': 'communications', 'description': 'Unit communication channels'},
            {'name': 'Field Reports', 'icon': 'file-alt', 'url': 'reports', 'description': 'Field situation reports'},
            {'name': 'Resource Status', 'icon': 'boxes', 'url': 'resources', 'description': 'Equipment and supplies'},
            {'name': 'Personnel Status', 'icon': 'user-check', 'url': 'personnel', 'description': 'Unit personnel status'},
            {'name': 'Tactical Planning', 'icon': 'chess', 'url': 'tactical', 'description': 'Tactical operation planning'},
        ]
    }
    return render(request, 'dashboard.html', context)


@login_required
def dashboard_intelligence(request):
    """Intelligence Officer Dashboard - Intelligence focus"""
    context = {
        'user': request.user,
        'current_time': timezone.now(),
        'rank_title': 'Intelligence Officer',
        'dashboard_type': 'INTELLIGENCE',
        'stats': {
            'threat_reports': 23,
            'intel_sources': 47,
            'classified_docs': 156,
            'security_clearance': 'TOP SECRET/SCI',
        },
        'modules': [
            {'name': 'Threat Analysis', 'icon': 'search', 'url': 'threats', 'description': 'Threat assessment and analysis'},
            {'name': 'Intelligence Reports', 'icon': 'file-contract', 'url': 'intel-reports', 'description': 'Classified intelligence reports'},
            {'name': 'Surveillance Data', 'icon': 'video', 'url': 'surveillance', 'description': 'Surveillance and reconnaissance'},
            {'name': 'Signal Intelligence', 'icon': 'broadcast-tower', 'url': 'sigint', 'description': 'Communication intercepts'},
            {'name': 'Risk Assessment', 'icon': 'exclamation-triangle', 'url': 'risk', 'description': 'Security risk evaluation'},
            {'name': 'Classified Comms', 'icon': 'lock', 'url': 'secure-comms', 'description': 'Highly classified communications'},
        ]
    }
    return render(request, 'dashboard.html', context)


@login_required
def dashboard_communications(request):
    """Communications Specialist Dashboard - Network and communications focus"""
    context = {
        'user': request.user,
        'current_time': timezone.now(),
        'rank_title': 'Communications Specialist',
        'dashboard_type': 'COMMUNICATIONS',
        'stats': {
            'active_channels': 23,
            'network_uptime': 99.8,
            'messages_processed': 12567,
            'device_connections': 234,
        },
        'modules': [
            {'name': 'Network Monitoring', 'icon': 'network-wired', 'url': 'network', 'description': 'Network status and monitoring'},
            {'name': 'Message Center', 'icon': 'envelope', 'url': 'messages', 'description': 'Message routing and delivery'},
            {'name': 'Device Status', 'icon': 'mobile-alt', 'url': 'device-status', 'description': 'Connected device monitoring'},
            {'name': 'Channel Management', 'icon': 'satellite-dish', 'url': 'channels', 'description': 'Communication channel control'},
            {'name': 'Encryption Keys', 'icon': 'key', 'url': 'encryption', 'description': 'Encryption key management'},
            {'name': 'Technical Support', 'icon': 'tools', 'url': 'support', 'description': 'Technical troubleshooting'},
        ]
    }
    return render(request, 'dashboard.html', context)


@login_required
def dashboard_field(request):
    """Field Personnel Dashboard - Basic operations focus"""
    context = {
        'user': request.user,
        'current_time': timezone.now(),
        'rank_title': 'Field Personnel',
        'dashboard_type': 'FIELD',
        'stats': {
            'active_missions': 1,
            'team_members': 8,
            'messages_today': 23,
            'equipment_status': 'OPERATIONAL',
        },
        'modules': [
            {'name': 'Mission Briefing', 'icon': 'clipboard-list', 'url': 'briefing', 'description': 'Current mission details'},
            {'name': 'Team Communications', 'icon': 'users', 'url': 'team-comms', 'description': 'Team communication channels'},
            {'name': 'Status Report', 'icon': 'flag', 'url': 'status-report', 'description': 'Submit status updates'},
            {'name': 'Emergency Alert', 'icon': 'exclamation-triangle', 'url': 'emergency', 'description': 'Emergency communication'},
            {'name': 'Equipment Check', 'icon': 'clipboard-check', 'url': 'equipment', 'description': 'Equipment status check'},
            {'name': 'Location Update', 'icon': 'map-marker-alt', 'url': 'location', 'description': 'Position reporting'},
        ]
    }
    return render(request, 'dashboard.html', context)


@login_required
def dashboard_emergency(request):
    """Emergency Override Dashboard - Crisis management focus"""
    context = {
        'user': request.user,
        'current_time': timezone.now(),
        'rank_title': 'Emergency Override',
        'dashboard_type': 'EMERGENCY',
        'stats': {
            'active_incidents': 1,
            'response_teams': 5,
            'emergency_contacts': 12,
            'system_status': 'EMERGENCY',
        },
        'modules': [
            {'name': 'Incident Command', 'icon': 'exclamation-circle', 'url': 'incident', 'description': 'Emergency incident management'},
            {'name': 'Mass Notification', 'icon': 'bullhorn', 'url': 'notification', 'description': 'Emergency mass alerts'},
            {'name': 'Resource Coordination', 'icon': 'hands-helping', 'url': 'coordination', 'description': 'Emergency resource coordination'},
            {'name': 'Communication Override', 'icon': 'satellite', 'url': 'override', 'description': 'Override communication protocols'},
            {'name': 'Emergency Contacts', 'icon': 'phone', 'url': 'contacts', 'description': 'Critical emergency contacts'},
            {'name': 'Situation Report', 'icon': 'chart-line', 'url': 'sitrep', 'description': 'Emergency situation reporting'},
        ]
    }
    return render(request, 'dashboard.html', context)


@login_required 
def device_join(request):
    """
    Device registration and joining system
    """
    if request.method == 'POST':
        device_data = {
            'device_type': request.POST.get('device_type'),
            'serial_number': request.POST.get('serial_number'),
            'military_unit': request.POST.get('military_unit'),
            'location': request.POST.get('location'),
            'requesting_officer': request.POST.get('requesting_officer'),
            'clearance_level': request.POST.get('clearance_level'),
            'purpose': request.POST.get('purpose'),
        }
        
        # TODO: Implement device registration with backend integration
        messages.success(request, f'Device registration request submitted for {device_data["device_type"]}. Awaiting authority approval.')
        return redirect('join')
    
    return render(request, 'join.html')


def user_logout(request):
    """
    Logout and redirect to landing page
    """
    logout(request)
    messages.info(request, 'Secure logout completed. Session terminated.')
    return redirect('index')


# API Endpoints for real-time data
@csrf_exempt
def api_system_stats(request):
    """
    Real-time system statistics for dashboard
    """
    if request.method == 'GET':
        stats = {
            'active_units': 2847,
            'connected_devices': 1567,
            'messages_today': 45234,
            'security_alerts': 3,
            'network_uptime': 99.8,
            'response_time': 2.3,
            'data_processed': '847GB',
            'threats_blocked': 0,
            'encryption_status': 'AES-256',
            'ai_monitoring': 'ACTIVE'
        }
        return JsonResponse(stats)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# Module placeholder views - To be implemented with full CRUD operations
@login_required
def module_messaging(request):
    """P2P Messaging Module"""
    from .models import MilitaryMessage, CommandMilitaryUser
    from django.contrib import messages
    from django.utils import timezone
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'send_message':
            try:
                # Get or create sender
                sender, created = CommandMilitaryUser.objects.get_or_create(
                    rank=request.user.username.upper()  # Using username as rank for demo
                )
                
                message_content = request.POST.get('message_content')
                message_type = request.POST.get('message_type', 'ROUTINE')
                recipient_name = request.POST.get('recipient', 'ALL')
                
                military_message = MilitaryMessage.objects.create(
                    sender=sender,
                    content=message_content,
                    priority=message_type,
                    channel=request.POST.get('channel', 'COMMAND-CENTER'),
                    timestamp=timezone.now()
                )
                
                messages.success(request, f'Message sent successfully to {recipient_name}')
            except Exception as e:
                messages.error(request, f'Error sending message: {str(e)}')
    
    # Get recent messages for display
    recent_messages = MilitaryMessage.objects.select_related('sender').order_by('-timestamp')[:50]
    
    # Get active users
    active_users = CommandMilitaryUser.objects.all()[:12]
    
    return render(request, 'modules/messaging.html', {
        'module_name': 'Secure Messaging',
        'rank_required': 'Any',
        'description': 'Peer-to-peer encrypted messaging system for secure communications',
        'recent_messages': recent_messages,
        'active_users': active_users,
        'current_time': timezone.now(),
        'total_personnel': active_users.count(),
        'active_channels': 12,
    })

@login_required
def module_p2p(request):
    """P2P Network Module"""
    return render(request, 'modules/p2p.html', {
        'module_name': 'P2P Network',
        'rank_required': 'Communications+',
        'description': 'Peer-to-peer network management and monitoring'
    })

@login_required
def module_personnel(request):
    """Personnel Management Module"""
    from .models import Personnel, CommandMilitaryUser
    from django.contrib import messages
    from django.shortcuts import get_object_or_404
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_personnel':
            # Create new personnel record
            try:
                # Get or create CommandMilitaryUser
                military_user, created = CommandMilitaryUser.objects.get_or_create(
                    rank=request.POST.get('rank', 'FIELD'),
                    unit=request.POST.get('current_assignment', 'Unknown Unit')
                )
                
                personnel = Personnel.objects.create(
                    military_user=military_user,
                    first_name=request.POST.get('first_name'),
                    last_name=request.POST.get('last_name'),
                    service_number=request.POST.get('service_number'),
                    date_of_birth=request.POST.get('date_of_birth'),
                    enlistment_date=request.POST.get('enlistment_date'),
                    current_assignment=request.POST.get('current_assignment'),
                    location=request.POST.get('location'),
                    status=request.POST.get('status', 'ACTIVE'),
                    emergency_contact_name=request.POST.get('emergency_contact_name'),
                    emergency_contact_phone=request.POST.get('emergency_contact_phone'),
                    medical_notes=request.POST.get('medical_notes', '')
                )
                messages.success(request, f'Personnel record created for {personnel.first_name} {personnel.last_name}')
            except Exception as e:
                messages.error(request, f'Error creating personnel record: {str(e)}')
        
        elif action == 'update_personnel':
            # Update existing personnel record
            try:
                personnel_id = request.POST.get('personnel_id')
                personnel = get_object_or_404(Personnel, personnel_id=personnel_id)
                
                personnel.first_name = request.POST.get('first_name')
                personnel.last_name = request.POST.get('last_name')
                personnel.current_assignment = request.POST.get('current_assignment')
                personnel.location = request.POST.get('location')
                personnel.status = request.POST.get('status')
                personnel.emergency_contact_name = request.POST.get('emergency_contact_name')
                personnel.emergency_contact_phone = request.POST.get('emergency_contact_phone')
                personnel.medical_notes = request.POST.get('medical_notes')
                personnel.save()
                
                messages.success(request, f'Personnel record updated for {personnel.first_name} {personnel.last_name}')
            except Exception as e:
                messages.error(request, f'Error updating personnel record: {str(e)}')
    
    # Get all personnel records
    personnel_list = Personnel.objects.all().select_related('military_user')
    
    return render(request, 'modules/personnel.html', {
        'module_name': 'Personnel Management',
        'rank_required': 'Operations+',
        'description': 'Personnel records, assignments, and status tracking',
        'personnel_list': personnel_list,
        'status_choices': Personnel.STATUS_CHOICES,
    })

@login_required
def module_devices(request):
    """Device Management Module"""
    from .models import MilitaryDevice, Personnel
    from django.contrib import messages
    from django.shortcuts import get_object_or_404
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_device':
            try:
                # Get assigned personnel if provided
                assigned_to = None
                personnel_id = request.POST.get('assigned_to')
                if personnel_id:
                    assigned_to = get_object_or_404(Personnel, personnel_id=personnel_id)
                
                device = MilitaryDevice.objects.create(
                    serial_number=request.POST.get('serial_number'),
                    device_type=request.POST.get('device_type'),
                    model=request.POST.get('model'),
                    assigned_to=assigned_to,
                    status=request.POST.get('status', 'ACTIVE'),
                    location=request.POST.get('location'),
                    acquisition_date=request.POST.get('acquisition_date'),
                    acquisition_cost=request.POST.get('acquisition_cost') or None,
                    notes=request.POST.get('notes', '')
                )
                messages.success(request, f'Device {device.serial_number} added successfully')
            except Exception as e:
                messages.error(request, f'Error adding device: {str(e)}')
        
        elif action == 'update_device':
            try:
                device_id = request.POST.get('device_id')
                device = get_object_or_404(MilitaryDevice, device_id=device_id)
                
                device.status = request.POST.get('status')
                device.location = request.POST.get('location')
                device.notes = request.POST.get('notes')
                
                # Update assigned personnel if provided
                personnel_id = request.POST.get('assigned_to')
                if personnel_id:
                    device.assigned_to = get_object_or_404(Personnel, personnel_id=personnel_id)
                else:
                    device.assigned_to = None
                
                device.save()
                messages.success(request, f'Device {device.serial_number} updated successfully')
            except Exception as e:
                messages.error(request, f'Error updating device: {str(e)}')
    
    # Get all devices and personnel for display
    devices = MilitaryDevice.objects.select_related('assigned_to').all()
    personnel_list = Personnel.objects.all()
    
    # Device statistics
    device_stats = {
        'total': devices.count(),
        'active': devices.filter(status='ACTIVE').count(),
        'maintenance': devices.filter(status='MAINTENANCE').count(),
        'repair': devices.filter(status='REPAIR').count(),
    }
    
    return render(request, 'modules/devices.html', {
        'module_name': 'Device Management',
        'rank_required': 'Field+',
        'description': 'Connected device monitoring and management',
        'devices': devices,
        'personnel_list': personnel_list,
        'device_stats': device_stats,
        'device_types': MilitaryDevice.DEVICE_TYPES,
        'status_choices': MilitaryDevice.STATUS_CHOICES,
    })

@login_required
def module_security(request):
    """Security Module"""
    from .models import CommandSecurityEvent
    from django.contrib import messages
    from django.shortcuts import get_object_or_404
    from django.utils import timezone
    from django.db.models import Count, Q
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_security_event':
            try:
                event = CommandSecurityEvent.objects.create(
                    user=request.user,
                    event_type=request.POST.get('event_type'),
                    severity=request.POST.get('severity', 'LOW'),
                    description=request.POST.get('description'),
                    ip_address=request.POST.get('ip_address', request.META.get('REMOTE_ADDR')),
                    user_agent=request.POST.get('user_agent', request.META.get('HTTP_USER_AGENT', '')),
                    module_accessed=request.POST.get('module_accessed', 'Security Center')
                )
                messages.success(request, f'Security event logged: {event.get_event_type_display()}')
            except Exception as e:
                messages.error(request, f'Error logging security event: {str(e)}')
        
        elif action == 'resolve_event':
            try:
                event_id = request.POST.get('event_id')
                event = get_object_or_404(CommandSecurityEvent, event_id=event_id)
                event.resolved = True
                event.resolved_by = request.user
                event.save()
                
                messages.success(request, f'Security event resolved successfully')
            except Exception as e:
                messages.error(request, f'Error resolving security event: {str(e)}')
    
    # Get security events with filtering
    events = CommandSecurityEvent.objects.select_related('user', 'resolved_by').order_by('-timestamp')
    
    # Filter by severity if specified
    severity_filter = request.GET.get('severity')
    if severity_filter:
        events = events.filter(severity=severity_filter)
    
    # Filter by resolved status
    resolved_filter = request.GET.get('resolved')
    if resolved_filter == 'unresolved':
        events = events.filter(resolved=False)
    elif resolved_filter == 'resolved':
        events = events.filter(resolved=True)
    
    # Get recent events (last 50)
    events = events[:50]
    
    # Calculate statistics
    total_events = CommandSecurityEvent.objects.count()
    unresolved_events = CommandSecurityEvent.objects.filter(resolved=False).count()
    critical_events = CommandSecurityEvent.objects.filter(severity='CRITICAL', resolved=False).count()
    recent_violations = CommandSecurityEvent.objects.filter(
        event_type='SECURITY_VIOLATION', 
        timestamp__gte=timezone.now() - timezone.timedelta(hours=24)
    ).count()
    
    security_stats = {
        'total': total_events,
        'unresolved': unresolved_events,
        'critical': critical_events,
        'violations_24h': recent_violations,
    }
    
    # Get event type distribution
    event_distribution = CommandSecurityEvent.objects.values('event_type').annotate(
        count=Count('event_id')
    ).order_by('-count')
    
    return render(request, 'modules/security.html', {
        'module_name': 'Security Center',
        'rank_required': 'Intelligence+',
        'description': 'Security monitoring, alerts, and incident management',
        'events': events,
        'security_stats': security_stats,
        'event_distribution': event_distribution,
        'event_types': CommandSecurityEvent.EVENT_TYPES,
        'severity_levels': CommandSecurityEvent.SEVERITY_LEVELS,
        'current_severity_filter': severity_filter,
        'current_resolved_filter': resolved_filter,
    })

@login_required
def module_reports(request):
    """Reports Module"""
    return render(request, 'modules/reports.html', {
        'module_name': 'Reports & Analytics',
        'rank_required': 'Operations+',
        'description': 'System reports and operational analytics'
    })

@login_required
def module_logs(request):
    """Logs Module"""
    return render(request, 'modules/logs.html', {
        'module_name': 'System Logs',
        'rank_required': 'Command',
        'description': 'Comprehensive system activity logs and audit trails'
    })

@login_required
def module_intel(request):
    """Intelligence Module"""
    return render(request, 'modules/intel.html', {
        'module_name': 'Intelligence Hub',
        'rank_required': 'Intelligence',
        'description': 'Intelligence gathering, analysis, and reporting'
    })

@login_required
def module_threats(request):
    """Threat Analysis Module"""
    return render(request, 'modules/threats.html', {
        'module_name': 'Threat Analysis',
        'rank_required': 'Intelligence+',
        'description': 'Threat assessment and risk analysis tools'
    })

@login_required
def module_classified(request):
    """Classified Documents Module"""
    return render(request, 'modules/classified.html', {
        'module_name': 'Classified Documents',
        'rank_required': 'Intelligence+',
        'description': 'Secure storage and management of classified materials'
    })

@login_required
def module_comms(request):
    """Communications Module"""
    return render(request, 'modules/comms.html', {
        'module_name': 'Communications',
        'rank_required': 'Communications+',
        'description': 'Communication systems management and coordination'
    })

@login_required
def module_networks(request):
    """Network Management Module"""
    return render(request, 'modules/networks.html', {
        'module_name': 'Network Management',
        'rank_required': 'Communications+',
        'description': 'Network infrastructure monitoring and control'
    })

@login_required
def module_broadcast(request):
    """Broadcast Module"""
    return render(request, 'modules/broadcast.html', {
        'module_name': 'Broadcast Systems',
        'rank_required': 'Command+',
        'description': 'Mass communication and emergency broadcast systems'
    })

@login_required
def module_missions(request):
    """Mission Control Module"""
    from .models import Mission, Personnel, CommandMilitaryUser
    from django.contrib import messages
    from django.shortcuts import get_object_or_404
    from django.utils import timezone
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_mission':
            try:
                # Get or create commander
                commander_user, created = CommandMilitaryUser.objects.get_or_create(
                    rank=request.POST.get('commander_rank', 'OPERATIONS')
                )
                commander, created = Personnel.objects.get_or_create(
                    military_user=commander_user,
                    defaults={
                        'first_name': request.POST.get('commander_name', 'Unknown'),
                        'last_name': 'Commander',
                        'service_number': f'CMD-{timezone.now().strftime("%Y%m%d")}-{Mission.objects.count() + 1:03d}',
                        'date_of_birth': '1980-01-01',
                        'enlistment_date': '2000-01-01',
                        'current_assignment': 'Mission Command',
                        'location': request.POST.get('location', 'Base'),
                        'emergency_contact_name': 'Emergency Contact',
                        'emergency_contact_phone': '+1-800-000-0000'
                    }
                )
                
                mission = Mission.objects.create(
                    mission_name=request.POST.get('mission_name'),
                    mission_code=request.POST.get('mission_code'),
                    description=request.POST.get('description'),
                    classification=request.POST.get('classification', 'UNCLASSIFIED'),
                    commander=commander,
                    status=request.POST.get('status', 'PLANNING'),
                    start_date=request.POST.get('start_date'),
                    location=request.POST.get('location'),
                    objectives=request.POST.get('objectives'),
                    resources_required=request.POST.get('resources_required'),
                    risk_assessment=request.POST.get('risk_assessment', '')
                )
                
                messages.success(request, f'Mission "{mission.mission_name}" created successfully')
            except Exception as e:
                messages.error(request, f'Error creating mission: {str(e)}')
        
        elif action == 'update_mission_status':
            try:
                mission_id = request.POST.get('mission_id')
                mission = get_object_or_404(Mission, mission_id=mission_id)
                mission.status = request.POST.get('new_status')
                if request.POST.get('new_status') == 'COMPLETED':
                    mission.end_date = timezone.now()
                mission.save()
                
                messages.success(request, f'Mission status updated to {mission.get_status_display()}')
            except Exception as e:
                messages.error(request, f'Error updating mission: {str(e)}')
    
    # Get all missions
    missions = Mission.objects.select_related('commander').prefetch_related('assigned_personnel').order_by('-created_at')
    
    # Get statistics
    mission_stats = {
        'total': missions.count(),
        'planning': missions.filter(status='PLANNING').count(),
        'in_progress': missions.filter(status='IN_PROGRESS').count(),
        'completed': missions.filter(status='COMPLETED').count(),
    }
    
    return render(request, 'modules/missions.html', {
        'module_name': 'Mission Control',
        'rank_required': 'Operations+',
        'description': 'Mission planning, execution, and tracking',
        'missions': missions,
        'mission_stats': mission_stats,
        'status_choices': Mission.STATUS_CHOICES,
        'classification_choices': Mission.CLASSIFICATION_LEVELS,
    })

@login_required
def module_tactical(request):
    """Tactical Operations Module"""
    return render(request, 'modules/tactical.html', {
        'module_name': 'Tactical Operations',
        'rank_required': 'Operations+',
        'description': 'Tactical planning and field operations management'
    })

@login_required
def module_operations(request):
    """Operations Center Module"""
    return render(request, 'modules/operations.html', {
        'module_name': 'Operations Center',
        'rank_required': 'Operations+',
        'description': 'Central operations coordination and management'
    })

@login_required
def module_equipment(request):
    """Equipment Module"""
    return render(request, 'modules/equipment.html', {
        'module_name': 'Equipment Management',
        'rank_required': 'Field+',
        'description': 'Equipment inventory, maintenance, and tracking'
    })

@login_required
def module_training(request):
    """Training Module"""
    return render(request, 'modules/training.html', {
        'module_name': 'Training & Drills',
        'rank_required': 'Field+',
        'description': 'Training schedules, drills, and performance tracking'
    })

@login_required
def module_emergency(request):
    """Emergency Protocols Module"""
    return render(request, 'modules/emergency.html', {
        'module_name': 'Emergency Protocols',
        'rank_required': 'Emergency',
        'description': 'Emergency response coordination and crisis management'
    })