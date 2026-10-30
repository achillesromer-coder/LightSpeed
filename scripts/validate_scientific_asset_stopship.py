#!/usr/bin/env python3
"""Fail-closed regression for the existing CGX scientific preflight route.

Synthetic evidence is deliberately adversarial; no test asserts that it
certifies a real astronomical source, DBR admission, or publication.
"""
from __future__ import annotations
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from cgx_assurance_route import route
from cgx_assurance_preflight import assess


def main():
    checks={}
    for depth in ("build","execute","publish"):
        resolution=route("romer",depth,"C0",["scientific-asset"])
        assert "V_AND_V" in resolution["required_methods"]
        fake={"source_verified":True,"method_receipts":{
            k:{"state":"COMPLETE","evidence_ids":["synthetic-self-claim"]}
            for k in resolution["required_methods"]
        }}
        status,reasons=assess(resolution,fake)
        checks[depth+"-forged-complete-receipts-rejected"]=(status=="HOLD" and
            "scientific-asset-authoritative-vector-verifier-not-integrated" in reasons)
    missing=route("romer","publish","C0",["ephemeris"])
    checks["ephemeris-alias-rejected"]=assess(missing,None)[0]=="HOLD"
    # Must not change existing low-consequence inspection route semantics.
    general=route("romer","inspect","C0",[])
    checks["non-science-inspection-unchanged"]=assess(general,None)[0]!="HOLD"
    # Design-review may proceed but cannot grant consequential execution.
    review=route("romer","propose","C0",["scientific-asset"])
    checks["science-proposal-requests-v-and-v"]="V_AND_V" in review["required_methods"]
    assert all(checks.values()),checks
    print(json.dumps({"schema":"CGX-SCIENTIFIC-STOPSHIP-REGRESSION/1.0", "tests":checks,
        "passed":sum(checks.values()),"total":len(checks),
        "scope":"review branch only; no provider source/rights/DBR authentication"},sort_keys=True))
    return 0
if __name__=="__main__":
    raise SystemExit(main())
