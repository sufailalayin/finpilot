# Android Release Checklist

Current application ID: `com.hastronventures.finpilot`

## Before Play Console setup

- Keep the application ID stable.
- Finalize the public product name before store listing submission.
- Generate the permanent Flutter Android scaffold.
- Confirm CI produces a debug APK successfully.
- Create an upload keystore and keep it outside Git.
- Configure release signing through environment/secret-backed Gradle properties.

## Google Play Billing products

Planned product IDs:

- `finpilot_pro_monthly`
- `finpilot_pro_yearly`

These IDs are configuration identifiers and can remain unchanged even if the visible app name changes.

## Purchase security

The Android app may initiate a purchase, but it must not grant Pro access itself.

Required flow:

1. Google Play returns purchase details.
2. Android sends product ID and purchase token to FinPilot backend.
3. Backend verifies the purchase with Google Play Developer API.
4. Backend updates the user's entitlement.
5. Android refreshes `/api/v1/subscriptions/status`.
6. Purchase is acknowledged/completed after successful handling.

## Required Play Console items later

- App listing
- Privacy policy URL
- Data safety form
- Subscription base plans/offers
- Internal testing track
- Service account / Play Developer API access
- Release AAB signed with upload key
