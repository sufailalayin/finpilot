"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export default function AdminLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [mfaRequired, setMfaRequired] = useState(false);
  const [code, setCode] = useState("");
  const [mfaEmail, setMfaEmail] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      if (mfaRequired) {
        const response = await fetch("/api/session/verify", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
          body: JSON.stringify({ code }),
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail ?? "Verification failed");
        }
        router.replace("/");
        router.refresh();
        return;
      }

      const response = await fetch("/api/session/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? "Login failed");

      if (data.mfa_required) {
        setMfaRequired(true);
        setMfaEmail(data.email ?? email);
        setPassword("");
        return;
      }

      throw new Error("Administrator verification was not started.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-shell">
      <section className="card login-card">
        <div className="brand">
          <div className="brand-mark">F</div>
          <div>
            <strong>FinPilot Admin</strong>
            <small>Hastron Ventures</small>
          </div>
        </div>
        <span className="eyebrow">Restricted access</span>
        <h1>Welcome back</h1>
        <p className="subtitle">Sign in with an authorized administrator account.</p>

        <form onSubmit={submit}>
          {!mfaRequired ? (
            <>
              <div className="field">
                <label htmlFor="email">Admin email</label>
                <input id="email" value={email} onChange={(e) => setEmail(e.target.value)} type="email" autoComplete="username" required />
              </div>
              <div className="field">
                <label htmlFor="password">Password</label>
                <input id="password" value={password} onChange={(e) => setPassword(e.target.value)} type="password" autoComplete="current-password" required />
              </div>
            </>
          ) : (
            <>
              <p className="subtitle">
                Enter the 6-digit verification code sent to {mfaEmail || "your administrator email"}.
              </p>
              <div className="field">
                <label htmlFor="code">Verification code</label>
                <input
                  id="code"
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  required
                />
              </div>
            </>
          )}
          {error ? <div className="error" style={{ marginTop: 14 }}>{error}</div> : null}
          <button className="btn" type="submit" disabled={loading}>
            {loading
              ? (mfaRequired ? "Verifying…" : "Signing in…")
              : (mfaRequired ? "Verify & continue" : "Secure sign in")}
          </button>
        </form>

        <p className="security-note">
          Admin access requires password plus a fresh email verification code. Session tokens are stored in Secure, HttpOnly cookies and are not exposed to browser JavaScript.
        </p>
      </section>
    </main>
  );
}
