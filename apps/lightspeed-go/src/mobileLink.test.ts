import { describe, expect, it } from "vitest";
import { linkStateFromStatus, readMobileManifest, resolveMobileRelayOrigin } from "./mobileLink";

const valid = {
  schema: "cgx.ls-go.mobile-link/1",
  host_node: "bouwerbase",
  bridge: {
    remote_transport: "owner_selected_private_https_relay",
    discovery: "configured_origin_only",
    probe: "GET /api/v1/status",
    owner_sign_in: "POST /api/v1/auth/login",
  },
  constraints: {
    embedded_credentials: false,
    public_direct_execution: false,
    automatic_owner_approval: false,
    fail_closed_on_missing_relay_or_auth: true,
  },
};

describe("CGX mobile bootstrap (no mobile runtime)", () => {
  it("accepts only the bounded host/transport and fails closed on altered authority", () => {
    expect(readMobileManifest(valid).host_node).toBe("bouwerbase");
    expect(() => readMobileManifest({ ...valid, host_node: "random-host" })).toThrow("unsafe");
    expect(() => readMobileManifest({ ...valid, constraints: { ...valid.constraints, automatic_owner_approval: true } })).toThrow("unsafe");
  });
  it("requires configured private HTTPS origin for the hosted site", () => {
    expect(resolveMobileRelayOrigin("https://private.example.test", "lightspeed-go.example.test")).toBe("https://private.example.test");
    expect(() => resolveMobileRelayOrigin("http://127.0.0.1:8765", "lightspeed-go.example.test")).toThrow("require an HTTPS relay");
    expect(() => resolveMobileRelayOrigin("", "lightspeed-go.example.test")).toThrow("Enter");
    expect(() => resolveMobileRelayOrigin("http://public.example.test", "lightspeed-go.example.test")).toThrow("use HTTPS");
  });
  it("allows local development loopback only from a local page", () => {
    expect(resolveMobileRelayOrigin("http://127.0.0.1:8765", "localhost")).toBe("http://127.0.0.1:8765");
  });
  it("rejects origins containing secrets or paths", () => {
    expect(() => resolveMobileRelayOrigin("https://x:y@private.example.test", "lightspeed-go.example.test")).toThrow("credentials");
    expect(() => resolveMobileRelayOrigin("https://private.example.test/api", "lightspeed-go.example.test")).toThrow("path");
  });
  it("keeps bridge reachability separate from authenticated, healthy operation", () => {
    expect(linkStateFromStatus(false, true, false, false, true)).toBe("offline");
    expect(linkStateFromStatus(true, false, false, false, true)).toBe("needs_auth");
    expect(linkStateFromStatus(true, true, true, false, true)).toBe("needs_auth");
    expect(linkStateFromStatus(true, true, false, false, true)).toBe("needs_auth");
    expect(linkStateFromStatus(true, true, false, true, false)).toBe("degraded");
    expect(linkStateFromStatus(true, true, false, true, true)).toBe("connected");
  });
});
