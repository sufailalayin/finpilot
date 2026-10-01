# FinPilot 1.1.4

Build 7

## Fixes

- Fixed mobile sign-in so valid legacy passwords are not blocked by an unnecessary client-side 10-character login rule.
- Aligned password reset validation with the backend 10-character minimum.
- Corrected password guidance shown on login, registration, and reset screens.

## Quality

- Added shared mobile password-policy regression tests.
- FinPilot CI now runs the Flutter test suite before Android release validation.
