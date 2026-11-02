/**
 * Source-only R3 projection guard for the existing UniSpace/LS GO FileSpace shell.
 * This is NOT an authentication, DBR, signing, routing or deployment implementation.
 * Only a trusted server adapter may supply the verified host policy below; browser
 * input, a loopback HTTP 200, a session header or a source hash cannot attest it.
 * No private source bytes, paths, credentials or raw receipts are returned.
 */
export type FileSpaceView =
  | "filespace-tree" | "topology-graph" | "active-object-inspector"
  | "evidence-claim" | "map-spatial" | "twin-3d" | "network-runtime";

export type EvidenceClass = "SOURCE_REVIEW" | "CREATIVE" | "SCIENTIFIC";
export type Admission = "CANDIDATE" | "SANDBOX_STAGED" | "NATIVE_ADMITTED";

export interface TrustedHostProjectionPolicy {
  /** Assertions MUST originate from independently validated host/DBR ACL checks. */
  hostSessionVerified: boolean;
  issuerVerified: boolean;
  revocationChecked: boolean;
  leaseValid: boolean;
  rootReadbackVerified: boolean;
  dbrReadbackVerified: boolean;
  audience: "owner-private" | "public";
  allowedObjectIds: readonly string[];
  allowedChildFileSpaces: readonly string[];
  hydrationCeiling: 0 | 1 | 2 | 3;
}

export interface QualifiedFileSpaceRecord {
  objectId: string;
  childFileSpace: string;
  admission: Admission;
  rights: "PERMITTED" | "UNKNOWN" | "DENIED";
  evidenceClass: EvidenceClass;
  /** Missing independent validation/units/frame always produces a Frontier. */
  geometry?: { independentlyValidated: boolean; frame: string; units: string };
  /** Deliberately not projected: may contain sensitive source paths and hashes. */
  sourceLocator?: string;
  rawSourceText?: string;
}

export interface FileSpaceProjectionRequest {
  objectId: string;
  childFileSpace: string;
  view: string;
  hydration: number;
}

export type FileSpaceProjection =
  | { permitted: false; reason: "HOST_AUTH_HOLD" | "SCOPE_HOLD" | "OBJECT_HOLD" |
      "SOURCE_HOLD" | "EXECUTION_HOLD" | "VIEW_HOLD" }
  | { permitted: true; objectId: string; childFileSpace: string;
      primaryView: FileSpaceView; hydration: 0 | 1 | 2 | 3;
      evidenceClass: EvidenceClass; projectionStatus: "ELIGIBLE_R3_READ_ONLY";
      frontier: "NONE" | "METRIC_GEOMETRY_UNQUALIFIED" };

const views = new Set<FileSpaceView>([
  "filespace-tree", "topology-graph", "active-object-inspector", "evidence-claim",
  "map-spatial", "twin-3d", "network-runtime",
]);

/** Never call this with browser-controlled policy. It is a fail-closed filter, not a grant. */
export function derivePrivateFileSpaceProjection(
  policy: TrustedHostProjectionPolicy | null,
  record: QualifiedFileSpaceRecord | null,
  request: FileSpaceProjectionRequest,
): FileSpaceProjection {
  if (!policy || !policy.hostSessionVerified || !policy.issuerVerified ||
      !policy.revocationChecked || !policy.leaseValid ||
      !policy.rootReadbackVerified || !policy.dbrReadbackVerified) {
    return { permitted: false, reason: "HOST_AUTH_HOLD" };
  }
  if (policy.audience !== "owner-private") return { permitted: false, reason: "SCOPE_HOLD" };
  if (!record || !request.objectId || !request.childFileSpace ||
      record.objectId !== request.objectId || record.childFileSpace !== request.childFileSpace ||
      !policy.allowedObjectIds.includes(request.objectId) ||
      !policy.allowedChildFileSpaces.includes(request.childFileSpace)) {
    return { permitted: false, reason: "OBJECT_HOLD" };
  }
  if (record.admission !== "NATIVE_ADMITTED" || record.rights !== "PERMITTED") {
    return { permitted: false, reason: "SOURCE_HOLD" };
  }
  if (!Number.isInteger(request.hydration) || request.hydration < 0 || request.hydration > 3) {
    return { permitted: false, reason: "EXECUTION_HOLD" };
  }
  if (!views.has(request.view as FileSpaceView)) return { permitted: false, reason: "VIEW_HOLD" };

  const spatial = request.view === "twin-3d" || request.view === "map-spatial";
  const metricQualified = record.geometry?.independentlyValidated === true &&
    typeof record.geometry.frame === "string" && Boolean(record.geometry.frame.trim()) &&
    typeof record.geometry.units === "string" && Boolean(record.geometry.units.trim());
  const frontier = spatial && !metricQualified ? "METRIC_GEOMETRY_UNQUALIFIED" : "NONE";
  const primaryView: FileSpaceView = frontier === "NONE"
    ? request.view as FileSpaceView : "evidence-claim";
  const hydration = Math.min(request.hydration, policy.hydrationCeiling) as 0 | 1 | 2 | 3;
  return {
    permitted: true, objectId: request.objectId, childFileSpace: request.childFileSpace,
    primaryView, hydration, evidenceClass: record.evidenceClass,
    projectionStatus: "ELIGIBLE_R3_READ_ONLY", frontier,
  };
}
