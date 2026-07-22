#!/usr/bin/env bash
# Manual APK build (no gradle — friendly to low-RAM servers).
set -euo pipefail

SDK=/opt/android-sdk
BT=$SDK/build-tools/34.0.0
PLATFORM=$SDK/platforms/android-34/android.jar
ROOT="$(cd "$(dirname "$0")" && pwd)"
BUILD=$ROOT/build
KEYSTORE=$ROOT/nihongoquest.keystore
KS_PASS=nihongoquest-release

rm -rf "$BUILD"
mkdir -p "$BUILD/obj" "$BUILD/dex" "$BUILD/compiled"

echo "==> 1/6 aapt2 compile resources"
"$BT/aapt2" compile --dir "$ROOT/res" -o "$BUILD/compiled/res.zip"

echo "==> 2/6 aapt2 link"
"$BT/aapt2" link \
  -I "$PLATFORM" \
  --manifest "$ROOT/AndroidManifest.xml" \
  -o "$BUILD/base.apk" \
  "$BUILD/compiled/res.zip" \
  --auto-add-overlay

echo "==> 3/6 javac"
javac -source 8 -target 8 -Xlint:-options \
  -bootclasspath "$PLATFORM" -classpath "$PLATFORM" \
  -d "$BUILD/obj" \
  "$ROOT"/java/com/nihongoquest/app/*.java

echo "==> 4/6 d8 (dex)"
"$BT/d8" --release --lib "$PLATFORM" --min-api 24 \
  --output "$BUILD/dex" \
  $(find "$BUILD/obj" -name '*.class')
(cd "$BUILD/dex" && zip -qu ../base.apk classes.dex)

echo "==> 5/6 zipalign"
"$BT/zipalign" -f 4 "$BUILD/base.apk" "$BUILD/aligned.apk"

echo "==> 6/6 sign"
if [ ! -f "$KEYSTORE" ]; then
  keytool -genkeypair -v -keystore "$KEYSTORE" -alias nihongoquest \
    -keyalg RSA -keysize 2048 -validity 10000 \
    -storepass "$KS_PASS" -keypass "$KS_PASS" \
    -dname "CN=NihongoQuest, OU=Dev, O=NihongoQuest, L=Internet, C=JP" >/dev/null 2>&1
fi
"$BT/apksigner" sign --ks "$KEYSTORE" --ks-pass "pass:$KS_PASS" \
  --key-pass "pass:$KS_PASS" \
  --out "$BUILD/NihongoQuest.apk" "$BUILD/aligned.apk"
"$BT/apksigner" verify "$BUILD/NihongoQuest.apk"

ls -lh "$BUILD/NihongoQuest.apk"
echo "APK ready: $BUILD/NihongoQuest.apk"
