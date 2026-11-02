import { describe, expect, it } from "vitest";
import { projectFileSpaceView, type HostProjectionReceipt, type ViewSelection } from "./filespaceProjectionGuard";

// Synthetic fixture: no real Object_ID, private corpus, tokens or ACL material.
const selection: ViewSelection = {
  objectId: "cgx:test:synthetic-object", childFileSpaceId: "cgx:test:synthetic-child",
  view: "tree", hydration: "H2", offline: false,
};
const receipt: HostProjectionReceipt = {
  objectId: selection.objectId, childFileSpaceId: selection.childFileSpaceId,
  stage: "NATIVE_ADMITTED", rights: "PRIVATE_AUTHORISED", issuerVerified: true,
  revocationChecked: true, leaseValid: true, aclAllowed: true, rootDbrVerified: true,
  allowedViews: ["tree", "graph", "spatial", "evidence"], maxHydration: "H2",
  evidenceClass: "OPERATIONAL", evidenceCeiling: "R1",
};
const decide = (s: ViewSelection = selection, r: HostProjectionReceipt | null = receipt) => projectFileSpaceView(s, r);

describe("UniSpace source-scoped FileSpace R3 display guard", () => {
  it("denies missing host receipt without exposing object identity", () => {
    expect(decide(selection, null)).toEqual({ state: "DENIED", reason: "NO_HOST_RECEIPT" });
  });
  it("denies cross-child hydration", () => {
    expect(decide({ ...selection, childFileSpaceId: "cgx:test:other-child" }).state).toBe("DENIED");
  });
  it("denies cross-object hydration", () => {
    expect(decide({ ...selection, objectId: "cgx:test:other-object" }).state).toBe("DENIED");
  });
  it("denies staged-only candidates", () => {
    expect(decide(selection, { ...receipt, stage: "SANDBOX_STAGED" }).state).toBe("DENIED");
  });
  it("denies revoked or expired authority", () => {
    expect(decide(selection, { ...receipt, leaseValid: false }).state).toBe("DENIED");
    expect(decide(selection, { ...receipt, revocationChecked: false }).state).toBe("DENIED");
  });
  it("denies an unauthorised or missing DBR scope", () => {
    expect(decide(selection, { ...receipt, aclAllowed: false }).state).toBe("DENIED");
    expect(decide(selection, { ...receipt, rootDbrVerified: false }).state).toBe("DENIED");
  });
  it("denies offline private projections even if a stale receipt says valid", () => {
    expect(decide({ ...selection, offline: true }).state).toBe("DENIED");
  });
  it("limits offline public to H0 metadata", () => {
    expect(decide({ ...selection, offline: true }, { ...receipt, rights: "PUBLIC_SAFE" }).state).toBe("FRONTIER");
    expect(decide({ ...selection, offline: true, hydration: "H0" }, { ...receipt, rights: "PUBLIC_SAFE" }).state).toBe("READY");
  });
  it("refuses unverified spatial geometry rather than inventing 3D", () => {
    expect(decide({ ...selection, view: "spatial" }).state).toBe("FRONTIER");
    expect(decide({ ...selection, view: "spatial" }, { ...receipt, geometry: { sourceVerified: true, frame: "", units: "m" } }).state).toBe("FRONTIER");
  });
  it("requires independent metric validation for SCIENTIFIC spatial projections", () => {
    const scientific: HostProjectionReceipt = {
      ...receipt, evidenceClass: "SCIENTIFIC",
      geometry: { sourceVerified: true, frame: "EPSG:7856", units: "m" },
    };
    expect(decide({ ...selection, view: "spatial" }, scientific).state).toBe("FRONTIER");
    expect(decide({ ...selection, view: "spatial" }, {
      ...scientific, geometry: { ...scientific.geometry!, independentlyMetricValidated: true },
    }).state).toBe("READY");
  });
  it("allows verified source-bound spatial presentation without increasing evidence", () => {
    const decision = decide({ ...selection, view: "spatial" }, {
      ...receipt, geometry: { sourceVerified: true, frame: "local-frame", units: "m" },
    });
    expect(decision.state).toBe("READY");
    if (decision.state === "READY") expect(decision.evidenceCeiling).toBe("R1");
  });
  it("refuses H3/H4 effectful requests", () => {
    expect(decide({ ...selection, hydration: "H3" }).state).toBe("DENIED");
    expect(decide({ ...selection, hydration: "H4" }).state).toBe("DENIED");
  });
  it("never exceeds the host's hydration ceiling", () => {
    const decision = decide(selection, { ...receipt, maxHydration: "H1" });
    expect(decision.state).toBe("READY");
    if (decision.state === "READY") {
      expect(decision.hydration).toBe("H1");
      expect(decision.note).toBe("HYDRATION_REDUCED_BY_HOST");
    }
  });
  it("denies views outside host allowlist", () => {
    expect(decide({ ...selection, view: "graph" }, { ...receipt, allowedViews: ["tree"] }).state).toBe("DENIED");
  });
  it("does not leak private locators or raw source in any result", () => {
    const output = JSON.stringify(decide(selection, { ...receipt, rights: "HOLD" }));
    expect(output).not.toContain(selection.objectId);
    expect(output).not.toContain(selection.childFileSpaceId);
  });
});
