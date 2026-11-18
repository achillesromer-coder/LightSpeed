from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "reconcile_live_runtime.py"


def load_module():
    spec = importlib.util.spec_from_file_location("reconcile_live_runtime_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def module():
    return load_module()


def init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    files = {
        "desktop/LightSpeed_Runtime/lightspeed_runtime/__init__.py": "runtime-new\n",
        "desktop/Desktop_Hooks/LightSpeed/__main__.py": "desktop-new\n",
        "desktop/Desktop_Hooks/LightSpeed/data/private.json": "must-not-copy\n",
        "desktop/Desktop_Hooks/LightSpeed/tests/test_ui.py": "must-not-copy\n",
        "apps/lightspeed-go/dist/index.html": "<html>new</html>\n",
        "scripts/run_cognigrex_local_stack.py": "stack-new\n",
        "scripts/ensure_cognigrex_local_stack.py": "watch-new\n",
        "tools/run_ls_go_bridge.py": "bridge-new\n",
        "scripts/cgx_assurance_route.py": "assurance-route\n",
        "scripts/cgx_assurance_preflight.py": "assurance-preflight\n",
        "scripts/resolve_cgx_extensions.py": "custodial-route\n",
        "scripts/cgx_custodial_preflight.py": "custodial-preflight\n",
        "cgx/domain_templates/assurance_selection_matrix.json": "{}\n",
        "cgx/domain_templates/assurance_method_registry.json": "{}\n",
        "cgx/domain_templates/custodial_extension_registry.json": "{}\n",
        "cgx/domain_templates/cgp_ies_policy_pack.json": "{}\n",
        "cgx/domain_templates/cgp_ies_domain_adapter_registry.json": "{}\n",
    }
    for name, content in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", str(repo)], cwd=repo, check=True)
    subprocess.run(["git", "update-ref", "refs/remotes/origin/main", "HEAD"], cwd=repo, check=True)
    return repo


def test_mappings_are_bounded_to_approved_tracked_surfaces(tmp_path: Path, module) -> None:
    repo = init_repo(tmp_path)
    runtime = tmp_path / "runtime"
    mappings = module.build_mappings(repo, runtime)
    targets = {item.target_relative for item in mappings}
    assert "Core/lightspeed_runtime/__init__.py" in targets
    assert "App/__main__.py" in targets
    assert "Apps/lightspeed-go/dist/index.html" in targets
    assert "Automation/run_cognigrex_local_stack.py" in targets
    assert "Automation/ensure_cognigrex_local_stack.py" in targets
    assert "Tools/run_ls_go_bridge.py" in targets
    assert "Tools/cgx_preflight/cgx_assurance_route.py" in targets
    assert "Tools/cgx/domain_templates/cgp_ies_policy_pack.json" in targets
    assert not any("private.json" in item for item in targets)
    assert not any("test_ui.py" in item for item in targets)


def test_deployment_readiness_is_read_only_and_fail_closed(module) -> None:
    accepted = {
        "branch": "main",
        "head": "a" * 40,
        "origin_main": "a" * 40,
        "clean": True,
    }
    pending = module.deployment_readiness(
        {**accepted, "branch": "ops/review", "clean": False}, [4173, 8765]
    )
    assert pending["status"] == "HOLD"
    assert pending["blockers"] == [
        "REVIEW_BRANCH_NOT_ACCEPTED_MAIN",
        "UNCOMMITTED_OR_UNTRACKED_SOURCE",
        "MANAGED_SERVICES_ACTIVE",
    ]
    assert not pending["runtime_installed"]
    assert not pending["native_mint_authorized"]
    ready = module.deployment_readiness(accepted, [])
    assert ready["status"] == "ELIGIBLE_FOR_OWNER_CONFIRMED_APPLY"
    assert ready["blockers"] == []
    assert ready["owner_approval_recorded"] is False
    assert ready["backup_verified"] is False
    assert ready["runtime_installed"] is False


def test_deployment_readiness_rejects_unaligned_main(module) -> None:
    state = {
        "branch": "main",
        "head": "a" * 40,
        "origin_main": "b" * 40,
        "clean": True,
    }
    result = module.deployment_readiness(state, [])
    assert result["status"] == "HOLD"
    assert result["blockers"] == ["MAIN_NOT_ALIGNED_WITH_ORIGIN"]


def test_apply_requires_confirmation(tmp_path: Path, module) -> None:
    repo = init_repo(tmp_path)
    with pytest.raises(RuntimeError, match="confirmed"):
        module.apply_transaction(repo, tmp_path / "runtime", tmp_path / "receipts", confirmed=False)


def test_apply_requires_clean_current_main(tmp_path: Path, monkeypatch, module) -> None:
    repo = init_repo(tmp_path)
    (repo / "dirty.txt").write_text("dirty", encoding="utf-8")
    monkeypatch.setattr(module, "open_service_ports", lambda: [])
    with pytest.raises(RuntimeError, match="clean main"):
        module.apply_transaction(repo, tmp_path / "runtime", tmp_path / "receipts", confirmed=True)


def test_apply_refuses_open_service_ports(tmp_path: Path, monkeypatch, module) -> None:
    repo = init_repo(tmp_path)
    monkeypatch.setattr(module, "open_service_ports", lambda: [8765])
    with pytest.raises(RuntimeError, match="Services must be stopped"):
        module.apply_transaction(repo, tmp_path / "runtime", tmp_path / "receipts", confirmed=True)


def test_apply_and_rollback_restore_exact_bytes(tmp_path: Path, monkeypatch, module) -> None:
    repo = init_repo(tmp_path)
    runtime = tmp_path / "runtime"
    receipts = tmp_path / "receipts"
    installed = runtime / "Core" / "lightspeed_runtime" / "__init__.py"
    installed.parent.mkdir(parents=True)
    installed.write_text("runtime-old\n", encoding="utf-8")
    monkeypatch.setattr(module, "open_service_ports", lambda: [])

    applied = module.apply_transaction(repo, runtime, receipts, confirmed=True)
    receipt = Path(applied["receipt_path"])
    assert installed.read_text(encoding="utf-8") == "runtime-new\n"
    assert applied["status"] == "APPLIED_HASH_VERIFIED"
    assert json.loads(receipt.read_text(encoding="utf-8"))["git"]["branch"] == "main"
    assert not (runtime / "App" / "data" / "private.json").exists()

    rolled_back = module.rollback_transaction(receipt, confirmed=True)
    assert rolled_back["status"] == "ROLLBACK_HASH_VERIFIED"
    assert installed.read_text(encoding="utf-8") == "runtime-old\n"
    assert not (runtime / "App" / "__main__.py").exists()


def test_apply_auto_rolls_back_after_copy_failure(tmp_path: Path, monkeypatch, module) -> None:
    repo = init_repo(tmp_path)
    runtime = tmp_path / "runtime"
    receipts = tmp_path / "receipts"
    installed = runtime / "Core" / "lightspeed_runtime" / "__init__.py"
    installed.parent.mkdir(parents=True)
    installed.write_text("runtime-old\n", encoding="utf-8")
    monkeypatch.setattr(module, "open_service_ports", lambda: [])
    real_copy = module._atomic_copy
    calls = {"count": 0}

    def fail_second(source: Path, target: Path) -> None:
        calls["count"] += 1
        if calls["count"] == 2:
            raise OSError("injected failure")
        real_copy(source, target)

    monkeypatch.setattr(module, "_atomic_copy", fail_second)
    with pytest.raises(OSError, match="injected failure"):
        module.apply_transaction(repo, runtime, receipts, confirmed=True)
    assert installed.read_text(encoding="utf-8") == "runtime-old\n"


def test_apply_rolls_back_when_receipt_cannot_persist(tmp_path: Path, monkeypatch, module) -> None:
    repo = init_repo(tmp_path)
    runtime = tmp_path / "runtime"
    receipts = tmp_path / "receipts"
    installed = runtime / "Core" / "lightspeed_runtime" / "__init__.py"
    installed.parent.mkdir(parents=True)
    installed.write_text("runtime-old\n", encoding="utf-8")
    monkeypatch.setattr(module, "open_service_ports", lambda: [])
    monkeypatch.setattr(
        module,
        "write_json_exclusive",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("receipt failure")),
    )

    with pytest.raises(OSError, match="receipt failure"):
        module.apply_transaction(repo, runtime, receipts, confirmed=True)
    assert installed.read_text(encoding="utf-8") == "runtime-old\n"
    assert not (runtime / "App" / "__main__.py").exists()


def test_receipt_writer_is_exclusive_and_readback_verified(tmp_path: Path, module) -> None:
    path = tmp_path / "receipt.json"
    module.write_json_exclusive(path, {"ok": True})
    assert json.loads(path.read_text(encoding="utf-8")) == {"ok": True}
    with pytest.raises(FileExistsError):
        module.write_json_exclusive(path, {"ok": False})


def test_installed_cgx_catalogue_snapshot_can_resolve_without_git_checkout(
    tmp_path: Path, monkeypatch, module,
) -> None:
    """Only source-authorised metadata, not DB/credentials, is packaged."""
    repo = Path(__file__).resolve().parents[1]
    runtime = tmp_path / "installed"
    mappings = module.build_mappings(repo, runtime)
    catalogues = [x for x in mappings if x.target_relative.startswith("Core/cgx_catalogue/")]
    assert len(catalogues) == 25
    assert all("credentials" not in x.target_relative.lower() and
               "/data/" not in x.target_relative.lower()
               for x in catalogues)
    import shutil
    for item in catalogues:
        item.target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item.source, item.target)
    sys.path.insert(0, str(repo / "desktop" / "LightSpeed_Runtime"))
    from lightspeed_runtime.cgx_catalogue_root import resolve_cgx_catalogue_root
    from lightspeed_runtime import cgx_capability_registry as registry

    installed_module = runtime / "Core" / "lightspeed_runtime" / "cgx_capability_registry.py"
    installed_module.parent.mkdir(parents=True, exist_ok=True)
    root = resolve_cgx_catalogue_root(installed_module)
    assert root == runtime / "Core" / "cgx_catalogue"
    monkeypatch.setattr(registry, "REPO_ROOT", root)
    monkeypatch.setattr(registry, "DEFAULT_ROUTES_PATH",
                        root / "cgx/domain_templates/plugin_capability_routes.json")
    monkeypatch.setattr(registry, "DEFAULT_SHORTCALLS_PATH",
                        root / "plugins/source/selector_shortcalls.json")
    view, _values = registry._capability_review_snapshot("LightSpeed")
    assert view["selector"] == "lightspeed"
    assert "role:neo" in view["references"]
    assert "route:cgx.plan_query" in view["references"]
    assert view["native_admitted"] is False
