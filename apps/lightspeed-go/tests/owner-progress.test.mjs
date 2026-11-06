import { test } from "vitest";
import { readFileSync } from "node:fs";
import { selectOwnerPrimaryView } from "../src/ownerPrimaryView.ts";
import assert from "node:assert/strict";
import { projectOwnerProgress } from "../src/ownerProgressProjection.ts";

const full = () => ({
  gateway: { session_verified:true, host_handshake_verified:true, root_acl_verified:true, object_acl_verified:true, source_rights_verified:true },
  source: { object_id:"Cognigrex.cgx:/FileSpace/qualified-candidate-1", filespace:"Cognigrex.cgx/FileSpace", revision:"a".repeat(64) },
  bridge: { reachable:true },
  consumer: { heartbeat_fresh:false, pid_identity_verified:false, lock_verified:false, lease_verified:false, dispatch_ready:false },
  checkpoint: { object_id:"Cognigrex.cgx:/FileSpace/qualified-candidate-1", filespace:"Cognigrex.cgx/FileSpace", source_revision:"a".repeat(64), reported_completed:3200, independently_verified_committed:3200, database_integrity_verified:false },
  latest: { object_id:"Cognigrex.cgx:/FileSpace/qualified-candidate-1", filespace:"Cognigrex.cgx/FileSpace", source_revision:"a".repeat(64), state:"FAIL_CLOSED", completed:0, target:0, observed_attempted:3216, error:"sqlite3.OperationalError: database is locked" },
});

test("no session/ACL/handshake yields no private metadata", () => {
  for (const key of Object.keys(full().gateway)) {
    const x=full(); x.gateway[key]=false;
    const view=projectOwnerProgress(x);
    assert.equal(view.access,"HOLD_PRIVATE_SCOPE");
    assert.equal(view.progress,null);
    assert.equal(view.object_id,null);
  }
  assert.equal(projectOwnerProgress(null).access,"HOLD_PRIVATE_SCOPE");
});

test("failed latest run zero does not erase reported checkpoint", () => {
  const v=projectOwnerProgress(full());
  assert.equal(v.access,"PRIVATE_SOURCE_REVIEW");
  assert.equal(v.bridge,"BRIDGE_REACHABLE");
  assert.equal(v.consumer,"CONSUMER_HELD");
  assert.equal(v.progress.latest_state,"FAIL_CLOSED");
  assert.equal(v.progress.latest_completed,0);
  assert.equal(v.progress.latest_target,0);
  assert.equal(v.progress.reported_checkpoint,3200);
  assert.equal(v.progress.independently_verified_committed,null);
  assert.equal(v.progress.observed_attempted,3216);
  assert.equal(v.progress.error_class,"SQLITE_DATABASE_LOCKED");
  assert.equal(v.native_admitted,false);
  assert.equal(v.dispatch_authorized,false);
});

test("verified DB integrity alone does not grant execution or native admission", () => {
  const x=full(); x.checkpoint.database_integrity_verified=true;
  const v=projectOwnerProgress(x);
  assert.equal(v.progress.independently_verified_committed,3200);
  assert.equal(v.dispatch_authorized,false);
  assert.equal(v.native_admitted,false);
});

test("bridge reachability cannot override stale PID/lease", () => {
  const x=full(); x.consumer.dispatch_ready=true;
  assert.equal(projectOwnerProgress(x).consumer,"CONSUMER_HELD");
  x.consumer.heartbeat_fresh=true;
  x.consumer.pid_identity_verified=true;
  x.consumer.lock_verified=true;
  x.consumer.lease_verified=true;
  const v=projectOwnerProgress(x);
  assert.equal(v.consumer,"CONSUMER_READY_CLAIM_NOT_AUTHORITY");
  assert.equal(v.dispatch_authorized,false);
});

test("wrong child FileSpace, missing ID or revision fails source identity", () => {
  for (const source of [
    {...full().source, filespace:"Eco.cgx/FileSpace"},
    {...full().source, object_id:"Eco.cgx:/FileSpace/foreign-object"},
    {...full().source, object_id:null},
    {...full().source, revision:"unsigned"},
  ]) {
    const x=full(); x.source=source;
    const v=projectOwnerProgress(x);
    assert.equal(v.access,"HOLD_SOURCE_IDENTITY");
    assert.equal(v.object_id,null);
    assert.equal(v.progress,null);
    assert.equal(v.bridge,"BRIDGE_WITHHELD");
    assert.equal(v.consumer,"CONSUMER_HELD");
    assert.equal(v.source_revision,null);
  }
});

test("private R3 selector accepts only exact Git SHA-1 or SHA-256 digest lengths", () => {
  for (const length of [0, 1, 39, 41, 42, 63, 65]) {
    const x=full(); x.source.revision="a".repeat(length);
    x.checkpoint.source_revision=x.source.revision;
    x.latest.source_revision=x.source.revision;
    const v=projectOwnerProgress(x);
    assert.equal(v.access,"HOLD_SOURCE_IDENTITY",String(length));
    assert.equal(v.object_id,null);
    assert.equal(v.progress,null);
    assert.equal(v.bridge,"BRIDGE_WITHHELD");
  }
  for (const length of [40, 64]) {
    const x=full(); x.source.revision="a".repeat(length);
    x.checkpoint.source_revision=x.source.revision;
    x.latest.source_revision=x.source.revision;
    const v=projectOwnerProgress(x);
    assert.equal(v.access,"PRIVATE_SOURCE_REVIEW",String(length));
    assert.equal(v.progress_binding,"SOURCE_BOUND");
    assert.equal(v.native_admitted,false);
    assert.equal(v.dispatch_authorized,false);
  }
});

test("private paths, tokens, raw prompts and arbitrary error text never project", () => {
  const x=full();
  x.private_path="C:\\Secret\\source.json";
  x.session_token="token-123";
  x.raw_prompts=["private text"];
  x.latest.error="C:\\Secret\\source.json token-123 internal error";
  const rendered=JSON.stringify(projectOwnerProgress(x));
  for (const secret of ["Secret","source.json","token-123","private text"]) assert.ok(!rendered.includes(secret));
  assert.ok(rendered.includes("REDACTED_FAILURE"));
});

test("malformed counts never masquerade as verified progress", () => {
  const x=full(); x.checkpoint.reported_completed=-1;
  x.checkpoint.independently_verified_committed=Number.NaN;
  x.checkpoint.database_integrity_verified=true;
  x.latest.observed_attempted=Infinity;
  const v=projectOwnerProgress(x);
  assert.equal(v.progress.reported_checkpoint,null);
  assert.equal(v.progress.independently_verified_committed,null);
  assert.equal(v.progress.observed_attempted,null);
});

test("Object_ID selector rejects traversal, ambiguous and empty path segments (#158)", () => {
  const rejected = [
    "Cognigrex.cgx:/FileSpace/../Eco.cgx/secret",
    "Cognigrex.cgx:/FileSpace/./qualified-candidate-1",
    "Cognigrex.cgx:/FileSpace/qualified-candidate-1/..",
    "Cognigrex.cgx:/FileSpace//qualified-candidate-1",
    "Cognigrex.cgx:/FileSpace/qualified-candidate-1/",
    "Cognigrex.cgx:/FileSpace/qualified-candidate-1:other",
    "Cognigrex.cgx:/FileSpace/__proto__/secret",
    "Cognigrex.cgx:/FileSpace/constructor",
    "Cognigrex.cgx:/FileSpace/PROTOTYPE",
    "Cognigrex.cgx:/FileSpace/",
    "Cognigrex.cgx:/FileSpace/" + "x".repeat(161),
  ];
  for (const object_id of rejected) {
    const x=full(); x.source.object_id=object_id;
    const view=projectOwnerProgress(x);
    assert.equal(view.access,"HOLD_SOURCE_IDENTITY",object_id);
    assert.equal(view.object_id,null);
    assert.equal(view.progress,null);
    assert.equal(view.bridge,"BRIDGE_WITHHELD");
  }
  const nested=full();
  nested.source.object_id="Cognigrex.cgx:/FileSpace/owner-reviewed/qualified-candidate-1";
  const view=projectOwnerProgress(nested);
  assert.equal(view.access,"PRIVATE_SOURCE_REVIEW");
  assert.equal(view.object_id,nested.source.object_id);
  assert.equal(view.native_admitted,false);
  assert.equal(view.dispatch_authorized,false);
});


test("progress is withheld if either receipt belongs to another Object_ID, child or revision", () => {
  const cases = [
    ["checkpoint", "object_id", "Cognigrex.cgx:/FileSpace/other-source"],
    ["latest", "object_id", "Cognigrex.cgx:/FileSpace/other-source"],
    ["checkpoint", "filespace", "Eco.cgx/FileSpace"],
    ["latest", "filespace", "Eco.cgx/FileSpace"],
    ["checkpoint", "source_revision", "b".repeat(64)],
    ["latest", "source_revision", "b".repeat(64)],
    ["checkpoint", "source_revision", undefined],
    ["latest", "object_id", undefined],
  ];
  for (const [part, key, value] of cases) {
    const x = full(); x[part][key] = value;
    const v = projectOwnerProgress(x);
    assert.equal(v.access, "PRIVATE_SOURCE_REVIEW");
    assert.equal(v.progress_binding, "HOLD_UNBOUND_PROGRESS");
    assert.equal(v.progress, null);
    assert.equal(v.native_admitted, false);
    assert.equal(v.dispatch_authorized, false);
  }
  const v = projectOwnerProgress(full());
  assert.equal(v.progress_binding, "SOURCE_BOUND");
  assert.equal(v.progress.reported_checkpoint, 3200);
});


test("offline or missing bridge holds consumer-ready claim despite reported consumer flags (#158)", () => {
  const x=full();
  x.consumer={heartbeat_fresh:true,pid_identity_verified:true,lock_verified:true,lease_verified:true,dispatch_ready:true};
  x.bridge.reachable=false;
  let view=projectOwnerProgress(x);
  assert.equal(view.bridge,"BRIDGE_OFFLINE");
  assert.equal(view.consumer,"CONSUMER_HELD");
  assert.equal(view.dispatch_authorized,false);
  delete x.bridge;
  view=projectOwnerProgress(x);
  assert.equal(view.consumer,"CONSUMER_HELD");
  x.bridge={reachable:true};
  view=projectOwnerProgress(x);
  assert.equal(view.consumer,"CONSUMER_READY_CLAIM_NOT_AUTHORITY");
  assert.equal(view.dispatch_authorized,false);
});

const currentPolicy = JSON.parse(readFileSync(new URL("../../../cgx/domain_templates/view_selection_policy.json", import.meta.url), "utf8"));
const currentLenses = JSON.parse(readFileSync(new URL("../../../cgx/domain_templates/semantic_view_lens_registry.json", import.meta.url), "utf8"));
const sourceBound = (x) => ({
  object_id:x.envelope.source.object_id,
  filespace:x.envelope.source.filespace,
  source_revision:x.envelope.source.revision,
  rights_verified:true,
});
const lensInput = (task="browse") => ({
  envelope:full(), task, policy:currentPolicy, registry:currentLenses,
  permitted_view_ids:currentLenses.shared_view_families.map(x=>x.id),
  device:"desktop", inspector_open:false,
});

test("single primary owner lens follows existing source registry and preserves exact source (#158)", () => {
  const x=lensInput("browse");
  const v=selectOwnerPrimaryView(x);
  assert.equal(v.state,"SOURCE_ONLY_VIEW_CANDIDATE");
  assert.equal(v.primary_view,"filespace-tree");
  assert.deepEqual(v.secondary_views,[]);
  assert.equal(v.object_id,x.envelope.source.object_id);
  assert.equal(v.source_revision,x.envelope.source.revision);
  assert.equal(v.filespace,"Cognigrex.cgx/FileSpace");
  assert.equal(v.evidence,"SOURCE_ONLY_UNADMITTED");
  assert.equal(v.native_admitted,false);
  assert.equal(v.live_verified,false);
  assert.equal(v.dispatch_authorized,false);
  assert.equal(v.public_publish_authorized,false);
  x.inspector_open=true;
  assert.deepEqual(selectOwnerPrimaryView(x).secondary_views,["active-object-inspector"]);
});

test("owner lens denies unverified gateway and cross-child identity without projection", () => {
  const x=lensInput();
  x.envelope.gateway.session_verified=false;
  let v=selectOwnerPrimaryView(x);
  assert.equal(v.state,"HOLD_PRIVATE_SCOPE");
  assert.equal(v.object_id,null);
  assert.equal(v.primary_view,null);
  x.envelope=full();
  x.envelope.source.filespace="Eco.cgx/FileSpace";
  v=selectOwnerPrimaryView(x);
  assert.equal(v.state,"HOLD_SOURCE_IDENTITY");
  assert.equal(v.object_id,null);
});

test("requested 3D view shows Frontier until source, frame and units qualify (#209)", () => {
  const x=lensInput("engineer");
  x.requested_view="twin-3d";
  let v=selectOwnerPrimaryView(x);
  assert.equal(v.primary_view,"active-object-inspector");
  assert.ok(v.frontier.includes("GEOMETRY_FRAME_UNVERIFIED"));
  x.geometry={...sourceBound(x),source_qualified:true,frame_verified:true,units_verified:true};
  v=selectOwnerPrimaryView(x);
  assert.equal(v.primary_view,"twin-3d");
  assert.equal(v.state,"SOURCE_ONLY_VIEW_CANDIDATE");
  assert.equal(v.live_verified,false);
  assert.equal(v.native_admitted,false);
});

test("spatial and time-bearing views cannot invent CRS, datum or temporal frame", () => {
  const eco=lensInput("ecology");
  eco.requested_view="map-spatial";
  eco.geometry={...sourceBound(eco),units_verified:true};
  let v=selectOwnerPrimaryView(eco);
  assert.equal(v.primary_view,"active-object-inspector");
  assert.ok(v.frontier.includes("SPATIAL_CRS_UNVERIFIED"));
  eco.spatial={...sourceBound(eco),crs_verified:true,datum_verified:true};
  assert.equal(selectOwnerPrimaryView(eco).primary_view,"map-spatial");
  const audit=lensInput("audit");
  audit.requested_view="timeline-dbr";
  v=selectOwnerPrimaryView(audit);
  assert.notEqual(v.primary_view,"timeline-dbr");
  assert.ok(v.frontier.includes("TEMPORAL_FRAME_UNVERIFIED"));
});

test("metric, spatial and temporal views reject foreign source, revision, child or rights (#158/#209)", () => {
  const engineer=lensInput("engineer");
  engineer.requested_view="twin-3d";
  engineer.geometry={...sourceBound(engineer),source_qualified:true,frame_verified:true,units_verified:true};
  assert.equal(selectOwnerPrimaryView(engineer).primary_view,"twin-3d");
  for (const mutation of [
    {object_id:"Cognigrex.cgx:/FileSpace/foreign"},
    {filespace:"Eco.cgx/FileSpace"},
    {source_revision:"b".repeat(64)},
    {rights_verified:false},
  ]) {
    engineer.geometry={...sourceBound(engineer),...mutation,source_qualified:true,frame_verified:true,units_verified:true};
    const v=selectOwnerPrimaryView(engineer);
    assert.notEqual(v.primary_view,"twin-3d");
    assert.ok(v.frontier.includes("GEOMETRY_FRAME_UNVERIFIED"));
    assert.equal(v.native_admitted,false);
  }
  const eco=lensInput("ecology");
  eco.requested_view="map-spatial";
  eco.geometry={...sourceBound(eco),units_verified:true};
  eco.spatial={...sourceBound(eco),crs_verified:true,datum_verified:true};
  assert.equal(selectOwnerPrimaryView(eco).primary_view,"map-spatial");
  eco.spatial={...eco.spatial,source_revision:"b".repeat(64)};
  assert.notEqual(selectOwnerPrimaryView(eco).primary_view,"map-spatial");
  eco.spatial={...sourceBound(eco),crs_verified:true,datum_verified:true};
  eco.geometry={...eco.geometry,filespace:"Romer.cgx/FileSpace"};
  assert.notEqual(selectOwnerPrimaryView(eco).primary_view,"map-spatial");
  const audit=lensInput("audit");
  audit.requested_view="timeline-dbr";
  audit.temporal={...sourceBound(audit),scale_verified:true,valid_at_verified:true,recorded_at_verified:true};
  assert.equal(selectOwnerPrimaryView(audit).primary_view,"timeline-dbr");
  audit.temporal={...audit.temporal,object_id:"Cognigrex.cgx:/FileSpace/foreign"};
  const v=selectOwnerPrimaryView(audit);
  assert.notEqual(v.primary_view,"timeline-dbr");
  assert.ok(v.frontier.includes("TEMPORAL_FRAME_UNVERIFIED"));
});

test("offline lens has one metadata-only fallback, no live runtime claim", () => {
  const x=lensInput("runtime");
  x.device="offline";
  x.offline_cache={
    object_id:x.envelope.source.object_id,
    filespace:x.envelope.source.filespace,
    source_revision:x.envelope.source.revision,
    integrity_verified:true,
    offline_grant_verified:true,
    offline_grant_unexpired:true,
    source_rights_verified:true,
  };
  x.requested_view="network-runtime";
  const v=selectOwnerPrimaryView(x);
  assert.equal(v.primary_view,"active-object-inspector");
  assert.equal(v.hydration,"H0_H2_CACHED_METADATA_ONLY");
  assert.ok(v.frontier.includes("OFFLINE_VIEW_NOT_CACHED"));
  assert.equal(v.dispatch_authorized,false);
});

test("policy drift and empty host view allowance hold rather than manufacture a UI", () => {
  const x=lensInput();
  x.policy={...currentPolicy,hybridisation_policy:{...currentPolicy.hybridisation_policy,max_primary_views:2}};
  assert.equal(selectOwnerPrimaryView(x).state,"HOLD_VIEW_POLICY");
  x.policy=currentPolicy;
  x.permitted_view_ids=[];
  const v=selectOwnerPrimaryView(x);
  assert.equal(v.state,"HOLD_NO_QUALIFIED_VIEW");
  assert.equal(v.primary_view,null);
});

test("v0.6 topology graph holds without exact R2 source, typed edges and rights (#158)", () => {
  const x=lensInput("browse");
  x.requested_view="topology-graph";
  let v=selectOwnerPrimaryView(x);
  assert.equal(v.primary_view,"filespace-tree");
  assert.ok(v.frontier.includes("GRAPH_TOPOLOGY_UNVERIFIED"));
  const bound={
    object_id:x.envelope.source.object_id,
    filespace:x.envelope.source.filespace,
    source_revision:x.envelope.source.revision,
    topology_source_verified:true,
    typed_edges_verified:true,
    rights_verified:true,
  };
  for (const mutation of [
    {object_id:"Cognigrex.cgx:/FileSpace/foreign"},
    {filespace:"Eco.cgx/FileSpace"},
    {source_revision:"b".repeat(64)},
    {topology_source_verified:false},
    {typed_edges_verified:false},
    {rights_verified:false},
  ]) {
    x.graph={...bound,...mutation};
    v=selectOwnerPrimaryView(x);
    assert.equal(v.primary_view,"filespace-tree",JSON.stringify(mutation));
    assert.ok(v.frontier.includes("GRAPH_TOPOLOGY_UNVERIFIED"));
    assert.equal(v.native_admitted,false);
    assert.equal(v.dispatch_authorized,false);
  }
  x.graph=bound;
  v=selectOwnerPrimaryView(x);
  assert.equal(v.primary_view,"topology-graph");
  assert.equal(v.object_id,bound.object_id);
  assert.equal(v.source_revision,bound.source_revision);
  assert.equal(v.filespace,bound.filespace);
  assert.equal(v.evidence,"SOURCE_ONLY_UNADMITTED");
  assert.equal(v.live_verified,false);
  assert.equal(v.public_publish_authorized,false);
});

test("offline FileSpace denies missing, expired, cross-object and cross-revision cache (#158)", () => {
  const baseline=lensInput("browse");
  baseline.device="offline";
  const denied=selectOwnerPrimaryView(baseline);
  assert.equal(denied.state,"HOLD_OFFLINE_CACHE");
  assert.equal(denied.object_id,null);
  assert.equal(denied.source_revision,null);
  assert.equal(denied.primary_view,null);
  assert.equal(denied.dispatch_authorized,false);
  const good={
    object_id:baseline.envelope.source.object_id,
    filespace:baseline.envelope.source.filespace,
    source_revision:baseline.envelope.source.revision,
    integrity_verified:true,offline_grant_verified:true,
    offline_grant_unexpired:true,source_rights_verified:true,
  };
  for (const mutation of [
    {object_id:"Cognigrex.cgx:/FileSpace/other"},
    {filespace:"Eco.cgx/FileSpace"},
    {source_revision:"b".repeat(64)},
    {integrity_verified:false},
    {offline_grant_verified:false},
    {offline_grant_unexpired:false},
    {source_rights_verified:false},
  ]) {
    const x=lensInput("browse"); x.device="offline";
    x.offline_cache={...good,...mutation};
    const v=selectOwnerPrimaryView(x);
    assert.equal(v.state,"HOLD_OFFLINE_CACHE",JSON.stringify(mutation));
    assert.equal(v.object_id,null);
    assert.equal(v.primary_view,null);
    assert.equal(v.live_verified,false);
    assert.equal(v.public_publish_authorized,false);
  }
  baseline.offline_cache=good;
  const permitted=selectOwnerPrimaryView(baseline);
  assert.equal(permitted.state,"SOURCE_ONLY_VIEW_CANDIDATE");
  assert.equal(permitted.primary_view,"filespace-tree");
  assert.equal(permitted.hydration,"H0_H2_CACHED_METADATA_ONLY");
  assert.equal(permitted.native_admitted,false);
  assert.equal(permitted.dispatch_authorized,false);
});

test("malformed provider lens/policy input holds without an exception or private view (#158)", () => {
  const cases = [
    {registry:{shared_view_families:[null]}},
    {registry:{shared_view_families:[{id:null}]}},
    {registry:{shared_view_families:[{id:"filespace-tree"}, undefined]}},
    {permitted_view_ids:[null]},
    {policy:{...currentPolicy,task_mapping:[]}},
    {policy:{...currentPolicy,task_mapping:{...currentPolicy.task_mapping,browse:["filespace-tree",null]}}},
  ];
  for (const mutation of cases) {
    const x=lensInput("browse");
    Object.assign(x,mutation);
    const v=selectOwnerPrimaryView(x);
    assert.equal(v.state,"HOLD_VIEW_POLICY",JSON.stringify(mutation));
    assert.equal(v.primary_view,null);
    assert.deepEqual(v.secondary_views,[]);
    assert.equal(v.native_admitted,false);
    assert.equal(v.dispatch_authorized,false);
    assert.equal(v.public_publish_authorized,false);
  }
});
