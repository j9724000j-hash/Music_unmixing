# Music_unmixing — Turkish Organ Pro (PWA + APK) + Previous Research

This repository now contains:

- **FREE_MUSIC_LIBRARIES_AR.md** — Arabic guide to free instrument libraries (FL Studio compatible)
- **TurkishOrganPro/** — **New: Professional Turkish Oriental Organ** (English UI, 10 Turkish instruments, 10 Turkish rhythms, Maqam quarter-tone engine, controls for keyboard size/smoothness, rhythm/tempo/pitch/reverb/EQ, sustain/pitch-bend etc.)
  - Live PWA: `TurkishOrganPro/www/index.html` — works offline, installable on Redmi 13, no subscription
  - APK: built via Capacitor + GitHub Actions (see `TurkishOrganPro/docs/APK_BUILD_GUIDE.md` and `TurkishOrganPro/releases/README.md`)
  - Research: `TurkishOrganPro/docs/TURKISH_LIBRARIES_RESEARCH.md` — free high-purity Turkish libraries without subscription (DSK World Stringz, TAQSIM, EasternONE, VCSL/VSCO2-CE, University of Iowa, Djembuka, FreePats …)

### Quick Open — Turkish Organ Pro

```bash
cd TurkishOrganPro/www && python3 -m http.server 8080
# → http://localhost:8080 — tap TAP TO START & PLAY
```

On Redmi 13: Chrome → open preview → ⋮ → Install app (offline, fullscreen).

### Build APK

See [TurkishOrganPro/docs/APK_BUILD_GUIDE.md](TurkishOrganPro/docs/APK_BUILD_GUIDE.md).

### Previous content

- `WakaWaka_Orchestral_A/` — orchestral arrangement example
- `Nay1_MIDI_Pack/` — measured Nay analysis + MIDI pack

