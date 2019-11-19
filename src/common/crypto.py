"""Cryptography related utilites."""
from hashlib import blake2b
from uuid import uuid4


def get_uuid_hex(digest_size=10):
    """Generate hex of uuid4 with the defined size."""
    return blake2b(uuid4().bytes, digest_size=digest_size).hexdigest()
