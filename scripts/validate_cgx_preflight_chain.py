#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from cgx_assurance_route import route as assurance_route
from cgx_assurance_preflight import assess as assurance_assess
from resolve_cgx_extensions import resolve as custodial_resolve
from cgx_custodial_preflight import assess_custodial

def complete_assurance(resolution):
    return {
      "source_verified":True,
      "method_receipts":{
        m:{"state":"BOUNDED","evidence_ids":[f"fixture:{m}"]}
        for m in resolution["required_methods"]
      },
      "blocking_findings":False,
      "control_verification_complete":True,
      "independent_stop_or_containment_verified":True
    }

def complete_custodial():
    return {
      "source_verified":True,
      "authority_confirmed":True,
      "hard_predicates":{
        "SAFETY":True,"LEGAL_OR_RIGHTS_AUTHORITY":True,"ECOLOGY":True,
        "RESOURCE_BUDGET":True,"WASTE_OR_CLOSURE":True,"SECURITY":True,
        "SUCCESSION":True,"STOP_PATH":True
      }
    }

def main():
    failures=[]
    ar=assurance_route("eco","inspect","C0",["field-observation"])
    ad,_=assurance_assess(ar,None)
    cr=custodial_resolve("eco","inspect","standard","C0",["field-observation"])
    cd,_=assess_custodial(cr,None)
    if ad=="HOLD" or cd=="HOLD": failures.append("low-consequence observation unexpectedly held")

    ar=assurance_route("romer","execute","C3",["resource-extraction"])
    ad,_=assurance_assess(ar,None)
    cr=custodial_resolve("romer","execute","standard","C3",["resource-extraction"])
    cd,_=assess_custodial(cr,None)
    if ad!="HOLD" or cd!="HOLD": failures.append("high-consequence unassessed extraction did not fail closed")

    tags=["intersol","facility","battery-room","public-route"]
    ar=assurance_route("romer","build","C2",tags)
    ad,arx=assurance_assess(ar,complete_assurance(ar))
    cr=custodial_resolve("romer","build","standard","C2",tags)
    cd,crx=assess_custodial(cr,complete_custodial())
    if ad=="HOLD" or cd=="HOLD": failures.append(f"bounded InterSol fixture failed: assurance={arx}, custodial={crx}")

    ar=assurance_route("lightspeed","execute","C3",["replication-control"])
    if ar["minimum_assurance_state"]!="SAFETY_CASE": failures.append("replication control is not routed to SAFETY_CASE")
    cr=custodial_resolve("lightspeed","execute","standard","C3",["replication-control"])
    if cr["mode"]!="ENFORCE_SAFETY": failures.append("replication control is not routed to ENFORCE_SAFETY")

    print({"status":"PASS" if not failures else "FAIL","failures":failures})
    return 1 if failures else 0

if __name__=="__main__":
    raise SystemExit(main())
