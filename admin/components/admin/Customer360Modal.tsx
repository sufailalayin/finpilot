"use client";

import React, { useEffect, useState } from "react";
import {
  deleteAdminUser,
  fetchAdminUserDetail,
  restoreAdminUser,
  revokeAdminUserSessions,
  suspendAdminUser,
  updateAdminUser,
  updateAdminUserLocation,
  voidPayment,
} from "../../lib/api";
import { formatDate, formatDateTime, formatMoney, truncate } from "../../lib/format";
import type { AdminBillingPlanRow, AdminUserDetail } from "../../lib/types/admin";
import { Modal } from "./Modal";
import { StatusBadge } from "./StatusBadge";
import { useToast } from "./Toast";

interface Customer360ModalProps {
  userId: string | null;
  plans: AdminBillingPlanRow[];
  onClose: () => void;
  onUserUpdated?: () => void;
}

export function Customer360Modal({
  userId,
  plans,
  onClose,
  onUserUpdated,
}: Customer360ModalProps) {
  const { showToast } = useToast();
  const [detail, setDetail] = useState<AdminUserDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<
    "overview" | "subscription" | "payments" | "security" | "history" | "danger"
  >("overview");

  // Form states
  const [submitting, setSubmitting] = useState(false);

  // Edit Access state
  const [editAccessOpen, setEditAccessOpen] = useState(false);
  const [editStatus, setEditStatus] = useState("");
  const [editPlanCode, setEditPlanCode] = useState("");
  const [editBillingPlanId, setEditBillingPlanId] = useState("");
  const [editEntitlementStatus, setEditEntitlementStatus] = useState("");
  const [editReason, setEditReason] = useState("");

  // Edit Location state
  const [editLocationOpen, setEditLocationOpen] = useState(false);
  const [locCountry, setLocCountry] = useState("");
  const [locState, setLocState] = useState("");
  const [locCity, setLocCity] = useState("");
  const [locPostal, setLocPostal] = useState("");
  const [locReason, setLocReason] = useState("");

  // Suspend/Restore state
  const [suspendReason, setSuspendReason] = useState("");
  const [showSuspendConfirm, setShowSuspendConfirm] = useState(false);

  // Void payment state
  const [voidingPaymentId, setVoidingPaymentId] = useState<string | null>(null);
  const [voidReason, setVoidReason] = useState("");

  // Delete state
  const [deleteConfirmation, setDeleteConfirmation] = useState("");
  const [deleteReason, setDeleteReason] = useState("");
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  async function loadDetail(id: string) {
    setLoading(true);
    try {
      const data = await fetchAdminUserDetail(id);
      setDetail(data);
      // Pre-fill edit fields
      setEditStatus(data.user.user_status);
      setEditPlanCode(data.user.plan_code || "free");
      setEditBillingPlanId(data.user.billing_plan_id || "");
      setEditEntitlementStatus(data.user.entitlement_status || "none");
      setLocCountry(data.country || "");
      setLocState(data.state || "");
      setLocCity(data.city || "");
      setLocPostal(data.postal_code || "");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to load user details", "error");
      onClose();
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (userId) {
      loadDetail(userId);
    } else {
      setDetail(null);
    }
  }, [userId]);

  if (!userId) return null;

  async function handleUpdateAccess(e: React.FormEvent) {
    e.preventDefault();
    if (!editReason.trim()) {
      showToast("Please provide an audit reason", "warning");
      return;
    }
    setSubmitting(true);
    try {
      await updateAdminUser(userId!, {
        user_status: editStatus,
        plan_code: editPlanCode,
        billing_plan_id: editBillingPlanId || null,
        entitlement_status: editEntitlementStatus,
        reason: editReason.trim(),
      });
      showToast("User access updated successfully", "success");
      setEditAccessOpen(false);
      setEditReason("");
      await loadDetail(userId!);
      onUserUpdated?.();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to update access", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleUpdateLocation(e: React.FormEvent) {
    e.preventDefault();
    if (!locReason.trim()) {
      showToast("Please provide an audit reason", "warning");
      return;
    }
    setSubmitting(true);
    try {
      await updateAdminUserLocation(userId!, {
        country: locCountry.trim() || null,
        state: locState.trim() || null,
        city: locCity.trim() || null,
        postal_code: locPostal.trim() || null,
        reason: locReason.trim(),
      });
      showToast("Customer location updated", "success");
      setEditLocationOpen(false);
      setLocReason("");
      await loadDetail(userId!);
      onUserUpdated?.();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to update location", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleToggleSuspend() {
    if (!suspendReason.trim()) {
      showToast("Please provide an audit reason", "warning");
      return;
    }
    setSubmitting(true);
    try {
      if (detail?.user.user_status === "suspended") {
        await restoreAdminUser(userId!, suspendReason.trim());
        showToast("Account restored to Active", "success");
      } else {
        await suspendAdminUser(userId!, suspendReason.trim());
        showToast("Account suspended and sessions invalidated", "warning");
      }
      setShowSuspendConfirm(false);
      setSuspendReason("");
      await loadDetail(userId!);
      onUserUpdated?.();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to update account status", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRevokeSessions() {
    const reason = window.prompt("Enter reason for invalidating all user sessions:");
    if (!reason || !reason.trim()) return;

    try {
      await revokeAdminUserSessions(userId!, reason.trim());
      showToast("All active sessions revoked", "success");
      await loadDetail(userId!);
      onUserUpdated?.();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to revoke sessions", "error");
    }
  }

  async function handleVoidPayment(e: React.FormEvent) {
    e.preventDefault();
    if (!voidingPaymentId || !voidReason.trim()) {
      showToast("Please provide a reason to void this payment", "warning");
      return;
    }
    setSubmitting(true);
    try {
      await voidPayment(voidingPaymentId, voidReason.trim());
      showToast("Payment record voided successfully", "success");
      setVoidingPaymentId(null);
      setVoidReason("");
      await loadDetail(userId!);
      onUserUpdated?.();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to void payment", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDeleteUser(e: React.FormEvent) {
    e.preventDefault();
    if (!deleteReason.trim()) {
      showToast("Please enter an audit reason", "warning");
      return;
    }
    setSubmitting(true);
    try {
      await deleteAdminUser(userId!, deleteReason.trim(), deleteConfirmation.trim());
      showToast("User account has been deleted", "success");
      setShowDeleteConfirm(false);
      onClose();
      onUserUpdated?.();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to delete user", "error");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal
      isOpen={Boolean(userId)}
      onClose={onClose}
      title="Customer 360 Profile"
      description="Holistic operational view of identity, subscriptions, security, and financial activity"
      maxWidth="900px"
    >
      {loading || !detail ? (
        <div className="customer-loading">
          <div className="table-skeleton" style={{ height: "40px", marginBottom: "12px" }} />
          <div className="table-skeleton" style={{ height: "180px" }} />
        </div>
      ) : (
        <div className="customer-360-container">
          {/* Header Banner */}
          <div className="customer-banner">
            <div className="customer-avatar-large">
              {(detail.user.full_name || detail.user.email).charAt(0).toUpperCase()}
            </div>
            <div className="customer-banner-info">
              <div className="customer-name-row">
                <h2>{detail.user.full_name || "Unnamed Customer"}</h2>
                <StatusBadge status={detail.user.user_status} variant="user" />
                <StatusBadge status={detail.user.plan_code} variant="plan" />
                {detail.user.email_verified ? (
                  <span className="pill-verified">✓ Email Verified</span>
                ) : (
                  <span className="pill-unverified">⚠ Email Unverified</span>
                )}
              </div>
              <div className="customer-email-row">
                <span>{detail.user.email}</span>
                <span className="dot-sep">•</span>
                <span className="user-id-code">ID: {detail.user.id}</span>
                <span className="dot-sep">•</span>
                <span>Joined {formatDate(detail.user.created_at)}</span>
              </div>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="customer-tabs">
            <button
              className={`c-tab ${activeTab === "overview" ? "active" : ""}`}
              onClick={() => setActiveTab("overview")}
            >
              👤 Overview & Location
            </button>
            <button
              className={`c-tab ${activeTab === "subscription" ? "active" : ""}`}
              onClick={() => setActiveTab("subscription")}
            >
              💳 Plan & Entitlements
            </button>
            <button
              className={`c-tab ${activeTab === "payments" ? "active" : ""}`}
              onClick={() => setActiveTab("payments")}
            >
              💵 Payments ({detail.payments.length})
            </button>
            <button
              className={`c-tab ${activeTab === "security" ? "active" : ""}`}
              onClick={() => setActiveTab("security")}
            >
              🛡️ Security & Sessions
            </button>
            <button
              className={`c-tab ${activeTab === "history" ? "active" : ""}`}
              onClick={() => setActiveTab("history")}
            >
              📜 Audit Trail ({detail.recent_admin_actions.length})
            </button>
            <button
              className={`c-tab ${activeTab === "danger" ? "active" : ""}`}
              onClick={() => setActiveTab("danger")}
            >
              ⚠️ Actions & Danger
            </button>
          </div>

          {/* TAB 1: OVERVIEW & LOCATION */}
          {activeTab === "overview" && (
            <div className="c-tab-content">
              <div className="c-grid-2">
                <div className="c-panel">
                  <div className="c-panel-header">
                    <h4>Customer Profile</h4>
                  </div>
                  <div className="c-info-list">
                    <div className="c-info-row">
                      <span className="c-label">Full Name:</span>
                      <span className="c-val">{detail.user.full_name || "—"}</span>
                    </div>
                    <div className="c-info-row">
                      <span className="c-label">Email:</span>
                      <span className="c-val">{detail.user.email}</span>
                    </div>
                    <div className="c-info-row">
                      <span className="c-label">Account Role:</span>
                      <span className="c-val">{detail.user.is_admin ? "Administrator" : "Standard User"}</span>
                    </div>
                    <div className="c-info-row">
                      <span className="c-label">Registration Date:</span>
                      <span className="c-val">{formatDateTime(detail.user.created_at)}</span>
                    </div>
                    <div className="c-info-row">
                      <span className="c-label">Last IP Address:</span>
                      <span className="c-val font-mono">{detail.last_ip_address || "—"}</span>
                    </div>
                    <div className="c-info-row">
                      <span className="c-label">Last Device / Agent:</span>
                      <span className="c-val" title={detail.last_user_agent || ""}>
                        {truncate(detail.last_user_agent, 40) || "—"}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="c-panel">
                  <div className="c-panel-header">
                    <h4>Location Address</h4>
                    <button
                      className="btn-link"
                      onClick={() => setEditLocationOpen(true)}
                    >
                      Edit Location
                    </button>
                  </div>
                  <div className="c-info-list">
                    <div className="c-info-row">
                      <span className="c-label">Country:</span>
                      <span className="c-val">{detail.country || "—"}</span>
                    </div>
                    <div className="c-info-row">
                      <span className="c-label">State / Province:</span>
                      <span className="c-val">{detail.state || "—"}</span>
                    </div>
                    <div className="c-info-row">
                      <span className="c-label">City:</span>
                      <span className="c-val">{detail.city || "—"}</span>
                    </div>
                    <div className="c-info-row">
                      <span className="c-label">Postal / Zip Code:</span>
                      <span className="c-val">{detail.postal_code || "—"}</span>
                    </div>
                    <div className="c-info-row">
                      <span className="c-label">Updated:</span>
                      <span className="c-val">{formatDateTime(detail.location_updated_at)}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Safe Financial Summary */}
              <div className="c-panel" style={{ marginTop: "16px" }}>
                <div className="c-panel-header">
                  <h4>Safe Financial Data Summary</h4>
                  <span className="text-muted text-sm">Aggregated entity counts (zero sensitive balances shown)</span>
                </div>
                <div className="c-metrics-row">
                  <div className="c-metric-box">
                    <span className="c-m-val">{detail.financial_summary.accounts_count}</span>
                    <span className="c-m-label">Finance Accounts</span>
                  </div>
                  <div className="c-metric-box">
                    <span className="c-m-val">{detail.financial_summary.transactions_count}</span>
                    <span className="c-m-label">Transactions</span>
                  </div>
                  <div className="c-metric-box">
                    <span className="c-m-val">{detail.financial_summary.assets_count}</span>
                    <span className="c-m-label">Assets Recorded</span>
                  </div>
                  <div className="c-metric-box">
                    <span className="c-m-val">{detail.financial_summary.liabilities_count}</span>
                    <span className="c-m-label">Liabilities Recorded</span>
                  </div>
                  <div className="c-metric-box">
                    <span className="c-m-val">{formatDate(detail.financial_summary.last_activity_date)}</span>
                    <span className="c-m-label">Last Financial Activity</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: SUBSCRIPTION */}
          {activeTab === "subscription" && (
            <div className="c-tab-content">
              <div className="c-panel">
                <div className="c-panel-header">
                  <h4>Entitlement & Tier</h4>
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={() => setEditAccessOpen(true)}
                  >
                    Modify Plan Access
                  </button>
                </div>
                <div className="c-grid-2">
                  <div className="c-info-list">
                    <div className="c-info-row">
                      <span className="c-label">Plan Code:</span>
                      <span className="c-val">
                        <StatusBadge status={detail.user.plan_code} variant="plan" />
                      </span>
                    </div>
                    <div className="c-info-row">
                      <span className="c-label">Billing Plan:</span>
                      <span className="c-val">{detail.user.billing_plan_name || "Standard / None"}</span>
                    </div>
                    <div className="c-info-row">
                      <span className="c-label">Entitlement Status:</span>
                      <span className="c-val">
                        <StatusBadge status={detail.user.entitlement_status} variant="entitlement" />
                      </span>
                    </div>
                  </div>
                  <div className="c-info-list">
                    <div className="c-info-row">
                      <span className="c-label">Trial Ends At:</span>
                      <span className="c-val">{formatDate(detail.user.trial_ends_at)}</span>
                    </div>
                    <div className="c-info-row">
                      <span className="c-label">Paid Until:</span>
                      <span className="c-val">{formatDate(detail.user.paid_until)}</span>
                    </div>
                    <div className="c-info-row">
                      <span className="c-label">Account Status:</span>
                      <span className="c-val">
                        <StatusBadge status={detail.user.user_status} variant="user" />
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: PAYMENTS */}
          {activeTab === "payments" && (
            <div className="c-tab-content">
              <div className="c-panel">
                <div className="c-panel-header">
                  <h4>Recorded Payment Records</h4>
                  <span className="text-muted text-sm">Historical ledger of all payments received from this user</span>
                </div>
                {detail.payments.length === 0 ? (
                  <div className="chart-empty" style={{ height: "140px" }}>
                    <span>No payment records found for this user</span>
                  </div>
                ) : (
                  <div className="c-table-wrap">
                    <table className="datatable-table">
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Plan</th>
                          <th>Amount</th>
                          <th>Method</th>
                          <th>Reference</th>
                          <th>Status</th>
                          <th>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {detail.payments.map((p) => (
                          <tr key={p.id}>
                            <td>{formatDate(p.received_at)}</td>
                            <td>{p.billing_plan_name || "—"}</td>
                            <td><strong>{formatMoney(p.amount, p.currency)}</strong></td>
                            <td>{p.payment_method}</td>
                            <td><span className="font-mono text-sm">{p.reference || "—"}</span></td>
                            <td><StatusBadge status={p.status} variant="payment" /></td>
                            <td>
                              {p.status !== "voided" ? (
                                <button
                                  className="btn-danger-outline btn-sm"
                                  onClick={() => setVoidingPaymentId(p.id)}
                                >
                                  Void
                                </button>
                              ) : (
                                <span className="text-muted text-sm">Voided</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 4: SECURITY & SESSIONS */}
          {activeTab === "security" && (
            <div className="c-tab-content">
              <div className="c-grid-2">
                <div className="c-panel">
                  <div className="c-panel-header">
                    <h4>Active Sessions</h4>
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={handleRevokeSessions}
                    >
                      Revoke All Sessions
                    </button>
                  </div>
                  <div className="c-info-list">
                    <div className="c-info-row">
                      <span className="c-label">Active Refresh Sessions:</span>
                      <span className="c-val"><strong>{detail.active_sessions_count}</strong> active session(s)</span>
                    </div>
                    <div className="c-info-row">
                      <span className="c-label">Security Note:</span>
                      <span className="c-val text-muted text-sm">
                        Revoking will bump the user token version and immediately log the user out on all mobile & web devices.
                      </span>
                    </div>
                  </div>
                </div>

                <div className="c-panel">
                  <div className="c-panel-header">
                    <h4>Device & Network Profile</h4>
                  </div>
                  <div className="c-info-list">
                    <div className="c-info-row">
                      <span className="c-label">Recent IP Address:</span>
                      <span className="c-val font-mono">{detail.last_ip_address || "None recorded"}</span>
                    </div>
                    <div className="c-info-row">
                      <span className="c-label">User Agent:</span>
                      <span className="c-val font-mono text-sm">{detail.last_user_agent || "None recorded"}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="c-panel" style={{ marginTop: "16px" }}>
                <div className="c-panel-header">
                  <h4>Recent Security Events</h4>
                </div>
                {detail.recent_security_events.length === 0 ? (
                  <div className="chart-empty" style={{ height: "100px" }}>
                    <span>No security events recorded for this user</span>
                  </div>
                ) : (
                  <div className="c-table-wrap">
                    <table className="datatable-table">
                      <thead>
                        <tr>
                          <th>Timestamp</th>
                          <th>Event Type</th>
                          <th>IP Address</th>
                          <th>Description</th>
                        </tr>
                      </thead>
                      <tbody>
                        {detail.recent_security_events.map((ev) => (
                          <tr key={ev.id}>
                            <td>{formatDateTime(ev.created_at)}</td>
                            <td><span className="font-mono text-sm">{ev.event_type}</span></td>
                            <td><span className="font-mono text-sm">{ev.ip_address || "—"}</span></td>
                            <td>{ev.description || "—"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 5: AUDIT TRAIL */}
          {activeTab === "history" && (
            <div className="c-tab-content">
              <div className="c-panel">
                <div className="c-panel-header">
                  <h4>Administrative Actions History</h4>
                  <span className="text-muted text-sm">Permanent immutable log of changes affecting this customer</span>
                </div>
                {detail.recent_admin_actions.length === 0 ? (
                  <div className="chart-empty" style={{ height: "120px" }}>
                    <span>No administrative actions recorded for this user</span>
                  </div>
                ) : (
                  <div className="c-table-wrap">
                    <table className="datatable-table">
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Action</th>
                          <th>Admin</th>
                          <th>Reason</th>
                          <th>IP</th>
                        </tr>
                      </thead>
                      <tbody>
                        {detail.recent_admin_actions.map((act) => (
                          <tr key={act.id}>
                            <td>{formatDateTime(act.created_at)}</td>
                            <td><span className="font-mono text-sm">{act.action}</span></td>
                            <td>{act.actor_admin_email || "System"}</td>
                            <td>{act.reason}</td>
                            <td><span className="font-mono text-sm">{act.ip_address || "—"}</span></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 6: DANGER & ACTIONS */}
          {activeTab === "danger" && (
            <div className="c-tab-content">
              <div className="c-panel danger-panel">
                <h4>Account Suspension & Access Controls</h4>
                <p className="text-muted text-sm">
                  Suspension blocks the user from authenticating, synchronizing finance transactions, or using AI features.
                </p>
                <div style={{ marginTop: "12px" }}>
                  <button
                    className={`btn ${
                      detail.user.user_status === "suspended" ? "btn-primary" : "btn-warning"
                    }`}
                    onClick={() => setShowSuspendConfirm(true)}
                  >
                    {detail.user.user_status === "suspended" ? "Restore User Account" : "Suspend User Account"}
                  </button>
                </div>
              </div>

              <div className="c-panel danger-panel" style={{ marginTop: "16px" }}>
                <h4>Permanent Soft-Deletion / Archive</h4>
                <p className="text-muted text-sm">
                  Deletes customer credentials, terminates active sessions, and marks account status as deleted. This action is permanently audited.
                </p>
                <div style={{ marginTop: "12px" }}>
                  <button
                    className="btn btn-danger"
                    onClick={() => setShowDeleteConfirm(true)}
                  >
                    Delete Customer Account
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* MODAL: EDIT ACCESS */}
          <Modal
            isOpen={editAccessOpen}
            onClose={() => setEditAccessOpen(false)}
            title="Modify User Access & Plan"
            description="Update user status, plan tier, or entitlement dates with audit reason"
          >
            <form onSubmit={handleUpdateAccess} className="admin-form">
              <div className="form-group">
                <label>Account Status</label>
                <select value={editStatus} onChange={(e) => setEditStatus(e.target.value)}>
                  <option value="active">Active</option>
                  <option value="suspended">Suspended</option>
                </select>
              </div>

              <div className="form-group">
                <label>Billing Plan</label>
                <select
                  value={editBillingPlanId}
                  onChange={(e) => {
                    const pid = e.target.value;
                    setEditBillingPlanId(pid);
                    const selected = plans.find((p) => p.id === pid);
                    if (selected) {
                      setEditPlanCode(selected.access_level === "pro" ? "pro" : "free");
                    }
                  }}
                >
                  <option value="">None / Custom Tier</option>
                  {plans.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.currency} {p.price} / {p.billing_period})
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Plan Code</label>
                <select value={editPlanCode} onChange={(e) => setEditPlanCode(e.target.value)}>
                  <option value="free">Free</option>
                  <option value="pro">Pro</option>
                </select>
              </div>

              <div className="form-group">
                <label>Entitlement Status</label>
                <select
                  value={editEntitlementStatus}
                  onChange={(e) => setEditEntitlementStatus(e.target.value)}
                >
                  <option value="none">None</option>
                  <option value="trial">Trial</option>
                  <option value="active">Active</option>
                  <option value="expired">Expired</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>

              <div className="form-group">
                <label>Reason for change (Required for audit log)</label>
                <textarea
                  required
                  rows={3}
                  placeholder="e.g. Granted Pro access following manual payment confirmation..."
                  value={editReason}
                  onChange={(e) => setEditReason(e.target.value)}
                />
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="btn"
                  onClick={() => setEditAccessOpen(false)}
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? "Saving Changes..." : "Apply Access Changes"}
                </button>
              </div>
            </form>
          </Modal>

          {/* MODAL: EDIT LOCATION */}
          <Modal
            isOpen={editLocationOpen}
            onClose={() => setEditLocationOpen(false)}
            title="Update Customer Location"
            description="Manage billing country, state, city, and postal code"
          >
            <form onSubmit={handleUpdateLocation} className="admin-form">
              <div className="form-grid-2">
                <div className="form-group">
                  <label>Country</label>
                  <input
                    type="text"
                    value={locCountry}
                    onChange={(e) => setLocCountry(e.target.value)}
                    placeholder="e.g. India"
                  />
                </div>
                <div className="form-group">
                  <label>State / Province</label>
                  <input
                    type="text"
                    value={locState}
                    onChange={(e) => setLocState(e.target.value)}
                    placeholder="e.g. Kerala"
                  />
                </div>
              </div>

              <div className="form-grid-2">
                <div className="form-group">
                  <label>City</label>
                  <input
                    type="text"
                    value={locCity}
                    onChange={(e) => setLocCity(e.target.value)}
                    placeholder="e.g. Kozhikode"
                  />
                </div>
                <div className="form-group">
                  <label>Postal Code</label>
                  <input
                    type="text"
                    value={locPostal}
                    onChange={(e) => setLocPostal(e.target.value)}
                    placeholder="e.g. 673001"
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Reason (Audit log required)</label>
                <input
                  type="text"
                  required
                  value={locReason}
                  onChange={(e) => setLocReason(e.target.value)}
                  placeholder="e.g. Customer support location correction request"
                />
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="btn"
                  onClick={() => setEditLocationOpen(false)}
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? "Saving..." : "Save Location"}
                </button>
              </div>
            </form>
          </Modal>

          {/* MODAL: SUSPEND / RESTORE CONFIRM */}
          <Modal
            isOpen={showSuspendConfirm}
            onClose={() => setShowSuspendConfirm(false)}
            title={detail.user.user_status === "suspended" ? "Restore User Account" : "Suspend User Account"}
            description="State changes revoke tokens and are logged permanently"
          >
            <div className="admin-form">
              <p>
                {detail.user.user_status === "suspended"
                  ? `Restore access for customer ${detail.user.email}? This will re-enable sign-in.`
                  : `Are you sure you want to suspend customer ${detail.user.email}? All active sessions will be revoked.`}
              </p>
              <div className="form-group">
                <label>Reason (Audit required)</label>
                <input
                  type="text"
                  required
                  value={suspendReason}
                  onChange={(e) => setSuspendReason(e.target.value)}
                  placeholder="e.g. Payment failure / terms violation investigation"
                />
              </div>
              <div className="modal-actions">
                <button
                  className="btn"
                  onClick={() => setShowSuspendConfirm(false)}
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button
                  className={`btn ${
                    detail.user.user_status === "suspended" ? "btn-primary" : "btn-warning"
                  }`}
                  onClick={handleToggleSuspend}
                  disabled={submitting}
                >
                  {submitting
                    ? "Updating..."
                    : detail.user.user_status === "suspended"
                      ? "Confirm Restore"
                      : "Confirm Suspension"}
                </button>
              </div>
            </div>
          </Modal>

          {/* MODAL: VOID PAYMENT */}
          <Modal
            isOpen={Boolean(voidingPaymentId)}
            onClose={() => setVoidingPaymentId(null)}
            title="Void Payment Record"
            description="Safely void this payment record while preserving audit integrity"
          >
            <form onSubmit={handleVoidPayment} className="admin-form">
              <p className="text-warning text-sm">
                Voiding marks this transaction as voided in the financial ledger and deducts it from analytics totals. It does not erase the record.
              </p>
              <div className="form-group">
                <label>Reason for voiding (Required)</label>
                <input
                  type="text"
                  required
                  value={voidReason}
                  onChange={(e) => setVoidReason(e.target.value)}
                  placeholder="e.g. Accidental double entry / bank chargeback"
                />
              </div>
              <div className="modal-actions">
                <button
                  type="button"
                  className="btn"
                  onClick={() => setVoidingPaymentId(null)}
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-danger" disabled={submitting}>
                  {submitting ? "Voiding..." : "Confirm Void"}
                </button>
              </div>
            </form>
          </Modal>

          {/* MODAL: DELETE USER CONFIRM */}
          <Modal
            isOpen={showDeleteConfirm}
            onClose={() => setShowDeleteConfirm(false)}
            title="Delete Customer Account"
            description="Safe archiving with strict confirmation"
          >
            <form onSubmit={handleDeleteUser} className="admin-form">
              <p className="text-danger text-sm">
                Warning: To confirm, type <strong>DELETE</strong> or{" "}
                <strong>DELETE {detail.user.email}</strong> below:
              </p>
              <div className="form-group">
                <label>Confirmation phrase</label>
                <input
                  type="text"
                  required
                  value={deleteConfirmation}
                  onChange={(e) => setDeleteConfirmation(e.target.value)}
                  placeholder="DELETE"
                />
              </div>
              <div className="form-group">
                <label>Audit Reason</label>
                <input
                  type="text"
                  required
                  value={deleteReason}
                  onChange={(e) => setDeleteReason(e.target.value)}
                  placeholder="e.g. Customer GDPR account closure request"
                />
              </div>
              <div className="modal-actions">
                <button
                  type="button"
                  className="btn"
                  onClick={() => setShowDeleteConfirm(false)}
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-danger" disabled={submitting}>
                  {submitting ? "Deleting..." : "Permanently Archive User"}
                </button>
              </div>
            </form>
          </Modal>
        </div>
      )}
    </Modal>
  );
}
