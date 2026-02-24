"""Tests for AES encryption."""

import pytest
from rag_shared.security.encryption import (
    AESEncryption,
    encrypt_data,
    decrypt_data,
    set_encryption_key,
)


def test_aes_encryption_decryption():
    """Test basic AES encryption and decryption."""
    cipher = AESEncryption()
    plaintext = "Secret message: नमस्ते"

    # Encrypt
    encrypted = cipher.encrypt(plaintext)
    assert encrypted != plaintext
    assert isinstance(encrypted, str)

    # Decrypt
    decrypted = cipher.decrypt(encrypted)
    assert decrypted == plaintext


def test_aes_different_plaintexts():
    """Test that different plaintexts produce different ciphertexts."""
    cipher = AESEncryption()

    encrypted1 = cipher.encrypt("message1")
    encrypted2 = cipher.encrypt("message2")

    assert encrypted1 != encrypted2


def test_aes_same_plaintext_different_ciphertexts():
    """Test that same plaintext encrypts differently (due to random nonce)."""
    cipher = AESEncryption()
    plaintext = "same message"

    encrypted1 = cipher.encrypt(plaintext)
    encrypted2 = cipher.encrypt(plaintext)

    # Should be different due to random nonce
    assert encrypted1 != encrypted2

    # But both should decrypt to same plaintext
    assert cipher.decrypt(encrypted1) == plaintext
    assert cipher.decrypt(encrypted2) == plaintext


def test_aes_with_existing_key():
    """Test creating cipher with existing key."""
    key = AESEncryption.generate_key()
    key_bytes = AESEncryption.key_from_string(key)

    cipher = AESEncryption(key_bytes)
    plaintext = "test message"

    encrypted = cipher.encrypt(plaintext)
    decrypted = cipher.decrypt(encrypted)

    assert decrypted == plaintext


def test_aes_invalid_key_length():
    """Test that invalid key length raises error."""
    with pytest.raises(ValueError):
        AESEncryption(b"short_key")


def test_aes_decrypt_invalid():
    """Test that decrypting invalid data raises error."""
    cipher = AESEncryption()

    with pytest.raises(ValueError):
        cipher.decrypt("invalid_encrypted_data")


def test_aes_generate_key():
    """Test key generation."""
    key1 = AESEncryption.generate_key()
    key2 = AESEncryption.generate_key()

    # Keys should be different (random)
    assert key1 != key2

    # Keys should be valid hex strings of correct length
    assert len(key1) == 64  # 32 bytes = 64 hex chars
    assert len(key2) == 64


def test_key_from_string():
    """Test converting hex key string to bytes."""
    key_hex = AESEncryption.generate_key()
    key_bytes = AESEncryption.key_from_string(key_hex)

    assert isinstance(key_bytes, bytes)
    assert len(key_bytes) == 32


def test_key_from_invalid_string():
    """Test that invalid key string raises error."""
    with pytest.raises(ValueError):
        AESEncryption.key_from_string("not_hex")

    with pytest.raises(ValueError):
        AESEncryption.key_from_string("ff" * 31)  # Wrong length


def test_module_level_encrypt_decrypt():
    """Test module-level encrypt/decrypt functions."""
    key = AESEncryption.generate_key()
    key_bytes = AESEncryption.key_from_string(key)
    set_encryption_key(key_bytes)

    plaintext = "secret data"
    encrypted = encrypt_data(plaintext)
    decrypted = decrypt_data(encrypted)

    assert decrypted == plaintext


def test_unicode_text_encryption():
    """Test encryption of Unicode text."""
    cipher = AESEncryption()
    plaintext = "नमस्ते मुझे नाम फिल्में 中文 🎉"

    encrypted = cipher.encrypt(plaintext)
    decrypted = cipher.decrypt(encrypted)

    assert decrypted == plaintext


def test_empty_string_encryption():
    """Test encryption of empty string."""
    cipher = AESEncryption()
    plaintext = ""

    encrypted = cipher.encrypt(plaintext)
    decrypted = cipher.decrypt(encrypted)

    assert decrypted == plaintext
