#!/usr/bin/env python3
"""Fail-closed regression for the existing CGX scientific preflight route.

Synthetic evidence is deliberately adversarial; no test asserts that it
certifies a real astronomical source, DBR admission, or publication.
"""
from __future__ import annotations
import json,sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from cgx_assurance_route import route
from cgx_assurance_preflight import assess


def main():
    checks={}
    for depth in ("simulate","build","execute","publish"):
        resolution=route("romer",depth,"C0",["scientific-asset"])
        assert "V_AND_V" in resolution["required_methods"]
        fake={"source_verified":True,"method_receipts":{
            k:{"state":"COMPLETE","evidence_ids":["synthetic-self-claim"]}
            for k in resolution["required_methods"]
        }}
        status,reasons=assess(resolution,fake)
        checks[depth+"-forged-complete-receipts-rejected"]=(status=="HOLD" and
            "scientific-asset-authoritative-vector-verifier-not-integrated" in reasons)
    # Explicit asset-class aliases must never bypass the science stop-ship, even
    # with fabricated COMPLETE receipts. Exercise every family and effectful depth.
    aliases=("orbital-geometry","orbital-scale","geometry-asset",
             "simulation-asset","engineering-asset","ecological-asset",
             "operational-asset")
    failures=[]
    for domain in ("romer","eco","emassc","lightspeed"):
        for depth in ("simulate","build","execute","publish"):
            for tag in aliases:
                resolution=route(domain,depth,"C0",[tag])
                fake={"source_verified":True,"method_receipts":{
                    m:{"state":"COMPLETE","evidence_ids":["synthetic-self-claim"]}
                    for m in resolution["required_methods"]}}
                status,reasons=assess(resolution,fake)
                if ("V_AND_V" not in resolution["required_methods"] or
                    status!="HOLD" or
                    "scientific-asset-authoritative-vector-verifier-not-integrated" not in reasons):
                    failures.append(f"{domain}/{depth}/{tag}")
    checks["explicit-asset-alias-matrix-112-forged-receipts-rejected"]=not failures
    # These are actual named source/solver *route labels*, not installed tools.
    # Their spelling, case and padding must not bypass the scientific stop-ship.
    astro_aliases = ("horizons-vectors", "spice-ephemeris",
                     "gmat-trajectory", "solar-system-state")
    astro_failures = []
    for domain in ("romer", "eco", "emassc", "lightspeed"):
        for depth in ("simulate", "build", "execute", "publish"):
            for tag in astro_aliases:
                resolution = route(domain, depth, "C0", [f" {tag.upper()} "])
                fake = {"source_verified": True, "method_receipts": {
                    method: {"state": "COMPLETE", "evidence_ids": ["forged-source"]}
                    for method in resolution["required_methods"]}}
                decision, reasons = assess(resolution, fake)
                if (resolution["context"]["tags"] != [tag]
                        or "AR-18" not in resolution["matched_routes"]
                        or "V_AND_V" not in resolution["required_methods"]
                        or decision != "HOLD"
                        or "scientific-asset-authoritative-vector-verifier-not-integrated" not in reasons):
                    astro_failures.append((domain, depth, tag, decision))
    checks["astronomical-adapter-alias-matrix-64-forged-receipts-rejected"] = not astro_failures
    # Source-only inspection still requires an assurance assessment before
    # this route could be cleared; no missing receipt implies native admission.
    checks["astronomical-source-inspection-without-receipt-held"] = (
        assess(route("lightspeed", "inspect", "C0", ["horizons-vectors"]), None)[0]
        == "HOLD")
    # CLI parsing is the final untrusted classification boundary.
    astro_cmd = [sys.executable,
        str(Path(__file__).resolve().parent / "cgx_assurance_preflight.py"),
        "--domain", "lightspeed", "--execution-depth", "simulate",
        "--tags", " SPICE-EPHEMERIS "]
    astro_proc = subprocess.run(astro_cmd, capture_output=True, text=True,
                                timeout=15, check=False)
    astro_cli = json.loads(astro_proc.stdout) if astro_proc.stdout.strip() else {}
    checks["spice-simulation-cli-fail-closed"] = (
        astro_proc.returncode == 3 and astro_cli.get("decision") == "HOLD"
        and "AR-18" in astro_cli.get("resolution", {}).get("matched_routes", [])
        and "scientific-asset-authoritative-vector-verifier-not-integrated"
        in astro_cli.get("hold_reasons", []))
    # Test the real CLI boundary, not just the Python function under test.
    cmd=[sys.executable,str(Path(__file__).resolve().parent/"cgx_assurance_preflight.py"),
         "--domain","romer","--execution-depth","build","--tags","orbital-geometry"]
    proc=subprocess.run(cmd,capture_output=True,text=True,timeout=15,check=False)
    cli=json.loads(proc.stdout) if proc.stdout.strip() else {}
    checks["orbital-geometry-cli-fail-closed"]=(proc.returncode==3 and
        cli.get("decision")=="HOLD" and
        "scientific-asset-authoritative-vector-verifier-not-integrated" in cli.get("hold_reasons",[]))
    # A numerical simulation is not made authoritative by a caller-supplied receipt.
    # The real CLI must stop even before an authenticated solver or DBR exists.
    sim_cmd=[sys.executable,str(Path(__file__).resolve().parent/"cgx_assurance_preflight.py"),
         "--domain","lightspeed","--execution-depth","simulate","--tags","simulation-asset"]
    sim_proc=subprocess.run(sim_cmd,capture_output=True,text=True,timeout=15,check=False)
    sim_cli=json.loads(sim_proc.stdout) if sim_proc.stdout.strip() else {}
    checks["simulation-asset-cli-fail-closed"]=(sim_proc.returncode==3 and
        sim_cli.get("decision")=="HOLD" and
        "scientific-asset-authoritative-vector-verifier-not-integrated" in sim_cli.get("hold_reasons",[]))
    missing=route("romer","publish","C0",["ephemeris"])
    checks["ephemeris-alias-rejected"]=assess(missing,None)[0]=="HOLD"
    # Must not change existing low-consequence inspection route semantics.
    general=route("romer","inspect","C0",[])
    checks["non-science-inspection-unchanged"]=assess(general,None)[0]!="HOLD"
    # Design-review may proceed but cannot grant consequential execution.
    review=route("romer","propose","C0",["scientific-asset"])
    checks["science-proposal-requests-v-and-v"]="V_AND_V" in review["required_methods"]
    # An untrusted caller can omit science classification entirely. Publication
    # cannot inherit permission from empty, benign or misclassified tags.
    generic_hold = "publication-authenticated-source-classification-rights-and-owner-approval-unverified"
    generic_failures = []
    for domain in ("romer", "eco", "emassc", "lightspeed"):
        for tags in ([], ["public-claim"], ["public-projection"], ["unclassified"]):
            resolution = route(domain, "publish", "C0", tags)
            forged = {"source_verified": True, "method_receipts": {
                m: {"state": "COMPLETE", "evidence_ids": ["caller-self-attested"]}
                for m in resolution["required_methods"]}}
            status, reasons = assess(resolution, forged)
            if status != "HOLD" or generic_hold not in reasons:
                generic_failures.append((domain, tags, status, reasons))
    checks["unclassified-publication-matrix-16-forged-receipts-rejected"] = not generic_failures
    # Both the assurance CLI and the composed consequence CLI must enforce it.
    script_dir = Path(__file__).resolve().parent
    assurance_cli = subprocess.run(
        [sys.executable, str(script_dir / "cgx_assurance_preflight.py"),
         "--domain", "romer", "--execution-depth", "publish", "--tags", "public-claim"],
        capture_output=True, text=True, timeout=15, check=False)
    a_receipt = json.loads(assurance_cli.stdout) if assurance_cli.stdout.strip() else {}
    checks["untagged-science-publication-assurance-cli-held"] = (
        assurance_cli.returncode == 3 and a_receipt.get("decision") == "HOLD"
        and generic_hold in a_receipt.get("hold_reasons", []))
    consequence_cli = subprocess.run(
        [sys.executable, str(script_dir / "cgx_consequence_preflight.py"),
         "--domain", "romer", "--execution-depth", "publish", "--tags", "public-projection"],
        capture_output=True, text=True, timeout=15, check=False)
    c_receipt = json.loads(consequence_cli.stdout) if consequence_cli.stdout.strip() else {}
    checks["unclassified-publication-consequence-cli-held"] = (
        consequence_cli.returncode == 3 and c_receipt.get("decision") == "HOLD"
        and c_receipt.get("assurance", {}).get("decision") == "HOLD"
        and generic_hold in c_receipt.get("assurance", {}).get("hold_reasons", []))
    assert all(checks.values()),checks
    print(json.dumps({"schema":"CGX-SCIENTIFIC-STOPSHIP-REGRESSION/1.0", "tests":checks,
        "passed":sum(checks.values()),"total":len(checks),
        "scope":"review branch only; no provider source/rights/DBR authentication"},sort_keys=True))
    return 0
if __name__=="__main__":
    raise SystemExit(main())
