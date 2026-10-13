import { describe, expect, it, vi } from "vitest";
import { disconnectMobileConnection, linkStateFromStatus, parseMobileCarrier, readMobileManifest, resolveMobileRelayOrigin, saveMobileConnection } from "./mobileLink";
import { MOBILE_LINK_DISCONNECTED_KEY, MOBILE_LINK_ORIGIN_KEY, readDesktopStatus, resolveActiveDesktopOrigin } from "./desktopBridge";
import shippedCarrier from "../public/cgx-mobile-link.cgx?raw";

const valid = {
  schema: "cgx.ls-go.mobile-link/1",
  semantic_root: "cgx://cgx.cgx",
  kind: "CGX-MOBILE-BOOTSTRAP/0.1",
  binding: "CGX-MOBILE-NODE-BINDING/0.1",
  protocol_chain: ["CGX-MOBILE-BOOTSTRAP/0.1", "CGX-DEVICE-HANDSHAKE/0.1", "CGX-NODE-EXCHANGE-CONTRACT/0.1"],
  mobile_role: "roaming_operator",
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
    new_backend: false,
    new_mobile_runtime: false,
    authority_by_device: false,
    transfer_full_corpus_on_open: false,
    drive_write_grants_execution: false,
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
  it("uses one carrier compatible with the Android binding fields", () => {
    expect(parseMobileCarrier(shippedCarrier, "cgx-mobile-link.cgx").semantic_root).toBe("cgx://cgx.cgx");
    expect(() => readMobileManifest({ ...valid, semantic_root: "cgx://other" })).toThrow("unsafe");
    expect(() => readMobileManifest({ ...valid, protocol_chain: valid.protocol_chain.slice().reverse() })).toThrow("unsafe");
    expect(() => readMobileManifest({ ...valid, constraints: { ...valid.constraints, new_mobile_runtime: "false" } })).toThrow("unsafe");
  });
  it("bounds imported files and ignores carrier-provided credentials and origins", () => {
    expect(() => parseMobileCarrier(JSON.stringify(valid), "other.json")).toThrow(".cgx");
    expect(() => parseMobileCarrier(" ".repeat(65537), "large.cgx")).toThrow("64 KiB");
    expect(() => parseMobileCarrier("broken", "link.cgx")).toThrow();
    const carrier = readMobileManifest({ ...valid, authenticated: true, session_token: "forged", bridge: { ...valid.bridge, origin: "https://attacker.test" } });
    expect(carrier).not.toHaveProperty("authenticated");
    expect(carrier).not.toHaveProperty("session_token");
    expect(carrier.bridge).not.toHaveProperty("origin");
  });
  it("never treats HTTPS loopback as an off-device route", () => {
    for (const origin of ["https://localhost", "https://localhost.", "https://x.localhost", "https://127.0.0.1", "https://127.0.0.2", "https://[::1]", "https://[::ffff:127.0.0.1]"]) {
      expect(() => resolveMobileRelayOrigin(origin, "hosted.example.test")).toThrow("HTTPS relay");
      expect(resolveActiveDesktopOrigin(origin, undefined, "hosted.example.test")).toBe("");
    }
    expect(resolveActiveDesktopOrigin(null, undefined, "hosted.example.test")).toBe("");
    expect(resolveActiveDesktopOrigin("broken", "https://private.example.test", "hosted.example.test")).toBe("https://private.example.test");
    expect(resolveActiveDesktopOrigin(null, undefined, "localhost")).toBe("http://127.0.0.1:8765");
  });
  it("persists only the selected route and explicit disconnect preference", () => {
    const values = new Map<string, string>();
    const storage = { setItem: (key: string, value: string) => { values.set(key, value); }, removeItem: (key: string) => { values.delete(key); } };
    expect(saveMobileConnection(storage, "https://private.example.test", "hosted.example.test")).toBe("https://private.example.test");
    expect([...values.keys()]).toEqual([MOBILE_LINK_ORIGIN_KEY]);
    disconnectMobileConnection(storage);
    expect([...values]).toEqual([[MOBILE_LINK_DISCONNECTED_KEY, "true"]]);
    saveMobileConnection(storage, "https://other.example.test", "hosted.example.test");
    expect([...values]).toEqual([[MOBILE_LINK_ORIGIN_KEY, "https://other.example.test"]]);
  });
  it("rejects an unconfigured request before issuing any fetch", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    try {
      await expect(readDesktopStatus("")).rejects.toThrow("Connect");
      expect(fetchSpy).not.toHaveBeenCalled();
    } finally { fetchSpy.mockRestore(); }
  });
});
