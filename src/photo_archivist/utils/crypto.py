from __future__ import annotations

import logging
from typing import Final

import keyring
from cryptography.fernet import Fernet
from keyring.errors import KeyringError

logger = logging.getLogger("photo_archivist.utils.crypto")

DEFAULT_SERVICE_NAME: Final[str] = "photo_archivist"


def get_or_create_fernet_key(
    key_name: str, *, service_name: str = DEFAULT_SERVICE_NAME
) -> bytes:
    """Fetch an existing Fernet key or create and persist a new one."""
    try:
        existing = keyring.get_password(service_name, key_name)
    except KeyringError as exc:  # pragma: no cover - protective logging
        logger.error({"event": "crypto.keyring.fetch_failed", "error": str(exc)})
        raise

    if existing:
        return existing.encode("utf-8")

    key = Fernet.generate_key()
    try:
        keyring.set_password(service_name, key_name, key.decode("utf-8"))
    except KeyringError as exc:
        logger.error({"event": "crypto.keyring.store_failed", "error": str(exc)})
        raise

    logger.info({"event": "crypto.keyring.key_created", "key_name": key_name})
    return key


def encrypt_bytes(
    data: bytes, key_name: str = "default", *, service_name: str = DEFAULT_SERVICE_NAME
) -> bytes:
    """Encrypt raw bytes using a Fernet key stored in the keyring."""
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("data must be bytes or bytearray")
    key = get_or_create_fernet_key(key_name, service_name=service_name)
    fernet = Fernet(key)
    return fernet.encrypt(bytes(data))


def decrypt_bytes(
    token: bytes,
    key_name: str = "default",
    *,
    service_name: str = DEFAULT_SERVICE_NAME,
) -> bytes:
    """Decrypt bytes previously produced by encrypt_bytes."""
    if not isinstance(token, (bytes, bytearray)):
        raise TypeError("token must be bytes or bytearray")
    key = get_or_create_fernet_key(key_name, service_name=service_name)
    fernet = Fernet(key)
    return fernet.decrypt(bytes(token))
