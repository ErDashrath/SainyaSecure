"""
Admin configuration for Army1 Frontend models
Provides comprehensive CRUD interface for command center operations
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    CommandSecurityEvent, MilitaryMessage, Personnel, 
    MilitaryDevice, Mission, SystemLog, OperationalLedger
)


@admin.register(CommandSecurityEvent)
class CommandSecurityEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'user', 'severity', 'ip_address', 'timestamp', 'resolved', 'resolved_status')
    list_filter = ('event_type', 'severity', 'resolved', 'timestamp')
    search_fields = ('user__username', 'ip_address', 'description', 'module_accessed')
    readonly_fields = ('event_id', 'timestamp')
    date_hierarchy = 'timestamp'
    actions = ['mark_resolved', 'mark_unresolved']
    
    def resolved_status(self, obj):
        if obj.resolved:
            return format_html('<span style="color: green;">✓ Resolved</span>')
        else:
            return format_html('<span style="color: red;">✗ Unresolved</span>')
    resolved_status.short_description = 'Status'
    
    def mark_resolved(self, request, queryset):
        queryset.update(resolved=True, resolved_by=request.user)
        self.message_user(request, f'{queryset.count()} events marked as resolved.')
    mark_resolved.short_description = 'Mark selected events as resolved'
    
    def mark_unresolved(self, request, queryset):
        queryset.update(resolved=False, resolved_by=None)
        self.message_user(request, f'{queryset.count()} events marked as unresolved.')
    mark_unresolved.short_description = 'Mark selected events as unresolved'


@admin.register(MilitaryMessage)
class MilitaryMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sender', 'priority', 'classification', 'status', 'created_at', 'sent_at')
    list_filter = ('priority', 'classification', 'status', 'is_encrypted', 'requires_receipt')
    search_fields = ('subject', 'sender__username', 'body')
    readonly_fields = ('message_id', 'created_at', 'sent_at')
    filter_horizontal = ('recipients',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Message Details', {
            'fields': ('sender', 'recipients', 'subject', 'body')
        }),
        ('Classification & Priority', {
            'fields': ('priority', 'classification', 'status')
        }),
        ('Security Options', {
            'fields': ('is_encrypted', 'requires_receipt', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'sent_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Personnel)
class PersonnelAdmin(admin.ModelAdmin):
    list_display = ('service_number', 'full_name', 'rank_display', 'current_assignment', 'status', 'location')
    list_filter = ('status', 'military_user__rank', 'military_user__branch')
    search_fields = ('first_name', 'last_name', 'service_number', 'current_assignment')
    readonly_fields = ('personnel_id', 'created_at', 'updated_at')
    date_hierarchy = 'enlistment_date'
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Full Name'
    
    def rank_display(self, obj):
        return obj.military_user.get_rank_display()
    rank_display.short_description = 'Rank'
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('military_user', 'first_name', 'last_name', 'service_number', 'date_of_birth')
        }),
        ('Military Service', {
            'fields': ('enlistment_date', 'current_assignment', 'location', 'status')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone')
        }),
        ('Medical & Notes', {
            'fields': ('medical_notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(MilitaryDevice)
class MilitaryDeviceAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'device_type', 'model', 'assigned_to', 'status', 'location', 'maintenance_status')
    list_filter = ('device_type', 'status', 'last_maintenance')
    search_fields = ('serial_number', 'model', 'location')
    readonly_fields = ('device_id', 'created_at', 'updated_at')
    date_hierarchy = 'acquisition_date'
    
    def maintenance_status(self, obj):
        if obj.next_maintenance:
            from django.utils import timezone
            if obj.next_maintenance < timezone.now().date():
                return format_html('<span style="color: red;">Overdue</span>')
            else:
                return format_html('<span style="color: green;">Scheduled</span>')
        return 'Not Scheduled'
    maintenance_status.short_description = 'Maintenance'
    
    fieldsets = (
        ('Device Information', {
            'fields': ('serial_number', 'device_type', 'model', 'status')
        }),
        ('Assignment & Location', {
            'fields': ('assigned_to', 'location')
        }),
        ('Maintenance', {
            'fields': ('last_maintenance', 'next_maintenance')
        }),
        ('Acquisition', {
            'fields': ('acquisition_date', 'acquisition_cost')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        })
    )


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ('mission_code', 'mission_name', 'commander', 'status', 'classification', 'start_date', 'location')
    list_filter = ('status', 'classification', 'start_date')
    search_fields = ('mission_name', 'mission_code', 'location', 'commander__first_name', 'commander__last_name')
    readonly_fields = ('mission_id', 'created_at', 'updated_at')
    filter_horizontal = ('assigned_personnel',)
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Mission Overview', {
            'fields': ('mission_name', 'mission_code', 'description', 'classification')
        }),
        ('Command & Personnel', {
            'fields': ('commander', 'assigned_personnel')
        }),
        ('Timeline & Location', {
            'fields': ('start_date', 'end_date', 'location', 'status')
        }),
        ('Mission Details', {
            'fields': ('objectives', 'resources_required', 'risk_assessment')
        })
    )


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'level', 'category', 'source', 'user', 'message_preview')
    list_filter = ('level', 'category', 'source', 'timestamp')
    search_fields = ('message', 'source', 'user__username')
    readonly_fields = ('log_id', 'timestamp')
    date_hierarchy = 'timestamp'
    
    def message_preview(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_preview.short_description = 'Message'
    
    def has_add_permission(self, request):
        # System logs should be created programmatically
        return False


@admin.register(OperationalLedger)
class OperationalLedgerAdmin(admin.ModelAdmin):
    list_display = ('transaction_date', 'transaction_type', 'description', 'amount', 'currency', 'authorized_by', 'cost_center')
    list_filter = ('transaction_type', 'currency', 'fiscal_year', 'transaction_date')
    search_fields = ('description', 'cost_center', 'authorized_by__first_name', 'authorized_by__last_name')
    readonly_fields = ('ledger_id', 'created_at')
    date_hierarchy = 'transaction_date'
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('transaction_type', 'description', 'amount', 'currency', 'transaction_date')
        }),
        ('Authorization & Cost Center', {
            'fields': ('authorized_by', 'cost_center', 'fiscal_year')
        }),
        ('Related Items', {
            'fields': ('mission', 'device')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('authorized_by', 'mission', 'device')


# Customize admin site header
admin.site.site_header = 'SainyaSecure Command Center'
admin.site.site_title = 'Command Center Admin'
admin.site.index_title = 'Military Operations Management'