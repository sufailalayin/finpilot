# FinPilot v1.0.0 Release Checklist

## Automated gates
- [ ] Backend migrations upgrade cleanly from current production schema.
- [ ] Backend automated tests pass.
- [ ] Admin production build passes.
- [ ] Flutter analysis passes.
- [ ] Android debug APK builds.
- [ ] Android release AAB builds.
- [ ] Docker smoke tests pass.
- [ ] Free/Pro API enforcement tests pass.
- [ ] Security & Privacy routes are registered and reachable.

## Production configuration
- [ ] FINPILOT_ENVIRONMENT=production
- [ ] Strong FINPILOT_JWT_SECRET configured outside source control.
- [ ] Production database and Redis URLs configured.
- [ ] CORS restricted to approved production origins.
- [ ] OpenAI key/model configured for Pro AI.
- [ ] Google Play package name is com.hastronventures.finpilot.
- [ ] Google Play monthly/yearly products exist.
- [ ] Google Play service account JSON configured securely.
- [ ] RTDN secret and notification path configured.
- [ ] Railway production migrations applied before rollout.

## Android signing
The CI release AAB is a **release-build validation artifact**. Before Play Store upload, configure a permanent upload signing key outside the repository. Never commit keystore files or passwords.

- [ ] Generate/store the upload key securely.
- [ ] Configure Play App Signing.
- [ ] Configure CI/release environment signing secrets.
- [ ] Produce signed production AAB.
- [ ] Record versionCode/versionName release history.

## Play Console
- [ ] App created in Play Console.
- [ ] Store listing reviewed.
- [ ] 512x512 store icon and feature graphic prepared.
- [ ] Phone screenshots captured from final release candidate.
- [ ] Privacy-policy URL published.
- [ ] Data Safety form completed from actual production data flows.
- [ ] Financial-features declarations completed if requested by Play.
- [ ] Content rating completed.
- [ ] App access instructions supplied for reviewer if login is required.
- [ ] Subscription products and base plans activated.
- [ ] Internal testing purchase verification completed.
- [ ] Closed test completed before production rollout.

## Real-device QA
- [ ] Fresh registration starts correct trial/free entitlement.
- [ ] Login/logout and revoked-session behavior work.
- [ ] Account/transaction CRUD and transfers persist correctly.
- [ ] Balances and net worth recalculate correctly.
- [ ] Budgets/goals work for Free.
- [ ] Pro-only areas route Free users to paywall.
- [ ] Pro user can access AI, reports, assets/liabilities and smart alerts.
- [ ] Google Play purchase activates Pro after server verification.
- [ ] Restore Purchase restores entitlement.
- [ ] Expired subscription returns user to Free access.
- [ ] PIN app lock works after cold start.
- [ ] Biometric unlock works on supported Android device.
- [ ] JSON/CSV exports open correctly.
- [ ] Permanent account deletion signs user out and removes account data.
- [ ] Empty/loading/error/offline states are usable.
- [ ] No debug banner, test data, development URLs, or secrets are visible.

## Release
- [ ] Tag source as v1.0.0.
- [ ] Upload signed AAB to Internal testing first.
- [ ] Verify install/upgrade from Play.
- [ ] Promote to Closed testing.
- [ ] Monitor backend logs, crash reports and subscription RTDN.
- [ ] Promote gradually to Production.
