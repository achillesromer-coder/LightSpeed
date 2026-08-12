export type WatchTowerEvidenceState =
  | "source-locked"
  | "semantic-hold"
  | "review-gated"
  | "blocked";

export type WatchTowerViewerMode = "internal-source" | "internal-semantic" | "public";

export type WatchTowerTwinManifest = {
  assetId: "WT-001";
  sourceFcstdSha256: string;
  sourceGeometryGlbSha256: string;
  geometryUnits: "m";
  coordinateState: "local-cad-not-geodetic";
  semanticMapVersion: string | null;
  finalPoleLabelsBound: boolean;
  towerCableNodesBound: boolean;
  cableEdgesIncluded: boolean;
  aestheticProfileApplied: boolean;
  publicationClassificationReviewed: boolean;
  evidenceState: WatchTowerEvidenceState;
};

export type WatchTowerTwinValidation = {
  valid: boolean;
  blockers: string[];
  warnings: string[];
};

export type WatchTowerViewerDecision = {
  allowed: boolean;
  mode: WatchTowerViewerMode;
  evidenceState: WatchTowerEvidenceState;
  blockers: string[];
  warnings: string[];
};

export const WATCH_TOWER_SOURCE_FCSTD_SHA256 =
  "c476f9f2f9946ab8e99e58dd399aa7b02bac630c5d9336b80ef66f5f2a397321";

export const WATCH_TOWER_SOURCE_GLB_SHA256 =
  "60fdbedb11868015d96b4c9e6692d4550e4987e59bbec60bfb0ead75762f3683";

export const watchTowerSourceManifest: WatchTowerTwinManifest = {
  assetId: "WT-001",
  sourceFcstdSha256: WATCH_TOWER_SOURCE_FCSTD_SHA256,
  sourceGeometryGlbSha256: WATCH_TOWER_SOURCE_GLB_SHA256,
  geometryUnits: "m",
  coordinateState: "local-cad-not-geodetic",
  semanticMapVersion: null,
  finalPoleLabelsBound: false,
  towerCableNodesBound: false,
  cableEdgesIncluded: false,
  aestheticProfileApplied: false,
  publicationClassificationReviewed: false,
  evidenceState: "semantic-hold",
};

const SHA256_RE = /^[0-9a-f]{64}$/;

export function validateWatchTowerManifest(
  manifest: WatchTowerTwinManifest,
): WatchTowerTwinValidation {
  const blockers: string[] = [];
  const warnings: string[] = [];

  if (manifest.assetId !== "WT-001") {
    blockers.push("Unexpected Watch Tower asset identity.");
  }

  if (!SHA256_RE.test(manifest.sourceFcstdSha256)) {
    blockers.push("FCStd SHA-256 is malformed.");
  } else if (manifest.sourceFcstdSha256 !== WATCH_TOWER_SOURCE_FCSTD_SHA256) {
    blockers.push("FCStd SHA-256 does not match the current source lock.");
  }

  if (!SHA256_RE.test(manifest.sourceGeometryGlbSha256)) {
    blockers.push("Source-geometry GLB SHA-256 is malformed.");
  } else if (manifest.sourceGeometryGlbSha256 !== WATCH_TOWER_SOURCE_GLB_SHA256) {
    blockers.push("Source-geometry GLB SHA-256 does not match the current derivative receipt.");
  }

  if (manifest.geometryUnits !== "m") {
    blockers.push("Watch Tower viewer geometry must use metres.");
  }

  if (manifest.coordinateState !== "local-cad-not-geodetic") {
    blockers.push("Watch Tower source coordinates must remain explicitly non-geodetic.");
  }

  if (manifest.semanticMapVersion === null) {
    warnings.push("Semantic map is unresolved: E/L/R pole labels and A/C tower nodes remain held.");
  }

  if (!manifest.finalPoleLabelsBound) {
    warnings.push("Final E/L1-L4/R1-R4 pole labels are not bound.");
  }

  if (!manifest.towerCableNodesBound) {
    warnings.push("Exact A/C tower face-node coordinates are not bound.");
  }

  if (manifest.cableEdgesIncluded && (!manifest.finalPoleLabelsBound || !manifest.towerCableNodesBound)) {
    blockers.push("Cable edges cannot be included before both endpoint families are semantically bound.");
  }

  if (manifest.aestheticProfileApplied && manifest.evidenceState === "source-locked") {
    warnings.push("Aesthetic state must remain a separate render profile from source geometry authority.");
  }

  if (manifest.evidenceState === "source-locked" && manifest.semanticMapVersion === null) {
    blockers.push("A semantically complete source-locked state requires a versioned semantic map.");
  }

  return { valid: blockers.length === 0, blockers, warnings };
}

export function decideWatchTowerViewerMode(
  manifest: WatchTowerTwinManifest,
  mode: WatchTowerViewerMode,
): WatchTowerViewerDecision {
  const validation = validateWatchTowerManifest(manifest);
  const blockers = [...validation.blockers];
  const warnings = [...validation.warnings];

  if (mode === "internal-semantic") {
    if (manifest.semanticMapVersion === null) {
      blockers.push("Semantic viewer mode requires a versioned semantic map.");
    }
    if (!manifest.finalPoleLabelsBound || !manifest.towerCableNodesBound) {
      blockers.push("Semantic viewer mode requires final pole labels and A/C tower nodes to be bound.");
    }
  }

  if (mode === "public") {
    if (!manifest.publicationClassificationReviewed) {
      blockers.push("Public viewer mode requires completed publication/security classification review.");
    }
    if (manifest.semanticMapVersion === null) {
      blockers.push("Public viewer mode cannot expose an unresolved semantic model.");
    }
    if (manifest.evidenceState !== "source-locked") {
      blockers.push("Public viewer mode requires an accepted source-locked semantic state.");
    }
  }

  if (mode === "internal-source") {
    warnings.push(
      "Internal source mode is geometry-only: it does not establish cable topology, structural adequacy, Solar Hull performance, ecological performance, sensor health, compliance, or build readiness.",
    );
  }

  return {
    allowed: blockers.length === 0,
    mode,
    evidenceState: manifest.evidenceState,
    blockers,
    warnings,
  };
}
