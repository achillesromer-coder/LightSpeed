# UniSpace × CGX public Squarespace and LS GO surface

**Brand:** UniSpace is the front-facing Universal Operating Model; CGX is the native recursive FileSpace/DataSpace/PrintSpace grammar. No new graph master, runtime, owner or rights are created.

## Deployment
A separate public static-only Vercel project named romer-unispace-public hosts approved demonstration files from apps/lightspeed-go/public/cgx. The site does NOT include the private LS GO entrypoint, owner sign-in, desktop command bridge, internal object review or private catalogue. The earlier romer-cgx-doom deployment was not modified.

Vercel production alias (deployment READY):
- https://romer-unispace-public.vercel.app/cgx/
- https://romer-unispace-public.vercel.app/cgx/fs/
- https://romer-unispace-public.vercel.app/cgx/ds/
- https://romer-unispace-public.vercel.app/cgx/ps/
- https://romer-unispace-public.vercel.app/cgx/doom/

Vercel source tree and production-ready deployment were confirmed. Direct external HTTP GET through the model environment was unavailable, so hosted page rendering and iframe behaviour still require independent browser acceptance. Five equivalent local static routes passed CI at https://github.com/achillesromer-coder/LightSpeed/actions/runs/38202673818.

## Squarespace installation
Create or keep five lower-case Squarespace routes: /cgx, /cgx/fs, /cgx/ds, /cgx/ps, /cgx/doom. Paste deployment/SQUARESPACE_CGX_EMBED.html into the Squarespace Code Block on every page. The embed chooses the matching route from the current Squarespace URL and resizes only on trusted origin messages. Where a Squarespace plan strips scripts, use its supported Code Injection or an iframe with the matching static route URL.

Vercel's content security policy permits embedding from romer.industries and www.romer.industries only. Do not paste internal credentials or invoke LS GO operator APIs from the public viewer.

## Public functions
FileSpace supports a synthetic prism/tree, identity and evidence/unknown lens.
DataSpace supports a LOCAL hypothetical device negotiation and candidate sparse state update, not real authenticated peer transport.
PrintSpace demonstrates CAN-IF material-sequence conditions, not qualified machine control or physical testing.
DOOM displays the genuine benchmark sizes and 15 byte-range slices and offers an external link to the separate DOOM host, without copying internal review assets.

All model values and inputs are explicitly synthetic; static content roots are reference fixtures only.

## Owner gates
Source branch is review-only; no public CGX authority promotion, new canonical store or scheduler. Real device handshake requires an authenticated source adapter, signature/lease and independent receipt (LightSpeed issue #161). Private/public separation remains issue #158. Physical PrintSpace qualification remains Raphael PR #6. User-facing Squarespace paths are NOT modified merely by deploying Vercel.

## Operator build isolation and post-package verification
The ordinary `apps/lightspeed-go/dist` (from `npm run build`) is **not** a CGX public release. Vite copies `public/data`, `public/review` and other operator-oriented files into that tree; do not upload, alias or deploy it as the public UniSpace viewer. Issue #158 remains OPEN until a separately authenticated private-asset route and anonymous/revoked-session HTTP readbacks pass.

For a **nonpublishing**, source-only static candidate, use the exact allowlist packager with a fresh directory *outside* the LightSpeed GO app and its public/dist trees. After creation, reverify the actual output bytes, metadata, and Vercel policy:

```bash
python apps/lightspeed-go/scripts/cgx_public_bundle_guard.py --output /tmp/unispace-cgx-review
python apps/lightspeed-go/scripts/cgx_public_bundle_guard.py --verify-output /tmp/unispace-cgx-review
```

Verification succeeds only for the exact 12 allowlisted payload files and two policy/receipt sidecars. Tampering, added private paths, changed rights claims, policy drift, and general operator dist are denied. Successful verification is **not** permission to publish: independent rights, host/ACL, root/DBR and founder gates still apply.

## Acceptance to finish
Open each Vercel route from a fresh desktop browser and phone; confirm HTTP 200 and local controls; install the Squarespace snippets; confirm five live romer.industries URLs, navigation, iframe size and mobile layout; separately verify the DOOM link target and source publication rights.
