import hashlib
import json

def generate_checksum(payload: dict) -> str:
    """
    Generates a SHA-256 checksum from structured patient data
    """
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
