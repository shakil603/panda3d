# Panda3D — Android APK বিল্ড সেটআপ

এই ফোল্ডারটি Panda3D প্রোজেক্টকে **অ্যান্ড্রয়েডে চলার জন্য সম্পূর্ণ প্রস্তুত** করেছে এবং
APK **স্বয়ংক্রিয়ভাবে (অটোমেটিক) বিল্ড হওয়ার** সমস্ত ব্যবস্থা যোগ করেছে।

## 📦 APK-তে যা থাকবে

বিল্ড করা APK-তে **একটি অ্যাপ** থাকবে: **Panda3D Studio** — ফোনেই 3D গেম
বানানোর পুরো টুল।

| ভেতরের ফিচার | কাজ |
|---|---|
| **Sample Games** | বান্ডেল করা রেডিমেড 3D গেম (ঘুরন্ত পান্ডা, Star Catcher, Teapot Tour) — ট্যাপ করেই খেলা যায়। |
| **My Games** | নিজের গেম: অ্যাপের ভেতরের **কোড এডিটর**-এ Python লিখে Save, তারপর এক ট্যাপে Run। |
| **3D Models** | বান্ডেল করা `.egg` মডেল 3D-তে দেখা (drag করে ঘোরানো যায়)। |

ভেতরে থাকে: সম্পূর্ণ Panda3D ইঞ্জিন (C++), cross-compiled **CPython 3.13**,
DirectGUI, Panda Viewer (`.egg`/`.bam` দেখায়) এবং Panda Python রানার
(`.py` চালায়)। ফাইল ম্যানেজার থেকে `.egg`/`.bam`/`.py` ফাইল খুলেও চালাতে পারবেন
("Open with")। ফোনে কিছুই আলাদা ইনস্টল করতে হয় না।

APK-র ভেতরে সম্পূর্ণ Panda3D ইঞ্জিন (C++ লাইব্রেরি), Cross-compiled **CPython 3.13**,
DirectGUI, সাপোর্ট লাইব্রেরি (bullet, freeimage ইত্যাদি), মডেল ও কনফিগ ফাইল — সবকিছুই থাকে।
ফোনে কিছুই ইনস্টল করতে হয় না।

## 🚀 গিটহাব অ্যাকশনে অটোমেটিক বিল্ড (প্রধান উপায়)

`.github/workflows/android-apk.yml` ওয়ার্কফ্লো যোগ করা আছে। এখন থেকে:

- **push / pull-request** → GitHub Actions নিজে থেকেই APK বিল্ড করবে
  (arm64-v8a + armeabi-v7a + universal) এবং **Artifacts** এ আপলোড করবে।
- **ট্যাগ (v1.0.0 ইত্যাদি)** → APK গুলো GitHub **Release**-এও যুক্ত হবে।
- চাইলে **Actions** ট্যাব থেকে হাতে (workflow_dispatch)ও চালানো যায়।

APK নিতে: GitHub repo → **Actions** → "Android APK" run → শেষে **Artifacts** →
`panda3d-apk-arm64-v8a` / `panda3d-apk-armeabi-v7a` / `panda3d-apk-universal` ডাউনলোড করুন।

> ট্যাগ দিলে (যেমন `git tag v1.0.0 && git push origin v1.0.0`) রিলিজের সাথে
> `panda3d-<version>-arm64-v8a.apk`, `panda3d-<version>-armeabi-v7a.apk` এবং
> `panda3d-<version>-universal.apk` আটচান করা হবে।

## 💻 লোকাল মেশিনে বিল্ড (Linux)

একটাই দুই-টি ধাপ:

```bash
# ১. একবারই প্রি-রিকোজাইট ইনস্টল করবে (JDK 17, CMake, Android SDK, NDK r29, CPython 3.13)
bash android/setup-env.sh

# ২. APK বিল্ড
bash android/build_apk.sh            # arm64-v8a (64-bit ফোন) — ডিফল্ট
bash android/build_apk.sh armeabi-v7a# 32-bit ফোন
bash android/build_apk.sh all        # দুটো ABI + universal APK
```

বিল্ড শেষে APK থাকবে: **`dist/panda3d-<version>-<abi>.apk`** (universal হলে
`dist/panda3d-<version>-universal.apk`)।

### ফোনে ইনস্টল

1. ফোনে **USB debugging** চালু করুন, অথবা APK ফাইলটি ফোনে পাঠান।
2. `adb install dist/panda3d-<version>-arm64-v8a.apk` (অথবা ফোনে ট্যাপ করে ইনস্টল)।
3. **"Panda Python"** আইকনে ট্যাপ করলেই ডেমো চলে! (ESC/ব্যাক = বের হওয়া)

### নিজের গেম/অ্যাপ রান করা

**সবচেয়ে সহজ উপায়**: Panda3D Studio → **My Games** → **"+ New Game"** →
অ্যাপের ভেতরের এডিটরে কোড লিখুন → **Save** → **Run**। গেমের ফাইল অ্যাপের
ভেতরেই সেভ হয়।

অথবা বাইরের `.py` ফাইল চালাতে — ফাইল ম্যানেজার থেকে "Open with" →
Panda Python। অথবা `adb` দিয়ে:

```bash
adb push my_game.py /sdcard/Download/
adb shell am start -a android.intent.action.VIEW -d "file:///sdcard/Download/my_game.py" -t "text/x-python"
```

### রিলিজ (release) সাইনিং

ডিফল্টে ডিবাগ কী দিয়ে সাইন হয় (সাইডলোড করার জন্য যথেষ্ট)। নিজের keystore দিয়ে সাইন করতে:

```bash
KEYSTORE=my.keystore KEYSTORE_PASS=*** KEY_ALIAS=mykey KEY_PASS=*** \
    bash android/build_apk.sh all
```

## ⚙️ বিল্ড কিভাবে কাজ করে

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. CPython 3.13.9  →  NDK দিয়ে cross-compile (arm64/armv7)      │
│ 2. panda3d-thirdparty → CMake+NDK দিয়ে support libs (bullet ...) │
│ 3. makepanda.py --target android-21 --installer                  │
│      ├─ Panda3D C++ ইঞ্জিন cross-compile (NDK clang)             │
│      ├─ Python মডিউল + Direct + সাইট-প্যাকেজ                      │
│      ├─ Java অ্যাক্টিভিটি → classes.dex (javac + d8)              │
│      └─ aapt + zipalign + apksigner → panda3d.apk                │
└─────────────────────────────────────────────────────────────────┘
```

### কাস্টমাইজ

| যা বদলাতে চান | কোথায় |
|---|---|
| ডিফল্ট ডেমো অ্যাপ | `android/default_app.py` (APK-র asset হিসেবে বান্ডেল হয়) |
| অ্যাপের নাম / icon / permission | `panda/src/android/pview_manifest.xml` |
| API level, NDK version | `android/build_apk.sh` ও `setup-env.sh`-এর উপরের কনফিগ ব্লক (CI-তে `.github/workflows/android-apk.yml`-এর `env:`) |
| নিজের ফোন অ্যাপ (পাণ্ডার প্রোজেক্ট) | `android/default_app.py`-তে নিজের Panda3D কোড লিখে ফেলুন — APK সেই ডিফল্ট অ্যাপ চালাবে |

### নোটিশ

- **API level 21+** (Android 5.0+) সাপোর্ট করে, **minSdk=21**।
- CI-তে একেবারে প্রথম বিল্ড ~৪০–৬০ মিনিট লাগে; এরপর ক্যাশ থাকায় অনেক দ্রুত।
- lollipop-era পুরনো ফোনে 32-bit ARM-এর জন্য `armeabi-v7a` বা `universal` APK ব্যবহার করুন।

---

## English summary

- **Automatic APK builds**: `.github/workflows/android-apk.yml` builds arm64-v8a,
  armeabi-v7a and a universal APK on every push/PR; on `v*` tags the APKs are
  attached to the GitHub release.
- **Local builds (Linux)**: `bash android/setup-env.sh` once, then
  `bash android/build_apk.sh [arm64-v8a|armeabi-v7a|all]` → `dist/*.apk`.
- The APK ships a single **Panda3D Studio** app: sample games, an in-app
  Python game editor with one-tap run, and a 3D model viewer.  The Panda
  Viewer (opens .egg/.bam) and Panda Python runner (opens .py; with no file
  it runs the bundled demo `android/default_app.py`) stay available for
  "Open with" intents from a file manager.
- The Studio UI lives in `panda/src/android/studio/`, sample games in
  `android/studio/games/`, and the launcher icon is generated by
  `android/studio/make_icon.py`.
- Release signing via `KEYSTORE/KEYSTORE_PASS/KEY_ALIAS/KEY_PASS` env vars.
