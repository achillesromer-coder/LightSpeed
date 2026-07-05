from __future__ import annotations

import json
import re
from pathlib import Path

from lightspeed_runtime.contracts import ReservoirManifest, utc_now_iso
from lightspeed_runtime.definition_library import (
    default_oracle_definition_library_path,
    decorate_theme_with_definition,
    write_oracle_definition_library,
)
from lightspeed_runtime.empirical import read_empirical_catalog
from lightspeed_runtime.storage_paths import catalog_root, datatables_root, encyclopedia_root, knowns_root, library_root, labs_root


TEXT_EXTENSIONS = {".md", ".txt", ".json", ".jsonl", ".csv", ".py", ".yaml", ".yml"}
SOURCE_PRIORITY_KEYWORDS = (
    "achilles",
    "cognigrex",
    "romer",
    "emassc",
    "architecture",
    "alignment",
    "system",
    "wizard",
    "gmat",
    "handoff",
    "start_here",
    "master_index",
)

THEME_DEFINITIONS = {
    "mission_stewardship": {
        "title": "Stewardship Mission",
        "category": "mission",
        "summary": (
            "The mission is framed as stewardship-first expansion: advance toward a Type-I civilization "
            "while keeping non-invasive extraction and ecological repair as hard gates."
        ),
        "keywords": [
            "type-i civilization",
            "type i civilization",
            "stewardship",
            "non-invasive",
            "eco-x",
            "environmental gate",
            "carbon",
        ],
    },
    "achilles_operator": {
        "title": "Achilles as Governed Operator",
        "category": "operator",
        "summary": (
            "Achilles is the primary operator persona: sovereign strategic protocol, mission co-pilot, "
            "decision auditor, and bounded operator rather than an unconstrained assistant."
        ),
        "keywords": [
            "achilles",
            "mission co-pilot",
            "decision auditor",
            "sovereign strategic protocol",
            "audit role",
            "approval",
            "operator",
        ],
    },
    "cognigrex_body": {
        "title": "Cognigrex as Swarm Body",
        "category": "operator",
        "summary": (
            "Cognigrex is the distributed execution body under Achilles oversight, coordinating floors, "
            "hardware, and project workflows as a governed swarm."
        ),
        "keywords": [
            "cognigrex",
            "swarm",
            "body",
            "hive-mind",
            "collective",
            "oversight",
        ],
    },
    "governance_ip": {
        "title": "Romer and EMASSC Governance",
        "category": "governance",
        "summary": (
            "EMASSC remains the IP custodian and governance layer while Romer operates as the executor. "
            "LightSpeed should keep that separation visible in project, publish, and approval flows."
        ),
        "keywords": [
            "emassc",
            "romer",
            "ip",
            "custodian",
            "license",
            "sovereign innovation trust",
            "commercial executor",
        ],
    },
    "smart_floor_os": {
        "title": "Smart-Floor Operating System",
        "category": "architecture",
        "summary": (
            "LightSpeed is a desktop-first operating shell built around smart floors, with workspace shell, "
            "operator portal, and holospace views sharing one runtime truth."
        ),
        "keywords": [
            "z-axis",
            "floor",
            "workspace shell",
            "operator portal",
            "holospace",
            "smart floor",
            "trinity",
            "merovingian",
            "oracle",
            "neo",
        ],
    },
    "proofed_knowns": {
        "title": "Proofed Knowns Pipeline",
        "category": "knowledge",
        "summary": (
            "Mounted sources should be proofed into knowns, library, encyclopedia, and datatables rather than "
            "left as loose archives, duplicated JSON logs, or ad hoc notes."
        ),
        "keywords": [
            "known known",
            "proof",
            "library",
            "encyclopedia",
            "datatable",
            "ingestion",
            "reservoir",
            "ai_logs",
            "notebooklm",
        ],
    },
    "simulation_pipeline": {
        "title": "Scenario and GMAT Pipeline",
        "category": "labs",
        "summary": (
            "Construct and Trinity should turn datasets into zoning, cluster analysis, simulations, and "
            "GMAT-ready mission batches with outputs tied back to governed workspaces."
        ),
        "keywords": [
            "gmat",
            "simulation",
            "scenario",
            "zoning",
            "cluster",
            "heliocentric",
            "orbital",
            "dataset",
            "target",
        ],
    },
    "ui_operator_model": {
        "title": "High-Fidelity Operator UX",
        "category": "experience",
        "summary": (
            "The user-facing system should feel like one clear high-end operator OS: streamlined, glassy, "
            "and business/lab ready, with Neo housing Achilles and Z Direct exposing durable governed objects."
        ),
        "keywords": [
            "ui",
            "glass",
            "portal",
            "wizard",
            "dashboard",
            "z direct",
            "high-end",
            "operator",
        ],
    },
    "alignment_cleanup": {
        "title": "Condensation and Alignment",
        "category": "refinement",
        "summary": (
            "The application should reduce file sprawl, fold historical guidance into current runtime behavior, "
            "and keep only compact weekly logs and canonical reports as active outputs."
        ),
        "keywords": [
            "alignment",
            "consolidation",
            "cleanup",
            "weekly",
            "finalization",
            "compact",
            "legacy",
            "archive",
        ],
    },
}


def default_knowns_registry_path(root: Path) -> Path:
    return knowns_root(root) / "knowns_registry.json"


def default_knowns_proofing_queue_path(root: Path) -> Path:
    return knowns_root(root) / "knowns_proofing_queue.json"


def default_knowns_promotion_ledger_path(root: Path) -> Path:
    return knowns_root(root) / "knowns_promotion_ledger.json"


def default_knowns_declassification_audit_path(root: Path) -> Path:
    return knowns_root(root) / "knowns_declassification_audit.json"


def default_knowns_queue_objects_path(root: Path) -> Path:
    return catalog_root(root) / "promotion_queue_objects.json"


def read_knowns_registry(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_knowns_registry_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def read_knowns_proofing_queue(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_knowns_proofing_queue_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def read_knowns_promotion_ledger(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_knowns_promotion_ledger_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def read_knowns_declassification_audit(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_knowns_declassification_audit_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def _manifest_text(manifest: ReservoirManifest) -> str:
    return _normalize(
        " ".join(
            [
                manifest.source_id,
                manifest.source_type,
                manifest.classification,
                " ".join(manifest.workspace_tags),
                " ".join(manifest.project_tags),
                " ".join(manifest.trusted_documents),
            ]
        )
    )


def _is_knowns_source(manifest: ReservoirManifest) -> bool:
    text = _manifest_text(manifest)
    markers = (
        "doctrine",
        "protocol",
        "alignment",
        "architecture",
        "ingestion",
        "achilles",
        "cognigrex",
        "romer",
        "emassc",
        "log",
        "handoff",
        "wizard",
    )
    return any(marker in text for marker in markers)


def _candidate_files(manifest: ReservoirManifest, *, max_documents: int = 14) -> list[Path]:
    root = Path(manifest.root_path)
    if not root.exists():
        return []

    trusted = [_normalize(item) for item in manifest.trusted_documents if item]
    scored: list[tuple[int, Path]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        lowered = _normalize(str(path.relative_to(root)))
        score = 0
        if any(token and token in lowered for token in trusted):
            score += 120
        if "temporary archived_launchers" in lowered:
            score -= 40
        if "recovery" in lowered:
            score -= 20
        score += 12 if path.suffix.lower() in {".md", ".txt"} else 4
        score += sum(8 for token in SOURCE_PRIORITY_KEYWORDS if token in lowered)
        score -= len(path.parts)
        scored.append((score, path))

    scored.sort(key=lambda item: (-item[0], str(item[1]).lower()))
    return [path for _score, path in scored[:max_documents]]


def _read_text_excerpt(path: Path, *, max_chars: int = 12000) -> str:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    return raw[:max_chars]


def _extract_excerpt(text: str, keywords: list[str]) -> str:
    if not text:
        return ""
    blocks = [item.strip() for item in re.split(r"\n{2,}", text) if item.strip()]
    lowered_blocks = [_normalize(item) for item in blocks]
    lowered_keywords = [_normalize(item) for item in keywords]
    for block, lowered in zip(blocks, lowered_blocks):
        if any(keyword in lowered for keyword in lowered_keywords if keyword):
            return re.sub(r"\s+", " ", block)[:420]
    line = re.sub(r"\s+", " ", blocks[0]) if blocks else ""
    return line[:420]


def build_knowns_registry(
    root: Path,
    manifests: list[ReservoirManifest],
    *,
    output_path: Path | None = None,
) -> dict:
    root = Path(root)
    selected_manifests = [manifest for manifest in manifests if _is_knowns_source(manifest)]
    documents: list[dict] = []
    theme_index: dict[str, dict] = {}

    for theme_id, definition in THEME_DEFINITIONS.items():
        theme_index[theme_id] = {
            "theme_id": theme_id,
            "title": definition["title"],
            "category": definition["category"],
            "summary": definition["summary"],
            "source_label": definition["title"],
            "support_source_ids": set(),
            "support_document_paths": set(),
            "evidence": [],
        }

    for manifest in selected_manifests:
        for path in _candidate_files(manifest):
            text = _read_text_excerpt(path)
            if not text.strip():
                continue
            relative_path = str(path.relative_to(Path(manifest.root_path))).replace("\\", "/")
            document_record = {
                "source_id": manifest.source_id,
                "relative_path": relative_path,
                "title": path.stem.replace("_", " ").replace("-", " "),
            }
            documents.append(document_record)
            searchable = _normalize(_manifest_text(manifest) + " " + text)
            for theme_id, definition in THEME_DEFINITIONS.items():
                matched_keywords = [keyword for keyword in definition["keywords"] if _normalize(keyword) in searchable]
                if not matched_keywords:
                    continue
                theme = theme_index[theme_id]
                theme["support_source_ids"].add(manifest.source_id)
                theme["support_document_paths"].add(f"{manifest.source_id}:{relative_path}")
                if len(theme["evidence"]) < 6:
                    theme["evidence"].append(
                        {
                            "source_id": manifest.source_id,
                            "relative_path": relative_path,
                            "title": document_record["title"],
                            "excerpt": _extract_excerpt(text, matched_keywords),
                            "matched_keywords": matched_keywords[:4],
                        }
                    )

    themes: list[dict] = []
    for theme in theme_index.values():
        source_count = len(theme["support_source_ids"])
        document_count = len(theme["support_document_paths"])
        if not source_count and not document_count:
            continue
        if source_count >= 3 or document_count >= 5:
            band = "core"
        elif source_count >= 2 or document_count >= 2:
            band = "aligned"
        else:
            band = "edge"
        signal_score = source_count * 3 + document_count
        themes.append(
            {
                "theme_id": theme["theme_id"],
                "title": theme["title"],
                "category": theme["category"],
                "summary": theme["summary"],
                "source_label": theme["source_label"],
                "support_source_count": source_count,
                "support_document_count": document_count,
                "support_source_ids": sorted(theme["support_source_ids"]),
                "consensus_band": band,
                "signal_score": signal_score,
                "evidence": theme["evidence"],
            }
        )

    empirical_catalog = read_empirical_catalog(root)
    empirical_headlines = empirical_catalog.get("headline_knowns") or []
    if empirical_headlines:
        empirical_sources = {
            str(item.get("source_id") or "library_empirical_data")
            for item in empirical_headlines
            if item.get("source_id") or "library_empirical_data"
        }
        empirical_count = len(empirical_headlines)
        if empirical_count >= 5:
            empirical_band = "core"
        elif empirical_count >= 2:
            empirical_band = "aligned"
        else:
            empirical_band = "edge"
        themes.append(
            {
                "theme_id": "empirical_dataset_layer",
                "title": "Empirical Dataset Layer",
                "category": "labs",
                "summary": (
                    "Mounted empirical datasets are condensed into Oracle and Construct-ready anchors for zoning, "
                    "simulation, and proofed scenario refinement."
                ),
                "source_label": "Empirical Dataset Layer",
                "support_source_count": len(empirical_sources),
                "support_document_count": empirical_count,
                "support_source_ids": sorted(empirical_sources),
                "consensus_band": empirical_band,
                "signal_score": len(empirical_sources) * 3 + empirical_count,
                "evidence": [
                    {
                        "source_id": item.get("source_id", "library_empirical_data"),
                        "relative_path": str(item.get("recommended_path") or ""),
                        "title": item.get("headline", "Empirical anchor"),
                        "excerpt": item.get("headline", "Empirical anchor"),
                        "matched_keywords": [item.get("theme", "general_empirical")],
                    }
                    for item in empirical_headlines[:6]
                ],
            }
        )

    themes.sort(key=lambda item: (-int(item["signal_score"]), str(item["title"]).lower()))
    for index, theme in enumerate(themes):
        themes[index] = decorate_theme_with_definition(theme)
    curve = {
        "core": [item["title"] for item in themes if item["consensus_band"] == "core"],
        "aligned": [item["title"] for item in themes if item["consensus_band"] == "aligned"],
        "edge": [item["title"] for item in themes if item["consensus_band"] == "edge"],
    }
    mission_statement = (
        "LightSpeed is the desktop-first smart-floor operating system for Romer and EMASSC, "
        "with Achilles as governed operator and Cognigrex as the execution body."
    )
    payload = {
        "generated_at": utc_now_iso(),
        "registry_path": str(output_path or default_knowns_registry_path(root)),
        "report_path": str(output_path or default_knowns_registry_path(root)),
        "source_count": len(selected_manifests),
        "document_count": len(documents),
        "mission_statement": mission_statement,
        "operator_model": {
            "primary_operator": "Achilles",
            "oversight_body": "Cognigrex",
            "workspace_mode": "desktop_first",
            "governance_mode": "approval_gated",
        },
        "definition_library_path": str(default_oracle_definition_library_path(root)),
        "definition_policy": (
            "Use Oracle's proofed definitions as canonical meanings; use source mentions only as provenance evidence."
        ),
        "bellcurve_overlay": {
            "center": curve["core"],
            "near_center": curve["aligned"],
            "edge": curve["edge"],
            "center_of_gravity": (curve["core"] or curve["aligned"] or curve["edge"])[:3],
        },
        "empirical_layer": {
            "headline_count": len(empirical_headlines),
            "clusterable_input_count": len(empirical_catalog.get("clusterable_inputs") or []),
            "recommended_dataset_count": len(empirical_catalog.get("recommended_datasets") or []),
            "role_totals": empirical_catalog.get("role_totals") or {},
            "headline_knowns": empirical_headlines[:8],
        },
        "themes": themes,
        "documents": documents[:48],
        "recommended_actions": [
            "Proof doctrine and AI-log material into knowns before expanding library width.",
            "Use Neo to retrieve from knowns and Oracle to verify provenance before staging changes.",
            "Keep heavy datasets mounted and indexed; only condensed knowns and approved tables become active runtime state.",
        ],
    }
    return payload


def write_knowns_registry(
    root: Path,
    manifests: list[ReservoirManifest],
    *,
    output_path: Path | None = None,
) -> dict:
    root = Path(root)
    destination = output_path or default_knowns_registry_path(root)
    payload = build_knowns_registry(root, manifests, output_path=destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_oracle_definition_library(
        root,
        knowns_registry=payload,
        empirical_catalog=read_empirical_catalog(root),
        output_path=default_oracle_definition_library_path(root),
    )
    return payload


def _proofing_destinations(theme: dict) -> list[str]:
    category = str(theme.get("category") or "")
    theme_id = str(theme.get("theme_id") or "")
    if theme_id == "empirical_dataset_layer":
        return ["knowns", "library", "encyclopedia_candidates", "datatables", "scenario_lab"]
    if category in {"mission", "governance", "operator", "architecture", "refinement"}:
        return ["knowns", "library", "encyclopedia_candidates"]
    if category in {"labs"} or theme_id == "simulation_pipeline":
        return ["knowns", "datatables", "scenario_lab"]
    if category in {"experience"}:
        return ["knowns", "library"]
    return ["knowns", "library"]


def build_knowns_proofing_queue(root: Path, registry_payload: dict) -> dict:
    root = Path(root)
    themes = registry_payload.get("themes") or []
    existing_queue = read_knowns_proofing_queue(root)
    existing_entries = {
        str(item.get("entry_id") or ""): item
        for item in (existing_queue.get("entries") or [])
        if item.get("entry_id")
    }
    entries: list[dict] = []
    destination_counts: dict[str, int] = {}
    destination_paths = {
        "knowns": str(knowns_root(root)),
        "library": str(library_root(root)),
        "encyclopedia_candidates": str(encyclopedia_root(root)),
        "datatables": str(datatables_root(root)),
        "scenario_lab": str(labs_root(root)),
    }
    for theme in themes:
        theme_id = str(theme.get("theme_id") or "")
        title = str(theme.get("title") or theme_id)
        destinations = _proofing_destinations(theme)
        evidence = theme.get("evidence") or []
        for destination in destinations:
            destination_counts[destination] = destination_counts.get(destination, 0) + 1
            entry_id = f"{theme_id}:{destination}"
            existing = existing_entries.get(entry_id, {})
            entries.append(
                {
                    "entry_id": entry_id,
                    "theme_id": theme_id,
                    "title": title,
                    "source_label": title,
                    "destination": destination,
                    "status": existing.get("status", "queued_for_proofing"),
                    "owner_floor": "Oracle",
                    "usage_role": destination,
                    "summary": theme.get("proofed_definition") or theme.get("summary", ""),
                    "proofed_definition": theme.get("proofed_definition", ""),
                    "operator_notes": theme.get("operator_notes", ""),
                    "consensus_band": theme.get("consensus_band", "edge"),
                    "support_source_count": int(theme.get("support_source_count", 0) or 0),
                    "support_document_count": int(theme.get("support_document_count", 0) or 0),
                    "definition_basis": theme.get("definition_basis", "theme_summary"),
                    "definition_confidence": theme.get("definition_confidence", "medium"),
                    "definition_term_refs": list(theme.get("definition_term_refs") or []),
                    "source_type_definition": "Oracle proofing queue entry",
                    "recommended_path": destination_paths.get(destination, ""),
                    "evidence_refs": [
                        {
                            "source_id": item.get("source_id"),
                            "relative_path": item.get("relative_path"),
                            "matched_keywords": item.get("matched_keywords", []),
                        }
                        for item in evidence[:4]
                    ],
                    "proofing_rule": "Verify source provenance, condense into approved runtime knowledge, then commit on review.",
                    "promoted_at": existing.get("promoted_at"),
                    "promoted_path": existing.get("promoted_path"),
                    "promoted_format": existing.get("promoted_format"),
                }
            )
    entries.sort(key=lambda item: (item["destination"], item["title"].lower()))
    promoted_count = sum(1 for item in entries if str(item.get("status") or "") == "promoted")
    return {
        "generated_at": utc_now_iso(),
        "registry_path": registry_payload.get("registry_path"),
        "report_path": str(default_knowns_proofing_queue_path(root)),
        "queue_path": str(default_knowns_proofing_queue_path(root)),
        "entry_count": len(entries),
        "queued_count": len(entries) - promoted_count,
        "promoted_count": promoted_count,
        "destination_counts": destination_counts,
        "entries": entries,
    }


def write_knowns_proofing_queue(
    root: Path,
    registry_payload: dict,
    *,
    output_path: Path | None = None,
) -> dict:
    root = Path(root)
    destination = output_path or default_knowns_proofing_queue_path(root)
    payload = build_knowns_proofing_queue(root, registry_payload)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _destination_root(root: Path, destination: str) -> Path:
    roots = {
        "knowns": knowns_root(root) / "approved",
        "library": library_root(root) / "knowns",
        "encyclopedia_candidates": encyclopedia_root(root) / "candidates",
        "datatables": datatables_root(root) / "knowns",
        "scenario_lab": labs_root(root) / "knowns",
    }
    return roots.get(destination, knowns_root(root) / "review")


def _promotion_target_path(root: Path, entry: dict) -> Path:
    theme_id = str(entry.get("theme_id") or "unknown_theme")
    destination = str(entry.get("destination") or "knowns")
    target_root = _destination_root(root, destination)
    suffix = ".md" if destination == "library" else ".json"
    return target_root / f"{theme_id}{suffix}"


def _promotion_record(theme: dict, entry: dict, target_path: Path) -> dict:
    evidence = theme.get("evidence") or entry.get("evidence_refs") or []
    definition_basis = str(theme.get("definition_basis") or entry.get("definition_basis") or "theme_summary")
    definition_confidence = str(theme.get("definition_confidence") or entry.get("definition_confidence") or "medium")
    operator_notes = str(theme.get("operator_notes") or entry.get("operator_notes") or "")
    return {
        "theme_id": str(theme.get("theme_id") or entry.get("theme_id") or ""),
        "title": str(theme.get("title") or entry.get("title") or ""),
        "source_label": str(theme.get("source_label") or entry.get("source_label") or theme.get("title") or ""),
        "owner_floor": "Oracle",
        "destination": str(entry.get("destination") or ""),
        "summary": str(theme.get("proofed_definition") or entry.get("summary") or theme.get("summary") or ""),
        "proofed_definition": str(theme.get("proofed_definition") or theme.get("summary") or entry.get("summary") or ""),
        "operational_use": str(theme.get("operational_use") or operator_notes or "Use after Oracle proofing and Morpheus review."),
        "operator_notes": operator_notes,
        "definition_basis": definition_basis,
        "definition_confidence": definition_confidence,
        "definition_term_refs": list(theme.get("definition_term_refs") or []),
        "category": str(theme.get("category") or ""),
        "consensus_band": str(theme.get("consensus_band") or entry.get("consensus_band") or "edge"),
        "mission_statement": str(theme.get("mission_statement") or ""),
        "support_source_count": int(theme.get("support_source_count", entry.get("support_source_count", 0)) or 0),
        "support_document_count": int(theme.get("support_document_count", entry.get("support_document_count", 0)) or 0),
        "support_source_ids": list(theme.get("support_source_ids") or []),
        "support_document_paths": list(theme.get("support_document_paths") or []),
        "evidence_refs": [
            {
                "source_id": item.get("source_id"),
                "relative_path": item.get("relative_path"),
                "matched_keywords": item.get("matched_keywords", []),
            }
            for item in evidence[:8]
        ],
        "proofing_rule": str(entry.get("proofing_rule") or ""),
        "recommended_path": str(entry.get("recommended_path") or target_path.parent),
        "promoted_path": str(target_path),
        "promoted_at": utc_now_iso(),
    }


def _promotion_markdown(record: dict) -> str:
    lines = [
        f"# {record.get('title', 'Known Theme')}",
        "",
        f"- Theme ID: `{record.get('theme_id', '')}`",
        f"- Source Label: `{record.get('source_label', '')}`",
        f"- Owner Floor: `{record.get('owner_floor', 'Oracle')}`",
        f"- Category: `{record.get('category', '')}`",
        f"- Consensus Band: `{record.get('consensus_band', '')}`",
        "",
        "## Summary",
        "",
        str(record.get("summary") or "No summary available."),
        "",
        "## Proofed Definition",
        "",
        str(record.get("proofed_definition") or "No proofed definition available."),
        "",
        "## Operational Use",
        "",
        str(record.get("operational_use") or "Use after Oracle proofing and Morpheus review."),
        "",
        "## Operator Notes",
        "",
        str(record.get("operator_notes") or "No operator notes recorded."),
        "",
        "## Definition Fidelity",
        "",
        f"- Basis: `{record.get('definition_basis', '')}`",
        f"- Confidence: `{record.get('definition_confidence', '')}`",
        f"- Term Refs: `{', '.join(record.get('definition_term_refs', []) or []) or '-'}`",
        "",
        "## Evidence",
        "",
    ]
    evidence = record.get("evidence_refs") or []
    if evidence:
        for item in evidence:
            lines.append(
                f"- `{item.get('source_id', '-')}` :: `{item.get('relative_path', '-')}`"
                f" :: keywords={', '.join(item.get('matched_keywords', [])) or '-'}"
            )
    else:
        lines.append("- No evidence references captured.")
    lines.extend(
        [
            "",
            "## Proofing Rule",
            "",
            str(record.get("proofing_rule") or "Verify source provenance, condense into approved runtime knowledge, then commit on review."),
            "",
            f"_Promoted at {record.get('promoted_at', '')}_",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def _write_promoted_record(target_path: Path, destination: str, record: dict) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if destination == "library":
        target_path.write_text(_promotion_markdown(record), encoding="utf-8")
        return
    target_path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def promote_knowns_entries(
    root: Path,
    registry_payload: dict,
    queue_payload: dict,
    *,
    entry_ids: list[str] | None = None,
    destinations: list[str] | None = None,
    max_entries: int | None = None,
    ledger_path: Path | None = None,
    queue_path: Path | None = None,
) -> dict:
    root = Path(root)
    queue_file = queue_path or default_knowns_proofing_queue_path(root)
    ledger_file = ledger_path or default_knowns_promotion_ledger_path(root)
    theme_map = {str(item.get("theme_id") or ""): item for item in registry_payload.get("themes") or []}
    selected_ids = {item for item in (entry_ids or []) if item}
    selected_destinations = {item for item in (destinations or []) if item}
    limit = max_entries if isinstance(max_entries, int) and max_entries > 0 else None
    entries = queue_payload.get("entries") or []

    promoted: list[dict] = []
    skipped: list[dict] = []
    failed: list[dict] = []
    processed = 0

    for entry in entries:
        entry_id = str(entry.get("entry_id") or "")
        destination = str(entry.get("destination") or "")
        include = True
        if selected_ids and entry_id not in selected_ids:
            include = False
        if selected_destinations and destination not in selected_destinations:
            include = False
        if not include:
            continue
        if limit is not None and processed >= limit:
            break

        target_path = _promotion_target_path(root, entry)
        if str(entry.get("status") or "") == "promoted" and target_path.exists():
            skipped.append(
                {
                    "entry_id": entry_id,
                    "destination": destination,
                    "target_path": str(target_path),
                    "reason": "already_promoted",
                }
            )
            continue

        theme = theme_map.get(str(entry.get("theme_id") or ""), {})
        record = _promotion_record(theme, entry, target_path)
        try:
            _write_promoted_record(target_path, destination, record)
            entry["status"] = "promoted"
            entry["promoted_at"] = record["promoted_at"]
            entry["promoted_path"] = str(target_path)
            entry["promoted_format"] = target_path.suffix
            promoted.append(
                {
                    "entry_id": entry_id,
                    "destination": destination,
                    "target_path": str(target_path),
                    "theme_id": record["theme_id"],
                    "title": record["title"],
                }
            )
            processed += 1
        except Exception as exc:
            failed.append(
                {
                    "entry_id": entry_id,
                    "destination": destination,
                    "target_path": str(target_path),
                    "error": str(exc),
                }
            )

    queue_payload["queue_path"] = str(queue_file)
    queue_payload["entry_count"] = len(entries)
    queue_payload["queued_count"] = sum(1 for item in entries if str(item.get("status") or "") != "promoted")
    queue_payload["promoted_count"] = sum(1 for item in entries if str(item.get("status") or "") == "promoted")
    queue_payload["last_promoted_at"] = utc_now_iso() if promoted else queue_payload.get("last_promoted_at")
    queue_file.parent.mkdir(parents=True, exist_ok=True)
    queue_file.write_text(json.dumps(queue_payload, indent=2), encoding="utf-8")

    existing_ledger = read_knowns_promotion_ledger(root, output_path=ledger_file)
    history = list(existing_ledger.get("history") or [])
    batch = {
        "promoted_at": utc_now_iso(),
        "promoted_count": len(promoted),
        "skipped_count": len(skipped),
        "failed_count": len(failed),
        "destinations": sorted({item["destination"] for item in promoted}),
        "entries": promoted[:12],
    }
    if promoted or skipped or failed:
        history.insert(0, batch)
    ledger_payload = {
        "report_path": str(ledger_file),
        "ledger_path": str(ledger_file),
        "queue_path": str(queue_file),
        "updated_at": utc_now_iso(),
        "history": history[:12],
        "total_promoted_entries": queue_payload["promoted_count"],
        "recent_batch": batch,
    }
    ledger_file.parent.mkdir(parents=True, exist_ok=True)
    ledger_file.write_text(json.dumps(ledger_payload, indent=2), encoding="utf-8")

    destination_counts: dict[str, int] = {}
    for item in promoted:
        destination = str(item.get("destination") or "")
        destination_counts[destination] = destination_counts.get(destination, 0) + 1

    return {
        "queue_path": str(queue_file),
        "report_path": str(queue_file),
        "ledger_path": str(ledger_file),
        "promoted_count": len(promoted),
        "skipped_count": len(skipped),
        "failed_count": len(failed),
        "destination_counts": destination_counts,
        "promoted": promoted,
        "skipped": skipped,
        "failed": failed,
        "queue": queue_payload,
        "ledger": ledger_payload,
    }


def build_knowns_queue_objects(
    root: Path,
    *,
    queue_payload: dict | None = None,
    registry_payload: dict | None = None,
) -> dict:
    root = Path(root)
    queue_payload = queue_payload or read_knowns_proofing_queue(root)
    registry_payload = registry_payload or read_knowns_registry(root)
    entries = list(queue_payload.get("entries") or [])
    theme_map = {
        str(theme.get("theme_id") or ""): theme
        for theme in (registry_payload.get("themes") or [])
        if theme.get("theme_id")
    }
    destination_order = ["knowns", "library", "encyclopedia_candidates", "datatables", "scenario_lab"]
    objects: list[dict] = []
    for destination in destination_order:
        grouped = [entry for entry in entries if str(entry.get("destination") or "") == destination]
        if not grouped:
            continue
        pending = [entry for entry in grouped if str(entry.get("status") or "") != "promoted"]
        promoted = [entry for entry in grouped if str(entry.get("status") or "") == "promoted"]
        first_pending = pending[0] if pending else None
        objects.append(
            {
                "object_id": f"oracle.promotion_queue.{destination}",
                "entity_kind": "promotion_queue",
                "owner_floor": "Oracle",
                "review_floor": "Morpheus",
                "destination": destination,
                "status": "ready" if pending else "complete",
                "entry_count": len(grouped),
                "pending_count": len(pending),
                "promoted_count": len(promoted),
                "target_root": str(_destination_root(root, destination)),
                "next_entry_id": first_pending.get("entry_id") if first_pending else None,
                "next_title": first_pending.get("title") if first_pending else None,
                "next_definition": (
                    theme_map.get(str(first_pending.get("theme_id") if first_pending else ""), {}).get("proofed_definition")
                    if first_pending
                    else None
                ),
                "action_surface": ["Oracle", "Morpheus", "Smith"],
                "proofing_rule": "Definitions are proofed in Oracle, reviewed in Morpheus, and committed to destination roots.",
            }
        )
    return {
        "generated_at": utc_now_iso(),
        "queue_objects_path": str(default_knowns_queue_objects_path(root)),
        "report_path": str(default_knowns_queue_objects_path(root)),
        "object_count": len(objects),
        "total_entries": len(entries),
        "pending_entries": sum(int(item.get("pending_count", 0) or 0) for item in objects),
        "promoted_entries": sum(int(item.get("promoted_count", 0) or 0) for item in objects),
        "objects": objects,
        "summary": "Oracle promotion queues are durable first-class objects, not only file naming conventions.",
    }


def read_knowns_queue_objects(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_knowns_queue_objects_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_knowns_queue_objects(
    root: Path,
    *,
    queue_payload: dict | None = None,
    registry_payload: dict | None = None,
    output_path: Path | None = None,
) -> dict:
    destination = output_path or default_knowns_queue_objects_path(root)
    payload = build_knowns_queue_objects(root, queue_payload=queue_payload, registry_payload=registry_payload)
    payload["queue_objects_path"] = str(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def build_knowns_declassification_audit(
    root: Path,
    *,
    registry_payload: dict | None = None,
    queue_payload: dict | None = None,
    ledger_payload: dict | None = None,
) -> dict:
    root = Path(root)
    registry_payload = registry_payload or read_knowns_registry(root)
    queue_payload = queue_payload or read_knowns_proofing_queue(root)
    ledger_payload = ledger_payload or read_knowns_promotion_ledger(root)

    documents = list(registry_payload.get("documents") or [])
    themes = list(registry_payload.get("themes") or [])
    promoted_theme_ids = {
        str(item.get("theme_id") or "")
        for item in (queue_payload.get("entries") or [])
        if str(item.get("status") or "") == "promoted"
    }
    fingerprint_groups: dict[str, list[dict]] = {}
    theme_refs: dict[str, list[str]] = {}
    for theme in themes:
        theme_id = str(theme.get("theme_id") or "")
        for ref in theme.get("support_document_paths") or []:
            theme_refs.setdefault(str(ref), []).append(theme_id)

    for document in documents:
        title = str(document.get("title") or "")
        excerpt = str(document.get("excerpt") or document.get("summary") or "")
        fingerprint = _normalize(f"{title} {excerpt[:180]}")[:180]
        if not fingerprint:
            continue
        fingerprint_groups.setdefault(fingerprint, []).append(document)

    duplicate_groups = []
    duplicate_lookup: dict[str, int] = {}
    for fingerprint, grouped_docs in fingerprint_groups.items():
        if len(grouped_docs) < 2:
            continue
        references = []
        for item in grouped_docs[:8]:
            doc_ref = f"{item.get('source_id')}:{item.get('relative_path')}"
            duplicate_lookup[doc_ref] = len(grouped_docs)
            references.append(
                {
                    "source_id": item.get("source_id"),
                    "provenance_links": [
                        {
                            "label": "source document",
                            "path": item.get("relative_path"),
                        }
                    ],
                    "title": item.get("title"),
                }
            )
        duplicate_groups.append(
            {
                "fingerprint": fingerprint,
                "document_count": len(grouped_docs),
                "documents": references,
            }
        )
    duplicate_groups.sort(key=lambda item: (-int(item.get("document_count", 0)), str(item.get("fingerprint") or "")))

    candidates = []
    for document in documents:
        doc_ref = f"{document.get('source_id')}:{document.get('relative_path')}"
        matched_theme_ids = sorted(set(theme_refs.get(doc_ref, [])))
        reasons: list[str] = []
        source_id = str(document.get("source_id") or "")
        relative_path = str(document.get("relative_path") or "")
        lowered_ref = _normalize(f"{source_id} {relative_path} {document.get('title') or ''}")
        if duplicate_lookup.get(doc_ref, 0) > 1:
            reasons.append("duplicate_excerpt_cluster")
        if matched_theme_ids:
            reasons.append("absorbed_into_knowns")
        if matched_theme_ids and any(token in lowered_ref for token in ("log", "handoff", "note", "wizard", "alignment")):
            reasons.append("raw_alignment_note")
        if not reasons:
            continue
        candidates.append(
            {
                "source_id": source_id,
                "title": str(document.get("title") or relative_path),
                "matched_theme_ids": matched_theme_ids,
                "duplicate_group_size": duplicate_lookup.get(doc_ref, 0),
                "promoted_theme_ids": [item for item in matched_theme_ids if item in promoted_theme_ids],
                "declassify_ready": bool(matched_theme_ids) or duplicate_lookup.get(doc_ref, 0) > 1,
                "reasons": reasons,
                "provenance_links": [
                    {
                        "label": "source document",
                        "path": relative_path,
                    }
                ],
                "evidence_summary": str(document.get("excerpt") or document.get("summary") or "")[:220],
            }
        )
    candidates.sort(
        key=lambda item: (
            0 if item.get("declassify_ready") else 1,
            -len(item.get("matched_theme_ids") or []),
            -int(item.get("duplicate_group_size", 0) or 0),
            str(item.get("title") or "").lower(),
        )
    )

    recent_batch = ledger_payload.get("recent_batch") or {}
    return {
        "generated_at": utc_now_iso(),
        "audit_path": str(default_knowns_declassification_audit_path(root)),
        "report_path": str(default_knowns_declassification_audit_path(root)),
        "document_count": len(documents),
        "theme_count": len(themes),
        "candidate_count": len(candidates),
        "ready_count": sum(1 for item in candidates if item.get("declassify_ready")),
        "duplicate_group_count": len(duplicate_groups),
        "promoted_theme_count": len(promoted_theme_ids),
        "recent_promotion_count": int(recent_batch.get("promoted_count", 0) or 0),
        "candidates": candidates[:64],
        "duplicate_groups": duplicate_groups[:20],
        "summary": (
            f"Doctrine declassification audit summarized {len(candidates)} corroboration candidates and "
            f"{len(duplicate_groups)} duplicate content groups after proofing; AI logs remain corroboration-only."
        ),
    }


def write_knowns_declassification_audit(
    root: Path,
    *,
    registry_payload: dict | None = None,
    queue_payload: dict | None = None,
    ledger_payload: dict | None = None,
    output_path: Path | None = None,
) -> dict:
    root = Path(root)
    destination = output_path or default_knowns_declassification_audit_path(root)
    payload = build_knowns_declassification_audit(
        root,
        registry_payload=registry_payload,
        queue_payload=queue_payload,
        ledger_payload=ledger_payload,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
