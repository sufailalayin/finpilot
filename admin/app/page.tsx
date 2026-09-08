"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { fetchAdminOverview, fetchAdminUsers } from "../lib/api";

type Overview = {
  total_users: number;
  active_trials: number;
  paid_users: number;
  expired_entitlements: number;
  ai_requests: number;
};

type UserRow = {
  id: string;
  email: string;
  full_name: string | null;
  entitlement_status: string | null;
  plan_code: string | null;
  trial_ends_at: string | null;
  paid_until: string | null;
  created_at: string;
};

export default function AdminDashboard() {
  const router = useRouter();
  const [overview, setOverview] = useState<Overview | null>(null);
  const [users, setUsers] = useState<UserRow[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("finpilot_admin_token");

    if (!token) {
      router.replace("/login");
      return;
    }

    Promise.all([
      fetchAdminOverview(token),
      fetchAdminUsers(token),
    ])
      .then(([overviewData, userData]) => {
        setOverview(overviewData);
        setUsers(userData);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Unable to load admin data");
      });
  }, [router]);

  function logout() {
    localStorage.removeItem("finpilot_admin_token");
    router.push("/login");
  }

  const cards = [
    ["Users", overview?.total_users ?? "—"],
    ["Active trials", overview?.active_trials ?? "—"],
    ["Paid subscribers", overview?.paid_users ?? "—"],
    ["Expired", overview?.expired_entitlements ?? "—"],
    ["AI requests", overview?.ai_requests ?? "—"],
  ];

  return (
    <main style={{ maxWidth: 1200, margin: "0 auto", padding: 32 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 16 }}>
        <div>
          <p style={{ marginBottom: 4 }}>Hastron Ventures</p>
          <h1 style={{ marginTop: 0 }}>FinPilot Admin</h1>
        </div>
        <button onClick={logout} style={{ height: 40 }}>Sign out</button>
      </div>

      {error ? <p style={{ color: "crimson" }}>{error}</p> : null}

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: 16,
          marginTop: 32,
        }}
      >
        {cards.map(([label, value]) => (
          <article
            key={String(label)}
            style={{ border: "1px solid #ddd", borderRadius: 16, padding: 20 }}
          >
            <small>{label}</small>
            <h2>{value}</h2>
          </article>
        ))}
      </section>

      <section style={{ marginTop: 40 }}>
        <h2>Users</h2>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                {["Name", "Email", "Plan", "Status", "Trial ends", "Paid until", "Joined"].map((heading) => (
                  <th key={heading} style={{ textAlign: "left", padding: 12, borderBottom: "1px solid #ddd" }}>
                    {heading}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td style={{ padding: 12, borderBottom: "1px solid #eee" }}>{user.full_name ?? "—"}</td>
                  <td style={{ padding: 12, borderBottom: "1px solid #eee" }}>{user.email}</td>
                  <td style={{ padding: 12, borderBottom: "1px solid #eee" }}>{user.plan_code ?? "—"}</td>
                  <td style={{ padding: 12, borderBottom: "1px solid #eee" }}>{user.entitlement_status ?? "—"}</td>
                  <td style={{ padding: 12, borderBottom: "1px solid #eee" }}>{user.trial_ends_at ? new Date(user.trial_ends_at).toLocaleDateString() : "—"}</td>
                  <td style={{ padding: 12, borderBottom: "1px solid #eee" }}>{user.paid_until ? new Date(user.paid_until).toLocaleDateString() : "—"}</td>
                  <td style={{ padding: 12, borderBottom: "1px solid #eee" }}>{new Date(user.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
