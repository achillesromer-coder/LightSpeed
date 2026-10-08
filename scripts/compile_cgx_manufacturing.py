#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cgx.manufacturing import (
    compile_component,
    emit_reference_gcode,
    find_archetype,
    find_instance,
    load_default_atlas,
    load_default_instance_population,
)


def load_optional(path: str | None):
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_output(value, path: str | None) -> None:
    text = value if isinstance(value, str) else json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if path:
        Path(path).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def main() -> None:
    ap = argparse.ArgumentParser(description="Compile CGX component manufacturing IR or emit gated reference G-code.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    comp = sub.add_parser("component")
    selector = comp.add_mutually_exclusive_group(required=True)
    selector.add_argument("--archetype", help="CGA ID or unique component-archetype substring")
    selector.add_argument("--instance-id", help="CGXI instance ID from the canonical component instance population")
    comp.add_argument("--instance", help="Explicit standalone instance JSON. Prefer --instance-id for canonical CGX instances.")
    comp.add_argument("--instance-population", help="Optional alternate instance-population JSON; canonical Git mirror is the default.")
    comp.add_argument("--simulation")
    comp.add_argument("--overrides")
    comp.add_argument("--horizon", default="H-TERR-SITE")
    comp.add_argument("--required-scope", action="append", default=[])
    comp.add_argument("--process-condition", action="append", default=[])
    comp.add_argument("--build-id")
    comp.add_argument("--output")

    gc = sub.add_parser("gcode")
    gc.add_argument("--toolpath", required=True)
    gc.add_argument("--machine", required=True)
    gc.add_argument("--output")

    args = ap.parse_args()
    if args.cmd == "component":
        atlas = load_default_atlas()
        explicit_instance = load_optional(args.instance)
        if args.instance_id:
            if explicit_instance is not None:
                raise SystemExit("--instance-id and --instance cannot be used together")
            population = load_optional(args.instance_population) or load_default_instance_population()
            explicit_instance = find_instance(population, args.instance_id)
            archetype_id = explicit_instance.get("archetype_id", "")
            if not archetype_id.startswith("CGA-"):
                raise SystemExit(f"instance {args.instance_id} does not resolve to a single CGA archetype: {archetype_id}")
            record = find_archetype(atlas, archetype_id)
        else:
            record = find_archetype(atlas, args.archetype)
        out = compile_component(
            record,
            instance=explicit_instance,
            simulation=load_optional(args.simulation),
            build_id=args.build_id,
            horizon=args.horizon,
            required_scopes=args.required_scope,
            process_conditions=args.process_condition,
            parameter_overrides=load_optional(args.overrides),
        )
        write_output(out, args.output)
    else:
        out = emit_reference_gcode(load_optional(args.toolpath), load_optional(args.machine))
        write_output(out, args.output)


if __name__ == "__main__":
    main()