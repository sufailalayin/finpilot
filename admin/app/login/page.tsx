"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export default function AdminLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await fetch("/api/session/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? "Login failed");
      router.replace("/");
      router.refresh();
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
          <div className="field">
            <label htmlFor="email">Admin email</label>
            <input id="email" value={email} onChange={(e) => setEmail(e.target.value)} type="email" autoComplete="username" required />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <input id="password" value={password} onChange={(e) => setPassword(e.target.value)} type="password" autoComplete="current-password" required />
          </div>
          {error ? <div className="error" style={{ marginTop: 14 }}>{error}</div> : null}
          <button className="btn" type="submit" disabled={loading}>
            {loading ? "Signing in…" : "Secure sign in"}
          </button>
        </form>

        <p className="security-note">
          Admin sessions are stored in a Secure, HttpOnly cookie and are not exposed to browser JavaScript.
        </p>
      </section>
    </main>
  );
}
