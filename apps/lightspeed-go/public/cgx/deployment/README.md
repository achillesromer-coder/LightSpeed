# UniSpace × CGX public Squarespace and LS GO surface

**Brand:** UniSpace is the front-facing Universal Operating Model; CGX is the native recursive FileSpace/DataSpace/PrintSpace grammar. No new graph master, runtime, owner or rights are created.

## Deployment
**Mandatory isolated publication boundary:** The LS GO `apps/lightspeed-go/public/` tree ALSO includes `data/`, `review/`, `ls-go/` and other review or operational files. Never publish that whole tree, the default Vite build `dist/`, or repository roots to Squarespace/Vercel as the CGX public viewer.

Prepare the existing separate public/static Vercel project from the reviewed, explicitly allowlisted CGX subset only:

```bash
python apps/lightspeed-go/scripts/assemble_cgx_public_site.py --output cgx-isolated-site
```

The output contains exactly 12 approved CGX static files under `cgx/`, `vercel.json` at the site root for the CSP/frame policy, and `cgx-public-integrity.json` with exact asset SHA-256 hashes. The builder refuses symlinks, source/output overlap, pre-existing outputs and operational/private identifier patterns; no unrelated `public/data`, `public/review` or `public/ls-go` content is copied. Deploy **the contents of `cgx-isolated-site/` as the static site root**, never `apps/lightspeed-go/public` or `apps/lightspeed-go/dist`. Publishing this candidate still requires issue #158 owner review and independent live GET/iframe testing.

GitHub CI `UniSpace CGX Public Viewer Validation` builds this exact isolated output, tests the five forbidden URL paths for HTTP 404, checks all seven site routes in Chromium and records browser/manifest proof artifacts. This is a source-level acceptance test, not a claim that the production Vercel project has been updated.

The existing proposed public viewer origin is `romer-unispace-public.vercel.app`; the separate older DOOM deployment must not be modified by CGX release packaging.

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

## Acceptance to finish
Open each Vercel route from a fresh desktop browser and phone; confirm HTTP 200 and local controls; install the Squarespace snippets; confirm five live romer.industries URLs, navigation, iframe size and mobile layout; separately verify the DOOM link target and source publication rights.
