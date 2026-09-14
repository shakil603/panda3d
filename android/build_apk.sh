#!/usr/bin/env bash
#
# build_apk.sh — Build the Panda3D Android APK end-to-end on Linux.
#
#   bash build_apk.sh              # build arm64-v8a (64-bit phones, default)
#   bash build_apk.sh arm64-v8a    # same, explicitly
#   bash build_apk.sh armeabi-v7a  # 32-bit phones
#   bash build_apk.sh all          # both ABIs + a "universal" APK with both
#
# Prerequisites: run  bash setup-env.sh  once (JDK 17, CMake, NDK, SDK, CPython).
#
# Result:  dist/panda3d-<version>-<abi>.apk   (plus -universal.apk for "all")
#
# The APK contains two launcher apps:
#   * "Panda Viewer"  — opens .egg/.bam 3D models (or shows the default model)
#   * "Panda Python"  — runs a .py script; launched without a file it runs the
#                       bundled demo (android/default_app.py)
#
# Optional release signing (otherwise a generated debug key is used):
#   KEYSTORE=my.keystore KEYSTORE_PASS=... KEY_ALIAS=... KEY_PASS=... bash build_apk.sh
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
cd "$ROOT"

# Pick up the environment produced by setup-env.sh (if present).
if [ -f "$HERE/build-env.sh" ]; then
    # shellcheck disable=SC1091
    . "$HERE/build-env.sh"
fi

# ---- Configuration -------------------------------------------------------------
ANDROID_API="${ANDROID_API:-21}"
NDK_VERSION="${NDK_VERSION:-29.0.14206865}"
BUILD_TOOLS_VERSION="${BUILD_TOOLS_VERSION:-34.0.0}"
TARGET_PYTHON_VERSION="${TARGET_PYTHON_VERSION:-3.13.9}"
BUILD_THREADS="${BUILD_THREADS:-$(nproc)}"

# Thirdparty repo (prebuilt cross-compiled support libraries for Panda3D).
THIRDPARTY_REPO="${THIRDPARTY_REPO:-https://github.com/rdb/panda3d-thirdparty.git}"
THIRDPARTY_REV="${THIRDPARTY_REV:-935c80380ca171e08587c570e9dad678d29db3c8}"

# The host Python that runs makepanda must match the target Python version
# (3.13.x) — setup-env.sh installs it via uv.
find_host_python() {
    local uv
    for uv in "$HOME/.local/bin/uv" "$(command -v uv 2>/dev/null || true)"; do
        [ -n "$uv" ] && [ -x "$uv" ] || continue
        local py
        py="$("$uv" python find 3.13 2>/dev/null || true)"
        if [ -n "$py" ] && [ -x "$py" ]; then
            echo "$py"
            return 0
        fi
    done
    command -v python3.13 || true
}

ABI="${1:-arm64-v8a}"

# ---- Sanity checks --------------------------------------------------------------
HOST_PY="${HOST_PY:-$(find_host_python)}"
[ -n "$HOST_PY" ] && [ -x "$HOST_PY" ] || {
    echo "ERROR: cannot find a 3.13 host Python. Run: bash $HERE/setup-env.sh" >&2
    exit 1
}
[ -d "$ANDROID_SDK_ROOT" ]  || { echo "ERROR: ANDROID_SDK_ROOT missing. Run: bash $HERE/setup-env.sh" >&2; exit 1; }
[ -d "$ANDROID_NDK_ROOT" ]  || { echo "ERROR: ANDROID_NDK_ROOT missing. Run: bash $HERE/setup-env.sh" >&2; exit 1; }
[ -d "$PYTHON_PREFIX" ]     || { echo "ERROR: PYTHON_PREFIX missing. Run: bash $HERE/setup-env.sh" >&2; exit 1; }

export ANDROID_NDK_ROOT
export JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/java-17-openjdk-amd64}"

# aapt / zipalign / d8 / apksigner come from build-tools.
BUILD_TOOLS_DIR="$ANDROID_SDK_ROOT/build-tools/$BUILD_TOOLS_VERSION"
[ -d "$BUILD_TOOLS_DIR" ] || { echo "ERROR: build-tools $BUILD_TOOLS_VERSION not found under $ANDROID_SDK_ROOT" >&2; exit 1; }
export PATH="$BUILD_TOOLS_DIR:$PATH"

VERSION="$("$HOST_PY" -c "
import re
for line in open('setup.cfg'):
    m = re.match(r'^version\s*=\s*(\S+)', line)
    if m: print(m.group(1)); break
")"
DIST="$ROOT/dist"
mkdir -p "$DIST"

# ---- ABI helpers ------------------------------------------------------------------
makepanda_arch() {  # what --arch expects
    case "$1" in
        arm64-v8a)   echo "arm64" ;;
        armeabi-v7a) echo "armv7a" ;;
        *) echo "ERROR: unsupported ABI $1 (use arm64-v8a or armeabi-v7a)" >&2; return 1 ;;
    esac
}
cmake_arch() {  # what CMAKE_ANDROID_ARCH expects
    case "$1" in
        arm64-v8a)   echo "arm64" ;;
        armeabi-v7a) echo "arm" ;;
        *) return 1 ;;
    esac
}

# ---- One full Panda3D build for a single ABI ---------------------------------------
build_abi() {
    local abi="$1" tpdir outdir arch
    arch="$(makepanda_arch "$abi")"
    tpdir="$ROOT/thirdparty-$abi"
    outdir="$ROOT/built-android-$abi"

    echo "==================================================================="
    echo "==> [$abi] Thirdparty support libraries"
    if [ ! -f "$tpdir/.built-$abi" ]; then
        rm -rf "$tpdir"
        git clone --depth=1 "$THIRDPARTY_REPO" "$tpdir"
        (cd "$tpdir" && git fetch --depth=1 origin "$THIRDPARTY_REV" && git checkout "$THIRDPARTY_REV")
        cmake -B "$tpdir/build" \
            -DCMAKE_BUILD_TYPE=Release \
            -DCMAKE_TOOLCHAIN_FILE="$ANDROID_NDK_ROOT/build/cmake/android.toolchain.cmake" \
            -DCMAKE_ANDROID_ARCH_ABI="$abi" \
            -DCMAKE_ANDROID_ARCH="$(cmake_arch "$abi")" \
            -DCMAKE_SYSTEM_VERSION="$ANDROID_API" \
            -DANDROID_ABI="$abi" \
            -DANDROID_PLATFORM=android-"$ANDROID_API" \
            -DBUILD_FCOLLADA=OFF \
            -DBUILD_OPENSSL=OFF \
            -DBUILD_VRPN=OFF \
            -DBUILD_ARTOOLKIT=OFF
        cmake --build "$tpdir/build" --config Release -j"$BUILD_THREADS"
        rm -rf "$tpdir/build"
        touch "$tpdir/.built-$abi"
    else
        echo "    (already built: $tpdir)"
    fi

    # The APK assembler looks for the cross-built CPython under
    # <thirdparty>/android-libs-<arch>/python/ — link our prefix there.
    # (thirdparty's CMake uses 'arm' for 32-bit, 'arm64' for 64-bit.)
    local tp_arch
    tp_arch="$(cmake_arch "$abi")"
    mkdir -p "$tpdir/android-libs-$tp_arch"
    ln -sfn "$PYTHON_PREFIX" "$tpdir/android-libs-$tp_arch/python"

    echo "==================================================================="
    echo "==> [$abi] Building Panda3D + APK (this is the long part) ..."
    MAKEPANDA_THIRDPARTY="$tpdir" "$HOST_PY" makepanda/makepanda.py \
        --git-commit="$(git rev-parse HEAD 2>/dev/null || echo local)" \
        --target "android-$ANDROID_API" \
        --arch "$arch" \
        --python-incdir="$PYTHON_PREFIX/include" \
        --python-libdir="$PYTHON_PREFIX/lib" \
        --outputdir="$outdir" \
        --everything \
        --no-openssl --no-tinydisplay --no-pandatool \
        --installer \
        --threads="$BUILD_THREADS"

    [ -f "$ROOT/panda3d.apk" ] || { echo "ERROR: panda3d.apk was not produced" >&2; exit 1; }
    mv "$ROOT/panda3d.apk" "$DIST/panda3d-$VERSION-$abi.apk"
    rm -rf "$ROOT/apkroot"
    echo "==> [$abi] APK ready: dist/panda3d-$VERSION-$abi.apk"
}

# ---- Release signing (optional) -----------------------------------------------------
sign_release() {
    local apk="$1"
    if [ -n "${KEYSTORE:-}" ]; then
        echo "==> Signing with $KEYSTORE ..."
        apksigner sign \
            --ks "$KEYSTORE" \
            --ks-pass "pass:${KEYSTORE_PASS:?KEYSTORE_PASS required}" \
            --ks-key-alias "${KEY_ALIAS:?KEY_ALIAS required}" \
            --key-pass "pass:${KEY_PASS:?KEY_PASS required}" \
            --min-sdk-version "$ANDROID_API" \
            --out "$apk.tmp" "$apk"
        mv "$apk.tmp" "$apk"
    fi
}

# ---- Merge two single-ABI APKs into one universal APK ------------------------------
merge_universal() {
    local base="$1" extra_abi="$2" work
    [ -f "$DIST/panda3d-$VERSION-$extra_abi.apk" ] || return 0
    work="$(mktemp -d)"
    echo "==================================================================="
    echo "==> Merging $base + $extra_abi into a universal APK ..."
    cp "$DIST/panda3d-$VERSION-$base.apk" "$DIST/panda3d-$VERSION-universal.apk"
    (cd "$work" && unzip -q -o "$DIST/panda3d-$VERSION-$extra_abi.apk" "lib/$extra_abi/*")
    # Inject the extra libraries (stored uncompressed, as required for .so).
    (cd "$work" && zip -q -r -X -0 "$DIST/panda3d-$VERSION-universal.apk" "lib/$extra_abi")
    rm -rf "$work"
    # Modifying an APK breaks alignment and signature: redo both.
    zipalign -f -p 4 "$DIST/panda3d-$VERSION-universal.apk" "$DIST/tmp-align.apk"
    if [ ! -f "$ROOT/debug.ks" ]; then
        keytool -genkey -noprompt -dname CN=Panda3D,O=Panda3D,C=US \
            -keystore debug.ks -storepass android -alias androiddebugkey \
            -keypass android -keyalg RSA -keysize 2048 -validity 1000
    fi
    apksigner sign --ks debug.ks --ks-pass pass:android \
        --min-sdk-version "$ANDROID_API" \
        --out "$DIST/panda3d-$VERSION-universal.apk" "$DIST/tmp-align.apk"
    rm -f "$DIST/tmp-align.apk"
    sign_release "$DIST/panda3d-$VERSION-universal.apk"
    echo "==> Universal APK ready: dist/panda3d-$VERSION-universal.apk"
}

# ---- Main ---------------------------------------------------------------------------
case "$ABI" in
    arm64-v8a|armeabi-v7a)
        build_abi "$ABI"
        sign_release "$DIST/panda3d-$VERSION-$ABI.apk"
        ;;
    all)
        build_abi arm64-v8a
        build_abi armeabi-v7a
        merge_universal arm64-v8a armeabi-v7a
        sign_release "$DIST/panda3d-$VERSION-arm64-v8a.apk"
        sign_release "$DIST/panda3d-$VERSION-armeabi-v7a.apk"
        ;;
    *)
        echo "Usage: bash build_apk.sh [arm64-v8a|armeabi-v7a|all]" >&2
        exit 1
        ;;
esac

echo
echo "==================================================================="
echo "Done. APK(s) in $DIST :"
ls -lh "$DIST"/*.apk 2>/dev/null || true
