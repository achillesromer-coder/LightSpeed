import { describe, expect, it } from "vitest";
import manifest from "../public/data/site_integration.json";
import {
  escapeSiteLabel, projectSiteIntegration, SITE_VIEW_SCHEMA,
} from "./siteIntegrationProjection";

describe("CGX LS GO site-side integration security projection", () => {
  const proposed = (patch: Record<string, unknown> = {}) =>
    ({ ...manifest, ...patch });

  it("binds existing owner-manifest fields but never claims deployment", () => {
    const s = projectSiteIntegration(manifest);
    expect(s.schema).toBe(SITE_VIEW_SCHEMA);
    expect(s.manifestEvidence).toBe("REVIEW_SOURCE_ONLY");
    expect(s.authority).toEqual(manifest.authority_chain);
    expect(s.sourceStatus).toContain("exact current Git and Drive readback pending");
    expect(s.sourceStatus).not.toContain("Git review source current");
    expect(s.launchStatus).toContain("held");
    expect(s.nativeVerified).toBe(false);
    expect(s.publicDeployed).toBe(false);
    expect(s.dbrVerified).toBe(false);
  });

  it("escapes HTML special characters in all manifest label slots", () => {
    expect(escapeSiteLabel("<img src=x onerror='x'>&\"")).toBe(
      "&lt;img src=x onerror=&#39;x&#39;&gt;&amp;&quot;"
    );
  });

  it("does not turn an injection-shaped authority label into markup", () => {
    const s = projectSiteIntegration(proposed({
      authority_chain: ["<svg/onload=alert(1)>", ...manifest.authority_chain.slice(1)],
    }));
    expect(s.manifestEvidence).toBe("REVIEW_SOURCE_ONLY");
    expect(escapeSiteLabel(s.authority[0])).toBe("&lt;svg/onload=alert(1)&gt;");
  });

  it("does not promote a forged public-state source label", () => {
    const s = projectSiteIntegration(proposed({
      source_state_label: "Published and minted",
      launch_state_label: "All native gates passed",
    }));
    expect(s.sourceStatus).not.toContain("Published and minted");
    expect(s.launchStatus).not.toContain("All native gates passed");
    expect(s.publicDeployed).toBe(false);
  });

  it("rejects a JSON manifest without the pinned review schema", () => {
    const s = projectSiteIntegration(proposed({ schema_version: "future-authority-v3" }));
    expect(s.manifestEvidence).toBe("INVALID_SOURCE_HELD");
  });

  it("rejects a request to create a second site", () => {
    expect(projectSiteIntegration(proposed({ create_new_site: true }))
      .manifestEvidence).toBe("INVALID_SOURCE_HELD");
  });

  it("rejects a manifest claiming public release", () => {
    expect(projectSiteIntegration(proposed({ publish_state: "deployed" }))
      .manifestEvidence).toBe("INVALID_SOURCE_HELD");
  });

  it("rejects a source commit claim as a host proof", () => {
    expect(projectSiteIntegration(proposed({ source_commit: "a".repeat(40) }))
      .manifestEvidence).toBe("INVALID_SOURCE_HELD");
  });

  it("rejects any future effectful release gate in a source document", () => {
    for (const flag of Object.keys(manifest.release_gates)) {
      const s = projectSiteIntegration(proposed({
        release_gates: { ...manifest.release_gates, [flag]: true },
      }));
      expect(s.manifestEvidence, flag).toBe("INVALID_SOURCE_HELD");
      expect(s.publicDeployed).toBe(false);
      expect(s.nativeVerified).toBe(false);
    }
  });

  it("rejects a truncated or untyped release gate register", () => {
    expect(projectSiteIntegration(proposed({ release_gates: {} }))
      .manifestEvidence).toBe("INVALID_SOURCE_HELD");
    expect(projectSiteIntegration(proposed({ release_gates: "all passed" }))
      .manifestEvidence).toBe("INVALID_SOURCE_HELD");
  });

  it("rejects oversized and control-character authority labels", () => {
    expect(projectSiteIntegration(proposed({
      authority_chain: ["a".repeat(10000)],
    })).manifestEvidence).toBe("INVALID_SOURCE_HELD");
    expect(projectSiteIntegration(proposed({
      authority_chain: ["legit\nspoofed", "runtime"],
    })).manifestEvidence).toBe("INVALID_SOURCE_HELD");
  });

  it("rejects prototype-shaped or cyclic manifest data", () => {
    expect(projectSiteIntegration(null).manifestEvidence).toBe("INVALID_SOURCE_HELD");
    expect(projectSiteIntegration([]).manifestEvidence).toBe("INVALID_SOURCE_HELD");
    expect(projectSiteIntegration({
      ...manifest, authority_chain: [null, 2],
    }).manifestEvidence).toBe("INVALID_SOURCE_HELD");
  });

  it("preserves singleton authority even when source input is invalid", () => {
    const s = projectSiteIntegration({
      schema_version: "invalid", authority_chain: ["untrusted root"],
    });
    expect(s.authority).not.toContain("untrusted root");
    expect(s.authority).toContain("Existing LightSpeed runtime");
    expect(s.dbrVerified).toBe(false);
  });
});
