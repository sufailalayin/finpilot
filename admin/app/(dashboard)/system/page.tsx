"use client";

import React, { useEffect, useState } from "react";
import { fetchSystemReadiness, sendAdminTestEmail } from "../../../lib/api";
import type { Readiness } from "../../../lib/types/admin";
import { StatusBadge } from "../../../components/admin/StatusBadge";
import { useToast } from "../../../components/admin/Toast";

export default function SystemHealthPage() {
  const { showToast } = useToast();
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [loading, setLoading] = useState(true);
  const [testingEmail, setTestingEmail] = useState(false);

  async function loadReadiness() {
    setLoading(true);
    try {
      const data = await fetchSystemReadiness();
      setReadiness(data);
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to load system readiness", "error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReadiness();
  }, []);

  async function handleTestEmail() {
    setTestingEmail(true);
    try {
      const res = await sendAdminTestEmail();
      showToast(`Test email successfully sent to ${res.recipient}`, "success");
      await loadReadiness();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Test email delivery failed", "error");
    } finally {
      setTestingEmail(false);
    }
  }

  const subsystems = [
    { name: "Primary Database", status: readiness?.database, desc: "PostgreSQL / SQLite connection pool and query readiness" },
    { name: "Email Delivery Service", status: readiness?.email_delivery, desc: `SMTP / Mail transport mode (${readiness?.email_mode || "standard"})` },
    { name: "AI Inference Provider", status: readiness?.ai, desc: "LLM / Gemini API integration and response synthesis" },
    { name: "Google Play Billing", status: readiness?.google_play, desc: "In-app purchases and subscription receipt validation" },
    { name: "CORS & Domain Policy", status: readiness?.cors, desc: "Origin validation and cross-site request security" },
    { name: "Production Mobile Build", status: readiness?.production_release, desc: "Build artifact integrity and signing validation" },
  ];

  return (
    <div className="dashboard-content">
      <div className="page-header-row">
        <div>
          <h2>System Health & Infrastructure</h2>
          <p className="text-muted">
            Inspect live production service availability, email transport readiness, and API integrations.
          </p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-secondary" onClick={loadReadiness} disabled={loading}>
            {loading ? "Checking..." : "Recheck Health"}
          </button>
          <button className="btn btn-primary" onClick={handleTestEmail} disabled={testingEmail}>
            {testingEmail ? "Sending..." : "✉️ Send Test Email"}
          </button>
        </div>
      </div>

      {/* OVERALL HEALTH BANNER */}
      <div className="system-health-banner">
        <div className="banner-left">
          <div className="health-big-icon">
            {readiness?.status === "ready" || readiness?.status === "healthy" ? "✓" : "!"}
          </div>
          <div>
            <h3>
              System Status:{" "}
              {readiness?.status === "ready" || readiness?.status === "healthy"
                ? "Operational & Ready"
                : "Attention Required"}
            </h3>
            <p className="text-muted">
              Environment: <strong>{readiness?.environment?.toUpperCase() || "PRODUCTION"}</strong> · Backend API active
            </p>
          </div>
        </div>
        <div>
          <StatusBadge status={readiness?.status} variant="system" />
        </div>
      </div>

      {/* SUBSYSTEM CHECKS GRID */}
      <div className="subsystems-grid" style={{ marginTop: "24px" }}>
        {subsystems.map((sub, i) => (
          <div key={i} className="card panel subsystem-card">
            <div className="subsystem-header">
              <h4>{sub.name}</h4>
              <StatusBadge status={sub.status} variant="system" />
            </div>
            <p className="subsystem-desc">{sub.desc}</p>
            <div className="subsystem-footer">
              <span className="font-mono text-sm">Status: {sub.status?.toUpperCase() || "CHECKING"}</span>
            </div>
          </div>
        ))}
      </div>

      {/* EMAIL TESTING TOOL PANEL */}
      <div className="card panel" style={{ marginTop: "24px" }}>
        <div className="section-header">
          <div>
            <h4>Email Delivery Verification Tool</h4>
            <p className="text-muted text-sm">
              Trigger a test verification email to your administrator inbox to confirm SMTP credentials
            </p>
          </div>
          <button className="btn btn-primary" onClick={handleTestEmail} disabled={testingEmail}>
            {testingEmail ? "Dispatching..." : "Send Test Email"}
          </button>
        </div>
        <div style={{ marginTop: "12px" }}>
          <p className="text-sm">
            Current Email Mode: <strong>{readiness?.email_mode || "—"}</strong>
          </p>
          <p className="text-muted text-sm" style={{ marginTop: "4px" }}>
            If mail credentials are not configured, FinPilot logs test mail previews to stdout safely without crashing.
          </p>
        </div>
      </div>
    </div>
  );
}
