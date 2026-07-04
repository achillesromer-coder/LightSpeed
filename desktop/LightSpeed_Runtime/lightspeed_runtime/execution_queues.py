from __future__ import annotations

import json
from pathlib import Path

from lightspeed_runtime.contracts import utc_now_iso
from lightspeed_runtime.storage_paths import canonical_execution_queue_path, finalization_queue_root


def default_execution_queue_path(root: Path) -> Path:
    """Return the canonical Architect-owned finalization queue path."""
    return canonical_execution_queue_path(root)


QUEUE_METADATA = {
    "knowledge_alignment": {
        "title": "Knowledge Alignment Queue",
        "owner_floor": "Oracle",
        "support_floor": "Morpheus",
        "summary": "Condense doctrine, empirical anchors, knowns, and proofing flow into one compact reviewable knowledge layer.",
    },
    "operator_simulation": {
        "title": "Operator and Simulation Queue",
        "owner_floor": "Neo",
        "support_floor": "TheConstruct",
        "summary": "Bind Achilles, empirical anchors, zoning, and scenario outputs into one governed operator and lab flow.",
    },
    "sweep_finalization": {
        "title": "Sweep and Finalization Queue",
        "owner_floor": "Architect",
        "support_floor": "Smith/Merovingian",
        "summary": "Reduce legacy roots, collapse compatibility layers, and keep the app compact under smart-floor ownership.",
    },
}


DEFAULT_ACTIONS = [
    {"action_id": "KA-01", "queue_id": "knowledge_alignment", "title": "Condense empirical bundle into compact Oracle catalog", "priority": 1, "owner_floor": "Oracle", "target_paths": ["Z Axis/Z-2_Oracle/data/library/empirical/empirical_catalog.json"], "summary": "Produce one compact empirical catalog instead of treating the empirical bundle as raw sprawl."},
    {"action_id": "KA-02", "queue_id": "knowledge_alignment", "title": "Fold empirical anchors into Oracle knowns registry", "priority": 1, "owner_floor": "Oracle", "target_paths": ["Z Axis/Z-2_Oracle/data/knowns/knowns_registry.json"], "summary": "Expose empirical anchors as doctrine-backed knowns for Achilles and smart-floor review."},
    {"action_id": "KA-03", "queue_id": "knowledge_alignment", "title": "Promote empirical layer into library and datatables", "priority": 2, "owner_floor": "Oracle", "target_paths": ["Z Axis/Z-2_Oracle/data/library", "Z Axis/Z-2_Oracle/data/datatables"], "summary": "Turn empirical headline anchors into approved Oracle outputs rather than leaving them only in the catalog."},
    {"action_id": "KA-04", "queue_id": "knowledge_alignment", "title": "Use Morpheus as the proofing review surface", "priority": 2, "owner_floor": "Morpheus", "target_paths": ["Z Axis/Z-1_Morpheus", "lightspeed_runtime/desktop_adapters.py"], "summary": "Review proofing queue entries and empirical anchors without opening raw JSON files."},
    {"action_id": "KA-05", "queue_id": "knowledge_alignment", "title": "Reduce duplicate doctrine notes into approved knowns", "priority": 3, "owner_floor": "Oracle", "target_paths": ["Z Axis/Z-2_Oracle/data/knowns", "ai_logs"], "summary": "Extract repeated alignment/doctrine content into approved knowns and declassify duplicate note files."},
    {"action_id": "KA-06", "queue_id": "knowledge_alignment", "title": "Add encyclopedia candidate promotion for empirical anchors", "priority": 3, "owner_floor": "Oracle", "target_paths": ["Z Axis/Z-2_Oracle/data/encyclopedia/candidates"], "summary": "Route empirical headline anchors into reusable encyclopedia candidates where appropriate."},
    {"action_id": "KA-07", "queue_id": "knowledge_alignment", "title": "Upgrade Oracle and Morpheus preview cards", "priority": 4, "owner_floor": "Oracle", "target_paths": ["lightspeed_runtime/desktop_adapters.py", "Z Axis/Oracle.py", "Z Axis/Morpheus.py"], "summary": "Replace inspection-heavy panes with concise preview cards and jump actions."},
    {"action_id": "KA-08", "queue_id": "knowledge_alignment", "title": "Normalize provenance jump actions across smart floors", "priority": 5, "owner_floor": "Oracle", "target_paths": ["lightspeed_runtime/desktop_adapters.py"], "summary": "Keep provenance navigation consistent from Oracle to Morpheus, Neo, and Construct."},
    {"action_id": "OS-01", "queue_id": "operator_simulation", "title": "Wire Neo doctrine overlay to empirical anchors", "priority": 1, "owner_floor": "Neo", "target_paths": ["lightspeed_runtime/desktop_adapters.py", "Z Axis/Neo.py"], "summary": "Show empirical anchors inside Achilles context instead of keeping operator context purely doctrinal."},
    {"action_id": "OS-02", "queue_id": "operator_simulation", "title": "Feed TheConstruct from clusterable empirical inputs", "priority": 1, "owner_floor": "TheConstruct", "target_paths": ["lightspeed_runtime/desktop_adapters.py", "Z Axis/TheConstruct.py"], "summary": "Use clusterable empirical inputs directly for zoning and scenario selection."},
    {"action_id": "OS-03", "queue_id": "operator_simulation", "title": "Bind heliocentric zoning to mounted empirical catalogs", "priority": 2, "owner_floor": "TheConstruct", "target_paths": ["lightspeed_runtime/labs", "Z Axis/Z0_TheConstruct/data/labs"], "summary": "Run zoning against mounted empirical datasets instead of templates wherever data is available."},
    {"action_id": "OS-04", "queue_id": "operator_simulation", "title": "Generate GMAT target batches from shortlisted zones", "priority": 2, "owner_floor": "TheConstruct", "target_paths": ["Z Axis/Z0_TheConstruct/data/labs", "Z Axis/Z+1_Architect/data/publish"], "summary": "Convert shortlisted zoning targets into GMAT-ready mission batches for Romer workflows."},
    {"action_id": "OS-05", "queue_id": "operator_simulation", "title": "Attach simulation outputs to Architect publish chain", "priority": 3, "owner_floor": "Architect", "target_paths": ["Z Axis/Z+1_Architect/data/publish"], "summary": "Keep scenario outputs inside the governed publish path rather than ad hoc files."},
    {"action_id": "OS-06", "queue_id": "operator_simulation", "title": "Let Neo propose simulation projects from knowns", "priority": 3, "owner_floor": "Neo", "target_paths": ["lightspeed_runtime/desktop_adapters.py", "Z Axis/Neo.py"], "summary": "Allow Achilles to propose bounded scenario projects from proofed doctrine and empirical anchors."},
    {"action_id": "OS-07", "queue_id": "operator_simulation", "title": "Create Romer-first simulation presets from empirical roles", "priority": 4, "owner_floor": "TheConstruct", "target_paths": ["lightspeed_runtime/labs", "Z Axis/Z0_TheConstruct/data/labs"], "summary": "Seed zoning and simulation presets from macro mapping and micro validation roles."},
    {"action_id": "OS-08", "queue_id": "operator_simulation", "title": "Reduce duplicate Neo surfaces into one Achilles operator shell", "priority": 5, "owner_floor": "Neo", "target_paths": ["Z Axis/Neo.py", "lightspeed_runtime/desktop_adapters.py"], "summary": "Keep the operator experience compact and approval-gated."},
    {"action_id": "SF-01", "queue_id": "sweep_finalization", "title": "Absorb data/generated compatibility shell into smart-floor owners", "priority": 1, "owner_floor": "Merovingian", "target_paths": ["data/generated", "Z Axis/Z-4_Merovingian/data"], "summary": "Move compatibility-shell outputs into floor-owned destinations and remove flat output dependence."},
    {"action_id": "SF-02", "queue_id": "sweep_finalization", "title": "Merge final legacy weekly log into Merovingian", "priority": 1, "owner_floor": "Merovingian", "target_paths": ["Z Axis/Z-4_Merovingian/data/logs"], "summary": "Collapse the final compatibility weekly log into the canonical Merovingian log."},
    {"action_id": "SF-03", "queue_id": "sweep_finalization", "title": "Audit remaining legacy roots and declassify empty shells", "priority": 2, "owner_floor": "Architect", "target_paths": ["canonical_runtime", "operations", "w6"], "summary": "Identify which remaining roots are reference-only and safe to remove or ignore."},
    {"action_id": "SF-04", "queue_id": "sweep_finalization", "title": "Reduce redundant dataindex duplication", "priority": 2, "owner_floor": "Architect", "target_paths": ["dataindex"], "summary": "Keep one canonical backlog/map set instead of overlapping root-classification and backlog notes."},
    {"action_id": "SF-05", "queue_id": "sweep_finalization", "title": "Sweep stale caches and empty directories", "priority": 3, "owner_floor": "Merovingian", "target_paths": ["tests", "Z Axis"], "summary": "Remove safe cache clutter and empty shells after each structural pass."},
    {"action_id": "SF-06", "queue_id": "sweep_finalization", "title": "Map remaining canonical_runtime references to in-tree runtime", "priority": 3, "owner_floor": "Merovingian", "target_paths": ["N.py", "lightspeed_runtime"], "summary": "Finish declassifying compatibility references to the old bundle."},
    {"action_id": "SF-07", "queue_id": "sweep_finalization", "title": "Consolidate assimilation and cleanup reporting", "priority": 4, "owner_floor": "Architect", "target_paths": ["Z Axis/Z-4_Merovingian/data/runtime_exports"], "summary": "Reduce overlapping reports into a tighter operator-facing finalization pack."},
    {"action_id": "SF-08", "queue_id": "sweep_finalization", "title": "Promote queue plan into architect-owned execution control", "priority": 4, "owner_floor": "Architect", "target_paths": ["Z Axis/Z+1_Architect/data/finalization"], "summary": "Keep the 25-action plan live inside the app instead of external notes only."},
    {"action_id": "SF-09", "queue_id": "sweep_finalization", "title": "Refresh validation baseline after each major sweep", "priority": 5, "owner_floor": "Merovingian", "target_paths": ["README.md", "Z Axis/Z-4_Merovingian/data/quality"], "summary": "Keep the recorded validation baseline synced with the live runtime and smoke state."},
]


RESEARCH_CHECKLIST_ACTIONS = [
    {"action_id": "KA-09", "queue_id": "knowledge_alignment", "title": "Define one canonical LightSpeed entity model", "priority": 1, "owner_floor": "Oracle", "target_paths": ["lightspeed_runtime", "Z Axis/Z-2_Oracle/data"], "summary": "Standardize Workspace, Project, Dataset, Table, Document, Run, Action, Artifact, Approval, Agent, and Floor entities."},
    {"action_id": "KA-10", "queue_id": "knowledge_alignment", "title": "Give every entity stable IDs and lifecycle state", "priority": 1, "owner_floor": "Oracle", "target_paths": ["lightspeed_runtime/contracts.py", "lightspeed_runtime"], "summary": "Ensure all primary entities carry stable identifiers, owner floor, status, provenance, and validation state."},
    {"action_id": "KA-11", "queue_id": "knowledge_alignment", "title": "Replace remaining freeform folder logic with floor-owned entity registries", "priority": 2, "owner_floor": "Oracle", "target_paths": ["lightspeed_runtime", "Z Axis"], "summary": "Reduce path-first assumptions by routing more app behavior through typed floor-owned records."},
    {"action_id": "KA-12", "queue_id": "knowledge_alignment", "title": "Standardize dataset roles across the application", "priority": 2, "owner_floor": "Oracle", "target_paths": ["Z Axis/Z-2_Oracle/data", "lightspeed_runtime"], "summary": "Use raw, reference, curated, derived, simulation_input, and publish_output roles consistently."},
    {"action_id": "KA-13", "queue_id": "knowledge_alignment", "title": "Add dataset manifests with hash schema units provenance and uncertainty", "priority": 2, "owner_floor": "Oracle", "target_paths": ["Z Axis/Z-2_Oracle/data/library", "lightspeed_runtime"], "summary": "Treat each important dataset as a governed asset with verifiable metadata."},
    {"action_id": "KA-14", "queue_id": "knowledge_alignment", "title": "Persist curated analytical tables as Parquet", "priority": 3, "owner_floor": "Oracle", "target_paths": ["Z Axis/Z-2_Oracle/data/datatables", "lightspeed_runtime"], "summary": "Use a compact columnar format for curated scientific and operational tables."},
    {"action_id": "KA-15", "queue_id": "knowledge_alignment", "title": "Use Arrow-style in-memory exchange for structured handoff", "priority": 3, "owner_floor": "Oracle", "target_paths": ["lightspeed_runtime", "Z Axis/Z0_TheConstruct/data/labs"], "summary": "Prepare fast structured interchange between catalog, review, simulation, and publish surfaces."},
    {"action_id": "KA-16", "queue_id": "knowledge_alignment", "title": "Add DuckDB-based mounted scientific query layer", "priority": 3, "owner_floor": "Oracle", "target_paths": ["lightspeed_runtime", "Z Axis/Z-2_Oracle/data/datatables"], "summary": "Query multiple mounted scientific sources without flattening them into ad hoc local copies."},
    {"action_id": "KA-17", "queue_id": "knowledge_alignment", "title": "Add unit handling and dimensional checks", "priority": 3, "owner_floor": "Oracle", "target_paths": ["lightspeed_runtime/labs", "lightspeed_runtime"], "summary": "Prevent silent scientific calculation drift by validating units and dimensions."},
    {"action_id": "KA-18", "queue_id": "knowledge_alignment", "title": "Track uncertainty and confidence in derived tables", "priority": 4, "owner_floor": "Oracle", "target_paths": ["Z Axis/Z-2_Oracle/data/datatables", "lightspeed_runtime/labs"], "summary": "Carry uncertainty columns and confidence markers through curated and derived outputs."},
    {"action_id": "KA-19", "queue_id": "knowledge_alignment", "title": "Add reusable bell-curve histogram and confidence overlays", "priority": 4, "owner_floor": "Oracle", "target_paths": ["lightspeed_runtime/labs", "Z Axis/Z0_TheConstruct"], "summary": "Standardize distribution and confidence views for scientific and operational review."},
    {"action_id": "KA-20", "queue_id": "knowledge_alignment", "title": "Add Pandera contracts for dataframe validation", "priority": 4, "owner_floor": "Oracle", "target_paths": ["lightspeed_runtime", "tests"], "summary": "Validate structured tables before promotion and publish."},
    {"action_id": "KA-21", "queue_id": "knowledge_alignment", "title": "Add Great Expectations checkpoints for publish gates", "priority": 4, "owner_floor": "Oracle", "target_paths": ["Z Axis/Z+1_Architect/data/publish", "lightspeed_runtime"], "summary": "Gate publishable datasets and packages behind explicit validation checkpoints."},
    {"action_id": "KA-22", "queue_id": "knowledge_alignment", "title": "Expand Pydantic contracts across actions configs and manifests", "priority": 4, "owner_floor": "Oracle", "target_paths": ["lightspeed_runtime/contracts.py", "lightspeed_runtime"], "summary": "Make key runtime envelopes stricter and easier to validate."},
    {"action_id": "KA-23", "queue_id": "knowledge_alignment", "title": "Create a STAC or DCAT style dataset catalog shell", "priority": 5, "owner_floor": "Oracle", "target_paths": ["Z Axis/Z-2_Oracle/data/library", "lightspeed_runtime"], "summary": "Present datasets as discoverable catalog entities with metadata and distributions."},
    {"action_id": "KA-24", "queue_id": "knowledge_alignment", "title": "Create a TAP-like query surface for scientific tables", "priority": 5, "owner_floor": "Oracle", "target_paths": ["lightspeed_runtime", "Z Axis/Z-2_Oracle/data/datatables"], "summary": "Support astronomy-style table query behavior over mounted scientific catalogs."},
    {"action_id": "KA-25", "queue_id": "knowledge_alignment", "title": "Adopt PDS4-like metadata depth for mission refinement assets", "priority": 5, "owner_floor": "Oracle", "target_paths": ["Z Axis/Z-2_Oracle/data/library", "lightspeed_runtime"], "summary": "Model high-value mission datasets with richer structure than generic file metadata."},
    {"action_id": "KA-26", "queue_id": "knowledge_alignment", "title": "Keep mounted raw sources out of primary UI surfaces", "priority": 5, "owner_floor": "Oracle", "target_paths": ["lightspeed_runtime/desktop_adapters.py", "Z Axis/Oracle.py"], "summary": "Default users to curated cards and views instead of raw archive browsing."},
    {"action_id": "KA-27", "queue_id": "knowledge_alignment", "title": "Promote knowns encyclopedia datatable and scenario queues as first-class objects", "priority": 5, "owner_floor": "Oracle", "target_paths": ["Z Axis/Z-2_Oracle/data", "lightspeed_runtime"], "summary": "Treat promotion queues as durable app entities rather than file conventions."},
    {"action_id": "OS-09", "queue_id": "operator_simulation", "title": "Make Smith the canonical job router and executor gateway", "priority": 1, "owner_floor": "Smith", "target_paths": ["Z Axis/Z-3_Smith", "lightspeed_runtime"], "summary": "Use Smith as the durable router for cross-floor jobs rather than scattered execution ownership."},
    {"action_id": "OS-10", "queue_id": "operator_simulation", "title": "Make Oracle the canonical knowledge and catalog floor", "priority": 1, "owner_floor": "Oracle", "target_paths": ["Z Axis/Z-2_Oracle", "lightspeed_runtime/desktop_adapters.py"], "summary": "Route knowledge, catalog, and provenance responsibilities consistently through Oracle."},
    {"action_id": "OS-11", "queue_id": "operator_simulation", "title": "Make Morpheus the canonical review and proofing floor", "priority": 1, "owner_floor": "Morpheus", "target_paths": ["Z Axis/Z-1_Morpheus", "lightspeed_runtime/desktop_adapters.py"], "summary": "Concentrate review, comparison, and proofing interactions in Morpheus."},
    {"action_id": "OS-12", "queue_id": "operator_simulation", "title": "Make TheConstruct the canonical scenario and simulation floor", "priority": 1, "owner_floor": "TheConstruct", "target_paths": ["Z Axis/Z0_TheConstruct", "lightspeed_runtime/labs"], "summary": "Keep scenario design, simulation runs, and holospace output aligned under one floor."},
    {"action_id": "OS-13", "queue_id": "operator_simulation", "title": "Make Architect the canonical governance and publish floor", "priority": 1, "owner_floor": "Architect", "target_paths": ["Z Axis/Z+1_Architect", "lightspeed_runtime/publishing"], "summary": "Keep approvals, package creation, and publish state inside Architect-owned flow."},
    {"action_id": "OS-14", "queue_id": "operator_simulation", "title": "Make Neo the canonical Achilles operator shell", "priority": 1, "owner_floor": "Neo", "target_paths": ["Z Axis/Neo.py", "Z Axis/Z+2_Neo", "lightspeed_runtime/desktop_adapters.py"], "summary": "Reduce parallel operator surfaces and keep Neo as the governed console for Achilles."},
    {"action_id": "OS-15", "queue_id": "operator_simulation", "title": "Use Neo or Achilles as the manager agent by default", "priority": 2, "owner_floor": "Neo", "target_paths": ["lightspeed_runtime", "Z Axis/Neo.py"], "summary": "Keep one manager pattern for agent-led work instead of uncontrolled peer orchestration."},
    {"action_id": "OS-16", "queue_id": "operator_simulation", "title": "Treat specialized floors as tools first and handoffs second", "priority": 2, "owner_floor": "Neo", "target_paths": ["lightspeed_runtime/floor_bridges.py", "lightspeed_runtime"], "summary": "Prefer bounded tool invocation before escalating to a floor-level takeover."},
    {"action_id": "OS-17", "queue_id": "operator_simulation", "title": "Carry rationale and context across all handoffs", "priority": 2, "owner_floor": "Neo", "target_paths": ["lightspeed_runtime/floor_bridges.py", "lightspeed_runtime/contracts.py"], "summary": "Preserve intent, artifact refs, and current state when one floor hands work to another."},
    {"action_id": "OS-18", "queue_id": "operator_simulation", "title": "Risk-rate every agent action type", "priority": 2, "owner_floor": "Neo", "target_paths": ["lightspeed_runtime/contracts.py", "lightspeed_runtime"], "summary": "Classify actions as read, curate, write, execute, or publish before dispatch."},
    {"action_id": "OS-19", "queue_id": "operator_simulation", "title": "Require approval for write execute and publish actions", "priority": 2, "owner_floor": "Architect", "target_paths": ["lightspeed_runtime", "Z Axis/Neo.py", "Z Axis/Architect.py"], "summary": "Keep high-impact automated actions behind explicit approval unless policy allows otherwise."},
    {"action_id": "OS-20", "queue_id": "operator_simulation", "title": "Add one action ledger across user floor and agent actions", "priority": 3, "owner_floor": "Merovingian", "target_paths": ["Z Axis/Z-4_Merovingian/data", "lightspeed_runtime"], "summary": "Keep a durable audit stream for all operational actions."},
    {"action_id": "OS-21", "queue_id": "operator_simulation", "title": "Add one approval ledger for governed work", "priority": 3, "owner_floor": "Architect", "target_paths": ["Z Axis/Z+1_Architect/data", "lightspeed_runtime"], "summary": "Track who approved what, when, and for which run or package."},
    {"action_id": "OS-22", "queue_id": "operator_simulation", "title": "Assign trace IDs to all runs handoffs and packages", "priority": 3, "owner_floor": "Merovingian", "target_paths": ["lightspeed_runtime", "Z Axis/Z-4_Merovingian/data"], "summary": "Make cross-floor work traceable end to end."},
    {"action_id": "OS-23", "queue_id": "operator_simulation", "title": "Adopt OpenTelemetry-compatible tracing and metrics", "priority": 3, "owner_floor": "Merovingian", "target_paths": ["lightspeed_runtime", "Z Axis/Z-4_Merovingian"], "summary": "Emit structured telemetry for actions, jobs, validations, and publish events."},
    {"action_id": "OS-24", "queue_id": "operator_simulation", "title": "Add resumable workflow state for long-running jobs", "priority": 4, "owner_floor": "Smith", "target_paths": ["lightspeed_runtime", "Z Axis/Z-3_Smith"], "summary": "Allow ingest, simulation, and publish flows to resume cleanly after interruption."},
    {"action_id": "OS-25", "queue_id": "operator_simulation", "title": "Normalize publish packages into one governed bundle shape", "priority": 4, "owner_floor": "Architect", "target_paths": ["lightspeed_runtime/publishing", "Z Axis/Z+1_Architect/data/publish"], "summary": "Keep publish outputs predictable and reviewable across workspaces."},
    {"action_id": "OS-26", "queue_id": "operator_simulation", "title": "Use Romer as the reference end-to-end project path", "priority": 4, "owner_floor": "Architect", "target_paths": ["Z Axis/Z+1_Architect/data/publish", "Z Axis/Z0_TheConstruct/data/labs"], "summary": "Proof the operating model on one canonical project path before broadening it."},
    {"action_id": "OS-27", "queue_id": "operator_simulation", "title": "Turn empirical catalogs into reusable simulation presets", "priority": 4, "owner_floor": "TheConstruct", "target_paths": ["lightspeed_runtime/labs", "Z Axis/Z0_TheConstruct/data/labs"], "summary": "Seed scenario presets directly from empirical roles and shortlist behavior."},
    {"action_id": "UX-01", "queue_id": "sweep_finalization", "title": "Normalize global keyboard shortcuts to desktop conventions", "priority": 1, "owner_floor": "Trinity", "target_paths": ["N.py", "Z Axis"], "summary": "Keep Ctrl+K, Ctrl+comma, Escape, and related shell shortcuts consistent and discoverable."},
    {"action_id": "UX-02", "queue_id": "sweep_finalization", "title": "Use the command palette as the primary global action surface", "priority": 1, "owner_floor": "Trinity", "target_paths": ["N.py", "Z Axis/Z+3_Trinity/wizards"], "summary": "Keep one searchable command surface for actions, objects, and navigation."},
    {"action_id": "UX-03", "queue_id": "sweep_finalization", "title": "Adopt per-page settings menus instead of implicit click behavior", "priority": 1, "owner_floor": "Trinity", "target_paths": ["N.py", "Z Axis"], "summary": "Expose page settings in visible menus or ellipsis controls rather than hidden click assumptions."},
    {"action_id": "UX-04", "queue_id": "sweep_finalization", "title": "Keep primary click for select open and activate only", "priority": 1, "owner_floor": "Trinity", "target_paths": ["N.py", "Z Axis"], "summary": "Avoid using primary click as a surprise settings or mode-switch action."},
    {"action_id": "UX-05", "queue_id": "sweep_finalization", "title": "Standardize arrows tab enter and escape behavior across floors", "priority": 2, "owner_floor": "Trinity", "target_paths": ["N.py", "Z Axis"], "summary": "Make desktop interaction predictable throughout the app."},
    {"action_id": "UX-06", "queue_id": "sweep_finalization", "title": "Restrict WASD movement to explicit Holospace contexts", "priority": 2, "owner_floor": "TheConstruct", "target_paths": ["N.py", "Z Axis/Z0_TheConstruct"], "summary": "Reserve movement keys for immersive contexts with clear mode indicators."},
    {"action_id": "UX-07", "queue_id": "sweep_finalization", "title": "Expose visible mode switching between Workspace Operator and Holospace", "priority": 2, "owner_floor": "Trinity", "target_paths": ["N.py", "Z Axis"], "summary": "Make the current shell mode explicit so interaction expectations stay clear."},
    {"action_id": "UX-08", "queue_id": "sweep_finalization", "title": "Standardize page headers into title status primary actions and page menu", "priority": 2, "owner_floor": "Trinity", "target_paths": ["Z Axis", "lightspeed_runtime/desktop_adapters.py"], "summary": "Keep page hierarchy stable and reduce bespoke header layouts."},
    {"action_id": "UX-09", "queue_id": "sweep_finalization", "title": "Continue replacing long flat button rows with grouped action bars", "priority": 3, "owner_floor": "Trinity", "target_paths": ["Z Axis", "lightspeed_runtime/desktop_adapters.py"], "summary": "Group actions by workflow instead of presenting one long row of commands."},
    {"action_id": "UX-10", "queue_id": "sweep_finalization", "title": "Replace JSON inspectors with cards summaries and tables", "priority": 3, "owner_floor": "Morpheus", "target_paths": ["lightspeed_runtime/desktop_adapters.py", "Z Axis"], "summary": "Show structured content in readable UI components before exposing raw JSON."},
    {"action_id": "UX-11", "queue_id": "sweep_finalization", "title": "Standardize empty loading error and success states", "priority": 3, "owner_floor": "Trinity", "target_paths": ["Z Axis", "lightspeed_runtime/desktop_adapters.py"], "summary": "Make system feedback predictable and reduce silent or ambiguous states."},
    {"action_id": "UX-12", "queue_id": "sweep_finalization", "title": "Bring the shell toward WCAG 2.2 keyboard and focus quality", "priority": 3, "owner_floor": "Trinity", "target_paths": ["N.py", "Z Axis"], "summary": "Improve focus visibility, keyboard reachability, and contrast where needed."},
    {"action_id": "UX-13", "queue_id": "sweep_finalization", "title": "Reduce decorative motion and keep only functional transitions", "priority": 4, "owner_floor": "Trinity", "target_paths": ["Z Axis", "core/ui"], "summary": "Use motion to explain state change, depth, and causality rather than decoration."},
    {"action_id": "UX-14", "queue_id": "sweep_finalization", "title": "Align typography and spacing across all major floors", "priority": 4, "owner_floor": "Trinity", "target_paths": ["Z Axis", "core/ui"], "summary": "Make the app feel like one operating system instead of adjacent tools."},
    {"action_id": "UX-15", "queue_id": "sweep_finalization", "title": "Use glass hierarchy as function not decoration", "priority": 4, "owner_floor": "Trinity", "target_paths": ["Z Axis", "core/ui"], "summary": "Reserve the strongest glass treatments for structure, focus, and depth cues."},
    {"action_id": "UX-16", "queue_id": "sweep_finalization", "title": "Add contextual help and shortcut hints to each major floor", "priority": 4, "owner_floor": "Trinity", "target_paths": ["N.py", "Z Axis"], "summary": "Make per-floor affordances and shortcuts discoverable without hunting through docs."},
    {"action_id": "UX-17", "queue_id": "sweep_finalization", "title": "Add floor ownership descriptions to major pages", "priority": 5, "owner_floor": "Trinity", "target_paths": ["Z Axis", "lightspeed_runtime/desktop_adapters.py"], "summary": "Explain what each floor owns so users know where work belongs."},
    {"action_id": "UX-18", "queue_id": "sweep_finalization", "title": "Run the final aesthetic and polish pass after structural work lands", "priority": 5, "owner_floor": "Trinity", "target_paths": ["N.py", "Z Axis", "core/ui"], "summary": "Finish visual polish only after the underlying flows and ownership model are stable."},
]


ALL_ACTIONS = DEFAULT_ACTIONS + RESEARCH_CHECKLIST_ACTIONS


def read_execution_queues(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_execution_queue_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _queue_snapshot(actions: list[dict], queue_id: str) -> dict:
    meta = QUEUE_METADATA[queue_id]
    queue_actions = [item for item in actions if item["queue_id"] == queue_id]
    pending = [item for item in queue_actions if item["status"] != "completed"]
    completed = [item for item in queue_actions if item["status"] == "completed"]
    pending.sort(key=lambda item: (int(item["priority"]), int(item["sequence"])))
    priority_bands: dict[str, int] = {}
    for item in pending:
        band = str(item["priority"])
        priority_bands[band] = priority_bands.get(band, 0) + 1
    return {
        "queue_id": queue_id,
        "title": meta["title"],
        "owner_floor": meta["owner_floor"],
        "support_floor": meta["support_floor"],
        "summary": meta["summary"],
        "action_count": len(queue_actions),
        "pending_count": len(pending),
        "completed_count": len(completed),
        "active_top_five": pending[:5],
        "priority_bands": priority_bands,
        "completion_ratio": round(len(completed) / len(queue_actions), 4) if queue_actions else 1.0,
    }


def build_execution_queues(root: Path, output_path: Path | None = None) -> dict:
    """Build the canonical three-queue Architect finalization matrix."""
    root = Path(root)
    existing = read_execution_queues(root, output_path=output_path)
    existing_actions = {
        str(item.get("action_id") or ""): item
        for item in (existing.get("actions") or [])
        if item.get("action_id")
    }
    history = existing.get("history") or []

    actions: list[dict] = []
    for index, action in enumerate(ALL_ACTIONS, start=1):
        current = dict(action)
        prior = existing_actions.get(current["action_id"], {})
        current["sequence"] = index
        current["status"] = prior.get("status", "pending")
        current["action_taken"] = prior.get("action_taken", "")
        current["completed_at"] = prior.get("completed_at")
        current["updated_at"] = prior.get("updated_at")
        current["last_reshuffled_at"] = prior.get("last_reshuffled_at")
        if prior.get("priority") is not None:
            current["priority"] = int(prior["priority"])
        actions.append(current)

    queues = [_queue_snapshot(actions, queue_id) for queue_id in QUEUE_METADATA]
    payload = {
        "generated_at": utc_now_iso(),
        "queue_path": str(output_path or default_execution_queue_path(root)),
        "queue_root": str(finalization_queue_root(root)),
        "queue_root_kind": "canonical_architect_finalization_root",
        "owner_floor": "Architect",
        "control_floor": "Architect",
        "queue_count": len(queues),
        "action_count": len(actions),
        "completed_count": sum(1 for item in actions if item["status"] == "completed"),
        "pending_count": sum(1 for item in actions if item["status"] != "completed"),
        "queues": queues,
        "overall_active_actions": [item for queue in queues for item in queue["active_top_five"]],
        "actions": actions,
        "history": history[-100:],
        "summary": "Three concurrent Architect-owned execution queues with rolling top-five priorities for LightSpeed finalization and research-backed checklist execution.",
    }
    return payload


def write_execution_queues(root: Path, output_path: Path | None = None) -> dict:
    """Persist the three-queue matrix to the canonical Architect queue path."""
    root = Path(root)
    destination = output_path or default_execution_queue_path(root)
    payload = build_execution_queues(root, output_path=destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def advance_execution_queue(
    root: Path,
    action_id: str,
    *,
    status: str = "completed",
    note: str = "",
    priority: int | None = None,
    output_path: Path | None = None,
) -> dict:
    """Advance a queued action while preserving the canonical Architect queue contract."""
    root = Path(root)
    destination = output_path or default_execution_queue_path(root)
    payload = build_execution_queues(root, output_path=destination)
    actions = payload.get("actions") or []
    target = next((item for item in actions if item.get("action_id") == action_id), None)
    if target is None:
        return {"updated": False, "reason": "action_not_found", "queue_path": str(destination)}
    timestamp = utc_now_iso()
    target["status"] = status
    target["action_taken"] = note
    target["updated_at"] = timestamp
    target["last_reshuffled_at"] = timestamp
    if status == "completed":
        target["completed_at"] = timestamp
    if priority is not None:
        target["priority"] = max(1, min(5, int(priority)))
    history = payload.get("history") or []
    history.append({"action_id": action_id, "status": status, "note": note, "priority": target.get("priority"), "updated_at": timestamp})
    payload["history"] = history[-100:]
    payload["generated_at"] = timestamp
    payload["completed_count"] = sum(1 for item in actions if item["status"] == "completed")
    payload["pending_count"] = sum(1 for item in actions if item["status"] != "completed")
    payload["queues"] = [_queue_snapshot(actions, queue_id) for queue_id in QUEUE_METADATA]
    payload["overall_active_actions"] = [item for queue in payload["queues"] for item in queue["active_top_five"]]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {
        "updated": True,
        "action_id": action_id,
        "queue_path": str(destination),
        "status": status,
        "note": note,
        "completed_count": payload["completed_count"],
        "pending_count": payload["pending_count"],
        "queues": payload["queues"],
    }
