import os
import hashlib

def generate_random_bytes(length):
    """Generate cryptographically secure random bytes of specified length."""
    return os.urandom(length)

def xor_bytes(b1, b2):
    """XOR two byte arrays and return the result."""
    if len(b1) != len(b2):
        raise ValueError("Lengths of byte arrays for XOR operation do not match.")
    return bytes(x ^ y for x, y in zip(b1, b2))

def hash_data(data):
    """Return SHA-256 digest of data (useful for integrity checks)."""
    return hashlib.sha256(data).digest()