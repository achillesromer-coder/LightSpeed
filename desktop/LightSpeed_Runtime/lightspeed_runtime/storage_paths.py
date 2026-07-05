from __future__ import annotations

from pathlib import Path


PRIMARY_GENERATED_ROOT = Path("data") / "generated"
Z_AXIS_ROOT = Path("Z Axis")
ROOT_W6_GENERATED_ROOT = Path("w6") / "data"
ROOT_OPERATIONS_W6_GENERATED_ROOT = Path("operations") / "w6" / "data"

FLOOR_DATA_DIRS = {
    "oracle": Z_AXIS_ROOT / "Z-2_Oracle" / "data",
    "morpheus": Z_AXIS_ROOT / "Z-1_Morpheus" / "data",
    "construct": Z_AXIS_ROOT / "Z0_TheConstruct" / "data",
    "architect": Z_AXIS_ROOT / "Z+1_Architect" / "data",
    "neo": Z_AXIS_ROOT / "Z+2_Neo" / "data",
    "trinity": Z_AXIS_ROOT / "Z+3_Trinity" / "data",
    "smith": Z_AXIS_ROOT / "Z-3_Smith" / "data",
    "merovingian": Z_AXIS_ROOT / "Z-4_Merovingian" / "data",
}
FLOOR_ROOT_DIRS = {key: path.parent for key, path in FLOOR_DATA_DIRS.items()}


def floor_root(root: Path, floor_key: str) -> Path:
    return Path(root) / FLOOR_ROOT_DIRS[floor_key]


def active_generated_root(root: Path) -> Path:
    return Path(root) / PRIMARY_GENERATED_ROOT


def floor_data_root(root: Path, floor_key: str) -> Path:
    return Path(root) / FLOOR_DATA_DIRS[floor_key]


def oracle_floor_root(root: Path) -> Path:
    return floor_root(root, "oracle")


def architect_floor_root(root: Path) -> Path:
    return floor_root(root, "architect")


def oracle_config_root(root: Path) -> Path:
    return oracle_floor_root(root) / "config"


def oracle_runtime_config_root(root: Path) -> Path:
    return oracle_config_root(root) / "runtime"


def architect_config_root(root: Path) -> Path:
    return architect_floor_root(root) / "config"


def architect_runtime_config_root(root: Path) -> Path:
    return architect_config_root(root) / "runtime"


def canonical_runtime_config_path(root: Path) -> Path:
    """Return the Oracle-owned canonical runtime reservoir config path."""
    return oracle_runtime_config_root(root) / "runtime_reservoirs.json"


def canonical_intermediary_targets_path(root: Path) -> Path:
    """Return the Architect-owned canonical intermediary target config path."""
    return architect_runtime_config_root(root) / "intermediary_targets.json"


def canonical_execution_queue_path(root: Path) -> Path:
    """Return the Architect-owned canonical execution queue path."""
    return finalization_queue_root(root) / "execution_queues.json"


def canonical_ai_settings_path(root: Path) -> Path:
    """Return the Architect-owned canonical AI settings path."""
    return architect_config_root(root) / "ai_config.json"


def _prefer_existing_path(canonical: Path, *legacy_candidates: Path) -> Path:
    if canonical.exists():
        return canonical
    for candidate in legacy_candidates:
        if candidate.exists():
            return candidate
    return canonical


def resolve_runtime_config_path(root: Path) -> Path:
    """Resolve the runtime reservoir config, preferring the canonical Oracle path."""
    root = Path(root)
    return _prefer_existing_path(
        canonical_runtime_config_path(root),
        root / "config" / "runtime" / "runtime_reservoirs.json",
        root / "config" / "runtime_reservoirs.json",
    )


def resolve_intermediary_targets_path(root: Path) -> Path:
    """Resolve intermediary targets, preferring the canonical Architect path."""
    root = Path(root)
    return _prefer_existing_path(
        canonical_intermediary_targets_path(root),
        root / "config" / "runtime" / "intermediary_targets.json",
        root / "config" / "intermediary_targets.json",
    )


def resolve_ai_settings_path(root: Path) -> Path:
    """Resolve AI settings, preferring the canonical Architect config path."""
    root = Path(root)
    return _prefer_existing_path(
        canonical_ai_settings_path(root),
        root / "config" / "ai_config.json",
    )


def oracle_root(root: Path) -> Path:
    return floor_data_root(root, "oracle")


def morpheus_root(root: Path) -> Path:
    return floor_data_root(root, "morpheus")


def construct_root(root: Path) -> Path:
    return floor_data_root(root, "construct")


def architect_root(root: Path) -> Path:
    return floor_data_root(root, "architect")


def neo_root(root: Path) -> Path:
    return floor_data_root(root, "neo")


def trinity_root(root: Path) -> Path:
    return floor_data_root(root, "trinity")


def smith_root(root: Path) -> Path:
    return floor_data_root(root, "smith")


def merovingian_root(root: Path) -> Path:
    return floor_data_root(root, "merovingian")


def smith_legacy_root(root: Path) -> Path:
    return smith_root(root) / "legacy"


def legacy_w6_generated_root(root: Path) -> Path:
    return smith_legacy_root(root) / "w6" / "data"


def legacy_operations_w6_generated_root(root: Path) -> Path:
    return smith_legacy_root(root) / "operations_w6" / "data"


def legacy_runtime_bundle_root(root: Path) -> Path:
    return merovingian_root(root) / "legacy_runtime_bundle" / "canonical_runtime"


def runtime_exports_root(root: Path) -> Path:
    return merovingian_root(root) / "runtime_exports"


def snapshot_export_root(root: Path) -> Path:
    """Return the Merovingian-owned runtime export snapshot destination."""
    return runtime_exports_root(root) / "snapshot"


def publish_root(root: Path) -> Path:
    return architect_root(root) / "publish"


def publish_snapshot_root(root: Path) -> Path:
    """Return the Architect-owned publish snapshot destination."""
    return publish_root(root) / "snapshot"


def finalization_queue_root(root: Path) -> Path:
    return architect_root(root) / "finalization"


def labs_root(root: Path) -> Path:
    return construct_root(root) / "labs"


def zoning_root(root: Path) -> Path:
    return labs_root(root) / "heliocentric_zoning"


def reports_root(root: Path) -> Path:
    return merovingian_root(root) / "reports"


def logs_root(root: Path) -> Path:
    return merovingian_root(root) / "logs"


def quality_root(root: Path) -> Path:
    return merovingian_root(root) / "quality"


def ingestion_root(root: Path) -> Path:
    return oracle_root(root) / "ingestion"


def knowns_root(root: Path) -> Path:
    return oracle_root(root) / "knowns"


def catalog_root(root: Path) -> Path:
    return oracle_root(root) / "catalog"


def oracle_reservoir_root(root: Path) -> Path:
    return oracle_root(root) / "reservoirs"


def library_root(root: Path) -> Path:
    return oracle_root(root) / "library"


def encyclopedia_root(root: Path) -> Path:
    return oracle_root(root) / "encyclopedia"


def datatables_root(root: Path) -> Path:
    return oracle_root(root) / "datatables"


def neo_actions_root(root: Path) -> Path:
    return neo_root(root) / "actions"


def operations_root(root: Path) -> Path:
    return smith_root(root) / "operations"


def construct_reservoir_root(root: Path) -> Path:
    return construct_root(root) / "reservoirs"


def legacy_flat_generated_root(root: Path) -> Path:
    return active_generated_root(root)


def ensure_generated_layout(root: Path) -> dict[str, str]:
    root = Path(root)
    paths = {
        "active_generated_root": active_generated_root(root),
        "oracle_config_root": oracle_config_root(root),
        "oracle_runtime_config_root": oracle_runtime_config_root(root),
        "oracle_root": oracle_root(root),
        "morpheus_root": morpheus_root(root),
        "construct_root": construct_root(root),
        "architect_config_root": architect_config_root(root),
        "architect_runtime_config_root": architect_runtime_config_root(root),
        "architect_root": architect_root(root),
        "neo_root": neo_root(root),
        "trinity_root": trinity_root(root),
        "smith_root": smith_root(root),
        "smith_legacy_root": smith_legacy_root(root),
        "merovingian_root": merovingian_root(root),
        "ingestion_root": ingestion_root(root),
        "knowns_root": knowns_root(root),
        "catalog_root": catalog_root(root),
        "oracle_reservoir_root": oracle_reservoir_root(root),
        "library_root": library_root(root),
        "encyclopedia_root": encyclopedia_root(root),
        "datatables_root": datatables_root(root),
        "labs_root": labs_root(root),
        "construct_reservoir_root": construct_reservoir_root(root),
        "publish_root": publish_root(root),
        "finalization_queue_root": finalization_queue_root(root),
        "runtime_exports_root": runtime_exports_root(root),
        "reports_root": reports_root(root),
        "logs_root": logs_root(root),
        "quality_root": quality_root(root),
        "operations_root": operations_root(root),
        "neo_actions_root": neo_actions_root(root),
        "legacy_w6_generated_root": legacy_w6_generated_root(root),
        "legacy_operations_w6_generated_root": legacy_operations_w6_generated_root(root),
        "legacy_runtime_bundle_root": legacy_runtime_bundle_root(root),
    }
    for name, path in paths.items():
        if name == "active_generated_root":
            continue
        path.mkdir(parents=True, exist_ok=True)
    return {name: str(path) for name, path in paths.items()}


def legacy_generated_roots(root: Path) -> list[Path]:
    base = Path(root)
    candidates = [
        legacy_w6_generated_root(base),
        legacy_operations_w6_generated_root(base),
        base / ROOT_W6_GENERATED_ROOT,
        base / ROOT_OPERATIONS_W6_GENERATED_ROOT,
    ]
    roots: list[Path] = []
    for path in candidates:
        if not path.exists():
            continue
        try:
            has_content = any(path.iterdir())
        except Exception:
            has_content = True
        if has_content and path not in roots:
            roots.append(path)
    return roots


def all_generated_roots(root: Path) -> list[Path]:
    roots: list[Path] = [active_generated_root(root)]
    for path in legacy_generated_roots(root):
        if path not in roots:
            roots.append(path)
    return roots


def smart_floor_roots(root: Path) -> dict[str, str]:
    return {
        "oracle": str(oracle_root(root)),
        "morpheus": str(morpheus_root(root)),
        "construct": str(construct_root(root)),
        "architect": str(architect_root(root)),
        "neo": str(neo_root(root)),
        "trinity": str(trinity_root(root)),
        "smith": str(smith_root(root)),
        "merovingian": str(merovingian_root(root)),
    }


def describe_generated_roots(root: Path) -> dict:
    return {
        "active_generated_root": str(active_generated_root(root)),
        "legacy_generated_roots": [str(path) for path in legacy_generated_roots(root)],
        "smart_floor_roots": smart_floor_roots(root),
    }


def resolve_tool_data_root(root: Path, tool_name: str) -> Path:
    active = ingestion_root(root) / tool_name
    if active.exists():
        return active

    flat_generated = legacy_flat_generated_root(root) / "ingestion" / tool_name
    if flat_generated.exists():
        return flat_generated

    for candidate_root in legacy_generated_roots(root):
        tool_root = candidate_root / tool_name
        if tool_root.exists():
            return tool_root
    return active
