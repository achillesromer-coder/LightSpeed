# CGX mobile local source acceptance — 13 October 2026

Owner request: prioritize the mobile handshake before systematic local alignment. Implementation owner remains draft PR176, based on `c757c66ecdfe5552e6849c8f8b60131178121929` and canonical main `99716d6b6c687aca2a6a9a85cea239cc7b8fb95f`.

Sources: Drive intent handoff `10CAlHc60-_1uVh8RVZIIj2fA3RQ0Nwms`, cross-lane addendum `1pAUxFON3Q-v5BGXdA91uU4NqlANwhA_U`, candidate Android ZIP `1MWY9dqZo8sHwXeKhgrmOV-sTLS1oOZJ0`. ZIP readback: 8,173 bytes, SHA-256 `ee346719af48dbb2a53f2eedca718c1d66f51c13cdf6af89a4ad69649651e012`. Shared chat rendered no readable conversation text through web fetch; the Drive files were read directly.

## Changes

Existing LS GO gains carrier recognition, explicitly selected HTTPS connect/resume, persistent disconnect and a route to its existing owner sign-in. Imported carrier fields cannot set a destination, session or execution authority. Only the selected origin and disconnect preference are stored; tokens remain in page memory. Route change reloads the page and clears origin-bound UI/session state. Reconnection does not submit pending jobs. A hosted unconfigured page no longer probes the phone's loopback or its own relative `/api/v1` path.

The source-controlled carrier now includes the semantic root/binding/protocol expected by the supplied Android candidate. The same bytes are used as its sample. The native association source is retained under `apps/cgx-android-link`, with strict boolean constraints, bounded byte/UTF-8 parsing, loopback-origin rejection and recognition reset for new intents. It delegates authentication and receipt reading to the existing LS GO UI. No device-key enrollment or new execution service was introduced.

## Evidence

| Acceptance item | Classification | Evidence / remaining requirement |
|---|---|---|
| Browser carrier recognition | PRESENT_AND_VERIFIED | Shared sample imported in isolated local UI; SHA-256 readback |
| Source-level negative boundaries | PRESENT_AND_VERIFIED | 66 frontend tests; 18 JVM validator checks |
| Type check / UI build | PRESENT_AND_VERIFIED | `npm.cmd run check` and `npm.cmd run build` |
| Existing desktop/auth/mobile contract regression | PRESENT_AND_VERIFIED | 82 pytest tests; one upstream deprecation warning |
| Phone-size browser layout | PRESENT_AND_VERIFIED | 390×844 test viewport; content width equals client width 375 after scrollbar; long hash wraps |
| Browser connect/resume/disconnect | PRESENT_AND_VERIFIED | Selected loopback development route persists across reload; disconnect clears it; no command submit performed |
| Android Activity/file association | PRESENT_UNTESTED | Source/manifest only; physical target required |
| Signed installable APK | BLOCKED | SDK/Gradle/JDK17 build setup absent in checked locations; no APK produced |
| Secure mobile-data route | BLOCKED | Owner reports no private HTTPS origin configured; inspected services bind loopback only |
| Phone/host node enrollment | BLOCKED | No physical phone identity, challenge/lease or readback received |
| Existing owner authentication on phone | BLOCKED | Private route and actual target required; fixtures are not phone acceptance |
| Local permitted operation and phone DBR | BLOCKED | Installed Smith consumer liveness/source gate plus private phone route remain open |
| Drive fallback/backup | PRESENT_UNTESTED | Existing outbox; no backup claim without matching destination hash readback |

The preview on port 4186 does not have installed bridge CORS approval; browser reachability there remains unverified even though direct local HTTP health reads succeed. No production CORS settings were changed to make the preview appear connected.

## Next bounded action and gates

Owner must select/approve a private HTTPS route that admits only BouwerBase and the Android access node, preserving the existing UI/API/session boundaries. No public bridge bind, firewall opening, tunnel enrollment, SDK-license acceptance, app installation, merge, deploy or source-to-installed update occurred. Prepare/build the native APK with supported tooling after its setup gate, then let the mobile lane verify installation and mobile-data access. The existing Smith recovery gate is a dependency of the final operation/DBR step; do not mark the mobile lane complete before that proof.

The candidate build artifact is not a publication bundle. Existing issue158 private asset classification and issue161 real authenticated-device proof remain held. Source rollback is a revert of this PR delta; the installed application and queues remain unchanged.
