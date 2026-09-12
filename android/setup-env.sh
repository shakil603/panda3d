#!/usr/bin/env bash
#
# setup-env.sh — Install everything needed to build the Panda3D Android APK
# on a Linux machine (Ubuntu/Debian).  Safe to re-run; it only installs
# things that are missing.
#
# What it installs:
#   * JDK 17 (javac, keytool)
#   * CMake, Ninja, yasm (for the thirdparty package build)
#   * uv + CPython 3.13 (host Python used by makepanda; its major.minor must
#     match the target Python version, because the APK assembler copies the
#     host standard library into the APK)
#   * Android SDK: platforms;android-21, build-tools 34, NDK r29
#   * CPython 3.13.9 cross-compiled for Android (into ~/python-prefix)
#
# Usage:  bash setup-env.sh [arm64-v8a|armeabi-v7a]     (default: arm64-v8a)
#
# When done it writes android/build-env.sh, which build_apk.sh sources.
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

# ---- Configuration (override via environment) --------------------------------
ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$HOME/android-sdk}"
NDK_VERSION="${NDK_VERSION:-29.0.14206865}"        # NDK r29
ANDROID_API="${ANDROID_API:-21}"                    # minimum API level
BUILD_TOOLS_VERSION="${BUILD_TOOLS_VERSION:-34.0.0}"
HOST_PYTHON_VERSION="${HOST_PYTHON_VERSION:-3.13}"  # must match TARGET_PYTHON
TARGET_PYTHON_VERSION="${TARGET_PYTHON_VERSION:-3.13.9}"
PYTHON_PREFIX="${PYTHON_PREFIX:-$HOME/python-prefix}"
ABI="${1:-arm64-v8a}"

have() { command -v "$1" >/dev/null 2>&1; }
SUDO=""
[ "$(id -u)" != "0" ] && SUDO="sudo"

# ---- 1. Base system packages ---------------------------------------------------
if ! have javac || ! have cmake || ! have yasm || ! have ninja; then
    echo "==> Installing system packages (JDK 17, cmake, ninja, yasm) ..."
    if ! $SUDO apt-get update -qq; then
        # Some restricted networks only allow HTTPS mirrors.
        echo "    apt over HTTP failed; retrying with HTTPS mirrors ..."
        if [ -f /etc/apt/sources.list.d/debian.sources ]; then
            $SUDO sed -i 's|URIs: http://|URIs: https://|' /etc/apt/sources.list.d/debian.sources
        fi
        [ -f /etc/apt/sources.list ] && $SUDO sed -i 's|^deb http://|deb https://|' /etc/apt/sources.list
        $SUDO apt-get update -qq
    fi
    $SUDO apt-get install -y -qq \
        openjdk-17-jdk-headless \
        cmake ninja-build yasm unzip wget curl ca-certificates || true
fi
export JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/java-17-openjdk-amd64}"
echo "    javac:  $(javac -version 2>&1 || echo MISSING)"
echo "    cmake:  $(cmake --version 2>/dev/null | head -1 || echo MISSING)"

# ---- 2. Host Python 3.13 (via uv) ----------------------------------------------
export PATH="$HOME/.local/bin:$PATH"
if ! have uv; then
    echo "==> Installing uv (fast standalone Python manager) ..."
    curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null
fi
HOST_PY="$(uv python find "$HOST_PYTHON_VERSION" 2>/dev/null || true)"
if [ -z "$HOST_PY" ]; then
    echo "==> Installing CPython $HOST_PYTHON_VERSION for the host (via uv) ..."
    uv python install "$HOST_PYTHON_VERSION" >/dev/null
    HOST_PY="$(uv python find "$HOST_PYTHON_VERSION")"
fi
echo "    host python: $HOST_PY ($("$HOST_PY" --version 2>&1))"

# ---- 3. Android SDK / NDK -------------------------------------------------------
SDKMGR="$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager"
if [ ! -x "$SDKMGR" ]; then
    echo "==> Downloading Android SDK command-line tools ..."
    mkdir -p "$ANDROID_SDK_ROOT/cmdline-tools"
    cd /tmp
    wget -q https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
    unzip -q -o commandlinetools-linux-11076708_latest.zip
    rm -rf "$ANDROID_SDK_ROOT/cmdline-tools/latest"
    mv cmdline-tools "$ANDROID_SDK_ROOT/cmdline-tools/latest"
    cd - >/dev/null
fi

echo "==> Accepting Android SDK licenses ..."
(yes | "$SDKMGR" --licenses) >/dev/null 2>&1 || true

install_if_missing() {
    local pkg="$1"
    case "$pkg" in
        "platforms;android-"*)
            [ -f "$ANDROID_SDK_ROOT/$pkg/android.jar" ] && return 0 ;;
        "build-tools;"*)
            [ -d "$ANDROID_SDK_ROOT/$pkg" ] && return 0 ;;
        "ndk;"*)
            [ -d "$ANDROID_SDK_ROOT/ndk/${pkg#ndk;}" ] && return 0 ;;
        "platform-tools")
            [ -d "$ANDROID_SDK_ROOT/platform-tools" ] && return 0 ;;
        *)
            return 0 ;;
    esac
    echo "==> Installing $pkg ..."
    "$SDKMGR" --install "$pkg" >/dev/null
}

install_if_missing "platforms;android-$ANDROID_API"
install_if_missing "build-tools;$BUILD_TOOLS_VERSION"
install_if_missing "ndk;$NDK_VERSION"
install_if_missing "platform-tools"

NDK_ROOT="$ANDROID_SDK_ROOT/ndk/$NDK_VERSION"
[ -d "$NDK_ROOT" ] || { echo "ERROR: NDK not found at $NDK_ROOT" >&2; exit 1; }
echo "    NDK: $NDK_ROOT"

# ---- 4. Cross-compiled CPython for Android --------------------------------------
if [ "$ABI" = "arm64-v8a" ]; then
    TRIPLE="aarch64-linux-android"
elif [ "$ABI" = "armeabi-v7a" ]; then
    TRIPLE="arm-linux-androideabi"
else
    echo "ERROR: unsupported ABI $ABI (use arm64-v8a or armeabi-v7a)" >&2
    exit 1
fi

if [ ! -d "$PYTHON_PREFIX/lib/python${TARGET_PYTHON_VERSION%.*}" ]; then
    echo "==> Cross-compiling CPython $TARGET_PYTHON_VERSION for $TRIPLE (a few minutes) ..."
    cd /tmp
    [ -f "Python-$TARGET_PYTHON_VERSION.tar.xz" ] || \
        wget -q "https://www.python.org/ftp/python/$TARGET_PYTHON_VERSION/Python-$TARGET_PYTHON_VERSION.tar.xz"
    rm -rf "Python-$TARGET_PYTHON_VERSION"
    tar -xJf "Python-$TARGET_PYTHON_VERSION.tar.xz"
    sed -i.bak "s/aarch64-linux-android/${TRIPLE}/" "Python-$TARGET_PYTHON_VERSION/Android/android.py"
    sed -i.bak "s/ndk_version=[0-9.]\{1,\}/ndk_version=$NDK_VERSION/" "Python-$TARGET_PYTHON_VERSION/Android/android-env.sh"
    (cd "Python-$TARGET_PYTHON_VERSION/Android" && ANDROID_HOME="$ANDROID_SDK_ROOT" python3 android.py build "$TRIPLE")
    rm -rf "$PYTHON_PREFIX"
    cp -R "Python-$TARGET_PYTHON_VERSION/cross-build/$TRIPLE/prefix" "$PYTHON_PREFIX"
    rm -rf "Python-$TARGET_PYTHON_VERSION"
else
    echo "==> CPython prefix already present at $PYTHON_PREFIX"
fi
echo "    python prefix: $PYTHON_PREFIX"

# ---- Done ------------------------------------------------------------------------
cat > "$HERE/build-env.sh" <<EOF
# Generated by setup-env.sh — do not edit by hand.
export ANDROID_SDK_ROOT="$ANDROID_SDK_ROOT"
export ANDROID_NDK_ROOT="$NDK_ROOT"
export PYTHON_PREFIX="$PYTHON_PREFIX"
export JAVA_HOME="$JAVA_HOME"
export HOST_PYTHON_VERSION="$HOST_PYTHON_VERSION"
export TARGET_PYTHON_VERSION="$TARGET_PYTHON_VERSION"
export NDK_VERSION="$NDK_VERSION"
export ANDROID_API="$ANDROID_API"
export BUILD_TOOLS_VERSION="$BUILD_TOOLS_VERSION"
EOF

echo
echo "Android build environment is ready."
echo "  ANDROID_SDK_ROOT=$ANDROID_SDK_ROOT"
echo "  ANDROID_NDK_ROOT=$NDK_ROOT"
echo "  PYTHON_PREFIX   =$PYTHON_PREFIX"
echo
echo "Now build the APK with:  bash $HERE/build_apk.sh [arm64-v8a|armeabi-v7a|all]"
