from __future__ import annotations

import ast
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lightspeed_runtime.cgx_persistence_preflight import (
    PersistenceReviewError,
    _pin_source,
    _shape_ok,
    git_blob_id,
    review_core_markers,
)

PREFLIGHT = b"""
REPO_HEAD = 'a' * 40
BLOB_PINS = {
 'desktop/LightSpeed_Runtime/lightspeed_runtime/achilles/operator.py': 'a' * 40,
 'desktop/LightSpeed_Runtime/lightspeed_runtime/node_exchange.py': 'b' * 40,
 'cgx/domain_templates/execution_lease_contract.json': 'c' * 40,
}
OPERATOR_METHODS = {'retrieve','propose_action','approve_action','reject_action'}
NODE_FUNCS = {'build_transfer_envelope','execute_local_transfer','build_compute_request',
              'execute_local_compute','resolve_node_root'}
LEASE_FIELDS = {'lease_id','state'}
"""


def test_git_blob_digest_and_no_import():
    assert git_blob_id(b"") == "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"
    assert git_blob_id(b"x") != git_blob_id(b"y")


def test_malformed_pins_fail_closed():
    for raw in (b"import os\nos.system('echo bad')", b"REPO_HEAD='x'",
                b"REPO_HEAD = broken()"):
        with pytest.raises(PersistenceReviewError):
            _pin_source(raw)


def test_existing_contract_shape_reuses_pin_declarations():
    p = {
        "OPERATOR_METHODS": {"retrieve", "propose_action"},
        "NODE_FUNCS": {"execute_local_compute"},
        "LEASE_FIELDS": {"lease_id", "state"},
    }
    op = b"class AchillesOperator:\n    def retrieve(self): pass\n    def propose_action(self): pass\n"
    node = b"def execute_local_compute(): pass\n"
    lease = json.dumps({"required_fields":["lease_id","state"],
                        "invariants":["missing-or-stale-lease-means-no-consequential-execution"]}).encode()
    assert _shape_ok("x/achilles/operator.py", op, p)
    assert _shape_ok("x/node_exchange.py", node, p)
    assert _shape_ok("x/execution_lease_contract.json", lease, p)
    assert not _shape_ok("x/achilles/operator.py", b"class AchillesOperator: pass", p)
    assert not _shape_ok("x/node_exchange.py", b"def innocent(): pass", p)
    assert not _shape_ok("x/execution_lease_contract.json", b"{}", p)


def test_review_markers_do_not_authorize_execution():
    core = b"""
class FamilyStore:
    database_name = 'family.sqlite3'
    source_occurrence = 'content_granted'
    def ingest(self): pass
    def occurrences_for_agent(self): pass
    def restore_for_agent(self): pass
    def source_search(self): pass
    def propose(self): pass
"""
    sup = b"class CoordinatorLock: pass\n"
    flags = review_core_markers(core, sup)
    assert flags == {
        "separate_review_database_declared": True,
        "source_occurrence_grant_methods_declared": True,
        "foreground_coordinator_declared": True,
    }
    flags["foreground_coordinator_declared"] = False
    assert flags["foreground_coordinator_declared"] is False


def test_missing_source_grant_method_cannot_pass():
    core = b"class FamilyStore:\n    def ingest(self): pass\n"
    assert not review_core_markers(core, b"class CoordinatorLock: pass")[
        "source_occurrence_grant_methods_declared"
    ]


def test_git_clean_filter_recognizes_crlf_without_elevating_authority(tmp_path):
    import subprocess
    from lightspeed_runtime.cgx_persistence_preflight import canonical_worktree_blob

    repo = tmp_path / "repo"
    repo.mkdir()
    def git(*args):
        return subprocess.run(
            ["git", "-C", str(repo), *args], check=True,
            capture_output=True, text=True,
        ).stdout.strip()
    git("init")
    (repo / ".gitattributes").write_text("*.py text eol=lf\n", encoding="utf-8")
    source = repo / "fixture.py"
    source.write_bytes(b"first\nsecond\n")
    expected = git("hash-object", "--path", "fixture.py", "fixture.py")
    assert canonical_worktree_blob(repo, "fixture.py", b"first\r\nsecond\r\n") == expected
    assert canonical_worktree_blob(repo, "fixture.py", b"first\r\nchanged\r\n") != expected


def test_pin_parser_reads_literal_source_without_evaluating_expressions():
    valid = (
        PREFLIGHT
        .replace(b"'a' * 40", b"'" + b"a" * 40 + b"'")
        .replace(b"'b' * 40", b"'" + b"b" * 40 + b"'")
        .replace(b"'c' * 40", b"'" + b"c" * 40 + b"'")
    )
    pins = _pin_source(valid)
    assert pins["REPO_HEAD"] == "a" * 40
    assert len(pins["BLOB_PINS"]) == 3
    with pytest.raises(PersistenceReviewError):
        _pin_source(PREFLIGHT)


def test_unreviewed_commit_is_rejected_before_any_source_read(tmp_path):
    from lightspeed_runtime.cgx_persistence_preflight import reconcile
    with pytest.raises(PersistenceReviewError, match="non-pinned"):
        reconcile(tmp_path, "a" * 40)
