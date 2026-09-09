"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  createBillingPlan,
  deleteAdminUser,
  fetchAdminActionLogs,
  fetchAdminAIUsage,
  fetchAdminOverview,
  fetchAdminSecurityEvents,
  fetchAdminSubscriptions,
  fetchAdminUserDetail,
  fetchAdminUsers,
  fetchBillingPlans,
  fetchPayments,
  fetchSystemReadiness,
  recordPayment,
  revokeAdminUserSessions,
  sendAdminTestEmail,
  updateAdminUser,
  updateAdminUserLocation,
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
  unverified_users: number;
};

type UserRow = {
  id: string;
  email: string;
  full_name: string | null;
  user_status: string;
  is_admin: boolean;
  email_verified: boolean;
  entitlement_status: string | null;
  plan_code: string | null;
  billing_plan_id?: string | null;
  billing_plan_name?: string | null;
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

type Readiness = {
  status: string;
  database: string;
  environment: string;
  email_delivery: string;
  email_mode: string;
  google_play: string;
  ai: string;
  cors: string;
  production_release: string;
};

type AIUsage = {
  total_requests: number;
  requests_24h: number;
  requests_7d: number;
  unique_users_7d: number;
  prompt_chars_7d: number;
  response_chars_7d: number;
};

type BillingPlan = {
  id: string;
  code: string;
  name: string;
  access_level: string;
  billing_period: string;
  google_play_product_id: string | null;
  price: number | string;
  currency: string;
  description: string | null;
  features: Record<string, unknown> | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

type Payment = {
  id: string;
  user_id: string;
  user_email: string;
  billing_plan_id: string | null;
  billing_plan_name: string | null;
  amount: number | string;
  currency: string;
  payment_method: string;
  provider: string | null;
  reference: string | null;
  status: string;
  notes: string | null;
  received_at: string;
  recorded_by_admin_email: string | null;
  created_at: string;
};

type UserDetail = {
  user: UserRow;
  country: string | null;
  state: string | null;
  city: string | null;
  postal_code: string | null;
  last_ip_address: string | null;
  last_user_agent: string | null;
  location_updated_at: string | null;
  payments: Payment[];
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
  created_at: string;
};

type SecurityEvent = {
  id: string;
  user_email: string | null;
  event_type: string;
  description: string | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
};

type Section =
  | "overview"
  | "users"
  | "plans"
  | "payments"
  | "subscriptions"
  | "ai"
  | "security"
  | "logs";

const nav: { key: Section; label: string; hint: string }[] = [
  { key: "overview", label: "Overview", hint: "Command center" },
  { key: "users", label: "Users", hint: "People" },
  { key: "plans", label: "Plans", hint: "Create & price" },
  { key: "payments", label: "Payments", hint: "Received" },
  { key: "subscriptions", label: "Subscriptions", hint: "Access" },
  { key: "ai", label: "AI Usage", hint: "Consumption" },
  { key: "security", label: "Security", hint: "Login activity" },
  { key: "logs", label: "Admin Logs", hint: "Changes" },
];

function formatDate(value: string | null | undefined) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("en-IN", { dateStyle: "medium" }).format(new Date(value));
}

function formatDateTime(value: string | null | undefined) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("en-IN", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function money(value: number | string, currency = "INR") {
  const amount = Number(value);
  return new Intl.NumberFormat("en-IN", { style: "currency", currency }).format(Number.isFinite(amount) ? amount : 0);
}

function badgeClass(value: string | null | undefined) {
  if (!value) return "badge";
  const normalized = value.toLowerCase();
  if (["active", "pro", "paid", "received", "ready"].includes(normalized)) return "badge good";
  if (["trial", "free", "pending"].includes(normalized)) return "badge warn";
  if (["expired", "cancelled", "suspended", "deleted", "failed", "refunded"].includes(normalized)) return "badge bad";
  return "badge";
}

export default function AdminDashboard() {
  const router = useRouter();
  const [section, setSection] = useState<Section>("overview");
  const [overview, setOverview] = useState<Overview | null>(null);
  const [users, setUsers] = useState<UserRow[]>([]);
  const [subscriptions, setSubscriptions] = useState<SubscriptionSummary | null>(null);
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [ai, setAI] = useState<AIUsage | null>(null);
  const [security, setSecurity] = useState<SecurityEvent[]>([]);
  const [actionLogs, setActionLogs] = useState<ActionLog[]>([]);
  const [plans, setPlans] = useState<BillingPlan[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [selectedUser, setSelectedUser] = useState<UserRow | null>(null);
  const [showPlanModal, setShowPlanModal] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await Promise.all([
        fetchAdminOverview(),
        fetchAdminUsers(),
        fetchAdminSubscriptions(),
        fetchAdminAIUsage(),
        fetchAdminSecurityEvents(),
        fetchAdminActionLogs(),
        fetchSystemReadiness(),
        fetchBillingPlans(),
        fetchPayments(),
      ]);
      setOverview(data[0]);
      setUsers(data[1]);
      setSubscriptions(data[2]);
      setAI(data[3]);
      setSecurity(data[4]);
      setActionLogs(data[5]);
      setReadiness(data[6]);
      setPlans(data[7]);
      setPayments(data[8]);
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

  const totalReceived = useMemo(
    () => payments.filter((item) => item.status === "received").reduce((sum, item) => sum + Number(item.amount), 0),
    [payments],
  );

  async function logout() {
    await fetch("/api/session/logout", { method: "POST", credentials: "same-origin" });
    router.replace("/login");
    router.refresh();
  }

  async function testEmailDelivery() {
    try {
      const result = await sendAdminTestEmail();
      window.alert("Test email sent to " + (result?.recipient ?? "your admin email"));
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to send test email");
    }
  }

  const kpis = [
    ["Total users", overview?.total_users ?? "—", String(overview?.registrations_7d ?? "—") + " joined in 7 days"],
    ["Paid subscribers", overview?.paid_users ?? "—", "Active Pro access"],
    ["Payments received", money(totalReceived), String(payments.length) + " payment records"],
    ["Active trials", overview?.active_trials ?? "—", "Conversion opportunity"],
    ["Transactions", overview?.transactions ?? "—", "Finance records"],
    ["Security events", overview?.security_events_24h ?? "—", "Last 24 hours"],
  ];

  return (
    <main className="admin-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">F</div>
          <div><strong>FinPilot</strong><small>Operations Console</small></div>
        </div>
        <nav className="nav" aria-label="Admin sections">
          {nav.map((item) => (
            <button key={item.key} className={section === item.key ? "active" : ""} onClick={() => setSection(item.key)}>
              <span>{item.label}</span><small>{item.hint}</small>
            </button>
          ))}
        </nav>
        <div className="sidebar-foot">
          <button className="btn btn-danger" style={{ width: "100%" }} onClick={logout}>Sign out</button>
        </div>
      </aside>

      <section className="main">
        <header className="topbar">
          <div>
            <span className="eyebrow">Hastron Ventures · FinPilot</span>
            <h1>{nav.find((item) => item.key === section)?.label}</h1>
            <p className="subtitle">
              {section === "overview" && "Simple operating view of customers, revenue, subscriptions and app security."}
              {section === "users" && "Comfortable customer cards with location, plan, payment and account controls."}
              {section === "plans" && "Create and manage your own sellable FinPilot plans."}
              {section === "payments" && "Record and review money received from customers."}
              {section === "subscriptions" && "Monitor free, trial, active, expired and cancelled access."}
              {section === "ai" && "Track FinPilot AI usage."}
              {section === "security" && "Review sign-ins, IP addresses and device information."}
              {section === "logs" && "Permanent audit trail of administrator changes."}
            </p>
          </div>
          <div className="actions">
            <button className="btn" onClick={load}>{loading ? "Refreshing…" : "Refresh"}</button>
            <button className="btn" onClick={testEmailDelivery}>Test email</button>
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
                  <div><h2>Quick actions</h2><p>Common admin work without searching through tables.</p></div>
                </div>
                <div className="quick-actions">
                  <button className="quick-action" onClick={() => setSection("users")}><strong>Manage users</strong><span>Plans, location, suspend or delete</span></button>
                  <button className="quick-action" onClick={() => setShowPaymentModal(true)}><strong>Record payment</strong><span>Add money received from a customer</span></button>
                  <button className="quick-action" onClick={() => setShowPlanModal(true)}><strong>Create plan</strong><span>Monthly, yearly or custom pricing</span></button>
                  <button className="quick-action" onClick={() => setSection("security")}><strong>Security</strong><span>Login IP and device activity</span></button>
                </div>
              </article>

              <article className="card panel">
                <div className="section-header"><div><h2>System health</h2><p>Production readiness without exposing secrets.</p></div></div>
                <div className="status-stack">
                  <StatusLine label="Database" value={readiness?.database ?? "—"} />
                  <StatusLine label="Email" value={readiness?.email_delivery ?? "—"} />
                  <StatusLine label="Google Play" value={readiness?.google_play ?? "—"} />
                  <StatusLine label="AI provider" value={readiness?.ai ?? "—"} />
                  <StatusLine label="Production release" value={readiness?.production_release ?? "—"} />
                </div>
              </article>
            </div>

            <section className="section">
              <div className="section-header">
                <div><h2>Newest customers</h2><p>Open any card for full user details.</p></div>
                <button className="btn" onClick={() => setSection("users")}>All users</button>
              </div>
              <UserCards users={users.slice(0, 6)} onManage={setSelectedUser} />
            </section>
          </>
        )}

        {section === "users" && (
          <section className="section">
            <div className="section-header responsive-header">
              <div><h2>Customers</h2><p>{visibleUsers.length} accounts</p></div>
              <input className="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search name, email, plan or status" />
            </div>
            <UserCards users={visibleUsers} onManage={setSelectedUser} />
          </section>
        )}

        {section === "plans" && (
          <section className="section">
            <div className="section-header">
              <div><h2>Billing plans</h2><p>Create plans and use them while activating customer accounts.</p></div>
              <button className="btn primary" onClick={() => setShowPlanModal(true)}>+ Create plan</button>
            </div>
            <div className="plan-grid">
              {plans.map((plan) => (
                <article className="card plan-card" key={plan.id}>
                  <div className="plan-card-head">
                    <div><span className={plan.is_active ? "badge good" : "badge bad"}>{plan.is_active ? "Active" : "Inactive"}</span><h3>{plan.name}</h3></div>
                    <span className="plan-code">{plan.code}</span>
                  </div>
                  <div className="plan-price">{money(plan.price, plan.currency)}</div>
                  <div className="kpi-note">{plan.billing_period} · {plan.access_level.toUpperCase()} access</div>
                  <p>{plan.description || "No description"}</p>
                </article>
              ))}
              {!plans.length && <div className="empty card">No custom plans yet. Create your first plan.</div>}
            </div>
          </section>
        )}

        {section === "payments" && (
          <section className="section">
            <div className="section-header">
              <div><h2>Payments received</h2><p>Total recorded: {money(totalReceived)}</p></div>
              <button className="btn primary" onClick={() => setShowPaymentModal(true)}>+ Record payment</button>
            </div>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Received</th><th>User</th><th>Plan</th><th>Amount</th><th>Method</th><th>Reference</th><th>Status</th><th>Recorded by</th></tr></thead>
                <tbody>
                  {payments.map((payment) => (
                    <tr key={payment.id}>
                      <td>{formatDateTime(payment.received_at)}</td>
                      <td>{payment.user_email}</td>
                      <td>{payment.billing_plan_name ?? "Manual / no plan"}</td>
                      <td><strong>{money(payment.amount, payment.currency)}</strong></td>
                      <td>{payment.payment_method}</td>
                      <td>{payment.reference ?? "—"}</td>
                      <td><span className={badgeClass(payment.status)}>{payment.status}</span></td>
                      <td>{payment.recorded_by_admin_email ?? "System"}</td>
                    </tr>
                  ))}
                  {!payments.length && <tr><td colSpan={8} className="empty">No payment records yet.</td></tr>}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {section === "subscriptions" && (
          <>
            <div className="grid kpis">
              {[
                ["Active paid", subscriptions?.active_paid_users ?? "—", "Pro customers"],
                ["Trials", subscriptions?.trial_users ?? "—", "Evaluating"],
                ["Free", subscriptions?.free_users ?? "—", "Free access"],
                ["Expired", subscriptions?.expired_users ?? "—", "Access ended"],
                ["Cancelled", subscriptions?.cancelled_users ?? "—", "Cancelled"],
              ].map(([label, value, note]) => (
                <article className="card kpi" key={String(label)}><div className="kpi-label">{label}</div><div className="kpi-value">{value}</div><div className="kpi-note">{note}</div></article>
              ))}
            </div>
            <section className="section"><UserCards users={users} onManage={setSelectedUser} /></section>
          </>
        )}

        {section === "ai" && (
          <div className="grid kpis">
            {[
              ["All-time requests", ai?.total_requests ?? "—", "Recorded calls"],
              ["Last 24 hours", ai?.requests_24h ?? "—", "Recent demand"],
              ["Last 7 days", ai?.requests_7d ?? "—", "Weekly traffic"],
              ["Weekly users", ai?.unique_users_7d ?? "—", "Unique users"],
              ["Weekly characters", ((ai?.prompt_chars_7d ?? 0) + (ai?.response_chars_7d ?? 0)).toLocaleString("en-IN"), "Prompt + response"],
            ].map(([label, value, note]) => (
              <article className="card kpi" key={String(label)}><div className="kpi-label">{label}</div><div className="kpi-value">{value}</div><div className="kpi-note">{note}</div></article>
            ))}
          </div>
        )}

        {section === "security" && (
          <section className="section">
            <div className="section-header"><div><h2>Security activity</h2><p>Login events with IP and device details.</p></div></div>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Time</th><th>Event</th><th>User</th><th>Description</th><th>IP</th><th>Device</th></tr></thead>
                <tbody>
                  {security.map((event) => (
                    <tr key={event.id}>
                      <td>{formatDateTime(event.created_at)}</td>
                      <td><span className="badge">{event.event_type.replaceAll("_", " ")}</span></td>
                      <td>{event.user_email ?? "System"}</td>
                      <td>{event.description ?? "—"}</td>
                      <td>{event.ip_address ?? "—"}</td>
                      <td>{event.user_agent ? event.user_agent.slice(0, 70) : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {section === "logs" && (
          <section className="section">
            <div className="section-header"><div><h2>Admin action logs</h2><p>Who changed what, when and why.</p></div></div>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Time</th><th>Admin</th><th>User</th><th>Action</th><th>Reason</th><th>Before</th><th>After</th><th>IP</th></tr></thead>
                <tbody>
                  {actionLogs.map((log) => (
                    <tr key={log.id}>
                      <td>{formatDateTime(log.created_at)}</td><td>{log.actor_admin_email ?? "—"}</td><td>{log.target_user_email ?? "—"}</td>
                      <td><span className="badge">{log.action.replaceAll("_", " ")}</span></td><td>{log.reason}</td>
                      <td><code>{log.before_state ? JSON.stringify(log.before_state) : "—"}</code></td>
                      <td><code>{log.after_state ? JSON.stringify(log.after_state) : "—"}</code></td><td>{log.ip_address ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {selectedUser && <ManageUserModal user={selectedUser} plans={plans} onClose={() => setSelectedUser(null)} onSaved={async () => { setSelectedUser(null); await load(); }} />}
        {showPlanModal && <CreatePlanModal onClose={() => setShowPlanModal(false)} onSaved={async () => { setShowPlanModal(false); await load(); }} />}
        {showPaymentModal && <RecordPaymentModal users={users} plans={plans} onClose={() => setShowPaymentModal(false)} onSaved={async () => { setShowPaymentModal(false); await load(); }} />}
      </section>
    </main>
  );
}

function StatusLine({ label, value }: { label: string; value: string }) {
  return <div className="status-line"><span>{label}</span><span className={badgeClass(value)}>{value.replaceAll("_", " ")}</span></div>;
}

function UserCards({ users, onManage }: { users: UserRow[]; onManage: (user: UserRow) => void }) {
  if (!users.length) return <div className="empty card">No users found.</div>;
  return (
    <div className="user-card-grid">
      {users.map((user) => (
        <article className="card user-card" key={user.id}>
          <div className="user-card-top">
            <div className="avatar">{(user.full_name || user.email).slice(0, 1).toUpperCase()}</div>
            <div className="user-card-identity">
              <strong>{user.full_name || "Unnamed user"}</strong>
              <span>{user.email}</span>
            </div>
            {user.is_admin && <span className="badge">Admin</span>}
          </div>
          <div className="user-card-badges">
            <span className={badgeClass(user.user_status)}>{user.user_status}</span>
            <span className={badgeClass(user.plan_code)}>{user.billing_plan_name || user.plan_code || "No plan"}</span>
            <span className={user.email_verified ? "badge good" : "badge warn"}>{user.email_verified ? "Email verified" : "Email pending"}</span>
          </div>
          <div className="user-facts">
            <div><span>Plan status</span><strong>{user.entitlement_status || "—"}</strong></div>
            <div><span>Paid until</span><strong>{formatDate(user.paid_until)}</strong></div>
            <div><span>Joined</span><strong>{formatDate(user.created_at)}</strong></div>
          </div>
          <button className="btn primary user-manage" onClick={() => onManage(user)}>Open full user details</button>
        </article>
      ))}
    </div>
  );
}

function ManageUserModal({ user, plans, onClose, onSaved }: { user: UserRow; plans: BillingPlan[]; onClose: () => void; onSaved: () => Promise<void> }) {
  const [detail, setDetail] = useState<UserDetail | null>(null);
  const [userStatus, setUserStatus] = useState(user.user_status);
  const [planCode, setPlanCode] = useState(user.plan_code ?? "free");
  const [billingPlanId, setBillingPlanId] = useState("");
  const [entitlementStatus, setEntitlementStatus] = useState(user.entitlement_status ?? "expired");
  const [trialEndsAt, setTrialEndsAt] = useState(user.trial_ends_at ? user.trial_ends_at.slice(0, 10) : "");
  const [paidUntil, setPaidUntil] = useState(user.paid_until ? user.paid_until.slice(0, 10) : "");
  const [country, setCountry] = useState("");
  const [stateName, setStateName] = useState("");
  const [city, setCity] = useState("");
  const [postalCode, setPostalCode] = useState("");
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchAdminUserDetail(user.id).then((data: UserDetail) => {
      setDetail(data);
      setBillingPlanId(data.user.billing_plan_id || "");
      setCountry(data.country || "");
      setStateName(data.state || "");
      setCity(data.city || "");
      setPostalCode(data.postal_code || "");
    }).catch((err: Error) => setError(err.message));
  }, [user.id]);

  async function saveAccess() {
    if (reason.trim().length < 3) return setError("Enter a reason for this change.");
    setSaving(true); setError("");
    try {
      await updateAdminUser(user.id, {
        user_status: userStatus,
        plan_code: planCode,
        ...(billingPlanId ? { billing_plan_id: billingPlanId } : {}),
        entitlement_status: entitlementStatus,
        trial_ends_at: trialEndsAt ? new Date(trialEndsAt + "T23:59:59Z").toISOString() : null,
        paid_until: paidUntil ? new Date(paidUntil + "T23:59:59Z").toISOString() : null,
        reason: reason.trim(),
      });
      await onSaved();
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to save"); }
    finally { setSaving(false); }
  }

  async function saveLocation() {
    if (reason.trim().length < 3) return setError("Enter a reason for this change.");
    setSaving(true); setError("");
    try {
      await updateAdminUserLocation(user.id, { country, state: stateName, city, postal_code: postalCode, reason: reason.trim() });
      const data = await fetchAdminUserDetail(user.id);
      setDetail(data);
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to save location"); }
    finally { setSaving(false); }
  }

  async function revokeSessions() {
    if (reason.trim().length < 3) return setError("Enter a reason first.");
    if (!window.confirm("Sign this user out from every device?")) return;
    setSaving(true);
    try { await revokeAdminUserSessions(user.id, reason.trim()); await onSaved(); }
    catch (err) { setError(err instanceof Error ? err.message : "Unable to revoke sessions"); }
    finally { setSaving(false); }
  }

  async function deleteUser() {
    if (user.is_admin) return setError("Admin accounts cannot be deleted here.");
    const confirmation = window.prompt("This disables the account and revokes all sessions. Type DELETE to continue.");
    if (confirmation !== "DELETE") return;
    const deleteReason = window.prompt("Reason for deleting this user:");
    if (!deleteReason || deleteReason.trim().length < 3) return setError("A deletion reason is required.");
    setSaving(true);
    try { await deleteAdminUser(user.id, deleteReason.trim()); await onSaved(); }
    catch (err) { setError(err instanceof Error ? err.message : "Unable to delete user"); }
    finally { setSaving(false); }
  }

  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <section className="card modal modal-wide" onMouseDown={(e) => e.stopPropagation()}>
        <div className="section-header">
          <div><span className="eyebrow">Customer 360°</span><h2>{user.full_name || user.email}</h2><p>{user.email}</p></div>
          <button className="btn" onClick={onClose}>Close</button>
        </div>

        <div className="user-detail-summary">
          <div><span>Account</span><strong className={badgeClass(userStatus)}>{userStatus}</strong></div>
          <div><span>Plan</span><strong>{detail?.user.billing_plan_name || planCode}</strong></div>
          <div><span>Last login IP</span><strong>{detail?.last_ip_address || "Not captured yet"}</strong></div>
          <div><span>Location</span><strong>{[detail?.city, detail?.state, detail?.country].filter(Boolean).join(", ") || "Not set"}</strong></div>
        </div>

        <div className="detail-section">
          <h3>Access & plan</h3>
          <div className="control-grid">
            <label className="field"><span>Account status</span><select value={userStatus} onChange={(e) => setUserStatus(e.target.value)}><option value="active">Active</option><option value="suspended">Suspended</option></select></label>
            <label className="field"><span>Custom plan</span><select value={billingPlanId} onChange={(e) => setBillingPlanId(e.target.value)}><option value="">No custom plan</option>{plans.filter((p) => p.is_active).map((plan) => <option key={plan.id} value={plan.id}>{plan.name} · {money(plan.price, plan.currency)}</option>)}</select></label>
            <label className="field"><span>Access level</span><select value={planCode} onChange={(e) => setPlanCode(e.target.value)}><option value="free">Free</option><option value="pro">Pro</option></select></label>
            <label className="field"><span>Plan status</span><select value={entitlementStatus} onChange={(e) => setEntitlementStatus(e.target.value)}><option value="trial">Trial</option><option value="active">Active</option><option value="expired">Expired</option><option value="cancelled">Cancelled</option></select></label>
            <label className="field"><span>Trial ends</span><input type="date" value={trialEndsAt} onChange={(e) => setTrialEndsAt(e.target.value)} /></label>
            <label className="field"><span>Paid until</span><input type="date" value={paidUntil} onChange={(e) => setPaidUntil(e.target.value)} /></label>
          </div>
          <button className="btn primary detail-save" disabled={saving} onClick={saveAccess}>Save access & plan</button>
        </div>

        <div className="detail-section">
          <h3>User location & device</h3>
          <div className="control-grid">
            <label className="field"><span>Country</span><input value={country} onChange={(e) => setCountry(e.target.value)} /></label>
            <label className="field"><span>State</span><input value={stateName} onChange={(e) => setStateName(e.target.value)} /></label>
            <label className="field"><span>City</span><input value={city} onChange={(e) => setCity(e.target.value)} /></label>
            <label className="field"><span>Postal code</span><input value={postalCode} onChange={(e) => setPostalCode(e.target.value)} /></label>
          </div>
          <div className="device-box"><strong>Last login IP:</strong> {detail?.last_ip_address || "Not captured yet"}<br/><strong>Device:</strong> {detail?.last_user_agent || "Not captured yet"}</div>
          <button className="btn detail-save" disabled={saving} onClick={saveLocation}>Save location</button>
        </div>

        <div className="detail-section">
          <h3>Payment history</h3>
          <div className="payment-mini-list">
            {detail?.payments?.map((payment) => <div key={payment.id}><span>{formatDate(payment.received_at)} · {payment.payment_method}</span><strong>{money(payment.amount, payment.currency)}</strong></div>)}
            {detail && !detail.payments.length && <div className="empty">No payments recorded for this user.</div>}
          </div>
        </div>

        <label className="field"><span>Reason for admin change *</span><input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Example: Customer paid yearly plan by bank transfer" /></label>
        {error && <div className="error" style={{ marginTop: 12 }}>{error}</div>}

        <div className="danger-zone">
          <div><h3>Danger zone</h3><p>Security actions are logged and require confirmation.</p></div>
          <div className="danger-actions">
            <button className="btn btn-danger" disabled={saving} onClick={revokeSessions}>Revoke all sessions</button>
            <button className="btn delete-btn" disabled={saving || user.is_admin} onClick={deleteUser}>Delete user</button>
          </div>
        </div>
      </section>
    </div>
  );
}

function CreatePlanModal({ onClose, onSaved }: { onClose: () => void; onSaved: () => Promise<void> }) {
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [price, setPrice] = useState("");
  const [period, setPeriod] = useState("monthly");
  const [googlePlayProductId, setGooglePlayProductId] = useState("");
  const [access, setAccess] = useState("pro");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");

  async function save() {
    try {
      await createBillingPlan({ code: code.trim().toLowerCase(), name: name.trim(), access_level: access, billing_period: period, google_play_product_id: googlePlayProductId.trim() || null, price: Number(price), currency: "INR", description: description.trim() || null, features: {}, is_active: true });
      await onSaved();
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to create plan"); }
  }

  return <div className="modal-backdrop" onMouseDown={onClose}><section className="card modal" onMouseDown={(e) => e.stopPropagation()}>
    <div className="section-header"><div><span className="eyebrow">New billing plan</span><h2>Create plan</h2></div><button className="btn" onClick={onClose}>Close</button></div>
    <div className="control-grid">
      <label className="field"><span>Plan name</span><input value={name} onChange={(e) => setName(e.target.value)} placeholder="FinPilot Pro Yearly" /></label>
      <label className="field"><span>Plan code</span><input value={code} onChange={(e) => setCode(e.target.value.replace(/[^a-zA-Z0-9_-]/g, "").toLowerCase())} placeholder="pro_yearly" /></label>
      <label className="field"><span>Price (INR)</span><input type="number" min="0" value={price} onChange={(e) => setPrice(e.target.value)} /></label>
      <label className="field"><span>Google Play product ID</span><input value={googlePlayProductId} onChange={(e) => setGooglePlayProductId(e.target.value.trim())} placeholder="finpilot_pro_monthly" /></label>
      <label className="field"><span>Billing period</span><select value={period} onChange={(e) => setPeriod(e.target.value)}><option value="monthly">Monthly</option><option value="quarterly">Quarterly</option><option value="yearly">Yearly</option><option value="lifetime">Lifetime</option><option value="custom">Custom</option></select></label>
      <label className="field"><span>Access level</span><select value={access} onChange={(e) => setAccess(e.target.value)}><option value="pro">Pro</option><option value="free">Free</option></select></label>
    </div>
    <label className="field"><span>Description</span><input value={description} onChange={(e) => setDescription(e.target.value)} /></label>
    {error && <div className="error" style={{ marginTop: 12 }}>{error}</div>}
    <button className="btn primary detail-save" onClick={save}>Create plan</button>
  </section></div>;
}

function RecordPaymentModal({ users, plans, onClose, onSaved }: { users: UserRow[]; plans: BillingPlan[]; onClose: () => void; onSaved: () => Promise<void> }) {
  const [userId, setUserId] = useState(users[0]?.id || "");
  const [planId, setPlanId] = useState("");
  const [amount, setAmount] = useState("");
  const [method, setMethod] = useState("bank_transfer");
  const [reference, setReference] = useState("");
  const [notes, setNotes] = useState("");
  const [reason, setReason] = useState("Payment received and verified");
  const [error, setError] = useState("");

  async function save() {
    try {
      await recordPayment({
        user_id: userId,
        billing_plan_id: planId || null,
        amount: Number(amount),
        currency: "INR",
        payment_method: method,
        provider: "manual_admin",
        reference: reference.trim() || null,
        status: "received",
        notes: notes.trim() || null,
        received_at: new Date().toISOString(),
        reason,
      });
      await onSaved();
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to record payment"); }
  }

  return <div className="modal-backdrop" onMouseDown={onClose}><section className="card modal" onMouseDown={(e) => e.stopPropagation()}>
    <div className="section-header"><div><span className="eyebrow">Payment received</span><h2>Record payment</h2></div><button className="btn" onClick={onClose}>Close</button></div>
    <div className="control-grid">
      <label className="field"><span>User</span><select value={userId} onChange={(e) => setUserId(e.target.value)}>{users.map((u) => <option key={u.id} value={u.id}>{u.full_name || u.email} · {u.email}</option>)}</select></label>
      <label className="field"><span>Plan</span><select value={planId} onChange={(e) => { setPlanId(e.target.value); const plan = plans.find((p) => p.id === e.target.value); if (plan) setAmount(String(plan.price)); }}><option value="">No plan</option>{plans.map((p) => <option key={p.id} value={p.id}>{p.name} · {money(p.price, p.currency)}</option>)}</select></label>
      <label className="field"><span>Amount (INR)</span><input type="number" min="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} /></label>
      <label className="field"><span>Payment method</span><select value={method} onChange={(e) => setMethod(e.target.value)}><option value="bank_transfer">Bank transfer</option><option value="upi">UPI</option><option value="cash">Cash</option><option value="card">Card</option><option value="google_play">Google Play</option><option value="other">Other</option></select></label>
      <label className="field"><span>Reference / transaction ID</span><input value={reference} onChange={(e) => setReference(e.target.value)} /></label>
    </div>
    <label className="field"><span>Notes</span><input value={notes} onChange={(e) => setNotes(e.target.value)} /></label>
    <label className="field"><span>Reason / verification note</span><input value={reason} onChange={(e) => setReason(e.target.value)} /></label>
    {error && <div className="error" style={{ marginTop: 12 }}>{error}</div>}
    <button className="btn primary detail-save" onClick={save}>Save payment received</button>
  </section></div>;
}
