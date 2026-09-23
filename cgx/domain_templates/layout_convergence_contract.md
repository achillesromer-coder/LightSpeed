# CGX Layout Convergence / Hybridisation Contract — 2026-09-23

Status: review blueprint; source-architecture coordination only.

## Problem

The corpus contains several successful but differently shaped interaction models:
- workbook landing dashboards;
- LightSpeed Web Shell hybrid canonical cells;
- CGX S75 topology navigation;
- S85 filesets/views and sparse hydration;
- folder/file navigation;
- digital-twin/3D interfaces;
- ecological map/temporal/food-web views;
- chat/generative UI;
- publication/Web2 pages.

They should not be collapsed into one permanent UI. They should resolve to one semantic state through different lenses.

## Convergence rule

For every newly encountered layout, classify it into one of five dispositions:

1. **CANONICAL MECHANIC** — changes how identity, semantics, authority, evidence, DBR or security work. Requires schema/kernel review.
2. **SHARED VIEW** — reusable projection useful across multiple domains. Add to the common view registry.
3. **DOMAIN VIEW** — useful because of a domain ontology (e.g. Eco food web; Römer interface tree). Keep under that domain's lens registry.
4. **SURFACE ADAPTER** — desktop/web/mobile/chat/API/node rendering or interaction technique. Bind to existing view semantics.
5. **REPRESENTATION** — generated publication/export. Never promote to source authority.

## Hybridise when

Hybridise two layouts when they expose complementary dimensions of the same underlying objects without conflicting authority.

Examples:
- folder tree + topology graph;
- collapsed dashboard cell + expanded object inspector;
- 3D twin + BOM/interface/evidence side panels;
- Eco map + temporal observation series + trophic graph;
- runtime node graph + job/receipt inspector.

## Keep separate when

Keep layouts as alternate lenses when:
- audiences differ materially;
- security/admission differs;
- one view is spatial and another temporal;
- one is an operational control view and another is an audit/evidence view;
- mobile projection requires less hydration;
- domain semantics differ even when the source object overlaps.

## Reject / do not carry forward when

Reject a layout as a durable CGX view when it:
- duplicates semantic state;
- creates a second authority/master;
- requires last-source-wins;
- hides provenance/evidence state;
- conflates simulation with physical evidence;
- stores transient Host-local state as canonical merely for display;
- is a one-off page whose function is already expressible as a reusable lens/cell/view;
- cannot identify its owning object/source/root.

## Hurdle resolution sequence

When a co-running lane encounters a layout/interaction hurdle:

1. identify the user task and semantic object(s);
2. identify current canonical owner/source;
3. determine whether the hurdle is semantic, view, surface, capability, provider or representation;
4. inspect existing view registry and domain-specific views;
5. reuse an existing view if adequate;
6. hybridise complementary views if one view cannot expose all required dimensions;
7. create a new reusable view only if the task recurs or exposes a genuinely missing semantic projection;
8. record the decision and rationale;
9. never restructure source authority solely to satisfy presentation;
10. if classification is uncertain, create a Frontier rather than force-fit.

## Default host composition

Desktop/workstation:
- left: filespace/tree + saved lenses;
- centre: active view (dashboard, graph, map, twin, evidence, etc.);
- right: active-object inspector;
- bottom/drawer: intake/work queue, history/DBR, command/chat.

Mobile:
- projection-lite current card/cell;
- swipe/tab between current view, inspector, evidence and work;
- expand/hydrate on demand.

Web/public:
- bounded lens with explicit evidence ceiling and no protected mutation unless a permitted Host session is present.

## Canonical-cell integration

The existing `49_Hybrid_Canonical_Cell_Map` is retained as an excellent dashboard composition pattern, not as the universal storage schema.

A cell is a reusable view binding:
`semantic objects + lens + evidence gate + interaction + next action`.

This is why it can compose Mission Control without duplicating technical data.

## Co-running coordination

ACR3 remains the cross-lane coordination/provenance surface until retirement gates close.
PR52 is the review/source implementation surface for the new Cognigrex child-shell/view contracts.
Legacy workbooks and Web Shell Builder remain source/provenance inputs, not additional masters.

Every co-running lane should:
- consume the newest ACR3 handoff rows before changing structure;
- write new architecture/layout decisions back to ACR3 or the successor CGX coordination object;
- preserve the source ID and intended disposition;
- avoid creating a new workbook/page/filespace merely because a view is missing.
