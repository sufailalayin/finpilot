# FinPilot — Google Play Data Safety Draft

**App:** FinPilot  
**Publisher:** Hastron Ventures  
**Package:** com.hastronventures.finpilot  
**Prepared:** 9 September 2026

> This is a submission draft based on the current FinPilot code and production architecture. Re-check every answer in Play Console against the exact production build, enabled SDKs, and final third-party contracts before submission.

## High-level answers

- Does the app collect user data? **Yes**
- Is all user data encrypted in transit? **Yes — production API traffic must use HTTPS/TLS**
- Can users request deletion of their data? **Yes**
- Does the app support account deletion? **Yes — in-app Security & Privacy flow and public /account-deletion instructions**
- Is a privacy policy provided? **Yes — public /privacy page**

## Data types FinPilot collects

### Personal info

**Name**
- Collected: Yes
- Required: Optional at signup depending on UI completion
- Purpose: Account management, app functionality

**Email address**
- Collected: Yes
- Required: Yes
- Purpose: Account management, authentication, email verification, password recovery, security

**User IDs**
- Collected/created: Yes
- Purpose: Account management, app functionality, security

### Financial info

**Other financial information**
- Collected: Yes
- Examples: manually entered accounts, balances, income, expenses, transactions, budgets, goals, recurring commitments, bills, assets, investments, liabilities, EMI details, net-worth inputs
- Purpose: Core app functionality, analytics shown to the user, personalization, financial health calculations

**Purchase history / subscription entitlement**
- Collected: Yes
- FinPilot receives Google Play subscription/purchase verification information needed to determine Pro entitlement
- Purpose: Subscription management, fraud prevention, app functionality

FinPilot should **not** declare that it collects raw card or bank-payment credentials if the production app only uses Google Play Billing and never receives those credentials.

### App activity

**App interactions**
- Collected: Yes
- Examples: AI requests/usage records, feature usage required for service operation, security/audit events
- Purpose: App functionality, analytics, security, fraud prevention

**Other user-generated content**
- Potentially applicable: AI Copilot questions/prompts entered by the user
- Purpose: Provide AI-generated responses
- Verify the exact Play Console subtype shown before submission.

### Device or other identifiers / technical data

FinPilot records technical security information such as IP address and user-agent on selected authentication/admin/security events.

Before submitting Data Safety, confirm how Google Play classifies these values in the current form and whether any production SDK adds device IDs, advertising IDs, crash IDs, or analytics identifiers.

## Data FinPilot does not currently require

Based on the current v1 scope, FinPilot does not intentionally require:
- Precise or approximate location
- Contacts
- Photos or videos
- Audio files
- Health or fitness data
- SMS or call logs
- Calendar data
- Browsing history
- Advertising ID for advertising
- Bank-login credentials
- Raw payment-card details

If any SDK or future feature adds one of these, update Data Safety before release.

## Data sharing

### AI provider

FinPilot Pro can send the user's AI question and relevant financial context to the configured AI provider to generate the requested response.

For Play Console:
- Confirm the production AI provider's contractual role.
- If the provider qualifies as a service provider processing data only on FinPilot's behalf under Google's Data Safety definition, apply the appropriate service-provider treatment.
- If it does not qualify for an exemption, declare the applicable data as shared.
- The privacy policy must remain consistent with the final declaration.

### Email provider

Email address is sent to the configured transactional-email provider for signup verification, OTP delivery and password recovery.

Confirm whether the final provider qualifies for Google's service-provider exception before deciding whether this must be marked as "shared."

### Google Play Billing

Google Play processes payments. FinPilot receives purchase/subscription verification information required to manage entitlement.

Do not claim that FinPilot itself collects raw card data unless the production implementation actually does.

### Hosting/infrastructure

FinPilot backend/database infrastructure processes user data to provide the service. Confirm final hosting providers and their contractual role before final Data Safety submission.

## Purposes likely selected in Play Console

Depending on the data type, likely purposes are:
- App functionality
- Account management
- Analytics
- Personalization
- Fraud prevention, security and compliance
- Developer communications only where email is used for account/security communication

Do not select Advertising or Marketing unless FinPilot actually starts using data for those purposes.

## Data handling / deletion

Users can:
- Export supported account data from Security & Privacy.
- Permanently delete their account in-app after confirmation.
- Use the public account-deletion instructions at /account-deletion.
- Contact info@hastron.in if they cannot access the app.

Password reset revokes previous sessions.

## Final verification checklist

Before submitting Data Safety:
- [ ] Confirm production build contains no analytics/crash/ads SDK not represented above.
- [ ] Confirm exact data sent to the AI provider.
- [ ] Confirm Resend/SMTP provider role and contract.
- [ ] Confirm hosting/database provider role.
- [ ] Confirm Google Play Billing SDK behavior.
- [ ] Confirm all API traffic is HTTPS.
- [ ] Confirm account deletion works against production.
- [ ] Confirm public Privacy Policy and Account Deletion URLs are live.
- [ ] Compare every submitted answer with the final privacy policy.
