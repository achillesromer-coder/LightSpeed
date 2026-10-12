import { resolveDesktopOrigin } from "./desktopBridge";

export interface MobileLinkManifest {
  schema: "cgx.ls-go.mobile-link/1";
  host_node: string;
  bridge: {
    remote_transport: string;
    discovery: string;
    probe: string;
    owner_sign_in: string;
  };
  constraints: {
    embedded_credentials: boolean;
    public_direct_execution: boolean;
    automatic_owner_approval: boolean;
    fail_closed_on_missing_relay_or_auth: boolean;
  };
}

export type LinkState =
  | "needs_relay" | "needs_auth" | "degraded"
  | "connected" | "offline" | "disconnected";

export function readMobileManifest(value: unknown): MobileLinkManifest {
  if (!value || typeof value !== "object") throw new TypeError("Unsupported or unsafe CGX mobile manifest");
  const manifest = value as Partial<MobileLinkManifest>;
  const bridge = manifest.bridge;
  const policy = manifest.constraints;
  if (manifest.schema !== "cgx.ls-go.mobile-link/1" ||
      manifest.host_node !== "bouwerbase" ||
      bridge?.remote_transport !== "owner_selected_private_https_relay" ||
      bridge.discovery !== "configured_origin_only" ||
      bridge.probe !== "GET /api/v1/status" ||
      bridge.owner_sign_in !== "POST /api/v1/auth/login" ||
      policy?.embedded_credentials !== false ||
      policy.public_direct_execution !== false ||
      policy.automatic_owner_approval !== false ||
      policy.fail_closed_on_missing_relay_or_auth !== true) {
    throw new TypeError("Unsupported or unsafe CGX mobile manifest");
  }
  return manifest as MobileLinkManifest;
}

export function resolveMobileRelayOrigin(input: string, pageHostname: string): string {
  if (!input.trim()) throw new TypeError("Enter the owner-controlled HTTPS relay origin");
  const origin = resolveDesktopOrigin(input);
  const localPage = ["localhost", "127.0.0.1", "::1", "[::1]"].includes(pageHostname.toLowerCase());
  if (!localPage && !origin.startsWith("https://")) {
    throw new TypeError("Mobile and off-device connections require an HTTPS relay");
  }
  return origin;
}

export function linkStateFromStatus(
  reachable: boolean, authConfigured: boolean, changeRequired: boolean,
  signedIn: boolean, healthy: boolean,
): LinkState {
  if (!reachable) return "offline";
  if (!authConfigured || changeRequired || !signedIn) return "needs_auth";
  return healthy ? "connected" : "degraded";
}

export function linkStateText(state: LinkState): string {
  return ({
    needs_relay: "Private bridge unavailable; Drive exchange can be used asynchronously.",
    needs_auth: "Bridge reachable; existing owner sign-in is required.",
    degraded: "Owner signed in; desktop health needs review.",
    connected: "Bridge and owner session available; receipt verification still required.",
    offline: "Bridge unreachable. Drive fallback does not execute commands.",
    disconnected: "Operator disconnected; no requests automatically submitted.",
  } satisfies Record<LinkState, string>)[state];
}
