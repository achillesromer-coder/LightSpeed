# UniSpace · Immersive-first CGX spatial operating interface
**Review design/implementation contract · 23 November 2026 · no native/public release**

## Outcome and compatibility
A **single** root \`cgx:root:cognigrex\` generates a reversible, addressable user-facing interface from the existing Interface Studio \`cgx.unispace.interface/1\` and additional **spatial presentation** schema \`cgx.spatial.homebase/1\`. It does **not** create a second FileSpace, agent, OS, signing service, runtime, personal database or game engine. The existing UniSpace/LightSpeed GO frontend, project files, local Desktop API at port 8765 and Achilles local supervisor at port 8772 retain their own authority.

The spatial GUI is placed **above the existing workspace tabs**, not a separate web application. Its cards, rooms and relation paths delegate through existing workspace navigation callbacks. Users can enter a Grex or game-world "room" from a personal home base, move objects on a two-dimensional map, inspect their links, customise a room's presentation theme and return via breadcrumbs without copying data into the presentation. Existing pages, files and source objects are not replaced.

## Presentation modes
| Mode | Concrete tested/editable behaviour | Boundary |
|---|---|---|
| AR-first HUD | Spatial buttons/cards/relationship lines layered over responsive 2D stage; optional camera behind HUD after **explicit** browser user gesture | Camera permission, secure context and local browser required; **no world-tracking, calibration, SLAM, face identity, image upload, recording or WebXR immersive session** |
| 2D plan | Top-down grid layout, drag + arrow-key movement, numeric resize, same-layer collision/overlap checks, cross-room relation editing | Geometry is for interface placement, not Raphael verified 3D meshes or physical printers |
| OS deck | Spatially arranged operational workspace windows and overlays; direct existing FileSpace, DataSpace, SocialSpace, PrintSpace, IntelligenceSpace/ProfileSpace callbacks | Host privileges not transferred to the GUI |
| VR-style stage | Immersive visual depth and gateway layout on a normal screen | **Not** a stereoscopic headset session or runtime game engine; add WebXR only after hardware, HTTPS, safety and identity gates |

These modes use **one** data model, so switching preserves placement and selection (except explicitly stopped camera). Device camera tracks stop on page hidden, page exit, mode change and manual user cancellation. Host workspace navigation never requires camera permission.

## Local spatial model
- Grid: 20 × 14 logical cells per room; bounded dimensions and object counts.
- Graph: rooms form a single acyclic anchored tree; related/depends-on/gateway links form a **nonlinear** second overlay. Neither grants data read privileges.
- Layers: \`ground\` disallows overlap within a room, \`overlay\` permits deliberate visual overlap with ground but not same-layer collision. All coordinates are independently validated.
- Nodes: \`facet\`, \`grex\`, \`game\`, \`profile\`, \`object\`. Nested Grex/game nodes open a child room with its own appearance; other components open only their already-bound UniSpace workspace.
- Microclimate: \`theme\` (neutral/forest/industrial/cosmos/arcade) and \`light\` (day/dusk/night), all labelled \`VISUAL_PRESET_ONLY\`. Climate is not simulated weather, physics, temperature or environmental measurement. Future verified data is a separate signed/permissioned source facet.
- Seeded user-visible rooms: home, Eco, Römer, game gateways, **De Sporte persistence**, Raphael, Achilles and Neo. These are source-qualified **interface rooms**, not verified independent running services. De Sporte shows persistence/recovery *review entry points* in existing sources/activity screens; its actual sidecar and rights remain separately controlled. Achilles retains the existing local 8772 page, with the Desktop API still on 8765.
- Links have source-qualified IDs or no source reference. No private payload, engine state, model weights or asset library are copied into the layout.

## Functional control, versioning and safety
- Local drag and keyboard movement, numeric x/y/w/h, template Grex/game/profile/object creation, nested room entry, breadcrumb backtracking, graph-edge creation and room-theme editing all execute browser-side with strict schema validation.
- Undo/redo holds up to 40 local versions; **Save local** is an opt-in browser storage draft, not native canonical storage. **Export .cgx layout** generates standalone JSON; **Import layout** rejects unbounded/malformed/privilege-bearing content and validates namespace, type and collision invariants; the layout is independently reconstructable.
- Existing FileSpace/DataSpace/Neo workspaces open through the exact current \`onOpenWorkspace\` callback; there are no copied agent start/stop, Desktop API, signer, wallet, mint, SQL, peer or print actions. A successful button is never represented as an authenticated native transaction.
- Persistent-looking HUD is a front-end component; true FileSpace/DataSpace persistence, De Sporte native DBR, lease, ACL, resurrection/cold restart and multi-node verification still require original host-side signed receipts (#161). Public/private static negative access testing remains #158.
- The Squarespace site operator remains a **staged sandboxed embed** until the authenticated editor, backup, save/readback, anonymous/revoked HTTP checks and release manifest have been verified. No live page change is implied.

## Cross-system source fold and future gates
| Existing service/facet | UI projection | Real authority/proof gate |
|---|---|---|
| FileSpace | Place folders/cards, open existing filespace | Scoped signed read/hydration and peer storage |
| DataSpace | Data provenance and edges | Schema, signed DBR and reproducible readback |
| De Sporte | Recovery/persistence review room | Real device state + scoped signed operator controls |
| Achilles/Neo | Operator/local oversight and agent routing rooms | Existing local shell 8772 / Desktop 8765, separately authenticated |
| Eco/Raphael/Römer | Distinct microclimate/room navigation and evidence cards | Real research/engineering source rights; independent physical evidence |
| Game worlds | User home-base portal/virtual world collection | Actual game engine, asset licence, interoperable gameplay/session identity; VR device support |
| PrintSpace | Manufacturing object entry | Measured printer capability, compatibility, device interlock and acceptance |

### Validation
\`apps/lightspeed-go/src/cgxSpatialHomebase.test.ts\` exercises room lineage, source schema, collision/overlap, relation DAG, fixed parent, bounds, visual climate and local version changes. Integrated frontend regression and strict TypeScript must pass; committed production \`dist\` must match deterministic Vite CI exactly before marking the desktop build ready. Authentication, multi-node DBR, real AR tracking and live website release are explicitly independent, unclosed gates.
