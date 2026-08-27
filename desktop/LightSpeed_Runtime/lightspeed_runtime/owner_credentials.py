from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import base64
import hashlib
import hmac
import json
from pathlib import Path
import re
import secrets
from typing import Any, Callable
from uuid import uuid4


CREDENTIAL_SCHEMA = "lightspeed-owner-credential-v1"
ACHILLES_REFERENCE_SCHEMA = "lightspeed-achilles-credential-reference-v1"
PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 600_000
REMINDER_DAYS = 90
MANDATORY_DAYS = 365
MINIMUM_PASSWORD_LENGTH = 12
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


class CredentialError(ValueError):
    pass


class CredentialUnavailable(CredentialError):
    pass


class CredentialAuthenticationFailed(CredentialError):
    pass


class CredentialChangeRequired(CredentialError):
    pass


def utc_now() -> datetime:
    return datetime.now(UTC)


def _as_utc(value: datetime | None) -> datetime:
    current = value or utc_now()
    if current.tzinfo is None:
        return current.replace(tzinfo=UTC)
    return current.astimezone(UTC)


def _iso(value: datetime) -> str:
    return _as_utc(value).isoformat(timespec="seconds")


def _parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return _as_utc(parsed)


def validate_username(username: str) -> str:
    value = str(username or "").strip()
    if not USERNAME_PATTERN.fullmatch(value):
        raise CredentialError("A bounded username is required")
    return value


def validate_new_password(password: str, *, username: str = "") -> None:
    value = str(password or "")
    if len(value) < MINIMUM_PASSWORD_LENGTH:
        raise CredentialError(
            f"New passwords must contain at least {MINIMUM_PASSWORD_LENGTH} characters"
        )
    if username and username.casefold() in value.casefold():
        raise CredentialError("New passwords must not contain the username")
    classes = sum(
        (
            any(character.islower() for character in value),
            any(character.isupper() for character in value),
            any(character.isdigit() for character in value),
            any(not character.isalnum() for character in value),
        )
    )
    if classes < 3:
        raise CredentialError(
            "New passwords must use at least three of lowercase, uppercase, digits, and symbols"
        )


def create_password_record(
    password: str,
    *,
    username: str,
    must_change: bool = False,
    bootstrap: bool = False,
    previous_record: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    bounded_username = validate_username(username)
    if bootstrap:
        if not str(password or ""):
            raise CredentialError("A non-empty bootstrap password is required")
    else:
        validate_new_password(password, username=bounded_username)

    changed = _as_utc(now)
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        str(password).encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    try:
        prior_sequence = int((previous_record or {}).get("rotation_sequence") or 0)
    except (TypeError, ValueError):
        prior_sequence = 0
    return {
        "schema_version": CREDENTIAL_SCHEMA,
        "username": bounded_username,
        "alg": PASSWORD_ALGORITHM,
        "iter": PASSWORD_ITERATIONS,
        "salt_b64": base64.b64encode(salt).decode("ascii"),
        "hash_b64": base64.b64encode(digest).decode("ascii"),
        "credential_key_id": f"LSCRED-{uuid4().hex.upper()}",
        "rotation_sequence": prior_sequence + 1,
        "changed_utc": _iso(changed),
        "reminder_due_utc": _iso(changed + timedelta(days=REMINDER_DAYS)),
        "mandatory_due_utc": _iso(changed + timedelta(days=MANDATORY_DAYS)),
        "must_change": bool(must_change),
        "bootstrap_credential": bool(bootstrap),
    }


def verify_password_record(record: Any, password: str) -> bool:
    try:
        if not isinstance(record, dict):
            return False
        if record.get("schema_version") != CREDENTIAL_SCHEMA:
            return False
        if record.get("alg") != PASSWORD_ALGORITHM:
            return False
        iterations = int(record.get("iter") or 0)
        if iterations < 200_000:
            return False
        salt = base64.b64decode(str(record.get("salt_b64") or ""), validate=True)
        expected = base64.b64decode(str(record.get("hash_b64") or ""), validate=True)
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            str(password or "").encode("utf-8"),
            salt,
            iterations,
        )
        return bool(expected) and hmac.compare_digest(actual, expected)
    except (TypeError, ValueError, OverflowError):
        return False


def credential_status(
    record: Any,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    if not isinstance(record, dict) or record.get("schema_version") != CREDENTIAL_SCHEMA:
        return {
            "configured": False,
            "must_change": False,
            "reminder_due": False,
            "mandatory_due": False,
        }
    current = _as_utc(now)
    changed = _parse_utc(record.get("changed_utc"))
    reminder = _parse_utc(record.get("reminder_due_utc"))
    mandatory = _parse_utc(record.get("mandatory_due_utc"))
    mandatory_due = mandatory is None or current >= mandatory
    must_change = bool(record.get("must_change")) or mandatory_due
    return {
        "configured": True,
        "username": str(record.get("username") or ""),
        "credential_key_id": str(record.get("credential_key_id") or ""),
        "rotation_sequence": int(record.get("rotation_sequence") or 0),
        "changed_utc": _iso(changed) if changed else None,
        "reminder_due_utc": _iso(reminder) if reminder else None,
        "mandatory_due_utc": _iso(mandatory) if mandatory else None,
        "must_change": must_change,
        "reminder_due": reminder is None or current >= reminder,
        "mandatory_due": mandatory_due,
        "password_age_days": (
            max(0, int((current - changed).total_seconds() // 86_400)) if changed else None
        ),
        "policy": {
            "reminder_days": REMINDER_DAYS,
            "mandatory_days": MANDATORY_DAYS,
            "minimum_password_length": MINIMUM_PASSWORD_LENGTH,
        },
    }


class CredentialStore:
    """Store credentials in the dedicated, migration-owned auth table."""

    def __init__(self, database: Any):
        self.database = database

    def _user(self, username: str) -> dict[str, Any]:
        value = validate_username(username)
        rows = self.database.execute_query(
            "SELECT id, username, role, clearance FROM users WHERE username = ? LIMIT 1",
            (value,),
        )
        if not rows:
            raise CredentialUnavailable("Configured user was not found")
        return dict(rows[0])

    def read_record(self, username: str) -> dict[str, Any] | None:
        user = self._user(username)
        try:
            rows = self.database.execute_query(
                """
                SELECT username, schema_version, alg, iterations, salt_b64, hash_b64,
                       credential_key_id, rotation_sequence, changed_utc,
                       reminder_due_utc, mandatory_due_utc, must_change,
                       bootstrap_credential
                FROM auth_credentials WHERE username = ? LIMIT 1
                """,
                (str(user["username"]),),
            )
        except Exception as exc:
            raise CredentialUnavailable(
                "The dedicated credential table is unavailable; run the reviewed Trinity migration"
            ) from exc
        if not rows:
            return None
        row = dict(rows[0])
        return {
            "schema_version": row.get("schema_version"),
            "username": row.get("username"),
            "alg": row.get("alg"),
            "iter": row.get("iterations"),
            "salt_b64": row.get("salt_b64"),
            "hash_b64": row.get("hash_b64"),
            "credential_key_id": row.get("credential_key_id"),
            "rotation_sequence": row.get("rotation_sequence"),
            "changed_utc": row.get("changed_utc"),
            "reminder_due_utc": row.get("reminder_due_utc"),
            "mandatory_due_utc": row.get("mandatory_due_utc"),
            "must_change": bool(row.get("must_change")),
            "bootstrap_credential": bool(row.get("bootstrap_credential")),
        }

    def _write_record(self, username: str, record: dict[str, Any]) -> None:
        try:
            changed = self.database.execute_update(
                """
                INSERT INTO auth_credentials (
                  username, schema_version, alg, iterations, salt_b64, hash_b64,
                  credential_key_id, rotation_sequence, changed_utc,
                  reminder_due_utc, mandatory_due_utc, must_change,
                  bootstrap_credential, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(username) DO UPDATE SET
                  schema_version = excluded.schema_version,
                  alg = excluded.alg,
                  iterations = excluded.iterations,
                  salt_b64 = excluded.salt_b64,
                  hash_b64 = excluded.hash_b64,
                  credential_key_id = excluded.credential_key_id,
                  rotation_sequence = excluded.rotation_sequence,
                  changed_utc = excluded.changed_utc,
                  reminder_due_utc = excluded.reminder_due_utc,
                  mandatory_due_utc = excluded.mandatory_due_utc,
                  must_change = excluded.must_change,
                  bootstrap_credential = excluded.bootstrap_credential,
                  updated_at = excluded.updated_at
                """,
                (
                    username,
                    record["schema_version"],
                    record["alg"],
                    int(record["iter"]),
                    record["salt_b64"],
                    record["hash_b64"],
                    record["credential_key_id"],
                    int(record["rotation_sequence"]),
                    record["changed_utc"],
                    record["reminder_due_utc"],
                    record["mandatory_due_utc"],
                    1 if record.get("must_change") else 0,
                    1 if record.get("bootstrap_credential") else 0,
                ),
            )
        except Exception as exc:
            raise CredentialUnavailable(
                "Credential update could not reach the dedicated auth table"
            ) from exc
        if changed < 1:
            raise CredentialUnavailable("Credential update was not persisted")

    def bootstrap(
        self,
        username: str,
        password: str,
        *,
        replace_existing: bool = False,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        user = self._user(username)
        canonical_username = str(user["username"])
        previous = self.read_record(canonical_username)
        if previous and not replace_existing:
            raise CredentialError("A credential already exists; explicit replacement is required")
        record = create_password_record(
            password,
            username=canonical_username,
            must_change=True,
            bootstrap=True,
            previous_record=previous,
            now=now,
        )
        self._write_record(canonical_username, record)
        return credential_status(record, now=now)

    def authenticate(
        self,
        username: str,
        password: str,
        *,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        record = self.read_record(username)
        if not record or not verify_password_record(record, password):
            raise CredentialAuthenticationFailed("Username or password is incorrect")
        return credential_status(record, now=now)

    def change_password(
        self,
        username: str,
        current_password: str,
        new_password: str,
        *,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        user = self._user(username)
        canonical_username = str(user["username"])
        previous = self.read_record(canonical_username)
        if not previous or not verify_password_record(previous, current_password):
            raise CredentialAuthenticationFailed("Username or password is incorrect")
        if hmac.compare_digest(str(current_password), str(new_password)):
            raise CredentialError("The new password must differ from the current password")
        record = create_password_record(
            new_password,
            username=canonical_username,
            must_change=False,
            bootstrap=False,
            previous_record=previous,
            now=now,
        )
        self._write_record(canonical_username, record)
        return credential_status(record, now=now)


@dataclass(frozen=True)
class SessionRecord:
    username: str
    credential_key_id: str
    expires_utc: datetime
    scope: str


class OwnerSessionStore:
    """Memory-only loopback sessions. Raw tokens are never persisted."""

    def __init__(self, *, lifetime: timedelta = timedelta(hours=8)):
        self.lifetime = lifetime
        self._sessions: dict[str, SessionRecord] = {}

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(str(token or "").encode("utf-8")).hexdigest()

    def issue(
        self,
        *,
        username: str,
        credential_key_id: str,
        scope: str = "owner",
        now: datetime | None = None,
    ) -> tuple[str, str]:
        current = _as_utc(now)
        token = secrets.token_urlsafe(32)
        expires = current + self.lifetime
        self._sessions[self._token_hash(token)] = SessionRecord(
            username=validate_username(username),
            credential_key_id=str(credential_key_id),
            expires_utc=expires,
            scope="password_change" if scope == "password_change" else "owner",
        )
        return token, _iso(expires)

    def verify(
        self,
        token: str,
        *,
        required_scope: str | None = None,
        now: datetime | None = None,
    ) -> SessionRecord:
        key = self._token_hash(token)
        record = self._sessions.get(key)
        current = _as_utc(now)
        if record is None or current >= record.expires_utc:
            self._sessions.pop(key, None)
            raise CredentialAuthenticationFailed("Owner session is invalid or expired")
        if required_scope and record.scope != required_scope:
            raise CredentialAuthenticationFailed("Owner session scope is not sufficient")
        return record

    def revoke(self, token: str) -> None:
        self._sessions.pop(self._token_hash(token), None)

    def revoke_username(self, username: str) -> None:
        key = validate_username(username).casefold()
        self._sessions = {
            digest: record
            for digest, record in self._sessions.items()
            if record.username.casefold() != key
        }


def write_achilles_credential_reference(
    destination: Path | str,
    *,
    status: dict[str, Any],
    event: str,
    now: datetime | None = None,
) -> Path:
    """Persist non-secret credential lineage for Achilles review.

    The reference deliberately excludes password hashes, salts, session tokens,
    and reset authority. Possession of this file cannot authenticate a caller.
    """
    username = validate_username(str(status.get("username") or ""))
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    current = _as_utc(now)
    payload: dict[str, Any] = {
        "schema_version": ACHILLES_REFERENCE_SCHEMA,
        "username": username,
        "non_secret_reference_only": True,
        "grants_authentication": False,
        "current": {},
        "history": [],
    }
    if path.is_file():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(existing, dict) and existing.get("schema_version") == ACHILLES_REFERENCE_SCHEMA:
                payload = existing
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            pass
    reference = {
        "event": str(event or "rotation")[:64],
        "recorded_utc": _iso(current),
        "credential_key_id": str(status.get("credential_key_id") or ""),
        "rotation_sequence": int(status.get("rotation_sequence") or 0),
        "changed_utc": status.get("changed_utc"),
        "reminder_due_utc": status.get("reminder_due_utc"),
        "mandatory_due_utc": status.get("mandatory_due_utc"),
        "must_change": bool(status.get("must_change")),
    }
    history = [item for item in payload.get("history", []) if isinstance(item, dict)]
    if not any(
        item.get("credential_key_id") == reference["credential_key_id"]
        for item in history
    ):
        history.append(reference)
    payload.update(
        {
            "username": username,
            "non_secret_reference_only": True,
            "grants_authentication": False,
            "current": reference,
            "history": history[-100:],
        }
    )
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(4)}.tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    return path
