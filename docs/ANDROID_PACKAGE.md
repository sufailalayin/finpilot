# Android Package

Current Android application ID:

`com.hastronventures.finpilot`

This identifier is independent from the visible app brand and can remain stable even if the public product name changes before launch.

To generate the permanent Android scaffold locally:

```bash
cd mobile
bash tool/bootstrap_android.sh
flutter pub get
flutter analyze
flutter build appbundle
```

Do not change the application ID after publishing the app in Google Play.
