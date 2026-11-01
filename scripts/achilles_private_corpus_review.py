#!/usr/bin/env python3
"""Achilles private, source-bound GPT export text review.

Additive R0->candidate R1 only. Never edits inputs, invokes models, executes
assistant tasks, writes the native database, serves raw dialogue, or mints CGX.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, hmac, html, http.server, json, os
from pathlib import Path
import re, secrets, sqlite3, threading, time, urllib.parse

SCHEMA = "CGX-ACHILLES-PRIVATE-R1/0.1"
PROGRESS_SCHEMA = "CGX-ACHILLES-PRIVATE-R1-PROGRESS/0.1"
WORDS = re.compile(r"\b[\w]+(?:['’-][\w]+)*\b", re.UNICODE)
FAMILIES = {
    "achilles_pa": ("achilles","personal assistant","jarvis","reason log","owner lane"),
    "cognigrex": ("cognigrex","cgx","object_id","family set","semantic"),
    "unispace": ("unispace","workspace","cockpit","gui","squarespace"),
    "lightspeed": ("lightspeed","ls go","neo","ollama","agent runtime"),
    "load_alexandria": ("alexandria","load.cgx","corpus","wikipedia","ingestion"),
    "filespace": ("filespace","dataspace","dbr","rootauthority","recovery"),
    "toolkits": ("ccc","cyc","plugin","toolkit","capability"),
    "raphael": ("raphael","emassc","physics","quantum","simulation"),
    "eco": ("athene","eco-grex","second cycle","bioblocks","ecology"),
    "geometry": ("geometry","shorthand","fractal","compression","hexagon"),
    "rights": ("copyright","licence","license","patent","publish"),
    "creative": ("interdimensional","dragon ball","naruto","doom","minecraft"),
    "business": ("intersol","warehouse","business","product"),
}
DENIED_CHANNELS = {"analysis", "summary", "notification", "justify", "confidence"}
SHA_RE = re.compile(r"^[a-f0-9]{64}$")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def qualified_receipt(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "CGX-OWNER-GPT-EXPORT-SHARD-RECEIPT/0.1":
        raise ValueError("SOURCE_RECEIPT_SCHEMA_HOLD")
    result = data.get("shards")
    if not isinstance(result, list) or len(result) != 12:
        raise ValueError("SOURCE_SHARD_COUNT_HOLD")
    seen = set()
    for entry in result:
        n = entry.get("shard")
        if (not isinstance(n, str) or not re.fullmatch(r"conversations-0(?:0[0-9]|1[01])\.json", n)
                or n in seen or not SHA_RE.fullmatch(str(entry.get("sha256", "")))
                or type(entry.get("size_bytes")) is not int or entry["size_bytes"] <= 0):
            raise ValueError("SOURCE_IDENTITY_HOLD")
        seen.add(n)
    if sum(x["size_bytes"] for x in result) != data.get("total_bytes"):
        raise ValueError("SOURCE_TOTAL_BYTES_HOLD")
    return sorted(result, key=lambda x: x["shard"])


def verify_source(path: Path, entry: dict) -> str:
    if not path.is_file() or path.is_symlink() or path.stat().st_size != entry["size_bytes"]:
        raise ValueError("SOURCE_FILE_IDENTITY_HOLD:" + entry["shard"])
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != entry["sha256"]:
        raise ValueError("SOURCE_SHA256_MISMATCH:" + entry["shard"])
    return digest.hexdigest()


def extract_text(message: dict) -> tuple[str, int]:
    content = message.get("content") or {}
    parts = content.get("parts") if isinstance(content, dict) else None
    text_parts, nontext = [], 0
    if isinstance(parts, list):
        for part in parts:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and isinstance(part.get("text"), str):
                text_parts.append(part["text"])
                nontext += 1  # Additional structured attributes excluded.
            else:
                nontext += 1
    elif isinstance(content, dict) and isinstance(content.get("text"), str):
        text_parts.append(content["text"])
    elif isinstance(content, str):
        text_parts.append(content)
    elif content:
        nontext += 1
    return "\n".join(text_parts), nontext


def connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(path, timeout=30)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.executescript("""
    CREATE TABLE IF NOT EXISTS shard(
      name TEXT PRIMARY KEY, sha256 TEXT, bytes INTEGER, conversations INTEGER,
      visible_nodes INTEGER, state TEXT, committed_utc TEXT);
    CREATE TABLE IF NOT EXISTS conversation(
      id TEXT PRIMARY KEY, shard TEXT, title TEXT, created REAL, updated REAL,
      visible_words INTEGER);
    CREATE TABLE IF NOT EXISTS message(
      id TEXT PRIMARY KEY, conversation_id TEXT, role TEXT, channel TEXT,
      source_shard TEXT, created REAL, parent_node TEXT, text TEXT,
      words INTEGER, text_sha256 TEXT, nontext_parts INTEGER);
    CREATE TABLE IF NOT EXISTS occurrence(
      shard TEXT, conversation_id TEXT, node_id TEXT, message_id TEXT,
      PRIMARY KEY(shard,conversation_id,node_id));
    CREATE INDEX IF NOT EXISTS message_parent_index ON message(parent_node);
    CREATE TABLE IF NOT EXISTS prompt_response(
      response_id TEXT PRIMARY KEY, prompt_id TEXT, conversation_id TEXT,
      ancestor_hops INTEGER);
    CREATE TABLE IF NOT EXISTS family_candidate(
      message_id TEXT, family TEXT, score INTEGER, PRIMARY KEY(message_id,family));
    CREATE TABLE IF NOT EXISTS source_issue(
      kind TEXT, source_id TEXT, detail TEXT);
    """)
    con.execute('CREATE VIRTUAL TABLE IF NOT EXISTS message_fts USING fts5(message_id UNINDEXED,content,tokenize="unicode61")')
    con.commit()
    return con


def family_scores(text: str, title: str) -> list[tuple[str, int]]:
    sample = (title + "\n" + text[:16000]).lower()
    return [(family, score) for family, terms in FAMILIES.items()
            if (score := sum(min(sample.count(t), 4) for t in terms)) >= 2]


def user_ancestor(node: dict, mapping: dict, limit: int = 120) -> tuple[str | None, int]:
    parent = node.get("parent")
    seen = set()
    steps = 0
    while parent and parent not in seen and steps < limit:
        seen.add(parent)
        steps += 1
        item = mapping.get(parent)
        if not isinstance(item, dict):
            break
        message = item.get("message") or {}
        if not isinstance(message, dict):
            break
        if (message.get("author") or {}).get("role") == "user":
            return str(message.get("id") or parent), steps
        parent = item.get("parent")
    return None, steps


def ingest_shard(con: sqlite3.Connection, source: Path, entry: dict) -> tuple[int, int, int]:
    digest = verify_source(source, entry)
    previous = con.execute("SELECT sha256,state FROM shard WHERE name=?", (entry["shard"],)).fetchone()
    if previous:
        if previous == (digest, "VERIFIED_R1_COMMITTED"):
            return -1, 0, 0
        raise ValueError("SOURCE_PREVIOUS_STATE_HOLD:" + entry["shard"])
    raw = json.loads(source.read_bytes())
    if not isinstance(raw, list):
        raise ValueError("SOURCE_JSON_FORMAT_HOLD")
    visible = 0
    try:
        con.execute("BEGIN")
        for conv in raw:
            if not isinstance(conv, dict):
                raise ValueError("SOURCE_CONVERSATION_SHAPE_HOLD")
            cid = str(conv.get("conversation_id") or conv.get("id") or "")
            if not cid:
                raise ValueError("SOURCE_CONVERSATION_ID_HOLD")
            mapping = conv.get("mapping") or {}
            if not isinstance(mapping, dict):
                raise ValueError("SOURCE_MAPPING_HOLD")
            title = str(conv.get("title") or "")
            words_sum = 0
            for node_id, node in mapping.items():
                if not isinstance(node, dict):
                    continue
                msg = node.get("message")
                if not isinstance(msg, dict):
                    continue
                mid = str(msg.get("id") or node_id)
                role = str((msg.get("author") or {}).get("role") or "")
                channel = str((msg.get("metadata") or {}).get("channel") or "")
                if role not in ("user", "assistant") or channel in DENIED_CHANNELS:
                    continue
                text, nontext = extract_text(msg)
                words = len(WORDS.findall(text))
                text_hash = sha(text.encode("utf-8"))
                old = con.execute("SELECT text_sha256,role FROM message WHERE id=?", (mid,)).fetchone()
                if old and old != (text_hash, role):
                    raise ValueError("CONFLICTING_MESSAGE_ID_HOLD:" + mid)
                con.execute("INSERT OR IGNORE INTO occurrence VALUES (?,?,?,?)",
                            (entry["shard"], cid, str(node_id), mid))
                if old:
                    continue
                con.execute("INSERT INTO message VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (mid, cid, role, channel, entry["shard"], msg.get("create_time"),
                             node.get("parent"), text, words, text_hash, nontext))
                con.execute("INSERT INTO message_fts VALUES (?,?)", (mid, text))
                for family, score in family_scores(text, title):
                    con.execute("INSERT OR IGNORE INTO family_candidate VALUES (?,?,?)",
                                (mid, family, score))
                if role == "assistant":
                    uid, hops = user_ancestor(node, mapping)
                    if uid:
                        con.execute("INSERT OR IGNORE INTO prompt_response VALUES (?,?,?,?)",
                                    (mid, uid, cid, hops))
                    else:
                        con.execute("INSERT INTO source_issue VALUES (?,?,?)",
                                    ("UNRESOLVED_USER_PARENT", mid, "Original branch ancestry lacks user"))
                words_sum += words
                visible += 1
            con.execute("INSERT OR IGNORE INTO conversation VALUES (?,?,?,?,?,?)",
                        (cid, entry["shard"], title, conv.get("create_time"),
                         conv.get("update_time"), words_sum))
        con.execute("INSERT INTO shard VALUES (?,?,?,?,?,?,?)",
                    (entry["shard"], digest, entry["size_bytes"], len(raw), visible,
                     "VERIFIED_R1_COMMITTED", dt.datetime.now(dt.timezone.utc).isoformat()))
        con.commit()
    except Exception:
        con.rollback()
        raise
    return len(raw), visible, entry["size_bytes"]


def summary(con: sqlite3.Connection) -> dict:
    one = lambda sql: con.execute(sql).fetchone()[0]
    return {
        "schema": SCHEMA,
        "state": "PRIVATE_TEXT_R1_REVIEW_ONLY",
        "shards": one("SELECT count(*) FROM shard WHERE state='VERIFIED_R1_COMMITTED'"),
        "conversations": one("SELECT count(*) FROM conversation"),
        "unique_messages": one("SELECT count(*) FROM message"),
        "visible_words": one("SELECT coalesce(sum(words),0) FROM message"),
        "user_words": one("SELECT coalesce(sum(words),0) FROM message WHERE role='user'"),
        "assistant_words": one("SELECT coalesce(sum(words),0) FROM message WHERE role='assistant'"),
        "prompt_response_links": one("SELECT count(*) FROM prompt_response"),
        "nontext_markers": one("SELECT coalesce(sum(nontext_parts),0) FROM message"),
        "candidate_topics": [{"family": f, "messages": n} for f, n in con.execute(
            "SELECT family,count(*) FROM family_candidate GROUP BY family ORDER BY count(*) DESC")],
        "native_admission": False, "model_weights_modified": False,
        "rights": "PRIVATE_OWNER_SOURCE_REVIEW_ONLY",
    }


PAGE = """<!doctype html><meta charset="utf-8"><title>Achilles private CGX review</title>
<style>body{font:16px system-ui;background:#0c1423;color:#e5f3ff;max-width:880px;margin:50px auto}
main{background:#172339;border-radius:15px;padding:26px}#bar{background:#63cab3;height:19px;width:0;border-radius:10px}
.track{background:#35475a;border-radius:10px;overflow:hidden}small{color:#aac0d4}</style>
<main><small>Achilles / Cognigrex — private loopback source review</small>
<h1>Original corpus ingestion</h1><p id="state">Awaiting verified source</p>
<div class="track"><div id="bar"></div></div><p id="pct">0%</p>
<p id="counts">No source records yet</p><small>R1 text review only — no training, DBR admission or publication</small></main>
<script>
const token=decodeURIComponent(location.pathname.slice(3));
async function refresh(){try{const r=await fetch('/api?token='+encodeURIComponent(token),{cache:'no-store'});if(!r.ok)return;
const x=await r.json();document.getElementById('state').textContent=x.shard+' · '+x.state;
document.getElementById('bar').style.width=x.percent+'%';
document.getElementById('pct').textContent=x.percent+'%';
document.getElementById('counts').textContent=(x.shards_completed||0)+' / 12 shards · '+(x.unique_messages||0).toLocaleString()+' messages';
}catch(e){}}refresh();setInterval(refresh,2000);</script>"""


def run(args: argparse.Namespace) -> int:
    source = args.shards_dir.resolve()
    receipt = args.receipt.resolve()
    target = args.private_dir.resolve()
    if not source.is_dir() or not receipt.is_file() or source == target or source in target.parents:
        raise ValueError("SOURCE_OR_OUTPUT_PATH_HOLD")
    entries = qualified_receipt(receipt)
    if args.preflight_only:
        print(json.dumps({"state": "READ_ONLY_PREFLIGHT", "source_count": len(entries),
                          "originals_present": all((source / x["shard"]).is_file() for x in entries),
                          "output_exists": target.is_dir(), "no_write": True}))
        return 0
    if not target.is_dir() or target.is_symlink():
        raise ValueError("PREAPPROVED_PRIVATE_DIRECTORY_REQUIRED")
    # The caller must enforce owner-only Windows ACL before running.
    progress = target / "progress.json"
    con = connect(target / "semantic_review.sqlite")
    server = None
    if args.serve:
        token = secrets.token_urlsafe(32)
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                path = urllib.parse.urlsplit(self.path)
                if path.path == "/t/" + token:
                    payload = PAGE.encode("utf-8")
                    mime = "text/html; charset=utf-8"
                elif path.path == "/api" and hmac.compare_digest(
                        urllib.parse.parse_qs(path.query).get("token", [""])[0], token):
                    try:
                        payload = progress.read_bytes()
                    except OSError:
                        payload = b'{"state":"NOT_STARTED","percent":0}'
                    mime = "application/json"
                else:
                    self.send_error(403)
                    return
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Cache-Control", "no-store, private")
                self.send_header("Referrer-Policy", "no-referrer")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                self.wfile.write(payload)
            def log_message(self, *args):
                pass
        server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        (target / "Open Achilles source progress.url").write_text(
            "[InternetShortcut]\nURL=http://127.0.0.1:"
            + str(args.port) + "/t/" + token + "\n", encoding="utf-8")
        print("LOOPBACK_DASHBOARD_STARTED; owner-private .url file available", flush=True)
    try:
        for index, item in enumerate(entries, 1):
            name = item["shard"]
            current = summary(con)
            atomic_json(progress, {"schema": PROGRESS_SCHEMA, "shard": name,
                                   "state": "VERIFYING_OR_INGESTING",
                                   "percent": round(100 * current["shards"] / len(entries), 2),
                                   "shards_completed": current["shards"],
                                   "unique_messages": current["unique_messages"]})
            convs, nodes, _ = ingest_shard(con, source / name, item)
            state = "ALREADY_VERIFIED" if convs < 0 else "COMMITTED_VERIFIED_TEXT_R1"
            current = summary(con)
            atomic_json(progress, {"schema": PROGRESS_SCHEMA, "shard": name, "state": state,
                                   "percent": round(100 * current["shards"] / len(entries), 2),
                                   "shards_completed": current["shards"],
                                   "unique_messages": current["unique_messages"]})
            print(json.dumps({"shard": name, "state": state,
                              "shards_completed": current["shards"], "visible_messages": nodes}),
                  flush=True)
            if args.max_shards and index >= args.max_shards:
                break
        atomic_json(target / "summary.json", summary(con))
        print("SOURCE_R1_RECEIPT_WRITTEN_NO_NATIVE_ADMISSION", flush=True)
    except Exception as ex:
        atomic_json(progress, {"schema": PROGRESS_SCHEMA, "state": "HOLD",
                               "reason": str(ex)[:180], "percent": 0})
        raise
    finally:
        con.close()
    if server:
        print("Dashboard remains active until Ctrl+C; no background service installed.", flush=True)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            server.shutdown()
            server.server_close()
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--shards-dir", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--private-dir", type=Path, required=True)
    p.add_argument("--preflight-only", action="store_true")
    p.add_argument("--max-shards", type=int, default=0)
    p.add_argument("--serve", action="store_true")
    p.add_argument("--port", type=int, default=8767)
    return run(p.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
