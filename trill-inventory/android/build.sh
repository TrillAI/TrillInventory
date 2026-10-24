#!/usr/bin/env bash
# ---------------------------------------------------------------
# Harry's Scan — APK build
#   aapt2 -> javac -> d8 -> zip -> zipalign -> apksigner
# No Gradle needed; only build-tools + platform + a JDK.
# ---------------------------------------------------------------
set -euo pipefail

export JAVA_HOME="${JAVA_HOME:-/usr/local/jdk17}"
export PATH="$JAVA_HOME/bin:$PATH"
SDK="${ANDROID_SDK_ROOT:-/usr/local/android-sdk}"
BT="$SDK/build-tools/34.0.0"
PLATFORM="$SDK/platforms/android-34/android.jar"

ROOT="$(cd "$(dirname "$0")" && pwd)"
WEB="$ROOT/.."                       # the web app lives one level up
BUILD="$ROOT/build"
KS="$ROOT/harrys-release.jks"
OUT_APK="$WEB/TrillInventory-1.20.0.apk"

KEYPASS="harrys2026"
ALIAS="harrys"

echo "==> cleaning"
rm -rf "$BUILD"
mkdir -p "$BUILD/res" "$BUILD/gen" "$BUILD/classes" "$BUILD/dex" "$ROOT/assets/www"

echo "==> staging web assets"
python3 - "$WEB/index.html" "$ROOT/assets/www/index.html" <<'PY'
import sys
src, dst = sys.argv[1], sys.argv[2]
html = open(src, encoding='utf-8').read()
tag = '<script src="jsnes.min.js"></script>\n<script src="zxing.min.js"></script>\n'
i = html.rfind('<script>')
assert i != -1, "main script tag not found"
out = html[:i] + tag + html[i:]
open(dst, 'w', encoding='utf-8').write(out)
print("   injected jsnes + ZXing script tags at offset", i)
PY
cp "$ROOT/vendor/zxing.min.js" "$ROOT/assets/www/zxing.min.js"
cp "$ROOT/vendor/jsnes.min.js" "$ROOT/assets/www/jsnes.min.js"
cp "$ROOT/vendor/Manrope-OFL.txt" "$ROOT/assets/www/Manrope-OFL.txt"
cp "$ROOT/vendor/Cinzel[wght].ttf" "$ROOT/assets/www/Cinzel[wght].ttf"
cp "$ROOT/vendor/Cinzel-OFL.txt" "$ROOT/assets/www/Cinzel-OFL.txt"
cp "$ROOT/vendor/PressStart2P-Regular.ttf" "$ROOT/assets/www/PressStart2P-Regular.ttf"
cp "$ROOT/vendor/PressStart2P-OFL.txt" "$ROOT/assets/www/PressStart2P-OFL.txt"
cp "$ROOT/vendor/qrcode-LICENSE.txt" "$ROOT/assets/www/qrcode-LICENSE.txt"
cp "$ROOT/vendor/remote.html" "$ROOT/assets/www/remote.html"

echo "==> aapt2 compile (resources)"
"$BT/aapt2" compile --dir "$ROOT/res" -o "$BUILD/res.zip"

echo "==> aapt2 link (manifest + assets)"
"$BT/aapt2" link \
    -o "$BUILD/unsigned.apk" \
    -I "$PLATFORM" \
    --manifest "$ROOT/AndroidManifest.xml" \
    -R "$BUILD/res.zip" \
    --java "$BUILD/gen" \
    --min-sdk-version 23 \
    --target-sdk-version 34 \
    --version-code 23 \
    --version-name 1.20.0 \
    -A "$ROOT/assets" \
    --auto-add-overlay

echo "==> javac"
find "$ROOT/src" "$BUILD/gen" -name '*.java' > "$BUILD/sources.txt"
javac -nowarn -encoding UTF-8 -source 11 -target 11 \
      -classpath "$PLATFORM" \
      -d "$BUILD/classes" \
      @"$BUILD/sources.txt"

echo "==> d8 (dex)"
"$BT/d8" --lib "$PLATFORM" --min-api 23 --output "$BUILD/dex" \
    $(find "$BUILD/classes" -name '*.class')

echo "==> packaging classes.dex"
cp "$BUILD/unsigned.apk" "$BUILD/withdex.apk"
( cd "$BUILD/dex" && zip -q "$BUILD/withdex.apk" classes.dex )

echo "==> zipalign"
"$BT/zipalign" -f -p 4 "$BUILD/withdex.apk" "$BUILD/aligned.apk"

echo "==> signing"
if [ ! -f "$KS" ]; then
  keytool -genkeypair -keystore "$KS" -alias "$ALIAS" \
      -keyalg RSA -keysize 2048 -validity 10000 \
      -storepass "$KEYPASS" -keypass "$KEYPASS" \
      -dname "CN=Trill Inventory, OU=Store Ops, O=Harry's Gas Stations, L=Cleveland, ST=TN, C=US" >/dev/null 2>&1
  echo "   generated keystore $KS (password: $KEYPASS)"
fi
"$BT/apksigner" sign \
    --ks "$KS" --ks-key-alias "$ALIAS" \
    --ks-pass "pass:$KEYPASS" --key-pass "pass:$KEYPASS" \
    --out "$OUT_APK" "$BUILD/aligned.apk"

echo "==> verifying"
"$BT/apksigner" verify --print-certs "$OUT_APK" | sed -n '1,5p'
"$BT/aapt2" dump badging "$OUT_APK" | sed -n '1,6p'

echo
echo "APK: $OUT_APK  ($(du -h "$OUT_APK" | cut -f1))"
