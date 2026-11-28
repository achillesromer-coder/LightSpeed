/**
 * Fail-closed projection of the existing LS GO site integration manifest.
 * Treat fetched JSON as data, not a live source/head/owner-session proof.
 * Never grants publish, runtime, mint, network or native DBR authority.
 */
export const SITE_VIEW_SCHEMA = "CGX-LSGO-SITE-INTEGRATION-PRESENTATION/0.1";
const MAX_LABEL = 96;
const DEFAULT_AUTHORITY = Object.freeze([
  "Owner review", "Achilles / GO gate", "Existing LightSpeed runtime",
  "Git source review", "Drive provenance review",
]);
const RELEASE_FLAGS = Object.freeze([
  "owner_credential_ready", "private_relay_configured", "off_device_verified",
  "accepted_head_installed", "drive_successor_readback",
  "public_deployment_verified", "public_direct_execution",
]);
const object = (x: unknown): x is Record<string, unknown> =>
  x !== null && typeof x === "object" && !Array.isArray(x);
const safeLabel = (value: unknown): string | null => {
  if (typeof value !== "string" || value.length < 1 ||
      value.length > MAX_LABEL || /[\u0000-\u001f\u007f]/.test(value)) return null;
  const valueTrimmed = value.trim();
  return valueTrimmed ? valueTrimmed : null;
};

export const escapeSiteLabel = (value: string): string =>
  value.replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;",
    '"': "&quot;", "'": "&#39;",
  }[character] ?? character));

export type SiteViewProjection = Readonly<{
  schema: typeof SITE_VIEW_SCHEMA;
  sourceStatus: string;
  launchStatus: string;
  authority: readonly string[];
  manifestEvidence: "REVIEW_SOURCE_ONLY" | "INVALID_SOURCE_HELD";
  nativeVerified: false;
  publicDeployed: false;
  dbrVerified: false;
}>;

export const projectSiteIntegration = (input: unknown): SiteViewProjection => {
  const valid = object(input)
    && input.schema_version === "lightspeed-go-sites-integration-v2"
    && input.site_name === "LightSpeed GO"
    && input.edit_mode === "existing-site-side-edit"
    && input.create_new_site === false
    && input.publish_state === "review_source_verified_deployment_held"
    && input.source_commit === null
    && object(input.release_gates)
    && RELEASE_FLAGS.every((key) => input.release_gates && object(input.release_gates)
      && input.release_gates[key] === false)
    && Array.isArray(input.authority_chain)
    && input.authority_chain.length >= 1
    && input.authority_chain.length <= 8
    && input.authority_chain.every((item) => safeLabel(item) !== null);
  const authority = valid
    ? Object.freeze((input.authority_chain as string[]).map((item) => safeLabel(item)!))
    : DEFAULT_AUTHORITY;
  return Object.freeze({
    schema: SITE_VIEW_SCHEMA,
    sourceStatus: valid
      ? "Source review only · exact current Git and Drive readback pending"
      : "Unqualified site manifest · source review required",
    launchStatus: "Public deployment, native acceptance and DBR proof held",
    authority,
    manifestEvidence: valid ? "REVIEW_SOURCE_ONLY" : "INVALID_SOURCE_HELD",
    nativeVerified: false,
    publicDeployed: false,
    dbrVerified: false,
  });
};
