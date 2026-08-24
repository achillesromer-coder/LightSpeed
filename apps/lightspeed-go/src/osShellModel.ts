import { routeInstruction, type Floor } from "./desktopBridge";

export const SHELL_SCHEMA = "lightspeed-cognigrex-os-shell-v0.1" as const;

export const SHELL_VIEWS = ["command", "activity", "objects", "system", "sources"] as const;
export type ShellView = (typeof SHELL_VIEWS)[number];

export type WorkflowStageId =
  | "intake"
  | "analyse"
  | "route"
  | "workshop"
  | "proof"
  | "consolidate"
  | "release";

export interface WorkflowStage {
  id: WorkflowStageId;
  label: string;
  owner: string;
  receipt: string;
  description: string;
}

export const WORKFLOW_STAGES: readonly WorkflowStage[] = [
  {
    id: "intake",
    label: "Intake",
    owner: "Neo",
    receipt: "source envelope",
    description: "Capture the request, source pointers, project identity, constraints and expected output without inventing missing authority.",
  },
  {
    id: "analyse",
    label: "Analyse",
    owner: "Neo + Oracle",
    receipt: "scope / evidence map",
    description: "Resolve knowns, source authority, evidence class, conflicts, privacy and the minimum useful execution path.",
  },
  {
    id: "route",
    label: "Commit",
    owner: "Neo",
    receipt: "stable task / agent route",
    description: "Commit one bounded job to the correct specialist floor while retaining stable identity and exact-once transport semantics.",
  },
  {
    id: "workshop",
    label: "Workshop",
    owner: "specialist floor",
    receipt: "artifact / data / result",
    description: "Execute the bounded specialist work: code, modelling, evidence extraction, interface work, planning or runtime recovery.",
  },
  {
    id: "proof",
    label: "Proof",
    owner: "Smith + Morpheus + Oracle",
    receipt: "tests / provenance / contradiction",
    description: "Test implementation, verify provenance, resolve conflicts and keep hypothesis, inference and empirical evidence distinct.",
  },
  {
    id: "consolidate",
    label: "Consolidate",
    owner: "Neo + Achilles",
    receipt: "canonical delta / supersession",
    description: "Return accepted results to the living canonical library as compact deltas, pointers and receipts rather than duplicate masters.",
  },
  {
    id: "release",
    label: "Publish-ready",
    owner: "Achilles",
    receipt: "claim / security / release gate",
    description: "Package approved digital artifacts, data and objects for a bounded release candidate. Publish-ready is not automatically published.",
  },
] as const;

export interface AgentRole {
  floor: Floor;
  short: string;
  role: string;
  boundary: string;
}

export const AGENT_ROLES: readonly AgentRole[] = [
  {
    floor: "Neo",
    short: "N",
    role: "Cognigrex operational head: intake, decomposition, routing, cycle control and result aggregation.",
    boundary: "May coordinate and reason operationally; cannot self-promote evidence, canon or public claims past Achilles/owner gates.",
  },
  {
    floor: "Oracle",
    short: "O",
    role: "Sources, evidence retrieval, indexing, known-state and data lineage.",
    boundary: "Preserves source authority and uncertainty; duplicate references do not become independent evidence.",
  },
  {
    floor: "Morpheus",
    short: "M",
    role: "Contradiction, provenance, claim proof, confidence and supersession review.",
    boundary: "Reviews and recommends; does not fabricate empirical validation.",
  },
  {
    floor: "Smith",
    short: "S",
    role: "Code, schemas, deterministic transforms, tests, build and execution receipts.",
    boundary: "Changes remain branch/review gated until the applicable execution and release receipts exist.",
  },
  {
    floor: "Architect",
    short: "A",
    role: "Projects, dependency topology, plans, interfaces and system decomposition.",
    boundary: "Uses canonical project identity and pointers rather than spawning competing masters.",
  },
  {
    floor: "TheConstruct",
    short: "TC",
    role: "Simulation, CAD, meshes, digital twins, derived views and manufacturing-reference artifacts.",
    boundary: "Derived models remain labelled and cannot imply physical performance without evidence.",
  },
  {
    floor: "Trinity",
    short: "T",
    role: "Interface, interaction, visual language, accessibility and communication surfaces.",
    boundary: "Presentation cannot elevate claim state or bypass evidence/security classification.",
  },
  {
    floor: "Merovingian",
    short: "R",
    role: "Runtime health, storage, recovery, resource control, persistence and operational receipts.",
    boundary: "Recovery and cleanup are reversible/evidence-gated; no silent deletion or second runtime.",
  },
  {
    floor: "Achilles",
    short: "Ω",
    role: "Meta-governance, proof thresholds, safety, canonical promotion and release oversight.",
    boundary: "Audits and gates the collective; it is not the routine task router inside Cognigrex.",
  },
] as const;

export const normalizeShellView = (value: string | null | undefined): ShellView =>
  SHELL_VIEWS.includes(value as ShellView) ? (value as ShellView) : "command";

export const inferWorkflowStage = (instruction: string): WorkflowStageId => {
  const text = instruction.trim().toLowerCase();
  if (!text) return "intake";
  if (/\b(publish|release|public[- ]?ready|export|mint|deploy)\b/.test(text)) return "release";
  if (/\b(consolidat|canon|supersed|assimil|promot|living library|handoff)\b/.test(text)) return "consolidate";
  if (/\b(test|proof|verify|validat|audit|conflict|provenance|claim|confidence)\b/.test(text)) return "proof";
  if (/\b(build|code|model|simulate|render|mesh|cad|analyse data|analyze data|workshop|execute|run)\b/.test(text)) return "workshop";
  if (/\b(route|delegate|commit|queue|assign|agent|floor)\b/.test(text)) return "route";
  if (/\b(source|evidence|research|analyse|analyze|classif|scope|compare|reconcile)\b/.test(text)) return "analyse";
  return "intake";
};

export const routeOperationalFloor = (instruction: string): Floor => {
  const text = instruction.trim().toLowerCase();
  if (/\b(proof|claim|verify|verification|conflict|confidence|audit|contradiction|supersession)\b/.test(text)) {
    return "Morpheus";
  }
  const routed = routeInstruction(instruction);
  return routed === "Achilles" && text ? "Neo" : routed;
};

export const workflowStage = (id: WorkflowStageId): WorkflowStage =>
  WORKFLOW_STAGES.find((stage) => stage.id === id) ?? WORKFLOW_STAGES[0];
