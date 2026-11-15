#!/usr/bin/env python3
"""Read-only audit of the existing desktop runtime source manifest."""
import hashlib
import json
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[2]
manifest=root/"desktop"/"source-manifest.json"
entries=json.loads(manifest.read_text(encoding="utf-8"))["records"]
mismatches=[]; verified=0
for item in entries:
    name=item["path"]
    if not name.startswith("LightSpeed_Runtime/"):
        continue
    target=root/"desktop"/name
    if not target.is_file():
        mismatches.append({"path":name,"status":"MISSING"})
        continue
    raw=target.read_bytes().replace(b"\r\n",b"\n")
    got=hashlib.sha256(raw).hexdigest()
    verified+=1
    if got!=item["sha256"] or len(raw)!=item["bytes"]:
        mismatches.append({"path":name,"expected":item["sha256"],"actual":got,
                           "expected_bytes":item["bytes"],"actual_bytes":len(raw)})
print(json.dumps({"schema":"CGX-SOURCE-MANIFEST-READONLY-AUDIT/0.1",
    "checked":verified,"mismatches":mismatches,"mutated":False},indent=2))
sys.exit(1 if mismatches else 0)
