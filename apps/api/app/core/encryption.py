"""Token encryption utilities using Fernet symmetric encryption.

Used to encrypt GitHub access tokens at rest.
Never expose encryption keys or decrypted tokens to the LLM.
"""

import logging

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


def generate_encryption_key() -> str:
    """Generate a new Fernet encryption key. Use for GITHUB_ENCRYPTION_KEY."""
    return Fernet.generate_key().decode()


def encrypt_token(token: str, encryption_key: str) -> str:
    """Encrypt a token using Fernet symmetric encryption.

    Args:
        token: The plaintext token to encrypt.
        encryption_key: The Fernet key (from GITHUB_ENCRYPTION_KEY).

    Returns:
        Base64-encoded encrypted token string.
    """
    f = Fernet(encryption_key.encode())
    return f.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str, encryption_key: str) -> str:
    """Decrypt a Fernet-encrypted token.

    Args:
        encrypted_token: The encrypted token string.
        encryption_key: The Fernet key.

    Returns:
        Plaintext token.

    Raises:
        ValueError: If decryption fails (wrong key or corrupted data).
    """
    try:
        f = Fernet(encryption_key.encode())
        return f.decrypt(encrypted_token.encode()).decode()
    except (InvalidToken, Exception) as e:
        logger.error("Failed to decrypt token")
        raise ValueError("Failed to decrypt stored credentials") from e
