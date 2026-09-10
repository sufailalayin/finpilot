# FinPilot v1.1.0 — Build 2

Release date: 10 September 2026

## Product updates

- Improved responsive Quick Entry sheet for smaller Android screens.
- Slightly deeper FinPilot green theme while preserving the existing visual identity.
- Added Money Given / Receivables with Pending and Cleared history.
- Added Cash/Bank ↔ Person ↔ Outside movement tracking.
- Added borrowing flows linked to Cash/Bank accounts and repayment balance checks.
- Added credit-card statement and reminder tracking without direct card payment.
- Added permanent Profile → App update checking.
- Added optional and required in-app update support.
- Improved Trial → Pro transitions and strict trial/subscription expiry enforcement.
- Improved AI Copilot reliability and conversation visibility.
- Added privacy policy, terms, data export, deletion, and backup/data-loss disclosures.

## Security release gate

- Sanitized user data export so password hashes and internal auth state are never exported.
- Persistent login brute-force throttling and security audit events.
- Stronger production JWT secret/CORS/OTP configuration validation.
- JWT issuer/audience validation.
- Migrated JWT implementation from python-jose/ecdsa to PyJWT[crypto].
- Administrator password + email OTP MFA with MFA-bound JWT claims.
- Admin console uses Secure/HttpOnly MFA session cookies.
- Admin proxy no longer accepts arbitrary incoming bearer-token fallback.
- Same-origin protection for state-changing admin proxy requests.
- Restrictive CORS and API security headers.
- Admin Content Security Policy, clickjacking, referrer and browser-permission protections.
- Production API documentation disabled.
- Non-root backend and Admin containers.
- Android backups and cleartext network traffic disabled in signed builds.
- CI/mobile validation is isolated from the production API.
- Secret scanning, Python production dependency audit, Bandit SAST and npm production dependency audit added to CI.
- Signed Android release runs only after successful FinPilot CI for the release commit.

## Version

- Version name: 1.1.0
- Build number: 2


## Persistent session & device protection

- Rotating 90-day refresh sessions keep the mobile app signed in without making access JWTs long-lived.
- Refresh tokens are stored only in Android secure storage and only token hashes are stored server-side.
- Refresh-token rotation prevents reuse of an already-consumed token.
- Password reset and session revocation invalidate persistent sessions.
- First successful sign-in asks the user to configure a 4–8 digit FinPilot app PIN and optional fingerprint/biometric unlock.
- App PINs use a random salt, iterative hashing, secure storage, legacy PIN migration, and failed-attempt lockout.
- Public readiness output is minimal; detailed readiness is administrator-only.
- Google Play RTDN authentication is fail-closed and constant-time validated.
- App update URLs must use HTTPS.
