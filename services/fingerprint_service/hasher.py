import hashlib
import os

def generate_exact_hash(canonical_json: str, salt: str = None) -> str:
    """
    SHA-256 hashes the canonical JSON combined with a consortium-wide salt.
    """
    if salt is None:
        salt = os.getenv("CONSORTIUM_SALT", "default-dev-salt-12345")
        
    combined = canonical_json + salt
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()
