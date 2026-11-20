// Source-only R3 projection gate. Not a host authorization substitute.
// Caller MUST supply a server-verified authorization decision; browser input is never trusted.
export function planR3Projection(request, decision) {
  const deny = (reason) => Object.freeze({ status: "DENY", reason, hydration: [], execute: false });
  if (!decision || decision.verified !== true || decision.issuerVerified !== true ||
      decision.sessionActive !== true || decision.revoked !== false ||
      decision.rootAclVerified !== true || decision.dbrVerified !== true ||
      decision.leaseActive !== true) return deny("AUTHORITY_UNVERIFIED");
  if (!request || typeof request.objectId !== "string" || !request.objectId ||
      typeof request.childFileSpace !== "string" || !request.childFileSpace ||
      request.objectId !== decision.objectId ||
      request.childFileSpace !== decision.childFileSpace) return deny("OBJECT_SCOPE_MISMATCH");
  if (decision.rightsQualified !== true || decision.sourceRevisionVerified !== true)
    return deny("SOURCE_UNQUALIFIED");
  const levels = Array.isArray(decision.allowedHydration) ? decision.allowedHydration : [];
  const hydration = ["H0", "H1", "H2", "H3"].filter(level => levels.includes(level));
  const view = request.view === "3d" && !(decision.geometryVerified && decision.frameVerified && decision.unitsVerified)
    ? "FRONTIER" : (["document", "graph", "matrix", "chat", "interactive", "3d"].includes(request.view) ? request.view : "document");
  // H4 is NEVER inferred from read scope or this presentation planner.
  return Object.freeze({ status: "SOURCE_ONLY_PLAN", objectId: decision.objectId,
    childFileSpace: decision.childFileSpace, view, hydration, execute: false,
    consumer: decision.bridgeReachable === true && decision.consumerReady !== true ? "CONSUMER_HELD" : "NOT_VERIFIED" });
}
