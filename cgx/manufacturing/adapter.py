from __future__ import annotations

import math
from typing import Any


class AdapterError(ValueError):
    pass


def _f(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise AdapterError(f"invalid-number:{value}") from exc
    if not math.isfinite(number):
        raise AdapterError(f"nonfinite-number:{value}")
    return number


def _range_bounds(value: Any, label: str) -> tuple[float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise AdapterError(f"invalid-range:{label}")
    lo, hi = _f(value[0]), _f(value[1])
    if lo > hi:
        raise AdapterError(f"invalid-range:{label}:{lo}>{hi}")
    return lo, hi


def _nonnegative_int(value: Any, label: str) -> int:
    number = _f(value)
    if number < 0 or not number.is_integer():
        raise AdapterError(f"invalid-integer:{label}:{number}")
    return int(number)


def _check_xyz(params: dict[str, Any], workspace: dict[str, list[float]]) -> None:
    for axis in ("x", "y", "z"):
        if axis not in params:
            continue
        value = _f(params[axis])
        lo, hi = _range_bounds(workspace[axis], f"workspace-{axis}")
        if not (lo <= value <= hi):
            raise AdapterError(f"workspace-exceeded:{axis}:{value}")


def emit_reference_gcode(toolpath_packet: dict[str, Any], machine_manifest: dict[str, Any]) -> str:
    """Emit a reference Cartesian G-code dialect from a fully bound dry-run packet.

    This adapter never runs the program. It fails closed unless the caller supplies
    BUILD_READY state, matching machine/calibration identity, supported opcodes and
    a validated dry-run. It is intentionally small and configuration-specific.
    """
    if toolpath_packet.get("schema") != "CGX-TOOLPATH/0.1":
        raise AdapterError("unsupported-toolpath-schema")
    if toolpath_packet.get("execution_state") != "BUILD_READY":
        raise AdapterError("build-not-ready")
    if toolpath_packet.get("dry_run_validated") is not True:
        raise AdapterError("dry-run-not-validated")
    if toolpath_packet.get("machine_id") != machine_manifest.get("machine_id"):
        raise AdapterError("machine-id-mismatch")
    if toolpath_packet.get("calibration_hash") != machine_manifest.get("calibration_hash"):
        raise AdapterError("calibration-hash-mismatch")

    supported = set(machine_manifest.get("supported_ops", []))
    workspace = machine_manifest.get("workspace_mm")
    if not workspace or any(axis not in workspace for axis in ("x", "y", "z")):
        raise AdapterError("workspace-not-declared")
    max_feed = _f(machine_manifest.get("max_feed_mm_min", 0))
    if max_feed <= 0:
        raise AdapterError("invalid-max-feed")

    lines = [
        "; CGX reference adapter output - review before any authorised execution",
        f"; machine={machine_manifest['machine_id']}",
        f"; calibration={machine_manifest['calibration_hash']}",
        "G21 ; millimetres",
        "G90 ; absolute coordinates",
    ]
    for index, op in enumerate(toolpath_packet.get("operations", []), start=1):
        opcode = op.get("opcode")
        if opcode not in supported:
            raise AdapterError(f"unsupported-op:{opcode}")
        p = op.get("params", {})
        _check_xyz(p, workspace)
        if opcode == "TOOL_SELECT":
            lines.append(f"T{_nonnegative_int(p['tool'], 'tool')}")
        elif opcode == "MOVE":
            feed = _f(p.get("feed_mm_min", max_feed))
            if feed <= 0 or feed > max_feed:
                raise AdapterError(f"feed-out-of-range:{feed}")
            axes = " ".join(f"{a.upper()}{_f(p[a]):.4f}" for a in ("x", "y", "z") if a in p)
            lines.append(f"G0 {axes} F{feed:.3f}".strip())
        elif opcode == "DEPOSIT_LINE":
            feed = _f(p["feed_mm_min"])
            if feed <= 0 or feed > max_feed:
                raise AdapterError(f"feed-out-of-range:{feed}")
            axes = " ".join(f"{a.upper()}{_f(p[a]):.4f}" for a in ("x", "y", "z") if a in p)
            e = _f(p["e"])
            lines.append(f"G1 {axes} E{e:.5f} F{feed:.3f}".strip())
        elif opcode == "DWELL":
            ms = _nonnegative_int(p["milliseconds"], "dwell-milliseconds")
            lines.append(f"G4 P{ms}")
        elif opcode == "SET_TOOL_TEMP":
            temp = _f(p["celsius"])
            lo, hi = _range_bounds(machine_manifest.get("tool_temperature_c"), "tool-temperature")
            if not (lo <= temp <= hi):
                raise AdapterError(f"temperature-out-of-range:{temp}")
            lines.append(f"M104 S{temp:.2f}")
        elif opcode == "WAIT_TOOL_TEMP":
            temp = _f(p["celsius"])
            lo, hi = _range_bounds(machine_manifest.get("tool_temperature_c"), "tool-temperature")
            if not (lo <= temp <= hi):
                raise AdapterError(f"temperature-out-of-range:{temp}")
            lines.append(f"M109 S{temp:.2f}")
        else:
            raise AdapterError(f"unimplemented-op:{opcode}")
        lines.append(f"; cgx-op-index={index}")
    lines.append("M400 ; wait for queued moves")
    lines.append("; END CGX reference adapter output")
    return "\n".join(lines) + "\n"
