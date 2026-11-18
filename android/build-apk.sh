#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ANDROID_DIR="$ROOT_DIR/android"
SDK_DIR="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
BUILD_TOOLS="$(ls -d "$SDK_DIR"/build-tools/* | sort -V | tail -n 1)"
PLATFORM_JAR="$(ls -d "$SDK_DIR"/platforms/android-*/android.jar | sort -V | tail -n 1)"

BUILD_DIR="$ANDROID_DIR/build"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/compiled-res" "$BUILD_DIR/gen" "$BUILD_DIR/classes" "$BUILD_DIR/dex" "$BUILD_DIR/assets"

# Bundle the exact same web app inside the Android APK
cp "$ROOT_DIR/index.html" "$BUILD_DIR/assets/index.html"

# 1. Compile Android resources
"$BUILD_TOOLS/aapt2" compile --dir "$ANDROID_DIR/res" -o "$BUILD_DIR/compiled-res/resources.zip"

# 2. Link resources + AndroidManifest + assets into base APK
"$BUILD_TOOLS/aapt2" link \
  -I "$PLATFORM_JAR" \
  --manifest "$ANDROID_DIR/AndroidManifest.xml" \
  -A "$BUILD_DIR/assets" \
  --java "$BUILD_DIR/gen" \
  -o "$BUILD_DIR/unsigned.apk" \
  "$BUILD_DIR/compiled-res/resources.zip"

# 3. Compile Java sources
javac --release 11 \
  -cp "$PLATFORM_JAR" \
  -d "$BUILD_DIR/classes" \
  "$ANDROID_DIR/src/com/studysense/app/MainActivity.java" \
  "$BUILD_DIR/gen/com/studysense/app/R.java"

# 4. Convert .class files to classes.dex (space-safe)
find "$BUILD_DIR/classes" -name "*.class" -exec \
  "$BUILD_TOOLS/d8" --lib "$PLATFORM_JAR" --min-api 24 --output "$BUILD_DIR/dex" {} +

# 5. Add classes.dex into the APK
(cd "$BUILD_DIR/dex" && zip -q -u "$BUILD_DIR/unsigned.apk" classes.dex)

# 6. Align APK
"$BUILD_TOOLS/zipalign" -f -p 4 "$BUILD_DIR/unsigned.apk" "$BUILD_DIR/aligned.apk"

# 7. Sign APK (reuses ~/.android/studysense.keystore or creates one automatically)
KEYSTORE="$HOME/.android/studysense.keystore"
mkdir -p "$(dirname "$KEYSTORE")"
if [ ! -f "$KEYSTORE" ]; then
  keytool -genkeypair -v \
    -keystore "$KEYSTORE" \
    -alias studysense \
    -keyalg RSA -keysize 2048 -validity 10000 \
    -storepass studysense123 -keypass studysense123 \
    -dname "CN=StudySense, OU=App, O=StudySense, L=Local, ST=Local, C=IN" >/dev/null 2>&1
fi

"$BUILD_TOOLS/apksigner" sign \
  --ks "$KEYSTORE" \
  --ks-key-alias studysense \
  --ks-pass pass:studysense123 \
  --key-pass pass:studysense123 \
  --out "$ROOT_DIR/StudySense.apk" \
  "$BUILD_DIR/aligned.apk"

"$BUILD_TOOLS/apksigner" verify --verbose "$ROOT_DIR/StudySense.apk"
rm -rf "$BUILD_DIR" "$ROOT_DIR/StudySense.apk.idsig"
echo "Built & verified: $ROOT_DIR/StudySense.apk"
