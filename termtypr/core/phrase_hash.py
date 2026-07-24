"""Stable hashing for phrase identity."""

import hashlib


def phrase_hash(phrase_text: str) -> str:
    """Hash a phrase to a short stable identifier.

    Computed on the exact phrase string (no normalization) so every
    component agrees on a phrase's identity.
    """
    return hashlib.sha256(phrase_text.encode("utf-8")).hexdigest()[:16]
