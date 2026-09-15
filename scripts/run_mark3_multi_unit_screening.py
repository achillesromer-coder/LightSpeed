#!/usr/bin/env python3
"""Run a supplied Mark III multi-unit screening scenario and write JSON receipts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = REPO_ROOT / "desktop" / "LightSpeed_Runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime.mark3_multi_unit import (  # noqa: E402
    Interlock,
    JointMove,
    Placement,
    ScreeningInputError,
    TraverseLeg,
    UnitSpec,
    simulate_scenario,
    sweep_delta_v,
)


def _tuple_ids(row: dict) -> dict:
    return {**row, "active_unit_ids": tuple(row["active_unit_ids"])}


def run(input_path: Path, output_path: Path) -> dict:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    units = [UnitSpec(**row) for row in payload["units"]]
    legs = [TraverseLeg(**_tuple_ids(row)) for row in payload["legs"]]
    moves = [JointMove(**row) for row in payload.get("moves", [])]
    placements = [Placement(**row) for row in payload["placements"]]
    interlocks = [Interlock(**row) for row in payload.get("interlocks", [])]
    result = simulate_scenario(
        scenario_id=payload["scenario_id"],
        units=units,
        legs=legs,
        moves=moves,
        placements=placements,
        interlocks=interlocks,
    )
    scales = payload.get("delta_v_scale")
    if scales is not None:
        result["delta_v_sweep"] = sweep_delta_v(
            scenario_id=payload["scenario_id"],
            units=units,
            legs=legs,
            moves=moves,
            placements=placements,
            interlocks=interlocks,
            delta_v_scale=scales,
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="source-bound scenario JSON")
    parser.add_argument("output", type=Path, help="derived receipt JSON")
    args = parser.parse_args()
    try:
        result = run(args.input, args.output)
    except (KeyError, TypeError, json.JSONDecodeError, ScreeningInputError) as exc:
        print(f"HOLD: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "schema": result["schema"],
                "scenario_id": result["scenario_id"],
                "evidence_class": result["evidence_class"],
                "screening_pass": result["summary"]["screening_pass"],
                "output": str(args.output.resolve()),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
