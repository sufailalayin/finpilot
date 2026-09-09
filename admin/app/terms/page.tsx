import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "FinPilot Terms of Service",
  description: "Terms of Service for FinPilot by Hastron Ventures",
  robots: { index: true, follow: true },
};

export default function TermsPage() {
  return (
    <main className="legal-shell">
      <article className="legal-card">
        <div className="legal-brand">
          <div className="brand-mark">F</div>
          <div><strong>FinPilot</strong><small>by Hastron Ventures</small></div>
        </div>
        <span className="eyebrow">Legal</span>
        <h1>Terms of Service</h1>
        <p className="legal-updated">Last updated: 10 September 2026</p>

        <p>These Terms govern use of FinPilot, a personal financial-management service provided by Hastron Ventures. By creating an account or using FinPilot, you agree to these Terms and acknowledge the Privacy Policy.</p>

        <h2>Purpose of FinPilot</h2>
        <p>FinPilot helps users record and organise personal financial information, accounts, transactions, budgets, goals, assets, liabilities and receivables, receive reminders, view calculated insights and use optional AI-assisted features. FinPilot is software and is not a bank, investment adviser, broker, accountant, tax adviser or law firm.</p>

        <h2>Your account and records</h2>
        <p>You are responsible for protecting your credentials and device and for reviewing the accuracy of information recorded in FinPilot. Balances, financial-health indicators, savings rates, reminders, projections and calculations depend on available data and may be incomplete or inaccurate. Important information should be checked against original financial records.</p>

        <h2>AI and informational content</h2>
        <p>AI-generated responses and automated insights may be inaccurate, incomplete or outdated. They are informational assistance only and do not constitute personalised financial, investment, trading, tax, accounting or legal advice. You remain responsible for decisions and actions you take.</p>

        <h2>Subscriptions and trials</h2>
        <p>Some features may require a trial or paid plan. Plan features, price, billing period and renewal information are presented through the applicable subscription flow. Access to paid features may be restricted after a trial or subscription ends. A payment or app-store provider may apply its own billing and refund rules.</p>

        <h2>Backups and independent copies</h2>
        <p>FinPilot may maintain periodic backups and recovery systems for operational resilience. A backup does not guarantee that a particular record or version can always be restored. Users should use available export tools and maintain independent copies of important financial information.</p>

        <h2>Availability and data loss</h2>
        <p>We aim to operate FinPilot reliably but cannot guarantee uninterrupted, completely secure or error-free operation. Maintenance, software or hardware failure, internet or infrastructure incidents, cyber incidents, user error, deletion, corruption or events outside our reasonable control may affect availability or data.</p>
        <p>To the maximum extent permitted by applicable law, Hastron Ventures and FinPilot are not liable for indirect, incidental, special or consequential loss resulting from service interruption or loss, corruption, deletion or unavailability of data caused by circumstances outside our reasonable control. Nothing in these Terms excludes or limits liability, statutory rights or remedies that cannot legally be excluded or limited.</p>

        <h2>Acceptable use</h2>
        <p>You must not misuse FinPilot, attempt unauthorised access to another account, interfere with the service, abuse APIs, bypass subscription or security controls, or use the service unlawfully.</p>

        <h2>Account suspension and deletion</h2>
        <p>We may restrict access where reasonably necessary to protect users or the service, investigate abuse or security risks, enforce these Terms or comply with law. Users may stop using FinPilot and may use the available permanent account-deletion process.</p>

        <h2>Changes</h2>
        <p>We may update these Terms as FinPilot changes or applicable requirements evolve. Where required, material changes will be communicated and additional consent obtained.</p>

        <h2>Contact</h2>
        <p>Questions about these Terms may be sent to <strong>info@hastron.in</strong>.</p>

        <div className="legal-links">
          <a href="/privacy">Privacy Policy</a>
          <a href="/account-deletion">Account deletion</a>
        </div>
      </article>
    </main>
  );
}
