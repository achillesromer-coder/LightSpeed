"""Bounded signed peer review contract tests; test keys and stores are temporary."""
from __future__ import annotations
import json
import sqlite3
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lightspeed_runtime.operational_store import OperationalStore
from lightspeed_runtime.cgx_signed_peer_review import (
    GENESIS, PeerReviewError, accept_review, digest, export_public_key, sign_review
)

T = datetime(2026, 11, 28, 6, 0, tzinfo=UTC)
SUBJECT = "a" * 64


def fixture_keys():
    a = Ed25519PrivateKey.generate()
    b = Ed25519PrivateKey.generate()
    return a, b, {"peer-a": export_public_key(a), "peer-b": export_public_key(b)}


def packet(key, origin="peer-a", recipient="peer-b", seq=1, predecessor=GENESIS,
           now=T, subject=SUBJECT):
    return sign_review(key, origin=origin, recipient=recipient,
                       sequence=seq, predecessor_sha256=predecessor,
                       subject_sha256=subject, now=now)


def test_two_independent_ledgers_and_verified_bidirectional_readback(tmp_path):
    a, b, trust = fixture_keys()
    store_a = OperationalStore(tmp_path / "a"/"lightspeed_unified.db")
    store_b = OperationalStore(tmp_path / "b"/"lightspeed_unified.db")
    first = packet(a)
    accepted = accept_review(store_b,first,recipient="peer-b",trust=trust,now=T)
    assert accepted["signed_test_key_authenticated"]
    assert accepted["native_admitted"] is False
    assert accepted["live_network_transport_verified"] is False
    assert accepted["independent_machine_operators_verified"] is False
    assert accepted["native_dbr_signed"] is False
    # A and B have independently persisted receipt records.
    response=packet(b,origin="peer-b",recipient="peer-a")
    result=accept_review(store_a,response,recipient="peer-a",trust=trust,now=T)
    assert result["sequence"]==1
    # Independently recover peer B receipt from a new OperationalStore instance.
    follow=packet(a,seq=2,predecessor=digest(first))
    after=accept_review(OperationalStore(store_b.path),follow,recipient="peer-b",trust=trust,now=T)
    assert after["sequence"]==2
    with sqlite3.connect(store_b.path) as c:
        n=c.execute("SELECT count(*) FROM operational_events WHERE kind=?",
                    ("cgx_signed_peer_review_v01",)).fetchone()[0]
        assert n==2
        contents="".join(x[0] for x in c.execute(
            "SELECT payload_json FROM operational_events WHERE kind='cgx_signed_peer_review_v01'"))
    assert "PRIVATE KEY" not in contents
    assert "source_bytes" not in contents or '"source_bytes_included":false' in contents.lower()


def test_replay_and_conflicting_fork_refused(tmp_path):
    a,b,trust=fixture_keys()
    store=OperationalStore(tmp_path/"ledger.db")
    first=packet(a)
    accept_review(store,first,recipient="peer-b",trust=trust,now=T)
    with pytest.raises(PeerReviewError,match="replayed"):
        accept_review(store,first,recipient="peer-b",trust=trust,now=T)
    conflicting=packet(a,subject="b"*64)
    with pytest.raises(PeerReviewError,match="replayed"):
        accept_review(store,conflicting,recipient="peer-b",trust=trust,now=T)


def test_missing_sequence_and_bad_predecessor_refused(tmp_path):
    a,b,trust=fixture_keys()
    store=OperationalStore(tmp_path/"ledger.db")
    second=packet(a,seq=2,predecessor="a"*64)
    with pytest.raises(PeerReviewError,match="previous"):
        accept_review(store,second,recipient="peer-b",trust=trust,now=T)
    first=packet(a)
    accept_review(store,first,recipient="peer-b",trust=trust,now=T)
    with pytest.raises(PeerReviewError,match="previous"):
        accept_review(store,second,recipient="peer-b",trust=trust,now=T)


@pytest.mark.parametrize("field,value,expected",[
    ("source_rights","PUBLIC","rights"),
    ("execution_authorised",True,"authority"),
    ("native_admitted",True,"authority"),
    ("signed_dbr",True,"authority"),
    ("source_bytes_included",True,"authority"),
    ("predecessor_sha256","a"*64,"genesis"),
])
def test_untrusted_scope_never_grants_execution(tmp_path,field,value,expected):
    a,b,trust=fixture_keys()
    message=packet(a)
    message["body"][field]=value
    message["signature_ed25519"]=a.sign(json.dumps(
        message["body"],sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hex()
    with pytest.raises(PeerReviewError,match=expected):
        accept_review(OperationalStore(tmp_path/"ledger.db"),message,
                      recipient="peer-b",trust=trust,now=T)


def test_signature_substitution_untrusted_identity_wrong_recipient(tmp_path):
    a,b,trust=fixture_keys()
    message=packet(a)
    with pytest.raises(PeerReviewError,match="not explicitly trusted"):
        accept_review(OperationalStore(tmp_path/"u.db"),message,
                      recipient="peer-b",trust={"peer-b":trust["peer-b"]},now=T)
    with pytest.raises(PeerReviewError,match="recipient"):
        accept_review(OperationalStore(tmp_path/"w.db"),message,
                      recipient="peer-a",trust=trust,now=T)
    wrong=dict(message,signature_ed25519=b.sign(b"made up payload").hex())
    with pytest.raises(PeerReviewError,match="signature"):
        accept_review(OperationalStore(tmp_path/"s.db"),wrong,
                      recipient="peer-b",trust=trust,now=T)


def test_tamper_expiry_future_and_unknown_field_refused(tmp_path):
    a,b,trust=fixture_keys()
    original=packet(a)
    modified=json.loads(json.dumps(original))
    modified["body"]["subject_sha256"]="b"*64
    with pytest.raises(PeerReviewError,match="signature"):
        accept_review(OperationalStore(tmp_path/"t.db"),modified,
                      recipient="peer-b",trust=trust,now=T)
    with pytest.raises(PeerReviewError,match="expired"):
        accept_review(OperationalStore(tmp_path/"e.db"),original,
                      recipient="peer-b",trust=trust,now=T+timedelta(minutes=4))
    with pytest.raises(PeerReviewError,match="future"):
        accept_review(OperationalStore(tmp_path/"f.db"),original,
                      recipient="peer-b",trust=trust,now=T-timedelta(minutes=1))
    modified=json.loads(json.dumps(original))
    modified["body"]["data_dump"]="private"
    with pytest.raises(PeerReviewError,match="schema"):
        accept_review(OperationalStore(tmp_path/"s.db"),modified,
                      recipient="peer-b",trust=trust,now=T)


def _loopback_server(store,trust,clock):
    """Test-only localhost transport, never a production daemon or listener."""
    import socketserver
    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            raw=self.rfile.readline(4097)
            if len(raw)>4096 or not raw.endswith(b"\n"):
                self.wfile.write(b'{"error":"FRAME_BOUND"}\n')
                return
            try:
                message=json.loads(raw)
                out=accept_review(store,message,recipient="peer-b",trust=trust,now=clock)
                reply={"status":"REVIEW_ONLY","receipt_sha256":out["packet_sha256"],
                       "native_admitted":False,"network_identity_issued":False}
            except (PeerReviewError,ValueError,TypeError):
                reply={"error":"UNTRUSTED_PACKET_REJECTED"}
            self.wfile.write(json.dumps(reply,sort_keys=True).encode()+b"\n")
    class LocalServer(socketserver.TCPServer):
        allow_reuse_address=False
    return LocalServer(("127.0.0.1",0),Handler)


def test_real_loopback_transport_roundtrip_with_persistent_receiver(tmp_path):
    import socket,threading
    a,b,trust=fixture_keys()
    store=OperationalStore(tmp_path/"receiver.db")
    messages=[packet(a),None]
    messages[1]=packet(a,seq=2,predecessor=digest(messages[0]))
    with _loopback_server(store,trust,T) as server:
        assert server.server_address[0]=="127.0.0.1"
        t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
        for msg in messages:
            with socket.create_connection(server.server_address,timeout=2) as sock:
                sock.sendall(json.dumps(msg).encode()+b"\n")
                with sock.makefile("rb") as reader:
                    response=json.loads(reader.readline())
            assert response["status"]=="REVIEW_ONLY"
            assert response["receipt_sha256"]==digest(msg)
            assert response["native_admitted"] is False
        server.shutdown();t.join(timeout=3)
    with sqlite3.connect(store.path) as conn:
        count=conn.execute("select count(*) from operational_events where kind=?",
                           ("cgx_signed_peer_review_v01",)).fetchone()[0]
    assert count==2


def test_loopback_transport_rejects_modified_and_replayed_messages(tmp_path):
    import socket,threading
    a,b,trust=fixture_keys()
    store=OperationalStore(tmp_path/"receiver.db")
    original=packet(a)
    tampered=json.loads(json.dumps(original))
    tampered["body"]["subject_sha256"]="c"*64
    with _loopback_server(store,trust,T) as server:
        t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
        def send(msg):
            with socket.create_connection(server.server_address,timeout=2) as sock:
                sock.sendall(json.dumps(msg).encode()+b"\n")
                with sock.makefile("rb") as reader:
                    return json.loads(reader.readline())
        assert send(tampered)=={"error":"UNTRUSTED_PACKET_REJECTED"}
        assert send(original)["status"]=="REVIEW_ONLY"
        assert send(original)=={"error":"UNTRUSTED_PACKET_REJECTED"}
        server.shutdown();t.join(timeout=3)
