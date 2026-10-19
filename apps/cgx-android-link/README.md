# CGX Android Link — smallest mobile association component

This **Android file handler** is intentionally **not** a LightSpeed GO runtime, an executor, a proxy, or an authorization mechanism. It registers a launch icon, a `cgx://cgx.cgx` URI handler, and common MIME handlers to offer **Open with → CGX Link** for existing `.cgx` files. Android file managers may supply unknown MIME types and opaque content URIs, so **Choose a .cgx file** remains the reliable fallback.

**Current state:** Android source candidate imported into existing LightSpeed PR176. The pure Java carrier/origin validator compiles and passes 18 JVM checks; the Activity, Android platform parser, APK and phone remain untested. **NOT an APK; NOT signed or installed.** A stand-alone `.cgx` document cannot install its own Android association.

## Build on the existing desktop (one-time)

1. Open this folder as a project in Android Studio (JDK 17, SDK Platform 35; Android Gradle Plugin 8.7.3 / Gradle 8.9 compatible).
2. Build → Build APK(s), or run `gradle :app:assembleDebug` from a shell with Gradle 8.9 and Android SDK 35 configured.
3. Install the generated `app/build/outputs/apk/debug/app-debug.apk` using the normal Android package installer or `adb install` with the phone authorized over USB.
4. On phone, tap **CGX Link** or use Files → Open with → CGX Link. If your Files app doesn't offer it for a generic MIME type, use **Choose a .cgx file** inside CGX Link.
5. The sample is the same byte-identical carrier as `../lightspeed-go/public/cgx-mobile-link.cgx`. Host-local addresses are descriptive only; imported endpoint/auth fields are never used to choose a route or grant authority.
6. Configure the **approved private HTTPS origin** provided by the desktop route. The same authenticated origin must serve `/` as the running LightSpeed GO UI and `/api/v1` as the existing desktop API. Test status and owner sign-in via browser; then verify a real DBR receipt. Do not use localhost addresses from the phone.

### Architecture

Phone (carrier importer / CGX Link) → authenticated private HTTPS route (to be configured) → BouwerBase existing LightSpeed GO UI on :4173 and API on :8765 → host's existing permission gates / DBR receipts. **Drive remains the existing fallback/backup**, handled by the existing CGX/LightSpeed lanes, not by this Android adapter.

### Security and verified limits

- Rejects malformed or oversized CGX, other semantic roots, unexpected host, dangerous authority flags.
- Does not execute the CGX file as code or run commands locally; it opens URLs in the existing browser.
- Never stores passwords or bearer credentials. Only stores a user-entered HTTPS origin in app-private preferences.
- Android's MIME resolution varies by Files app; `.cgx` filename alone does not register a universally reliable file association.
- Opening the private URL in a browser is **not** proof that an authenticated handshake occurred; confirm host identity, existing owner permissions, status and receipt readback.
- The link shown for the public LightSpeed GO web interface is a **separate UI route**, not proof that the BouwerBase desktop service is connected.
- Only the platform-independent validator was compiled on the existing JDK 8. APK compilation requires JDK 17, Android SDK 35 and Gradle 8.9; none was found in the checked build locations/PATH. No SDK licenses were automatically accepted.

## JVM validation (does not establish Android acceptance)

Compile `MobileCarrier.java` and `tests/MobileCarrierProbe.java` with a test-only `org.json:json:20240303` JAR, then run `au.com.cognigrex.cgxlink.MobileCarrierProbe samples/CGX_Mobile_Handshake_BouwerBase.cgx`. Production uses Android's platform `org.json`; no JAR is bundled in the app. Test dependency SHA-256: `3cf6cd6892e32e2b4c1c39e0f52f5248a2f5b37646fdfbb79a66b46b618414ed`.

Checks cover the shared binding/protocol, oversize and invalid UTF-8 input, altered/string-valued authority flags, wrong root, loopback/insecure/credential/path/query/fragment origins and a valid HTTPS origin. The native handler resets recognition on each incoming intent and opens the existing UI for owner sign-in and DBR reading; raw browser API navigation cannot supply the UI's session header.

Rollback before device installation is a source revert. After an owner-authorized test installation, uninstall `au.com.cognigrex.cgxlink`; no desktop runtime, credentials, carrier authority or executor is installed by this adapter.

Official platform reference: https://developer.android.com/guide/components/intents-filters
