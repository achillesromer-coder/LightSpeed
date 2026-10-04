from __future__ import annotations

import pytest

from lightspeed_runtime.platform_keystore import (
    CRED_PERSIST_LOCAL_MACHINE,
    PlatformSecretNotFound,
    WindowsCredentialManagerStore,
)


class FakeCredentialApi:
    def __init__(self):
        self.rows = {}

    def write(self, target, username, secret, persist):
        self.rows[target] = (username, bytes(secret), persist)

    def read(self, target):
        try:
            return self.rows[target]
        except KeyError as exc:
            raise PlatformSecretNotFound("missing") from exc

    def delete(self, target):
        return self.rows.pop(target, None) is not None


def test_platform_secret_roundtrip_and_revocation_without_receipt_secret():
    api = FakeCredentialApi()
    store = WindowsCredentialManagerStore(api=api)
    reference = store.put("provider/test-token", b"ephemeral-secret", username="cgx-test")

    assert store.recover("provider/test-token") == b"ephemeral-secret"
    assert store.exists("provider/test-token") is True
    assert api.rows[reference.target_name][2] == CRED_PERSIST_LOCAL_MACHINE

    receipt = reference.public_receipt()
    assert receipt["secret_material_emitted"] is False
    assert "ephemeral-secret" not in str(receipt)
    assert "target_name" not in receipt

    assert store.revoke("provider/test-token") is True
    assert store.exists("provider/test-token") is False
    with pytest.raises(PlatformSecretNotFound):
        store.recover("provider/test-token")


def test_platform_secret_rejects_empty_oversized_and_unsafe_keys():
    store = WindowsCredentialManagerStore(api=FakeCredentialApi())

    with pytest.raises(ValueError):
        store.put("safe", b"")
    with pytest.raises(ValueError):
        store.put("safe", b"x" * 1025)
    with pytest.raises(ValueError):
        store.put("../escape", b"x")
    with pytest.raises(ValueError):
        store.put("contains space", b"x")


def test_revoke_missing_is_idempotent_false():
    store = WindowsCredentialManagerStore(api=FakeCredentialApi())
    assert store.revoke("missing") is False
