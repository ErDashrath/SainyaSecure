"""
Command Center Admin Configuration

Provides Django admin interface for command center management:
- Node connectivity monitoring and management
- Master blockchain ledger inspection  
- Decrypted message access control
- Security alert management
- Mission audit trail administration
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils import timezone
from .models import CommandNode, MasterLedger, DecryptedMessage, CommandAlert, MissionAudit


@admin.register(CommandNode)
class CommandNodeAdmin(admin.ModelAdmin):
    list_display = ('node_name', 'node_type', 'status_indicator', 'last_seen', 'is_online', 'assigned_personnel', 'location_display')
    list_filter = ('node_type', 'status', 'last_seen')
    search_fields = ('node_name', 'ip_address', 'assigned_personnel__username')
    readonly_fields = ('node_id', 'created_at', 'updated_at', 'last_seen')
    
    fieldsets = (
        ('Node Information', {
            'fields': ('node_name', 'node_type', 'status', 'ip_address', 'assigned_personnel')
        }),
        ('Location', {
            'fields': ('location_lat', 'location_lon'),
            'classes': ('collapse',)
        }),
        ('Synchronization', {
            'fields': ('lamport_clock', 'vector_clock'),
            'classes': ('collapse',)
        }),
        ('Security', {
            'fields': ('public_key',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_seen'),
            'classes': ('collapse',)
        })
    )
    
    def status_indicator(self, obj):
        colors = {
            'ONLINE': 'green',
            'OFFLINE': 'red', 
            'RESYNC': 'orange',
            'COMPROMISED': 'darkred',
            'MAINTENANCE': 'blue'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {};">● {}</span>',
            color,
            obj.get_status_display()
        )
    status_indicator.short_description = 'Status'
    
    def location_display(self, obj):
        if obj.location_lat and obj.location_lon:
            return f"{obj.location_lat}, {obj.location_lon}"
        return "No location"
    location_display.short_description = 'Location'
    
    def is_online(self, obj):
        return obj.is_online
    is_online.boolean = True
    is_online.short_description = 'Online Now'


@admin.register(MasterLedger)
class MasterLedgerAdmin(admin.ModelAdmin):
    list_display = ('block_height', 'transaction_type', 'sender_node', 'receiver_node', 'timestamp', 'is_validated', 'is_synced')
    list_filter = ('transaction_type', 'is_validated', 'is_synced', 'timestamp')
    search_fields = ('message_hash', 'sender_node__node_name', 'receiver_node__node_name')
    readonly_fields = ('block_id', 'block_height', 'message_hash', 'timestamp', 'lamport_timestamp')
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Block Information', {
            'fields': ('block_height', 'transaction_type', 'message_hash', 'timestamp')
        }),
        ('Nodes', {
            'fields': ('sender_node', 'receiver_node')
        }),
        ('Content', {
            'fields': ('payload_encrypted', 'payload_decrypted'),
            'classes': ('collapse',)
        }),
        ('Blockchain', {
            'fields': ('previous_hash', 'merkle_root', 'nonce', 'difficulty'),
            'classes': ('collapse',)
        }),
        ('Synchronization', {
            'fields': ('lamport_timestamp', 'vector_timestamp', 'is_validated', 'is_synced', 'sync_conflicts'),
            'classes': ('collapse',)
        }),
        ('Security', {
            'fields': ('digital_signature',),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        # Ledger entries should only be created through sync process
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Immutable ledger - no deletions allowed
        return False


@admin.register(DecryptedMessage)
class DecryptedMessageAdmin(admin.ModelAdmin):
    list_display = ('subject_preview', 'message_type', 'classification', 'sender_node', 'decrypted_by', 'decrypted_at')
    list_filter = ('message_type', 'classification', 'decrypted_at')
    search_fields = ('subject', 'content', 'ledger_entry__sender_node__node_name')
    readonly_fields = ('message_id', 'decrypted_at', 'access_log')
    date_hierarchy = 'decrypted_at'
    
    fieldsets = (
        ('Message Information', {
            'fields': ('ledger_entry', 'message_type', 'classification', 'subject')
        }),
        ('Content', {
            'fields': ('content', 'code_words_used', 'media_attachments')
        }),
        ('Security', {
            'fields': ('decrypted_by', 'decrypted_at', 'access_log'),
            'classes': ('collapse',)
        })
    )
    
    def subject_preview(self, obj):
        return obj.subject[:50] + '...' if len(obj.subject) > 50 else obj.subject
    subject_preview.short_description = 'Subject'
    
    def sender_node(self, obj):
        return obj.ledger_entry.sender_node.node_name
    sender_node.short_description = 'Sender'
    
    def has_change_permission(self, request, obj=None):
        # Check if user has appropriate clearance level
        if obj and obj.classification == 'TOP_SECRET':
            return request.user.has_perm('command_center.view_top_secret')
        elif obj and obj.classification == 'SECRET':
            return request.user.has_perm('command_center.view_secret')
        return request.user.has_perm('command_center.view_classified')


@admin.register(CommandAlert)
class CommandAlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'alert_type', 'severity_indicator', 'source_node', 'is_resolved', 'created_at')
    list_filter = ('alert_type', 'severity', 'is_resolved', 'created_at')
    search_fields = ('title', 'description', 'source_node__node_name')
    readonly_fields = ('alert_id', 'created_at', 'resolved_at')
    date_hierarchy = 'created_at'
    actions = ['mark_resolved', 'mark_unresolved']
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('alert_type', 'severity', 'title', 'description')
        }),
        ('Source', {
            'fields': ('source_node', 'related_ledger_entry')
        }),
        ('AI Analysis', {
            'fields': ('ai_confidence_score', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolved_by', 'resolved_at', 'resolution_notes')
        })
    )
    
    def severity_indicator(self, obj):
        colors = {
            'LOW': 'green',
            'MEDIUM': 'orange',
            'HIGH': 'red',
            'CRITICAL': 'darkred'
        }
        color = colors.get(obj.severity, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_severity_display()
        )
    severity_indicator.short_description = 'Severity'
    
    def mark_resolved(self, request, queryset):
        queryset.update(
            is_resolved=True,
            resolved_by=request.user,
            resolved_at=timezone.now()
        )
        self.message_user(request, f'{queryset.count()} alerts marked as resolved.')
    mark_resolved.short_description = 'Mark selected alerts as resolved'
    
    def mark_unresolved(self, request, queryset):
        queryset.update(
            is_resolved=False,
            resolved_by=None,
            resolved_at=None
        )
        self.message_user(request, f'{queryset.count()} alerts marked as unresolved.')
    mark_unresolved.short_description = 'Mark selected alerts as unresolved'


@admin.register(MissionAudit)
class MissionAuditAdmin(admin.ModelAdmin):
    list_display = ('mission_code', 'mission_name', 'status', 'commanding_officer', 'start_time', 'total_communications')
    list_filter = ('status', 'classification_level', 'start_time')
    search_fields = ('mission_name', 'mission_code', 'commanding_officer__username')
    readonly_fields = ('audit_id', 'created_at', 'updated_at', 'mission_duration', 'total_communications')
    filter_horizontal = ('participating_nodes', 'related_ledger_entries')
    date_hierarchy = 'start_time'
    
    fieldsets = (
        ('Mission Information', {
            'fields': ('mission_name', 'mission_code', 'status', 'classification_level')
        }),
        ('Timeline', {
            'fields': ('start_time', 'end_time', 'mission_duration')
        }),
        ('Personnel & Resources', {
            'fields': ('commanding_officer', 'participating_nodes')
        }),
        ('Mission Details', {
            'fields': ('objectives', 'outcomes', 'audit_notes')
        }),
        ('Communication History', {
            'fields': ('related_ledger_entries', 'total_communications'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def mission_duration(self, obj):
        return obj.mission_duration
    mission_duration.short_description = 'Duration'
    
    def total_communications(self, obj):
        return obj.total_communications
    total_communications.short_description = 'Total Communications'


# Customize admin site
admin.site.site_header = 'SainyaSecure Command Center'
admin.site.site_title = 'Command Center Admin'
admin.site.index_title = 'Military Command & Control Administration'