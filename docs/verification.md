# Preview verification · v0.3.0 · 2026-10-16

## Current v0.3 verification

APK SHA-256: 917bf5d663730d459ef11fe3ec26627a01a4b65c6d841440e297ef31cd660519.

- Production compilation passed with strict Angular template/type checks. Initial chunks: 351.24 kB raw / 85.88 kB estimated transfer; account UI is deferred (18.50 kB raw / 4.70 kB estimated transfer). The 350 kB warning threshold is exceeded by 1.24 kB; the 500 kB hard limit passes. These estimates exclude fonts, profiles, images and HTTP overhead and are not production benchmarks.
- Six recommendation tests, one full 110-profile fixture check and sixteen Python behavioral/security test groups passed. Google verification is mocked at its library boundary for integration tests; no live Google account login was tested or claimed.
- Browser registration created an isolated test account with zero initial connections/messages, correct name/age/city, and empty personal attributes. Session and profile form values survived reload. Editing the bio, signing out and signing in again restored the saved bio.
- All six app sections were opened, each with the expected page-entry animation and no horizontal overflow. Console errors: none in the inspected flows.
- Mobile 390 × 844: self-hosted Vazirmatn loaded; account dialog scrolls inside the viewport with no horizontal overflow. Finder like/negative-feedback controls ended at approximately 594/645 CSS pixels, above bottom navigation. No broken images were found.
- Android and iOS were synchronized with the final Angular bundle. Android assembleDebug passed and apksigner verified v2 with one debug signer. Version 0.3.0, code 3; APK size 5,074,831 bytes. iOS compilation/signing and Android device execution were not run.
- The existing private Sites audience is preserved. This publication and native offline sample do not run Python accounts. Email registration/login is verified on the local Python deployment; Google requires an externally created OAuth client. The Cloud console returned HTTP 403 in the available browser, so no client was created. See accounts.md.

## Historical v0.2 baseline

The following build and APK records describe v0.2 rather than the current release.

### v0.2 verification

- Strict Angular production compilation passed. JavaScript: 301.50 kB raw / 73.25 kB estimated transfer; stylesheet: 41.07 kB raw / 8.15 kB estimated transfer. Combined compressed estimate: 81.39 kB, excluding images/fonts and HTTP overhead.
- Six recommendation test groups passed: selection exclusion/undo, similar-profile suppression, pass behavior, attribute/relationship-goal ranking, hard preference filters, and Persian normalization without photo/name/age/city similarity inference.
- Eight Python API test groups passed, including negative feedback, attribute validation/persistence and legacy-state migration. Partial updates preserve omitted attributes; existing choices and custom biographies survive migration. Tests use an isolated temporary database.
- Browser checks confirmed automatic advance after a like/pass, persisted negative feedback, reversible suppression patterns, and attribute edits that survive reload and change recommendation order.
- Existing user choices were preserved. Four new fictional adult sample profiles provide fresh choices, making ten sample profiles in total.
- No broken images, horizontal overflow or browser console errors were found during the tested flows.
- At a 390 × 844 mobile viewport override (384 CSS pixels available), all three choice controls were visible above the bottom navigation. At a 1280 × 720 desktop override, the last action ended at 692 CSS pixels, within the viewport.
- Screenshots: docs/screenshots/finding-desktop.jpg and finding-mobile.jpg.
- Android and iOS were synchronized with the final bundle. Android :app:assembleDebug passed; apksigner verified Signature Scheme v2 with one debug signer. Package com.rafiqbaz.app, version 0.2.0 (code 2), minimum SDK 24, target SDK 36.
- Current APK: 5,020,073 bytes. SHA-256: 4d3e4bdaeaced8391161ff51c7d5166f818597b8e7d3bac1ba95f5b1ff447c4f.
- Local preview uses the Python API (health version 0.2.0). Hosted and bundled native previews use local sample state.

iOS compilation/signing requires macOS and was not run. Android-device execution and store distribution have not been verified. Performance figures are build estimates, not production benchmarks.

## Historical v0.1 baseline

The following records describe the earlier build, not the current APK or bundle.

## Build

- Angular 21.2.25 production compilation: passed, strict TypeScript/template checks.
- Initial JavaScript: 251.87 kB raw; estimated transfer 65.12 kB.
- Initial stylesheet: 39.04 kB raw; estimated transfer 7.82 kB.
- Combined code/style estimate: 72.94 kB compressed, excluding images/fonts and HTTP overhead.
- Six self-hosted 720 × 940 WebP portraits: 38,602–70,406 bytes each.
- Persian font: 46,308 bytes; Latin font: 34,524 bytes.

These figures describe this preview build, not a guarantee of the fastest possible application. No Lighthouse, production-network, real-device FPS, or load/concurrency benchmark has been claimed.

## API

Five behavioral test groups passed:

1. Mutual like behavior, idempotence and session isolation.
2. Messaging requires a connection; whitespace rejected; literal message text preserved as data.
3. Adult age and preference validation.
4. Save toggle, pass/undo and unknown profile rejection.
5. Invalid session UUID rejection and API 404 handling.

Local health endpoint sample: 30 requests after 3 warmups, median 1.75 ms, p95 2.01 ms, one client on loopback. This is a local smoke measurement of the health endpoint, not a database throughput or production latency benchmark.

## Browser review

- Desktop profile discovery, interest filter, save, like, mutual connection dialog and demo chat were exercised through the browser.
- A demo message was saved and appeared in the conversation.
- Full-stack server served all images with no broken images and no horizontal overflow.
- Mobile navigation and conversation view were exercised with a 390 × 844 viewport override.
- Screenshots are saved under docs/screenshots.
- The runtime settings showed the local app connected to the Python API.
- Desktop browser console checked for errors: none at the full-stack preview.

## Native status

Android and iOS projects were generated and synchronized with the production Angular bundle. The iOS project is ready to open with Xcode and uses Swift Package Manager; compilation/signing requires macOS and has not been run on this Windows system.

Android :app:assembleDebug passed locally. The standard Google Maven endpoint returned HTTP 404 for the Android Gradle Plugin from this environment. An opt-in, HTTPS mirror fallback is available by setting RB_MAVEN_MIRROR=1 before invoking the Android build helper. There are no credentials in this repository.

The app's debug APK was generated and verified with Android SDK apksigner. APK Signature Scheme v2 verification passed with one debug signer. Package: com.rafiqbaz.app, version 0.1.0, minimum SDK 24, target SDK 36. Size: 4,647,983 bytes. SHA-256: 8130d6132cab81a9d8dc3347be0998ccd350c22447081da8267051bdbf65cb60.

The local deliverable is releases/rafiq-baz-debug.apk; it is excluded from Git source and is intended for testing, not store distribution.

The native app is an offline sample build. Native-device execution and store distribution are separate from the browser preview.
