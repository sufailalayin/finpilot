#!/usr/bin/env sh
set -eu

APP_DIR=/tmp/finpilot_mobile
rm -rf "$APP_DIR"
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
p = Path("/tmp/finpilot_mobile/android/app/src/main/AndroidManifest.xml")
text = p.read_text()
text = text.replace("<application", '<application android:allowBackup="false" android:usesCleartextTraffic="false"', 1)
p.write_text(text)
PY

cd "$APP_DIR"
flutter pub get
flutter analyze --no-fatal-infos
flutter build apk --debug --dart-define=FINPILOT_API_BASE_URL=https://finpilot-backend-production-eaf5.up.railway.app/api/v1

mkdir -p /out
cp "$APP_DIR/build/app/outputs/flutter-apk/app-debug.apk" /out/FinPilot-1.1.1-build3-Railway.apk
