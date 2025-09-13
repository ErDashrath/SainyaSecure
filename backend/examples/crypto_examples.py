"""
Military Crypto Usage Examples

Shows how the new libraries simplify blockchain and cryptography operations
compared to manual implementations.
"""

from utils.military_crypto import military_crypto, military_blockchain
from django.conf import settings

# Example 1: Before vs After - Message Encryption
def encrypt_battlefield_message_example():
    """Example of simplified message encryption"""
    
    # Generate RSA key pair (one line!)
    keys = military_crypto.generate_rsa_keys()
    
    # Original message from soldier
    message = "Target acquired at coordinates 32.7767° N, 96.7970° W. Request immediate air support."
    
    # Encrypt message (one line!)
    encrypted = military_crypto.rsa_encrypt(message, keys.public_key)
    print(f"✅ Message encrypted: {encrypted[:50]}...")
    
    # Sign message (one line!)
    signature = military_crypto.sign_message(message, keys.private_key)
    print(f"✅ Message signed: {signature[:50]}...")
    
    # Decrypt at command center (one line!)
    decrypted = military_crypto.rsa_decrypt(encrypted, keys.private_key)
    print(f"✅ Message decrypted: {decrypted}")
    
    # Verify signature (one line!)
    is_valid = military_crypto.verify_signature(message, signature, keys.public_key)
    print(f"✅ Signature valid: {is_valid}")


# Example 2: Before vs After - Blockchain Operations  
def create_blockchain_block_example():
    """Example of simplified blockchain operations"""
    
    # Sample transaction data
    transactions = [
        {"from": "Soldier_A", "to": "Command", "message": "Enemy movement detected"},
        {"from": "Drone_B", "to": "Command", "message": "Reconnaissance complete"},
        {"from": "Command", "to": "All_Units", "message": "Mission parameters updated"}
    ]
    
    # Create Merkle tree from transactions (one line!)
    merkle_root = military_blockchain.create_merkle_tree(transactions)
    print(f"✅ Merkle root: {merkle_root}")
    
    # Block data
    block_data = {
        'block_number': 1,
        'previous_hash': '0000000000000000000000000000000000000000000000000000000000000000',
        'merkle_root': merkle_root,
        'timestamp': '2025-09-13T14:30:00Z',
        'transactions': transactions
    }
    
    # Mine block with proof of work (one line!)
    difficulty = settings.MILITARY_COMM_SETTINGS.get('MINING_DIFFICULTY', 4)
    block_hash, nonce = military_blockchain.mine_block(block_data, difficulty)
    
    print(f"✅ Block mined:")
    print(f"   Hash: {block_hash}")
    print(f"   Nonce: {nonce}")
    print(f"   Difficulty: {difficulty}")
    
    # Validate block (one line!)
    block_data['block_hash'] = block_hash
    block_data['nonce'] = nonce
    is_valid = military_blockchain.validate_block_hash(block_data)
    print(f"✅ Block valid: {is_valid}")


# Example 3: AES Encryption for Large Payloads
def aes_encryption_example():
    """Example of AES encryption for large military data"""
    
    # Generate AES key (one line!)
    aes_key = military_crypto.generate_aes_key()
    
    # Large military data payload
    large_payload = {
        "mission_id": "ALPHA-2025-001",
        "classification": "SECRET",
        "personnel": ["Bravo-6", "Charlie-3", "Delta-1"],
        "coordinates": [
            {"lat": 32.7767, "lon": -96.7970, "alt": 500},
            {"lat": 32.7800, "lon": -96.8000, "alt": 520}
        ],
        "equipment": ["M4A1", "M249", "AT4", "MK19"],
        "timeline": "2025-09-13T15:00:00Z to 2025-09-13T18:00:00Z"
    }
    
    # Convert to JSON and encrypt (one line!)
    import json
    payload_json = json.dumps(large_payload)
    encrypted_data = military_crypto.aes_encrypt(payload_json, aes_key)
    
    print(f"✅ Large payload encrypted with AES-256-GCM")
    print(f"   Original size: {len(payload_json)} bytes")
    print(f"   Encrypted size: {len(encrypted_data['ciphertext'])} bytes")
    
    # Decrypt payload (one line!)
    decrypted_json = military_crypto.aes_decrypt(encrypted_data, aes_key)
    decrypted_payload = json.loads(decrypted_json)
    
    print(f"✅ Payload decrypted successfully")
    print(f"   Mission ID: {decrypted_payload['mission_id']}")
    print(f"   Classification: {decrypted_payload['classification']}")


if __name__ == "__main__":
    print("🔐 Military Crypto Library Examples\n")
    
    print("📨 1. RSA Message Encryption Example:")
    encrypt_battlefield_message_example()
    
    print("\n⛓️  2. Blockchain Operations Example:")
    create_blockchain_block_example()
    
    print("\n🔒 3. AES Large Payload Example:")
    aes_encryption_example()
    
    print("\n✅ All examples completed successfully!")
    print("📋 Summary of simplifications:")
    print("   • RSA encryption: 1 line vs 20+ lines manual")
    print("   • Digital signatures: 1 line vs 15+ lines manual") 
    print("   • Merkle trees: 1 line vs 50+ lines manual")
    print("   • Block mining: 1 line vs 30+ lines manual")
    print("   • AES encryption: 1 line vs 25+ lines manual")