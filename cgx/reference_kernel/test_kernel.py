import json, shutil, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "cgx/reference_kernel/cgx_kernel.py"

def run(*args):
    p = subprocess.run(["python3", str(CLI), *map(str,args)], capture_output=True, text=True, check=True)
    return json.loads(p.stdout)

# Reference test body is mirrored from the living CGX carrier test suite.
# The carrier itself remains the authoritative Phase-B executable fixture.
print("Use CGX living carrier tests/test_kernel.py for full conformance run")
