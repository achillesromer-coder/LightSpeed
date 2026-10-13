import { MOBILE_LINK_DISCONNECTED_KEY, MOBILE_LINK_ORIGIN_KEY, isLoopbackOriginHost, resolveDesktopOrigin } from "./desktopBridge";

export interface MobileLinkManifest {
  schema: "cgx.ls-go.mobile-link/1";
  semantic_root: "cgx://cgx.cgx";
  kind: "CGX-MOBILE-BOOTSTRAP/0.1";
  binding: "CGX-MOBILE-NODE-BINDING/0.1";
  protocol_chain: string[];
  mobile_role: "roaming_operator";
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
    new_backend: boolean;
    new_mobile_runtime: boolean;
    authority_by_device: boolean;
    transfer_full_corpus_on_open: boolean;
    drive_write_grants_execution: boolean;
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
      manifest.semantic_root !== "cgx://cgx.cgx" ||
      manifest.kind !== "CGX-MOBILE-BOOTSTRAP/0.1" ||
      manifest.binding !== "CGX-MOBILE-NODE-BINDING/0.1" ||
      manifest.mobile_role !== "roaming_operator" ||
      !Array.isArray(manifest.protocol_chain) ||
      JSON.stringify(manifest.protocol_chain) !== JSON.stringify([
        "CGX-MOBILE-BOOTSTRAP/0.1", "CGX-DEVICE-HANDSHAKE/0.1", "CGX-NODE-EXCHANGE-CONTRACT/0.1",
      ]) ||
      manifest.host_node !== "bouwerbase" ||
      bridge?.remote_transport !== "owner_selected_private_https_relay" ||
      bridge.discovery !== "configured_origin_only" ||
      bridge.probe !== "GET /api/v1/status" ||
      bridge.owner_sign_in !== "POST /api/v1/auth/login" ||
      policy?.embedded_credentials !== false ||
      policy.public_direct_execution !== false ||
      policy.automatic_owner_approval !== false ||
      policy.new_backend !== false || policy.new_mobile_runtime !== false ||
      policy.authority_by_device !== false || policy.transfer_full_corpus_on_open !== false ||
      policy.drive_write_grants_execution !== false ||
      policy.fail_closed_on_missing_relay_or_auth !== true) {
    throw new TypeError("Unsupported or unsafe CGX mobile manifest");
  }
  // Drop arbitrary carrier fields, including endpoint/auth assertions. The operator selects the route.
  return {
    schema: manifest.schema, semantic_root: manifest.semantic_root, kind: manifest.kind,
    binding: manifest.binding, protocol_chain: [...manifest.protocol_chain],
    mobile_role: manifest.mobile_role, host_node: manifest.host_node,
    bridge: { remote_transport: bridge.remote_transport, discovery: bridge.discovery,
      probe: bridge.probe, owner_sign_in: bridge.owner_sign_in },
    constraints: { embedded_credentials: false, public_direct_execution: false,
      automatic_owner_approval: false, fail_closed_on_missing_relay_or_auth: true,
      new_backend: false, new_mobile_runtime: false, authority_by_device: false,
      transfer_full_corpus_on_open: false, drive_write_grants_execution: false },
  };
}

export const MAX_MOBILE_CARRIER_BYTES = 65536;

export function parseMobileCarrier(text: string, filename: string): MobileLinkManifest {
  if (!filename.toLowerCase().endsWith(".cgx")) throw new TypeError("Choose a .cgx carrier");
  if (new TextEncoder().encode(text).byteLength > MAX_MOBILE_CARRIER_BYTES) throw new TypeError("CGX carrier exceeds 64 KiB");
  return readMobileManifest(JSON.parse(text));
}

export function saveMobileConnection(storage: Pick<Storage, "setItem" | "removeItem">, input: string, hostname: string): string {
  const origin = resolveMobileRelayOrigin(input, hostname);
  storage.setItem(MOBILE_LINK_ORIGIN_KEY, origin);
  storage.removeItem(MOBILE_LINK_DISCONNECTED_KEY);
  return origin;
}

export function disconnectMobileConnection(storage: Pick<Storage, "setItem" | "removeItem">): void {
  // Disable first, so a partial storage failure cannot resume a compiled route.
  storage.setItem(MOBILE_LINK_DISCONNECTED_KEY, "true");
  storage.removeItem(MOBILE_LINK_ORIGIN_KEY);
}

export function resolveMobileRelayOrigin(input: string, pageHostname: string): string {
  if (!input.trim()) throw new TypeError("Enter the owner-controlled HTTPS relay origin");
  const origin = resolveDesktopOrigin(input);
  const localPage = ["localhost", "127.0.0.1", "::1", "[::1]"].includes(pageHostname.toLowerCase());
  const relayHost = new URL(origin).hostname.toLowerCase();
  if (!localPage && (!origin.startsWith("https://") ||
      isLoopbackOriginHost(relayHost))) {
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
