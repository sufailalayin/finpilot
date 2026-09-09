import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Delete FinPilot Account",
  description: "How to permanently delete a FinPilot account and associated data",
  robots: { index: true, follow: true },
};

export default function AccountDeletionPage() {
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

        <span className="eyebrow">Account &amp; data</span>
        <h1>Delete your FinPilot account</h1>

        <p>
          FinPilot users can permanently delete their account and associated
          application data from inside the FinPilot app.
        </p>

        <h2>Delete from the app</h2>
        <ol>
          <li>Open FinPilot and sign in.</li>
          <li>Open Profile.</li>
          <li>Open Security &amp; Privacy.</li>
          <li>Select the permanent account deletion option.</li>
          <li>Confirm your password and the deletion confirmation shown by the app.</li>
        </ol>

        <h2>What is deleted</h2>
        <p>
          Permanent account deletion removes the FinPilot user account and
          account-linked application data such as manually entered finance
          accounts, transactions, categories, budgets, goals, recurring items,
          bills, assets, liabilities and other user-owned FinPilot records,
          subject to applicable retention obligations.
        </p>

        <h2>What may be retained</h2>
        <p>
          Limited records may be retained where reasonably required by law,
          payment or accounting obligations, security and fraud prevention,
          dispute resolution, or enforcement of legal rights. Google Play
          purchase records controlled by Google are subject to Google&apos;s own
          retention policies.
        </p>

        <h2>Cannot access the app?</h2>
        <p>
          If you cannot access FinPilot but want to request deletion, email
          <strong> info@hastron.in</strong> from the email address registered
          with your FinPilot account. We may need to verify account ownership
          before processing the request.
        </p>

        <h2>Important</h2>
        <p>
          Account deletion is permanent. After deletion, deleted FinPilot data
          may not be recoverable.
        </p>

        <div className="legal-links">
          <a href="/privacy">Privacy Policy</a>
        </div>
      </article>
    </main>
  );
}
