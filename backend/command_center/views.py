"""
Command Center Views - Master Authority Dashboard

Provides comprehensive command center functionality:
- Real-time message logs and blockchain ledger explorer
- Node connectivity monitoring and status dashboard
- AI anomaly detection alerts and management
- Mission audit trails and replay capabilities
- Encrypted message decryption for authorized personnel
- Lamport/Vector clock conflict resolution interface
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, DetailView, TemplateView
from django.http import JsonResponse, StreamingHttpResponse
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json
from datetime import timedelta

from .models import CommandNode, MasterLedger, DecryptedMessage, CommandAlert, MissionAudit
from messaging.models import Message
from ai_anomaly.models import AnomalyAlert
from blockchain.models import LocalLedgerBlock


class CommandCenterDashboard(LoginRequiredMixin, TemplateView):
    """
    Main command center dashboard with real-time monitoring
    Integrates with existing army1 dashboard but provides command authority view
    """
    template_name = 'command_center/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Node connectivity status
        nodes_online = CommandNode.objects.filter(status='ONLINE').count()
        nodes_total = CommandNode.objects.count()
        nodes_offline = CommandNode.objects.filter(status='OFFLINE').count()
        nodes_resync = CommandNode.objects.filter(status='RESYNC').count()
        
        # Recent ledger activity (last 24 hours)
        last_24h = timezone.now() - timedelta(hours=24)
        recent_transactions = MasterLedger.objects.filter(timestamp__gte=last_24h).count()
        
        # Unresolved alerts
        critical_alerts = CommandAlert.objects.filter(
            is_resolved=False, 
            severity='CRITICAL'
        ).count()
        
        high_alerts = CommandAlert.objects.filter(
            is_resolved=False, 
            severity='HIGH'
        ).count()
        
        # Active missions
        active_missions = MissionAudit.objects.filter(status='ACTIVE').count()
        
        # AI anomaly detection status
        ai_anomalies_today = AnomalyAlert.objects.filter(
            created_at__gte=timezone.now().replace(hour=0, minute=0, second=0)
        ).count()
        
        context.update({
            'user': self.request.user,
            'current_time': timezone.now(),
            'rank_title': 'Command Center Authority',
            'dashboard_type': 'COMMAND_CENTER',
            
            # Network Status
            'nodes_status': {
                'total': nodes_total,
                'online': nodes_online,
                'offline': nodes_offline,
                'resync': nodes_resync,
                'uptime_percentage': round((nodes_online / nodes_total * 100) if nodes_total > 0 else 0, 1)
            },
            
            # Communication Stats
            'communication_stats': {
                'recent_transactions': recent_transactions,
                'messages_today': Message.objects.filter(
                    created_at__gte=timezone.now().replace(hour=0, minute=0, second=0)
                ).count(),
                'avg_response_time': '2.3ms',  # TODO: Calculate from actual metrics
                'encryption_success_rate': '99.8%'  # TODO: Calculate from actual metrics
            },
            
            # Security Status
            'security_status': {
                'critical_alerts': critical_alerts,
                'high_alerts': high_alerts,
                'ai_anomalies_today': ai_anomalies_today,
                'total_unresolved': critical_alerts + high_alerts
            },
            
            # Mission Status
            'mission_status': {
                'active_missions': active_missions,
                'completed_today': MissionAudit.objects.filter(
                    status='COMPLETED',
                    end_time__gte=timezone.now().replace(hour=0, minute=0, second=0)
                ).count()
            }
        })
        
        return context


class BlockchainLedgerView(LoginRequiredMixin, ListView):
    """
    Blockchain ledger explorer showing all validated transactions
    Immutable audit trail with search and filter capabilities
    """
    model = MasterLedger
    template_name = 'command_center/ledger_explorer.html'
    context_object_name = 'transactions'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = MasterLedger.objects.select_related(
            'sender_node', 'receiver_node'
        ).filter(is_validated=True)
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(sender_node__node_name__icontains=search) |
                Q(receiver_node__node_name__icontains=search) |
                Q(message_hash__icontains=search)
            )
        
        # Filter by transaction type
        tx_type = self.request.GET.get('type')
        if tx_type:
            queryset = queryset.filter(transaction_type=tx_type)
            
        # Filter by date range
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)
            
        return queryset.order_by('-block_height')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transaction_types'] = MasterLedger.TRANSACTION_TYPES
        context['total_blocks'] = MasterLedger.objects.count()
        context['search_query'] = self.request.GET.get('search', '')
        return context


class MessageLogsView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Decrypted message logs for authorized command personnel
    Shows plaintext content with proper access control and logging
    """
    model = DecryptedMessage
    template_name = 'command_center/message_logs.html'
    context_object_name = 'messages'
    paginate_by = 25
    permission_required = 'command_center.view_decrypted_message'
    
    def get_queryset(self):
        queryset = DecryptedMessage.objects.select_related(
            'ledger_entry__sender_node',
            'ledger_entry__receiver_node',
            'decrypted_by'
        ).all()
        
        # Filter by classification level based on user permissions
        user_clearance = self.get_user_clearance_level()
        if user_clearance == 'CONFIDENTIAL':
            queryset = queryset.filter(
                classification__in=['UNCLASSIFIED', 'RESTRICTED', 'CONFIDENTIAL']
            )
        elif user_clearance == 'SECRET':
            queryset = queryset.exclude(classification='TOP_SECRET')
        # TOP_SECRET users can see everything
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(subject__icontains=search) |
                Q(content__icontains=search) |
                Q(ledger_entry__sender_node__node_name__icontains=search)
            )
            
        return queryset.order_by('-decrypted_at')
    
    def get_user_clearance_level(self):
        """Determine user's security clearance level"""
        user = self.request.user
        if user.has_perm('command_center.view_top_secret'):
            return 'TOP_SECRET'
        elif user.has_perm('command_center.view_secret'):
            return 'SECRET'
        elif user.has_perm('command_center.view_classified'):
            return 'CONFIDENTIAL'
        return 'RESTRICTED'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_clearance'] = self.get_user_clearance_level()
        context['classification_levels'] = DecryptedMessage.CLASSIFICATION_LEVELS
        context['message_types'] = DecryptedMessage.MESSAGE_TYPES
        return context


class NodeMonitoringView(LoginRequiredMixin, ListView):
    """
    Real-time node connectivity monitoring and management
    Shows all network nodes with status, location, and sync state
    """
    model = CommandNode
    template_name = 'command_center/node_monitoring.html'
    context_object_name = 'nodes'
    
    def get_queryset(self):
        return CommandNode.objects.select_related('assigned_personnel').all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Node statistics
        nodes = self.get_queryset()
        context.update({
            'total_nodes': nodes.count(),
            'online_nodes': nodes.filter(status='ONLINE').count(),
            'offline_nodes': nodes.filter(status='OFFLINE').count(),
            'resync_nodes': nodes.filter(status='RESYNC').count(),
            'node_types': CommandNode.NODE_TYPES,
            'node_statuses': CommandNode.NODE_STATUS,
        })
        
        return context


class AlertManagementView(LoginRequiredMixin, ListView):
    """
    Security and system alert management interface
    Handles AI anomaly detection results and system alerts
    """
    model = CommandAlert
    template_name = 'command_center/alert_management.html'
    context_object_name = 'alerts'
    paginate_by = 30
    
    def get_queryset(self):
        queryset = CommandAlert.objects.select_related(
            'source_node', 'related_ledger_entry', 'resolved_by'
        ).all()
        
        # Filter by status
        show_resolved = self.request.GET.get('resolved', 'false')
        if show_resolved != 'true':
            queryset = queryset.filter(is_resolved=False)
            
        # Filter by severity
        severity = self.request.GET.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
            
        # Filter by alert type
        alert_type = self.request.GET.get('type')
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
            
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'alert_types': CommandAlert.ALERT_TYPES,
            'severity_levels': CommandAlert.SEVERITY_LEVELS,
            'unresolved_count': CommandAlert.objects.filter(is_resolved=False).count(),
            'critical_count': CommandAlert.objects.filter(
                is_resolved=False, severity='CRITICAL'
            ).count(),
        })
        return context


class MissionAuditView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Mission audit trails and communication history replay
    Provides comprehensive mission analysis and replay capabilities
    """
    model = MissionAudit
    template_name = 'command_center/mission_audit.html'
    context_object_name = 'missions'
    permission_required = 'command_center.view_mission_audit'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = MissionAudit.objects.select_related('commanding_officer').all()
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        # Search by mission name or code
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(mission_name__icontains=search) |
                Q(mission_code__icontains=search)
            )
            
        return queryset.order_by('-start_time')


# API Endpoints for Real-time Dashboard Updates

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_dashboard_stats(request):
    """
    Real-time dashboard statistics API
    Used by frontend for live updates without page refresh
    """
    stats = {
        'timestamp': timezone.now().isoformat(),
        'nodes': {
            'total': CommandNode.objects.count(),
            'online': CommandNode.objects.filter(status='ONLINE').count(),
            'offline': CommandNode.objects.filter(status='OFFLINE').count(),
            'resync': CommandNode.objects.filter(status='RESYNC').count(),
        },
        'transactions': {
            'total': MasterLedger.objects.count(),
            'last_24h': MasterLedger.objects.filter(
                timestamp__gte=timezone.now() - timedelta(hours=24)
            ).count(),
            'pending_validation': MasterLedger.objects.filter(
                is_validated=False
            ).count(),
        },
        'alerts': {
            'critical': CommandAlert.objects.filter(
                is_resolved=False, severity='CRITICAL'
            ).count(),
            'high': CommandAlert.objects.filter(
                is_resolved=False, severity='HIGH'
            ).count(),
            'total_unresolved': CommandAlert.objects.filter(
                is_resolved=False
            ).count(),
        },
        'missions': {
            'active': MissionAudit.objects.filter(status='ACTIVE').count(),
            'completed_today': MissionAudit.objects.filter(
                status='COMPLETED',
                end_time__gte=timezone.now().replace(hour=0, minute=0, second=0)
            ).count(),
        }
    }
    
    return Response(stats)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_sync_ledger(request):
    """
    Ledger synchronization endpoint for P2P nodes
    Handles conflict resolution using Lamport/Vector clocks
    """
    try:
        node_id = request.data.get('node_id')
        local_blocks = request.data.get('blocks', [])
        
        if not node_id:
            return Response({'error': 'node_id required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        node = get_object_or_404(CommandNode, node_id=node_id)
        
        # TODO: Implement Lamport/Vector clock conflict resolution
        # For now, simple merge strategy
        
        synced_count = 0
        conflicts = []
        
        for block_data in local_blocks:
            # Validate block signature and hash
            # Resolve conflicts using vector clocks
            # Merge into master ledger
            
            # Placeholder implementation
            ledger_entry, created = MasterLedger.objects.get_or_create(
                message_hash=block_data.get('message_hash'),
                defaults={
                    'sender_node': node,
                    'transaction_type': 'SYNC',
                    'payload_encrypted': block_data.get('payload', ''),
                    'lamport_timestamp': block_data.get('lamport_timestamp', 0),
                    'vector_timestamp': block_data.get('vector_timestamp', {}),
                    'previous_hash': block_data.get('previous_hash', ''),
                    'digital_signature': block_data.get('signature', ''),
                    'is_synced': True,
                    'merkle_root': block_data.get('merkle_root', ''),
                }
            )
            
            if created:
                synced_count += 1
                
        # Update node sync status
        node.status = 'ONLINE'
        node.lamport_clock = max(node.lamport_clock, 
                               max([b.get('lamport_timestamp', 0) for b in local_blocks] + [0]))
        node.save()
        
        return Response({
            'status': 'success',
            'synced_blocks': synced_count,
            'conflicts_resolved': len(conflicts),
            'conflicts': conflicts
        })
        
    except Exception as e:
        return Response({'error': str(e)}, 
                      status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_resolve_alert(request, alert_id):
    """
    Resolve security/system alert
    """
    try:
        alert = get_object_or_404(CommandAlert, alert_id=alert_id)
        resolution_notes = request.data.get('resolution_notes', '')
        
        alert.is_resolved = True
        alert.resolved_by = request.user
        alert.resolved_at = timezone.now()
        alert.resolution_notes = resolution_notes
        alert.save()
        
        return Response({'status': 'resolved'})
        
    except Exception as e:
        return Response({'error': str(e)}, 
                      status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_node_status(request):
    """
    Get real-time node connectivity status
    """
    nodes = CommandNode.objects.all()
    node_data = []
    
    for node in nodes:
        node_data.append({
            'id': str(node.node_id),
            'name': node.node_name,
            'type': node.node_type,
            'status': node.status,
            'last_seen': node.last_seen.isoformat(),
            'is_online': node.is_online,
            'location': {
                'lat': float(node.location_lat) if node.location_lat else None,
                'lon': float(node.location_lon) if node.location_lon else None,
            },
            'assigned_personnel': node.assigned_personnel.username if node.assigned_personnel else None,
        })
    
    return Response({'nodes': node_data})


# Utility functions for encryption/decryption
# TODO: Implement proper AES + RSA encryption/decryption

def decrypt_message_content(encrypted_payload, private_key):
    """
    Decrypt AES encrypted message content using RSA private key
    Placeholder for actual encryption implementation
    """
    # TODO: Implement AES decryption with RSA key exchange
    return "DECRYPTED_CONTENT_PLACEHOLDER"


def verify_digital_signature(message_hash, signature, public_key):
    """
    Verify RSA digital signature for message authentication
    Placeholder for actual signature verification
    """
    # TODO: Implement RSA signature verification
    return True