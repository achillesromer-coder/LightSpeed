#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "desktop" / "LightSpeed_Runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from lightspeed_runtime.cgx_conversion_planner import CGXConversionPlanError, compile_conversion_plan
from lightspeed_runtime.source_intake import (
    SourceIntakeError,
    bind_envelope_to_conversion_plan,
    build_source_envelope_from_path,
)

CGX_TEMPLATES = ROOT / "cgx" / "domain_templates"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a read-only native-preserving CGX source envelope."
    )
    parser.add_argument("source", help="Path to the source file.")
    parser.add_argument("--authority", default="source")
    parser.add_argument("--evidence-state", default="OBSERVED")
    parser.add_argument("--release-class", default="Internal")
    parser.add_argument("--output", help="Optional output JSON path. Stdout when omitted.")
    parser.add_argument("--with-plan", action="store_true", help="Compile and bind the current CGX conversion plan for this exact source.")
    parser.add_argument("--domain", help="Optional semantic domain used only for registered first-file mapping selection.")
    parser.add_argument("--semantic-target", help="Optional desired R2 semantic target. Holds if no registered mapping exists.")
    parser.add_argument("--requested-output", action="append", default=[], help="Optional R3 representation request; repeatable and non-canonical.")
    args = parser.parse_args()

    try:
        envelope = build_source_envelope_from_path(
            args.source,
            authority=args.authority,
            evidence_state=args.evidence_state,
            release_class=args.release_class,
        )
    except SourceIntakeError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}), file=sys.stderr)
        return 2

    result: dict = envelope
    receipt: dict | None = None
    if args.with_plan:
        try:
            type_registry = json.loads(
                (CGX_TEMPLATES / "file_type_conversion_registry.json").read_text(encoding="utf-8")
            )
            conversion_contract = json.loads(
                (CGX_TEMPLATES / "file_conversion_contract.json").read_text(encoding="utf-8")
            )
            first_file_registry = json.loads(
                (CGX_TEMPLATES / "first_file_conversion_registry.json").read_text(encoding="utf-8")
            )
            plan = compile_conversion_plan(
                file_name=envelope["source_name"],
                source_sha256=envelope["sha256"],
                source_ref=envelope["native_preservation"]["source_ref"],
                media_type=envelope["media_type"],
                domain=args.domain,
                semantic_target=args.semantic_target,
                requested_outputs=args.requested_output,
                type_registry=type_registry,
                conversion_contract=conversion_contract,
                first_file_registry=first_file_registry,
            )
            bound = bind_envelope_to_conversion_plan(envelope, plan)
        except (OSError, json.JSONDecodeError, CGXConversionPlanError, SourceIntakeError) as exc:
            print(json.dumps({"status": "FAIL", "error": str(exc)}), file=sys.stderr)
            return 3

        receipt = {
            "schema": "CGX-FIRST-FILE-CONFORMANCE-RECEIPT/0.1",
            "status": (
                "PASS"
                if not str(bound.get("admission_state", "")).startswith("BLOCKED")
                else "BLOCKED"
            ),
            "source_id": bound["source_id"],
            "source_sha256": bound["sha256"],
            "source_name": bound["source_name"],
            "source_ref": bound["native_preservation"]["source_ref"],
            "adapter_id": bound["adapter_id"],
            "conversion_plan_sha256": plan["plan_sha256"],
            "admission_state": bound.get("admission_state"),
            "conversion_classes_admitted": bound.get("conversion_classes_admitted") or [],
            "semantic_target": bound.get("semantic_target"),
            "frontier": plan.get("frontier") or [],
            "unresolved": bound.get("unresolved") or [],
            "projection_kinds": [
                projection.get("kind")
                for projection in bound.get("projections") or []
                if isinstance(projection, dict)
            ],
            "native_source_authority_preserved": True,
            "canonical_mutation": False,
            "execution_performed": False,
        }
        result = {
            "schema": "CGX-FIRST-FILE-CONFORMANCE-BUNDLE/0.1",
            "envelope": envelope,
            "conversion_plan": plan,
            "bound_envelope": bound,
            "receipt": receipt,
        }

    payload = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload + "\n", encoding="utf-8")
        summary = {
            "status": receipt["status"] if receipt else "PASS",
            "source_id": envelope["source_id"],
            "adapter_id": envelope["adapter_id"],
            "output": str(out),
            "canonical_mutation": False,
        }
        if receipt:
            summary.update(
                {
                    "admission_state": receipt["admission_state"],
                    "conversion_plan_sha256": receipt["conversion_plan_sha256"],
                }
            )
        print(json.dumps(summary, sort_keys=True))
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
