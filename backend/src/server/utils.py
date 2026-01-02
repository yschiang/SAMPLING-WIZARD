"""
Server utility functions for timestamp handling and other common tasks.
"""
import os
import hashlib
import uuid
from datetime import datetime


def get_deterministic_timestamp():
    """
    Get a timestamp that can be deterministic for testing.
    
    In test environments (when TEST_DETERMINISTIC_TIMESTAMPS is set),
    returns a fixed timestamp. Otherwise returns current UTC time.
    
    This enables deterministic testing without affecting production behavior.
    """
    if os.getenv("TEST_DETERMINISTIC_TIMESTAMPS") == "true":
        # Fixed timestamp for deterministic testing
        return "2024-01-01T12:00:00Z"
    else:
        # Real timestamp for production
        return datetime.utcnow().isoformat() + "Z"


def get_deterministic_id(content_hash_input):
    """
    Get an ID that can be deterministic for testing.
    
    In test environments, generates deterministic IDs based on content hash.
    Otherwise generates random UUIDs.
    
    Args:
        content_hash_input: String content to use for deterministic ID generation
    
    Returns:
        String ID that's deterministic in test mode, random in production
    """
    if os.getenv("TEST_DETERMINISTIC_TIMESTAMPS") == "true":
        # Generate deterministic ID based on content hash
        hash_obj = hashlib.md5(content_hash_input.encode())
        # Format as UUID-like string for compatibility
        hash_hex = hash_obj.hexdigest()
        return f"{hash_hex[:8]}-{hash_hex[8:12]}-{hash_hex[12:16]}-{hash_hex[16:20]}-{hash_hex[20:32]}"
    else:
        # Real UUID for production
        return str(uuid.uuid4())