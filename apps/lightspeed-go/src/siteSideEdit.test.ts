import { describe, expect, it } from "vitest";
import manifest from "../public/data/site_integration.json";

describe("LS GO site integration manifest", () => {
  it("binds the current review source without claiming a deployed commit", () => {
    expect(manifest.schema_version).toBe("lightspeed-go-sites-integration-v2");
    expect(manifest.source_pull_request).toBe(44);
    expect(manifest.source_commit).toBeNull();
    expect(manifest.publish_state).toBe("review_source_verified_deployment_held");
    expect(manifest.source_state_label).toContain("Drive successor pending");
  });

  it("keeps every external transition fail closed", () => {
    expect(manifest.current_views).toEqual([
      "Command",
      "Activity",
      "Objects",
      "System",
      "Sources",
    ]);
    expect(manifest.release_gates).toEqual({
      owner_credential_ready: false,
      private_relay_configured: false,
      off_device_verified: false,
      accepted_head_installed: false,
      drive_successor_readback: false,
      public_deployment_verified: false,
      public_direct_execution: false,
    });
  });
});
