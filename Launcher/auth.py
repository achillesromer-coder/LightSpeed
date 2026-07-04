# Launcher/auth.py
from __future__ import annotations
import json, secrets, hashlib
from pathlib import Path
from dataclasses import dataclass, asdict

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
USERS = DATA_DIR / "users.json"
COMPANIES = DATA_DIR / "companies.json"
PROJECTS = DATA_DIR / "projects.json"
for p in (DATA_DIR,):
    p.mkdir(exist_ok=True, parents=True)
for f in (USERS, COMPANIES, PROJECTS):
    if not f.exists(): f.write_text("[]", encoding="utf-8")

def _load(path: Path): return json.loads(path.read_text(encoding="utf-8"))
def _save(path: Path, obj): path.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def _hash_pw(pw: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 200_000).hex()

@dataclass
class User:
    username: str
    role: str = "viewer"   # viewer|designer|engineer|scientist|ops|admin|founder|it
    company_ids: list[str] = None
    salt: str = ""
    pw_hash: str = ""
    def set_password(self, pw: str):
        self.salt = secrets.token_hex(16); self.pw_hash = _hash_pw(pw, self.salt)

def list_users(): return [User(**u) for u in _load(USERS)]
def save_users(users: list[User]): _save(USERS, [asdict(x) for x in users])

def ensure_bootstrap():
    users = list_users()
    if not users:
        u = User(username="founder", role="founder", company_ids=[]); u.set_password("changeme")  # _____ set on first run
        save_users([u])
    for path, seed in ((COMPANIES, []), (PROJECTS, [])):
        if not path.exists(): _save(path, seed)

def verify(username: str, password: str) -> User | None:
    for u in list_users():
        if u.username == username:
            return u if u.pw_hash == _hash_pw(password, u.salt) else None
    return None

def list_companies(): return _load(COMPANIES)          # [{id,name}]
def save_companies(arr): _save(COMPANIES, arr)
def list_projects(): return _load(PROJECTS)            # [{id,company_id,name,parent_id}]
def save_projects(arr): _save(PROJECTS, arr)
