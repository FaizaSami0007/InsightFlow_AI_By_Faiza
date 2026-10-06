"""Secure Secret Management & Credential Encryption Provider for Phase 17 Connectors."""

import base64
import hashlib
import json
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet

from app.core.config import settings


class SecretProvider:
    """Handles field-level symmetric encryption and decryption for sensitive connector credentials."""

    SENSITIVE_KEY_PATTERNS = {
        "password",
        "api_key",
        "token",
        "secret",
        "client_secret",
        "access_token",
        "private_key",
        "auth_header",
        "connection_string",
        "ssh_key",
        "key",
    }

    def __init__(self, master_key: Optional[str] = None):
        raw_key = master_key or settings.jwt_secret
        # Derive a deterministic 32-byte urlsafe base64 key from the master secret
        derived = hashlib.sha256(raw_key.encode("utf-8")).digest()
        self._fernet = Fernet(base64.urlsafe_b64encode(derived))

    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """Encrypts dictionary credentials into a safe ciphertext string."""
        if not credentials:
            return ""
        payload = json.dumps(credentials).encode("utf-8")
        return self._fernet.encrypt(payload).decode("utf-8")

    def encrypt(self, credentials: Dict[str, Any]) -> str:
        """Alias for encrypt_credentials."""
        return self.encrypt_credentials(credentials)

    def decrypt_credentials(self, ciphertext: Optional[str]) -> Dict[str, Any]:
        """Decrypts ciphertext string back into dictionary credentials in memory."""
        if not ciphertext:
            return {}
        try:
            decrypted = self._fernet.decrypt(ciphertext.encode("utf-8"))
            return json.loads(decrypted.decode("utf-8"))
        except Exception as e:
            raise ValueError(f"Failed to decrypt connector credentials: {str(e)}")

    def decrypt(self, ciphertext: Optional[str]) -> Dict[str, Any]:
        """Alias for decrypt_credentials."""
        return self.decrypt_credentials(ciphertext)

    @classmethod
    def mask_credentials(cls, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Returns safe masked representations for sensitive credentials and preserves public config."""
        masked: Dict[str, Any] = {}
        for k, v in credentials.items():
            k_lower = k.lower()
            if any(pattern in k_lower for pattern in cls.SENSITIVE_KEY_PATTERNS):
                masked[k] = "********"
            else:
                masked[k] = v
        return masked
