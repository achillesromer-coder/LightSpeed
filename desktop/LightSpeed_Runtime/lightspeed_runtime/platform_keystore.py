from __future__ import annotations

from dataclasses import dataclass
import ctypes
import ctypes.wintypes as wt
import hashlib
import os
import re
from typing import Protocol


CRED_TYPE_GENERIC = 1
CRED_PERSIST_SESSION = 1
CRED_PERSIST_LOCAL_MACHINE = 2
ERROR_NOT_FOUND = 1168
MAX_SECRET_BYTES = 1024
_KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,255}$")


class PlatformKeystoreError(RuntimeError):
    pass


class PlatformKeystoreUnavailable(PlatformKeystoreError):
    pass


class PlatformSecretNotFound(PlatformKeystoreError):
    pass


@dataclass(frozen=True)
class PlatformSecretReference:
    provider: str
    target_name: str
    target_fingerprint: str
    persistence: str
    secret_bytes: int

    def public_receipt(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "target_fingerprint": self.target_fingerprint,
            "persistence": self.persistence,
            "secret_bytes": self.secret_bytes,
            "secret_material_emitted": False,
        }


class CredentialApi(Protocol):
    def write(self, target: str, username: str, secret: bytes, persist: int) -> None: ...
    def read(self, target: str) -> tuple[str, bytes, int]: ...
    def delete(self, target: str) -> bool: ...


class FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", wt.DWORD), ("dwHighDateTime", wt.DWORD)]


class CREDENTIALW(ctypes.Structure):
    _fields_ = [
        ("Flags", wt.DWORD),
        ("Type", wt.DWORD),
        ("TargetName", wt.LPWSTR),
        ("Comment", wt.LPWSTR),
        ("LastWritten", FILETIME),
        ("CredentialBlobSize", wt.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", wt.DWORD),
        ("AttributeCount", wt.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wt.LPWSTR),
        ("UserName", wt.LPWSTR),
    ]


class WindowsCredentialApi:
    def __init__(self) -> None:
        if os.name != "nt":
            raise PlatformKeystoreUnavailable("Windows Credential Manager is only available on Windows")
        self._advapi = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
        self._advapi.CredWriteW.argtypes = [ctypes.POINTER(CREDENTIALW), wt.DWORD]
        self._advapi.CredWriteW.restype = wt.BOOL
        self._advapi.CredReadW.argtypes = [
            wt.LPCWSTR,
            wt.DWORD,
            wt.DWORD,
            ctypes.POINTER(ctypes.POINTER(CREDENTIALW)),
        ]
        self._advapi.CredReadW.restype = wt.BOOL
        self._advapi.CredDeleteW.argtypes = [wt.LPCWSTR, wt.DWORD, wt.DWORD]
        self._advapi.CredDeleteW.restype = wt.BOOL
        self._advapi.CredFree.argtypes = [ctypes.c_void_p]
        self._advapi.CredFree.restype = None

    def write(self, target: str, username: str, secret: bytes, persist: int) -> None:
        buffer = (ctypes.c_ubyte * len(secret)).from_buffer_copy(secret)
        credential = CREDENTIALW()
        credential.Flags = 0
        credential.Type = CRED_TYPE_GENERIC
        credential.TargetName = target
        credential.Comment = "LightSpeed platform-protected secret"
        credential.CredentialBlobSize = len(secret)
        credential.CredentialBlob = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))
        credential.Persist = persist
        credential.AttributeCount = 0
        credential.Attributes = None
        credential.TargetAlias = None
        credential.UserName = username
        if not self._advapi.CredWriteW(ctypes.byref(credential), 0):
            raise PlatformKeystoreError(
                f"Windows CredWriteW failed with error {ctypes.get_last_error()}"
            )

    def read(self, target: str) -> tuple[str, bytes, int]:
        pointer = ctypes.POINTER(CREDENTIALW)()
        if not self._advapi.CredReadW(
            target, CRED_TYPE_GENERIC, 0, ctypes.byref(pointer)
        ):
            error = ctypes.get_last_error()
            if error == ERROR_NOT_FOUND:
                raise PlatformSecretNotFound("Platform secret was not found")
            raise PlatformKeystoreError(f"Windows CredReadW failed with error {error}")
        try:
            credential = pointer.contents
            secret = ctypes.string_at(
                credential.CredentialBlob, credential.CredentialBlobSize
            )
            return credential.UserName or "", secret, int(credential.Persist)
        finally:
            self._advapi.CredFree(pointer)

    def delete(self, target: str) -> bool:
        if self._advapi.CredDeleteW(target, CRED_TYPE_GENERIC, 0):
            return True
        error = ctypes.get_last_error()
        if error == ERROR_NOT_FOUND:
            return False
        raise PlatformKeystoreError(f"Windows CredDeleteW failed with error {error}")


class WindowsCredentialManagerStore:
    """Bounded Windows Credential Manager wrapper for application secrets.

    This is deliberately separate from the LightSpeed owner-password database.
    It is intended for tokens/keys that require OS-protected at-rest storage.
    """

    provider = "windows-credential-manager-v1"

    def __init__(
        self,
        *,
        namespace: str = "LightSpeed/CGX",
        persistence: str = "local_machine",
        api: CredentialApi | None = None,
    ) -> None:
        self.namespace = namespace.strip().rstrip("/")
        if not self.namespace or len(self.namespace) > 128:
            raise ValueError("A bounded keystore namespace is required")
        if persistence not in {"session", "local_machine"}:
            raise ValueError("persistence must be session or local_machine")
        self.persistence = persistence
        self._persist_value = (
            CRED_PERSIST_SESSION
            if persistence == "session"
            else CRED_PERSIST_LOCAL_MACHINE
        )
        self._api = api

    def _backend(self) -> CredentialApi:
        if self._api is None:
            self._api = WindowsCredentialApi()
        return self._api

    def target_name(self, key: str) -> str:
        bounded = str(key or "").strip()
        if not _KEY_PATTERN.fullmatch(bounded):
            raise ValueError("Platform secret key contains unsupported characters")
        target = f"{self.namespace}/{bounded}"
        if len(target) > 512:
            raise ValueError("Platform secret target is too long")
        return target

    @staticmethod
    def _fingerprint(target: str) -> str:
        return hashlib.sha256(target.encode("utf-8")).hexdigest()

    def put(self, key: str, secret: bytes, *, username: str = "LightSpeed") -> PlatformSecretReference:
        payload = bytes(secret)
        if not payload:
            raise ValueError("Platform secret must not be empty")
        if len(payload) > MAX_SECRET_BYTES:
            raise ValueError(f"Platform secret exceeds {MAX_SECRET_BYTES} bytes")
        target = self.target_name(key)
        self._backend().write(target, str(username or "LightSpeed"), payload, self._persist_value)
        return PlatformSecretReference(
            provider=self.provider,
            target_name=target,
            target_fingerprint=self._fingerprint(target),
            persistence=self.persistence,
            secret_bytes=len(payload),
        )

    def recover(self, key: str) -> bytes:
        target = self.target_name(key)
        _username, secret, _persist = self._backend().read(target)
        return secret

    def revoke(self, key: str) -> bool:
        return self._backend().delete(self.target_name(key))

    def exists(self, key: str) -> bool:
        try:
            self._backend().read(self.target_name(key))
        except PlatformSecretNotFound:
            return False
        return True
