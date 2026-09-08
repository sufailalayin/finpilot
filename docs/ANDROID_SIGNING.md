# Android Signing

FinPilot release builds use a private upload keystore. Never commit the keystore, passwords, aliases, or generated `key.properties`.

## Required GitHub Actions secrets

- `ANDROID_KEYSTORE_BASE64`
- `ANDROID_KEYSTORE_PASSWORD`
- `ANDROID_KEY_ALIAS`
- `ANDROID_KEY_PASSWORD`

## Required repository variable

- `FINPILOT_API_BASE_URL`

## Create an upload keystore locally

Example:

```bash
keytool -genkeypair \
  -v \
  -keystore upload-keystore.jks \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -alias upload
```

Convert the keystore to base64 before storing it as a GitHub Actions secret.

Linux/macOS:

```bash
base64 -w 0 upload-keystore.jks
```

PowerShell:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("upload-keystore.jks"))
```

The workflow `FinPilot Android Release` builds a signed AAB only when manually started and only when all required secrets are present.
