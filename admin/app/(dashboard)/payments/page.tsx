"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  fetchAdminAnalyticsRevenue,
  fetchAdminUsers,
  fetchBillingPlans,
  fetchPayments,
  getExportUrl,
  recordPayment,
  voidPayment,
} from "../../../lib/api";
import { formatDate, formatDateTime, formatMoney, formatNumber } from "../../../lib/format";
import type {
  AdminAnalyticsRevenue,
  AdminBillingPlanRow,
  AdminPaginationMeta,
  AdminPaymentRow,
  AdminUserRow,
} from "../../../lib/types/admin";
import { type Column, DataTable } from "../../../components/admin/DataTable";
import { Modal } from "../../../components/admin/Modal";
import { StatCard } from "../../../components/admin/StatCard";
import { StatusBadge } from "../../../components/admin/StatusBadge";
import { useToast } from "../../../components/admin/Toast";

export default function PaymentsPage() {
  const { showToast } = useToast();
  const [payments, setPayments] = useState<AdminPaymentRow[]>([]);
  const [revenueStats, setRevenueStats] = useState<AdminAnalyticsRevenue | null>(null);
  const [meta, setMeta] = useState<AdminPaginationMeta>({
    page: 1,
    page_size: 25,
    total: 0,
    total_pages: 1,
  });
  const [loading, setLoading] = useState(false);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [methodFilter, setMethodFilter] = useState("");

  // Modals
  const [recordOpen, setRecordOpen] = useState(false);
  const [voidingPayment, setVoidingPayment] = useState<AdminPaymentRow | null>(null);
  const [voidReason, setVoidReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Plans & Users for Record form
  const [plans, setPlans] = useState<AdminBillingPlanRow[]>([]);
  const [usersList, setUsersList] = useState<AdminUserRow[]>([]);
  const [userSearchText, setUserSearchText] = useState("");

  // Record Form Fields
  const [selectedUserId, setSelectedUserId] = useState("");
  const [selectedPlanId, setSelectedPlanId] = useState("");
  const [amount, setAmount] = useState("");
  const [currency, setCurrency] = useState("INR");
  const [paymentMethod, setPaymentMethod] = useState("UPI");
  const [provider, setProvider] = useState("");
  const [reference, setReference] = useState("");
  const [notes, setNotes] = useState("");
  const [recordReason, setRecordReason] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [paymentsRes, statsRes] = await Promise.all([
        fetchPayments({
          page: meta.page,
          page_size: meta.page_size,
          q: searchQuery.trim() || undefined,
          status: statusFilter || undefined,
          payment_method: methodFilter || undefined,
        }),
        fetchAdminAnalyticsRevenue("30d").catch(() => null),
      ]);
      setPayments(paymentsRes.items);
      setMeta(paymentsRes.meta);
      setRevenueStats(statsRes);
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to load payments", "error");
    } finally {
      setLoading(false);
    }
  }, [meta.page, meta.page_size, searchQuery, statusFilter, methodFilter, showToast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    fetchBillingPlans()
      .then(setPlans)
      .catch(() => {});
  }, []);

  // Search users for record modal
  useEffect(() => {
    if (!recordOpen) return;
    const timer = setTimeout(() => {
      fetchAdminUsers({ q: userSearchText.trim() || undefined, page_size: 10 })
        .then((res) => setUsersList(res.items))
        .catch(() => {});
    }, 200);
    return () => clearTimeout(timer);
  }, [recordOpen, userSearchText]);

  async function handleRecord(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedUserId || !amount || !recordReason.trim()) {
      showToast("User, amount, and audit reason are required", "warning");
      return;
    }
    setSubmitting(true);
    try {
      await recordPayment({
        user_id: selectedUserId,
        billing_plan_id: selectedPlanId || null,
        amount: parseFloat(amount) || 0,
        currency: currency.trim().toUpperCase(),
        payment_method: paymentMethod,
        provider: provider.trim() || null,
        reference: reference.trim() || null,
        notes: notes.trim() || null,
        reason: recordReason.trim(),
      });
      showToast("Payment recorded successfully", "success");
      setRecordOpen(false);
      // Reset
      setSelectedUserId("");
      setSelectedPlanId("");
      setAmount("");
      setReference("");
      setNotes("");
      setRecordReason("");
      await loadData();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to record payment", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleVoid(e: React.FormEvent) {
    e.preventDefault();
    if (!voidingPayment || !voidReason.trim()) {
      showToast("Please provide a reason to void this payment", "warning");
      return;
    }
    setSubmitting(true);
    try {
      await voidPayment(voidingPayment.id, voidReason.trim());
      showToast("Payment voided successfully", "success");
      setVoidingPayment(null);
      setVoidReason("");
      await loadData();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to void payment", "error");
    } finally {
      setSubmitting(false);
    }
  }

  const columns: Column<AdminPaymentRow>[] = [
    {
      key: "received_at",
      header: "Date Received",
      width: "140px",
      render: (p) => formatDateTime(p.received_at),
    },
    {
      key: "user_email",
      header: "Customer",
      render: (p) => (
        <div>
          <span className="font-mono text-sm">{p.user_email}</span>
        </div>
      ),
    },
    {
      key: "billing_plan_name",
      header: "Plan",
      width: "160px",
      render: (p) => p.billing_plan_name || "Custom / Direct",
    },
    {
      key: "amount",
      header: "Amount",
      width: "140px",
      render: (p) => (
        <strong className={p.status === "voided" ? "text-strikethrough text-muted" : "text-good"}>
          {formatMoney(p.amount, p.currency)}
        </strong>
      ),
    },
    {
      key: "payment_method",
      header: "Method",
      width: "120px",
      render: (p) => <span className="font-mono text-sm">{p.payment_method}</span>,
    },
    {
      key: "reference",
      header: "Reference",
      width: "160px",
      render: (p) => (
        <span className="font-mono text-sm text-muted">
          {p.reference ? p.reference : "—"}
        </span>
      ),
    },
    {
      key: "status",
      header: "Status",
      width: "120px",
      render: (p) => <StatusBadge status={p.status} variant="payment" />,
    },
    {
      key: "actions",
      header: "Actions",
      width: "100px",
      align: "right",
      render: (p) =>
        p.status !== "voided" ? (
          <button
            className="btn btn-sm btn-danger-outline"
            onClick={() => {
              setVoidingPayment(p);
              setVoidReason("");
            }}
          >
            Void
          </button>
        ) : (
          <span className="text-muted text-sm">Voided</span>
        ),
    },
  ];

  return (
    <div className="dashboard-content">
      <div className="page-header-row">
        <div>
          <h2>Payment Records & Accounting</h2>
          <p className="text-muted">
            Audit customer payments, reconcile bank or gateway records, and safely void transactions.
          </p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-primary" onClick={() => setRecordOpen(true)}>
            + Record Manual Payment
          </button>
          <a href={getExportUrl("payments")} download className="btn btn-secondary">
            📥 Export CSV
          </a>
        </div>
      </div>

      {/* REVENUE STATS CARDS */}
      <div className="kpi-grid">
        <StatCard
          title="TOTAL RECORDED REVENUE"
          value={formatMoney(revenueStats?.total_revenue)}
          subtext={`${formatNumber(revenueStats?.total_transactions)} recorded payments`}
          trend={{ value: "All time", isPositive: true }}
          icon="💳"
        />

        <StatCard
          title="VOIDED / REVERSED REVENUE"
          value={formatMoney(revenueStats?.voided_revenue)}
          subtext="Excluded from valid ledger"
          trend={{ value: "Voided", isNeutral: true }}
          icon="↩️"
        />

        <StatCard
          title="FILTERED RECORDS"
          value={formatNumber(meta.total)}
          subtext="Matching current filters"
          trend={{ value: `${meta.total_pages} pages`, isNeutral: true }}
          icon="📋"
        />
      </div>

      {/* FILTER CONTROLS */}
      <div className="filter-controls-card">
        <div className="search-input-box">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            className="input-search"
            placeholder="Search reference, customer email, notes, or provider..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setMeta((prev) => ({ ...prev, page: 1 }));
            }}
          />
        </div>

        <div className="filters-row">
          <select
            className="filter-select"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setMeta((prev) => ({ ...prev, page: 1 }));
            }}
          >
            <option value="">Status: All</option>
            <option value="received">Received</option>
            <option value="pending">Pending</option>
            <option value="voided">Voided</option>
            <option value="refunded">Refunded</option>
          </select>

          <select
            className="filter-select"
            value={methodFilter}
            onChange={(e) => {
              setMethodFilter(e.target.value);
              setMeta((prev) => ({ ...prev, page: 1 }));
            }}
          >
            <option value="">Method: All</option>
            <option value="UPI">UPI</option>
            <option value="Card">Card</option>
            <option value="NetBanking">Net Banking</option>
            <option value="GooglePlay">Google Play</option>
            <option value="BankTransfer">Bank Transfer</option>
            <option value="Cash">Cash</option>
          </select>

          {(searchQuery || statusFilter || methodFilter) && (
            <button
              className="btn btn-sm btn-link"
              onClick={() => {
                setSearchQuery("");
                setStatusFilter("");
                setMethodFilter("");
                setMeta((prev) => ({ ...prev, page: 1 }));
              }}
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* PAYMENTS DATA TABLE */}
      <div className="card-table-container">
        <DataTable
          columns={columns}
          data={payments}
          keyExtractor={(p) => p.id}
          loading={loading}
          emptyMessage="No payment records match the current filter criteria."
          pagination={{
            page: meta.page,
            pageSize: meta.page_size,
            total: meta.total,
            totalPages: meta.total_pages,
            onPageChange: (p) => setMeta((prev) => ({ ...prev, page: p })),
            onPageSizeChange: (s) => setMeta((prev) => ({ ...prev, page_size: s, page: 1 })),
          }}
        />
      </div>

      {/* RECORD PAYMENT MODAL */}
      <Modal
        isOpen={recordOpen}
        onClose={() => setRecordOpen(false)}
        title="Record Manual Payment"
        description="Add a verified customer payment into the financial ledger"
      >
        <form onSubmit={handleRecord} className="admin-form">
          <div className="form-group">
            <label>Customer Search & Selection</label>
            <input
              type="text"
              placeholder="Search customer email..."
              value={userSearchText}
              onChange={(e) => setUserSearchText(e.target.value)}
            />
            <select
              required
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value)}
              style={{ marginTop: "6px" }}
            >
              <option value="">Select customer ({usersList.length} options)...</option>
              {usersList.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.full_name ? `${u.full_name} (${u.email})` : u.email}
                </option>
              ))}
            </select>
          </div>

          <div className="form-grid-2">
            <div className="form-group">
              <label>Billing Plan</label>
              <select
                value={selectedPlanId}
                onChange={(e) => {
                  const pid = e.target.value;
                  setSelectedPlanId(pid);
                  const plan = plans.find((p) => p.id === pid);
                  if (plan) {
                    setAmount(String(plan.price));
                    setCurrency(plan.currency);
                  }
                }}
              >
                <option value="">Direct / Custom Amount</option>
                {plans.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.currency} {p.price})
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Payment Method</label>
              <select
                value={paymentMethod}
                onChange={(e) => setPaymentMethod(e.target.value)}
              >
                <option value="UPI">UPI</option>
                <option value="Card">Card</option>
                <option value="NetBanking">Net Banking</option>
                <option value="GooglePlay">Google Play</option>
                <option value="BankTransfer">Bank Transfer</option>
                <option value="Cash">Cash</option>
              </select>
            </div>
          </div>

          <div className="form-grid-2">
            <div className="form-group">
              <label>Amount</label>
              <input
                type="number"
                step="0.01"
                required
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Currency</label>
              <input
                type="text"
                required
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
              />
            </div>
          </div>

          <div className="form-grid-2">
            <div className="form-group">
              <label>Provider (Optional)</label>
              <input
                type="text"
                placeholder="e.g. Razorpay, HDFC, Stripe"
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Reference / Transaction ID</label>
              <input
                type="text"
                placeholder="e.g. UPI-928374928"
                value={reference}
                onChange={(e) => setReference(e.target.value)}
              />
            </div>
          </div>

          <div className="form-group">
            <label>Notes</label>
            <input
              type="text"
              placeholder="Internal memo or notes..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Audit Reason (Required)</label>
            <input
              type="text"
              required
              placeholder="e.g. Verified bank receipt via customer support"
              value={recordReason}
              onChange={(e) => setRecordReason(e.target.value)}
            />
          </div>

          <div className="modal-actions">
            <button
              type="button"
              className="btn"
              onClick={() => setRecordOpen(false)}
              disabled={submitting}
            >
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? "Recording..." : "Record Payment"}
            </button>
          </div>
        </form>
      </Modal>

      {/* VOID PAYMENT MODAL */}
      <Modal
        isOpen={Boolean(voidingPayment)}
        onClose={() => setVoidingPayment(null)}
        title="Void Payment Record"
        description="Preserve financial audit trail with void semantics"
      >
        <form onSubmit={handleVoid} className="admin-form">
          <div className="alert-box-warning">
            <p>
              Voiding payment of <strong>{formatMoney(voidingPayment?.amount, voidingPayment?.currency)}</strong>{" "}
              from customer <strong>{voidingPayment?.user_email}</strong>.
            </p>
            <p className="text-sm" style={{ marginTop: "6px" }}>
              Voiding updates this record&apos;s status to &ldquo;voided&rdquo;, deducts the amount from financial analytics, and creates an immutable audit log entry.
            </p>
          </div>

          <div className="form-group" style={{ marginTop: "14px" }}>
            <label>Reason for voiding (Required)</label>
            <input
              type="text"
              required
              placeholder="e.g. Customer bank dispute or duplicate entry..."
              value={voidReason}
              onChange={(e) => setVoidReason(e.target.value)}
            />
          </div>

          <div className="modal-actions">
            <button
              type="button"
              className="btn"
              onClick={() => setVoidingPayment(null)}
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
    </div>
  );
}
