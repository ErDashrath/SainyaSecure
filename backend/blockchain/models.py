"""
Military Communication System - Blockchain Models

This module defines models for blockchain-based immutable logging:
- Local ledger blocks for offline-first operation
- Blockchain transaction tracking
- Message integrity and audit trails
- Consensus and verification mechanisms
"""

from django.db import models
from django.utils import timezone
from users.models import MilitaryUser, Device
from messaging.models import Message
import uuid
import hashlib
import json


class LocalLedgerBlock(models.Model):
    """
    Local blockchain ledger block for offline-first operation
    
    Features:
    - Offline message logging
    - Cryptographic integrity
    - Merkle tree verification
    - Sync with main blockchain
    """
    
    BLOCK_STATUS = [
        ('PENDING', 'Pending Sync'),
        ('SYNCING', 'Syncing to Blockchain'),
        ('CONFIRMED', 'Confirmed on Blockchain'),
        ('FAILED', 'Sync Failed'),
        ('ORPHANED', 'Orphaned Block'),
    ]
    
    # Block identification
    block_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    block_number = models.BigIntegerField(help_text="Sequential block number")
    previous_block_hash = models.CharField(max_length=64, help_text="Hash of previous block")
    block_hash = models.CharField(max_length=64, unique=True, help_text="Current block hash")
    
    # Block content
    merkle_root = models.CharField(max_length=64, help_text="Merkle tree root of transactions")
    transaction_count = models.IntegerField(default=0)
    
    # Device and location context
    created_by_device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='created_blocks')
    device_location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    device_location_lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    offline_timestamp = models.DateTimeField(help_text="Timestamp when created offline")
    
    # Blockchain sync status
    sync_status = models.CharField(max_length=10, choices=BLOCK_STATUS, default='PENDING')
    blockchain_tx_hash = models.CharField(max_length=66, blank=True, help_text="Ethereum transaction hash")
    blockchain_block_number = models.BigIntegerField(null=True, blank=True)
    sync_attempts = models.IntegerField(default=0)
    last_sync_attempt = models.DateTimeField(null=True, blank=True)
    sync_error = models.TextField(blank=True)
    
    # Verification
    nonce = models.BigIntegerField(default=0, help_text="Proof of work nonce")
    difficulty = models.IntegerField(default=1, help_text="Mining difficulty")
    is_verified = models.BooleanField(default=False)
    verification_signature = models.TextField(blank=True)
    
    class Meta:
        db_table = 'local_ledger_blocks'
        verbose_name = 'Local Ledger Block'
        verbose_name_plural = 'Local Ledger Blocks'
        ordering = ['block_number']
        indexes = [
            models.Index(fields=['block_number']),
            models.Index(fields=['sync_status']),
            models.Index(fields=['created_by_device', 'timestamp']),
            models.Index(fields=['blockchain_tx_hash']),
        ]
    
    def __str__(self):
        return f"Block #{self.block_number} - {self.sync_status}"
    
    def calculate_block_hash(self):
        """Calculate the hash of this block"""
        block_data = {
            'block_number': self.block_number,
            'previous_block_hash': self.previous_block_hash,
            'merkle_root': self.merkle_root,
            'timestamp': self.offline_timestamp.isoformat(),
            'nonce': self.nonce,
        }
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def is_hash_valid(self):
        """Verify the block hash is correct"""
        return self.block_hash == self.calculate_block_hash()
    
    def mine_block(self):
        """Simple proof of work mining"""
        target = "0" * self.difficulty
        while not self.block_hash.startswith(target):
            self.nonce += 1
            self.block_hash = self.calculate_block_hash()
        self.is_verified = True


class MessageTransaction(models.Model):
    """
    Individual message transaction within a block
    
    Features:
    - Message integrity verification
    - Digital signatures
    - Transaction linking
    - Audit trail support
    """
    
    TRANSACTION_TYPES = [
        ('MESSAGE_SENT', 'Message Sent'),
        ('MESSAGE_DELIVERED', 'Message Delivered'),
        ('MESSAGE_READ', 'Message Read'),
        ('MESSAGE_DELETED', 'Message Deleted'),
        ('FILE_TRANSFERRED', 'File Transferred'),
        ('VOICE_CALL', 'Voice Call'),
        ('VIDEO_CALL', 'Video Call'),
    ]
    
    # Transaction identification
    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    block = models.ForeignKey(LocalLedgerBlock, on_delete=models.CASCADE, related_name='transactions')
    transaction_index = models.IntegerField(help_text="Index within the block")
    
    # Message reference
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='blockchain_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    
    # Participants
    sender = models.ForeignKey(MilitaryUser, on_delete=models.CASCADE, related_name='sent_transactions')
    sender_device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='sent_transactions')
    recipients = models.ManyToManyField(MilitaryUser, related_name='received_transactions')
    
    # Transaction data (encrypted)
    transaction_data_encrypted = models.TextField(help_text="Encrypted transaction details")
    transaction_hash = models.CharField(max_length=64, unique=True)
    
    # Verification
    digital_signature = models.TextField(help_text="Sender's digital signature")
    is_signature_valid = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    message_timestamp = models.DateTimeField(help_text="Original message timestamp")
    
    # Audit metadata
    device_fingerprint = models.TextField(help_text="Device fingerprint at time of transaction")
    location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    network_info = models.JSONField(default=dict, help_text="Network context information")
    
    class Meta:
        db_table = 'message_transactions'
        verbose_name = 'Message Transaction'
        verbose_name_plural = 'Message Transactions'
        ordering = ['block', 'transaction_index']
        indexes = [
            models.Index(fields=['message', 'transaction_type']),
            models.Index(fields=['sender', 'created_at']),
            models.Index(fields=['block', 'transaction_index']),
            models.Index(fields=['transaction_hash']),
        ]
    
    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.transaction_type}"
    
    def calculate_transaction_hash(self):
        """Calculate hash of transaction data"""
        tx_data = {
            'transaction_id': str(self.transaction_id),
            'message_id': str(self.message.message_id),
            'sender_id': str(self.sender.military_id),
            'transaction_type': self.transaction_type,
            'timestamp': self.message_timestamp.isoformat(),
        }
        tx_string = json.dumps(tx_data, sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()


class BlockchainTransaction(models.Model):
    """
    Track transactions on the main blockchain network
    
    Features:
    - Ethereum/Hyperledger integration
    - Gas cost tracking
    - Transaction confirmation monitoring
    - Network status tracking
    """
    
    BLOCKCHAIN_NETWORKS = [
        ('ETHEREUM_PRIVATE', 'Private Ethereum'),
        ('ETHEREUM_TESTNET', 'Ethereum Testnet'),
        ('HYPERLEDGER_FABRIC', 'Hyperledger Fabric'),
        ('POLYGON', 'Polygon Network'),
    ]
    
    TX_STATUS = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('FAILED', 'Failed'),
        ('DROPPED', 'Dropped'),
    ]
    
    # Transaction identification
    tx_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    blockchain_network = models.CharField(max_length=20, choices=BLOCKCHAIN_NETWORKS)
    transaction_hash = models.CharField(max_length=66, unique=True)
    block_hash = models.CharField(max_length=66, blank=True)
    block_number = models.BigIntegerField(null=True, blank=True)
    
    # Related local data
    local_block = models.OneToOneField(LocalLedgerBlock, on_delete=models.CASCADE, related_name='blockchain_tx')
    
    # Transaction details
    from_address = models.CharField(max_length=42, help_text="Sender blockchain address")
    to_address = models.CharField(max_length=42, help_text="Recipient blockchain address")
    gas_used = models.BigIntegerField(null=True, blank=True)
    gas_price = models.BigIntegerField(null=True, blank=True)
    transaction_fee = models.DecimalField(max_digits=20, decimal_places=10, null=True, blank=True)
    
    # Status tracking
    status = models.CharField(max_length=10, choices=TX_STATUS, default='PENDING')
    confirmations = models.IntegerField(default=0)
    required_confirmations = models.IntegerField(default=6)
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    
    # Smart contract interaction
    contract_address = models.CharField(max_length=42, blank=True)
    contract_method = models.CharField(max_length=100, blank=True)
    contract_data = models.TextField(blank=True, help_text="Contract interaction data")
    
    class Meta:
        db_table = 'blockchain_transactions'
        verbose_name = 'Blockchain Transaction'
        verbose_name_plural = 'Blockchain Transactions'
        indexes = [
            models.Index(fields=['transaction_hash']),
            models.Index(fields=['status', 'submitted_at']),
            models.Index(fields=['blockchain_network', 'block_number']),
            models.Index(fields=['from_address']),
        ]
    
    def __str__(self):
        return f"Blockchain TX {self.transaction_hash[:10]}... - {self.status}"
    
    def is_confirmed(self):
        """Check if transaction has enough confirmations"""
        return self.confirmations >= self.required_confirmations
    
    def calculate_fee_in_usd(self, eth_price_usd=None):
        """Calculate transaction fee in USD (if ETH price provided)"""
        if self.transaction_fee and eth_price_usd:
            return float(self.transaction_fee) * eth_price_usd
        return None


class AuditLog(models.Model):
    """
    Immutable audit log for compliance and forensics
    
    Features:
    - Tamper-proof logging
    - Compliance reporting
    - Forensic investigation support
    - Chain of custody
    """
    
    LOG_TYPES = [
        ('MESSAGE_SENT', 'Message Sent'),
        ('MESSAGE_READ', 'Message Read'),
        ('FILE_ACCESSED', 'File Accessed'),
        ('USER_LOGIN', 'User Login'),
        ('USER_LOGOUT', 'User Logout'),
        ('SECURITY_EVENT', 'Security Event'),
        ('SYSTEM_ACCESS', 'System Access'),
        ('DATA_EXPORT', 'Data Export'),
        ('ADMIN_ACTION', 'Admin Action'),
        ('BLOCKCHAIN_SYNC', 'Blockchain Sync'),
    ]
    
    # Log entry identification
    log_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    log_type = models.CharField(max_length=20, choices=LOG_TYPES)
    
    # Associated entities
    user = models.ForeignKey(MilitaryUser, on_delete=models.CASCADE, null=True, blank=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, null=True, blank=True)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, blank=True)
    transaction = models.ForeignKey(MessageTransaction, on_delete=models.CASCADE, null=True, blank=True)
    
    # Log data
    description = models.TextField()
    log_data = models.JSONField(default=dict, help_text="Structured log data")
    
    # Integrity protection
    previous_log_hash = models.CharField(max_length=64, help_text="Hash of previous log entry")
    log_hash = models.CharField(max_length=64, unique=True, help_text="Hash of this log entry")
    
    # Context information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Timestamps (immutable)
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)
    
    # Blockchain anchoring
    blockchain_anchored = models.BooleanField(default=False)
    blockchain_tx_hash = models.CharField(max_length=66, blank=True)
    anchor_block_number = models.BigIntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['device', 'timestamp']),
            models.Index(fields=['log_type', 'timestamp']),
            models.Index(fields=['blockchain_anchored']),
        ]
    
    def __str__(self):
        return f"Audit: {self.log_type} - {self.timestamp}"
    
    def calculate_log_hash(self):
        """Calculate hash of this log entry"""
        log_data = {
            'log_id': str(self.log_id),
            'log_type': self.log_type,
            'description': self.description,
            'timestamp': self.timestamp.isoformat(),
            'previous_log_hash': self.previous_log_hash,
        }
        log_string = json.dumps(log_data, sort_keys=True)
        return hashlib.sha256(log_string.encode()).hexdigest()
    
    def verify_integrity(self):
        """Verify log entry integrity"""
        return self.log_hash == self.calculate_log_hash()


class BlockchainSyncStatus(models.Model):
    """
    Track overall blockchain synchronization status
    
    Features:
    - Network health monitoring
    - Sync performance metrics
    - Error tracking and recovery
    """
    
    # Device tracking
    device = models.OneToOneField(Device, on_delete=models.CASCADE, related_name='blockchain_sync_status')
    
    # Sync status
    is_syncing = models.BooleanField(default=False)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    next_sync_at = models.DateTimeField(null=True, blank=True)
    sync_interval = models.IntegerField(default=300, help_text="Sync interval in seconds")
    
    # Progress tracking
    total_blocks_to_sync = models.IntegerField(default=0)
    blocks_synced = models.IntegerField(default=0)
    sync_progress_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    # Network status
    blockchain_height = models.BigIntegerField(default=0, help_text="Latest blockchain height")
    local_height = models.BigIntegerField(default=0, help_text="Local ledger height")
    peer_count = models.IntegerField(default=0, help_text="Connected peer count")
    network_latency_ms = models.IntegerField(null=True, blank=True)
    
    # Error tracking
    consecutive_failures = models.IntegerField(default=0)
    last_error = models.TextField(blank=True)
    last_error_at = models.DateTimeField(null=True, blank=True)
    
    # Performance metrics
    avg_sync_time_seconds = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    blocks_per_second = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'blockchain_sync_status'
        verbose_name = 'Blockchain Sync Status'
        verbose_name_plural = 'Blockchain Sync Statuses'
    
    def __str__(self):
        return f"Sync Status for {self.device.name} - {self.sync_progress_percent}%"
    
    def is_fully_synced(self):
        """Check if device is fully synced with blockchain"""
        return self.local_height >= self.blockchain_height
    
    def calculate_sync_progress(self):
        """Calculate sync progress percentage"""
        if self.total_blocks_to_sync > 0:
            progress = (self.blocks_synced / self.total_blocks_to_sync) * 100
            self.sync_progress_percent = min(100.0, progress)
        else:
            self.sync_progress_percent = 0.0
