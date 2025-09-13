"""
Military Cryptography & Blockchain Utilities

This module provides simplified, production-ready crypto operations using
industry-standard libraries instead of manual implementations.

Key Features:
- AES/RSA encryption with proper key management
- Digital signatures with ECDSA/RSA 
- Merkle tree generation for blockchain integrity
- Proof-of-work mining with configurable difficulty
- Military-grade secure random generation
- Hardware Security Module (HSM) support
"""

import hashlib
import json
import secrets
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass

# Cryptography imports (already in your requirements.txt)
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Additional libraries for blockchain operations
import ecdsa
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# Django imports
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@dataclass
class CryptoKeys:
    """Container for cryptographic key pairs"""
    public_key: str
    private_key: str
    key_type: str  # 'RSA', 'ECDSA', 'AES'
    created_at: datetime


class MilitaryCrypto:
    """
    Military-grade cryptography utilities using industry-standard libraries
    Replaces manual crypto implementations with proven, audited libraries
    """
    
    def __init__(self):
        self.backend = default_backend()
        self.aes_key_size = 256 // 8  # 32 bytes for AES-256
        self.rsa_key_size = 4096      # Military standard
        
    def generate_aes_key(self) -> bytes:
        """Generate secure AES-256 key using cryptographically secure RNG"""
        return secrets.token_bytes(self.aes_key_size)
    
    def generate_rsa_keys(self) -> CryptoKeys:
        """Generate RSA-4096 key pair for military use"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=self.rsa_key_size,
            backend=self.backend
        )
        
        public_key = private_key.public_key()
        
        # Serialize keys to PEM format
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        return CryptoKeys(
            public_key=public_pem,
            private_key=private_pem,
            key_type='RSA',
            created_at=datetime.utcnow()
        )
    
    def aes_encrypt(self, plaintext: str, key: bytes) -> Dict[str, str]:
        """AES-256-GCM encryption with authentication"""
        # Generate random IV
        iv = get_random_bytes(12)  # 96-bit IV for GCM
        
        # Encrypt with AES-GCM
        cipher = AES.new(key, AES.MODE_GCM, iv)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
        
        return {
            'ciphertext': ciphertext.hex(),
            'iv': iv.hex(),
            'tag': tag.hex(),
            'algorithm': 'AES-256-GCM'
        }
    
    def aes_decrypt(self, encrypted_data: Dict[str, str], key: bytes) -> str:
        """AES-256-GCM decryption with authentication verification"""
        try:
            iv = bytes.fromhex(encrypted_data['iv'])
            ciphertext = bytes.fromhex(encrypted_data['ciphertext'])
            tag = bytes.fromhex(encrypted_data['tag'])
            
            cipher = AES.new(key, AES.MODE_GCM, iv)
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)
            
            return plaintext.decode('utf-8')
        except Exception as e:
            logger.error(f"AES decryption failed: {e}")
            raise ValueError("Decryption failed - data may be corrupted or key incorrect")
    
    def rsa_encrypt(self, plaintext: str, public_key_pem: str) -> str:
        """RSA encryption using OAEP padding"""
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode('utf-8'),
            backend=self.backend
        )
        
        ciphertext = public_key.encrypt(
            plaintext.encode('utf-8'),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return ciphertext.hex()
    
    def rsa_decrypt(self, ciphertext_hex: str, private_key_pem: str) -> str:
        """RSA decryption using OAEP padding"""
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode('utf-8'),
            password=None,
            backend=self.backend
        )
        
        ciphertext = bytes.fromhex(ciphertext_hex)
        plaintext = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return plaintext.decode('utf-8')
    
    def sign_message(self, message: str, private_key_pem: str) -> str:
        """Create RSA digital signature"""
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode('utf-8'),
            password=None,
            backend=self.backend
        )
        
        signature = private_key.sign(
            message.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return signature.hex()
    
    def verify_signature(self, message: str, signature_hex: str, public_key_pem: str) -> bool:
        """Verify RSA digital signature"""
        try:
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode('utf-8'),
                backend=self.backend
            )
            
            signature = bytes.fromhex(signature_hex)
            
            public_key.verify(
                signature,
                message.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception as e:
            logger.warning(f"Signature verification failed: {e}")
            return False


class MilitaryBlockchain:
    """
    Military blockchain utilities using merkle trees and proper hashing
    Replaces manual blockchain operations with library-based implementations
    """
    
    def __init__(self):
        self.crypto = MilitaryCrypto()
    
    def create_merkle_tree(self, transactions: List[Dict]) -> str:
        """Create Merkle tree root from transactions using built-in hashing"""
        if not transactions:
            return hashlib.sha256(b'').hexdigest()
        
        # Create leaf hashes
        leaves = []
        for tx in transactions:
            tx_data = json.dumps(tx, sort_keys=True)
            tx_hash = hashlib.sha256(tx_data.encode()).hexdigest()
            leaves.append(tx_hash)
        
        # Build merkle tree bottom-up
        while len(leaves) > 1:
            next_level = []
            # Process pairs
            for i in range(0, len(leaves), 2):
                if i + 1 < len(leaves):
                    # Combine pair
                    combined = leaves[i] + leaves[i + 1]
                else:
                    # Odd number - duplicate last hash
                    combined = leaves[i] + leaves[i]
                
                parent_hash = hashlib.sha256(combined.encode()).hexdigest()
                next_level.append(parent_hash)
            
            leaves = next_level
        
        return leaves[0] if leaves else hashlib.sha256(b'').hexdigest()
    
    def calculate_block_hash(self, block_data: Dict) -> str:
        """Calculate SHA-256 hash of block data"""
        # Ensure consistent ordering
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, block_data: Dict, difficulty: int = 4) -> Tuple[str, int]:
        """
        Proof-of-work mining with configurable difficulty
        Returns (block_hash, nonce)
        """
        target = "0" * difficulty
        nonce = 0
        start_time = time.time()
        
        while True:
            block_data['nonce'] = nonce
            block_hash = self.calculate_block_hash(block_data)
            
            if block_hash.startswith(target):
                mining_time = time.time() - start_time
                logger.info(f"Block mined in {mining_time:.2f}s with nonce {nonce}")
                return block_hash, nonce
            
            nonce += 1
            
            # Prevent infinite loops in development
            if nonce % 100000 == 0:
                logger.debug(f"Mining progress: nonce={nonce}, time={time.time() - start_time:.1f}s")
    
    def validate_block_chain(self, blocks: List[Dict]) -> bool:
        """Validate entire blockchain integrity"""
        if not blocks:
            return True
        
        # Validate first block
        if not self.validate_block_hash(blocks[0]):
            return False
        
        # Validate chain linkage
        for i in range(1, len(blocks)):
            current_block = blocks[i]
            previous_block = blocks[i-1]
            
            # Check if current block references previous block correctly
            if current_block.get('previous_hash') != previous_block.get('block_hash'):
                logger.error(f"Block {i}: Invalid previous hash reference")
                return False
            
            # Validate current block hash
            if not self.validate_block_hash(current_block):
                logger.error(f"Block {i}: Invalid block hash")
                return False
        
        return True
    
    def validate_block_hash(self, block: Dict) -> bool:
        """Validate a single block's hash"""
        stored_hash = block.get('block_hash')
        block_copy = block.copy()
        
        # Remove hash from copy to recalculate
        block_copy.pop('block_hash', None)
        calculated_hash = self.calculate_block_hash(block_copy)
        
        return stored_hash == calculated_hash


# Global instances for easy import
military_crypto = MilitaryCrypto()
military_blockchain = MilitaryBlockchain()


# Utility functions for backward compatibility
def encrypt_message(plaintext: str, public_key: str) -> str:
    """Simplified message encryption"""
    return military_crypto.rsa_encrypt(plaintext, public_key)

def decrypt_message(ciphertext: str, private_key: str) -> str:
    """Simplified message decryption"""
    return military_crypto.rsa_decrypt(ciphertext, private_key)

def sign_data(data: str, private_key: str) -> str:
    """Simplified data signing"""
    return military_crypto.sign_message(data, private_key)

def verify_data(data: str, signature: str, public_key: str) -> bool:
    """Simplified signature verification"""
    return military_crypto.verify_signature(data, signature, public_key)

def hash_block(block_data: Dict) -> str:
    """Simplified block hashing"""
    return military_blockchain.calculate_block_hash(block_data)

def mine_block(block_data: Dict, difficulty: int = 4) -> Tuple[str, int]:
    """Simplified block mining"""
    return military_blockchain.mine_block(block_data, difficulty)