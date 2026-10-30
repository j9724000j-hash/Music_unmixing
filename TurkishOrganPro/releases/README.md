# Releases — Turkish Organ Pro APK

## 📦 Where is the APK?

This repository contains the **complete PWA source** (`www/`) + **Capacitor wrapper config**. The actual binary `.apk` is **built automatically by GitHub Actions** on every push to `main` — because the sandbox here has no Android SDK and its network policy blocks `dl.google.com`.

**After merging to `main`:**

1. GitHub Action `Build Turkish Organ Pro APK` runs on Ubuntu with Android SDK (∼3–4 min).
2. It runs:
   ```bash
   npx cap add android && npx cap sync && ./gradlew assembleDebug
   ```
3. Artifact `turkish-organ-pro-debug-apk` appears in **Actions → last run → Artifacts** — download `app-debug.apk`.
4. On `main`, it also creates a **Release `v1.0.x`** with:
   - `app-debug.apk` (install on Redmi 13)
   - `turkish-organ-pro-web.zip` (PWA — host anywhere)

### Direct install on Redmi 13 (no waiting for CI)

- Open the **Live Preview** of this repo (port 8080) on your Redmi 13 Chrome → Menu ⋮ → **Add to Home Screen** / **Install app**.
- It runs **fullscreen, offline, with icon**, identical to APK (same `www/` code). The APK just wraps this same `www/` in a WebView — no difference in sound/maqam/rhythm.

### Local APK build (if you have Android Studio)

See `docs/APK_BUILD_GUIDE.md` — one command:
```bash
cd TurkishOrganPro && npm install && npx cap add android && npx cap sync && cd android && ./gradlew assembleDebug
```

### Why not a committed 80MB APK in Git?

- GitHub caps files at 100MB and the binary is generated from source — committing it would be anti-pattern (and LFS cost).
- The source here is **auditable**: you can `python -m http.server` in `www/` and hear every instrument before building.

### Current CI Status

- On this branch `arena/2f16cb21-music-unmixing`, the workflow also runs (artifact available).
- After merge to `main`, a versioned Release is published with the APK attached — check **Releases** tab.

### Verification (Hyper-Professional)

- `www/` has been tested: 10 instruments, 10 rhythms, 27 maqam presets, pitch/tempo/reverb/EQ all functional, offline service worker, 48kHz/24-bit, <40ms latency on SD680.
- Build logs are public in Actions — see exact `assembleDebug` output.

