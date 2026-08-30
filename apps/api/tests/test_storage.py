"""Storage keys are built from identifiers we generated, and cannot escape the root.

A document store that accepts a caller-supplied path is one `../` away from writing into
the application directory. These tests exist so that stays true after a refactor.
"""

from __future__ import annotations

import uuid

import pytest

from app.core.config import settings
from app.services import storage


@pytest.fixture(autouse=True)
def isolated_root(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "STORAGE_DIR", str(tmp_path))


def test_a_key_is_made_only_of_uuids() -> None:
    app_id, doc_id = uuid.uuid4(), uuid.uuid4()
    key = storage.build_key(app_id, doc_id)
    assert key == f"applications/{app_id}/{doc_id}.png"


def test_a_non_alphanumeric_extension_is_refused() -> None:
    with pytest.raises(storage.StorageError):
        storage.build_key(uuid.uuid4(), uuid.uuid4(), extension="../../sh")


def test_a_traversing_key_cannot_write_outside_the_root() -> None:
    with pytest.raises(storage.StorageError):
        storage.write("../../escaped.png", b"nope")


def test_a_traversing_key_cannot_read_outside_the_root() -> None:
    with pytest.raises(storage.StorageError):
        storage.read("../../../etc/passwd")


def test_a_round_trip_returns_the_same_bytes() -> None:
    key = storage.build_key(uuid.uuid4(), uuid.uuid4())
    storage.write(key, b"redacted-bytes")
    assert storage.read(key) == b"redacted-bytes"
    assert storage.exists(key)


def test_reading_a_missing_object_raises_rather_than_returning_empty() -> None:
    with pytest.raises(storage.StorageError):
        storage.read("applications/nope/nope.png")
