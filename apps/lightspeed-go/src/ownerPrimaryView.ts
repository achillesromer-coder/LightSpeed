/**
 * UniSpace owner-only primary-view selector (SOURCE REVIEW ONLY).
 * Consumes the existing CGX view_selection_policy and semantic lens registry
 * as injected, reviewed inputs. It neither imports private catalogues into Vite
 * nor fetches/admits objects, verifies host authority or dispatches commands.
 * Client-supplied flags and allowlists are NOT security credentials.
 */
import { projectOwnerProgress, type OwnerProgressEnvelope } from "./ownerProgressProjection";

export interface OwnerViewSelectionInput {
  envelope: OwnerProgressEnvelope | null | undefined;
  task: string;
  requested_view?: string;
  permitted_view_ids: string[];
  policy: {
    task_mapping: Record<string, string[]>;
    hybridisation_policy: { max_primary_views: number; secondary_panels_on_demand: boolean };
  };
  registry: { shared_view_families: Array<{ id: string }> };
  geometry?: { source_qualified?: boolean; frame_verified?: boolean; units_verified?: boolean };
  spatial?: { crs_verified?: boolean; datum_verified?: boolean };
  temporal?: { scale_verified?: boolean; valid_at_verified?: boolean; recorded_at_verified?: boolean };
  device?: "desktop" | "phone" | "offline";
  inspector_open?: boolean;
  /** Trusted local verifier output only; client flags do not constitute a signed grant. */
  offline_cache?: {
    object_id?: string;
    filespace?: string;
    source_revision?: string;
    integrity_verified?: boolean;
    offline_grant_verified?: boolean;
    offline_grant_unexpired?: boolean;
    source_rights_verified?: boolean;
  };
}

export function selectOwnerPrimaryView(input: OwnerViewSelectionInput) {
  const projection = projectOwnerProgress(input.envelope);
  const held = {
    state: "HOLD_PRIVATE_SCOPE",
    object_id: null as string | null,
    source_revision: null as string | null,
    filespace: null as string | null,
    primary_view: null as string | null,
    secondary_views: [] as string[],
    frontier: [] as string[],
    hydration: "H0_H2_METADATA_ONLY",
    evidence: "NO_PRIVATE_R3",
    native_admitted: false,
    live_verified: false,
    dispatch_authorized: false,
    public_publish_authorized: false,
  };
  if (projection.access !== "PRIVATE_SOURCE_REVIEW") {
    return { ...held, state: projection.access };
  }
  const scoped = {
    ...held,
    object_id: projection.object_id,
    source_revision: projection.source_revision,
    filespace: projection.filespace,
    evidence: "SOURCE_ONLY_UNADMITTED",
  };
  // Offline is not a cached copy of the last online session. Require an exact
  // source/revision/child binding plus trusted cache, grant and rights checks.
  // These are injected review assertions, NOT browser-side cryptographic proof.
  // No matching proof => withhold even the private source selector (#158).
  if (input.device === "offline") {
    const cache = input.offline_cache;
    if (cache?.object_id !== projection.object_id ||
        cache?.filespace !== projection.filespace ||
        cache?.source_revision !== projection.source_revision ||
        cache?.integrity_verified !== true ||
        cache?.offline_grant_verified !== true ||
        cache?.offline_grant_unexpired !== true ||
        cache?.source_rights_verified !== true) {
      return { ...held, state: "HOLD_OFFLINE_CACHE" };
    }
  }
  // The source contracts require exactly one primary view. A changed/invalid
  // policy is held rather than silently creating another UI or semantic master.
  if (input.policy?.hybridisation_policy?.max_primary_views !== 1 ||
      !input.policy?.task_mapping || !Array.isArray(input.registry?.shared_view_families) ||
      !Array.isArray(input.permitted_view_ids)) {
    return { ...scoped, state: "HOLD_VIEW_POLICY" };
  }
  const registered = new Set(input.registry.shared_view_families.map(view => view.id));
  const permitted = new Set(input.permitted_view_ids);
  const taskViews = input.policy.task_mapping[input.task];
  if (!Array.isArray(taskViews)) return { ...scoped, state: "HOLD_VIEW_POLICY" };
  const frontier: string[] = [];
  const offline = input.device === "offline";
  const qualifies = (view: string): boolean => {
    if (!registered.has(view) || !permitted.has(view)) return false;
    if (offline && view !== "filespace-tree" && view !== "active-object-inspector") {
      frontier.push("OFFLINE_VIEW_NOT_CACHED");
      return false;
    }
    if (view === "twin-3d" &&
        !(input.geometry?.source_qualified === true &&
          input.geometry.frame_verified === true && input.geometry.units_verified === true)) {
      frontier.push("GEOMETRY_FRAME_UNVERIFIED");
      return false;
    }
    if (view === "map-spatial" &&
        !(input.spatial?.crs_verified === true && input.spatial.datum_verified === true &&
          input.geometry?.units_verified === true)) {
      frontier.push("SPATIAL_CRS_UNVERIFIED");
      return false;
    }
    if (view === "timeline-dbr" &&
        !(input.temporal?.scale_verified === true && input.temporal.valid_at_verified === true &&
          input.temporal.recorded_at_verified === true)) {
      frontier.push("TEMPORAL_FRAME_UNVERIFIED");
      return false;
    }
    return true;
  };
  // A user override can choose only a task-relevant, registered and permitted
  // view. Security/evidence and task outrank device and presentation preference.
  const ordered = input.requested_view && taskViews.includes(input.requested_view)
    ? [input.requested_view, ...taskViews.filter(view => view !== input.requested_view)]
    : taskViews;
  let primary: string | null = null;
  for (const view of ordered) {
    if (qualifies(view)) { primary = view; break; }
  }
  if (!primary) return {
    ...scoped, state: "HOLD_NO_QUALIFIED_VIEW",
    frontier: [...new Set(frontier)],
  };
  const inspector = input.inspector_open === true &&
    input.policy.hybridisation_policy.secondary_panels_on_demand === true &&
    primary !== "active-object-inspector" && registered.has("active-object-inspector") &&
    permitted.has("active-object-inspector");
  return {
    ...scoped,
    state: "SOURCE_ONLY_VIEW_CANDIDATE",
    primary_view: primary,
    secondary_views: inspector ? ["active-object-inspector"] : [],
    frontier: [...new Set(frontier)],
    hydration: offline ? "H0_H2_CACHED_METADATA_ONLY" : "H0_H2_METADATA_ONLY",
  };
}
