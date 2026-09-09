# Google Play Reviewer Access — FinPilot

## App access
FinPilot requires an account to access the main product.

For Play Console review, create a dedicated reviewer account in the production environment before submitting a build. Do not reuse a personal administrator account.

Recommended reviewer account setup:
- Email: a dedicated review-only address controlled by Hastron Ventures.
- Email verification: completed.
- Account status: active.
- Plan: Pro.
- Entitlement status: active.
- Paid-until date: sufficiently beyond the expected review window.

Record the reviewer email/password only in the Google Play Console **App access** section or another approved confidential reviewer field. Never commit reviewer credentials to GitHub.

## Reviewer instructions
1. Launch FinPilot.
2. Choose Sign in.
3. Enter the review account credentials supplied in Play Console.
4. The reviewer can access Dashboard, transactions, budgets, goals, AI, reports, assets/liabilities, smart alerts, Security & Privacy, and subscription-related UI.
5. PIN/biometric lock is optional and does not need to be enabled for review.

## Subscription testing
Google Play purchase testing should use licensed/internal testers and Play billing test products. The dedicated content-review account can be manually granted Pro access from FinPilot Admin if Play requires access to Pro screens without completing a real purchase.

## Account deletion
In-app deletion is available under Profile -> Security & Privacy. Public deletion instructions are available at /account-deletion on the FinPilot admin/public web host.

## Privacy policy
The public privacy policy is available at /privacy on the FinPilot admin/public web host.
