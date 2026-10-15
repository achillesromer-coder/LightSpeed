import { describe, expect, it } from "vitest";
import {
  AGENT_ROLES,
  CGX_FAMILY_TEMPLATES,
  CGX_WORKSPACE_ACTIONS,
  cgxDraftInstruction,
  cgxFamilyTemplate,
  normalizeCgxFamily,
  inferWorkflowStage,
  normalizeShellView,
  routeOperationalFloor,
  shellViewFromSearch,
  WORKFLOW_STAGES,
} from "./osShellModel";

describe("Cognigrex OS shell model", () => {
  it("keeps Neo as operational head and Achilles as governance", () => {
    expect(AGENT_ROLES[0]?.floor).toBe("Neo");
    expect(AGENT_ROLES[AGENT_ROLES.length - 1]?.floor).toBe("Achilles");
  });

  it("preserves the complete intake-to-release workflow", () => {
    expect(WORKFLOW_STAGES.map((stage) => stage.id)).toEqual([
      "intake",
      "analyse",
      "route",
      "workshop",
      "proof",
      "consolidate",
      "release",
    ]);
  });

  it("maps blank and unknown operational work to Neo while preserving explicit governance", () => {
    expect(routeOperationalFloor("")).toBe("Neo");
    expect(routeOperationalFloor("coordinate this bounded work")).toBe("Neo");
    expect(routeOperationalFloor("prepare dinner notes")).toBe("Neo");
    expect(routeOperationalFloor("audit the evidence conflict")).toBe("Morpheus");
    expect(routeOperationalFloor("send this to the Achilles governance gate")).toBe("Achilles");
  });

  it("infers workflow stage without elevating release state", () => {
    expect(inferWorkflowStage("reconcile these source files")).toBe("analyse");
    expect(inferWorkflowStage("run the model and generate a mesh")).toBe("workshop");
    expect(inferWorkflowStage("verify provenance and claims")).toBe("proof");
    expect(inferWorkflowStage("consolidate accepted deltas into canon")).toBe("consolidate");
    expect(inferWorkflowStage("prepare a public-ready export")).toBe("release");
  });

  it("fails safely to the command workspace", () => {
    expect(normalizeShellView("objects")).toBe("objects");
    expect(normalizeShellView("not-a-view")).toBe("command");
    expect(normalizeShellView(null)).toBe("command");
  });

  it("opens a bounded workspace requested by a compatibility URL", () => {
    expect(shellViewFromSearch("?view=system", "activity")).toBe("system");
    expect(shellViewFromSearch("view=not-a-view", "activity")).toBe("command");
    expect(shellViewFromSearch("", "activity")).toBe("activity");
  });
});


describe("CGX family/type landing bindings", () => {
  it("reuses six existing LS GO workspace routes and preserves single authority", () => {
    expect(CGX_WORKSPACE_ACTIONS.map((action) => action.view)).toEqual([
      "command", "activity", "sources", "objects", "system", "review",
    ]);
    expect(new Set(CGX_WORKSPACE_ACTIONS.map((action) => action.id)).size).toBe(CGX_WORKSPACE_ACTIONS.length);
    expect(CGX_WORKSPACE_ACTIONS.every((action) => action.view in Object.fromEntries(
      ["command", "activity", "review", "objects", "system", "sources"].map((id) => [id, true]),
    ))).toBe(true);
  });

  it("keeps domain profiles scoped and fails closed to parent on unknown family", () => {
    expect(CGX_FAMILY_TEMPLATES.map((family) => family.id)).toEqual([
      "cognigrex", "romer", "eco", "emassc", "lightspeed", "sai",
    ]);
    expect(normalizeCgxFamily("other")).toBe("cognigrex");
    expect(cgxFamilyTemplate("eco").types).toContain("ecology");
    expect(cgxFamilyTemplate("sai").focus).toContain("Shared Australian Intelligence");
  });

  it("prepares but never dispatches a heavy workload or unfamiliar component type", () => {
    const draft = cgxDraftInstruction("romer", "unknown", "heavy-review", "models");
    expect(draft).toContain("engineering");
    expect(draft).toContain("heavy-compute");
    expect(draft).toContain("do not launch a job");
    expect(draft).toContain("Object_ID");
    expect(draft).not.toContain("unknown");
  });
});
