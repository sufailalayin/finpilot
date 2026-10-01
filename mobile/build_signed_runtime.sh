#!/usr/bin/env bash
set -euo pipefail

required=(
  ANDROID_KEYSTORE_BASE64
  ANDROID_KEYSTORE_PASSWORD
  ANDROID_KEY_ALIAS
  ANDROID_KEY_PASSWORD
  FINPILOT_API_BASE_URL
)
for name in "${required[@]}"; do
  if [ -z "${!name:-}" ]; then
    echo "Missing required signing variable: $name" >&2
    exit 1
  fi
done

APP_DIR=/tmp/finpilot_release
OUT_DIR=/out
rm -rf "$APP_DIR" "$OUT_DIR"
mkdir -p "$OUT_DIR"

flutter create --platforms=android --org com.hastronventures --project-name finpilot "$APP_DIR"
rm -rf "$APP_DIR/lib" "$APP_DIR/test"
cp -R /src/lib "$APP_DIR/lib"
cp /src/pubspec.yaml "$APP_DIR/pubspec.yaml"

mkdir -p "$APP_DIR/android/app/src/main/kotlin/com/hastronventures/finpilot"
cat > "$APP_DIR/android/app/src/main/kotlin/com/hastronventures/finpilot/MainActivity.kt" <<'EOF'
package com.hastronventures.finpilot

import io.flutter.embedding.android.FlutterFragmentActivity

class MainActivity: FlutterFragmentActivity()
EOF

sed -i '/<manifest/a\    <uses-permission android:name="android.permission.USE_BIOMETRIC" />' "$APP_DIR/android/app/src/main/AndroidManifest.xml"

mkdir -p "$APP_DIR/android/app/src/main/res/drawable" "$APP_DIR/android/app/src/main/res/drawable-v21"
cat > "$APP_DIR/android/app/src/main/res/drawable/finpilot_mark.xml" <<'EOF'
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path android:fillColor="#124D40" android:pathData="M54,8A46,46 0,1 0,54 100A46,46 0,1 0,54 8Z"/>
    <path android:fillColor="#FFFFFF" android:pathData="M31,30H77V41H43V50H70V61H43V79H31Z"/>
    <path android:fillColor="#A9E4D5" android:pathData="M62,50H77V61H62Z"/>
</vector>
EOF

cat > "$APP_DIR/android/app/src/main/res/drawable/launch_background.xml" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item><shape android:shape="rectangle"><solid android:color="#F3F6F5" /></shape></item>
    <item android:width="120dp" android:height="120dp" android:gravity="center" android:drawable="@drawable/finpilot_mark" />
</layer-list>
EOF
cp "$APP_DIR/android/app/src/main/res/drawable/launch_background.xml" "$APP_DIR/android/app/src/main/res/drawable-v21/launch_background.xml"
sed -i 's/android:label="finpilot"/android:label="FinPilot"/' "$APP_DIR/android/app/src/main/AndroidManifest.xml"
sed -i 's#android:icon="@mipmap/ic_launcher"#android:icon="@drawable/finpilot_mark"#' "$APP_DIR/android/app/src/main/AndroidManifest.xml"

python3 - <<'PY'
from pathlib import Path
p = Path("/tmp/finpilot_release/android/app/src/main/AndroidManifest.xml")
text = p.read_text()
text = text.replace(
    "<application",
    '<application android:allowBackup="false" android:usesCleartextTraffic="false"',
    1,
)
p.write_text(text)
PY

printf '%s' "$ANDROID_KEYSTORE_BASE64" | base64 --decode > "$APP_DIR/android/app/upload-keystore.jks"
cat > "$APP_DIR/android/key.properties" <<EOF
storePassword=$ANDROID_KEYSTORE_PASSWORD
keyPassword=$ANDROID_KEY_PASSWORD
keyAlias=$ANDROID_KEY_ALIAS
storeFile=upload-keystore.jks
EOF

python3 - <<'PY'
from pathlib import Path

path = Path("/tmp/finpilot_release/android/app/build.gradle.kts")
text = path.read_text()

if "import java.util.Properties" not in text:
    text = "import java.util.Properties\nimport java.io.FileInputStream\n\n" + text

marker = "android {"
insert = '''val keystoreProperties = Properties()
val keystorePropertiesFile = rootProject.file("key.properties")
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(FileInputStream(keystorePropertiesFile))
}

'''
text = text.replace(marker, insert + marker, 1)

text = text.replace(
    "    defaultConfig {",
    '''    signingConfigs {
        create("release") {
            keyAlias = keystoreProperties["keyAlias"] as String
            keyPassword = keystoreProperties["keyPassword"] as String
            storeFile = file(keystoreProperties["storeFile"] as String)
            storePassword = keystoreProperties["storePassword"] as String
        }
    }

    defaultConfig {''',
    1,
)

text = text.replace(
    'signingConfig = signingConfigs.getByName("debug")',
    'signingConfig = signingConfigs.getByName("release")',
)

path.write_text(text)
PY

cat >> "$APP_DIR/android/gradle.properties" <<'EOF'
org.gradle.jvmargs=-Xmx2048m -XX:MaxMetaspaceSize=512m -Dfile.encoding=UTF-8
org.gradle.daemon=false
org.gradle.parallel=false
org.gradle.workers.max=2
kotlin.daemon.jvmargs=-Xmx1024m
EOF

export GRADLE_OPTS="-Dorg.gradle.daemon=false -Dorg.gradle.workers.max=2"

cd "$APP_DIR"
flutter pub get
flutter analyze --no-fatal-infos
flutter build apk --release --dart-define=FINPILOT_API_BASE_URL="$FINPILOT_API_BASE_URL"
flutter build appbundle --release --dart-define=FINPILOT_API_BASE_URL="$FINPILOT_API_BASE_URL"

APKSIGNER="$ANDROID_HOME/build-tools/$(ls "$ANDROID_HOME/build-tools" | sort -V | tail -1)/apksigner"
"$APKSIGNER" verify --verbose build/app/outputs/flutter-apk/app-release.apk

VERSION="$(awk '/^version:/ {print $2}' /src/pubspec.yaml)"
VERSION_NAME="${VERSION%%+*}"
VERSION_CODE="${VERSION##*+}"
APK_NAME="FinPilot-${VERSION_NAME}-build${VERSION_CODE}-production.apk"
AAB_NAME="FinPilot-${VERSION_NAME}-build${VERSION_CODE}-production.aab"

cp build/app/outputs/flutter-apk/app-release.apk "$OUT_DIR/$APK_NAME"
cp build/app/outputs/bundle/release/app-release.aab "$OUT_DIR/$AAB_NAME"
sha256sum "$OUT_DIR/$APK_NAME" "$OUT_DIR/$AAB_NAME" > "$OUT_DIR/SHA256SUMS.txt"

cat > "$OUT_DIR/BUILD_INFO.txt" <<EOF
version_name=$VERSION_NAME
version_code=$VERSION_CODE
api_base_url=$FINPILOT_API_BASE_URL
EOF

cd "$OUT_DIR"
python3 -m http.server "${PORT:-8080}" --bind 0.0.0.0
