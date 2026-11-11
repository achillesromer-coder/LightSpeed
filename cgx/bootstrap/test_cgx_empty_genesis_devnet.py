"""Positive and adversarial checks for the non-issuing local-only genesis."""
import importlib.util
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import unittest

SCRIPT = Path(__file__).with_name("cgxEmptyGenesisDevnet.py")
SPEC = importlib.util.spec_from_file_location("empty_local_cgx", SCRIPT)
CGX = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CGX)


class EmptyGenesisTests(unittest.TestCase):
    def test_deterministic_zero_transactions_no_issuer_and_single_root(self):
        a = CGX.genesis_record()
        self.assertEqual(a, CGX.genesis_record())
        self.assertEqual(CGX.validate_record(a), a)
        block = a["genesis"]
        for key in ("object_count", "transaction_count", "minted_count", "account_count"):
            self.assertEqual(block[key], 0)
        for key in ("signed_root_authority", "independent_dbr", "source_rights_verified",
                    "native_admission", "public_network", "may_mint", "may_sign",
                    "may_submit_transactions"):
            self.assertIs(block[key], False)
        self.assertEqual(block["parent"], "cgx:root:cognigrex")

    def test_exclusive_genesis_init_does_not_overwrite(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "local" / "genesis.json"
            a = CGX.initialise(path)
            self.assertEqual(CGX.read_state(path), a)
            before = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "ALREADY_EXISTS"):
                CGX.initialise(path)
            self.assertEqual(path.read_bytes(), before)

    def test_tampered_digest_or_nonempty_record_never_passes(self):
        for edit in (
            lambda j: j.__setitem__("genesis_sha256", "0" * 64),
            lambda j: j["genesis"].__setitem__("minted_count", 1),
            lambda j: j["genesis"].__setitem__("independent_dbr", True),
            lambda j: j["genesis"].__setitem__("signed_root_authority", True),
            lambda j: j["genesis"].__setitem__("parent", "cgx:root:duplicate"),
            lambda j: j["genesis"].__setitem__("consensus", "BFT_VERIFIED"),
            lambda j: j["genesis"].__setitem__("public_network", True),
        ):
            with TemporaryDirectory() as tmp:
                path = Path(tmp) / "genesis.json"
                CGX.initialise(path)
                j = json.loads(path.read_text())
                edit(j)
                path.write_text(json.dumps(j), encoding="utf-8")
                with self.assertRaises(ValueError):
                    CGX.read_state(path)

    def test_missing_or_malformed_state_fails(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "genesis.json"
            with self.assertRaisesRegex(ValueError, "MISSING"):
                CGX.read_state(path)
            path.write_text("{not-json")
            with self.assertRaisesRegex(ValueError, "GENESIS_JSON_INVALID"):
                CGX.read_state(path)

    def test_readonly_loopback_http_and_mutation_denials(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "genesis.json"
            CGX.initialise(path)
            srv = ThreadingHTTPServer(("127.0.0.1", 0), CGX.make_handler(path))
            thread = Thread(target=srv.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{srv.server_address[1]}"
            try:
                for suffix in ("/health", "/status", "/genesis"):
                    with urlopen(base + suffix, timeout=3) as response:
                        self.assertEqual(response.status, 200)
                        payload = json.loads(response.read())
                        self.assertNotIn(str(path), json.dumps(payload))
                        self.assertNotIn("private", json.dumps(payload).lower())
                        self.assertEqual(response.headers.get("Cache-Control"), "no-store")
                with urlopen(base + "/status", timeout=3) as response:
                    status = json.loads(response.read())
                    self.assertEqual(status["height"], 0)
                    self.assertFalse(status["native_mint"])
                    self.assertFalse(status["authenticated_two_node_dbr"])
                for method in ("POST", "PUT", "DELETE", "PATCH"):
                    with self.assertRaises(HTTPError) as err:
                        urlopen(Request(base + "/mint", method=method, data=b"{}"), timeout=3)
                    self.assertEqual(err.exception.code, 405)
                with self.assertRaises(HTTPError) as err:
                    urlopen(base + "/api/private/source?token=secret", timeout=3)
                self.assertEqual(err.exception.code, 404)
                j = json.loads(path.read_text())
                j["genesis"]["object_count"] = 1
                path.write_text(json.dumps(j), encoding="utf-8")
                with self.assertRaises(HTTPError) as err:
                    urlopen(base + "/status", timeout=3)
                self.assertEqual(err.exception.code, 503)
            finally:
                srv.shutdown()
                srv.server_close()
                thread.join(timeout=3)

    def test_readonly_service_rejects_invalid_public_port(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "genesis.json"
            CGX.initialise(path)
            with self.assertRaisesRegex(ValueError, "INVALID_LOCAL_DEVNET_PORT"):
                CGX.serve(path, 80)
            with self.assertRaisesRegex(ValueError, "INVALID_LOCAL_DEVNET_PORT"):
                CGX.serve(path, 70000)


if __name__ == "__main__":
    unittest.main()
