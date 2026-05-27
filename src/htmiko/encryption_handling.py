# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

import base64
import os
from typing import Any
from typing import Dict
from typing import Union

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers import algorithms
from cryptography.hazmat.primitives.ciphers import modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ENCRYPTION_PREFIX: str = "__encrypt__"


def get_encryption_key() -> bytes:
    key: Union[str, None] = os.environ.get("HTMIKO_TOOLS_KEY")
    if not key:
        raise ValueError(
            "Encryption key not found. Set the 'HTMIKO_TOOLS_KEY' environment variable.",
        )
    return key.encode()


def decrypt_value(encrypted_value: str, key: bytes, encryption_type: str) -> str:
    # Remove the encryption prefix
    encrypted_value = encrypted_value.replace(ENCRYPTION_PREFIX, "", 1)

    # Extract salt and ciphertext
    salt_str, ciphertext_str = encrypted_value.split(":", 1)
    salt = base64.b64decode(salt_str)
    ciphertext = base64.b64decode(ciphertext_str)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    derived_key: bytes = kdf.derive(key)

    if encryption_type == "fernet":
        f = Fernet(base64.urlsafe_b64encode(derived_key))
        return f.decrypt(ciphertext).decode()
    elif encryption_type == "aes128":
        iv = ciphertext[:16]
        ciphertext = ciphertext[16:]
        cipher = Cipher(algorithms.AES(derived_key[:16]), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded: bytes = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        unpadded: bytes = unpadder.update(padded) + unpadder.finalize()
        return unpadded.decode()
    else:
        raise ValueError(f"Unsupported encryption type: {encryption_type}")


def decrypt_config(
    config: Dict[str, Any],
    key: bytes,
    encryption_type: str,
) -> Dict[str, Any]:
    for device, params in config.items():
        if isinstance(params, dict):
            for field, value in params.items():
                if isinstance(value, str) and value.startswith(ENCRYPTION_PREFIX):
                    len_prefix = len(ENCRYPTION_PREFIX)
                    data: str = value[len_prefix:]
                    params[field] = decrypt_value(data, key, encryption_type)
    return config


def encrypt_value(value: str, key: bytes, encryption_type: str) -> str:
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    derived_key: bytes = kdf.derive(key)

    if encryption_type == "fernet":
        f = Fernet(base64.urlsafe_b64encode(derived_key))
        encrypted = f.encrypt(value.encode())
    elif encryption_type == "aes128":
        iv = os.urandom(16)
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(value.encode()) + padder.finalize()
        cipher = Cipher(algorithms.AES(derived_key[:16]), modes.CBC(iv))
        encryptor = cipher.encryptor()
        encrypted = iv + encryptor.update(padded_data) + encryptor.finalize()
    else:
        raise ValueError(f"Unsupported encryption type: {encryption_type}")

    # Combine salt and encrypted data
    b64_salt = base64.b64encode(salt).decode()
    return f"{ENCRYPTION_PREFIX}{b64_salt}:{base64.b64encode(encrypted).decode()}"
