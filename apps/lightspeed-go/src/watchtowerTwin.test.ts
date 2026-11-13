import { describe, expect, it } from "vitest";

import {
  decideWatchTowerViewerMode,
  validateWatchTowerManifest,
  WATCH_TOWER_SOURCE_FCSTD_SHA256,
  WATCH_TOWER_SOURCE_GLB_SHA256,
  watchTowerSourceManifest,
  type WatchTowerTwinManifest,
} from "./watchtowerTwin";

const semanticCompleteFixture = (): WatchTowerTwinManifest => ({
  ...watchTowerSourceManifest,
  semanticMapVersion: "WT-SEM-1.0.0",
  finalPoleLabelsBound: true,
  towerCableNodesBound: true,
  cableEdgesIncluded: true,
  evidenceState: "source-locked",
});

describe("Watch Tower source twin contract", () => {
  it("accepts the exact current raw source manifest for internal geometry viewing", () => {
    const decision = decideWatchTowerViewerMode(
      watchTowerSourceManifest,
      "internal-source",
    );

    expect(decision.allowed).toBe(true);
    expect(decision.blockers).toEqual([]);
    expect(decision.warnings.join(" ")).toContain("Semantic map is unresolved");
    expect(watchTowerSourceManifest.cableEdgesIncluded).toBe(false);
    expect(watchTowerSourceManifest.aestheticProfileApplied).toBe(false);
  });

  it("blocks semantic mode while pole labels and A/C nodes are unresolved", () => {
    const decision = decideWatchTowerViewerMode(
      watchTowerSourceManifest,
      "internal-semantic",
    );

    expect(decision.allowed).toBe(false);
    expect(decision.blockers.join(" ")).toContain("versioned semantic map");
    expect(decision.blockers.join(" ")).toContain("final pole labels and A/C tower nodes");
  });

  it("blocks public mode until semantic and publication classification gates are complete", () => {
    const decision = decideWatchTowerViewerMode(watchTowerSourceManifest, "public");

    expect(decision.allowed).toBe(false);
    expect(decision.blockers.join(" ")).toContain("publication/security classification review");
    expect(decision.blockers.join(" ")).toContain("unresolved semantic model");
  });

  it("rejects a source hash that is not the current FCStd lock", () => {
    const manifest: WatchTowerTwinManifest = {
      ...watchTowerSourceManifest,
      sourceFcstdSha256: "0".repeat(64),
    };

    const validation = validateWatchTowerManifest(manifest);

    expect(validation.valid).toBe(false);
    expect(validation.blockers.join(" ")).toContain("current source lock");
  });

  it("rejects a geometry derivative hash that is not the current GLB receipt", () => {
    const manifest: WatchTowerTwinManifest = {
      ...watchTowerSourceManifest,
      sourceGeometryGlbSha256: "1".repeat(64),
    };

    const validation = validateWatchTowerManifest(manifest);

    expect(validation.valid).toBe(false);
    expect(validation.blockers.join(" ")).toContain("current derivative receipt");
  });

  it("rejects cable edges when endpoint semantics are unresolved", () => {
    const manifest: WatchTowerTwinManifest = {
      ...watchTowerSourceManifest,
      cableEdgesIncluded: true,
    };

    const validation = validateWatchTowerManifest(manifest);

    expect(validation.valid).toBe(false);
    expect(validation.blockers.join(" ")).toContain("both endpoint families");
  });

  it("permits a semantically complete internal state only when the semantic inputs are explicit", () => {
    const manifest = semanticCompleteFixture();
    const decision = decideWatchTowerViewerMode(manifest, "internal-semantic");

    expect(decision.allowed).toBe(true);
    expect(decision.blockers).toEqual([]);
    expect(manifest.sourceFcstdSha256).toBe(WATCH_TOWER_SOURCE_FCSTD_SHA256);
    expect(manifest.sourceGeometryGlbSha256).toBe(WATCH_TOWER_SOURCE_GLB_SHA256);
  });

  it("still blocks public mode for a semantic-complete manifest until publication classification is reviewed", () => {
    const manifest = semanticCompleteFixture();
    const decision = decideWatchTowerViewerMode(manifest, "public");

    expect(decision.allowed).toBe(false);
    expect(decision.blockers.join(" ")).toContain("publication/security classification review");
  });
});
