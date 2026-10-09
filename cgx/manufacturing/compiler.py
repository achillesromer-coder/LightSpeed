from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .volumetric import resolve_volumetric_topology

ROOT = Path(__file__).resolve().parents[2]
ATLAS_PATH = ROOT / "cgx" / "component_atlas" / "component_geometry_atlas_v0_1.json"
INSTANCE_POPULATION_PATH = ROOT / "cgx" / "component_atlas" / "component_instance_population_v0_1.json"

SCHEMA = "CGX-MANUFACTURING-IR/0.1"
RECIPE_SCHEMA = "CGX-MANUFACTURING-RECIPE/0.1"
KNOWN_OPTIONAL_SCOPES = {
    "electrical",
    "thermal",
    "em_field",
    "electric_field",
    "optical",
    "mechanical",
    "chemical",
    "fluid",
    "pressure",
    "gravity",
    "radiation",
    "humidity_moisture",
    "esd",
    "cleanliness",
    "spatial_coupling",
}
ALWAYS_SCOPES = {
    "geometry": "Geometry/tolerances are required to manufacture or place the article.",
    "material": "Material/lot/passport state can change process feasibility and acceptance.",
    "process": "Directional process/assembly history is required for evidence and damage checks.",
    "process_environment": "The actual process environment must be declared even when no environment solver is needed.",
    "metrology": "Acceptance/readback requires a declared measurement/calibration path.",
    "provenance": "Source/revision/hash lineage is required for CGX/DBR traceability.",
}

SPACE_HORIZONS = {"ORBIT", "LUNAR", "ASTEROID", "INTERPLANETARY", "INTERSTELLAR"}

DOMAIN_BASE_SCOPES: dict[str, set[str]] = {
    "Electrical": {"electrical"},
    "Electrical/Packaging": {"electrical", "mechanical"},
    "Semiconductor": {"electrical", "thermal", "esd", "cleanliness"},
    "Power/Control": {"electrical", "thermal", "esd"},
    "Protection/Switching": {"electrical", "thermal"},
    "Electromagnetic": {"electrical", "em_field", "thermal"},
    "RF/Communications": {"electrical", "em_field", "spatial_coupling"},
    "Optical/Display": {"optical", "cleanliness"},
    "Sensing": set(),
    "Actuation": {"mechanical"},
    "Mechanical": {"mechanical"},
    "Fluid/Thermal": {"fluid"},
    "Energy": {"electrical", "thermal"},
    "Electrochemical/Chemical": {"electrical", "chemical", "thermal", "humidity_moisture"},
    "Acoustic/Ultrasonic": {"mechanical"},
}

RECIPE_OPS: dict[str, list[tuple[str, str, str | None]]] = {
    "HYBRID_SEED": [
        ("VERIFY_SEED", "HYBRID", None),
        ("PREP_CARRIER", "STRUCT", "VERIFY_SEED"),
        ("FORM_CARRIER_INTERCONNECT", "FUNC", "PREP_CARRIER"),
        ("PLACE_SEED", "HYBRID", "FORM_CARRIER_INTERCONNECT"),
        ("JOIN", "HYBRID", "PLACE_SEED"),
        ("INSPECT", "METRO", "JOIN"),
        ("FUNCTION_TEST", "METRO", "INSPECT"),
        ("ENROL_OBJECT", "METRO", "FUNCTION_TEST"),
    ],
    "PRINTED_FUNCTIONAL": [
        ("PREP_SUBSTRATE", "FUNC", None),
        ("DEPOSIT_PLACE_FUNCTIONAL", "FUNC", "PREP_SUBSTRATE"),
        ("ACTIVATE_CURE_IF_REQUIRED", "FUNC", "DEPOSIT_PLACE_FUNCTIONAL"),
        ("INSPECT", "METRO", "ACTIVATE_CURE_IF_REQUIRED"),
        ("FUNCTION_TEST", "METRO", "INSPECT"),
        ("ENCAPSULATE_IF_QUALIFIED", "FUNC", "FUNCTION_TEST"),
    ],
    "STRUCTURAL_FORM": [
        ("PREP_FEED_FIXTURE", "STRUCT", None),
        ("DEPOSIT_FORM_STRUCTURE", "STRUCT", "PREP_FEED_FIXTURE"),
        ("IN_PROCESS_INSPECT", "METRO", "DEPOSIT_FORM_STRUCTURE"),
        ("FINISH_IF_REQUIRED", "STRUCT", "IN_PROCESS_INSPECT"),
        ("FUNCTION_TEST", "METRO", "FINISH_IF_REQUIRED"),
    ],
    "FLUIDIC_PROCESS": [
        ("PREP_MATERIAL_SEAL", "STRUCT", None),
        ("FORM_CHANNEL_BODY", "STRUCT", "PREP_MATERIAL_SEAL"),
        ("JOIN_SEAL_IF_REQUIRED", "HYBRID", "FORM_CHANNEL_BODY"),
        ("INSPECT", "METRO", "JOIN_SEAL_IF_REQUIRED"),
        ("LEAK_FLOW_FUNCTION_TEST", "METRO", "INSPECT"),
    ],
    "ELECTROCHEMICAL_PROCESS": [
        ("PREP_CONTAINMENT_SUBSTRATE", "STRUCT", None),
        ("PLACE_DEPOSIT_ELECTRODES", "FUNC", "PREP_CONTAINMENT_SUBSTRATE"),
        ("PLACE_SEPARATOR_ELECTROLYTE", "FUNC", "PLACE_DEPOSIT_ELECTRODES"),
        ("SEAL", "HYBRID", "PLACE_SEPARATOR_ELECTROLYTE"),
        ("INSPECT", "METRO", "SEAL"),
        ("ELECTROCHEMICAL_TEST", "METRO", "INSPECT"),
    ],
    "ARCHETYPE_ONLY": [
        ("BIND_SOURCE_GEOMETRY_MATERIAL_PROCESS", "METRO", None),
        ("DEFINE_TEST_AND_FALSIFIER", "METRO", "BIND_SOURCE_GEOMETRY_MATERIAL_PROCESS"),
    ],
}


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _slug(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip())
    return value.strip("-").lower() or "unnamed"


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_default_atlas() -> dict[str, Any]:
    return json.loads(ATLAS_PATH.read_text(encoding="utf-8"))


def load_default_instance_population() -> dict[str, Any]:
    return json.loads(INSTANCE_POPULATION_PATH.read_text(encoding="utf-8"))


def find_instance(population: dict[str, Any], query: str) -> dict[str, Any]:
    exact = [r for r in population["records"] if r.get("instance_id") == query]
    if exact:
        return exact[0]
    q = _norm(query)
    matches = [
        r for r in population["records"]
        if q in _norm(r.get("instance_id"))
        or q in _norm(r.get("archetype_id"))
        or q in _norm(r.get("geometry_source_type"))
    ]
    if not matches:
        raise KeyError(f"instance-not-found:{query}")
    if len(matches) != 1:
        raise KeyError(f"instance-ambiguous:{query}:{','.join(r['instance_id'] for r in matches[:12])}")
    return matches[0]


def _instance_binding_progress(instance: dict[str, Any] | None) -> str:
    if not instance:
        return "ARCHETYPE_ONLY"
    if instance.get("binding_state") == "BUILD_READY":
        return "BUILD_READY"
    evidence = str(instance.get("evidence_ceiling", "")).upper()
    source_auth = str(instance.get("exact_source_authority", "")).upper()
    source_locator = str(instance.get("source_locator_or_hash", "")).upper()
    if "SOURCE-CANDIDATE BOUND" in evidence or source_auth.startswith("ATTRIBUTABLE CANDIDATE SOURCES BOUND"):
        return "SOURCE_CANDIDATE_BOUND"
    if source_locator and "UNRESOLVED" not in source_locator and "NOT SELECTED" not in source_locator and "NOT YET BOUND" not in source_locator:
        return "SOURCE_IDENTIFIED"
    return "UNBOUND"


def find_archetype(atlas: dict[str, Any], query: str) -> dict[str, Any]:
    exact = [r for r in atlas["records"] if r.get("ID") == query]
    if exact:
        return exact[0]
    q = _norm(query)
    matches = [r for r in atlas["records"] if q in _norm(r.get("Component Archetype"))]
    if not matches:
        raise KeyError(f"archetype-not-found:{query}")
    if len(matches) > 1:
        exact_name = [r for r in matches if _norm(r.get("Component Archetype")) == q]
        if len(exact_name) == 1:
            return exact_name[0]
        raise KeyError(f"archetype-ambiguous:{query}:{','.join(r['ID'] for r in matches[:12])}")
    return matches[0]


def classify_process_strategy(record: dict[str, Any]) -> str:
    domain = record.get("Domain", "")
    build_class = _norm(record.get("Current CGX Build Class"))
    route = _norm(record.get("Current Manufacturing Route"))
    name = _norm(record.get("Component Archetype"))

    if "insert-seed" in build_class or "seed " in route or route.startswith("seed"):
        return "HYBRID_SEED"
    if domain == "Electrochemical/Chemical":
        return "ELECTROCHEMICAL_PROCESS"
    if domain == "Fluid/Thermal" and any(k in name for k in ("channel", "valve", "pump", "nozzle", "orifice", "pipe", "tube", "manifold")):
        return "FLUIDIC_PROCESS"
    if domain == "Mechanical" or "structure" in name or "conduit" in name or "raceway" in name:
        return "STRUCTURAL_FORM"
    if any(k in build_class for k in ("print", "direct")) or any(k in route for k in ("print", "deposit", "direct-write", "screen", "inkjet", "aerosol", "wind", "place")):
        return "PRINTED_FUNCTIONAL"
    return "ARCHETYPE_ONLY"


def _add_scope(out: dict[str, str], name: str, reason: str) -> None:
    if name not in out:
        out[name] = reason


def resolve_minimal_scopes(
    record: dict[str, Any],
    *,
    horizon: str = "H-TERR-SITE",
    required_scopes: Iterable[str] | None = None,
    process_conditions: Iterable[str] | None = None,
) -> dict[str, Any]:
    included = dict(ALWAYS_SCOPES)
    domain = record.get("Domain", "")
    name = _norm(record.get("Component Archetype"))
    function = _norm(record.get("Primary Function"))
    route = _norm(record.get("Current Manufacturing Route"))
    tests = _norm(record.get("Acceptance Tests"))
    failures = _norm(record.get("Failure Modes"))
    materials = _norm(record.get("Typical Material Stack"))
    build_class = _norm(record.get("Current CGX Build Class"))
    text = " ".join((name, function, route, tests, failures, materials, build_class))

    for scope in DOMAIN_BASE_SCOPES.get(domain, set()):
        _add_scope(included, scope, f"domain:{domain}")

    # Domain/name-specific refinements deliberately avoid generic atlas phrases
    # such as "optical where applicable" causing unnecessary solvers.
    if "capacitor" in name or "dielectric" in name:
        _add_scope(included, "electrical", "capacitive/dielectric function")
        _add_scope(included, "electric_field", "capacitance and dielectric acceptance depend on field geometry")
        _add_scope(included, "humidity_moisture", "dielectric leakage/insulation can depend on moisture")
    if any(k in name for k in ("inductor", "coil", "transformer", "antenna", "resonator", "waveguide", "rf ", "nfc", "rfid", "transceiver", "receiver", "transmitter")):
        _add_scope(included, "electrical", "electromagnetic component")
        _add_scope(included, "em_field", "field/coupling geometry materially affects function")
    if domain == "RF/Communications" or any(k in name for k in ("antenna", "rfid", "nfc", "receiver", "transmitter", "transceiver")):
        _add_scope(included, "spatial_coupling", "nearby geometry/environment can materially detune or couple the RF function")
    if domain == "Optical/Display" or any(k in name for k in ("led", "laser", "photodiode", "photovoltaic", "optical", "waveplate", "beamsplitter")):
        _add_scope(included, "optical", "optical generation/transport/detection is part of acceptance")
    if domain == "Semiconductor":
        _add_scope(included, "electrical", "semiconductor electrical function")
        _add_scope(included, "thermal", "junction/package limits and assembly exposure are consequential")
        _add_scope(included, "esd", "seed/package handling can be ESD-sensitive")
        _add_scope(included, "cleanliness", "contacts/package/interface assembly needs controlled contamination state")
    if domain == "Sensing":
        _add_scope(included, "metrology", "sensor output requires calibration/readback")
        if any(k in text for k in ("temperature", "thermo", "heat")):
            _add_scope(included, "thermal", "temperature is the measurand or cross-sensitivity")
        if any(k in text for k in ("strain", "force", "load", "pressure", "acceler", "vibration")):
            _add_scope(included, "mechanical", "mechanical measurand/coupling")
        if any(k in text for k in ("hall", "magnet", "field", "current", "voltage", "conductivity")):
            _add_scope(included, "electrical", "electrical/field measurand")
        if any(k in text for k in ("optical", "photo", "infrared", "uv", "light")):
            _add_scope(included, "optical", "optical measurand")
        if any(k in text for k in ("gas", "humidity", "ph", "chemical")):
            _add_scope(included, "chemical", "chemical/environment measurand")
    if domain == "Actuation":
        if any(k in text for k in ("motor", "solenoid", "electromagnet", "voice coil")):
            _add_scope(included, "electrical", "electromechanical actuation")
            _add_scope(included, "em_field", "field/current coupling drives actuation")
            _add_scope(included, "thermal", "coil/drive heating can limit operation")
        if any(k in text for k in ("pneumatic", "hydraulic", "fluid")):
            _add_scope(included, "fluid", "fluid-power actuation")
            _add_scope(included, "pressure", "pressure materially drives actuation and safety")
    if domain == "Fluid/Thermal":
        _add_scope(included, "fluid", "fluid/thermal component")
        if any(k in text for k in ("valve", "pump", "channel", "nozzle", "orifice", "pressure", "vacuum", "pneumatic", "hydraulic", "manifold")):
            _add_scope(included, "pressure", "pressure/flow state can change feasibility or acceptance")
        if any(k in text for k in ("heat", "thermal", "radiator", "exchanger", "heater", "cool")):
            _add_scope(included, "thermal", "thermal transport is a primary function")
    if domain == "Mechanical":
        _add_scope(included, "mechanical", "mechanical geometry/load/service acceptance")
    if domain == "Electrochemical/Chemical":
        _add_scope(included, "chemical", "chemistry materially controls function/process")
        _add_scope(included, "electrical", "electrochemical current/voltage state")
        _add_scope(included, "thermal", "temperature affects kinetics/safety")
        _add_scope(included, "humidity_moisture", "water/electrolyte state can affect process and storage")
    if any(k in text for k in ("cure", "sinter", "anneal", "reflow", "fire", "bake", "heat treatment")):
        _add_scope(included, "thermal", "source/process route includes a consequential thermal history")
    if any(k in text for k in ("solvent", "electrolyte", "reactive", "corrosion", "etch", "plating")):
        _add_scope(included, "chemical", "source/process route includes chemical exposure")
    if any(k in text for k in ("adhesion", "stress", "force", "load", "torque", "wear", "fatigue")):
        _add_scope(included, "mechanical", "acceptance/failure mode includes mechanical state")

    conditions = {_norm(x) for x in (process_conditions or []) if str(x).strip()}
    if conditions & {"vacuum", "positive pressure", "pressure", "pressurised", "pressurized"}:
        _add_scope(included, "pressure", "exact process conditions explicitly require pressure/vacuum handling")
    if conditions & {"inert", "reactive gas", "controlled gas", "dry", "clean", "vacuum"}:
        _add_scope(included, "cleanliness", "exact process condition requires controlled environment")
    if conditions & {"liquid", "slurry", "flow", "fluid"}:
        _add_scope(included, "fluid", "exact process condition includes fluid behaviour")
    if conditions & {"orientation-sensitive", "free-surface", "settling"}:
        _add_scope(included, "gravity", "exact process condition is orientation/gravity sensitive")

    h = horizon.upper().replace("H-", "").replace("-SITE", "")
    if h in SPACE_HORIZONS:
        _add_scope(included, "radiation", f"horizon:{h} can impose radiation/material/electronic exposure")
        _add_scope(included, "pressure", f"horizon:{h} can impose vacuum/pressure compatibility")
        _add_scope(included, "thermal", f"horizon:{h} thermal environment differs from terrestrial baseline")

    for scope in required_scopes or []:
        _add_scope(included, str(scope), "explicit exact-instance/process requirement")

    omitted = {
        scope: "not inferred as material to process feasibility, acceptance, safety or declared service state"
        for scope in sorted(KNOWN_OPTIONAL_SCOPES - set(included))
    }
    return {
        "included": dict(sorted(included.items())),
        "omitted": omitted,
        "rule": "Solve only dimensions that can materially change feasibility, component state, acceptance or safety; exact source/process evidence may add scopes, never silently remove a consequential one.",
    }


def validate_simulation_result(simulation: dict[str, Any] | None) -> dict[str, Any]:
    if not simulation:
        return {"provided": False, "accepted": False, "reasons": ["no-simulation-provided"], "candidate_overrides": {}}
    reasons: list[str] = []
    required_present = ("baseline_id", "candidate_id", "solver", "solver_version", "candidate_overrides")
    for key in required_present:
        if not simulation.get(key):
            reasons.append(f"missing:{key}")
    for key in ("same_material", "same_environment", "hard_gates_pass", "uncertainty_bounded"):
        if simulation.get(key) is not True:
            reasons.append(f"required-true:{key}")
    if simulation.get("physical_evidence_uplift") is True:
        reasons.append("simulation-cannot-uplift-physical-evidence")
    return {
        "provided": True,
        "accepted": not reasons,
        "reasons": reasons,
        "candidate_overrides": simulation.get("candidate_overrides", {}) if not reasons else {},
        "solver": simulation.get("solver"),
        "solver_version": simulation.get("solver_version"),
        "baseline_id": simulation.get("baseline_id"),
        "candidate_id": simulation.get("candidate_id"),
    }


def _recipe_uri(record: dict[str, Any], strategy: str) -> str:
    family = _slug(record.get("Family", record.get("Domain", "generic")))
    return f"cgx://manufacturing/recipe/{strategy.lower()}/{family}/v0.1"


def _operation_env_signature(scopes: dict[str, Any]) -> str:
    keys = [k for k in ("pressure", "fluid", "chemical", "cleanliness", "thermal", "radiation") if k in scopes["included"]]
    return "+".join(keys) if keys else "ambient-declared"


def _operation_list(strategy: str, scopes: dict[str, Any]) -> list[dict[str, Any]]:
    ops = RECIPE_OPS[strategy]
    out: list[dict[str, Any]] = []
    previous: str | None = None
    env = _operation_env_signature(scopes)
    for idx, (opcode, family, declared_dep) in enumerate(ops, start=1):
        op_id = f"op-{idx:02d}-{opcode.lower().replace('_','-')}"
        dep = declared_dep
        depends = [previous] if previous else []
        if dep and previous is None:
            depends = [dep]
        out.append(
            {
                "id": op_id,
                "opcode": opcode,
                "tool_family": family,
                "environment_signature": env,
                "depends_on": depends,
                "physical_execution": False,
            }
        )
        previous = op_id
    return out


def _looks_unresolved_instance_value(value: Any) -> bool:
    text = str(value or "").strip().upper()
    if not text or text in {"UNRESOLVED", "UNKNOWN", "NONE", "TBD", "TBC"}:
        return True
    unresolved_markers = (
        "UNRESOLVED",
        "NOT YET BOUND",
        "NOT BOUND",
        "NOT YET SELECTED",
        "NOT SELECTED",
        "TO BE BOUND",
        "TO BE SELECTED",
    )
    return any(marker in text for marker in unresolved_markers)


def _instance_blockers(instance: dict[str, Any] | None) -> list[str]:
    if not instance:
        return ["exact-instance-not-bound"]
    blockers: list[str] = []
    state = instance.get("binding_state")
    if state != "BUILD_READY":
        blockers.append(f"binding-state:{state or 'UNKNOWN'}")
    for field in (
        "source_locator_or_hash",
        "geometry_revision",
        "dimensions_and_tolerances",
        "material_stack_and_lots",
        "tool_and_calibration_refs",
        "configuration_hash",
        "source_hashes",
    ):
        if _looks_unresolved_instance_value(instance.get(field, "")):
            blockers.append(f"unresolved:{field}")
    if instance.get("physical_state") not in {"NOT_RUN", "BUILT", "MEASURED", "REVIEWED_PROMOTION"}:
        blockers.append("invalid-physical-state")
    return blockers


def compile_component(
    record: dict[str, Any],
    *,
    instance: dict[str, Any] | None = None,
    simulation: dict[str, Any] | None = None,
    build_id: str | None = None,
    horizon: str = "H-TERR-SITE",
    required_scopes: Iterable[str] | None = None,
    process_conditions: Iterable[str] | None = None,
    parameter_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    strategy = classify_process_strategy(record)
    scopes = resolve_minimal_scopes(
        record,
        horizon=horizon,
        required_scopes=required_scopes,
        process_conditions=process_conditions,
    )
    sim = validate_simulation_result(simulation)
    overrides = dict(parameter_overrides or {})
    if sim["accepted"]:
        overrides.update(sim["candidate_overrides"])

    bid = _slug(build_id or f"{record['ID']}-build")
    blockers = _instance_blockers(instance)
    operations = _operation_list(strategy, scopes)
    exact_ref = instance.get("instance_id") if instance else None
    recipe_uri = _recipe_uri(record, strategy)
    volumetric = resolve_volumetric_topology(record, instance=instance)

    out: dict[str, Any] = {
        "schema": SCHEMA,
        "cgx_uri": f"cgx://manufacturing/build/{bid}",
        "recipe_uri": recipe_uri,
        "recipe_schema": RECIPE_SCHEMA,
        "build_id": bid,
        "archetype": {
            "id": record["ID"],
            "name": record.get("Component Archetype"),
            "domain": record.get("Domain"),
            "family": record.get("Family"),
            "build_class": record.get("Current CGX Build Class"),
            "evidence_state": record.get("Evidence State"),
        },
        "instance_ref": exact_ref,
        "binding_progress": _instance_binding_progress(instance),
        "horizon": horizon,
        "process_strategy": strategy,
        "parameter_overrides": overrides,
        "scope_decision": scopes,
        "operations": operations,
        "simulation_refinement": sim,
        "volumetric_topology": volumetric,
        "acceptance_tests": record.get("Acceptance Tests"),
        "failure_modes": record.get("Failure Modes"),
        "ports_interfaces": record.get("Ports / Interfaces"),
        "filespace": {
            "archetype_ref": record["ID"],
            "instance_ref": exact_ref,
            "source_authority_class": record.get("Source Authority Class"),
            "instance_source_authority": instance.get("exact_source_authority") if instance else None,
            "source_locator_or_hash": instance.get("source_locator_or_hash") if instance else None,
            "material_stack_and_lots": instance.get("material_stack_and_lots") if instance else None,
            "material_passport_refs": instance.get("material_passport_refs") if instance else None,
            "tool_and_calibration_refs": instance.get("tool_and_calibration_refs") if instance else None,
            "recipe_ref": recipe_uri,
        },
        "dataspace": {
            "compile_event_type": "BUILD_PLANNED",
            "simulation_ref": simulation.get("candidate_id") if simulation else None,
            "expected_readback": "compiler/hash + later machine/test DBR",
        },
        "solid_state": {
            "geometry": record.get("Baseline Geometry"),
            "materials": record.get("Typical Material Stack"),
            "interfaces": record.get("Ports / Interfaces"),
            "volumetric_topology_tokens": volumetric.get("compiler_tokens", []),
        },
        "blockers": sorted(set(blockers)),
        "compile_state": "DIGITAL_PLAN",
        "execution_state": "BUILD_READY" if not blockers and instance and instance.get("binding_state") == "BUILD_READY" else "HOLD",
        "physical_execution": False,
        "authority_boundary": "Compiler output is machine-neutral digital intent; it does not actuate hardware, certify the article, or raise the recorded evidence ceiling.",
    }
    out["configuration_hash"] = _canonical_hash({k: v for k, v in out.items() if k != "configuration_hash"})
    return out


def _transition_signature(op: dict[str, Any]) -> tuple[str, str]:
    return (op.get("tool_family", ""), op.get("environment_signature", ""))


def _topological_schedule(nodes: dict[str, dict[str, Any]], edges: set[tuple[str, str]]) -> list[str]:
    incoming: dict[str, set[str]] = {n: set() for n in nodes}
    outgoing: dict[str, set[str]] = defaultdict(set)
    for before, after in edges:
        if before not in nodes or after not in nodes:
            raise ValueError(f"unknown-dependency:{before}->{after}")
        incoming[after].add(before)
        outgoing[before].add(after)

    ready = sorted([n for n, deps in incoming.items() if not deps])
    schedule: list[str] = []
    previous_sig: tuple[str, str] | None = None
    while ready:
        same = [n for n in ready if previous_sig is not None and _transition_signature(nodes[n]) == previous_sig]
        chosen = sorted(same or ready)[0]
        ready.remove(chosen)
        schedule.append(chosen)
        previous_sig = _transition_signature(nodes[chosen])
        for nxt in sorted(outgoing.get(chosen, ())):
            incoming[nxt].discard(chosen)
            if not incoming[nxt] and nxt not in schedule and nxt not in ready:
                ready.append(nxt)
        ready.sort()
    if len(schedule) != len(nodes):
        unresolved = sorted(set(nodes) - set(schedule))
        raise ValueError(f"dependency-cycle:{','.join(unresolved)}")
    return schedule


def _transition_count(schedule: list[str], nodes: dict[str, dict[str, Any]]) -> int:
    if not schedule:
        return 0
    count = 0
    prev = _transition_signature(nodes[schedule[0]])
    for ref in schedule[1:]:
        cur = _transition_signature(nodes[ref])
        if cur != prev:
            count += 1
        prev = cur
    return count


def compile_assembly(
    child_builds: list[dict[str, Any]],
    *,
    build_id: str,
    relations: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: set[tuple[str, str]] = set()
    naive: list[str] = []

    for child in child_builds:
        child_uri = child["cgx_uri"]
        local_to_ref: dict[str, str] = {}
        for op in child["operations"]:
            ref = f"{child_uri}#{op['id']}"
            local_to_ref[op["id"]] = ref
            nodes[ref] = {
                "ref": ref,
                "child_build_ref": child_uri,
                "operation_id": op["id"],
                "opcode": op["opcode"],
                "tool_family": op.get("tool_family"),
                "environment_signature": op.get("environment_signature"),
            }
            naive.append(ref)
        for op in child["operations"]:
            after = local_to_ref[op["id"]]
            for dep in op.get("depends_on", []):
                if dep in local_to_ref:
                    edges.add((local_to_ref[dep], after))

    for relation in relations or []:
        before = relation["before"]
        after = relation["after"]
        edges.add((before, after))

    schedule = _topological_schedule(nodes, edges)
    state = "BUILD_READY" if all(c.get("execution_state") == "BUILD_READY" for c in child_builds) else "HOLD"
    out = {
        "schema": "CGX-MANUFACTURING-ASSEMBLY/0.1",
        "cgx_uri": f"cgx://manufacturing/build/{_slug(build_id)}",
        "child_build_refs": [c["cgx_uri"] for c in child_builds],
        "child_recipe_refs": [c["recipe_uri"] for c in child_builds],
        "recipe_bodies_duplicated": False,
        "operation_refs": nodes,
        "dependencies": [{"before": a, "after": b} for a, b in sorted(edges)],
        "schedule": schedule,
        "optimization": {
            "objective": "minimise compatible tool/environment transitions without violating dependency order",
            "naive_transition_count": _transition_count(naive, nodes),
            "scheduled_transition_count": _transition_count(schedule, nodes),
        },
        "execution_state": state,
        "physical_execution": False,
        "authority_boundary": "Assembly scheduling cannot raise any child evidence ceiling or bypass a child/interface/safety/authority gate.",
    }
    out["configuration_hash"] = _canonical_hash({k: v for k, v in out.items() if k != "configuration_hash"})
    return out