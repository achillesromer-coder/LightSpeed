# Achilles mobile secondary-node bootstrap — source review

The user-facing Android chat is the **primary interaction device**, not the
primary CGX execution or database authority. The desktop Work session handles
supervised changes to BouwerBase; this isolated mobile review branch does not
modify the shared active checkout or the installed runtime.

## Built surface

- `apps/lightspeed-go/public/achilles-mobile.cgx.html` is a single-file,
  offline-capable H0 staging surface. It can be opened on Android immediately,
  subject to the browser's normal local-file handling.
- The existing Vite build copies the page to
  `apps/lightspeed-go/dist/achilles-mobile.cgx.html`, which the desktop
  reconciler includes in its tracked installation inputs. The bootstrap test
  checks byte equality with the source page.
- It creates a short-lived random **unsigned coordination nonce**, records
  user-selected permission *requests*, and exports a scrubbed JSON handoff.
  This is not Android keystore identity or an authenticated device grant.
- An optional user-supplied private HTTPS origin can be tested on demand by
  requesting only `/api/v1/status` without cookies, bearer tokens, login,
  mutation, peer transfer or automatic background polling.
- A successful HTTP status does **not** prove peer identity, private relay
  ownership, signed device capability, lease or DataSpace registration.
- Credentials, private keys, OS fingerprints, content sources, location and
  chat history are not collected or saved by this page. Nothing is stored in
  localStorage/IndexedDB or a second Cognigrex database.
- The existing `cgx-mobile-node` and `cgx-handshake` skills remain the
  source contracts. This adds a surface for completing the **initial
  handoff**, not a new native agent or runtime.
- The owner review panel drafts A1–A3 Y/N decisions and optional notes for
  manual transfer into the owner's chat. The form keeps notes in page memory
  and excludes them from the device handoff JSON and relay status request.
  Chat drafts carry no host authentication or execution authority.

## Desktop Work handoff

1. Review PR and identify the existing private HTTPS/WSS relay and owner
   authentication route; current desktop status says local-only.
2. Route the same-origin hosted mobile UniSpace surface through the existing
   LS GO deployment and registered CGX selector. Do not publicly expose
   port 8765 or accept a browser-provided mobile nonce as canonical identity.
3. Enroll with a platform-keystore-backed node key and server-side signature
   challenge; verify independently registered roots and bounded capabilities.
4. Verify the mobile endpoint's Android OS permissions via explicit device
   actions, no blanket background, microphone, camera or file grant.
5. Complete authenticated device-to-host readback, and issue the existing
   receipt + scoped lease without minting a new DataSpace authority.
6. Only then consider live peer status and sanctioned mobile operations.

## Verification and bounds

The page's exported JSON explicitly marks identity, owner session, Recovery,
leases, peer and mint claims as **unverified**. The mobile device cannot be
configured remotely by this script, and ChatGPT's mobile chat by itself is not
an authorized network peer for the host. A physical device-side handshake and
private relay must be verified first.

Separate release and native mint gates in PR #228 and persistence PR #227
remain unchanged.
