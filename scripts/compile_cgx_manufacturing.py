#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cgx.manufacturing import (
    compile_component,
    compile_printable_catalogue,
    compile_printable_component,
    compile_printable_stack,
    emit_reference_gcode,
    find_archetype,
    find_instance,
    load_default_atlas,
    load_default_instance_population,
    resolve_binding_gate,
    resolve_binding_queue,
    validate_lot_passport,
    validate_tool_manifest,
    create_witness_coupon_packet,
)


def load_optional(path: str | None):
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_output(value, path: str | None) -> None:
    if isinstance(value, str):
        text = value
    elif path:
        text = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    else:
        # Keep CLI/stdout JSON portable across Windows console code pages while
        # preserving Unicode semantics via JSON escapes. File outputs remain UTF-8.
        text = json.dumps(value, indent=2, ensure_ascii=True) + "\n"
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


    pcomp = sub.add_parser("printable-component")
    pselector = pcomp.add_mutually_exclusive_group(required=True)
    pselector.add_argument("--archetype", help="CGA ID or unique component-archetype substring")
    pselector.add_argument("--instance-id", help="CGXI instance ID from the canonical component instance population")
    pcomp.add_argument("--instance-population")
    pcomp.add_argument("--simulation")
    pcomp.add_argument("--overrides")
    pcomp.add_argument("--horizon", default="H-TERR-SITE")
    pcomp.add_argument("--required-scope", action="append", default=[])
    pcomp.add_argument("--process-condition", action="append", default=[])
    pcomp.add_argument("--build-id")
    pcomp.add_argument("--output")

    pcat = sub.add_parser("printable-catalogue")
    pcat.add_argument("--output")

    pstack = sub.add_parser("printable-stack")
    pstack.add_argument("--spec", required=True, help="JSON spec with stack_id, components and optional relations/horizon")
    pstack.add_argument("--instance-population")
    pstack.add_argument("--output")

    bind = sub.add_parser("binding")
    bind.add_argument("--instance-id")
    bind.add_argument("--queue", action="store_true")
    bind.add_argument("--instance-population")
    bind.add_argument("--output")

    lot = sub.add_parser("lot-passport")
    lot.add_argument("--passport", required=True)
    lot.add_argument("--output")

    tool = sub.add_parser("tool-manifest")
    tool.add_argument("--manifest", required=True)
    tool.add_argument("--output")

    coupon = sub.add_parser("witness-packet")
    coupon.add_argument("--instance-id", required=True)
    coupon.add_argument("--instance-population")
    coupon.add_argument("--geometry")
    coupon.add_argument("--lot-refs")
    coupon.add_argument("--process")
    coupon.add_argument("--tool-manifest", action="append", default=[])
    coupon.add_argument("--measurement-method")
    coupon.add_argument("--output")

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
    elif args.cmd == "printable-component":
        atlas = load_default_atlas()
        population = load_optional(args.instance_population) or load_default_instance_population()
        instance = None
        if args.instance_id:
            instance = find_instance(population, args.instance_id)
            archetype_id = instance.get("archetype_id", "")
            if not archetype_id.startswith("CGA-"):
                raise SystemExit(f"instance {args.instance_id} does not resolve to a single CGA archetype: {archetype_id}")
            record = find_archetype(atlas, archetype_id)
        else:
            record = find_archetype(atlas, args.archetype)
        out = compile_printable_component(
            record,
            instance=instance,
            simulation=load_optional(args.simulation),
            build_id=args.build_id,
            horizon=args.horizon,
            required_scopes=args.required_scope,
            process_conditions=args.process_condition,
            parameter_overrides=load_optional(args.overrides),
        )
        write_output(out, args.output)
    elif args.cmd == "printable-catalogue":
        write_output(compile_printable_catalogue(load_default_atlas()), args.output)
    elif args.cmd == "printable-stack":
        spec = load_optional(args.spec)
        atlas = load_default_atlas()
        population = load_optional(args.instance_population) or load_default_instance_population()
        component_specs = []
        for index, item in enumerate(spec.get("components", []), start=1):
            instance = None
            if item.get("instance_id"):
                instance = find_instance(population, item["instance_id"])
                record = find_archetype(atlas, instance["archetype_id"])
            elif item.get("archetype"):
                record = find_archetype(atlas, item["archetype"])
            else:
                raise SystemExit(f"printable-stack component {index} requires archetype or instance_id")
            component_specs.append(
                {
                    "record": record,
                    "instance": instance,
                    "build_id": item.get("build_id"),
                    "horizon": item.get("horizon", spec.get("horizon", "H-TERR-SITE")),
                    "required_scopes": item.get("required_scopes"),
                    "process_conditions": item.get("process_conditions"),
                    "parameter_overrides": item.get("parameter_overrides"),
                    "simulation": item.get("simulation"),
                }
            )
        stack_id = spec.get("stack_id")
        if not stack_id:
            raise SystemExit("printable-stack spec requires stack_id")
        out = compile_printable_stack(
            component_specs,
            stack_id=stack_id,
            relations=spec.get("relations"),
            horizon=spec.get("horizon", "H-TERR-SITE"),
        )
        write_output(out, args.output)
    elif args.cmd == "binding":
        population = load_optional(args.instance_population) or load_default_instance_population()
        if args.queue:
            out = resolve_binding_queue(population)
        else:
            if not args.instance_id:
                raise SystemExit("binding requires --instance-id or --queue")
            out = resolve_binding_gate(find_instance(population, args.instance_id), population=population)
        write_output(out, args.output)
    elif args.cmd == "lot-passport":
        write_output(validate_lot_passport(load_optional(args.passport)), args.output)
    elif args.cmd == "tool-manifest":
        write_output(validate_tool_manifest(load_optional(args.manifest)), args.output)
    elif args.cmd == "witness-packet":
        population = load_optional(args.instance_population) or load_default_instance_population()
        instance = find_instance(population, args.instance_id)
        lot_refs_payload = load_optional(args.lot_refs) if args.lot_refs else []
        if isinstance(lot_refs_payload, dict):
            lot_refs_payload = lot_refs_payload.get("lot_refs", [])
        tools = [load_optional(p) for p in args.tool_manifest]
        out = create_witness_coupon_packet(
            instance,
            geometry=load_optional(args.geometry),
            lot_refs=lot_refs_payload,
            process=load_optional(args.process),
            tool_manifests=tools,
            measurement_method=load_optional(args.measurement_method),
        )
        write_output(out, args.output)
    else:
        out = emit_reference_gcode(load_optional(args.toolpath), load_optional(args.machine))
        write_output(out, args.output)


if __name__ == "__main__":
    main()