from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "desktop" / "LightSpeed_Runtime"
TEST_FILE = RUNTIME / "tests" / "test_cgx_capability_facades.py"
sys.path.insert(0, str(RUNTIME))

spec = importlib.util.spec_from_file_location("cgx_facade_tests", TEST_FILE)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

result = {
    "schema": "CGX-CAPABILITY-FACADE-LOCAL-VALIDATION/0.1",
    "tests": [],
    "passed": True,
}

for name in sorted(dir(module)):
    if not name.startswith("test_"):
        continue
    fn = getattr(module, name)
    if not callable(fn):
        continue
    try:
        fn()
        result["tests"].append({"name": name, "status": "PASS"})
    except Exception as exc:
        result["passed"] = False
        result["tests"].append({
            "name": name,
            "status": "FAIL",
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
        })

receipt_dir = ROOT / "State" / "Review" / "CGX_CAPABILITY_FACADES_20261002"
receipt_dir.mkdir(parents=True, exist_ok=True)
receipt = receipt_dir / "local_repo_validation_receipt.json"
receipt.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
raise SystemExit(0 if result["passed"] else 2)
