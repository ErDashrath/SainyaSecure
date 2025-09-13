"""
P2P Communication System - Battlefield Messaging with Offline Mode

This module simulates peer-to-peer communication in battlefield conditions:
- Server failure handling with automatic P2P fallback
- Offline-first message storage with local ledgers
- Radio/Wi-Fi simulation for different connectivity modes
- Automatic node discovery and mesh networking
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
from utils.military_crypto import military_crypto, military_blockchain


class ConnectivityMode(Enum):
    ONLINE = "online"           # Full server connection
    P2P_WIFI = "p2p_wifi"      # Wi-Fi mesh mode
    P2P_RADIO = "p2p_radio"    # Radio simulation mode  
    OFFLINE = "offline"         # Completely isolated


class MessageType(Enum):
    CHAT = "chat"
    ALERT = "alert"
    COMMAND = "command"
    STATUS = "status"
    SYNC_REQUEST = "sync_request"
    SYNC_RESPONSE = "sync_response"


@dataclass
class P2PMessage:
    """P2P message structure for battlefield communication"""
    message_id: str
    sender_id: str
    receiver_id: Optional[str]  # None for broadcast
    message_type: MessageType
    content: str
    timestamp: float
    lamport_clock: int
    vector_clock: Dict[str, int]
    encrypted_payload: str
    digital_signature: str
    hop_count: int = 0
    max_hops: int = 5
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['message_type'] = self.message_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: dict):
        data['message_type'] = MessageType(data['message_type'])
        return cls(**data)


@dataclass
class PeerNode:
    """Represents a battlefield node (soldier device)"""
    node_id: str
    node_name: str
    rank: str
    location: tuple  # (lat, lon)
    connectivity_mode: ConnectivityMode
    is_online: bool
    last_seen: float
    public_key: str
    private_key: str
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['connectivity_mode'] = self.connectivity_mode.value
        return data


class LocalLedger:
    """Lightweight blockchain ledger for each peer node"""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.blocks: List[dict] = []
        self.pending_messages: List[P2PMessage] = []
        self.last_block_hash = "0" * 64
        
    def add_message(self, message: P2PMessage) -> dict:
        """Add message to local ledger with blockchain validation"""
        block = {
            'block_number': len(self.blocks),
            'timestamp': time.time(),
            'previous_hash': self.last_block_hash,
            'message_data': message.to_dict(),
            'node_id': self.node_id,
            'nonce': 0
        }
        
        # Mine block with simple proof of work
        block_hash, nonce = military_blockchain.mine_block(block, difficulty=2)
        block['block_hash'] = block_hash
        block['nonce'] = nonce
        
        self.blocks.append(block)
        self.last_block_hash = block_hash
        
        print(f"📦 Block #{block['block_number']} added to ledger: {block_hash[:16]}...")
        return block
    
    def get_messages_since(self, timestamp: float) -> List[dict]:
        """Get all messages since given timestamp"""
        return [
            block for block in self.blocks 
            if block['timestamp'] >= timestamp
        ]
    
    def validate_chain(self) -> bool:
        """Validate entire blockchain integrity"""
        return military_blockchain.validate_block_chain(self.blocks)


class P2PNetworkSimulator:
    """Simulates P2P battlefield communication network"""
    
    def __init__(self):
        self.nodes: Dict[str, PeerNode] = {}
        self.ledgers: Dict[str, LocalLedger] = {}
        self.message_queues: Dict[str, List[P2PMessage]] = {}
        self.network_topology: Dict[str, Set[str]] = {}  # node_id -> connected_nodes
        self.server_online = True
        self.lamport_clock = 0
        
    def add_node(self, node: PeerNode) -> None:
        """Add a new peer node to the network"""
        self.nodes[node.node_id] = node
        self.ledgers[node.node_id] = LocalLedger(node.node_id)
        self.message_queues[node.node_id] = []
        self.network_topology[node.node_id] = set()
        
        print(f"🔗 Node {node.node_name} ({node.rank}) joined network")
    
    def simulate_server_failure(self):
        """Simulate central server going down"""
        self.server_online = False
        print("🚨 SERVER DOWN - Switching to P2P mode")
        
        # Switch all nodes to P2P mode
        for node in self.nodes.values():
            if node.connectivity_mode == ConnectivityMode.ONLINE:
                node.connectivity_mode = ConnectivityMode.P2P_WIFI
    
    def simulate_server_recovery(self):
        """Simulate central server coming back online"""
        self.server_online = True
        print("✅ SERVER RECOVERED - Initiating sync")
        
        # Switch nodes back to online mode
        for node in self.nodes.values():
            if node.connectivity_mode in [ConnectivityMode.P2P_WIFI, ConnectivityMode.P2P_RADIO]:
                node.connectivity_mode = ConnectivityMode.ONLINE
        
        # Trigger sync process
        self.sync_all_nodes()
    
    def simulate_node_dropout(self, node_id: str):
        """Simulate node going offline (battlefield conditions)"""
        if node_id in self.nodes:
            self.nodes[node_id].connectivity_mode = ConnectivityMode.OFFLINE
            self.nodes[node_id].is_online = False
            print(f"📵 Node {self.nodes[node_id].node_name} went OFFLINE")
    
    def simulate_node_reconnect(self, node_id: str):
        """Simulate node coming back online"""
        if node_id in self.nodes:
            self.nodes[node_id].connectivity_mode = ConnectivityMode.P2P_WIFI
            self.nodes[node_id].is_online = True
            print(f"🔄 Node {self.nodes[node_id].node_name} RECONNECTED")
            
            # Trigger sync for this node
            self.sync_node(node_id)
    
    def establish_p2p_connections(self):
        """Establish P2P connections based on proximity (simplified)"""
        node_list = list(self.nodes.values())
        
        for i, node1 in enumerate(node_list):
            for node2 in node_list[i+1:]:
                if self.can_communicate_p2p(node1, node2):
                    self.network_topology[node1.node_id].add(node2.node_id)
                    self.network_topology[node2.node_id].add(node1.node_id)
    
    def can_communicate_p2p(self, node1: PeerNode, node2: PeerNode) -> bool:
        """Check if two nodes can communicate directly (distance-based)"""
        # Simple distance calculation (in real scenario, consider radio range, obstacles)
        lat1, lon1 = node1.location
        lat2, lon2 = node2.location
        distance = ((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2) ** 0.5
        
        # Different ranges for different connectivity modes
        max_range = {
            ConnectivityMode.P2P_WIFI: 0.1,   # Close range
            ConnectivityMode.P2P_RADIO: 0.5,  # Medium range
            ConnectivityMode.ONLINE: float('inf')  # Server-mediated
        }
        
        mode = node1.connectivity_mode
        return distance <= max_range.get(mode, 0.1) and node1.is_online and node2.is_online
    
    def send_message(self, sender_id: str, receiver_id: Optional[str], 
                    message_type: MessageType, content: str) -> bool:
        """Send message through P2P network with routing"""
        
        if sender_id not in self.nodes:
            return False
        
        sender = self.nodes[sender_id]
        
        # Increment Lamport clock
        self.lamport_clock += 1
        
        # Create vector clock (simplified - in real implementation, each node maintains its own)
        vector_clock = {node_id: 0 for node_id in self.nodes.keys()}
        vector_clock[sender_id] = self.lamport_clock
        
        # Encrypt message (simplified)
        encrypted_payload = military_crypto.aes_encrypt(
            content, military_crypto.generate_aes_key()
        )
        
        # Create digital signature
        signature = military_crypto.sign_message(content, sender.private_key)
        
        message = P2PMessage(
            message_id=str(uuid.uuid4()),
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=message_type,
            content=content,
            timestamp=time.time(),
            lamport_clock=self.lamport_clock,
            vector_clock=vector_clock,
            encrypted_payload=json.dumps(encrypted_payload),
            digital_signature=signature
        )
        
        # Add to sender's local ledger
        self.ledgers[sender_id].add_message(message)
        
        # Route message based on connectivity mode
        return self.route_message(message)
    
    def route_message(self, message: P2PMessage) -> bool:
        """Route message through P2P network"""
        sender = self.nodes[message.sender_id]
        
        if sender.connectivity_mode == ConnectivityMode.OFFLINE:
            print(f"📱 Message stored offline on {sender.node_name}")
            return False
        
        if sender.connectivity_mode == ConnectivityMode.ONLINE and self.server_online:
            # Direct server routing
            return self.deliver_via_server(message)
        
        # P2P routing
        return self.deliver_via_p2p(message)
    
    def deliver_via_server(self, message: P2PMessage) -> bool:
        """Deliver message via central server"""
        if message.receiver_id:
            # Direct message
            if message.receiver_id in self.message_queues:
                self.message_queues[message.receiver_id].append(message)
                print(f"📬 Server delivered message to {self.nodes[message.receiver_id].node_name}")
                return True
        else:
            # Broadcast message
            for node_id in self.nodes:
                if node_id != message.sender_id:
                    self.message_queues[node_id].append(message)
            print(f"📢 Server broadcast message from {self.nodes[message.sender_id].node_name}")
            return True
        return False
    
    def deliver_via_p2p(self, message: P2PMessage) -> bool:
        """Deliver message via P2P routing"""
        if message.hop_count >= message.max_hops:
            print(f"🚫 Message exceeded max hops: {message.message_id[:8]}")
            return False
        
        sender_id = message.sender_id
        delivered = False
        
        # Get connected peers
        connected_peers = self.network_topology.get(sender_id, set())
        
        for peer_id in connected_peers:
            peer = self.nodes[peer_id]
            
            if not peer.is_online:
                continue
            
            # If this is the target recipient
            if message.receiver_id == peer_id:
                self.message_queues[peer_id].append(message)
                print(f"📡 P2P delivered to {peer.node_name}")
                delivered = True
            elif message.receiver_id is None:  # Broadcast
                self.message_queues[peer_id].append(message)
                delivered = True
            else:
                # Forward message (flood routing - simplified)
                message.hop_count += 1
                # In real implementation, use smarter routing algorithms
                continue
        
        if message.receiver_id is None and delivered:
            print(f"📻 P2P broadcast from {self.nodes[sender_id].node_name}")
        
        return delivered
    
    def sync_node(self, node_id: str):
        """Sync a specific node's ledger with the network"""
        if node_id not in self.ledgers:
            return
        
        node_ledger = self.ledgers[node_id]
        print(f"🔄 Syncing node {self.nodes[node_id].node_name}...")
        
        # In real implementation, this would involve complex conflict resolution
        # For demo, we'll simulate basic sync
        sync_conflicts = []
        
        # Check for conflicts with other nodes' ledgers
        for other_node_id, other_ledger in self.ledgers.items():
            if other_node_id == node_id:
                continue
            
            # Compare recent blocks for conflicts
            recent_blocks = other_ledger.get_messages_since(time.time() - 300)  # Last 5 minutes
            
            for block in recent_blocks:
                # Simplified conflict detection
                if block['message_data']['lamport_clock'] > node_ledger.blocks[-1]['message_data']['lamport_clock'] if node_ledger.blocks else 0:
                    sync_conflicts.append({
                        'conflict_type': 'lamport_ordering',
                        'block': block,
                        'source_node': other_node_id
                    })
        
        if sync_conflicts:
            print(f"⚠️  Resolved {len(sync_conflicts)} sync conflicts for {self.nodes[node_id].node_name}")
        else:
            print(f"✅ No conflicts found for {self.nodes[node_id].node_name}")
    
    def sync_all_nodes(self):
        """Sync all nodes when server comes back online"""
        print("🔄 Starting network-wide synchronization...")
        
        for node_id in self.nodes:
            self.sync_node(node_id)
        
        print("✅ Network synchronization complete")
    
    def get_network_status(self) -> dict:
        """Get current network status for dashboard"""
        online_nodes = sum(1 for node in self.nodes.values() if node.is_online)
        total_messages = sum(len(ledger.blocks) for ledger in self.ledgers.values())
        
        return {
            'server_online': self.server_online,
            'total_nodes': len(self.nodes),
            'online_nodes': online_nodes,
            'offline_nodes': len(self.nodes) - online_nodes,
            'total_messages': total_messages,
            'connectivity_modes': {
                mode.value: sum(1 for node in self.nodes.values() 
                               if node.connectivity_mode == mode)
                for mode in ConnectivityMode
            }
        }
    
    def get_node_messages(self, node_id: str) -> List[dict]:
        """Get all messages for a specific node"""
        if node_id not in self.message_queues:
            return []
        
        messages = []
        for msg in self.message_queues[node_id]:
            messages.append({
                'id': msg.message_id,
                'sender': self.nodes[msg.sender_id].node_name,
                'content': msg.content,
                'timestamp': datetime.fromtimestamp(msg.timestamp).strftime('%H:%M:%S'),
                'type': msg.message_type.value,
                'lamport_clock': msg.lamport_clock
            })
        
        return messages


# Global P2P network instance
p2p_network = P2PNetworkSimulator()


def initialize_demo_network():
    """Initialize demo network with sample nodes"""
    
    # Generate crypto keys for demo nodes
    keys1 = military_crypto.generate_rsa_keys()
    keys2 = military_crypto.generate_rsa_keys()
    keys3 = military_crypto.generate_rsa_keys()
    keys4 = military_crypto.generate_rsa_keys()
    
    # Create demo battlefield nodes
    nodes = [
        PeerNode(
            node_id="alpha_1",
            node_name="Alpha Team Lead",
            rank="Sergeant",
            location=(32.7767, -96.7970),  # Dallas coordinates as example
            connectivity_mode=ConnectivityMode.ONLINE,
            is_online=True,
            last_seen=time.time(),
            public_key=keys1.public_key,
            private_key=keys1.private_key
        ),
        PeerNode(
            node_id="bravo_1",
            node_name="Bravo Scout",
            rank="Corporal", 
            location=(32.7800, -96.8000),
            connectivity_mode=ConnectivityMode.ONLINE,
            is_online=True,
            last_seen=time.time(),
            public_key=keys2.public_key,
            private_key=keys2.private_key
        ),
        PeerNode(
            node_id="charlie_1",
            node_name="Charlie Support",
            rank="Private",
            location=(32.7750, -96.7950),
            connectivity_mode=ConnectivityMode.ONLINE,
            is_online=True,
            last_seen=time.time(),
            public_key=keys3.public_key,
            private_key=keys3.private_key
        ),
        PeerNode(
            node_id="delta_1", 
            node_name="Delta Command",
            rank="Lieutenant",
            location=(32.7820, -96.7980),
            connectivity_mode=ConnectivityMode.ONLINE,
            is_online=True,
            last_seen=time.time(),
            public_key=keys4.public_key,
            private_key=keys4.private_key
        )
    ]
    
    # Add nodes to network
    for node in nodes:
        p2p_network.add_node(node)
    
    # Establish P2P connections
    p2p_network.establish_p2p_connections()
    
    print("🎖️ Demo battlefield network initialized with 4 nodes")
    print("✅ P2P connections established")
    
    return p2p_network


if __name__ == "__main__":
    # Demo script
    network = initialize_demo_network()
    
    # Send some demo messages
    network.send_message("alpha_1", "bravo_1", MessageType.COMMAND, "Move to position Bravo")
    network.send_message("bravo_1", None, MessageType.STATUS, "Position reached, all clear")
    
    # Simulate server failure
    network.simulate_server_failure()
    
    # Send messages in P2P mode
    network.send_message("charlie_1", "alpha_1", MessageType.ALERT, "Enemy contact at grid 123456")
    
    # Simulate node dropout
    network.simulate_node_dropout("bravo_1")
    
    # Send message to offline node (should be stored locally)
    network.send_message("alpha_1", "bravo_1", MessageType.COMMAND, "Status report requested")
    
    # Reconnect node
    network.simulate_node_reconnect("bravo_1")
    
    # Recover server
    network.simulate_server_recovery()
    
    print("\n📊 Final Network Status:")
    print(json.dumps(network.get_network_status(), indent=2))