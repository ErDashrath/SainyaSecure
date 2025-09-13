"""
Command Center Signal Handlers

Automated operations triggered by system events:
- Auto-create alerts for anomalies and system events
- Sync master ledger when new transactions arrive
- Update node status based on activity
- Trigger decryption for authorized content
- Log access attempts and security events
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import CommandNode, MasterLedger, DecryptedMessage, CommandAlert
from messaging.models import Message
from ai_anomaly.models import AnomalyAlert
from blockchain.models import LocalLedgerBlock

User = get_user_model()


@receiver(post_save, sender=AnomalyAlert)
def create_command_alert_from_ai(sender, instance, created, **kwargs):
    """
    Automatically create command center alert when AI detects anomaly
    """
    if created:
        # Determine severity based on AI confidence score
        severity = 'CRITICAL' if instance.confidence_score > 0.9 else 'HIGH' if instance.confidence_score > 0.7 else 'MEDIUM'
        
        CommandAlert.objects.create(
            alert_type='ANOMALY',
            severity=severity,
            title=f"AI Anomaly Detected: {instance.anomaly_type}",
            description=f"AI system detected {instance.anomaly_type} with confidence {instance.confidence_score:.2%}. Details: {instance.details}",
            ai_confidence_score=instance.confidence_score,
            metadata={
                'ai_model': instance.model_used,
                'anomaly_type': instance.anomaly_type,
                'original_alert_id': str(instance.id)
            }
        )


@receiver(post_save, sender=LocalLedgerBlock)
def sync_to_master_ledger(sender, instance, created, **kwargs):
    """
    Automatically sync local ledger blocks to master ledger
    """
    if created and not instance.is_synced:
        try:
            # Create corresponding master ledger entry
            master_entry = MasterLedger.objects.create(
                transaction_type='MESSAGE',
                sender_node_id=instance.sender_id,
                receiver_node_id=instance.receiver_id,
                message_hash=instance.block_hash,
                payload_encrypted=instance.encrypted_content,
                previous_hash=instance.previous_hash,
                merkle_root=instance.merkle_root,
                lamport_timestamp=instance.lamport_timestamp,
                vector_timestamp=instance.vector_clock or {},
                digital_signature=instance.digital_signature,
                is_validated=False,  # Will be validated separately
                is_synced=True
            )
            
            # Mark local block as synced
            instance.is_synced = True
            instance.master_ledger_id = master_entry.block_id
            instance.save(update_fields=['is_synced', 'master_ledger_id'])
            
        except Exception as e:
            # Create alert for sync failure
            CommandAlert.objects.create(
                alert_type='SYNC_CONFLICT',
                severity='HIGH',
                title='Ledger Sync Failed',
                description=f'Failed to sync local ledger block {instance.id} to master ledger: {str(e)}',
                metadata={'local_block_id': str(instance.id), 'error': str(e)}
            )


@receiver(post_save, sender=Message)
def update_node_activity(sender, instance, created, **kwargs):
    """
    Update node last_seen timestamp when messages are sent/received
    """
    if created:
        # Update sender node activity
        try:
            sender_node = CommandNode.objects.get(assigned_personnel=instance.sender)
            sender_node.last_seen = timezone.now()
            sender_node.status = 'ONLINE'
            sender_node.save(update_fields=['last_seen', 'status'])
        except CommandNode.DoesNotExist:
            pass
        
        # Update receiver node activity if applicable
        for participant in instance.conversation.participants.all():
            if participant != instance.sender:
                try:
                    receiver_node = CommandNode.objects.get(assigned_personnel=participant)
                    receiver_node.last_seen = timezone.now()
                    if receiver_node.status == 'OFFLINE':
                        receiver_node.status = 'ONLINE'
                    receiver_node.save(update_fields=['last_seen', 'status'])
                except CommandNode.DoesNotExist:
                    pass


@receiver(pre_save, sender=CommandNode)
def monitor_node_status_changes(sender, instance, **kwargs):
    """
    Create alerts when node status changes to offline or compromised
    """
    if instance.pk:  # Only for updates, not new creates
        try:
            old_instance = CommandNode.objects.get(pk=instance.pk)
            
            # Alert on status changes to critical states
            if old_instance.status != instance.status:
                if instance.status == 'OFFLINE':
                    CommandAlert.objects.create(
                        alert_type='NODE_OFFLINE',
                        severity='MEDIUM',
                        title=f'Node {instance.node_name} Offline',
                        description=f'Node {instance.node_name} ({instance.get_node_type_display()}) has gone offline.',
                        source_node=instance,
                        metadata={
                            'previous_status': old_instance.status,
                            'new_status': instance.status,
                            'assigned_personnel': instance.assigned_personnel.username if instance.assigned_personnel else None
                        }
                    )
                    
                elif instance.status == 'COMPROMISED':
                    CommandAlert.objects.create(
                        alert_type='SECURITY',
                        severity='CRITICAL',
                        title=f'Node {instance.node_name} Compromised',
                        description=f'CRITICAL: Node {instance.node_name} has been marked as compromised. Immediate action required.',
                        source_node=instance,
                        metadata={
                            'previous_status': old_instance.status,
                            'security_incident': True,
                            'assigned_personnel': instance.assigned_personnel.username if instance.assigned_personnel else None
                        }
                    )
                    
        except CommandNode.DoesNotExist:
            pass


@receiver(post_save, sender=DecryptedMessage)
def log_message_access(sender, instance, created, **kwargs):
    """
    Log access to decrypted messages for audit purposes
    """
    if created:
        instance.log_access(
            user=instance.decrypted_by,
            action='DECRYPT'
        )
        
        # Create audit alert for high-classification decryptions
        if instance.classification in ['SECRET', 'TOP_SECRET']:
            CommandAlert.objects.create(
                alert_type='SECURITY',
                severity='MEDIUM' if instance.classification == 'SECRET' else 'HIGH',
                title=f'{instance.classification} Message Decrypted',
                description=f'User {instance.decrypted_by.username} decrypted a {instance.classification} message: {instance.subject[:100]}',
                related_ledger_entry=instance.ledger_entry,
                metadata={
                    'classification': instance.classification,
                    'decrypted_by': instance.decrypted_by.username,
                    'message_type': instance.message_type,
                    'subject': instance.subject[:100]
                }
            )


@receiver(post_save, sender=MasterLedger)
def validate_ledger_entry(sender, instance, created, **kwargs):
    """
    Automatically validate new master ledger entries
    """
    if created and not instance.is_validated:
        # TODO: Implement proper cryptographic validation
        # For now, simple validation based on signature presence
        
        if instance.digital_signature and instance.message_hash:
            # Placeholder validation logic
            instance.is_validated = True
            instance.save(update_fields=['is_validated'])
            
        else:
            # Create alert for invalid ledger entry
            CommandAlert.objects.create(
                alert_type='MESSAGE_INTEGRITY',
                severity='HIGH',
                title='Invalid Ledger Entry',
                description=f'Ledger entry {instance.block_height} failed validation. Missing signature or hash.',
                related_ledger_entry=instance,
                metadata={
                    'validation_failure': True,
                    'block_height': instance.block_height,
                    'sender_node': instance.sender_node.node_name
                }
            )


# Periodic tasks (to be called via Celery)
def check_node_heartbeats():
    """
    Periodic task to check node heartbeats and mark inactive nodes as offline
    Should be called every 5 minutes
    """
    from datetime import timedelta
    
    offline_threshold = timezone.now() - timedelta(minutes=5)
    
    # Find nodes that haven't been seen recently but are marked as online
    stale_nodes = CommandNode.objects.filter(
        status='ONLINE',
        last_seen__lt=offline_threshold
    )
    
    for node in stale_nodes:
        node.status = 'OFFLINE'
        node.save(update_fields=['status'])
        
        # This will trigger the pre_save signal to create an alert


def cleanup_old_alerts():
    """
    Periodic task to clean up old resolved alerts
    Should be called daily
    """
    from datetime import timedelta
    
    # Delete resolved alerts older than 30 days
    old_alerts = CommandAlert.objects.filter(
        is_resolved=True,
        resolved_at__lt=timezone.now() - timedelta(days=30)
    )
    
    deleted_count = old_alerts.count()
    old_alerts.delete()
    
    return f"Cleaned up {deleted_count} old alerts"