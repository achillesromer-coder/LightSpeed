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

from lightspeed_runtime.source_intake import SourceIntakeError, build_source_envelope_from_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a read-only native-preserving CGX source envelope."
    )
    parser.add_argument("source", help="Path to the source file.")
    parser.add_argument("--authority", default="source")
    parser.add_argument("--evidence-state", default="OBSERVED")
    parser.add_argument("--release-class", default="Internal")
    parser.add_argument("--output", help="Optional output JSON path. Stdout when omitted.")
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

    payload = json.dumps(envelope, indent=2, sort_keys=True, ensure_ascii=False)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload + "\n", encoding="utf-8")
        print(json.dumps({
            "status": "PASS",
            "source_id": envelope["source_id"],
            "adapter_id": envelope["adapter_id"],
            "output": str(out),
            "canonical_mutation": False,
        }, sort_keys=True))
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
