"""Mutually pinned local process genesis read attestations: strict negative tests."""
import importlib.util
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from threading import Lock, Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import unittest
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location("cgx_genesis_peer_review", ROOT / "cgxGenesisPeerReview.py")
peer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(peer)
from cgxEmptyGenesisDevnet import initialise, read_state, CHAIN_ID


class MutualGenesisReviewTests(unittest.TestCase):
    def fixture(self, tmp: Path):
        a = tmp / "node_a" / "genesis.json"
        b = tmp / "node_b" / "genesis.json"
        initialise(a)
        initialise(b)
        client = peer.create_identity(tmp / "private", "review_node_a")
        server = peer.create_identity(tmp / "private", "review_node_b")
        key_a = peer.load_private(client["private_key_file"])
        key_b = peer.load_private(server["private_key_file"])
        return a, b, client, server, key_a, key_b

    def test_distinct_identities_same_genesis_mutual_pin(self):
        with TemporaryDirectory() as td:
            a, b, client, server, _, key_b = self.fixture(Path(td))
            self.assertNotEqual(client["public_key_hex"], server["public_key_hex"])
            srv = ThreadingHTTPServer(("127.0.0.1", 0), peer.make_handler(
                b, key_b, client["public_key_hex"]))
            worker = Thread(target=srv.serve_forever, daemon=True)
            worker.start()
            try:
                proof = peer.probe(a, Path(client["private_key_file"]),
                                   server["public_key_hex"], srv.server_address[1])
                self.assertEqual(proof["state"], "LOCAL_MUTUAL_PINNED_GENESIS_PROOF_ONLY")
                self.assertEqual(proof["genesis_sha256"], read_state(a)["genesis_sha256"])
                self.assertTrue(proof["verified_ed25519"])
                for field in ("independent_dbr", "issuer_verified", "mint_authorized",
                              "native_admission", "public_network"):
                    self.assertIs(proof[field], False, field)
                with self.assertRaisesRegex(ValueError, "RESPONSE_NOT_BOUND_TO_REQUEST|INVALID_PEER_SIGNATURE"):
                    request = peer.request_proof(proof["genesis_sha256"],
                                                 peer.load_private(client["private_key_file"]))
                    response = peer.build_reply(request, key_b, client["public_key_hex"],
                                                proof["genesis_sha256"], int(time.time()),
                                                set(), Lock())
                    peer.verify_reply(response, request, "0" * 64, int(time.time()))
            finally:
                srv.shutdown()
                srv.server_close()
                worker.join(timeout=3)

    def test_untrusted_client_and_mutation_endpoint_denied(self):
        with TemporaryDirectory() as td:
            a, b, client, server, _, key_b = self.fixture(Path(td))
            srv = ThreadingHTTPServer(("127.0.0.1", 0), peer.make_handler(
                b, key_b, client["public_key_hex"]))
            worker = Thread(target=srv.serve_forever, daemon=True)
            worker.start()
            base = f"http://127.0.0.1:{srv.server_address[1]}"
            try:
                rogue = peer.create_identity(Path(td) / "rogue", "review_node_a")
                with self.assertRaises(HTTPError) as ex:
                    peer.probe(a, Path(rogue["private_key_file"]),
                               server["public_key_hex"], srv.server_address[1])
                self.assertEqual(ex.exception.code, 403)
                for method in ("POST", "PUT", "DELETE", "PATCH"):
                    with self.assertRaises(HTTPError) as ex:
                        urlopen(Request(base + "/mint", data=b"{}", method=method), timeout=3)
                    self.assertEqual(ex.exception.code, 405)
                with self.assertRaises(HTTPError) as ex:
                    urlopen(base + "/private/source", timeout=3)
                self.assertEqual(ex.exception.code, 404)
            finally:
                srv.shutdown()
                srv.server_close()
                worker.join(timeout=3)

    def test_nonce_replay_and_short_lease_enforced(self):
        with TemporaryDirectory() as td:
            a, _, client, _, key_a, key_b = self.fixture(Path(td))
            genesis = read_state(a)["genesis_sha256"]
            request = peer.request_proof(genesis, key_a)
            seen = set()
            reply = peer.build_reply(request, key_b, client["public_key_hex"], genesis,
                                     int(time.time()), seen, Lock())
            self.assertEqual(reply["scope"], "genesis.readonly")
            self.assertLessEqual(reply["expires_at"] - reply["issued_at"], 20)
            self.assertIs(reply["mint_authorized"], False)
            with self.assertRaisesRegex(ValueError, "NONCE_REPLAY_HOLD"):
                peer.build_reply(request, key_b, client["public_key_hex"], genesis,
                                 int(time.time()), seen, Lock())
            request["issued_at"] -= 300
            request["expires_at"] -= 300
            request["signature"] = peer._sign({k: v for k, v in request.items() if k != "signature"}, key_a)
            with self.assertRaisesRegex(ValueError, "CHALLENGE_EXPIRED"):
                peer.build_reply(request, key_b, client["public_key_hex"], genesis,
                                 int(time.time()), set(), Lock())

    def test_genesis_tamper_scope_and_authority_escalation_denied(self):
        with TemporaryDirectory() as td:
            a, _, client, server, key_a, key_b = self.fixture(Path(td))
            hash_ = read_state(a)["genesis_sha256"]
            q = peer.request_proof(hash_, key_a)
            signed = peer.build_reply(q, key_b, client["public_key_hex"],
                                      hash_, int(time.time()), set(), Lock())
            for field in ("native_dbr_verified", "signed_root_authority", "mint_authorized",
                          "consensus_verified"):
                response = dict(signed)
                response[field] = True
                # Even a correctly signed response cannot convert a review proof to authority.
                response["signature"] = peer._sign(
                    {k: v for k, v in response.items() if k != "signature"}, key_b)
                with self.subTest(field=field), self.assertRaisesRegex(ValueError, "REVIEW_AUTHORITY"):
                    peer.verify_reply(response, q, server["public_key_hex"], int(time.time()))
            altered = dict(q)
            altered["scope"] = "mint"
            altered["signature"] = peer._sign(
                {k: v for k, v in altered.items() if k != "signature"}, key_a)
            with self.assertRaisesRegex(ValueError, "REQUEST_CHAIN_OR_SCOPE"):
                peer.build_reply(altered, key_b, client["public_key_hex"],
                                 hash_, int(time.time()), set(), Lock())
            with self.assertRaisesRegex(ValueError, "GENESIS_PIN_MISMATCH"):
                peer.build_reply(q, key_b, client["public_key_hex"],
                                 "f" * 64, int(time.time()), set(), Lock())

    def test_no_key_overwrite_and_bad_identity_pin(self):
        with TemporaryDirectory() as td:
            folder = Path(td)
            a = peer.create_identity(folder, "review_node_a")
            before = Path(a["private_key_file"]).read_bytes()
            with self.assertRaisesRegex(ValueError, "IDENTITY_EXISTS"):
                peer.create_identity(folder, "review_node_a")
            self.assertEqual(before, Path(a["private_key_file"]).read_bytes())
            with self.assertRaisesRegex(ValueError, "PEER_PUBLIC_KEY_PIN_INVALID"):
                peer._parse_pin("NotAKey")
            with self.assertRaisesRegex(ValueError, "PEER_PUBLIC_KEY_PIN_INVALID"):
                peer._parse_pin(None)

    def test_signed_reply_does_not_confirm_an_independent_dbr(self):
        with TemporaryDirectory() as td:
            a, _, client, server, key_a, key_b = self.fixture(Path(td))
            request = peer.request_proof(read_state(a)["genesis_sha256"], key_a)
            reply = peer.build_reply(request, key_b, client["public_key_hex"],
                                     read_state(a)["genesis_sha256"], int(time.time()),
                                     set(), Lock())
            result = peer.verify_reply(reply, request, server["public_key_hex"], int(time.time()))
            self.assertFalse(result["independent_dbr"])
            self.assertFalse(result["native_admission"])
            self.assertFalse(result["public_network"])
            self.assertEqual(result["chain_id"], CHAIN_ID)
            self.assertNotIn(client["private_key_file"], json.dumps(result))


if __name__ == "__main__":
    unittest.main()
