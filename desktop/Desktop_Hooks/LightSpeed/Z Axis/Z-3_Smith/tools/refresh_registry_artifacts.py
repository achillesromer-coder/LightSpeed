#!/usr/bin/env python
"""
Refresh operations registry derived artifacts:
- depmap fragment (operations_registry_adapter.py)
- embed snippets (generate_operations_embeds.py)
- full dataindex (generate_dataindex.py)
"""
import subprocess, sys, pathlib
root = pathlib.Path(__file__).resolve().parents[3]
tools = root / "Z Axis" / "Z-3_Smith" / "tools"
cmds = [
    [sys.executable, str(tools / "operations_registry_adapter.py")],
    [sys.executable, str(tools / "generate_operations_embeds.py")],
    [sys.executable, str(tools / "generate_dataindex.py")],
]
for c in cmds:
    print("[refresh]", " ".join(c))
    subprocess.run(c, check=False)
