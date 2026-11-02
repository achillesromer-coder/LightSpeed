import { describe, expect, it } from "vitest";
import { derivePrivateFileSpaceProjection, type TrustedHostProjectionPolicy,
  type QualifiedFileSpaceRecord, type FileSpaceProjectionRequest } from "./filespaceProjectionGate";

const policy: TrustedHostProjectionPolicy = {
  hostSessionVerified: true, issuerVerified: true, revocationChecked: true,
  leaseValid: true, rootReadbackVerified: true, dbrReadbackVerified: true,
  audience: "owner-private", allowedObjectIds: ["cgx:admitted:one"],
  allowedChildFileSpaces: ["cgx:filespace:eco"], hydrationCeiling: 2,
};
const record: QualifiedFileSpaceRecord = {
  objectId: "cgx:admitted:one", childFileSpace: "cgx:filespace:eco",
  admission: "NATIVE_ADMITTED", rights: "PERMITTED", evidenceClass: "SCIENTIFIC",
  sourceLocator: "C:\\PRIVATE\\DO_NOT_LEAK", rawSourceText: "DO_NOT_LEAK",
};
const request: FileSpaceProjectionRequest = {
  objectId: record.objectId, childFileSpace: record.childFileSpace,
  view: "filespace-tree", hydration: 3,
};
const run = (p = policy, r = record, q = request) => derivePrivateFileSpaceProjection(p, r, q);

describe("private FileSpace R3 source-only projection guard", () => {
  it("allows only a read-only, bounded H0-H3 projection", () => {
    expect(run()).toMatchObject({ permitted: true, primaryView: "filespace-tree", hydration: 2,
      projectionStatus: "ELIGIBLE_R3_READ_ONLY" });
  });
  it("never returns private paths, text or credentials", () => {
    const json = JSON.stringify(run());
    expect(json).not.toContain("DO_NOT_LEAK");
    expect(json).not.toContain("sourceLocator");
  });
  it.each(["hostSessionVerified", "issuerVerified", "revocationChecked", "leaseValid",
    "rootReadbackVerified", "dbrReadbackVerified"] as const)("fails closed if %s is false", (key) => {
    expect(run({ ...policy, [key]: false })).toEqual({ permitted: false, reason: "HOST_AUTH_HOLD" });
  });
  it("denies public audience despite otherwise valid assertions", () => {
    expect(run({ ...policy, audience: "public" })).toEqual({ permitted: false, reason: "SCOPE_HOLD" });
  });
  it("denies cross-child or cross-object hydration", () => {
    expect(run(policy, record, { ...request, childFileSpace: "cgx:filespace:romer" }))
      .toEqual({ permitted: false, reason: "OBJECT_HOLD" });
    expect(run(policy, record, { ...request, objectId: "cgx:admitted:other" }))
      .toEqual({ permitted: false, reason: "OBJECT_HOLD" });
  });
  it("denies source-only candidates and unqualified rights", () => {
    expect(run(policy, { ...record, admission: "SANDBOX_STAGED" }))
      .toEqual({ permitted: false, reason: "SOURCE_HOLD" });
    expect(run(policy, { ...record, rights: "UNKNOWN" }))
      .toEqual({ permitted: false, reason: "SOURCE_HOLD" });
  });
  it("denies H4 execution and invalid hydration", () => {
    expect(run(policy, record, { ...request, hydration: 4 }))
      .toEqual({ permitted: false, reason: "EXECUTION_HOLD" });
    expect(run(policy, record, { ...request, hydration: Number.NaN }))
      .toEqual({ permitted: false, reason: "EXECUTION_HOLD" });
  });
  it("denies unknown view names", () => {
    expect(run(policy, record, { ...request, view: "arbitrary-admin" }))
      .toEqual({ permitted: false, reason: "VIEW_HOLD" });
  });
  it("downgrades unqualified 3D to evidence Frontier, not fabricated geometry", () => {
    expect(run(policy, record, { ...request, view: "twin-3d" })).toMatchObject({
      permitted: true, primaryView: "evidence-claim", frontier: "METRIC_GEOMETRY_UNQUALIFIED",
    });
  });
  it("requires validated metric geometry, frame and units for spatial view", () => {
    expect(run(policy, { ...record, geometry: { independentlyValidated: true, frame: "", units: "m" } },
      { ...request, view: "map-spatial" })).toMatchObject({ primaryView: "evidence-claim" });
    expect(run(policy, { ...record, geometry: { independentlyValidated: true, frame: "EPSG:7856", units: "m" } },
      { ...request, view: "map-spatial" })).toMatchObject({ primaryView: "map-spatial", frontier: "NONE" });
  });
});
