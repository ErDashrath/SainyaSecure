"""
Advanced Battlefield Communication Demo Server
Simulates real military communication scenarios with P2P fallback,
server failures, node dropouts, and message synchronization
"""

import asyncio
import json
import logging
import random
import time
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Set
from collections import defaultdict
import websockets
import websockets.server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NetworkState(Enum):
    CENTRALIZED = "centralized"
    P2P_FALLBACK = "p2p_fallback"
    DEGRADED = "degraded"
    ISOLATED = "isolated"

class MessageType(Enum):
    CHAT = "chat"
    COMMAND = "command"
    ALERT = "alert"
    STATUS = "status"
    SYSTEM = "system"

class NodeStatus(Enum):
    ONLINE = "online"
    P2P_ONLY = "p2p_only"
    OFFLINE = "offline"
    RECONNECTING = "reconnecting"

@dataclass
class BattlefieldNode:
    id: str
    name: str
    rank: str
    unit: str
    position: Dict[str, float]  # x, y coordinates
    status: NodeStatus
    last_seen: datetime
    websocket: Optional = None
    p2p_connections: Set[str] = None
    message_queue: List = None
    lamport_clock: int = 0
    
    def __post_init__(self):
        if self.p2p_connections is None:
            self.p2p_connections = set()
        if self.message_queue is None:
            self.message_queue = []

@dataclass
class BattlefieldMessage:
    id: str
    sender_id: str
    content: str
    message_type: MessageType
    timestamp: datetime
    lamport_clock: int
    recipients: List[str] = None
    encrypted: bool = True
    signature: str = ""
    route_path: List[str] = None
    delivery_attempts: int = 0
    
    def __post_init__(self):
        if self.recipients is None:
            self.recipients = []
        if self.route_path is None:
            self.route_path = []

@dataclass
class NetworkEvent:
    event_type: str
    description: str
    timestamp: datetime
    affected_nodes: List[str]
    severity: str  # info, warning, critical

class BattlefieldCommunicationServer:
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        
        # Network state
        self.server_online = True
        self.network_state = NetworkState.CENTRALIZED
        self.nodes: Dict[str, BattlefieldNode] = {}
        self.messages: List[BattlefieldMessage] = []
        self.events: List[NetworkEvent] = []
        
        # WebSocket connections
        self.client_connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        
        # Simulation parameters
        self.failure_scenarios = {
            'server_failure': {'probability': 0.02, 'duration_range': (30, 120)},
            'node_dropout': {'probability': 0.01, 'duration_range': (10, 60)},
            'network_partition': {'probability': 0.005, 'duration_range': (45, 90)},
            'message_delay': {'probability': 0.03, 'delay_range': (1, 10)}
        }
        
        # Initialize demo nodes
        self.initialize_demo_nodes()
        
    def initialize_demo_nodes(self):
        """Initialize battlefield nodes for demonstration"""
        demo_nodes_data = [
            {
                'id': 'alpha_1',
                'name': 'Alpha Team Lead',
                'rank': 'Sergeant',
                'unit': 'Alpha Company',
                'position': {'x': 100, 'y': 150}
            },
            {
                'id': 'bravo_1', 
                'name': 'Bravo Scout',
                'rank': 'Corporal',
                'unit': 'Bravo Company',
                'position': {'x': 300, 'y': 200}
            },
            {
                'id': 'charlie_1',
                'name': 'Charlie Support', 
                'rank': 'Private',
                'unit': 'Charlie Company',
                'position': {'x': 200, 'y': 350}
            },
            {
                'id': 'delta_1',
                'name': 'Delta Command',
                'rank': 'Lieutenant', 
                'unit': 'Delta Command',
                'position': {'x': 450, 'y': 180}
            },
            {
                'id': 'echo_1',
                'name': 'Echo Medic',
                'rank': 'Corporal',
                'unit': 'Echo Support',
                'position': {'x': 350, 'y': 100}
            }
        ]
        
        for node_data in demo_nodes_data:
            node = BattlefieldNode(
                id=node_data['id'],
                name=node_data['name'],
                rank=node_data['rank'],
                unit=node_data['unit'],
                position=node_data['position'],
                status=NodeStatus.ONLINE,
                last_seen=datetime.now()
            )
            self.nodes[node.id] = node
            
        logger.info(f"Initialized {len(self.nodes)} battlefield nodes")
    
    def get_network_topology(self):
        """Get current network topology and connections"""
        topology = {
            'server_online': self.server_online,
            'network_state': self.network_state.value,
            'nodes': {},
            'connections': []
        }
        
        for node_id, node in self.nodes.items():
            topology['nodes'][node_id] = {
                'id': node.id,
                'name': node.name,
                'rank': node.rank,
                'unit': node.unit,
                'status': node.status.value,
                'position': node.position,
                'last_seen': node.last_seen.isoformat(),
                'message_queue_size': len(node.message_queue),
                'lamport_clock': node.lamport_clock
            }
            
        # Determine connections based on current network state
        if self.server_online and self.network_state == NetworkState.CENTRALIZED:
            # All online nodes connected to central server
            online_nodes = [n for n in self.nodes.keys() 
                          if self.nodes[n].status == NodeStatus.ONLINE]
            
            for node_id in online_nodes:
                topology['connections'].append({
                    'from': 'central_server',
                    'to': node_id,
                    'type': 'centralized',
                    'strength': 100
                })
                
        else:
            # P2P connections based on proximity and radio range
            for node1_id, node1 in self.nodes.items():
                if node1.status == NodeStatus.OFFLINE:
                    continue
                    
                for node2_id, node2 in self.nodes.items():
                    if (node2.status == NodeStatus.OFFLINE or 
                        node1_id >= node2_id):  # Avoid duplicates
                        continue
                        
                    distance = self.calculate_distance(node1.position, node2.position)
                    max_p2p_range = 200  # Maximum P2P communication range
                    
                    if distance <= max_p2p_range:
                        connection_strength = max(20, 100 - (distance / max_p2p_range) * 80)
                        topology['connections'].append({
                            'from': node1_id,
                            'to': node2_id,
                            'type': 'p2p',
                            'distance': distance,
                            'strength': connection_strength
                        })
        
        return topology
    
    def calculate_distance(self, pos1: Dict, pos2: Dict) -> float:
        """Calculate Euclidean distance between two positions"""
        return ((pos1['x'] - pos2['x'])**2 + (pos1['y'] - pos2['y'])**2)**0.5
    
    async def handle_client_connection(self, websocket, path):
        """Handle incoming WebSocket client connections"""
        client_id = str(uuid.uuid4())
        self.client_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected from {websocket.remote_address}")
        
        try:
            # Send initial network state
            await self.send_to_client(websocket, {
                'type': 'network_topology',
                'data': self.get_network_topology()
            })
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_client_message(client_id, data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from client {client_id}")
                except Exception as e:
                    logger.error(f"Error handling message from {client_id}: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        finally:
            if client_id in self.client_connections:
                del self.client_connections[client_id]
    
    async def handle_client_message(self, client_id: str, data: Dict):
        """Process incoming client messages"""
        message_type = data.get('type')
        
        if message_type == 'send_message':
            await self.handle_send_message(data)
        elif message_type == 'simulate_scenario':
            await self.handle_simulation_command(data)
        elif message_type == 'get_network_status':
            topology = self.get_network_topology()
            await self.broadcast_to_clients({
                'type': 'network_topology',
                'data': topology
            })
        elif message_type == 'force_sync':
            await self.handle_force_sync()
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    async def handle_send_message(self, data: Dict):
        """Handle message sending with routing logic"""
        sender_id = data.get('sender_id')
        content = data.get('content', '')
        message_type = MessageType(data.get('message_type', 'chat'))
        recipients = data.get('recipients', [])
        
        if not sender_id or sender_id not in self.nodes:
            return
            
        # Create message
        message = BattlefieldMessage(
            id=str(uuid.uuid4()),
            sender_id=sender_id,
            content=content,
            message_type=message_type,
            timestamp=datetime.now(),
            lamport_clock=self.nodes[sender_id].lamport_clock + 1,
            recipients=recipients,
            encrypted=True,
            signature=f"sig_{random.randint(1000, 9999)}"
        )
        
        # Update sender's Lamport clock
        self.nodes[sender_id].lamport_clock = message.lamport_clock
        
        # Route message based on network state
        if self.server_online and self.network_state == NetworkState.CENTRALIZED:
            # Central server routing
            await self.route_message_centralized(message)
        else:
            # P2P routing
            await self.route_message_p2p(message, sender_id)
            
        self.messages.append(message)
        
        # Broadcast message to all clients
        await self.broadcast_to_clients({
            'type': 'new_message',
            'data': {
                'id': message.id,
                'sender_id': message.sender_id,
                'sender_name': self.nodes[sender_id].name,
                'content': message.content,
                'message_type': message.message_type.value,
                'timestamp': message.timestamp.isoformat(),
                'lamport_clock': message.lamport_clock,
                'route_path': message.route_path
            }
        })
    
    async def route_message_centralized(self, message: BattlefieldMessage):
        """Route message through central server"""
        message.route_path = ['central_server']
        
        # Simulate potential server processing delay
        if random.random() < 0.1:  # 10% chance of delay
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
        logger.info(f"Routed message {message.id} via central server")
    
    async def route_message_p2p(self, message: BattlefieldMessage, sender_id: str):
        """Route message through P2P network"""
        if not message.recipients:
            # Broadcast to all reachable nodes
            message.recipients = list(self.nodes.keys())
        
        # Find optimal P2P routes using simple flooding with TTL
        visited = set([sender_id])
        current_hops = [sender_id]
        max_hops = 3
        
        for hop in range(max_hops):
            next_hops = []
            for current_node in current_hops:
                if current_node not in self.nodes:
                    continue
                    
                node = self.nodes[current_node]
                if node.status == NodeStatus.OFFLINE:
                    continue
                
                # Find nodes within P2P range
                for target_id, target_node in self.nodes.items():
                    if (target_id in visited or 
                        target_node.status == NodeStatus.OFFLINE):
                        continue
                        
                    distance = self.calculate_distance(node.position, target_node.position)
                    if distance <= 200:  # P2P range
                        next_hops.append(target_id)
                        visited.add(target_id)
                        message.route_path.append(target_id)
            
            current_hops = next_hops
            if not current_hops:
                break
        
        # Simulate P2P routing delay
        routing_delay = len(message.route_path) * 0.1
        if routing_delay > 0:
            await asyncio.sleep(routing_delay)
            
        logger.info(f"Routed message {message.id} via P2P: {' -> '.join(message.route_path)}")
    
    async def handle_simulation_command(self, data: Dict):
        """Handle simulation commands from clients"""
        scenario = data.get('scenario')
        
        if scenario == 'server_failure':
            await self.simulate_server_failure()
        elif scenario == 'server_recovery':
            await self.simulate_server_recovery()
        elif scenario == 'node_dropout':
            await self.simulate_node_dropout()
        elif scenario == 'network_partition':
            await self.simulate_network_partition()
        elif scenario == 'full_demo':
            await self.simulate_full_battlefield_demo()
        else:
            logger.warning(f"Unknown simulation scenario: {scenario}")
    
    async def simulate_server_failure(self):
        """Simulate central server failure"""
        if not self.server_online:
            return
            
        self.server_online = False
        self.network_state = NetworkState.P2P_FALLBACK
        
        # Switch all online nodes to P2P mode
        for node in self.nodes.values():
            if node.status == NodeStatus.ONLINE:
                node.status = NodeStatus.P2P_ONLY
        
        # Create event
        event = NetworkEvent(
            event_type='server_failure',
            description='Central communication server has failed. Switching to P2P mode.',
            timestamp=datetime.now(),
            affected_nodes=list(self.nodes.keys()),
            severity='critical'
        )
        self.events.append(event)
        
        # Broadcast event to clients
        await self.broadcast_to_clients({
            'type': 'system_event',
            'data': {
                'event_type': event.event_type,
                'description': event.description,
                'timestamp': event.timestamp.isoformat(),
                'severity': event.severity
            }
        })
        
        # Update network topology
        await self.broadcast_to_clients({
            'type': 'network_topology',
            'data': self.get_network_topology()
        })
        
        logger.info("Simulated server failure - switched to P2P mode")
    
    async def simulate_server_recovery(self):
        """Simulate server recovery and network resynchronization"""
        if self.server_online:
            return
            
        self.server_online = True
        self.network_state = NetworkState.CENTRALIZED
        
        # Switch nodes back to centralized mode
        for node in self.nodes.values():
            if node.status == NodeStatus.P2P_ONLY:
                node.status = NodeStatus.ONLINE
        
        # Simulate synchronization process
        await asyncio.sleep(2)  # Sync delay
        
        # Resolve any message conflicts using Lamport clocks
        await self.synchronize_network()
        
        event = NetworkEvent(
            event_type='server_recovery',
            description='Central server recovered. Network synchronized successfully.',
            timestamp=datetime.now(),
            affected_nodes=list(self.nodes.keys()),
            severity='info'
        )
        self.events.append(event)
        
        await self.broadcast_to_clients({
            'type': 'system_event',
            'data': {
                'event_type': event.event_type,
                'description': event.description,
                'timestamp': event.timestamp.isoformat(),
                'severity': event.severity
            }
        })
        
        await self.broadcast_to_clients({
            'type': 'network_topology',
            'data': self.get_network_topology()
        })
        
        logger.info("Simulated server recovery - network synchronized")
    
    async def simulate_node_dropout(self):
        """Simulate random node going offline"""
        online_nodes = [n for n in self.nodes.values() 
                       if n.status in [NodeStatus.ONLINE, NodeStatus.P2P_ONLY]]
        
        if not online_nodes:
            return
            
        dropout_node = random.choice(online_nodes)
        dropout_node.status = NodeStatus.OFFLINE
        
        event = NetworkEvent(
            event_type='node_dropout',
            description=f'{dropout_node.name} ({dropout_node.rank}) has gone offline',
            timestamp=datetime.now(),
            affected_nodes=[dropout_node.id],
            severity='warning'
        )
        self.events.append(event)
        
        await self.broadcast_to_clients({
            'type': 'system_event',
            'data': {
                'event_type': event.event_type,
                'description': event.description,
                'timestamp': event.timestamp.isoformat(),
                'severity': event.severity
            }
        })
        
        await self.broadcast_to_clients({
            'type': 'network_topology',
            'data': self.get_network_topology()
        })
        
        # Schedule node recovery
        asyncio.create_task(self.schedule_node_recovery(dropout_node.id))
        
        logger.info(f"Node {dropout_node.name} dropped out")
    
    async def schedule_node_recovery(self, node_id: str):
        """Schedule node to come back online"""
        recovery_delay = random.uniform(10, 30)  # 10-30 seconds
        await asyncio.sleep(recovery_delay)
        
        if node_id in self.nodes:
            node = self.nodes[node_id]
            node.status = NodeStatus.ONLINE if self.server_online else NodeStatus.P2P_ONLY
            node.last_seen = datetime.now()
            
            event = NetworkEvent(
                event_type='node_recovery',
                description=f'{node.name} has reconnected to the network',
                timestamp=datetime.now(),
                affected_nodes=[node.id],
                severity='info'
            )
            self.events.append(event)
            
            await self.broadcast_to_clients({
                'type': 'system_event',
                'data': {
                    'event_type': event.event_type,
                    'description': event.description,
                    'timestamp': event.timestamp.isoformat(),
                    'severity': event.severity
                }
            })
            
            await self.broadcast_to_clients({
                'type': 'network_topology',
                'data': self.get_network_topology()
            })
            
            logger.info(f"Node {node.name} recovered")
    
    async def simulate_network_partition(self):
        """Simulate network partition splitting nodes"""
        nodes_list = list(self.nodes.values())
        if len(nodes_list) < 2:
            return
            
        # Split nodes into two partitions
        partition_size = len(nodes_list) // 2
        partition_a = nodes_list[:partition_size]
        partition_b = nodes_list[partition_size:]
        
        # Simulate partition by modifying P2P connections
        # This is a simplified demonstration
        
        event = NetworkEvent(
            event_type='network_partition',
            description=f'Network partitioned: {len(partition_a)} vs {len(partition_b)} nodes',
            timestamp=datetime.now(),
            affected_nodes=[n.id for n in nodes_list],
            severity='critical'
        )
        self.events.append(event)
        
        await self.broadcast_to_clients({
            'type': 'system_event',
            'data': {
                'event_type': event.event_type,
                'description': event.description,
                'timestamp': event.timestamp.isoformat(),
                'severity': event.severity
            }
        })
        
        logger.info(f"Simulated network partition")
    
    async def simulate_full_battlefield_demo(self):
        """Run comprehensive battlefield scenario"""
        await self.broadcast_to_clients({
            'type': 'system_event',
            'data': {
                'event_type': 'demo_start',
                'description': 'Starting full battlefield communication demo...',
                'timestamp': datetime.now().isoformat(),
                'severity': 'info'
            }
        })
        
        # Phase 1: Normal operations
        await asyncio.sleep(3)
        
        # Phase 2: Server failure
        await self.simulate_server_failure()
        await asyncio.sleep(5)
        
        # Phase 3: Node dropout during P2P mode
        await self.simulate_node_dropout()
        await asyncio.sleep(8)
        
        # Phase 4: Server recovery and sync
        await self.simulate_server_recovery()
        await asyncio.sleep(3)
        
        await self.broadcast_to_clients({
            'type': 'system_event',
            'data': {
                'event_type': 'demo_complete',
                'description': 'Battlefield communication demo completed successfully',
                'timestamp': datetime.now().isoformat(),
                'severity': 'info'
            }
        })
        
        logger.info("Full battlefield demo completed")
    
    async def synchronize_network(self):
        """Synchronize network state and resolve conflicts"""
        # Simulate Lamport clock synchronization
        max_clock = max(node.lamport_clock for node in self.nodes.values())
        
        for node in self.nodes.values():
            node.lamport_clock = max_clock + 1
            
        # Process queued messages
        total_synced = 0
        for node in self.nodes.values():
            total_synced += len(node.message_queue)
            node.message_queue.clear()  # Simulate processing
            
        logger.info(f"Synchronized {total_synced} queued messages")
    
    async def handle_force_sync(self):
        """Handle manual synchronization request"""
        await self.synchronize_network()
        
        event = NetworkEvent(
            event_type='manual_sync',
            description='Manual network synchronization completed',
            timestamp=datetime.now(),
            affected_nodes=list(self.nodes.keys()),
            severity='info'
        )
        self.events.append(event)
        
        await self.broadcast_to_clients({
            'type': 'system_event',
            'data': {
                'event_type': event.event_type,
                'description': event.description,
                'timestamp': event.timestamp.isoformat(),
                'severity': event.severity
            }
        })
    
    async def send_to_client(self, websocket, data: Dict):
        """Send data to specific client"""
        try:
            await websocket.send(json.dumps(data))
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"Error sending to client: {e}")
    
    async def broadcast_to_clients(self, data: Dict):
        """Broadcast data to all connected clients"""
        if not self.client_connections:
            return
            
        disconnected = []
        for client_id, websocket in self.client_connections.items():
            try:
                await websocket.send(json.dumps(data))
            except websockets.exceptions.ConnectionClosed:
                disconnected.append(client_id)
            except Exception as e:
                logger.error(f"Error broadcasting to client {client_id}: {e}")
                disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            del self.client_connections[client_id]
    
    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting battlefield communication server on {self.host}:{self.port}")
        
        async with websockets.serve(self.handle_client_connection, self.host, self.port):
            logger.info("Battlefield communication server is running")
            await asyncio.Future()  # Run forever

def main():
    """Run the battlefield communication server"""
    server = BattlefieldCommunicationServer()
    
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    main()