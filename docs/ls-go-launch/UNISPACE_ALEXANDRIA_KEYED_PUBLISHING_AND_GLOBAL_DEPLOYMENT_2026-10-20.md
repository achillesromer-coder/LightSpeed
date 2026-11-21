# CGX / UniSpace / Alexandria — One infrastructure, keyed publication and global capability roadmap
**Date:** 2026-10-20 · **State:** Source-first review / no canonical mutation or public deployment

## Canonical scope and reuse
Re-use `Cognigrex.cgx`, `Cognigrex.cgx:/ccc`, existing FS identity, DS deltas/ack roots, LS leases/node registry, `cgx-handshake`, Press/Creator and existing children. **No new DB, blockchain, execution layer, semantic oracle or scheduler.** CGX-CCC != historical CCC / Create Your Collective. Parent graph links child-owned objects; no copying ownership.

## Publishing without blockchain
- A fileset key is a **nonsecret, versioned lookup** pointing at a manifest/source envelope and digest. It is not an identity, entitlement, payment token, remote peer, licence or guarantee that content is available.
- Exact content SHA-256 dedupes bytes only. Object_ID maps true referents. Representation_ID and conversion R0/R1/R2/R3/F classify projected meaning/behaviour; unverifiable inferences remain hypotheses.
- Profiles associate with filesets **privately** at authenticated services or per-device offline workspaces. Publishing a key cannot reveal subscribers.
- Grant validation is separate: signed issuer and metadata, audience, scope, expiry, revocation, user consent, replay/CAS and profile-controlled authorization. Avoid custom cryptography; geometry selectors are not signatures.
- A public/offline pack contains only specifically approved redistributable bytes and included dependencies, and remains usable without future server access; private packs require genuinely tested encryption/key preservation or cannot claim secrecy.
- DataSpace delivery is selected from full cold bundle / verified cached source / sparse replay / reference-only; missing source stays NOT_CACHED, unavailable stays WITHHELD, disagreement stays CONTESTED. Receiver proves base hash/size before delta. Compare total delivered bytes, memory, CPU, energy and recovery against ZIP/zstd/standard methods.

## Public reserve and network constraints
Treat public capacity reserve as an **application-level service objective over actually available and legally operated transports**: public-basic/offline recovery access, fair quotas, clearly published emergency priority, no paid starvation, documented resource exhaustion. The Schumann resonance system is a naturally occurring Earth-ionosphere ELF phenomenon; it cannot be reserved as IP internet communications bandwidth. Geologic site/physical infrastructure ties may affect node power and location, but not automatically provide communications.

## Archives, engines, space/science and semantic reuse
Pinned discovery catalogue:
- `bobeff/open-source-games` pinned at `3a9ab8fc892a2cdadf8989a72ba7624a11e39cec`, CC0 for the *list only*, not underlying games;
- `bobeff/open-source-engines` pinned at `4d54f3995140e64beebef6575760996bf14324ec`, CC0 for the list only;
- NASA software catalog and science data portal; candidates NASA Open MCT, F Prime, Earthdata MCP. Each package/source has its own terms, provenance and risk.
- Miniclip/Friv via Wayback Machine **discovery only**; snapshot capture verification blocked in this session and copying proprietary game/Flash assets is NOT approved merely because they are archived. An ad-free self-hosted public kit must use approved rights-cleared materials rather than removing licence or site restrictions.

Build one `CGX-CCC` adapter/engine registry, one shared source blob per exact hash, many rights-separated object references, and many domain-tailored representations. Do not merge unrelated engines' code into one binary merely because projects are indexed together. Test ABI/version, platform and content asset rights before treating engines as substitutable. NASA mission software is not a physical-validated simulation by virtue of inclusion; GMAT/MPL provenance and model restrictions remain independent.

## Corpus archive conflict tradeoff and reversible inference
For each archived/new statement: preserve source locator, timestamp, revision, licence, confidence, falsifiability, matched Object_ID candidates and known counterexamples; classify EXACT_SAME_CONTENT / SAME_REFERENT_CANDIDATE / REPRESENTATION_LINK / SEMANTIC_CONFLICT / INCOMPATIBLE_RUNTIME / RIGHTS_CONFLICT / NEW_FRONTIER.
Possible resolutions: alias exact duplicate source, merge nonconflicting attributes, create typed link, preserve parallel disputed hypotheses or explicitly supersede with date/evidence. Record *payoff and negative externalities* (bytes saved, CPU, network, lost fidelity, review cost, privacy/security/legal risks). Never rewrite R0 originals; R1 gets tested inverse; R2/3 generated new knowledge needs sources and independent validation. UI can render comparisons and suggest resolutions; no AI automatic source-owner promotion.

## Geo/institutional scope and speech
SAI (Shared Australian Intelligence) is an Australia-first functional lens/offer, not a legal state entity or independent regulator. Government customers can license managed workspaces, verified government data, data-residency choices and openly documented jurisdictional compliance overlays. **Do not design concealed political content suppression, personal surveillance or location-only blocks of the global open commons.** Separate government-authored data and national legal notices from original historical/source views. Where specific distribution restrictions are legally required, show transparent legal citations, applicable region, publisher, review, appeal/correction channel and expiry. Provide public information and offline access as widely as lawful; never promise a VPN circumvent method, unlicensed spectrum or transfer of sovereign authority through a file key.

## Deployment ladder and candidate five-container humanitarian cell
One common kernel/Creator/CCC family, distinct domain manifests and permitted dependencies:
- Level 0: Alexandria public index and no-login offline kit with truly distributable educational content;
- Level 1: UniSpace Creator offline file/data workspaces, source backups and custom lenses;
- Level 2: authenticated research/community collaboration and institutional hosting;
- Level 3: Römer-Grex/Eco-Grex/EMASSC domain tools and independent scientific/industrial qualification;
- Level 4: geographically tailored sovereign/humanitarian projects following actual partners, permits and evidence.

Five conceptual shipping-container **functions**, pending matching to any older approved deployment specification:
1. power, safe electrical distribution and independent communications;
2. water treatment/storage and sanitation;
3. shelter, safe-point and site logistics;
4. health/first response with clinical governance and privacy;
5. education, resilient repair/PrintSpace manufacturing and community/food-skills.

A suitable deployment may redistribute these functions across differently sized units; do not infer exact container dimensions, area, food/water throughput, medical certification, battery size, security permissions or site approvals. Local conditions must be assessed: climate, geology, flood/fire, grid and solar, accessibility, water quality, waste, transport and public safety. Offline Alexandria documentation and CGX inventory/training can support responders, but physical protection requires authority and qualified partners.

## Founder scope and release sequencing
- *Before launch*: verified offline kit, published catalogue rights, public/private negative leak test (#158), independent real native FS/DS pairing/readback (#161), plain-language legal terms and user portability.
- *Launch*: first public-safe Alexandria/UniSpace; measure cold/warm traffic, offline usability and independent devices. Publisher controls remain opt-in.
- *Post-launch*: richer content packs, search, profiles, creator hosting, contributed CCC packages, interoperability grants and paid capacity. Optional government/humanitarian institutional pilots; no automatic subscription/usage charging.
- *Phase expansion*: independently measured public-bandwidth reserve, field relays, device diversity, disaster kits and geography-aware science/Römer/Eco systems. No unsupported promises of eliminating new fibre or supplying global electricity.

## Source priority and PR owner gates
Keep existing draft PR #172–179 and issues #158/#161 as independent owner gates. This branch is additional **source candidate only**: it does not merge, deploy, enroll, rewrite child source, sign manifests, install plugins or submit funding/partner contracts. Reconcile first with current `main`, then owner-reviewed branch-by-branch merge with isolated tests. Do not duplicate base architecture; include functional deltas only.

## Release criteria / acceptance
1. Standalone signed source manifest with no private profile data, and rights-conformant offline reopen.
2. Two identity-distinct authorisations referencing the same key with no cross-profile leakage.
3. Exact blob reuse across two apps plus dependency ABI/rights proof; cold/warm savings quantified.
4. Reversible document↔worksheet conversion fixture where structurally possible, with a loss map elsewhere.
5. Multiple conflicting archive claims retained, payoff log review, and no silent last-write-wins.
6. Verified outbound public reserve on actually operated channel, exhaustion and emergency override tests.
7. Da Fit-style peripheral only with vendor-supported, user-consented export and no false node privilege.
8. Full regional/jurisdictional accessibility and privacy test including appeals, geography errors and offline access.
9. Separate certified physical safety gates for proposed five-container response modules.
