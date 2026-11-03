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
    # Without authenticated classification, even an untagged simulation can
    # produce a consequential numerical claim. Forged receipts cannot clear it.
    simulation_hold = "simulation-authenticated-asset-classification-and-native-verifier-unavailable"
    unclassified_simulation_failures = []
    for domain in ("romer", "eco", "emassc", "lightspeed"):
        for tags in ([], ["public-claim"], ["unclassified"], ["render-preview"]):
            resolution = route(domain, "simulate", "C0", tags)
            forged = {"source_verified": True, "method_receipts": {
                method: {"state": "COMPLETE", "evidence_ids": ["caller-self-attested"]}
                for method in resolution["required_methods"]}}
            decision, reasons = assess(resolution, forged)
            if decision != "HOLD" or simulation_hold not in reasons:
                unclassified_simulation_failures.append((domain, tags, decision, reasons))
    checks["unclassified-simulation-matrix-16-forged-receipts-rejected"] = (
        not unclassified_simulation_failures)
    simulation_cli = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent / "cgx_assurance_preflight.py"),
         "--domain", "lightspeed", "--execution-depth", "simulate", "--tags", "render-preview"],
        capture_output=True, text=True, timeout=15, check=False)
    simulation_receipt = json.loads(simulation_cli.stdout) if simulation_cli.stdout.strip() else {}
    checks["unclassified-simulation-cli-held"] = (
        simulation_cli.returncode == 3 and simulation_receipt.get("decision") == "HOLD"
        and simulation_hold in simulation_receipt.get("hold_reasons", []))
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
    # Source-only JPL request contracts: no URL is fetched and no vector is asserted.
    from urllib.parse import urlsplit, parse_qs
    from cgx_horizons_request_review import plan_vector_request, TARGETS, EPOCH_UT, DOC
    planned = [plan_vector_request(body) for body in TARGETS]
    checks["horizons-request-spec-eight-planet-centers"] = (
        len(planned) == 8 and len({p["target_naif"] for p in planned}) == 8
        and 399 in TARGETS and 3 not in TARGETS)
    checks["horizons-request-spec-exact-epoch-frame-units"] = all(
        p["epoch_input"] == EPOCH_UT and p["time_scale_requested"] == "UT"
        and p["origin"] == "500@10" and p["reference_plane"] == "ECLIPTIC"
        and p["reference_system"] == "ICRF" and p["units"] == "KM-S"
        and p["vector_table"] == 2 and p["correction"] == "NONE"
        and p["tdb_minus_ut_report_requested"] is True
        and p["calendar_type"] == "GREGORIAN"
        and p["vector_component_labels_requested"] is True
        and p["source_documentation"] == DOC for p in planned)
    required = {"COMMAND", "CENTER", "TLIST", "TLIST_TYPE", "TIME_TYPE",
                "REF_PLANE", "REF_SYSTEM", "OUT_UNITS", "VEC_TABLE",
                "VEC_CORR", "EPHEM_TYPE", "TIME_DIGITS",
                "VEC_DELTA_T", "CAL_TYPE", "VEC_LABELS"}
    checks["horizons-request-spec-url-parameters"] = all(
        urlsplit(p["url"]).netloc == "ssd.jpl.nasa.gov"
        and required <= parse_qs(urlsplit(p["url"]).query).keys()
        and parse_qs(urlsplit(p["url"]).query)["COMMAND"] == [f"'{p['target_naif']}'"]
        and parse_qs(urlsplit(p["url"]).query)["TLIST"] == [f"'{EPOCH_UT}'"]
        for p in planned)
    checks["horizons-request-spec-explicit-timescale-offset-and-labels"] = all(
        parse_qs(urlsplit(p["url"]).query).get("VEC_DELTA_T") == ["\'YES\'"]
        and parse_qs(urlsplit(p["url"]).query).get("CAL_TYPE") == ["\'GREGORIAN\'"]
        and parse_qs(urlsplit(p["url"]).query).get("VEC_LABELS") == ["\'YES\'"]
        for p in planned)
    # Recompute the planned-request digest independently from URL parameters.
    # It is intentionally NOT a response-body hash or CGX Object_ID.
    from hashlib import sha256
    from cgx_horizons_request_review import SCHEMA, ENDPOINT, API_DOC_VERSION, API_DOC_DATE
    def independent_spec_digest(planned_request):
        query = parse_qs(urlsplit(planned_request["url"]).query, strict_parsing=True)
        params = {key: values[0] for key, values in query.items()}
        canonical = json.dumps(
            {"schema": SCHEMA, "endpoint": ENDPOINT, "documentation": DOC,
             "api_document_version": API_DOC_VERSION, "api_document_date": API_DOC_DATE,
             "params": params},
            sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("utf-8")
        return sha256(canonical).hexdigest()
    checks["horizons-request-spec-digest-independent-recompute"] = all(
        p["request_spec_sha256"] == independent_spec_digest(p)
        and p["request_spec_hash_scope"] == "canonical-json-schema-endpoint-documentation-version-date-params-only"
        for p in planned)
    checks["horizons-request-spec-documentation-version-bound"] = all(
        p["source_documentation"] == DOC
        and p["source_documentation_version"] == "1.3"
        and p["source_documentation_date"] == "2025 June"
        and p["request_spec_sha256"] == independent_spec_digest(p)
        for p in planned)
    # The version/date is part of the digest preimage; an independent
    # recomputation with a different documented API revision must differ.
    checks["horizons-request-spec-version-substitution-changes-hash"] = all(
        sha256(json.dumps({
            "schema": SCHEMA, "endpoint": ENDPOINT, "documentation": DOC,
            "api_document_version": "0.0-unverified", "api_document_date": API_DOC_DATE,
            "params": {k: v[0] for k, v in parse_qs(
                urlsplit(p["url"]).query, strict_parsing=True).items()},
        }, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")).hexdigest() != p["request_spec_sha256"]
        for p in planned)
    # Fail closed on silently added API parameters; only the reviewed request
    # contract may be emitted. This is source-plan integrity, not JPL proof.
    checks["horizons-request-spec-parameter-allowlist"] = all(
        set(parse_qs(urlsplit(p["url"]).query, strict_parsing=True))
        == required | {"format", "OBJ_DATA", "MAKE_EPHEM"}
        for p in planned)
    # An altered target, center, timescale, frame or unit must invalidate the
    # request-spec digest. No digest here authenticates any response bytes.
    from urllib.parse import urlencode, quote
    tamper_cases = (("COMMAND", "'3'"), ("CENTER", "'500@399'"),
                    ("TIME_TYPE", "'TDB'"), ("REF_PLANE", "'FRAME'"),
                    ("OUT_UNITS", "'AU-D'"))
    def altered_request_digest(p, key, replacement):
        params = {k: values[0] for k, values in parse_qs(
            urlsplit(p["url"]).query, strict_parsing=True).items()}
        params[key] = replacement
        return independent_spec_digest({**p, "url": ENDPOINT + "?" +
            urlencode(params, quote_via=quote)})
    checks["horizons-request-spec-scientific-parameter-tamper-rejected"] = all(
        altered_request_digest(p, key, value) != p["request_spec_sha256"]
        for p in planned for key, value in tamper_cases)
    checks["horizons-request-spec-digest-distinct-and-repeatable"] = (
        len({p["request_spec_sha256"] for p in planned}) == len(TARGETS)
        and planned == [plan_vector_request(body) for body in TARGETS])
    checks["horizons-request-hash-is-not-fabricated-source-hash"] = all(
        p["source_response_sha256"] is None
        and p["source_response_bytes"] is None
        and p["raw_source_verified"] is False
        and p["network_executed"] is False for p in planned)
    rejected = 0
    for invalid in (3, 10, 0, 999, "399", True, None, 399.0):
        try:
            plan_vector_request(invalid)
        except ValueError:
            rejected += 1
    checks["horizons-request-spec-rejects-barycenter-and-ambiguous-types"] = rejected == 8
    checks["horizons-request-spec-never-promotes-to-raw-or-native"] = all(
        p["evidence_stage"] == "REQUEST_SPEC_ONLY"
        and all(p[flag] is False for flag in (
            "network_executed", "raw_source_verified", "numerical_result_verified",
            "native_admitted", "runtime_verified")) for p in planned)
    # Review-plan consumer boundary: a locally planned URL/digest is not an
    # authoritative R0 source, and no caller can promote it by editing fields.
    from cgx_horizons_request_review import verify_planned_request
    checks["horizons-review-plan-consumer-accepts-only-canonical-plans"] = all(
        verify_planned_request(p) == p for p in planned)
    def rejects_review_plan(candidate):
        try:
            verify_planned_request(candidate)
        except ValueError:
            return True
        return False
    plan_tamper_cases = (
        lambda p: {**p, "url": p["url"] + "&COMMAND=%273%27"},
        lambda p: {**p, "url": p["url"].replace("CENTER=%27500%4010%27", "CENTER=%27500%40399%27")},
        lambda p: {**p, "request_spec_sha256": "0" * 64},
        lambda p: {**p, "source_documentation_version": "unverified"},
        lambda p: {**p, "epoch_input": "2025-Jun-05 12:00:00"},
        lambda p: {**p, "target_naif": 3},
        lambda p: {**p, "target_naif": True},
        lambda p: {**p, "source_response_sha256": "forged"},
        lambda p: {**p, "source_response_bytes": 123},
        lambda p: {**p, "network_executed": True},
        lambda p: {**p, "raw_source_verified": True},
        lambda p: {**p, "native_admitted": True},
        lambda p: {**p, "runtime_verified": True},
        lambda p: {**p, "evidence_stage": "ADMITTED"},
        lambda p: {**p, "unreviewed_extra_parameter": "1"},
    )
    checks["horizons-review-plan-consumer-rejects-tampering"] = all(
        rejects_review_plan(mutator(p)) for p in planned
        for mutator in plan_tamper_cases)
    checks["horizons-review-plan-consumer-rejects-malformed-types"] = all(
        rejects_review_plan(candidate) for candidate in
        (None, True, 399, "399", [], {"target_naif": 399}))
    # Python's bool/int/float equality can otherwise admit an untyped
    # external JSON plan even when every nominal value appears canonical.
    # These 56 negative cases do not simulate or certify ephemeris data.
    type_confusions = (
        ("vector_table", 2.0),
        ("tdb_minus_ut_report_requested", 1),
        ("network_executed", 0),
        ("raw_source_verified", 0),
        ("numerical_result_verified", 0),
        ("native_admitted", 0),
        ("runtime_verified", 0),
    )
    checks["horizons-review-plan-consumer-rejects-56-type-confusions"] = all(
        rejects_review_plan({**p, key: replacement})
        for p in planned for key, replacement in type_confusions)
    assert all(checks.values()),checks
    print(json.dumps({"schema":"CGX-SCIENTIFIC-STOPSHIP-REGRESSION/1.0", "tests":checks,
        "passed":sum(checks.values()),"total":len(checks),
        "scope":"review branch only; no provider source/rights/DBR authentication"},sort_keys=True))
    return 0
if __name__=="__main__":
    raise SystemExit(main())
