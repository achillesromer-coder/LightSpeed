import { describe, expect, it } from "vitest";
import { checkpointUiProjection } from "./cgxNativeCheckpointUi";
import type { CgxDynamicSurface } from "./desktopBridge";

const view: CgxDynamicSurface = {
  schema: "CGX-UNISPACE-DYNAMIC-SURFACE/0.1",
  selector: "lightspeed",
  source_view_sha256: "a".repeat(64),
  route_count: 3,
  routes: [
    { id: "cgx.plan_query", state: "available", kind: "runtime", read_only: true, needs_review: false, gate: "", execution_enabled: false },
    { id: "node.compute", state: "gated", kind: "runtime", read_only: false, needs_review: true, gate: "host lease", execution_enabled: false },
    { id: "ops.queue", state: "available", kind: "runtime", read_only: false, needs_review: true, gate: "private", execution_enabled: false },
  ],
  roles: [{ id: "neo", floor: "Neo", responsibility: "source-bound review", execution_enabled: false }],
  role_source_holds: [],
  native_mint_authorized: false,
  execution_authorized: false,
};

describe("CGX native checkpoint in existing UniSpace panel", () => {
  it("derives choices from backend registry and excludes gated/write routes", () => {
    const result = checkpointUiProjection(view);
    expect(result.roles).toEqual([{ id: "neo", label: "Neo" }]);
    expect(result.routes).toEqual([{ id: "cgx.plan_query", label: "cgx.plan_query" }]);
    expect(result.canStage).toBe(true);
    expect(result.permission).toBe("owner_session_private_review_only");
    expect(result.revision).toBe(view.source_view_sha256);
  });

  it("fails closed if no available read-only routes or no roles", () => {
    expect(checkpointUiProjection({ ...view, routes: view.routes.slice(1) }).canStage).toBe(false);
    expect(checkpointUiProjection({ ...view, roles: [] }).canStage).toBe(false);
  });
});
