import os
import hashlib
try:
    from bech32 import bech32_encode, bech32_decode, convertbits
    BECH32_AVAILABLE = True
except ImportError:
    BECH32_AVAILABLE = False
    print("[WARNING] bech32 module not available, using simple address format")

# Import MemoryVault
try:
    from memoryvault import MemoryVault, MemoryVaultSeed
    MEMORYVAULT_AVAILABLE = True
except ImportError:
    MEMORYVAULT_AVAILABLE = False
    print("[WARNING] MemoryVault not available, using traditional address generation")

HRP = 'lakha'

# Global MemoryVault instance
_memory_vault = None

def get_memory_vault():
    """Get or create MemoryVault instance"""
    global _memory_vault
    if _memory_vault is None and MEMORYVAULT_AVAILABLE:
        _memory_vault = MemoryVault()
    return _memory_vault

def generate_address(pubkey_bytes=None):
    """Generate a new Bech32 address from pubkey bytes or random bytes."""
    if pubkey_bytes is None:
        pubkey_bytes = os.urandom(20)  # 160 bits, like Ethereum
    
    if BECH32_AVAILABLE:
        data = convertbits(pubkey_bytes, 8, 5)
        return bech32_encode(HRP, data)
    else:
        # Fallback: simple hex address with prefix
        return f"lakha{pubkey_bytes.hex()}"

def generate_address_from_story(story: str) -> dict:
    """
    Generate a Lakha address from a personal story using MemoryVault.
    
    Args:
        story (str): Personal story with private details
        
    Returns:
        dict: Contains address, mnemonic, story_hash, and validation info
    """
    if not MEMORYVAULT_AVAILABLE:
        raise ImportError("MemoryVault not available. Install required dependencies.")
    
    mv = get_memory_vault()
    
    # Validate story personalness
    validation = mv.validate_story_personalness(story)
    
    # Create MemoryVault seed
    seed = mv.create_memory_vault_seed(story)
    
    return {
        'address': seed.address,
        'mnemonic': seed.mnemonic,
        'story_hash': seed.story_hash,
        'personal_elements_count': len(seed.personal_elements),
        'personalness_score': validation['personalness_score'],
        'element_types': validation['element_types'],
        'recommendations': validation['recommendations'],
        'private_key': seed.private_key,
        'public_key': seed.public_key
    }

def generate_address_from_mnemonic(mnemonic: str) -> dict:
    """
    Generate a Lakha address from a BIP39 mnemonic phrase.
    
    Args:
        mnemonic (str): BIP39 mnemonic phrase
        
    Returns:
        dict: Contains address, private_key, and public_key
    """
    if not MEMORYVAULT_AVAILABLE:
        raise ImportError("MemoryVault not available. Install required dependencies.")
    
    mv = get_memory_vault()
    
    # Recover from mnemonic
    seed = mv.recover_from_mnemonic(mnemonic)
    
    return {
        'address': seed.address,
        'private_key': seed.private_key,
        'public_key': seed.public_key,
        'mnemonic': seed.mnemonic
    }

def validate_story_personalness(story: str) -> dict:
    """
    Validate how personal a story is for MemoryVault.
    
    Args:
        story (str): Personal story to validate
        
    Returns:
        dict: Validation results and recommendations
    """
    if not MEMORYVAULT_AVAILABLE:
        raise ImportError("MemoryVault not available. Install required dependencies.")
    
    mv = get_memory_vault()
    return mv.validate_story_personalness(story)

def is_valid_address(address):
    """Check if the address is a valid Lahka address."""
    if BECH32_AVAILABLE:
        hrp, data = bech32_decode(address)
        if hrp != HRP or data is None:
            return False
        # Convert back to bytes to check length
        decoded = convertbits(data, 5, 8, False)
        return decoded is not None and len(decoded) == 20
    else:
        # Fallback: check if it starts with 'lakha' and has valid hex
        if not address.startswith('lakha'):
            return False
        try:
            hex_part = address[5:]  # Remove 'lakha' prefix
            bytes.fromhex(hex_part)
            return len(hex_part) == 40  # 20 bytes = 40 hex chars
        except:
            return False

def encode_address(pubkey_bytes):
    """Encode pubkey bytes to a Lahka address."""
    if BECH32_AVAILABLE:
        data = convertbits(pubkey_bytes, 8, 5)
        return bech32_encode(HRP, data)
    else:
        return f"lakha{pubkey_bytes.hex()}"

def decode_address(address):
    """Decode a Lahka address to bytes. Returns None if invalid."""
    if BECH32_AVAILABLE:
        hrp, data = bech32_decode(address)
        if hrp != HRP or data is None:
            return None
        decoded = convertbits(data, 5, 8, False)
        if decoded is None or len(decoded) != 20:
            return None
        return bytes(decoded)
    else:
        # Fallback: decode from hex
        if not address.startswith('lakha'):
            return None
        try:
            hex_part = address[5:]  # Remove 'lakha' prefix
            return bytes.fromhex(hex_part)
        except:
            return None

# Legacy function for backward compatibility
def generate_address_legacy(pubkey_bytes=None):
    """Legacy address generation (original function)."""
    return generate_address(pubkey_bytes) 