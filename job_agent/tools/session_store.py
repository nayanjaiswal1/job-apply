from __future__ import annotations

import json
import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


_SESSIONS_DIR = Path("sessions")
_KEY_ENV = "SECRET_KEY"


def _key() -> bytes:
    raw = os.environ.get(_KEY_ENV, "")
    # derive a 32-byte key by hashing — avoids length requirements on arbitrary secret strings
    import hashlib
    return hashlib.sha256(raw.encode()).digest()


class SessionStore:
    """AES-GCM encrypted per-platform cookie/session storage."""

    def __init__(self, sessions_dir: Path = _SESSIONS_DIR) -> None:
        self._dir = sessions_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, platform: str) -> Path:
        return self._dir / f"{platform}.enc"

    def save(self, platform: str, cookies: dict[str, str]) -> None:
        aesgcm = AESGCM(_key())
        nonce = os.urandom(12)
        plaintext = json.dumps(cookies).encode()
        ct = aesgcm.encrypt(nonce, plaintext, None)
        self._path(platform).write_bytes(nonce + ct)

    def load(self, platform: str) -> dict[str, str] | None:
        p = self._path(platform)
        if not p.exists():
            return None
        data = p.read_bytes()
        nonce, ct = data[:12], data[12:]
        aesgcm = AESGCM(_key())
        try:
            plaintext = aesgcm.decrypt(nonce, ct, None)
            return dict(json.loads(plaintext))
        except Exception:
            return None

    def delete(self, platform: str) -> None:
        p = self._path(platform)
        if p.exists():
            p.unlink()
