"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  fetchAdminActionLogs,
  fetchAdminAIUsage,
  fetchAdminOverview,
  fetchAdminSecurityEvents,
  fetchAdminSubscriptions,
  fetchAdminUsers,
  revokeAdminUserSessions,
  updateAdminUser,
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

type ActionLog = {
  id: string;
  actor_admin_email: string | null;
  target_user_email: string | null;
  action: string;
  reason: string;
  before_state: Record<string, unknown> | null;
  after_state: Record<string, unknown> | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
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

type Section = "overview" | "users" | "subscriptions" | "ai" | "security" | "logs";

const nav: { key: Section; label: string; hint: string }[] = [
  { key: "overview", label: "Overview", hint: "Command center" },
  { key: "users", label: "Users", hint: "Accounts" },
  { key: "subscriptions", label: "Subscriptions", hint: "Plans" },
  { key: "ai", label: "AI Usage", hint: "Consumption" },
  { key: "security", label: "Security", hint: "Audit" },
  { key: "logs", label: "Admin Logs", hint: "Changes" },
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
  const [actionLogs, setActionLogs] = useState<ActionLog[]>([]);
  const [selectedUser, setSelectedUser] = useState<UserRow | null>(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [overviewData, userData, subscriptionData, aiData, securityData, actionLogData] = await Promise.all([
        fetchAdminOverview(),
        fetchAdminUsers(),
        fetchAdminSubscriptions(),
        fetchAdminAIUsage(),
        fetchAdminSecurityEvents(),
        fetchAdminActionLogs(),
      ]);
      setOverview(overviewData);
      setUsers(userData);
      setSubscriptions(subscriptionData);
      setAI(aiData);
      setSecurity(securityData);
      setActionLogs(actionLogData);
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
              {section === "security" && "Review authentication, session revocation and account security activity."}
              {section === "logs" && "Detailed record of every manual admin change, including who changed what and why."}
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
            <UsersTable users={visibleUsers} onManage={setSelectedUser} />
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
              <UsersTable users={users} onManage={setSelectedUser} />
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

        {section === "logs" && (
          <section className="section">
            <div className="section-header">
              <div><h2>Admin action logs</h2><p>Every manual plan, account and session-control change is recorded here.</p></div>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Time</th><th>Admin</th><th>Target user</th><th>Action</th><th>Reason</th><th>Before</th><th>After</th><th>IP</th>
                  </tr>
                </thead>
                <tbody>
                  {actionLogs.map((log) => (
                    <tr key={log.id}>
                      <td>{formatDateTime(log.created_at)}</td>
                      <td>{log.actor_admin_email ?? "—"}</td>
                      <td>{log.target_user_email ?? "—"}</td>
                      <td><span className="badge">{log.action.replaceAll("_", " ")}</span></td>
                      <td>{log.reason}</td>
                      <td><code>{log.before_state ? JSON.stringify(log.before_state) : "—"}</code></td>
                      <td><code>{log.after_state ? JSON.stringify(log.after_state) : "—"}</code></td>
                      <td>{log.ip_address ?? "—"}</td>
                    </tr>
                  ))}
                  {!actionLogs.length && <tr><td colSpan={8} className="empty">No admin changes recorded yet.</td></tr>}
                </tbody>
              </table>
            </div>
          </section>
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
        {selectedUser ? (
          <ManageUserModal
            key={selectedUser.id}
            user={selectedUser}
            onClose={() => setSelectedUser(null)}
            onSaved={async () => {
              setSelectedUser(null);
              await load();
            }}
          />
        ) : null}
      </section>
    </main>
  );
}

function UsersTable({ users, onManage }: { users: UserRow[]; onManage?: (user: UserRow) => void }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Name</th><th>Email</th><th>Account</th><th>Plan</th><th>Entitlement</th><th>Trial ends</th><th>Paid until</th><th>Joined</th>{onManage ? <th>Control</th> : null}
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
              {onManage ? <td><button className="btn" onClick={() => onManage(user)}>Manage</button></td> : null}
            </tr>
          ))}
          {!users.length && <tr><td colSpan={onManage ? 9 : 8} className="empty">No users found.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}


function ManageUserModal({
  user,
  onClose,
  onSaved,
}: {
  user: UserRow;
  onClose: () => void;
  onSaved: () => Promise<void>;
}) {
  const [userStatus, setUserStatus] = useState(user.user_status);
  const [planCode, setPlanCode] = useState(user.plan_code ?? "free");
  const [entitlementStatus, setEntitlementStatus] = useState(user.entitlement_status ?? "expired");
  const [trialEndsAt, setTrialEndsAt] = useState(user.trial_ends_at ? user.trial_ends_at.slice(0, 10) : "");
  const [paidUntil, setPaidUntil] = useState(user.paid_until ? user.paid_until.slice(0, 10) : "");
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function save() {
    if (reason.trim().length < 3) {
      setError("Enter a reason for this admin change.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await updateAdminUser(user.id, {
        user_status: userStatus,
        plan_code: planCode,
        entitlement_status: entitlementStatus,
        trial_ends_at: trialEndsAt ? new Date(trialEndsAt + "T23:59:59Z").toISOString() : null,
        paid_until: paidUntil ? new Date(paidUntil + "T23:59:59Z").toISOString() : null,
        reason: reason.trim(),
      });
      await onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update user");
    } finally {
      setSaving(false);
    }
  }

  async function revokeSessions() {
    if (reason.trim().length < 3) {
      setError("Enter a reason before revoking sessions.");
      return;
    }
    if (!window.confirm("Sign this user out from all current sessions?")) return;
    setSaving(true);
    setError("");
    try {
      await revokeAdminUserSessions(user.id, reason.trim());
      await onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to revoke sessions");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section className="card modal" role="dialog" aria-modal="true" onMouseDown={(event) => event.stopPropagation()}>
        <div className="section-header">
          <div>
            <span className="eyebrow">Secure user control</span>
            <h2>{user.full_name ?? user.email}</h2>
            <p>{user.email}</p>
          </div>
          <button className="btn" onClick={onClose}>Close</button>
        </div>

        <div className="control-grid">
          <label className="field"><span>Account status</span>
            <select value={userStatus} onChange={(e) => setUserStatus(e.target.value)}>
              <option value="active">Active</option><option value="suspended">Suspended</option>
            </select>
          </label>
          <label className="field"><span>Plan</span>
            <select value={planCode} onChange={(e) => setPlanCode(e.target.value)}>
              <option value="free">Free</option><option value="pro">Pro</option>
            </select>
          </label>
          <label className="field"><span>Plan status</span>
            <select value={entitlementStatus} onChange={(e) => setEntitlementStatus(e.target.value)}>
              <option value="trial">Trial</option><option value="active">Active</option><option value="expired">Expired</option><option value="cancelled">Cancelled</option>
            </select>
          </label>
          <label className="field"><span>Trial ends</span><input type="date" value={trialEndsAt} onChange={(e) => setTrialEndsAt(e.target.value)} /></label>
          <label className="field"><span>Paid until</span><input type="date" value={paidUntil} onChange={(e) => setPaidUntil(e.target.value)} /></label>
        </div>

        <label className="field"><span>Reason for change *</span>
          <input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Example: Manual Pro activation after payment verification" maxLength={300} />
        </label>
        {error ? <div className="error" style={{ marginTop: 12 }}>{error}</div> : null}

        <div className="modal-actions">
          <button className="btn btn-danger" disabled={saving} onClick={revokeSessions}>Revoke all sessions</button>
          <button className="btn primary" disabled={saving} onClick={save}>{saving ? "Saving…" : "Save access changes"}</button>
        </div>
        <p className="security-note">Every change stores the admin, target user, reason, before/after values, IP address and device user-agent.</p>
      </section>
    </div>
  );
}
