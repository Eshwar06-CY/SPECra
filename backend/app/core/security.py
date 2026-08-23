"""
Security, hashing, and token generation utilities for SPECra.
"""
import hashlib
import hmac
import os
import secrets
from typing import Tuple

PBKDF2_ITERATIONS = 100_000
SALT_BYTES = 16


class SecurityUtils:
    """
    Cryptographic password hashing and verification using PBKDF2-HMAC-SHA256.
    Zero third-party binary C-extensions required; pure standard library.
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hashes password with random 16-byte salt and 100,000 PBKDF2 iterations.
        Returns formatted string: 'pbkdf2:sha256:100000$<salt_hex>$<hash_hex>'
        """
        if not password:
            raise ValueError("Password cannot be empty.")
        
        salt = os.urandom(SALT_BYTES)
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            PBKDF2_ITERATIONS,
        )
        return f"pbkdf2:sha256:{PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Constant-time verification of plain password against stored hash string.
        """
        if not plain_password or not hashed_password:
            return False

        try:
            algorithm, salt_hex, hash_hex = hashed_password.split("$")
            _, hash_name, iterations_str = algorithm.split(":")
            iterations = int(iterations_str)
            salt = bytes.fromhex(salt_hex)
            expected_hash = bytes.fromhex(hash_hex)

            dk = hashlib.pbkdf2_hmac(
                hash_name,
                plain_password.encode("utf-8"),
                salt,
                iterations,
            )
            return hmac.compare_digest(dk, expected_hash)
        except Exception:
            return False

    @staticmethod
    def generate_session_token() -> str:
        """
        Generates 32-byte cryptographic random token (URL-safe).
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def normalize_email(email: str) -> str:
        """
        Trims whitespace and lowercases email address for consistent indexing.
        """
        return email.strip().lower() if email else ""
