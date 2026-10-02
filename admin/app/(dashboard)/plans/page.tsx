"use client";

import React, { useEffect, useState } from "react";
import {
  createBillingPlan,
  deleteBillingPlan,
  fetchBillingPlans,
  updateBillingPlan,
} from "../../../lib/api";
import { formatDate, formatMoney } from "../../../lib/format";
import type { AdminBillingPlanRow } from "../../../lib/types/admin";
import { Modal } from "../../../components/admin/Modal";
import { StatusBadge } from "../../../components/admin/StatusBadge";
import { useToast } from "../../../components/admin/Toast";

export default function PlansPage() {
  const { showToast } = useToast();
  const [plans, setPlans] = useState<AdminBillingPlanRow[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal states
  const [createOpen, setCreateOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState<AdminBillingPlanRow | null>(null);
  const [deletingPlan, setDeletingPlan] = useState<AdminBillingPlanRow | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Create form fields
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [accessLevel, setAccessLevel] = useState("pro");
  const [billingPeriod, setBillingPeriod] = useState("monthly");
  const [price, setPrice] = useState("499");
  const [currency, setCurrency] = useState("INR");
  const [googlePlayId, setGooglePlayId] = useState("");
  const [description, setDescription] = useState("");
  const [isActive, setIsActive] = useState(true);

  // Edit form fields
  const [editName, setEditName] = useState("");
  const [editAccessLevel, setEditAccessLevel] = useState("pro");
  const [editBillingPeriod, setEditBillingPeriod] = useState("monthly");
  const [editPrice, setEditPrice] = useState("");
  const [editCurrency, setEditCurrency] = useState("INR");
  const [editGooglePlayId, setEditGooglePlayId] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editIsActive, setEditIsActive] = useState(true);
  const [editReason, setEditReason] = useState("");

  // Delete field
  const [deleteReason, setDeleteReason] = useState("");

  async function loadPlans() {
    setLoading(true);
    try {
      const data = await fetchBillingPlans();
      setPlans(data);
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to load billing plans", "error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPlans();
  }, []);

  function openEdit(plan: AdminBillingPlanRow) {
    setEditingPlan(plan);
    setEditName(plan.name);
    setEditAccessLevel(plan.access_level);
    setEditBillingPeriod(plan.billing_period);
    setEditPrice(String(plan.price));
    setEditCurrency(plan.currency);
    setEditGooglePlayId(plan.google_play_product_id || "");
    setEditDescription(plan.description || "");
    setEditIsActive(plan.is_active);
    setEditReason("");
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!code.trim() || !name.trim()) {
      showToast("Code and name are required", "warning");
      return;
    }
    setSubmitting(true);
    try {
      await createBillingPlan({
        code: code.trim().toLowerCase(),
        name: name.trim(),
        access_level: accessLevel,
        billing_period: billingPeriod,
        price: parseFloat(price) || 0,
        currency: currency.trim().toUpperCase(),
        google_play_product_id: googlePlayId.trim() || null,
        description: description.trim() || null,
        is_active: isActive,
      });
      showToast("Billing plan created successfully", "success");
      setCreateOpen(false);
      // Reset
      setCode("");
      setName("");
      setDescription("");
      await loadPlans();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to create plan", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleUpdate(e: React.FormEvent) {
    e.preventDefault();
    if (!editingPlan || !editReason.trim()) {
      showToast("Please provide an audit reason", "warning");
      return;
    }
    setSubmitting(true);
    try {
      await updateBillingPlan(editingPlan.id, {
        name: editName.trim(),
        access_level: editAccessLevel,
        billing_period: editBillingPeriod,
        price: parseFloat(editPrice) || 0,
        currency: editCurrency.trim().toUpperCase(),
        google_play_product_id: editGooglePlayId.trim() || null,
        description: editDescription.trim() || null,
        is_active: editIsActive,
        reason: editReason.trim(),
      });
      showToast("Billing plan updated", "success");
      setEditingPlan(null);
      await loadPlans();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to update plan", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(e: React.FormEvent) {
    e.preventDefault();
    if (!deletingPlan) return;
    if (deletingPlan.active_subscribers_count > 0) {
      showToast("Cannot delete plan with active subscribers", "error");
      return;
    }
    setSubmitting(true);
    try {
      await deleteBillingPlan(deletingPlan.id, deleteReason.trim() || "Deleted unused plan");
      showToast("Billing plan deleted", "success");
      setDeletingPlan(null);
      await loadPlans();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to delete plan", "error");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="dashboard-content">
      <div className="page-header-row">
        <div>
          <h2>Billing Plans & Tiers</h2>
          <p className="text-muted">
            Configure pricing tiers, billing cycles, Google Play subscription IDs, and active features.
          </p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-primary" onClick={() => setCreateOpen(true)}>
            + Create New Plan
          </button>
        </div>
      </div>

      {/* PLANS CARDS GRID */}
      <div className="plans-cards-grid">
        {plans.map((p) => (
          <div key={p.id} className="plan-card">
            <div className="plan-card-head">
              <div>
                <span className="plan-code-badge">{p.code}</span>
                <h3 className="plan-card-title">{p.name}</h3>
              </div>
              <StatusBadge status={p.is_active ? "active" : "inactive"} variant="plan" />
            </div>

            <div className="plan-price-row">
              <span className="plan-price-val">{formatMoney(p.price, p.currency)}</span>
              <span className="plan-period-val">/ {p.billing_period}</span>
            </div>

            <div className="plan-details-list">
              <div className="plan-detail-line">
                <span className="detail-key">Access Level:</span>
                <span className="detail-val font-mono">{p.access_level.toUpperCase()}</span>
              </div>
              <div className="plan-detail-line">
                <span className="detail-key">Subscribers:</span>
                <span className="detail-val">
                  <strong>{p.active_subscribers_count}</strong> active
                </span>
              </div>
              {p.google_play_product_id && (
                <div className="plan-detail-line">
                  <span className="detail-key">Play Store ID:</span>
                  <span className="detail-val font-mono text-sm">
                    {p.google_play_product_id}
                  </span>
                </div>
              )}
            </div>

            {p.description && <p className="plan-desc-text">{p.description}</p>}

            <div className="plan-actions-footer">
              <button
                className="btn btn-sm btn-secondary"
                onClick={() => openEdit(p)}
              >
                Edit Plan
              </button>
              <button
                className="btn btn-sm btn-danger-outline"
                onClick={() => {
                  setDeletingPlan(p);
                  setDeleteReason("");
                }}
              >
                Delete
              </button>
            </div>
          </div>
        ))}

        {!loading && plans.length === 0 && (
          <div className="card panel" style={{ gridColumn: "1 / -1", textAlign: "center", padding: "40px" }}>
            <p className="text-muted">No custom billing plans configured yet.</p>
            <button className="btn btn-primary" onClick={() => setCreateOpen(true)} style={{ marginTop: "12px" }}>
              Create First Plan
            </button>
          </div>
        )}
      </div>

      {/* CREATE PLAN MODAL */}
      <Modal
        isOpen={createOpen}
        onClose={() => setCreateOpen(false)}
        title="Create New Billing Plan"
        description="Add a new subscription tier for FinPilot customers"
      >
        <form onSubmit={handleCreate} className="admin-form">
          <div className="form-grid-2">
            <div className="form-group">
              <label>Plan Code (Unique slug)</label>
              <input
                type="text"
                required
                placeholder="e.g. pro_monthly"
                value={code}
                onChange={(e) => setCode(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Plan Name</label>
              <input
                type="text"
                required
                placeholder="e.g. FinPilot Pro (Monthly)"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
          </div>

          <div className="form-grid-2">
            <div className="form-group">
              <label>Access Level</label>
              <select value={accessLevel} onChange={(e) => setAccessLevel(e.target.value)}>
                <option value="pro">Pro</option>
                <option value="free">Free</option>
              </select>
            </div>
            <div className="form-group">
              <label>Billing Period</label>
              <select value={billingPeriod} onChange={(e) => setBillingPeriod(e.target.value)}>
                <option value="monthly">Monthly</option>
                <option value="quarterly">Quarterly</option>
                <option value="yearly">Yearly</option>
                <option value="lifetime">Lifetime</option>
              </select>
            </div>
          </div>

          <div className="form-grid-2">
            <div className="form-group">
              <label>Price</label>
              <input
                type="number"
                step="0.01"
                required
                value={price}
                onChange={(e) => setPrice(e.target.value)}
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

          <div className="form-group">
            <label>Google Play Product ID (Optional)</label>
            <input
              type="text"
              placeholder="e.g. finpilot_pro_monthly"
              value={googlePlayId}
              onChange={(e) => setGooglePlayId(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea
              rows={2}
              placeholder="Features and perks included with this tier..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div className="form-group-checkbox">
            <label>
              <input
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
              />
              <span>Activate plan immediately for new customers</span>
            </label>
          </div>

          <div className="modal-actions">
            <button
              type="button"
              className="btn"
              onClick={() => setCreateOpen(false)}
              disabled={submitting}
            >
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? "Creating..." : "Create Plan"}
            </button>
          </div>
        </form>
      </Modal>

      {/* EDIT PLAN MODAL */}
      <Modal
        isOpen={Boolean(editingPlan)}
        onClose={() => setEditingPlan(null)}
        title={`Edit Plan: ${editingPlan?.name}`}
        description="Update pricing, period, and status with audit justification"
      >
        <form onSubmit={handleUpdate} className="admin-form">
          <div className="form-grid-2">
            <div className="form-group">
              <label>Plan Name</label>
              <input
                type="text"
                required
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Access Level</label>
              <select value={editAccessLevel} onChange={(e) => setEditAccessLevel(e.target.value)}>
                <option value="pro">Pro</option>
                <option value="free">Free</option>
              </select>
            </div>
          </div>

          <div className="form-grid-2">
            <div className="form-group">
              <label>Price</label>
              <input
                type="number"
                step="0.01"
                required
                value={editPrice}
                onChange={(e) => setEditPrice(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Billing Period</label>
              <select value={editBillingPeriod} onChange={(e) => setEditBillingPeriod(e.target.value)}>
                <option value="monthly">Monthly</option>
                <option value="quarterly">Quarterly</option>
                <option value="yearly">Yearly</option>
                <option value="lifetime">Lifetime</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Google Play Product ID</label>
            <input
              type="text"
              value={editGooglePlayId}
              onChange={(e) => setEditGooglePlayId(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea
              rows={2}
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
            />
          </div>

          <div className="form-group-checkbox">
            <label>
              <input
                type="checkbox"
                checked={editIsActive}
                onChange={(e) => setEditIsActive(e.target.checked)}
              />
              <span>Plan is Active and available for selection</span>
            </label>
          </div>

          <div className="form-group">
            <label>Audit Reason (Required)</label>
            <input
              type="text"
              required
              placeholder="e.g. Updated annual pricing for Q4 promotion..."
              value={editReason}
              onChange={(e) => setEditReason(e.target.value)}
            />
          </div>

          <div className="modal-actions">
            <button
              type="button"
              className="btn"
              onClick={() => setEditingPlan(null)}
              disabled={submitting}
            >
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </form>
      </Modal>

      {/* DELETE PLAN MODAL */}
      <Modal
        isOpen={Boolean(deletingPlan)}
        onClose={() => setDeletingPlan(null)}
        title={`Delete Plan: ${deletingPlan?.name}`}
        description="Verify safety constraints before removing this plan"
      >
        <form onSubmit={handleDelete} className="admin-form">
          {deletingPlan && deletingPlan.active_subscribers_count > 0 ? (
            <div className="alert-box-warning">
              <h4>⚠️ Cannot Delete Plan with Active Subscribers</h4>
              <p>
                This plan currently has <strong>{deletingPlan.active_subscribers_count}</strong> active subscriber(s).
                Deleting it would leave existing customers without a valid billing plan.
              </p>
              <p style={{ marginTop: "8px" }}>
                <strong>Recommendation:</strong> Instead of deleting, edit the plan and deactivate it (set Active to false) to prevent new subscribers while preserving existing accounts.
              </p>
              <div className="modal-actions">
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => setDeletingPlan(null)}
                >
                  Understood
                </button>
              </div>
            </div>
          ) : (
            <>
              <p>
                Are you sure you want to permanently delete plan <strong>{deletingPlan?.name}</strong>?
                This action is audited and cannot be undone.
              </p>
              <div className="form-group">
                <label>Audit Reason</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Deprecated test tier with zero subscribers"
                  value={deleteReason}
                  onChange={(e) => setDeleteReason(e.target.value)}
                />
              </div>
              <div className="modal-actions">
                <button
                  type="button"
                  className="btn"
                  onClick={() => setDeletingPlan(null)}
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-danger" disabled={submitting}>
                  {submitting ? "Deleting..." : "Confirm Delete"}
                </button>
              </div>
            </>
          )}
        </form>
      </Modal>
    </div>
  );
}
