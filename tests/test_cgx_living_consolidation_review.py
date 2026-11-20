from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/cgx_living_consolidation_review.py"


def load_module():
    name = "cgx_living_consolidation_review_test"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def fixture_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main", str(repo)], check=True,
                   capture_output=True)
    files = {
        "pkg/__init__.py": b"",
        "physics/raphael/geometry.py": b"",
        "spare/empty.dat": b"",
        "pkg/actual.py": b"meaningful",
    }
    for rel, data in files.items():
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    subprocess.run(["git", "-C", str(repo), "add", "."],
                   check=True, capture_output=True)
    return repo


def test_one_source_and_no_deletions(tmp_path):
    module = load_module()
    repo = fixture_repo(tmp_path)
    carriers = tmp_path / "carrier"
    carriers.mkdir()
    (carriers / "LS.cgx").write_bytes(b"same")
    (carriers / "LightSpeed.cgx").write_bytes(b"same")
    (carriers / "Romer.cgx").write_bytes(b"other")
    before = {x.relative_to(repo).as_posix(): x.read_bytes()
              for x in repo.rglob("*") if x.is_file() and ".git" not in x.parts}
    result = module.build_living_consolidation_review(repo, carriers)
    assert result["schema"] == "CGX-LIVING-CONSOLIDATION-REVIEW/0.1"
    assert result["tracked_source_count"] == 4
    assert result["tracked_zero_byte_count"] == 3
    assert result["retained_zero_by_kind"] == {
        "RETAIN_PYTHON_PACKAGE_MARKER": 1,
        "RETAIN_UNVERIFIED_RESEARCH_SCAFFOLD": 1,
        "RETAIN_UNRESOLVED_ZERO_BYTE_ASSET": 1,
    }
    assert result["unique_carrier_hash_count"] == 2
    assert result["collapsed_display_aliases"] == 1
    assert len(result["one_card_per_unique_content"]) == 2
    assert not result["file_deletion_performed"]
    assert not result["source_modification_performed"]
    assert result["safe_delete_candidates"] == []
    assert all(not row["deletion_eligible"] for row in result["retained_zero_byte_source"])
    after = {x.relative_to(repo).as_posix(): x.read_bytes()
             for x in repo.rglob("*") if x.is_file() and ".git" not in x.parts}
    assert before == after
    assert result == module.build_living_consolidation_review(repo, carriers)


def test_empty_cgx_carrier_is_held_not_erased(tmp_path):
    module = load_module()
    repo = fixture_repo(tmp_path)
    carriers = tmp_path / "carrier"
    carriers.mkdir()
    empty = carriers / "UNVERIFIED.cgx"
    empty.write_bytes(b"")
    result = module.build_living_consolidation_review(repo, carriers)
    assert result["zero_byte_carrier_holds"] == ["UNVERIFIED.cgx"]
    assert empty.exists()
    assert result["safe_delete_candidates"] == []
    assert not result["native_mint_performed"]


def test_git_scope_failure_denies_review(tmp_path):
    import pytest
    module = load_module()
    root = tmp_path / "not-a-repo"
    root.mkdir()
    with pytest.raises(ValueError, match="tracked Git scope unavailable"):
        module.build_living_consolidation_review(root, tmp_path)


def test_digital_twin_source_layer_linkage_and_hash_preservation(tmp_path):
    import json
    import hashlib
    module = load_module()
    repo = fixture_repo(tmp_path)
    twin = "test_twin"
    manifest = {
        "schema": "achilles_complete_digital_asset_bundle_v1",
        "assets": [{
            "twin_id": twin, "asset_id": "test_twin.viewer_mesh.v1",
            "file": f"assets/models/{twin}.obj",
            "representation_class": "INTERACTION_PROXY",
        }],
    }
    references = {
        "data/digital-twin/complete_digital_asset_manifest_2026-09-12.json":
            json.dumps(manifest).encode("utf-8"),
        "assets/models/test_twin.obj": b"v 0 0 0\n",
        "assets/previews/test_twin_six_view.png": b"synthetic preview",
    }
    references.update({
        f"assets/type1-svg/{twin}/T1-{i:02d}.svg":
            b"<svg>synthetic</svg>" for i in range(8)
    })
    for relative, data in references.items():
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True, capture_output=True)
    source = module.review_digital_twin_assets(repo, module._tracked(repo))
    assert source["state"] == "OBSERVED_READ_ONLY"
    assert source["asset_family_count"] == 1
    assert source["layer_path_count"] == 10
    assert source["observed_layer_count"] == 10
    assert source["linked_assets"][0]["representation_class"] == "INTERACTION_PROXY"
    assert source["duplicate_byte_groups"]
    assert source["linked_assets"][0]["native_mesh_verified"] is False
    assert source["linked_assets"][0]["fabrication_authorized"] is False
    assert source["linked_assets"][0]["licence_verified"] is False
    assert source["linked_files_are_source_proxies_only"]
    assert source["deletion_authorized"] is False
    assert source["linked_assets"][0]["files"][0]["sha256"] == hashlib.sha256(
        b"v 0 0 0\n").hexdigest()
    assert source == module.review_digital_twin_assets(repo, module._tracked(repo))


def test_digital_twin_missing_preview_is_visible_not_minted(tmp_path):
    import json
    module = load_module()
    repo = fixture_repo(tmp_path)
    path = repo / "data/digital-twin/complete_digital_asset_manifest_2026-09-12.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "schema": "achilles_complete_digital_asset_bundle_v1",
        "assets": [{
            "twin_id": "project1", "asset_id": "proj1",
            "file": "assets/models/project1.obj",
            "representation_class": "INTERACTION_PROXY",
        }]
    }), encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True, capture_output=True)
    result = module.review_digital_twin_assets(repo, module._tracked(repo))
    assert result["state"] == "HOLD_ASSET_GAPS"
    assert result["layer_path_count"] == 10
    assert result["observed_layer_count"] == 0
    assert len(result["missing_asset_paths"]) == 10
    assert not result["promotion_authorized"]


def test_digital_twin_rejects_duplicate_and_escaping_identity(tmp_path):
    import json
    import pytest
    module = load_module()
    repo = fixture_repo(tmp_path)
    path = repo / "data/digital-twin/complete_digital_asset_manifest_2026-09-12.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    for twin in ("../escape", "UPPER", "bad/name", "same"):
        data = {"schema": "achilles_complete_digital_asset_bundle_v1",
                "assets": [
                    {"twin_id": twin, "file": f"assets/models/{twin}.obj"},
                    *([{"twin_id": twin, "file": f"assets/models/{twin}.obj"}]
                      if twin == "same" else [])
                ]}
        path.write_text(json.dumps(data), encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True,
                       capture_output=True)
        with pytest.raises(ValueError):
            module.review_digital_twin_assets(repo, module._tracked(repo))


def test_parent_cgx_registry_relationships_source_complete():
    module = load_module()
    result = module.review_cgx_domain_contracts(ROOT, module._tracked(ROOT))
    assert result["state"] == "SOURCE_REFERENCES_PRESENT"
    assert result["parent_semantic_object_id"] == "cgx:root:cognigrex"
    assert result["child_domain_count"] == 3
    assert result["child_registry_count"] == 9
    assert result["shared_contract_count"] == 48
    assert not result["missing_source_paths"]
    assert {x["domain"] for x in result["children"]} == {"romer", "eco", "emassc"}
    assert result["nested_lightspeed"] == {
        "semantic_object_id": "cgx:domain:lightspeed",
        "filespace": "LS.cgx",
        "parent_id": "cgx:domain:emassc",
        "native_admitted": False,
    }
    assert all(x["state"] == "OBSERVED_SOURCE_BYTES"
               for x in result["shared_contracts"])
    assert all(not x["domain_semantic_authority_proven"]
               for x in result["children"])
    assert result["semantic_authority_verified"] is False
    assert result["native_mint_authorized"] is False
    assert result["source_grants_verified"] is False
    assert result["cross_grex_mutation_performed"] is False


def _mini_domain_contract_fixture(tmp_path):
    import shutil
    import json
    module = load_module()
    source = ROOT / "cgx/domain_templates"
    dest = tmp_path / "mini"
    target = dest / "cgx/domain_templates"
    target.mkdir(parents=True)
    named = {"domains.json", "domain_child_identity_registry.json",
             "cognigrex_parent_topology.json"}
    manifest = json.loads((source / "domains.json").read_text(encoding="utf-8"))
    named.update(manifest["shared_contracts"].values())
    for entry in manifest["domains"].values():
        named.update(entry[k] for k in ("semantic_library",
                                        "type_registry", "relation_registry"))
    for name in named:
        shutil.copyfile(source / name, target / name)
    subprocess.run(["git", "init", "-b", "main", str(dest)],
                   check=True, capture_output=True)
    subprocess.run(["git", "-C", str(dest), "add", "."],
                   check=True, capture_output=True)
    return module, dest, target


def test_cross_grex_missing_contract_is_hold_not_new_identity(tmp_path):
    module, repo, target = _mini_domain_contract_fixture(tmp_path)
    expected = module.review_cgx_domain_contracts(repo, module._tracked(repo))
    assert expected["state"] == "SOURCE_REFERENCES_PRESENT"
    missing = target / "execution_lease_contract.json"
    missing.unlink()
    review = module.review_cgx_domain_contracts(repo, module._tracked(repo))
    assert review["state"] == "HOLD_MISSING_CONTRACTS"
    assert "cgx/domain_templates/execution_lease_contract.json" in review["missing_source_paths"]
    assert not review["native_mint_authorized"]
    assert not review["source_grants_verified"]


def test_cross_grex_conflicting_child_identity_rejected(tmp_path):
    import json
    import pytest
    module, repo, target = _mini_domain_contract_fixture(tmp_path)
    path = target / "domain_child_identity_registry.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["children"]["eco"]["parent_semantic_object_id"] = "cgx:domain:romer"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="inconsistent child semantic identity"):
        module.review_cgx_domain_contracts(repo, module._tracked(repo))
