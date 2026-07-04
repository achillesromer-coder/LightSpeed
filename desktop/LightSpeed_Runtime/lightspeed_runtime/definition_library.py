from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

from lightspeed_runtime.contracts import utc_now_iso
from lightspeed_runtime.storage_paths import knowns_root


def default_oracle_definition_library_path(root: Path) -> Path:
    return knowns_root(root) / "oracle_definition_library.json"


def default_it_dictionary_path(root: Path) -> Path:
    return knowns_root(root).parent / "library" / "dictionary" / "IT.json"


def _normalize_token(value: Any) -> str:
    text = str(value or "").strip().lower()
    return re.sub(r"[^a-z0-9]+", "", text)


def _dedupe_preserve(values: Iterable[Any]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        key = _normalize_token(text)
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return out


CURATED_TERM_DEFINITIONS = {
    "achilles": {
        "term": "Achilles",
        "category": "operator",
        "dictionary_category": "IT",
        "shorthand": "A",
        "definition": (
            "The governed operator layer for LightSpeed: retrieves context, proposes bounded actions, "
            "keeps rationale visible, and routes higher-impact work through approval gates."
        ),
        "operational_use": "Neo houses Achilles as the primary operator console and manager-agent surface.",
        "owner_floor": "Neo",
        "aliases": ["Achilles operator", "Achilles protocol"],
        "confidence": "high",
    },
    "cognigrex": {
        "term": "Cognigrex",
        "category": "operator",
        "dictionary_category": "IT",
        "shorthand": "CGX",
        "definition": (
            "The coordinated execution body under Achilles oversight, used to describe distributed floor, "
            "tool, and project work without giving it unbounded authority."
        ),
        "operational_use": "Cognigrex is represented through governed Smith jobs, floor tools, and action ledgers.",
        "owner_floor": "Neo",
        "aliases": ["Cognigrex oversight", "execution body"],
        "confidence": "high",
    },
    "oracle": {
        "term": "Oracle",
        "category": "floor",
        "dictionary_category": "IT",
        "shorthand": "O",
        "floor_aliases": ["Z-2", "O"],
        "definition": (
            "The canonical knowledge, catalog, provenance, definition, and proofing floor for LightSpeed."
        ),
        "operational_use": "Oracle owns knowns, entity registries, catalog shells, curated tables, and proof queues.",
        "owner_floor": "Oracle",
        "aliases": ["knowledge floor", "catalog floor"],
        "confidence": "high",
    },
    "morpheus": {
        "term": "Morpheus",
        "category": "floor",
        "dictionary_category": "IT",
        "shorthand": "M",
        "floor_aliases": ["Z-1", "M1"],
        "definition": "The review and proofing floor for comparing retrieved material, evidence, and queue items.",
        "operational_use": "Morpheus turns search results into review decisions and Smith proofing jobs.",
        "owner_floor": "Morpheus",
        "aliases": ["review floor", "proofing floor"],
        "confidence": "high",
    },
    "the_construct": {
        "term": "TheConstruct",
        "category": "floor",
        "dictionary_category": "IT",
        "shorthand": "C",
        "floor_aliases": ["Z0", "C", "C-A"],
        "definition": "The scenario, simulation, zoning, and holospace floor for empirical and lab work.",
        "operational_use": "TheConstruct consumes empirical catalogs, presets, GMAT batches, and scenario outputs.",
        "owner_floor": "TheConstruct",
        "aliases": ["Construct", "holospace", "scenario floor"],
        "confidence": "high",
    },
    "architect": {
        "term": "Architect",
        "category": "floor",
        "dictionary_category": "IT",
        "shorthand": "A",
        "floor_aliases": ["Z+1", "A", "C-A"],
        "definition": "The governance, approval, packaging, and publish floor.",
        "operational_use": "Architect owns publish bundles, approval ledgers, finalization queues, and project governance.",
        "owner_floor": "Architect",
        "aliases": ["governance floor", "publish floor"],
        "confidence": "high",
    },
    "smith": {
        "term": "Smith",
        "category": "floor",
        "dictionary_category": "IT",
        "shorthand": "S",
        "floor_aliases": ["Z-3", "S"],
        "definition": "The job router, tool executor gateway, indexing, and controlled background-work floor.",
        "operational_use": "Smith tracks queued and completed cross-floor work through a durable router state.",
        "owner_floor": "Smith",
        "aliases": ["job router", "executor gateway"],
        "confidence": "high",
    },
    "merovingian": {
        "term": "Merovingian",
        "category": "floor",
        "dictionary_category": "IT",
        "shorthand": "ME",
        "floor_aliases": ["Z-4", "ME"],
        "definition": "The audit, diagnostics, quality, telemetry, and runtime export floor.",
        "operational_use": "Merovingian owns ledgers, logs, validation baselines, and runtime reports.",
        "owner_floor": "Merovingian",
        "aliases": ["audit floor", "quality floor"],
        "confidence": "high",
    },
    "trinity": {
        "term": "Trinity",
        "category": "floor",
        "dictionary_category": "IT",
        "shorthand": "T",
        "floor_aliases": ["Z+3", "T"],
        "definition": "The operator portal, setup, settings, and governance-routing floor.",
        "operational_use": "Trinity exposes portal controls, setup wizards, and cross-floor administrative surfaces.",
        "owner_floor": "Trinity",
        "aliases": ["operator portal", "setup floor"],
        "confidence": "high",
    },
    "neo": {
        "term": "Neo",
        "category": "floor",
        "dictionary_category": "IT",
        "shorthand": "N",
        "floor_aliases": ["Z+2", "N"],
        "definition": "The Achilles operator shell and primary human-facing planning console.",
        "operational_use": "Neo retrieves, briefs, proposes, approves, and executes bounded Achilles actions.",
        "owner_floor": "Neo",
        "aliases": ["operator shell", "Achilles console"],
        "confidence": "high",
    },
    "z_axis": {
        "term": "Z Axis",
        "category": "architecture",
        "dictionary_category": "IT",
        "shorthand": "ZA",
        "definition": "The smart-floor ownership structure that houses LightSpeed functions by responsibility.",
        "operational_use": "Z Axis replaces loose folder sprawl with Oracle, Morpheus, Construct, Architect, Neo, Trinity, Smith, and Merovingian ownership.",
        "owner_floor": "Trinity",
        "aliases": ["smart floors", "Z floors"],
        "confidence": "high",
    },
    "smart_floor": {
        "term": "Smart Floor",
        "category": "architecture",
        "dictionary_category": "IT",
        "shorthand": "SF",
        "definition": (
            "A responsibility-owned Z Axis surface that exposes only the actions, data, and tools "
            "its owner floor should directly control."
        ),
        "operational_use": "Use smart floors to collapse sprawl into a single source of responsibility and routing.",
        "owner_floor": "Trinity",
        "aliases": ["floor shell", "owned surface", "smart floor system"],
        "confidence": "high",
    },
    "bento": {
        "term": "Bento",
        "category": "ui",
        "dictionary_category": "IT",
        "shorthand": "B",
        "definition": (
            "A compact, tile-based interface unit that presents one action, preview, artifact, control, "
            "or visualization without adding a blank page."
        ),
        "operational_use": "Use Bento as the default visible unit across project walls, floor shells, and settings surfaces.",
        "owner_floor": "Trinity",
        "aliases": ["bento system", "bento tile", "smart widget"],
        "confidence": "high",
    },
    "z_direct": {
        "term": "Z Direct",
        "category": "architecture",
        "dictionary_category": "IT",
        "shorthand": "ZD",
        "floor_aliases": ["ZD", "Z-D"],
        "definition": "A direct object and action access layer for governed smart-floor records.",
        "operational_use": "Z Direct should expose committed objects and jump actions without forcing raw file traversal.",
        "owner_floor": "Trinity",
        "aliases": ["direct registry", "object access"],
        "confidence": "medium",
    },
    "knowns": {
        "term": "Knowns",
        "category": "knowledge",
        "dictionary_category": "IT",
        "shorthand": "K",
        "definition": "Approved compact knowledge records extracted from mounted sources and proofed before reuse.",
        "operational_use": "Knowns feed Neo briefs, Oracle cataloging, Morpheus review, datatables, and scenario-lab queues.",
        "owner_floor": "Oracle",
        "aliases": ["known knowns", "approved knowns"],
        "confidence": "high",
    },
    "heliocentric_zoning_grid": {
        "term": "Heliocentric Zoning Grid",
        "category": "science",
        "dictionary_category": "IT",
        "shorthand": "HZG",
        "definition": (
            "A Sun-centered asteroid zoning workflow that combines orbital bands, physical proxies, "
            "accessibility measures, clusters, shortlists, and GMAT target batches."
        ),
        "operational_use": "TheConstruct uses it as the Romer-first scenario path from empirical catalog to simulation output.",
        "owner_floor": "TheConstruct",
        "aliases": ["zoning grid", "asteroid zoning"],
        "confidence": "high",
    },
    "construct_architect_bridge": {
        "term": "Construct-Architect Bridge",
        "category": "workflow",
        "dictionary_category": "IT",
        "shorthand": "C-A",
        "definition": (
            "A shorthand for work that must move between TheConstruct and Architect as a governed handoff, "
            "typically after simulation or scenario validation and before publish packaging."
        ),
        "operational_use": "Use C-A when simulation output is ready for approval, packaging, or publish routing.",
        "owner_floor": "Architect",
        "aliases": ["C-A", "Construct-Architect", "Construct Architect", "CA"],
        "confidence": "medium",
    },
    "rfs": {
        "term": "RFS",
        "category": "strategy",
        "dictionary_category": "IT",
        "shorthand": "RFS",
        "definition": (
            "A project-specific strategic filter referenced after zoning and clustering. Its scoring policy "
            "must remain explicit in a run manifest before operational decisions use it."
        ),
        "operational_use": "Apply only after zoning and cluster detection, not as a global pre-filter.",
        "owner_floor": "Architect",
        "aliases": ["RFS classification"],
        "confidence": "medium",
    },
    "emff": {
        "term": "EMFF",
        "category": "strategy",
        "dictionary_category": "IT",
        "shorthand": "EMFF",
        "definition": (
            "A project-specific strategic filter referenced after zoning and clustering. Its exact scoring "
            "contract must be validated before publish or mission execution."
        ),
        "operational_use": "Apply only to candidate clusters or target shortlists with provenance and validation state attached.",
        "owner_floor": "Architect",
        "aliases": ["EMFF classification"],
        "confidence": "medium",
    },
}


IT_WORKFLOW_DEFINITIONS = {
    "bento_widget": {
        "term": "Bento Widget",
        "category": "ui",
        "dictionary_category": "IT",
        "shorthand": "BW",
        "definition": "A compact project or floor tile that exposes one artifact, preview, control, table, document, or visualization.",
        "operational_use": "Use bento widgets as the default UI unit instead of blank pages or isolated buttons.",
        "owner_floor": "Trinity",
        "aliases": ["smart widget", "bento tile"],
        "confidence": "high",
    },
    "project_component_set": {
        "term": "Project Component Set",
        "category": "project",
        "dictionary_category": "IT",
        "shorthand": "PCS",
        "definition": "A project subfolder group containing documents, tables, visuals, tasks, simulations, and widgets for one work area.",
        "operational_use": "When a project is selected, show its component sets as navigable bento groups.",
        "owner_floor": "Architect",
        "aliases": ["component set", "project subfolder"],
        "confidence": "high",
    },
    "interactive_artifact": {
        "term": "Interactive Artifact",
        "category": "ui",
        "dictionary_category": "IT",
        "shorthand": "IA",
        "definition": "A file, table, dashboard, simulation, icon, or preview tile that can be opened, edited, routed, or promoted.",
        "operational_use": "Attach artifacts to bento widgets and open them through preview, edit, or full-screen actions.",
        "owner_floor": "Trinity",
        "aliases": ["artifact tile", "smart artifact"],
        "confidence": "high",
    },
    "original_file": {
        "term": "Original File",
        "category": "data",
        "dictionary_category": "IT",
        "shorthand": "OF",
        "definition": "The unchanged source file received by Oracle and preserved for editing, attachment, provenance, or project assignment.",
        "operational_use": "Keep the original available while ingestion extracts components for review and table/object updates.",
        "owner_floor": "Oracle",
        "aliases": ["source file", "raw original"],
        "confidence": "high",
    },
    "ingestion_pass": {
        "term": "Ingestion Pass",
        "category": "workflow",
        "dictionary_category": "IT",
        "shorthand": "IP",
        "definition": "The Oracle-owned process that breaks a source into components, strings, tasks, definitions, tables, and partial objects.",
        "operational_use": "Send extracted components through Morpheus review before they update other floor records.",
        "owner_floor": "Oracle",
        "aliases": ["ingest", "file breakdown"],
        "confidence": "high",
    },
    "partial_object_data": {
        "term": "Partial Object Data",
        "category": "data",
        "dictionary_category": "IT",
        "shorthand": "POD",
        "definition": "An incomplete object record that gains fields as later documents corroborate or add missing attributes.",
        "operational_use": "Use for warehouse dimensions, assets, people, tasks, or scientific objects that are built across sources.",
        "owner_floor": "Oracle",
        "aliases": ["incomplete object", "progressive object"],
        "confidence": "high",
    },
    "handoff_queue": {
        "term": "Handoff Queue",
        "category": "workflow",
        "dictionary_category": "IT",
        "shorthand": "HQ",
        "definition": "A Z Direct queue carrying an object, rationale, source links, and requested floor action between smart floors.",
        "operational_use": "Every queued handoff should confirm received, update, complete, or delete/declassify when resolved.",
        "owner_floor": "Smith",
        "aliases": ["Z Direct queue", "floor handoff"],
        "confidence": "high",
    },
    "brain_stem": {
        "term": "Brain Stem",
        "category": "architecture",
        "dictionary_category": "IT",
        "shorthand": "BS",
        "definition": "The Z Axis operating layer that keeps the smart floors connected as compartmentalized thinking and memory.",
        "operational_use": "Use as the mental model for the whole platform: floors specialize, Z Direct connects, Neo narrates.",
        "owner_floor": "Trinity",
        "aliases": ["Z Axis brain stem", "smart-floor nervous system"],
        "confidence": "medium",
    },
    "internal_monologue": {
        "term": "Internal Monologue",
        "category": "operator",
        "dictionary_category": "IT",
        "shorthand": "IM",
        "definition": "Neo's role as the first contact, guidance layer, and explanation surface across Achilles and Cognigrex work.",
        "operational_use": "Neo should brief, propose, explain, and route rather than silently executing high-impact actions.",
        "owner_floor": "Neo",
        "aliases": ["Neo narration", "operator guidance"],
        "confidence": "high",
    },
    "neural_tree": {
        "term": "Neural Tree",
        "category": "knowledge",
        "dictionary_category": "IT",
        "shorthand": "NT",
        "definition": "A visual knowledge network of definitions, empirical catalogs, projects, objects, and proofed relationships.",
        "operational_use": "Use as Oracle's intelligence-desk background and let search results take over the main panel when selected.",
        "owner_floor": "Oracle",
        "aliases": ["knowledge network", "definition graph"],
        "confidence": "high",
    },
    "mode_switcher": {
        "term": "Mode Switcher",
        "category": "ui",
        "dictionary_category": "IT",
        "shorthand": "MS",
        "definition": "A visible dropdown for Workspace, Operator, Review, Holospace, Publish, and Settings modes.",
        "operational_use": "Keep mode changes explicit so WASD, search, settings, and publish controls only appear where expected.",
        "owner_floor": "Trinity",
        "aliases": ["mode dropdown", "operator mode"],
        "confidence": "high",
    },
    "external_tools_toggle": {
        "term": "External Tools Toggle",
        "category": "settings",
        "dictionary_category": "IT",
        "shorthand": "ETT",
        "definition": "A Trinity settings/API control that enables or disables optional external tools without blocking local launch.",
        "operational_use": "Show missing tools as disabled with install/approval tasks for Neo instead of crashing the shell.",
        "owner_floor": "Trinity",
        "aliases": ["API tools toggle", "external dependencies"],
        "confidence": "high",
    },
    "ephemeris_result": {
        "term": "Ephemeris Result",
        "category": "science",
        "dictionary_category": "IT",
        "shorthand": "ER",
        "definition": "A saved simulation or mission-state output that can be revised, shared, or re-simulated later.",
        "operational_use": "TheConstruct should persist simulation results as reviewable artifacts, not transient screen-only output.",
        "owner_floor": "TheConstruct",
        "aliases": ["ephemerides", "mission state result"],
        "confidence": "high",
    },
}

CURATED_TERM_DEFINITIONS.update(IT_WORKFLOW_DEFINITIONS)


THEME_DEFINITION_BINDINGS = {
    "mission_stewardship": {
        "definition": (
            "Stewardship-first expansion doctrine: growth toward Type-I-scale capability is constrained by "
            "non-invasive extraction, ecological repair, and explicit governance gates."
        ),
        "operational_use": "Keep mission framing visible in approvals, publish packages, and strategic filters.",
        "term_refs": ["knowns", "architect"],
        "confidence": "high",
    },
    "achilles_operator": {
        "definition": CURATED_TERM_DEFINITIONS["achilles"]["definition"],
        "operational_use": CURATED_TERM_DEFINITIONS["achilles"]["operational_use"],
        "term_refs": ["achilles", "neo"],
        "confidence": "high",
    },
    "cognigrex_body": {
        "definition": CURATED_TERM_DEFINITIONS["cognigrex"]["definition"],
        "operational_use": CURATED_TERM_DEFINITIONS["cognigrex"]["operational_use"],
        "term_refs": ["cognigrex", "smith"],
        "confidence": "high",
    },
    "governance_ip": {
        "definition": (
            "Governance separation between EMASSC as IP custodian and Romer as commercial executor, "
            "with approvals and publish boundaries kept explicit."
        ),
        "operational_use": "Route approval and publish work through Architect; keep execution artifacts bound to Romer workspaces.",
        "term_refs": ["architect", "knowns"],
        "confidence": "high",
    },
    "smart_floor_os": {
        "definition": CURATED_TERM_DEFINITIONS["z_axis"]["definition"],
        "operational_use": CURATED_TERM_DEFINITIONS["z_axis"]["operational_use"],
        "term_refs": ["z_axis", "trinity"],
        "confidence": "high",
    },
    "proofed_knowns": {
        "definition": CURATED_TERM_DEFINITIONS["knowns"]["definition"],
        "operational_use": CURATED_TERM_DEFINITIONS["knowns"]["operational_use"],
        "term_refs": ["knowns", "oracle", "morpheus"],
        "confidence": "high",
    },
    "simulation_pipeline": {
        "definition": CURATED_TERM_DEFINITIONS["heliocentric_zoning_grid"]["definition"],
        "operational_use": CURATED_TERM_DEFINITIONS["heliocentric_zoning_grid"]["operational_use"],
        "term_refs": ["heliocentric_zoning_grid", "the_construct"],
        "confidence": "high",
    },
    "ui_operator_model": {
        "definition": (
            "A single operator OS interaction model: visible mode, compact grouped actions, predictable "
            "settings, and Neo as the Achilles-facing control surface."
        ),
        "operational_use": "Use bento/status cards and grouped action bars instead of blank pages or hidden click behavior.",
        "term_refs": ["neo", "trinity", "z_direct"],
        "confidence": "high",
    },
    "alignment_cleanup": {
        "definition": (
            "The active reduction rule for LightSpeed: extract durable knowledge and operational records, "
            "then declassify or archive duplicated logs, raw notes, and compatibility shells."
        ),
        "operational_use": "Prefer compact ledgers, weekly logs, and floor-owned registries over scattered run files.",
        "term_refs": ["merovingian", "oracle", "smith"],
        "confidence": "high",
    },
    "empirical_dataset_layer": {
        "definition": (
            "The mounted empirical layer used to bridge macro asteroid mapping, micro mission validation, "
            "simulation models, and reference imagery into curated Oracle and Construct-ready records."
        ),
        "operational_use": "Use as the preferred source for zoning presets, clusterable inputs, and GMAT target batches.",
        "term_refs": ["oracle", "the_construct", "heliocentric_zoning_grid"],
        "confidence": "high",
    },
}


def read_oracle_definition_library(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_oracle_definition_library_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def proof_definition_for_theme(theme: dict) -> dict:
    theme_id = str(theme.get("theme_id") or "")
    binding = THEME_DEFINITION_BINDINGS.get(theme_id, {})
    definition = binding.get("definition") or str(theme.get("summary") or "")
    operational_use = binding.get("operational_use") or "Use after Oracle proofing and Morpheus review."
    confidence = _normalize_confidence(binding.get("confidence") or theme.get("definition_confidence") or "medium")
    return {
        "theme_id": theme_id,
        "source_label": str(theme.get("title") or theme_id or "theme"),
        "definition": definition,
        "operational_use": operational_use,
        "operator_notes": operational_use,
        "definition_basis": "curated_oracle_dictionary" if binding else "theme_summary",
        "confidence": confidence,
        "term_refs": list(binding.get("term_refs") or []),
    }


def _normalize_confidence(value: str) -> str:
    label = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if label in {"high", "medium", "low"}:
        return label
    if label in {"strong", "confident", "certain"}:
        return "high"
    if label in {"mid", "moderate", "moderately_confident"}:
        return "medium"
    if label in {"weak", "tentative", "uncertain"}:
        return "low"
    return "medium"


def proof_first_dictionary_entry(term_id: str, record: dict) -> dict:
    """
    Return a proof-first normalized record for IT dictionary use.

    This keeps canonical term, aliases, definition, ownership, confidence, and provenance
    together so downstream search surfaces can stay definition-first.
    """
    term = str(record.get("term") or term_id or "").strip()
    category = str(record.get("category") or "general").strip()
    dictionary_category = str(record.get("dictionary_category") or "IT").strip().upper()
    aliases = _dedupe_preserve(
        [
            term,
            term_id.replace("_", " ").title() if term_id else "",
            *list(record.get("aliases") or []),
            *list(record.get("floor_aliases") or []),
            str(record.get("shorthand") or ""),
        ]
    )
    provenance = {
        "source": "curated_seed_set",
        "proofing_status": "curated_definition",
        "source_policy": "Use this definition as Oracle's compact canonical meaning; use source evidence only for provenance.",
        "operational_use": str(record.get("operational_use") or ""),
    }
    return {
        "term_id": term_id,
        "category": category,
        "dictionary_category": dictionary_category,
        "canonical_term": term,
        "term": term,
        "aliases": aliases,
        "definition": str(record.get("definition") or ""),
        "owner_floor": str(record.get("owner_floor") or ""),
        "confidence": _normalize_confidence(record.get("confidence") or "medium"),
        "provenance": provenance,
        "shorthand": str(record.get("shorthand") or ""),
    }


def build_proof_first_it_entries(root: Path | None = None) -> list[dict]:
    """Build proof-first IT entries without mutating the registry."""
    entries = [
        proof_first_dictionary_entry(term_id, record)
        for term_id, record in CURATED_TERM_DEFINITIONS.items()
        if str(record.get("dictionary_category") or "").upper() == "IT"
    ]
    entries.sort(key=lambda item: str(item.get("canonical_term") or "").lower())
    return entries


def search_it_dictionary(query: str, *, entries: list[dict] | None = None) -> list[dict]:
    """
    Search the IT dictionary with suffix support.

    - `IT` returns the whole category.
    - `neo.IT` searches the IT category for Neo and alias matches.
    """
    normalized = str(query or "").strip()
    if not normalized:
        return []

    entries = list(entries or build_proof_first_it_entries())
    if normalized.upper() == "IT":
        return entries

    prefix = normalized
    if "." in normalized:
        maybe_prefix, maybe_suffix = normalized.rsplit(".", 1)
        if maybe_suffix.upper() == "IT":
            prefix = maybe_prefix
    needle = _normalize_token(prefix)
    if not needle:
        return entries if normalized.upper().endswith(".IT") else []

    results: list[dict] = []
    for entry in entries:
        haystacks = [
            entry.get("canonical_term"),
            entry.get("term_id"),
            entry.get("shorthand"),
            entry.get("category"),
            entry.get("dictionary_category"),
            *list(entry.get("aliases") or []),
        ]
        if any(needle in _normalize_token(value) for value in haystacks):
            results.append(entry)
    return results


def decorate_theme_with_definition(theme: dict) -> dict:
    proofed = proof_definition_for_theme(theme)
    decorated = dict(theme)
    decorated["proofed_definition"] = proofed["definition"]
    decorated["operational_use"] = proofed["operational_use"]
    decorated["operator_notes"] = proofed["operator_notes"]
    decorated["definition_basis"] = proofed["definition_basis"]
    decorated["definition_confidence"] = proofed["confidence"]
    decorated["definition_term_refs"] = proofed["term_refs"]
    decorated["summary"] = proofed["definition"]
    decorated["source_label"] = proofed.get("source_label") or decorated.get("source_label") or decorated.get("title")
    return decorated


def _term_record(term_id: str, record: dict) -> dict:
    return {
        "term_id": term_id,
        "source_label": record.get("term"),
        **record,
        "proofing_status": "curated_definition",
        "source_policy": "Use this definition as Oracle's compact canonical meaning; use source evidence only for provenance.",
        "operator_notes": record.get("operational_use"),
    }


def build_it_dictionary(root: Path, *, output_path: Path | None = None) -> dict:
    root = Path(root)
    terms = [
        _term_record(term_id, record)
        for term_id, record in CURATED_TERM_DEFINITIONS.items()
        if str(record.get("dictionary_category") or "").upper() == "IT"
    ]
    proof_first_terms = build_proof_first_it_entries(root)
    terms.sort(key=lambda item: str(item.get("term", "")).lower())
    by_letter: dict[str, list[dict]] = {}
    for item in terms:
        letter = str(item.get("term") or "#")[:1].upper()
        if not letter.isalpha():
            letter = "#"
        by_letter.setdefault(letter, []).append(
            {
                "term_id": item.get("term_id"),
                "term": item.get("term"),
                "shorthand": item.get("shorthand"),
                "owner_floor": item.get("owner_floor"),
                "definition": item.get("definition"),
            }
        )
    alias_index: dict[str, list[str]] = {}
    for item in proof_first_terms:
        for alias in item.get("aliases") or []:
            key = _normalize_token(alias)
            if not key:
                continue
            term_ref = str(item.get("term_id") or item.get("canonical_term") or "")
            bucket = alias_index.setdefault(key, [])
            if term_ref and term_ref not in bucket:
                bucket.append(term_ref)
    return {
        "generated_at": utc_now_iso(),
        "dictionary": "IT",
        "dictionary_path": str(output_path or default_it_dictionary_path(root)),
        "owner_floor": "Oracle",
        "control_floor": "Trinity",
        "term_count": len(terms),
        "search_examples": ["IT", "Z Direct.IT", "Neo.IT", "Smart Floor.IT", "Bento.IT", "C-A.IT"],
        "category_policy": (
            "New dictionary categories start as Z Direct tasks for Neo/Oracle classification, "
            "then become Oracle-owned searchable terms after Morpheus review."
        ),
        "new_category_handoff": {
            "request_floor": "Trinity",
            "classification_floor": "Oracle",
            "review_floor": "Morpheus",
            "guidance_floor": "Neo",
            "queue_owner": "Smith",
            "action": "queue_dictionary_category_classification",
        },
        "terms": terms,
        "proof_first_terms": proof_first_terms,
        "a_to_z": by_letter,
        "alias_index": alias_index,
    }


def read_it_dictionary(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_it_dictionary_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_it_dictionary(root: Path, output_path: Path | None = None) -> dict:
    destination = output_path or default_it_dictionary_path(root)
    payload = build_it_dictionary(root, output_path=destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def build_oracle_definition_library(
    root: Path,
    *,
    knowns_registry: dict | None = None,
    empirical_catalog: dict | None = None,
    output_path: Path | None = None,
) -> dict:
    root = Path(root)
    registry = knowns_registry or {}
    empirical = empirical_catalog or {}
    themes = list(registry.get("themes") or [])
    theme_definitions = [proof_definition_for_theme(theme) for theme in themes]
    term_records = []
    for term_id, record in CURATED_TERM_DEFINITIONS.items():
        term_records.append(_term_record(term_id, record))
    term_records.sort(key=lambda item: (str(item.get("category", "")), str(item.get("term", "")).lower()))
    dictionary_categories: dict[str, dict] = {}
    for item in term_records:
        category = str(item.get("dictionary_category") or item.get("category") or "General")
        group = dictionary_categories.setdefault(category, {"term_count": 0, "term_ids": []})
        group["term_count"] += 1
        group["term_ids"].append(item.get("term_id"))
    return {
        "generated_at": utc_now_iso(),
        "definition_library_path": str(output_path or default_oracle_definition_library_path(root)),
        "it_dictionary_path": str(default_it_dictionary_path(root)),
        "term_count": len(term_records),
        "theme_definition_count": len(theme_definitions),
        "empirical_anchor_count": len(empirical.get("headline_knowns") or []),
        "definition_policy": (
            "Definitions are compact Oracle-owned meanings. Evidence paths explain provenance; they do not replace definitions."
        ),
        "dictionary_categories": dictionary_categories,
        "terms": term_records,
        "theme_definitions": [
            {**item, "source_label": item.get("source_label") or item.get("theme_id")}
            for item in theme_definitions
        ],
    }


def write_oracle_definition_library(
    root: Path,
    *,
    knowns_registry: dict | None = None,
    empirical_catalog: dict | None = None,
    output_path: Path | None = None,
) -> dict:
    destination = output_path or default_oracle_definition_library_path(root)
    payload = build_oracle_definition_library(
        root,
        knowns_registry=knowns_registry,
        empirical_catalog=empirical_catalog,
        output_path=destination,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
