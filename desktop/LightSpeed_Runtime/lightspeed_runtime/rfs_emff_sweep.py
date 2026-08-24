from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import shutil
import struct
import tempfile
from typing import Any, Mapping, Sequence
import zlib


REQUEST_SCHEMA = "lightspeed-rfs-emff-sweep-request-v1"
RESULT_SCHEMA = "lightspeed-rfs-emff-sweep-result-v1"
MANIFEST_SCHEMA = "lightspeed-rfs-emff-sweep-manifest-v1"
MODEL_VERSION = "rfs-emff-first-order-screening-v1"
EVIDENCE_CLASS = "derived_screening"
COMPARISON_STATUS = "comparison_blocked"
CLAIM_CONTROLS = {
    "extraction_rate_allowed": False,
    "purity_allowed": False,
    "optimal_frequency_allowed": False,
    "energy_efficiency_allowed": False,
    "equipment_safety_allowed": False,
}

MAX_REQUEST_BYTES = 64 * 1024
MAX_AXES = 4
MAX_AXIS_VALUES = 32
MAX_CASES = 256
MAX_SOURCE_REFS = 32

MU0 = 4.0 * math.pi * 1e-7
COMMAND_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,95}$")

REQUIRED_ARTIFACT_NAMES = (
    "results.json",
    "results.csv",
    "screening_sweep.png",
    "METHODS.md",
    "APPENDIX.md",
)

BLOCK_FIELDS: dict[str, dict[str, str]] = {
    "rfs": {
        "frequency_hz": "nonnegative",
        "displacement_amplitude_m": "nonnegative",
        "particle_diameter_m": "positive",
        "particle_density_kg_m3": "positive",
    },
    "emff": {
        "coil_turns": "nonnegative",
        "coil_length_m": "positive",
        "coil_diameter_m": "positive",
        "current_a": "nonnegative",
        "relative_permeability": "positive",
        "particle_susceptibility": "finite",
        "particle_diameter_m": "positive",
        "particle_density_kg_m3": "positive",
        "field_gradient_t_per_m": "finite",
        "grad_b2_t2_per_m": "finite",
    },
    "medium": {
        "dynamic_viscosity_pa_s": "positive",
        "density_kg_m3": "positive",
    },
}

REQUIRED_BLOCK_FIELDS = {
    "rfs": {
        "frequency_hz",
        "displacement_amplitude_m",
        "particle_diameter_m",
        "particle_density_kg_m3",
    },
    "emff": {
        "coil_turns",
        "coil_length_m",
        "current_a",
        "relative_permeability",
        "particle_diameter_m",
        "particle_density_kg_m3",
    },
    "medium": {"dynamic_viscosity_pa_s", "density_kg_m3"},
}

CSV_FIELDS = (
    "case_index",
    "rfs_frequency_hz",
    "rfs_displacement_amplitude_m",
    "rfs_particle_diameter_m",
    "rfs_particle_density_kg_m3",
    "rfs_angular_frequency_rad_s",
    "rfs_acceleration_peak_m_s2",
    "rfs_particle_volume_m3",
    "rfs_particle_mass_kg",
    "rfs_inertial_force_peak_n",
    "emff_coil_turns",
    "emff_coil_length_m",
    "emff_coil_diameter_m",
    "emff_current_a",
    "emff_relative_permeability",
    "emff_particle_susceptibility",
    "emff_particle_diameter_m",
    "emff_particle_density_kg_m3",
    "emff_field_gradient_t_per_m",
    "emff_grad_b2_input_t2_per_m",
    "emff_long_solenoid_field_t",
    "emff_grad_b2_t2_per_m",
    "emff_magnetic_force_linear_susceptibility_n",
    "emff_particle_volume_m3",
    "emff_particle_mass_kg",
    "medium_dynamic_viscosity_pa_s",
    "medium_density_kg_m3",
    "medium_stokes_drag_coefficient_n_s_m",
    "medium_terminal_velocity_screening_m_s",
    "medium_reynolds_number",
    "long_solenoid_aspect_ratio",
    "long_solenoid_screening_pass",
    "stokes_low_re_pass",
    "evidence_class",
    "comparison_status",
)


class SweepValidationError(ValueError):
    """Raised when a sweep request is malformed or exceeds a fixed bound."""


class ReplayConflict(RuntimeError):
    """Raised when an immutable command output cannot be safely replayed."""


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_bytes(path: Path, value: bytes) -> None:
    path.write_bytes(value)


def _write_json(path: Path, value: Any) -> None:
    path.write_bytes(
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


def _number(value: Any, path: str, rule: str) -> float:
    if isinstance(value, bool):
        raise SweepValidationError(f"{path} must be numeric, not boolean")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise SweepValidationError(f"{path} must be numeric") from exc
    if not math.isfinite(numeric):
        raise SweepValidationError(f"{path} must be finite")
    if rule == "positive" and numeric <= 0:
        raise SweepValidationError(f"{path} must be > 0")
    if rule == "nonnegative" and numeric < 0:
        raise SweepValidationError(f"{path} must be >= 0")
    return numeric


def _validate_block(block_name: str, value: Any, *, require_complete: bool) -> dict[str, float]:
    if not isinstance(value, Mapping):
        raise SweepValidationError(f"base_case.{block_name} must be an object")
    unknown = set(value) - set(BLOCK_FIELDS[block_name])
    if unknown:
        raise SweepValidationError(
            f"base_case.{block_name} contains unsupported fields: {', '.join(sorted(unknown))}"
        )
    if require_complete:
        missing = REQUIRED_BLOCK_FIELDS[block_name] - set(value)
        if missing:
            raise SweepValidationError(
                f"base_case.{block_name} is missing: {', '.join(sorted(missing))}"
            )
    return {
        key: _number(raw, f"base_case.{block_name}.{key}", BLOCK_FIELDS[block_name][key])
        for key, raw in value.items()
    }


def _validated_text(value: Any, path: str, *, maximum: int, required: bool = False) -> str:
    if value is None:
        text = ""
    elif isinstance(value, str):
        text = " ".join(value.split()).strip()
    else:
        raise SweepValidationError(f"{path} must be a string")
    if required and not text:
        raise SweepValidationError(f"{path} is required")
    if len(text) > maximum:
        raise SweepValidationError(f"{path} exceeds {maximum} characters")
    return text


def validate_request(request: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize one bounded, derived-only sweep request."""

    if not isinstance(request, Mapping):
        raise SweepValidationError("request must be an object")
    try:
        request_size = len(_canonical_json_bytes(request))
    except (TypeError, ValueError) as exc:
        raise SweepValidationError("request must contain finite JSON values") from exc
    if request_size > MAX_REQUEST_BYTES:
        raise SweepValidationError(f"request exceeds {MAX_REQUEST_BYTES} bytes")

    allowed = {"schema_version", "project_ref", "source_refs", "base_case", "axes"}
    unknown = set(request) - allowed
    if unknown:
        raise SweepValidationError(f"request contains unsupported fields: {', '.join(sorted(unknown))}")
    if request.get("schema_version") != REQUEST_SCHEMA:
        raise SweepValidationError(f"schema_version must be {REQUEST_SCHEMA}")

    project_ref = _validated_text(request.get("project_ref"), "project_ref", maximum=128)
    source_refs_raw = request.get("source_refs", [])
    if not isinstance(source_refs_raw, Sequence) or isinstance(source_refs_raw, (str, bytes)):
        raise SweepValidationError("source_refs must be an array")
    if len(source_refs_raw) > MAX_SOURCE_REFS:
        raise SweepValidationError(f"source_refs exceeds {MAX_SOURCE_REFS} items")
    source_refs = [
        _validated_text(value, f"source_refs[{index}]", maximum=512, required=True)
        for index, value in enumerate(source_refs_raw)
    ]

    base_raw = request.get("base_case")
    if not isinstance(base_raw, Mapping):
        raise SweepValidationError("base_case must be an object")
    unknown_blocks = set(base_raw) - set(BLOCK_FIELDS)
    if unknown_blocks:
        raise SweepValidationError(
            f"base_case contains unsupported blocks: {', '.join(sorted(unknown_blocks))}"
        )
    if not ({"rfs", "emff"} & set(base_raw)):
        raise SweepValidationError("base_case requires rfs or emff")
    if "medium" in base_raw and "emff" not in base_raw:
        raise SweepValidationError("base_case.medium requires base_case.emff")
    base_case = {
        name: _validate_block(name, value, require_complete=False)
        for name, value in base_raw.items()
    }

    axes_raw = request.get("axes")
    if not isinstance(axes_raw, Sequence) or isinstance(axes_raw, (str, bytes)):
        raise SweepValidationError("axes must be an array")
    if not 1 <= len(axes_raw) <= MAX_AXES:
        raise SweepValidationError(f"axes must contain 1-{MAX_AXES} items")

    axes: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    case_count = 1
    for index, raw_axis in enumerate(axes_raw):
        if not isinstance(raw_axis, Mapping):
            raise SweepValidationError(f"axes[{index}] must be an object")
        axis_unknown = set(raw_axis) - {"path", "values"}
        if axis_unknown:
            raise SweepValidationError(
                f"axes[{index}] contains unsupported fields: {', '.join(sorted(axis_unknown))}"
            )
        path = _validated_text(raw_axis.get("path"), f"axes[{index}].path", maximum=96, required=True)
        parts = path.split(".")
        if len(parts) != 2 or parts[0] not in BLOCK_FIELDS or parts[1] not in BLOCK_FIELDS[parts[0]]:
            raise SweepValidationError(f"axes[{index}].path is not a supported scalar input")
        if parts[0] not in base_case:
            raise SweepValidationError(f"axes[{index}].path requires base_case.{parts[0]}")
        if path in seen_paths:
            raise SweepValidationError(f"duplicate sweep axis: {path}")
        seen_paths.add(path)
        values_raw = raw_axis.get("values")
        if not isinstance(values_raw, Sequence) or isinstance(values_raw, (str, bytes)):
            raise SweepValidationError(f"axes[{index}].values must be an array")
        if not 1 <= len(values_raw) <= MAX_AXIS_VALUES:
            raise SweepValidationError(
                f"axes[{index}].values must contain 1-{MAX_AXIS_VALUES} items"
            )
        rule = BLOCK_FIELDS[parts[0]][parts[1]]
        values = [
            _number(value, f"axes[{index}].values[{value_index}]", rule)
            for value_index, value in enumerate(values_raw)
        ]
        case_count *= len(values)
        if case_count > MAX_CASES:
            raise SweepValidationError(f"sweep expands to more than {MAX_CASES} cases")
        axes.append({"path": path, "values": values})

    normalized = {
        "schema_version": REQUEST_SCHEMA,
        "project_ref": project_ref or None,
        "source_refs": source_refs,
        "base_case": base_case,
        "axes": axes,
    }
    # Validate every generated case after axes populate any missing base fields.
    for case in _expand_cases(normalized):
        _validate_complete_case(case)
    return normalized


def validate_sweep_request(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Stable integration alias for the single sweep-request validator."""

    return validate_request(payload)


def _expand_cases(request: Mapping[str, Any]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = [copy.deepcopy(dict(request["base_case"]))]
    for axis in request["axes"]:
        block_name, field_name = str(axis["path"]).split(".", 1)
        expanded: list[dict[str, Any]] = []
        for case in cases:
            for value in axis["values"]:
                candidate = copy.deepcopy(case)
                candidate[block_name][field_name] = value
                expanded.append(candidate)
        cases = expanded
    return cases


def _validate_complete_case(case: Mapping[str, Any]) -> None:
    for block_name, block in case.items():
        _validate_block(block_name, block, require_complete=True)
    emff = case.get("emff") or {}
    if "field_gradient_t_per_m" in emff and "grad_b2_t2_per_m" in emff:
        raise SweepValidationError(
            "emff must supply field_gradient_t_per_m or grad_b2_t2_per_m, not both"
        )


def _calculate_case(case: Mapping[str, Any], case_index: int) -> dict[str, Any]:
    calculations: dict[str, Any] = {}
    applicability: dict[str, Any] = {}

    if "rfs" in case:
        rfs = case["rfs"]
        omega = 2.0 * math.pi * rfs["frequency_hz"]
        acceleration_peak = omega * omega * rfs["displacement_amplitude_m"]
        radius = rfs["particle_diameter_m"] / 2.0
        particle_volume = 4.0 * math.pi * radius**3 / 3.0
        particle_mass = rfs["particle_density_kg_m3"] * particle_volume
        calculations["rfs"] = {
            "angular_frequency_rad_s": omega,
            "acceleration_peak_m_s2": acceleration_peak,
            "particle_volume_m3": particle_volume,
            "particle_mass_kg": particle_mass,
            "inertial_force_peak_n": particle_mass * acceleration_peak,
        }

    magnetic_force = None
    particle_radius = None
    if "emff" in case:
        emff = case["emff"]
        particle_radius = emff["particle_diameter_m"] / 2.0
        particle_volume = 4.0 * math.pi * particle_radius**3 / 3.0
        particle_mass = emff["particle_density_kg_m3"] * particle_volume
        field_t = (
            MU0
            * emff["relative_permeability"]
            * (emff["coil_turns"] / emff["coil_length_m"])
            * emff["current_a"]
        )
        if "grad_b2_t2_per_m" in emff:
            grad_b2 = emff["grad_b2_t2_per_m"]
        else:
            grad_b2 = 2.0 * field_t * emff.get("field_gradient_t_per_m", 0.0)
        magnetic_force = (
            emff.get("particle_susceptibility", 0.0)
            * particle_volume
            * grad_b2
            / (2.0 * MU0)
        )
        calculations["emff"] = {
            "long_solenoid_field_t": field_t,
            "grad_b2_t2_per_m": grad_b2,
            "magnetic_force_linear_susceptibility_n": magnetic_force,
            "particle_volume_m3": particle_volume,
            "particle_mass_kg": particle_mass,
        }
        if "coil_diameter_m" in emff:
            aspect_ratio = emff["coil_length_m"] / emff["coil_diameter_m"]
            applicability["long_solenoid_aspect_ratio"] = aspect_ratio
            applicability["long_solenoid_screening_pass"] = aspect_ratio >= 2.0
        else:
            applicability["long_solenoid_aspect_ratio"] = None
            applicability["long_solenoid_screening_pass"] = False

    if "medium" in case:
        medium = case["medium"]
        if magnetic_force is None or particle_radius is None:
            raise SweepValidationError("medium calculation requires emff")
        diameter = particle_radius * 2.0
        drag_coefficient = 6.0 * math.pi * medium["dynamic_viscosity_pa_s"] * particle_radius
        terminal_velocity = magnetic_force / drag_coefficient
        reynolds = (
            medium["density_kg_m3"]
            * abs(terminal_velocity)
            * diameter
            / medium["dynamic_viscosity_pa_s"]
        )
        calculations["medium"] = {
            "stokes_drag_coefficient_n_s_m": drag_coefficient,
            "terminal_velocity_screening_m_s": terminal_velocity,
            "reynolds_number": reynolds,
        }
        applicability["stokes_low_re_pass"] = reynolds < 0.1

    finite = all(
        math.isfinite(float(value))
        for values in calculations.values()
        for value in values.values()
    )
    if not finite:
        raise SweepValidationError(f"case {case_index} produced a non-finite result")
    return {
        "case_index": case_index,
        "inputs": copy.deepcopy(dict(case)),
        "calculations": calculations,
        "applicability": applicability,
        "evidence_class": EVIDENCE_CLASS,
        "comparison_status": COMPARISON_STATUS,
        "claim_controls": dict(CLAIM_CONTROLS),
    }


def _csv_record(row: Mapping[str, Any]) -> dict[str, Any]:
    inputs = row["inputs"]
    rfs = inputs.get("rfs") or {}
    emff = inputs.get("emff") or {}
    medium = inputs.get("medium") or {}
    rfs_calc = row["calculations"].get("rfs") or {}
    emff_calc = row["calculations"].get("emff") or {}
    medium_calc = row["calculations"].get("medium") or {}
    applicability = row["applicability"]
    return {
        "case_index": row["case_index"],
        **{f"rfs_{key}": value for key, value in rfs.items()},
        **{f"rfs_{key}": value for key, value in rfs_calc.items()},
        **{f"emff_{key}": value for key, value in emff.items()},
        "emff_grad_b2_input_t2_per_m": emff.get("grad_b2_t2_per_m"),
        **{f"emff_{key}": value for key, value in emff_calc.items()},
        **{f"medium_{key}": value for key, value in medium.items()},
        **{f"medium_{key}": value for key, value in medium_calc.items()},
        **applicability,
        "evidence_class": row["evidence_class"],
        "comparison_status": row["comparison_status"],
    }


def _render_csv(rows: Sequence[Mapping[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=list(CSV_FIELDS),
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(_csv_record(row))
    return stream.getvalue().encode("utf-8")


def _first_axis(request: Mapping[str, Any], block_name: str) -> str | None:
    for axis in request["axes"]:
        if str(axis["path"]).startswith(block_name + "."):
            return str(axis["path"])
    return None


_FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "10010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
}


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def _render_png(request: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> bytes:
    """Render a deterministic, dependency-free two-panel screening PNG."""

    width, height = 1200, 640
    pixels = bytearray(bytes((8, 17, 29)) * (width * height))

    def pixel(x: int, y: int, color: tuple[int, int, int]) -> None:
        if 0 <= x < width and 0 <= y < height:
            offset = (y * width + x) * 3
            pixels[offset : offset + 3] = bytes(color)

    def rectangle(
        left: int,
        top: int,
        right: int,
        bottom: int,
        color: tuple[int, int, int],
    ) -> None:
        for y in range(max(0, top), min(height, bottom)):
            start = (y * width + max(0, left)) * 3
            end = (y * width + min(width, right)) * 3
            pixels[start:end] = bytes(color) * max(0, min(width, right) - max(0, left))

    def line(
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        color: tuple[int, int, int],
    ) -> None:
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        error = dx + dy
        while True:
            pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            twice = 2 * error
            if twice >= dy:
                error += dy
                x0 += sx
            if twice <= dx:
                error += dx
                y0 += sy

    def point(cx: int, cy: int, color: tuple[int, int, int]) -> None:
        for y in range(cy - 4, cy + 5):
            for x in range(cx - 4, cx + 5):
                if (x - cx) ** 2 + (y - cy) ** 2 <= 16:
                    pixel(x, y, color)

    def text(x: int, y: int, value: str, color: tuple[int, int, int], scale: int = 2) -> None:
        cursor = x
        for char in value.upper():
            if char == " ":
                cursor += 4 * scale
                continue
            glyph = _FONT.get(char)
            if glyph is None:
                cursor += 6 * scale
                continue
            for row_index, pattern in enumerate(glyph):
                for column_index, active in enumerate(pattern):
                    if active == "1":
                        rectangle(
                            cursor + column_index * scale,
                            y + row_index * scale,
                            cursor + (column_index + 1) * scale,
                            y + (row_index + 1) * scale,
                            color,
                        )
            cursor += 6 * scale

    rectangle(40, 70, 580, 535, (14, 27, 43))
    rectangle(620, 70, 1160, 535, (14, 27, 43))
    text(55, 24, "RFS / EMFF FIRST ORDER SCREENING", (238, 247, 255), 3)

    panel_specs = (
        ("rfs", "inertial_force_peak_n", (93, 228, 199), (40, 70, 550, 500)),
        (
            "emff",
            "magnetic_force_linear_susceptibility_n",
            (138, 180, 255),
            (620, 70, 1130, 500),
        ),
    )
    for block, output_key, color, bounds in panel_specs:
        left, top, right, bottom = bounds
        text(left + 25, top + 18, f"{block} force", (220, 233, 245), 2)
        plot_left, plot_top = left + 55, top + 65
        plot_right, plot_bottom = right - 20, bottom - 20
        for division in range(6):
            x = plot_left + (plot_right - plot_left) * division // 5
            y = plot_top + (plot_bottom - plot_top) * division // 5
            line(x, plot_top, x, plot_bottom, (38, 58, 79))
            line(plot_left, y, plot_right, y, (38, 58, 79))
        line(plot_left, plot_bottom, plot_right, plot_bottom, (157, 177, 199))
        line(plot_left, plot_top, plot_left, plot_bottom, (157, 177, 199))

        axis_path = _first_axis(request, block)
        selected = [row for row in rows if block in row["calculations"]]
        if not selected:
            text(left + 155, top + 215, f"NO {block} INPUTS", (183, 201, 221), 2)
            continue
        if axis_path:
            _, field = axis_path.split(".", 1)
            x_values = [float(row["inputs"][block][field]) for row in selected]
        else:
            x_values = [float(row["case_index"]) for row in selected]
        y_values = [float(row["calculations"][block][output_key]) for row in selected]
        x_min, x_max = min(x_values), max(x_values)
        y_min, y_max = min(y_values), max(y_values)
        x_span = x_max - x_min
        y_span = y_max - y_min
        for x_value, y_value in zip(x_values, y_values):
            x_fraction = 0.5 if x_span == 0 else (x_value - x_min) / x_span
            y_fraction = 0.5 if y_span == 0 else (y_value - y_min) / y_span
            x = round(plot_left + x_fraction * (plot_right - plot_left))
            y = round(plot_bottom - y_fraction * (plot_bottom - plot_top))
            point(x, y, color)

    rectangle(0, 570, width, height, (35, 30, 25))
    text(
        130,
        590,
        "DERIVED SCREENING - NOT EMPIRICAL - COMPARISON BLOCKED",
        (245, 196, 107),
        2,
    )
    raw = b"".join(
        b"\x00" + bytes(pixels[y * width * 3 : (y + 1) * width * 3])
        for y in range(height)
    )
    description = (
        b"Description\x00RFS and EMFF scalar force screening; derived, not empirical, "
        b"comparison blocked"
    )
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _png_chunk(b"tEXt", description)
        + _png_chunk(b"IDAT", zlib.compress(raw, level=9))
        + _png_chunk(b"IEND", b"")
    )


def _methods_text() -> str:
    return """# RFS / EMFF Sweep Methods

Evidence class: **derived screening**. Comparison state: **comparison blocked**.

This bounded scalar model does not establish extraction rate, purity, an optimal
frequency, energy efficiency, equipment safety, or physical-system capability.
It does not write to a workbook, dataset catalog, Drive surface, or public site.

## RFS first-order relations

- Angular frequency: `omega = 2*pi*f` (rad/s)
- Peak sinusoidal acceleration: `a_peak = omega^2*A` (m/s^2)
- Spherical particle volume: `V = 4*pi*(d/2)^3/3` (m^3)
- Particle mass: `m = rho*V` (kg)
- Peak inertial force: `F_inertial = m*a_peak` (N)

## EMFF first-order relations

- Long-solenoid field: `B = mu0*mu_r*(N/L)*I` (T)
- If a field gradient is supplied: `grad(B^2) = 2*B*grad(B)` (T^2/m)
- Linear-susceptibility force: `F_mag = chi*V*grad(B^2)/(2*mu0)` (N)

The long-solenoid applicability screen passes only when `L/diameter >= 2`.

## Optional medium screen

- Stokes drag coefficient: `c = 6*pi*eta*r` (N*s/m)
- Terminal-velocity screen: `v = F_mag/c` (m/s)
- Reynolds number: `Re = rho_medium*abs(v)*d/eta`

The Stokes applicability screen passes only when `Re < 0.1`. These relations are
first-order calculations under their stated assumptions, not empirical proof.
"""


def _appendix_text(request: Mapping[str, Any], request_sha256: str, row_count: int) -> str:
    rendered_request = json.dumps(request, ensure_ascii=False, indent=2, sort_keys=True)
    return f"""# RFS / EMFF Sweep Appendix

- Request SHA-256: `{request_sha256}`
- Model version: `{MODEL_VERSION}`
- Case count: `{row_count}` (hard limit `{MAX_CASES}`)
- Row ordering: deterministic Cartesian expansion in the supplied axis order;
  the final axis changes fastest.
- Dataset role: `derived`
- Validation state: `{COMPARISON_STATUS}`
- Automatic canonical promotion: `false`

## Normalized request

```json
{rendered_request}
```

## Output contract

`results.json` preserves nested inputs and calculations. `results.csv` provides
the same cases as fixed unit-bearing columns. `screening_sweep.png` visualizes
only the first scalar axis for each available force family and does not select
or claim an optimum.
"""


def _run_name(command_id: str) -> str:
    if not isinstance(command_id, str) or not COMMAND_ID_PATTERN.fullmatch(command_id):
        raise SweepValidationError(
            "command_id must use 1-96 ASCII letters, digits, dot, underscore, colon, or hyphen"
        )
    lexical = re.sub(r"[^A-Za-z0-9._-]+", "_", command_id).strip("._-") or "command"
    digest = hashlib.sha256(command_id.encode("ascii")).hexdigest()[:12]
    return f"{lexical[:64]}-{digest}"


def _artifact_entry(path: Path, media_type: str) -> dict[str, Any]:
    return {
        "name": path.name,
        "media_type": media_type,
        "size_bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
    }


def _validate_replay(
    run_dir: Path,
    *,
    command_id: str,
    request_sha256: str,
) -> dict[str, Any]:
    if run_dir.is_symlink() or not run_dir.is_dir():
        raise ReplayConflict(f"immutable run destination is not a regular directory: {run_dir}")
    manifest_path = run_dir / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReplayConflict("immutable run destination has no valid manifest") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != MANIFEST_SCHEMA:
        raise ReplayConflict("immutable run manifest schema does not match")
    if manifest.get("command_id") != command_id or manifest.get("request_sha256") != request_sha256:
        raise ReplayConflict("command_id already identifies different sweep content")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or {item.get("name") for item in artifacts if isinstance(item, dict)} != set(
        REQUIRED_ARTIFACT_NAMES
    ):
        raise ReplayConflict("immutable run manifest does not contain the required artifact set")
    for item in artifacts:
        name = str(item.get("name") or "")
        path = run_dir / name
        if path.parent != run_dir or not path.is_file():
            raise ReplayConflict(f"immutable artifact is missing: {name}")
        if path.stat().st_size != item.get("size_bytes") or _sha256_file(path) != item.get("sha256"):
            raise ReplayConflict(f"immutable artifact hash mismatch: {name}")
    return {
        "status": "completed",
        "idempotent_replay": True,
        "command_id": command_id,
        "request_sha256": request_sha256,
        "run_dir": str(run_dir),
        "manifest_path": str(manifest_path),
        "manifest_sha256": _sha256_file(manifest_path),
        "row_count": manifest.get("row_count"),
        "artifacts": artifacts,
        "artifact_paths": [str(run_dir / item["name"]) for item in artifacts],
        "evidence_class": EVIDENCE_CLASS,
        "comparison_status": COMPARISON_STATUS,
        "claim_controls": dict(CLAIM_CONTROLS),
        "automatic_workbook_write": False,
        "automatic_dataset_catalog_write": False,
        "drive_write_executed": False,
        "public_publish_authorized": False,
    }


def run_sweep(
    request: Mapping[str, Any],
    *,
    command_id: str,
    output_root: Path | str,
) -> dict[str, Any]:
    """Run one bounded immutable RFS/EMFF scalar sweep.

    The caller supplies a local output root. The final child directory is
    deterministic from ``command_id``. No database, queue, workbook, catalog,
    Drive, or public surface is read or written.
    """

    normalized = validate_request(request)
    request_sha256 = _sha256_bytes(_canonical_json_bytes(normalized))
    run_name = _run_name(command_id)
    base_root = Path(output_root).absolute()
    base_root.mkdir(parents=True, exist_ok=True)
    if not base_root.is_dir() or base_root.is_symlink():
        raise SweepValidationError("output_root must be a regular local directory")
    run_dir = base_root / run_name
    if run_dir.exists() or run_dir.is_symlink():
        return _validate_replay(
            run_dir,
            command_id=command_id,
            request_sha256=request_sha256,
        )

    partial = Path(tempfile.mkdtemp(prefix=f".partial-{run_name}-", dir=base_root))
    try:
        cases = _expand_cases(normalized)
        rows = [_calculate_case(case, index) for index, case in enumerate(cases, start=1)]
        results = {
            "schema_version": RESULT_SCHEMA,
            "command_id": command_id,
            "request_sha256": request_sha256,
            "model_version": MODEL_VERSION,
            "evidence_class": EVIDENCE_CLASS,
            "comparison_status": COMPARISON_STATUS,
            "project_ref": normalized["project_ref"],
            "source_refs": normalized["source_refs"],
            "axes": normalized["axes"],
            "row_count": len(rows),
            "rows": rows,
            "claim_controls": dict(CLAIM_CONTROLS),
        }
        _write_json(partial / "results.json", results)
        _write_bytes(partial / "results.csv", _render_csv(rows))
        _write_bytes(partial / "screening_sweep.png", _render_png(normalized, rows))
        _write_bytes(partial / "METHODS.md", _methods_text().encode("utf-8"))
        _write_bytes(
            partial / "APPENDIX.md",
            _appendix_text(normalized, request_sha256, len(rows)).encode("utf-8"),
        )

        media_types = {
            "results.json": "application/json",
            "results.csv": "text/csv",
            "screening_sweep.png": "image/png",
            "METHODS.md": "text/markdown",
            "APPENDIX.md": "text/markdown",
        }
        artifacts = [
            _artifact_entry(partial / name, media_types[name])
            for name in REQUIRED_ARTIFACT_NAMES
        ]
        manifest = {
            "schema_version": MANIFEST_SCHEMA,
            "command_id": command_id,
            "request_schema_version": REQUEST_SCHEMA,
            "request_sha256": request_sha256,
            "model_version": MODEL_VERSION,
            "run_directory": run_name,
            "row_count": len(rows),
            "case_limit": MAX_CASES,
            "evidence_class": EVIDENCE_CLASS,
            "canonical_role": "derived",
            "validation_state": COMPARISON_STATUS,
            "comparison_status": COMPARISON_STATUS,
            "review_required": True,
            "source_mutated": False,
            "automatic_workbook_write": False,
            "automatic_dataset_catalog_write": False,
            "drive_write_executed": False,
            "public_publish_authorized": False,
            "claim_controls": results["claim_controls"],
            "dataset_catalog_candidate": {
                "owner_floor": "TheConstruct",
                "role": "derived",
                "scientific_role": "rfs_emff_screening",
                "validation_state": COMPARISON_STATUS,
                "automatic_registration": False,
            },
            "artifacts": artifacts,
            "manifest_self_hash": "reported_out_of_band_to_avoid_self_reference",
        }
        _write_json(partial / "manifest.json", manifest)
        try:
            partial.replace(run_dir)
        except FileExistsError:
            shutil.rmtree(partial)
            return _validate_replay(
                run_dir,
                command_id=command_id,
                request_sha256=request_sha256,
            )
    except Exception:
        if partial.exists():
            shutil.rmtree(partial)
        raise

    return {
        "status": "completed",
        "idempotent_replay": False,
        "command_id": command_id,
        "request_sha256": request_sha256,
        "run_dir": str(run_dir),
        "manifest_path": str(run_dir / "manifest.json"),
        "manifest_sha256": _sha256_file(run_dir / "manifest.json"),
        "row_count": len(rows),
        "artifacts": artifacts,
        "artifact_paths": [str(run_dir / item["name"]) for item in artifacts],
        "evidence_class": EVIDENCE_CLASS,
        "comparison_status": COMPARISON_STATUS,
        "claim_controls": dict(CLAIM_CONTROLS),
        "automatic_workbook_write": False,
        "automatic_dataset_catalog_write": False,
        "drive_write_executed": False,
        "public_publish_authorized": False,
    }


def execute_sweep(
    action_payload: Mapping[str, Any],
    *,
    task_id: Any,
    job_id: Any,
    shell_root: Path | str,
    allow_heavy: bool = False,
    command_id: str | None = None,
) -> dict[str, Any]:
    """Consumer-compatible wrapper around the bounded immutable executor.

    ``command_id`` should be supplied by the typed LS GO consumer. The job-based
    fallback keeps the wrapper directly callable during integration without
    adding transport identity fields to the strict action-payload schema.
    """

    if allow_heavy is not False:
        raise SweepValidationError("rfs_emff_sweep does not permit heavy execution")
    if isinstance(job_id, bool):
        raise SweepValidationError("job_id must be a positive integer")
    try:
        normalized_job_id = int(job_id)
    except (TypeError, ValueError) as exc:
        raise SweepValidationError("job_id must be a positive integer") from exc
    if normalized_job_id <= 0:
        raise SweepValidationError("job_id must be a positive integer")
    normalized_task_id = _validated_text(
        str(task_id) if task_id is not None else None,
        "task_id",
        maximum=96,
        required=True,
    )
    execution_id = command_id or f"LSGO-JOB-{normalized_job_id}"
    output_root = (
        Path(shell_root).absolute()
        / "Z Axis"
        / "Z0_TheConstruct"
        / "data"
        / "labs"
        / "rfs_emff"
        / "runs"
    )
    result = run_sweep(
        action_payload,
        command_id=execution_id,
        output_root=output_root,
    )
    return {
        **result,
        "task_id": normalized_task_id,
        "job_id": normalized_job_id,
        "shell_root": str(Path(shell_root).absolute()),
        "allow_heavy": False,
    }
