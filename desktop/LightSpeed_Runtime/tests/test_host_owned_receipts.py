from __future__ import annotations
import hashlib,json
from pathlib import Path
import pytest
import sys
RUNTIME_ROOT=Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:sys.path.insert(0,str(RUNTIME_ROOT))
from lightspeed_runtime.host_owned_receipts import prepare_source,build_request,validate_model_selection

def setup(tmp_path):
 p=tmp_path/"review-state.json"
 p.write_text('{\n  "native_state": "candidate",\n  "signed_lease": false,\n  "review_required": true\n}\n',encoding="utf-8")
 src,ids=prepare_source(p)
 return p,src,ids

def ok(ids):
 return {"response":json.dumps({"floor_summary":"The native state remains candidate and signed lease is unverified.","blocker":"Owner review required.","evidence_ids":[next(iter(ids))]}),
         "done":True,"done_reason":"stop"}

def test_real_host_citation_binding(tmp_path):
 p,src,ids=setup(tmp_path)
 req=build_request("Neo",ids)
 assert req["options"]["num_ctx"]==2048
 assert str(p) not in req["prompt"]
 selected=validate_model_selection(ok(ids),ids,src)
 assert selected["citations"][0]["path"]==str(p)
 assert selected["citations"][0]["sha256"]==hashlib.sha256(p.read_bytes()).hexdigest()
 assert selected["safe_artifact_route"] is None
 assert selected["route_host_owned"] is True

@pytest.mark.parametrize("payload",[
 {"floor_summary":"ok","blocker":None,"evidence_ids":["E99"]},
 {"floor_summary":"ok","blocker":None,"evidence_ids":[]},
 {"floor_summary":"ok","blocker":None,"evidence_ids":["E00","E00"]},
 {"floor_summary":"ok","blocker":None,"evidence_ids":["E00"],"safe_artifact_route":"C:\\bad\\path"},
 {"floor_summary":"","blocker":None,"evidence_ids":["E00"]},
])
def test_untrusted_evidence_fails_closed(tmp_path,payload):
 _,src,ids=setup(tmp_path)
 with pytest.raises(ValueError):
  validate_model_selection({"response":json.dumps(payload),"done":True},ids,src)

def test_broken_json_windows_path_rejected(tmp_path):
 _,src,ids=setup(tmp_path)
 raw=r'{"floor_summary":"x","blocker":null,"evidence_ids":["E00"],"path":"C:\bad\path"}'
 with pytest.raises(ValueError,match="strict JSON"):
  validate_model_selection({"response":raw,"done":True},ids,src)

def test_source_change_blocks_stale_hash(tmp_path):
 p,src,ids=setup(tmp_path)
 p.write_text('{"native_state":"active"}\n',encoding="utf-8")
 with pytest.raises(ValueError,match="changed"):
  validate_model_selection(ok(ids),ids,src)

@pytest.mark.parametrize("reason",["length","stop"])
def test_missing_completion_fails(tmp_path,reason):
 _,src,ids=setup(tmp_path)
 result=ok(ids);result["done_reason"]=reason;result["done"]=reason=="length"
 with pytest.raises(ValueError,match="incomplete"):
  validate_model_selection(result,ids,src)

def test_source_limits_and_symlink_safety(tmp_path):
 _,src,ids=setup(tmp_path)
 with pytest.raises(ValueError):
  prepare_source(tmp_path/"not_found.txt")
 assert all(c["sha256"]==src["sha256"] for c in ids.values())