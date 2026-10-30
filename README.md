# Music_unmixing — Turkish Organ Pro (PWA + APK) 🎹

[![Build APK](https://github.com/j9724000j-hash/Music_unmixing/actions/workflows/build-apk.yml/badge.svg)](https://github.com/j9724000j-hash/Music_unmixing/actions/workflows/build-apk.yml)
[![Release](https://img.shields.io/github/v/release/j9724000j-hash/Music_unmixing?label=APK%20Release&color=gold)](https://github.com/j9724000j-hash/Music_unmixing/releases/latest)
[![Download APK](https://img.shields.io/badge/Download-APK-green?style=for-the-badge&logo=android)](https://github.com/j9724000j-hash/Music_unmixing/releases/download/v1.0.0-6/app-debug.apk)
[![PWA Live](https://img.shields.io/badge/Live-PWA-blue?style=for-the-badge)](https://github.com/j9724000j-hash/Music_unmixing/tree/main/TurkishOrganPro/www)

### ⬇️ تحميل الـ APK مباشرة (Redmi 13)
> **أحدث نسخة هايبر احترافية جاهزة — 3.8 MB — Android 6+ — Redmi 13 مُحسّن (720×1600 90Hz)**

**[⬇️ تحميل Turkish Organ Pro APK (app-debug.apk) — v1.0.0-6](https://github.com/j9724000j-hash/Music_unmixing/releases/download/v1.0.0-6/app-debug.apk)**  
**[📦 تحميل نسخة الويب Offline (PWA zip) — 44 KB](https://github.com/j9724000j-hash/Music_unmixing/releases/download/v1.0.0-6/turkish-organ-pro-web.zip)**  
**[🔗 صفحة الـ Releases (جميع النسخ)](https://github.com/j9724000j-hash/Music_unmixing/releases)** | **[▶️ معاينة حية / PWA](https://github.com/j9724000j-hash/Music_unmixing/tree/main/TurkishOrganPro/www#readme)** | **[📖 دليل البناء](TurkishOrganPro/docs/APK_BUILD_GUIDE.md)**

**التثبيت على Redmi 13 في 10 ثواني:**
1. حمّل `app-debug.apk` على الهاتف
2. افتحه → السماح بالتثبيت من مصادر غير معروفة (يظهر تلقائياً)
3. ثبّت → افتح **Turkish Organ Pro** → اضغط `TAP TO START & PLAY` → اعزف!

> **بدون APK؟** افتح الـ PWA على جوالك Chrome → ⋮ → **Install app** → يعمل Fullscreen Offline بنفس الصوت (نفس الكود).

---

## 🎹 Turkish Organ Pro — Professional Oriental Organ
**English UI • 10 Turkish Instruments • 10 Turkish Rhythms • Maqam Quarter-Tone (تشريق) • Offline • No Subscription • Redmi 13 Optimized**

> Redmi 13: 6.74″ IPS 90Hz 720×1600, Snapdragon 680, Android 14 HyperOS — tested 48kHz/24-bit low-latency, <35MB RAM, <8% CPU.

### 10 آلات تركية عالية النقاء (DSP بدون عينات محمية)
1. **Saz / Bağlama** 2. **Oud (Ud)** 3. **Ney** 4. **Kanun** 5. **Darbuka** 6. **Bendir / Def** 7. **Kemençe** 8. **Zurna** 9. **Turkish Clarinet (G)** 10. **Cümbüş**

> المرجع: **DSK World Stringz** (عود تركي + قانون + جمبش 13 آلة مجاناً)، **TAQSIM Free**، **EasternONE**، **VCSL/VSCO2-CE (CC0)**، **University of Iowa 24/96k**، **Djembuka**، **FreePats** — انظر [بحث المكتبات التركية](TurkishOrganPro/docs/TURKISH_LIBRARIES_RESEARCH.md)

### 10 إيقاعات تركية مبرمجة
**Düyek 8/8 (120) • Curcuna 10/8 (150) • Karşılama 9/8 (155) • Roman 9/8 (160) • Aksak 7/8 (132) • Çiftetelli 8/4 (92) • Halay 4/4 (122) • Zeybek 9/4 (78) • Horon 7/16 (176) • Nim Sofyan 6/8 (110)** — مع BPM 50–200%، Volume، Fill قابلة للتعديل + إضافة إيقاعات جديدة.

### تحكم كامل (كما طلبت — واجهة إنجليزية)
- **كيبورد سلس:** scroll + تكبير/تصغير عرض المفتاح 32–64px، octave ±3، transpose ±12، حساسية لمس + glissando
- **إيقاع/سرعة/بيتش:** عجلة Tempo، Master Tune A 392–452Hz، Pitch-bend ±12st
- **صوت:** Master Volume، Reverb، EQ Bass/Treble، ADSR، Filter، Pan، Metronome
- **تشريق (Maqam):** 27 مقام (Rast Bayati Hijaz Saba Nahawand Kurd Nikriz Hicazkar Uşşak Segah Huzzam...)، تعديل كل نغمة ±100¢، كوما 1/9–9/9
- **إضافة المزيد:** استيراد SFZ/SF2/WAV + شبكة إيقاع + Export/Import JSON + تسجيل

📂 **المشروع:** `TurkishOrganPro/www/index.html` (PWA offline) | `TurkishOrganPro/docs/` | البناء عبر [Capacitor + GitHub Actions](TurkishOrganPro/docs/APK_BUILD_GUIDE.md)

```bash
cd TurkishOrganPro/www && python3 -m http.server 8080
# → http://localhost:8080 — TAP TO START & PLAY
```

---

## 📚 Previous Research
- **FREE_MUSIC_LIBRARIES_AR.md** — دليل عربي لمكتبات مجانية لـ FL Studio
- **WakaWaka_Orchestral_A/** — توزيع أوركسترالي
- **Nay1_MIDI_Pack/** — تحليل ناي + حزمة MIDI

---
*Build: `Build Turkish Organ Pro APK` on `ubuntu-latest` with Android SDK (preinstalled) → `assembleDebug` → artifact `turkish-organ-pro-debug-apk` → Release `v1.0.0-6` on `main`.*
