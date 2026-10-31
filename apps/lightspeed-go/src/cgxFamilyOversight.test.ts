import { describe, expect, it } from "vitest";
import { renderCgxFamilyOversight, type CgxFamilyOversightSnapshot } from "./cgxFamilyOversight";

const fixture = (): CgxFamilyOversightSnapshot => ({
  schema: "CGX-LS-FAMILY-OVERSIGHT/0.1",
  mode: "OWNER_PRIVATE_READ_ONLY_NATIVE_AND_SOURCE_INDEX",
  parent: {
    semantic_object_id: "cgx:root:cognigrex",
    filespace: "Cognigrex.cgx",
    operational: {
      resolution: "OPERATIONAL_ROW_OBSERVED_NOT_DBR_ADMISSION",
      operational_state: "candidate",
      identifier_state: "active",
      representation_count: 1,
    },
    carrier: { state: "LOCAL_BYTES_MATCH_REGISTRY", byte_binding_match: true },
    native_parent_admitted: false,
  },
  families: [{
    domain: "lightspeed",
    semantic_object_id: "cgx:domain:lightspeed",
    parent_semantic_object_id: "cgx:domain:emassc",
    filespace: "LS.cgx",
    operational: {
      resolution: "NO_NATIVE_OBJECT_MATCH",
      operational_state: "UNRESOLVED",
      identifier_state: "UNRESOLVED",
      representation_count: 0,
    },
    load_source_reference_count: 1,
    native_child_accepted: false,
    scope_owner_acl_verified: false,
    load_alias_admitted: false,
    runtime_capability_installed: false,
  }],
  load_alexandria: {
    state: "SOURCE_REFERENCES_ONLY_NOT_ADMITTED", reference_count: 131,
    source_registry_count: 14, frontier_count: 3, native_accepted: 0,
  },
  effects: {
    canonical_db_writes: 0, object_ids_minted: 0,
    source_bytes_copied: 0, public_release: false,
  },
});

describe("CGX LS owner-only family oversight renderer", () => {
  it("retains semantic parent-child lineage, candidate and source-only states", () => {
    const output = renderCgxFamilyOversight(fixture());
    expect(output).toContain("Cognigrex.cgx");
    expect(output).toContain("LS.cgx");
    expect(output).toContain("cgx:domain:emassc");
    expect(output).toContain("131");
    expect(output).toContain("14");
    expect(output).toContain("3");
    expect(output).toContain("not an owner signature");
  });
  it("escapes untrusted labels instead of accepting markup", () => {
    const value = fixture();
    value.families[0].filespace = '<img src=x onerror=alert(1)>';
    const output = renderCgxFamilyOversight(value);
    expect(output).not.toContain("<img src=x");
    expect(output).toContain("&lt;img");
  });
  it("fails closed on inferred native admission or mutated effects", () => {
    const admitted = fixture();
    admitted.families[0].native_child_accepted = true as false;
    expect(renderCgxFamilyOversight(admitted)).toContain("Unverified authority claim");
    const mutated = fixture();
    mutated.effects.canonical_db_writes = 1;
    expect(renderCgxFamilyOversight(mutated)).toContain("contract invalid");
  });
});
