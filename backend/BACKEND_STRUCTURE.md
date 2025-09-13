# Military Communication System - Backend Structure

## Django Apps Created

### 1. users/
**Purpose**: Soldier/device management, WebAuthn/JWT authentication
- User authentication and authorization
- Device registration and management
- Role-based access control for military hierarchy

### 2. messaging/
**Purpose**: Send/receive messages, local and server metadata logging  
- Encrypted message handling (text, voice, video)
- Message metadata and logging
- Real-time message delivery via WebSockets

### 3. p2p_sync/
**Purpose**: Offline-first sync, local ledger management
- Offline message buffering and caching
- Peer-to-peer communication fallback
- Local blockchain ledger synchronization

### 4. blockchain/
**Purpose**: Blockchain interface for immutable logs
- Integration with private Ethereum/Hyperledger Fabric
- Immutable message logging and audit trails
- Blockchain transaction management

### 5. ai_anomaly/
**Purpose**: NLP/ML detection of suspicious messages
- Real-time message content analysis
- Anomaly detection using DistilBERT/LLM models
- Threat assessment and alerting

### 6. dashboard/
**Purpose**: Endpoints for React/Next.js dashboard views
- Command dashboard API endpoints
- Real-time status monitoring
- Analytics and reporting

## Configuration Features

- **REST Framework**: Token and session authentication
- **WebSocket Support**: Real-time communication via Channels
- **CORS**: Configured for React/Next.js frontend
- **Celery**: Async task processing for blockchain and AI operations  
- **Security**: Military-grade security settings
- **Logging**: Comprehensive logging for audit and debugging

## Next Steps

1. Define models for each app
2. Create API endpoints and GraphQL schema
3. Implement WebSocket consumers for real-time communication
4. Set up Celery workers for background tasks