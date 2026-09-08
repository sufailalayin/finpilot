"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  fetchAdminAIUsage,
  fetchAdminOverview,
  fetchAdminSecurityEvents,
  fetchAdminSubscriptions,
  fetchAdminUsers,
} from "../lib/api";

type Overview = {
  total_users: number;
  active_trials: number;
  paid_users: number;
  expired_entitlements: number;
  ai_requests: number;
  registrations_7d: number;
  finance_accounts: number;
  transactions: number;
  assets: number;
  liabilities: number;
  security_events_24h: number;
};

type UserRow = {
  id: string;
  email: string;
  full_name: string | null;
  user_status: string;
  is_admin: boolean;
  entitlement_status: string | null;
  plan_code: string | null;
  trial_ends_at: string | null;
  paid_until: string | null;
  created_at: string;
};

type SubscriptionSummary = {
  free_users: number;
  trial_users: number;
  active_paid_users: number;
  cancelled_users: number;
  expired_users: number;
};

type AIUsage = {
  total_requests: number;
  requests_24h: number;
  requests_7d: number;
  unique_users_7d: number;
  prompt_chars_7d: number;
  response_chars_7d: number;
};

type SecurityEvent = {
  id: string;
  user_id: string | null;
  user_email: string | null;
  event_type: string;
  description: string | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
};

type Section = "overview" | "users" | "subscriptions" | "ai" | "security";

const nav: { key: Section; label: string; hint: string }[] = [
  { key: "overview", label: "Overview", hint: "Command center" },
  { key: "users", label: "Users", hint: "Accounts" },
  { key: "subscriptions", label: "Subscriptions", hint: "Plans" },
  { key: "ai", label: "AI Usage", hint: "Consumption" },
  { key: "security", label: "Security", hint: "Audit" },
];

function formatDate(value: string | null) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("en-IN", { dateStyle: "medium" }).format(new Date(value));
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function badgeClass(value: string | null) {
  if (!value) return "badge";
  const normalized = value.toLowerCase();
  if (["active", "pro", "paid"].includes(normalized)) return "badge good";
  if (["trial", "free"].includes(normalized)) return "badge warn";
  if (["expired", "cancelled", "suspended", "deleted"].includes(normalized)) return "badge bad";
  return "badge";
}

export default function AdminDashboard() {
  const router = useRouter();
  const [section, setSection] = useState<Section>("overview");
  const [overview, setOverview] = useState<Overview | null>(null);
  const [users, setUsers] = useState<UserRow[]>([]);
  const [subscriptions, setSubscriptions] = useState<SubscriptionSummary | null>(null);
  const [ai, setAI] = useState<AIUsage | null>(null);
  const [security, setSecurity] = useState<SecurityEvent[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [overviewData, userData, subscriptionData, aiData, securityData] = await Promise.all([
        fetchAdminOverview(),
        fetchAdminUsers(),
        fetchAdminSubscriptions(),
        fetchAdminAIUsage(),
        fetchAdminSecurityEvents(),
      ]);
      setOverview(overviewData);
      setUsers(userData);
      setSubscriptions(subscriptionData);
      setAI(aiData);
      setSecurity(securityData);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to load admin data";
      if (message === "ADMIN_SESSION_EXPIRED") {
        router.replace("/login");
        return;
      }
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    load();
  }, [load]);

  const visibleUsers = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return users;
    return users.filter((user) =>
      [user.full_name, user.email, user.plan_code, user.entitlement_status, user.user_status]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(term)),
    );
  }, [query, users]);

  async function logout() {
    await fetch("/api/session/logout", { method: "POST", credentials: "same-origin" });
    router.replace("/login");
    router.refresh();
  }

  const kpis = [
    ["Total users", overview?.total_users ?? "—", `${overview?.registrations_7d ?? "—"} joined in 7 days`],
    ["Paid subscribers", overview?.paid_users ?? "—", "Active Pro access"],
    ["Active trials", overview?.active_trials ?? "—", "Conversion opportunity"],
    ["Transactions", overview?.transactions ?? "—", "Finance records created"],
    ["AI requests", overview?.ai_requests ?? "—", `${ai?.requests_24h ?? "—"} in last 24h`],
  ];

  return (
    <main className="admin-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">F</div>
          <div>
            <strong>FinPilot</strong>
            <small>Admin Console</small>
          </div>
        </div>

        <nav className="nav" aria-label="Admin sections">
          {nav.map((item) => (
            <button
              key={item.key}
              className={section === item.key ? "active" : ""}
              onClick={() => setSection(item.key)}
            >
              <span>{item.label}</span>
              <small>{item.hint}</small>
            </button>
          ))}
        </nav>

        <div className="sidebar-foot">
          <button className="btn btn-danger" style={{ width: "100%" }} onClick={logout}>
            Sign out
          </button>
        </div>
      </aside>

      <section className="main">
        <header className="topbar">
          <div>
            <span className="eyebrow">Hastron Ventures · FinPilot</span>
            <h1>{nav.find((item) => item.key === section)?.label}</h1>
            <p className="subtitle">
              {section === "overview" && "Live operating view of users, product usage, subscriptions, AI and security."}
              {section === "users" && "Search and inspect FinPilot accounts, access status and plan lifecycle."}
              {section === "subscriptions" && "Monitor trial, free, paid, cancelled and expired entitlement states."}
              {section === "ai" && "Track AI feature adoption and consumption across the platform."}
              {section === "security" && "Review authentication and account security activity."}
            </p>
          </div>
          <div className="actions">
            <button className="btn" onClick={load}>{loading ? "Refreshing…" : "Refresh data"}</button>
            <button className="btn btn-danger" onClick={logout}>Sign out</button>
          </div>
        </header>

        {error ? <div className="error">{error}</div> : null}

        {section === "overview" && (
          <>
            <div className="grid kpis">
              {kpis.map(([label, value, note]) => (
                <article className="card kpi" key={String(label)}>
                  <div className="kpi-label">{label}</div>
                  <div className="kpi-value">{value}</div>
                  <div className="kpi-note">{note}</div>
                </article>
              ))}
            </div>

            <div className="grid two-col section">
              <article className="card panel">
                <div className="section-header">
                  <div>
                    <h2>Product activity</h2>
                    <p>Core finance modules currently being used across FinPilot.</p>
                  </div>
                </div>
                <div className="metric-list">
                  <div className="metric"><span className="kpi-label">Finance accounts</span><strong>{overview?.finance_accounts ?? "—"}</strong></div>
                  <div className="metric"><span className="kpi-label">Transactions</span><strong>{overview?.transactions ?? "—"}</strong></div>
                  <div className="metric"><span className="kpi-label">Assets tracked</span><strong>{overview?.assets ?? "—"}</strong></div>
                  <div className="metric"><span className="kpi-label">Liabilities tracked</span><strong>{overview?.liabilities ?? "—"}</strong></div>
                </div>
              </article>

              <article className="card panel">
                <div className="section-header">
                  <div>
                    <h2>Security pulse</h2>
                    <p>Recent authentication and security events.</p>
                  </div>
                </div>
                <div className="kpi-value">{overview?.security_events_24h ?? "—"}</div>
                <div className="kpi-note">events in the last 24 hours</div>
                <div style={{ marginTop: 18 }}>
                  <span className="badge good">HttpOnly admin session enabled</span>
                </div>
              </article>
            </div>

            <section className="section">
              <div className="section-header">
                <div><h2>Recent users</h2><p>Newest FinPilot accounts and current entitlement.</p></div>
                <button className="btn" onClick={() => setSection("users")}>View all users</button>
              </div>
              <UsersTable users={users.slice(0, 8)} />
            </section>
          </>
        )}

        {section === "users" && (
          <section className="section">
            <div className="section-header">
              <div><h2>User directory</h2><p>{visibleUsers.length} visible accounts</p></div>
              <input
                className="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search name, email, plan or status"
              />
            </div>
            <UsersTable users={visibleUsers} />
          </section>
        )}

        {section === "subscriptions" && (
          <>
            <div className="grid kpis">
              {[
                ["Active paid", subscriptions?.active_paid_users ?? "—", "Pro customers"],
                ["Trials", subscriptions?.trial_users ?? "—", "Currently evaluating"],
                ["Free", subscriptions?.free_users ?? "—", "Free entitlement"],
                ["Expired", subscriptions?.expired_users ?? "—", "Access ended"],
                ["Cancelled", subscriptions?.cancelled_users ?? "—", "Cancelled entitlement"],
              ].map(([label, value, note]) => (
                <article className="card kpi" key={String(label)}>
                  <div className="kpi-label">{label}</div>
                  <div className="kpi-value">{value}</div>
                  <div className="kpi-note">{note}</div>
                </article>
              ))}
            </div>
            <section className="section">
              <div className="section-header"><div><h2>Subscription members</h2><p>Plan and lifecycle dates for every account.</p></div></div>
              <UsersTable users={users} />
            </section>
          </>
        )}

        {section === "ai" && (
          <div className="grid kpis">
            {[
              ["All-time requests", ai?.total_requests ?? "—", "Recorded AI calls"],
              ["Last 24 hours", ai?.requests_24h ?? "—", "Recent demand"],
              ["Last 7 days", ai?.requests_7d ?? "—", "Weekly AI traffic"],
              ["Weekly AI users", ai?.unique_users_7d ?? "—", "Unique users"],
              ["Weekly characters", ((ai?.prompt_chars_7d ?? 0) + (ai?.response_chars_7d ?? 0)).toLocaleString("en-IN"), "Prompt + response"],
            ].map(([label, value, note]) => (
              <article className="card kpi" key={String(label)}>
                <div className="kpi-label">{label}</div>
                <div className="kpi-value">{value}</div>
                <div className="kpi-note">{note}</div>
              </article>
            ))}
          </div>
        )}

        {section === "security" && (
          <section className="section">
            <div className="section-header">
              <div><h2>Security audit log</h2><p>Latest login, account and security-related activity.</p></div>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Time</th><th>Event</th><th>User</th><th>Description</th><th>IP address</th><th>User agent</th>
                  </tr>
                </thead>
                <tbody>
                  {security.map((event) => (
                    <tr key={event.id}>
                      <td>{formatDateTime(event.created_at)}</td>
                      <td><span className="badge">{event.event_type.replaceAll("_", " ")}</span></td>
                      <td>{event.user_email ?? "System / unknown"}</td>
                      <td>{event.description ?? "—"}</td>
                      <td>{event.ip_address ?? "—"}</td>
                      <td title={event.user_agent ?? ""}>{event.user_agent ? event.user_agent.slice(0, 70) : "—"}</td>
                    </tr>
                  ))}
                  {!security.length && <tr><td colSpan={6} className="empty">No security events recorded yet.</td></tr>}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </section>
    </main>
  );
}

function UsersTable({ users }: { users: UserRow[] }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Name</th><th>Email</th><th>Account</th><th>Plan</th><th>Entitlement</th><th>Trial ends</th><th>Paid until</th><th>Joined</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td>{user.full_name ?? "—"} {user.is_admin ? <span className="badge">Admin</span> : null}</td>
              <td>{user.email}</td>
              <td><span className={badgeClass(user.user_status)}>{user.user_status}</span></td>
              <td><span className={badgeClass(user.plan_code)}>{user.plan_code ?? "—"}</span></td>
              <td><span className={badgeClass(user.entitlement_status)}>{user.entitlement_status ?? "—"}</span></td>
              <td>{formatDate(user.trial_ends_at)}</td>
              <td>{formatDate(user.paid_until)}</td>
              <td>{formatDate(user.created_at)}</td>
            </tr>
          ))}
          {!users.length && <tr><td colSpan={8} className="empty">No users found.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
