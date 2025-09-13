"""
Command Center Django App - Master Authority Module

This app serves as the central command authority with:
- Full access to all nodes, logs, and blockchain ledger
- Real-time dashboard for message logs (text, voice, video) 
- Blockchain ledger explorer with immutable audit trails
- AI anomaly detection alerts and monitoring
- Node connectivity status tracking
- Mission history replay and audit capabilities
- Lamport/Vector clock conflict resolution during resync

Encryption Flow:
- Receives encrypted payloads from soldiers (code words → AES + RSA)
- Authorized decryption for command personnel only
- All decrypted messages stored immutably in blockchain ledger
- Maintains master ledger as source of truth
"""

from django.apps import AppConfig


class CommandCenterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'command_center'
    verbose_name = 'Military Command Center'
    
    def ready(self):
        import command_center.signals