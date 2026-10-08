#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cgx.manufacturing import compile_component, emit_reference_gcode, find_archetype, load_default_atlas


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
    comp.add_argument("--archetype", required=True, help="CGA ID or unique component-archetype substring")
    comp.add_argument("--instance")
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
        record = find_archetype(atlas, args.archetype)
        out = compile_component(
            record,
            instance=load_optional(args.instance),
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
