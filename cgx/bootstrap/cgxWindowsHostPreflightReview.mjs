/**
 * CGX Windows host startup triage, SOURCE-REVIEW ONLY.
 * Interpret owner/provider-reported observations without reading files, running
 * PowerShell, changing execution policy, mounting sources or authorising CGX.
 * Existing native LightSpeed startup/RootAuthority owns all execution.
 */
export const WINDOWS_PREFLIGHT_SCHEMA = "CGX-WINDOWS-HOST-PREFLIGHT-REVIEW/0.1";
const POLICY_VALUES = new Set(["Undefined", "Restricted", "AllSigned", "RemoteSigned", "Unrestricted", "Bypass"]);
const SCOPE_ORDER = ["MachinePolicy", "UserPolicy", "Process", "CurrentUser", "LocalMachine"];
const STATES = new Set(["ONLINE", "OFFLINE", "UNKNOWN"]);
const ACCESS = new Set(["VERIFIED_READ_ONLY", "QUOTA_BLOCKED", "DENIED", "NOT_CHECKED"]);
const SIGNATURES = new Set(["VALID", "NOT_SIGNED", "INVALID", "UNKNOWN"]);
const ZONES = new Set(["INTERNET", "LOCAL", "UNKNOWN"]);
const ERRORS = new Set(["NONE", "UNSIGNED_SCRIPT", "PARSE_ERROR", "ARGUMENT_TYPES_DO_NOT_MATCH", "OTHER"]);
const cleanObject = value => value !== null && typeof value === "object" && !Array.isArray(value);

export function reviewWindowsCGXHost(observed = {}) {
  if (!cleanObject(observed)) return {schema: WINDOWS_PREFLIGHT_SCHEMA, state: "DENIED", reason: "INVALID_OBSERVATION"};
  const {
    connection = "UNKNOWN", fileAccess = "NOT_CHECKED", policies = {},
    signature = "UNKNOWN", zone = "UNKNOWN", startupError = "NONE", psVersion = "UNKNOWN"
  } = observed;
  if (!STATES.has(connection) || !ACCESS.has(fileAccess) || !cleanObject(policies) ||
      !SIGNATURES.has(signature) || !ZONES.has(zone) || !ERRORS.has(startupError) ||
      typeof psVersion !== "string" || psVersion.length > 40 || /[\u0000-\u001f]/.test(psVersion) ||
      Object.keys(policies).some(k => !SCOPE_ORDER.includes(k) || !POLICY_VALUES.has(policies[k]))) {
    return {schema: WINDOWS_PREFLIGHT_SCHEMA, state: "DENIED", reason: "INVALID_OBSERVATION"};
  }
  const effectiveScope = SCOPE_ORDER.find(k => policies[k] && policies[k] !== "Undefined") ?? null;
  const effectivePolicy = effectiveScope ? policies[effectiveScope] : "UNKNOWN";
  const holds = [];
  if (connection !== "ONLINE") holds.push("HOST_CONNECTION_UNVERIFIED");
  if (fileAccess === "QUOTA_BLOCKED") holds.push("PROVIDER_MONTHLY_QUOTA_HOLD_DO_NOT_RETRY");
  else if (fileAccess !== "VERIFIED_READ_ONLY") holds.push("HOST_FILESYSTEM_READBACK_UNVERIFIED");
  if (startupError === "UNSIGNED_SCRIPT" || (effectivePolicy === "AllSigned" && signature !== "VALID") ||
      (effectivePolicy === "RemoteSigned" && zone === "INTERNET" && signature !== "VALID")) {
    holds.push("SCRIPT_SIGNING_POLICY_HOLD");
  }
  if (startupError === "PARSE_ERROR") holds.push("POWERSHELL_SCRIPT_PARSE_HOLD");
  if (startupError === "ARGUMENT_TYPES_DO_NOT_MATCH") holds.push("WIZARD_RUNTIME_ARGUMENT_HOLD");
  if (startupError === "OTHER") holds.push("UNCLASSIFIED_STARTUP_FAILURE");
  if (effectivePolicy === "Restricted") holds.push("POWERSHELL_SCRIPT_EXECUTION_RESTRICTED");
  // An AllSigned/RemoteSigned/Bypass observation is diagnostic data, not execution permission.
  const noHostReadback = fileAccess !== "VERIFIED_READ_ONLY";
  const nextReadOnly = holds.includes("PROVIDER_MONTHLY_QUOTA_HOLD_DO_NOT_RETRY")
    ? "Wait for provider quota reset or receive owner-supplied redacted diagnostics; do not retry this provider."
    : holds.includes("SCRIPT_SIGNING_POLICY_HOLD")
      ? "Inspect Get-ExecutionPolicy -List and Get-AuthenticodeSignature; do not disable a managed signing policy."
      : holds.includes("WIZARD_RUNTIME_ARGUMENT_HOLD")
        ? "Inspect the wizard's stage-specific exception and stack; do not infer native CGX failure."
        : holds.includes("POWERSHELL_SCRIPT_PARSE_HOLD")
          ? "Inspect script encoding and parser error line without running or modifying the original."
          : noHostReadback ? "Obtain an authorised read-only host and source inventory." :
            "Review actual current RootAuthority, signed lease, DBR, ACL and runtime status separately.";
  return {
    schema: WINDOWS_PREFLIGHT_SCHEMA, state: holds.length ? "HOLD" : "REVIEW_ONLY",
    observed_connection: connection, observed_file_access: fileAccess,
    effective_policy: effectivePolicy, effective_policy_scope: effectiveScope,
    signature_observation: signature, zone_observation: zone,
    powershell_version_observation: psVersion,
    startup_error_class: startupError, holds: [...new Set(holds)],
    next_read_only_step: nextReadOnly,
    // This source-only review never proves an action, regardless of user-supplied flags.
    authority_verified: false, signed_lease_verified: false, dbr_verified: false,
    runtime_installed: false, native_source_ingested: false,
    may_execute: false, may_change_execution_policy: false, may_mutate_carrier: false,
    may_publish: false
  };
}
