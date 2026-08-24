import { describe, expect, it } from "vitest";
import {
  AGENT_ROLES,
  inferWorkflowStage,
  normalizeShellView,
  routeOperationalFloor,
  WORKFLOW_STAGES,
} from "./osShellModel";

describe("Cognigrex OS shell model", () => {
  it("keeps Neo as operational head and Achilles as governance", () => {
    expect(AGENT_ROLES[0]?.floor).toBe("Neo");
    expect(AGENT_ROLES.at(-1)?.floor).toBe("Achilles");
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

  it("maps unknown operational work to Neo rather than routine Achilles routing", () => {
    expect(routeOperationalFloor("coordinate this bounded work")).toBe("Neo");
    expect(routeOperationalFloor("prepare dinner notes")).toBe("Neo");
    expect(routeOperationalFloor("audit the evidence conflict")).toBe("Morpheus");
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
});
