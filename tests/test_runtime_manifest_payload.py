"""Verify manifest completeness and imports from its copied runtime payload."""
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_missing_queue_consumer_is_rejected(tmp_path, monkeypatch, capsys):
    spec = importlib.util.spec_from_file_location("surface_check", ROOT / "scripts/validate_lightspeed_surfaces.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    manifest = json.loads(module.MANIFEST.read_text())
    omitted = "LightSpeed_Runtime/lightspeed_runtime/ls_go_job_consumer.py"
    manifest["records"] = [r for r in manifest["records"] if r["path"] != omitted]
    altered = tmp_path / "manifest.json"
    altered.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(module, "MANIFEST", altered)
    assert module.main() == 1
    assert f"Runtime source missing from manifest: {omitted}" in capsys.readouterr().err


def test_manifest_runtime_imports_from_copied_payload(tmp_path):
    core = tmp_path / "Core"
    records = json.loads((ROOT / "desktop/source-manifest.json").read_text())["records"]
    for record in records:
        path = PurePosixPath(record["path"])
        if path.parts[0] != "LightSpeed_Runtime":
            continue
        assert not path.is_absolute() and ".." not in path.parts
        content = (ROOT / "desktop" / Path(*path.parts)).read_bytes().replace(b"\r\n", b"\n")
        assert hashlib.sha256(content).hexdigest() == record["sha256"]
        destination = core / Path(*path.parts[1:])
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    probe = """import importlib,sys
from pathlib import Path
core=Path(sys.argv[1]).resolve()
sys.path.insert(0,str(core))
for name in ['lightspeed_runtime','lightspeed_runtime.ls_go_bridge','lightspeed_runtime.ls_go_job_consumer']:
 module=importlib.import_module(name)
 assert Path(module.__file__).resolve().is_relative_to(core), name
"""
    result = subprocess.run([sys.executable, "-I", "-B", "-c", probe, str(core)],
                            cwd=tmp_path, capture_output=True, text=True, timeout=45)
    assert result.returncode == 0, result.stderr
