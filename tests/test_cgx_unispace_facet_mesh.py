from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "tools/cgx_unispace_facet_mesh.py"
spec = importlib.util.spec_from_file_location("cgx_unispace_facet_mesh", SCRIPT)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fixture_repo(tmp_path: Path):
    repo = tmp_path / "repo"
    path = repo / "cgx/domain_templates"
    path.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    keys = {key for space in m.FACETS.values() for key in space["contracts"]}
    names = {key: key + "_contract.json" for key in keys}
    manifest = {"schema": "CGX-DOMAIN-TEMPLATES/0.4",
                "parent_filespace": {"file": "Cognigrex.cgx"},
                "shared_contracts": names}
    service_ids = {key for space in m.FACETS.values() for key in space["services"]}
    topology = {"schema": "CGX-COGNIGREX-PARENT-TOPOLOGY/0.2",
                "root": {"file": "Cognigrex.cgx"},
                "shared_root_services": [
                    {"id": key, "location": "Cognigrex.cgx:/" + key}
                    for key in sorted(service_ids)]}
    (path / "domains.json").write_text(json.dumps(manifest), encoding="utf-8")
    (path / "cognigrex_parent_topology.json").write_text(
        json.dumps(topology), encoding="utf-8")
    for key, name in names.items():
        (path / name).write_text(json.dumps({"schema": "test-contract/0.1", "id": key}),
                                 encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True,
                   capture_output=True)
    return repo, path


def test_five_facets_one_root_and_source_qualified(tmp_path):
    repo, path = fixture_repo(tmp_path)
    a = m.build_unispace_facet_mesh(repo)
    b = m.build_unispace_facet_mesh(repo)
    assert a == b
    assert a["schema"] == m.SCHEMA
    assert a["state"] == "SOURCE_CONTRACT_MESH_OBSERVED"
    assert a["canonical_root_id"] == "cgx:root:cognigrex"
    assert a["canonical_carrier"] == "Cognigrex.cgx"
    assert a["facet_count"] == 5
    assert {x["id"] for x in a["facets"]} == set(m.FACETS)
    assert a["unique_contract_count"] < sum(len(x["contracts"])
                                              for x in m.FACETS.values())
    assert a["unique_contract_count"] == len(a["unique_contracts"])
    assert len({c["sha256"] for c in a["unique_contracts"]}) == a["unique_contract_count"]
    assert all(f["canonical_root_ref"] == "cgx:root:cognigrex"
               and f["storage_policy"] == "REFERENCE_EXISTING_ROOT_ONLY"
               and f["state"] == "SOURCE_CONTRACTS_PRESENT"
               and not f["execution_authorized"]
               and not f["runtime_engine_attached"]
               for f in a["facets"])
    assert not a["new_root_created"]
    assert not a["new_database_created"]
    assert not a["native_execution_authorized"]
    assert not a["mint_or_network_authorized"]
    assert not a["model_weights_modified"]
    assert all(p.is_file() for p in path.glob("*.json"))


def test_cross_space_reuses_shared_contract_and_services(tmp_path):
    repo, _ = fixture_repo(tmp_path)
    mesh = m.build_unispace_facet_mesh(repo)
    out = m.plan_facet_projection(mesh,
                                  ["social_space", "file_space", "social_space", "data_space"])
    assert out["requested_spaces"] == ["data_space", "file_space", "social_space"]
    assert out["state"] == "SOURCE_PROJECTION_READY_FOR_REVIEW"
    assert len({x["contract_id"] for x in out["contract_refs"]}) == len(out["contract_refs"])
    assert len(out["contract_refs"]) == 6
    agent = next(x for x in out["service_users"] if x["service_id"] == "agents")
    assert agent["spaces"] == ["social_space"]
    assert out["single_runtime_requirement"] is True
    assert not out["owner_action_taken"]
    assert not out["model_inference_executed"]
    assert not out["semantic_state_mutated"]
    assert out == m.plan_facet_projection(mesh, reversed(out["requested_spaces"]))


def test_missing_contract_is_held_without_downgrading_other_facets(tmp_path):
    repo, folder = fixture_repo(tmp_path)
    (folder / "node_exchange_contract.json").unlink()
    mesh = m.build_unispace_facet_mesh(repo)
    assert mesh["state"] == "HOLD_SOURCE_GAPS"
    states = {f["id"]: f["state"] for f in mesh["facets"]}
    assert states["data_space"] == "HOLD_SOURCE_GAPS"
    assert states["file_space"] == "SOURCE_CONTRACTS_PRESENT"
    out = m.plan_facet_projection(mesh, ["file_space", "data_space"])
    assert out["state"] == "HOLD_MISSING_CONTRACTS"
    assert out["held_spaces"] == ["data_space"]
    assert not out["native_approval"]


def test_untracked_contract_is_held(tmp_path):
    repo, folder = fixture_repo(tmp_path)
    (folder / "node_exchange_contract.json").unlink()
    (folder / "node_exchange_contract.json").write_text("{}", encoding="utf-8")
    tracked = m._tracked_paths(repo)
    tracked.remove("cgx/domain_templates/node_exchange_contract.json")
    mesh = m.build_unispace_facet_mesh(repo, tracked)
    assert mesh["state"] == "HOLD_SOURCE_GAPS"
    assert "cgx/domain_templates/node_exchange_contract.json" in next(
        f for f in mesh["facets"] if f["id"] == "data_space")["missing_contract_paths"]


def test_duplicate_parent_service_rejected(tmp_path):
    repo, folder = fixture_repo(tmp_path)
    path = folder / "cognigrex_parent_topology.json"
    obj = json.loads(path.read_text(encoding="utf-8"))
    obj["shared_root_services"].append(obj["shared_root_services"][0])
    path.write_text(json.dumps(obj), encoding="utf-8")
    with pytest.raises(m.FacetHold, match="duplicate parent service"):
        m.build_unispace_facet_mesh(repo)


def test_parent_traversal_contract_rejected(tmp_path):
    repo, folder = fixture_repo(tmp_path)
    path = folder / "domains.json"
    obj = json.loads(path.read_text(encoding="utf-8"))
    obj["shared_contracts"]["node_exchange"] = "../../private.json"
    path.write_text(json.dumps(obj), encoding="utf-8")
    with pytest.raises(m.FacetHold, match="violates parent namespace"):
        m.build_unispace_facet_mesh(repo)


def test_missing_parent_returns_hold_with_no_facets_or_authority(tmp_path):
    repo, folder = fixture_repo(tmp_path)
    (folder / "domains.json").unlink()
    result = m.build_unispace_facet_mesh(repo)
    assert result["state"] == "HOLD_PARENT_UNAVAILABLE"
    assert result["facets"] == []
    assert not result["native_execution_authorized"]
    assert not result["mint_or_network_authorized"]
    with pytest.raises(m.FacetHold, match="requested facet unavailable"):
        m.plan_facet_projection(result, ["file_space"])


@pytest.mark.parametrize("operation", ["execute", "mint", "delete", "publish", "train", "dispatch"])
def test_mutation_requests_rejected(tmp_path, operation):
    repo, _ = fixture_repo(tmp_path)
    with pytest.raises(m.FacetHold, match="source-only"):
        m.plan_facet_projection(m.build_unispace_facet_mesh(repo), ["file_space"], operation)


def test_unknown_unbounded_empty_spaces_fail_closed(tmp_path):
    repo, _ = fixture_repo(tmp_path)
    mesh = m.build_unispace_facet_mesh(repo)
    for value in ([], ["unknown_space"], ["data_space"] * 21):
        with pytest.raises(m.FacetHold):
            m.plan_facet_projection(mesh, value)


def test_projection_detects_conflicting_shared_contract_source(tmp_path):
    repo, _ = fixture_repo(tmp_path)
    mesh = m.build_unispace_facet_mesh(repo)
    other = next(f for f in mesh["facets"] if f["id"] == "social_space")
    ref = next(c for c in other["contract_bindings"]
               if c["contract_id"] == "source_envelope")
    ref["sha256"] = "0" * 64
    with pytest.raises(m.FacetHold, match="conflicting shared contract"):
        m.plan_facet_projection(mesh, ["social_space", "file_space"])


def test_tampered_contract_readiness_never_promotes_source_hold(tmp_path):
    repo, _ = fixture_repo(tmp_path)
    mesh = m.build_unispace_facet_mesh(repo)
    bound = next(f for f in mesh["facets"] if f["id"] == "data_space")
    bound["contract_bindings"][0]["state"] = "HOLD_SOURCE_UNAVAILABLE"
    assert bound["state"] == "SOURCE_CONTRACTS_PRESENT"
    planned = m.plan_facet_projection(mesh, ["data_space"])
    assert planned["state"] == "HOLD_MISSING_CONTRACTS"
    assert planned["held_spaces"] == ["data_space"]
    assert planned["native_approval"] is False
