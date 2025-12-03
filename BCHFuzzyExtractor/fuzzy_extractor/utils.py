import os
import hashlib

def generate_random_bytes(length):
    """지정된 길이만큼의 랜덤 바이트를 생성합니다."""
    return os.urandom(length)

def xor_bytes(b1, b2):
    """두 바이트 배열을 XOR 연산합니다."""
    if len(b1) != len(b2):
        raise ValueError("XOR 연산을 위한 두 바이트 배열의 길이가 다릅니다.")
    return bytes(x ^ y for x, y in zip(b1, b2))

def hash_data(data):
    """데이터의 SHA-256 해시를 반환합니다 (무결성 검증용)."""
    return hashlib.sha256(data).digest()