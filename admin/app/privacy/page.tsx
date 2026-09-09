import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "FinPilot Privacy Policy",
  description: "Privacy policy for FinPilot by Hastron Ventures",
  robots: { index: true, follow: true },
};

export default function PrivacyPage() {
  return (
    <main className="legal-shell">
      <article className="legal-card">
        <div className="legal-brand">
          <div className="brand-mark">F</div>
          <div>
            <strong>FinPilot</strong>
            <small>by Hastron Ventures</small>
          </div>
        </div>

        <span className="eyebrow">Legal</span>
        <h1>Privacy Policy</h1>
        <p className="legal-updated">Last updated: 9 September 2026</p>

        <p>
          FinPilot is a personal finance application designed to help users
          record, organize and understand their financial information.
        </p>

        <h2>Information we process</h2>
        <p>
          FinPilot may process account profile information, email address,
          manually entered financial accounts, balances, transactions,
          categories, budgets, goals, recurring items, bills, subscriptions,
          assets, investments, liabilities, EMI information, AI questions,
          subscription status, security events, and technical information
          required to operate and secure the service.
        </p>

        <h2>How we use information</h2>
        <p>
          We use information to provide requested finance features, calculate
          dashboards and reports, generate financial health indicators, provide
          AI-assisted insights where enabled, manage subscriptions, secure
          accounts, prevent abuse, troubleshoot the service, and comply with
          applicable legal obligations.
        </p>

        <h2>Email verification and account security</h2>
        <p>
          FinPilot may send email verification and password-reset codes.
          Verification codes are time-limited and are used only to verify
          account ownership or recover access. Security events may be recorded
          to help protect accounts and investigate suspicious activity.
        </p>

        <h2>AI features</h2>
        <p>
          FinPilot Pro may send relevant financial context and the user&apos;s
          question to the configured AI service to generate the requested
          response. FinPilot aims to send only information required for the
          feature being used. AI output is informational and does not guarantee
          financial outcomes.
        </p>

        <h2>Security</h2>
        <p>
          FinPilot uses authenticated API access, secure token storage on
          supported devices, optional PIN or biometric app lock, session
          revocation, audit logging, email verification, and production
          configuration controls. No system can guarantee absolute security.
        </p>

        <h2>Data export and deletion</h2>
        <p>
          Users can export supported FinPilot data from Security &amp; Privacy.
          Users can also request permanent account deletion from within the app.
          Account-deletion instructions are available on our public account
          deletion page.
        </p>

        <h2>Payments</h2>
        <p>
          Paid FinPilot subscriptions on Android are processed through Google
          Play. Google may process payment and purchase information under its
          own privacy terms. FinPilot receives subscription verification
          information needed to determine entitlement status.
        </p>

        <h2>Data retention</h2>
        <p>
          FinPilot retains user information while an account remains active and
          as reasonably required to provide the service, protect the platform,
          resolve disputes, and comply with applicable obligations. When an
          account is permanently deleted, account-linked application data is
          deleted subject to any information that must be retained by law or
          for legitimate security, fraud-prevention, or dispute purposes.
        </p>

        <h2>Children</h2>
        <p>
          FinPilot is intended for users who are legally able to manage their
          own personal financial information under applicable rules. FinPilot
          is not designed as a service directed to young children.
        </p>

        <h2>Third-party services</h2>
        <p>
          FinPilot may use infrastructure, email delivery, AI, and payment
          providers where required to operate the service. Those providers
          process information according to their respective terms and privacy
          commitments.
        </p>

        <h2>Contact</h2>
        <p>
          For privacy questions or account-related requests, contact
          <strong> info@hastron.in</strong>.
        </p>

        <div className="legal-links">
          <a href="/account-deletion">Account deletion</a>
        </div>
      </article>
    </main>
  );
}
