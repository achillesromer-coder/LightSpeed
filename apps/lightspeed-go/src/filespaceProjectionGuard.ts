/**
 * UniSpace R3 PRESENTATION guard. Source-only review adapter, not an auth service.
 * A browser can forge every field below: the existing host must validate issuer,
 * revocation, lease, Object_ID, FileSpace, DBR and ACL BEFORE sending any payload.
 * This module must never be used to authorise fetches, execute CCC, or grant access.
 * Contract basis: CGX-VIEW-SELECTION-POLICY/0.1 and issue #158.
 */
export type ViewIntent = "tree" | "graph" | "spatial" | "evidence";
export type Hydration = "H0" | "H1" | "H2" | "H3" | "H4";
export type EvidenceClass = "CREATIVE" | "SCIENTIFIC" | "OPERATIONAL";

export interface ViewSelection {
  objectId: string;
  childFileSpaceId: string;
  view: ViewIntent;
  hydration: Hydration;
  offline: boolean;
}

/** Opaque, redacted status metadata from the EXISTING authenticated host bridge. */
export interface HostProjectionReceipt {
  objectId: string;
  childFileSpaceId: string;
  stage: "SANDBOX_STAGED" | "NATIVE_ADMITTED" | "HOLD";
  rights: "PUBLIC_SAFE" | "PRIVATE_AUTHORISED" | "HOLD";
  issuerVerified: boolean;
  revocationChecked: boolean;
  leaseValid: boolean;
  aclAllowed: boolean;
  rootDbrVerified: boolean;
  allowedViews: readonly ViewIntent[];
  maxHydration: "H0" | "H1" | "H2";
  evidenceClass: EvidenceClass;
  evidenceCeiling: "R0" | "R1" | "R2" | "R3";
  geometry?: { sourceVerified: boolean; independentlyMetricValidated?: boolean; frame: string; units: string };
}

export type ProjectionDecision =
  | { state: "DENIED"; reason: string }
  | { state: "FRONTIER"; reason: string; view: "evidence"; hydration: "H0" }
  | { state: "READY"; objectId: string; childFileSpaceId: string; view: ViewIntent;
      hydration: "H0" | "H1" | "H2"; evidenceClass: EvidenceClass;
      evidenceCeiling: HostProjectionReceipt["evidenceCeiling"]; note: string };

const LEVEL: Record<Hydration, number> = { H0: 0, H1: 1, H2: 2, H3: 3, H4: 4 };
const VALID_VIEWS: readonly ViewIntent[] = ["tree", "graph", "spatial", "evidence"];
const VALID_CLASSES: readonly EvidenceClass[] = ["CREATIVE", "SCIENTIFIC", "OPERATIONAL"];
const VALID_CEILINGS = ["R0", "R1", "R2", "R3"] as const;
const VALID_LEVELS = ["H0", "H1", "H2"] as const;

/** Display-only. Denied decisions deliberately omit Object_ID and private locators. */
export function projectFileSpaceView(
  selection: ViewSelection,
  receipt: HostProjectionReceipt | null,
): ProjectionDecision {
  if (!receipt) return { state: "DENIED", reason: "NO_HOST_RECEIPT" };
  if (!selection.objectId || !selection.childFileSpaceId ||
      selection.objectId !== receipt.objectId ||
      selection.childFileSpaceId !== receipt.childFileSpaceId) {
    return { state: "DENIED", reason: "EXACT_OBJECT_OR_CHILD_SCOPE_MISMATCH" };
  }
  if (receipt.stage !== "NATIVE_ADMITTED" ||
      (receipt.rights !== "PUBLIC_SAFE" && receipt.rights !== "PRIVATE_AUTHORISED")) {
    return { state: "DENIED", reason: "ADMISSION_OR_RIGHTS_HOLD" };
  }
  if (receipt.issuerVerified !== true || receipt.revocationChecked !== true ||
      receipt.leaseValid !== true || receipt.aclAllowed !== true ||
      receipt.rootDbrVerified !== true) {
    return { state: "DENIED", reason: "HOST_AUTHORITY_UNVERIFIED" };
  }
  if (!VALID_CLASSES.includes(receipt.evidenceClass) ||
      !VALID_CEILINGS.includes(receipt.evidenceCeiling) ||
      !Object.prototype.hasOwnProperty.call(LEVEL, selection.hydration) ||
      !VALID_VIEWS.includes(selection.view) || !Array.isArray(receipt.allowedViews) ||
      !receipt.allowedViews.includes(selection.view) ||
      !VALID_LEVELS.includes(receipt.maxHydration)) {
    return { state: "DENIED", reason: "PROJECTION_POLICY_MISMATCH" };
  }
  // Offline revocation cannot be freshly checked: only approved public H0 metadata.
  if (selection.offline && receipt.rights !== "PUBLIC_SAFE") {
    return { state: "DENIED", reason: "OFFLINE_PRIVATE_SOURCE_DENIED" };
  }
  if (selection.offline && selection.hydration !== "H0") {
    return { state: "FRONTIER", reason: "OFFLINE_PUBLIC_H0_ONLY", view: "evidence", hydration: "H0" };
  }
  // Metric scientific/operational views require independent verification; creative previews remain labelled.
  if (selection.view === "spatial" &&
      (receipt.geometry?.sourceVerified !== true ||
       (receipt.evidenceClass !== "CREATIVE" && receipt.geometry?.independentlyMetricValidated !== true) ||
       typeof receipt.geometry.frame !== "string" || !receipt.geometry.frame.trim() ||
       typeof receipt.geometry.units !== "string" || !receipt.geometry.units.trim())) {
    return { state: "FRONTIER", reason: "GEOMETRY_FRAME_UNITS_OR_SOURCE_UNVERIFIED", view: "evidence", hydration: "H0" };
  }
  // This is a READ-ONLY R3 viewport. H3 capability and H4 execution are not here.
  if (LEVEL[selection.hydration] > 2) {
    return { state: "DENIED", reason: "H3_H4_REQUIRE_SEPARATE_HOST_CAPABILITY" };
  }
  const allowedLevel = Math.min(LEVEL[selection.hydration], LEVEL[receipt.maxHydration]);
  const hydration = VALID_LEVELS[allowedLevel];
  return {
    state: "READY", objectId: receipt.objectId, childFileSpaceId: receipt.childFileSpaceId,
    view: selection.view, hydration, evidenceClass: receipt.evidenceClass,
    evidenceCeiling: receipt.evidenceCeiling,
    note: allowedLevel < LEVEL[selection.hydration] ? "HYDRATION_REDUCED_BY_HOST" : "SOURCE_SCOPED_READ_ONLY",
  };
}
