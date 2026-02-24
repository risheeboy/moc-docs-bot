"""AES encryption for data at rest."""

from typing import Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import base64
import logging

logger = logging.getLogger(__name__)


class AESEncryption:
    """AES-256-GCM encryption for sensitive data at rest.

    Uses authenticated encryption (GCM mode) to ensure data integrity.
    """

    def __init__(self, key: Optional[bytes] = None):
        """Initialize encryption with AES-256 key.

        Args:
            key: 32-byte encryption key (256-bit). If None, generates random key.
        """
        if key is None:
            key = os.urandom(32)  # Generate random 256-bit key
        elif len(key) != 32:
            raise ValueError("Key must be 32 bytes (256 bits)")

        self.key = key

    def encrypt(self, plaintext: str) -> str:
        """Encrypt string using AES-256-GCM.

        Args:
            plaintext: Text to encrypt

        Returns:
            Base64-encoded (nonce + ciphertext + tag)
        """
        # Generate random 96-bit nonce
        nonce = os.urandom(12)

        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.GCM(nonce),
            backend=default_backend(),
        )

        # Encrypt
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext.encode("utf-8")) + encryptor.finalize()
        tag = encryptor.tag

        # Combine nonce + ciphertext + tag and encode to base64
        encrypted = nonce + ciphertext + tag
        encoded = base64.b64encode(encrypted).decode("utf-8")

        return encoded

    def decrypt(self, encrypted: str) -> str:
        """Decrypt AES-256-GCM encrypted string.

        Args:
            encrypted: Base64-encoded (nonce + ciphertext + tag)

        Returns:
            Decrypted plaintext

        Raises:
            ValueError: If decryption fails or authentication fails
        """
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted.encode("utf-8"))

            # Extract components (12-byte nonce, 16-byte tag)
            nonce = encrypted_bytes[:12]
            ciphertext = encrypted_bytes[12:-16]
            tag = encrypted_bytes[-16:]

            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.key),
                modes.GCM(nonce, tag),
                backend=default_backend(),
            )

            # Decrypt
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            return plaintext.decode("utf-8")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Failed to decrypt data (invalid key or corrupted data)")

    @staticmethod
    def generate_key() -> str:
        """Generate a random AES-256 key.

        Returns:
            Hex-encoded 256-bit key
        """
        key = os.urandom(32)
        return key.hex()

    @staticmethod
    def key_from_string(key_str: str) -> bytes:
        """Convert hex-encoded key string to bytes.

        Args:
            key_str: Hex-encoded key string

        Returns:
            32-byte key

        Raises:
            ValueError: If key is not valid hex or not 256 bits
        """
        try:
            key_bytes = bytes.fromhex(key_str)
            if len(key_bytes) != 32:
                raise ValueError(f"Key must be 32 bytes, got {len(key_bytes)}")
            return key_bytes
        except ValueError as e:
            raise ValueError(f"Invalid key format: {e}")


# Module-level encryption functions for convenience
_default_cipher: Optional[AESEncryption] = None


def set_encryption_key(key: bytes) -> None:
    """Set the default encryption key for module-level functions.

    Args:
        key: 32-byte AES-256 key
    """
    global _default_cipher
    _default_cipher = AESEncryption(key)


def encrypt_data(plaintext: str) -> str:
    """Encrypt string using default encryption key.

    Args:
        plaintext: Text to encrypt

    Returns:
        Encrypted base64-encoded string

    Raises:
        RuntimeError: If encryption key not set
    """
    if _default_cipher is None:
        raise RuntimeError("Encryption key not set. Call set_encryption_key() first.")
    return _default_cipher.encrypt(plaintext)


def decrypt_data(encrypted: str) -> str:
    """Decrypt string using default encryption key.

    Args:
        encrypted: Encrypted base64-encoded string

    Returns:
        Decrypted plaintext

    Raises:
        RuntimeError: If encryption key not set
    """
    if _default_cipher is None:
        raise RuntimeError("Encryption key not set. Call set_encryption_key() first.")
    return _default_cipher.decrypt(encrypted)
