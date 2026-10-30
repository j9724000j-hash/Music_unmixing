# APK Build Guide — Turkish Organ Pro → Redmi 13

This converts the PWA (`www/`) into a native `.apk` that installs on Redmi 13 (or any Android 6+). You have two options: **(A) One-command Capacitor build (recommended)** or **(B) PWA Install (no SDK, instant)**.

---

## Option A — Real Signed APK (for Play Store / direct install)

### 1) Install Prereqs (once)

- **Node 18+**: https://nodejs.org — verify `node -v` and `npm -v`
- **Java 17** (Temurin recommended): https://adoptium.net — `java -version` must show 17
- **Android Studio**: https://developer.android.com/studio
  - Open SDK Manager → install **Android SDK Platform 34**, **Build-Tools 34.0.0**, **NDK** (optional)
  - Set `ANDROID_HOME` / `ANDROID_SDK_ROOT` to e.g. `C:\Users\You\AppData\Local\Android\Sdk` (Win) or `/Users/you/Library/Android/sdk` (macOS) or `~/Android/Sdk` (Linux)
  - Add to PATH: `platform-tools` and `emulator`

### 2) Build

```bash
cd TurkishOrganPro
npm install                      # installs @capacitor/* devDeps
npx cap add android              # creates android/ wrapper on first run only
npx cap sync                     # syncs www/ → android/app/src/main/assets/public
cd android
./gradlew assembleDebug          # debug APK (install directly)
# or
./gradlew bundleRelease          # Play Store .aab
# or
./gradlew assembleRelease        # signed APK (needs keystore config)
```

**Outputs**
- Debug: `android/app/build/outputs/apk/debug/app-debug.apk` (≈ 4–6 MB — web assets only, no heavy native libs)
- Release AAB: `android/app/build/outputs/bundle/release/app-release.aab`

### 3) Install on Redmi 13

1. Copy `app-debug.apk` to phone (USB, Telegram, Drive).
2. On Redmi 13: Settings → Apps → Special permissions → Install unknown apps → allow your file manager / browser.
3. Tap APK → Install → Open → **Turkish Organ Pro** appears in drawer, full-screen, offline.

### 4) Signing for Play Store

Create a keystore once:

```bash
keytool -genkey -v -keystore turkish-organ.jks -keyalg RSA -keysize 2048 -validity 10000 -alias turkish
```

Then in `android/app/build.gradle` → `android { signingConfigs { release { storeFile ... storePassword ... keyAlias ... } } }` and run `assembleRelease` / `bundleRelease` with `--signing`.

App ID: `com.turkishorgan.pro` (see `capacitor.config.json`) — change if you upload under another package.

---

## Option B — Instant PWA Install (No SDK, 10 seconds)

If you just want an app icon on Redmi 13 right now:

1. Host `www/` anywhere HTTPS (GitHub Pages, Netlify, Vercel, or `python -m http.server` via ngrok).
2. On Redmi 13, open Chrome → visit URL → menu (⋮) → **Add to Home Screen** / **Install app**.
3. The PWA launches fullscreen, offline (service worker caches all assets), with the gold icon (192/512), no URL bar — indistinguishable from APK for this use case (no native-only features needed: audio/MIDI all work via Web APIs).

Redmi 13 HyperOS + Chrome fully support PWA install; the preview in this repo is already configured (manifest + sw.js).

---

## Troubleshooting

- **`cap: command not found`** → `npx cap` not `cap`.
- **`SDK not found`** → set `ANDROID_HOME` env and reopen terminal.
- **Audio silent after install** → first tap must be on screen (autoplay policy); splash “TAP TO START” handles this.
- **MIDI not showing** → use OTG cable + USB-host MIDI keyboard; grant MIDI permission on Android 12+. Chrome for Android supports Web MIDI via flag; native APK via Capacitor has full MIDI.
- **APK size huge** → ensure you didn’t accidentally bundle `VIBE88_...zip` 99MB — `.gitignore` excludes media.

---

## CI (GitHub Actions) — Optional Auto-APK

You can add `.github/workflows/build-apk.yml` that on `git push` builds the APK with `r0adkll/upload-android-artifact` etc. — left out to keep repo light, but ask and we’ll add it.

---

## What’s Already Done

- `www/` is production-ready, linted, 0 build-step.
- `capacitor.config.json` is pre-filled (`appId com.turkishorgan.pro`, `webDir www`).
- `package.json` scripts: `npm run cap:sync`, `cap:build`, `apk:release`.
- Icons, manifest, service worker all wired.

Just run the two commands above and you have a hyper-professional APK.
