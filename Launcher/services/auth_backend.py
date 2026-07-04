# Launcher/services/auth_backend.py
from __future__ import annotations

import os
import json
import hmac
import base64
import hashlib
import secrets
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict, Any, List


APP_ROOT = Path(__file__).resolve().parents[1]      # .../Launcher
DATA_DIR = APP_ROOT.parent / "data"                 # .../data
COMPANIES_DIR = DATA_DIR / "companies"
COMPANIES_DIR.mkdir(parents=True, exist_ok=True)


# ---------- password hashing ----------
def _hash_password(password: str, salt_b64: Optional[str] = None) -> Dict[str, str]:
    salt = base64.b64decode(salt_b64) if salt_b64 else secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000, dklen=32)
    return {
        "salt": base64.b64encode(salt).decode("ascii"),
        "hash": base64.b64encode(dk).decode("ascii"),
        "algo": "pbkdf2_sha256_120k_32",
    }


def _verify_password(password: str, rec: Dict[str, Any]) -> bool:
    try:
        salt = rec["salt"]
        want = rec["hash"]
        algo = rec.get("algo")
        if algo != "pbkdf2_sha256_120k_32":
            return False
        got = _hash_password(password, salt)["hash"]
        return hmac.compare_digest(want, got)
    except Exception:
        return False


# ---------- models ----------
@dataclass
class User:
    id: str
    name: str
    email: str
    role: str
    clearance: int
    enabled: bool = True
    prefs: Dict[str, Any] = None
    # password fields (stored only in users.json)
    salt: str = ""
    hash: str = ""
    algo: str = "pbkdf2_sha256_120k_32"

    def to_public(self) -> Dict[str, Any]:
        d = asdict(self)
        for k in ("salt", "hash", "algo"):
            d.pop(k, None)
        return d


# ---------- helpers ----------
def _company_dir(company: str) -> Path:
    d = COMPANIES_DIR / company
    (d / "projects").mkdir(parents=True, exist_ok=True)
    return d


def _users_path(company: str) -> Path:
    d = _company_dir(company)
    return d / "users.json"


def _load_users(company: str) -> Dict[str, Any]:
    p = _users_path(company)
    if not p.exists():
        p.write_text(json.dumps({"users": []}, indent=2), encoding="utf-8")
    return json.loads(p.read_text(encoding="utf-8"))


def _save_users(company: str, data: Dict[str, Any]) -> None:
    p = _users_path(company)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ---------- public API ----------
def ensure_founder(company: str, name: str, email: str, password: str) -> User:
    """Create founder if none exists; id='founder' reserved."""
    data = _load_users(company)
    users: List[Dict[str, Any]] = data.get("users", [])
    for u in users:
        if u.get("role") in ("Founder",) or u.get("id") == "founder":
            return User(**u)
    hp = _hash_password(password)
    founder = User(
        id="founder",
        name=name,
        email=email,
        role="Founder",
        clearance=5,
        enabled=True,
        prefs={"theme": "dark", "ui_scale": 1.0},
        salt=hp["salt"],
        hash=hp["hash"],
        algo=hp["algo"],
    )
    users.append(asdict(founder))
    data["users"] = users
    _save_users(company, data)
    return founder


def create_user(company: str, user_id: str, name: str, email: str,
                role: str = "Viewer", clearance: int = 1, password: Optional[str] = None) -> User:
    data = _load_users(company)
    users = data.get("users", [])
    if any(u.get("id") == user_id for u in users):
        raise ValueError(f"user id '{user_id}' already exists")
    hp = _hash_password(password or secrets.token_urlsafe(12))
    u = User(
        id=user_id, name=name, email=email,
        role=role, clearance=int(clearance),
        enabled=True, prefs={"theme": "dark", "ui_scale": 1.0},
        salt=hp["salt"], hash=hp["hash"], algo=hp["algo"],
    )
    users.append(asdict(u))
    data["users"] = users
    _save_users(company, data)
    return u


def list_users(company: str, public_only: bool = True) -> List[Dict[str, Any]]:
    users = _load_users(company).get("users", [])
    if public_only:
        return [User(**u).to_public() for u in users]
    return users


def set_role(company: str, user_id: str, role: str, clearance: Optional[int] = None) -> None:
    data = _load_users(company)
    changed = False
    for u in data.get("users", []):
        if u.get("id") == user_id:
            u["role"] = role
            if clearance is not None:
                u["clearance"] = int(clearance)
            changed = True
            break
    if not changed:
        raise KeyError(user_id)
    _save_users(company, data)


def authenticate(company: str, email_or_id: str, password: str) -> Optional[Dict[str, Any]]:
    """Return public user dict on success; None otherwise."""
    data = _load_users(company)
    for u in data.get("users", []):
        if email_or_id in (u.get("email"), u.get("id")):
            if _verify_password(password, u):
                return User(**u).to_public()
            return None
    return None

