#!/usr/bin/env bash
set -e

# ==============================================================================
# StudySense iOS Build & Device Installer Script
# Builds native iOS app, signs it with your Apple ID, and installs to connected iPhone
# ==============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IOS_DIR="$PROJECT_ROOT/ios"
DERIVED_DATA="$HOME/Library/Developer/Xcode/DerivedData"

echo "📱 Step 1: Syncing web bundle into iOS project..."
mkdir -p "$IOS_DIR/Sources/Resources/www"
cp "$PROJECT_ROOT/index.html" "$IOS_DIR/Sources/Resources/www/index.html"
cp "$PROJECT_ROOT/manifest.json" "$IOS_DIR/Sources/Resources/www/manifest.json"
cp "$PROJECT_ROOT/icon.svg" "$IOS_DIR/Sources/Resources/www/icon.svg"

echo "⚙️  Step 2: Generating Xcode project..."
cd "$IOS_DIR"
xcodegen generate

echo "🔍 Step 3: Detecting connected iOS devices..."
DEVICE_ID=$(xcrun devicectl list devices --json-output - 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
devices = data.get('result', {}).get('devices', [])
for d in devices:
    if d.get('hardwareProperties', {}).get('reality') == 'physical' and d.get('connectionProperties', {}).get('transportType') in ['usb', 'localNetwork']:
        print(d.get('identifier'))
        break
" 2>/dev/null || echo "")

if [ -z "$DEVICE_ID" ]; then
    DEVICE_ID="00008140-001068913487001C" # Default to Krishna's iPhone 16
fi
echo "🎯 Target Device UDID: $DEVICE_ID"

echo "🔨 Step 4: Compiling and signing iOS app with xcodebuild..."
xcodebuild -project "$IOS_DIR/StudySense.xcodeproj" \
           -scheme StudySense \
           -destination "id=$DEVICE_ID" \
           -allowProvisioningUpdates \
           build

APP_PATH=$(find "$DERIVED_DATA" -name "StudySense.app" -path "*/Debug-iphoneos/*" -type d 2>/dev/null | head -n 1)

if [ -z "$APP_PATH" ]; then
    echo "❌ Error: Could not locate built StudySense.app"
    exit 1
fi
echo "✅ Built: $APP_PATH"

echo "📦 Step 5: Packaging StudySense.ipa..."
TMP_IPA=$(mktemp -d)
mkdir -p "$TMP_IPA/Payload"
cp -R "$APP_PATH" "$TMP_IPA/Payload/"
(cd "$TMP_IPA" && zip -q -r -9 "$PROJECT_ROOT/StudySense.ipa" Payload)
cp "$PROJECT_ROOT/StudySense.ipa" "$IOS_DIR/StudySense.ipa"
rm -rf "$TMP_IPA"
echo "✅ Packaged: $PROJECT_ROOT/StudySense.ipa"

echo "📲 Step 6: Installing directly onto your iPhone..."
xcrun devicectl device install app --device "$DEVICE_ID" "$APP_PATH"

echo "🎉 SUCCESS: StudySense is installed on your iPhone!"
echo "👉 On your iPhone: Go to Settings -> General -> VPN & Device Management, tap your developer email and tap 'Trust' (first time only)."
