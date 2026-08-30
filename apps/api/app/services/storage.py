"""Where redacted document bytes are written.

A local directory behind an interface, so the demo runs from `docker compose up` with no
cloud account, and a deployment can swap in object storage without touching the routes.

Two rules this module enforces rather than documents:

  1. **Keys are built from UUIDs only.** No part of a storage key comes from user input,
     so a filename like `../../etc/passwd` has nowhere to go.
  2. **Nothing unredacted arrives here.** `documents.analyse` returns the bytes that may
     be stored, and it raises rather than returning an original. This module writes what
     it is given; the decision was made upstream.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from app.core.config import settings


class StorageError(RuntimeError):
    pass


def _root() -> Path:
    root = Path(settings.STORAGE_DIR).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def build_key(application_id: uuid.UUID, document_id: uuid.UUID, extension: str = "png") -> str:
    """A storage key made entirely of identifiers we generated."""
    safe = extension.lower().lstrip(".")
    if not safe.isalnum():
        raise StorageError(f"Refusing an extension that is not alphanumeric: {extension!r}")
    return f"applications/{application_id}/{document_id}.{safe}"


def write(key: str, data: bytes) -> str:
    """Write bytes at `key` and return the key. Refuses to escape the storage root."""
    root = _root()
    target = (root / key).resolve()
    if not target.is_relative_to(root):
        raise StorageError(f"Storage key escapes the storage root: {key!r}")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return key


def read(key: str) -> bytes:
    root = _root()
    target = (root / key).resolve()
    if not target.is_relative_to(root):
        raise StorageError(f"Storage key escapes the storage root: {key!r}")
    if not target.is_file():
        raise StorageError(f"No stored object at {key!r}")
    return target.read_bytes()


def exists(key: str) -> bool:
    root = _root()
    target = (root / key).resolve()
    return target.is_relative_to(root) and target.is_file()
