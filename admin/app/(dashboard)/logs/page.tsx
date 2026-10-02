"use client";

import React, { useCallback, useEffect, useState } from "react";
import { fetchAdminActionLogs, getExportUrl } from "../../../lib/api";
import { formatDateTime } from "../../../lib/format";
import type {
  AdminActionLogRow,
  AdminPaginationMeta,
} from "../../../lib/types/admin";
import { type Column, DataTable } from "../../../components/admin/DataTable";
import { Modal } from "../../../components/admin/Modal";
import { useToast } from "../../../components/admin/Toast";

export default function ActionLogsPage() {
  const { showToast } = useToast();
  const [logs, setLogs] = useState<AdminActionLogRow[]>([]);
  const [meta, setMeta] = useState<AdminPaginationMeta>({
    page: 1,
    page_size: 25,
    total: 0,
    total_pages: 1,
  });
  const [loading, setLoading] = useState(false);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [actionFilter, setActionFilter] = useState("");

  // Inspect Modal
  const [selectedLog, setSelectedLog] = useState<AdminActionLogRow | null>(null);

  const loadLogs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchAdminActionLogs({
        page: meta.page,
        page_size: meta.page_size,
        q: searchQuery.trim() || undefined,
        action: actionFilter || undefined,
      });
      setLogs(res.items);
      setMeta(res.meta);
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to load audit logs", "error");
    } finally {
      setLoading(false);
    }
  }, [meta.page, meta.page_size, searchQuery, actionFilter, showToast]);

  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  const columns: Column<AdminActionLogRow>[] = [
    {
      key: "created_at",
      header: "Timestamp",
      width: "160px",
      render: (log) => formatDateTime(log.created_at),
    },
    {
      key: "actor_admin_email",
      header: "Admin Actor",
      width: "200px",
      render: (log) => (
        <span className="font-mono text-sm">{log.actor_admin_email || "System"}</span>
      ),
    },
    {
      key: "action",
      header: "Action",
      width: "180px",
      render: (log) => (
        <span className="font-mono text-sm text-good">{log.action}</span>
      ),
    },
    {
      key: "target_user_email",
      header: "Target Customer",
      width: "200px",
      render: (log) => (
        <span className="font-mono text-sm text-muted">
          {log.target_user_email || "Global / System"}
        </span>
      ),
    },
    {
      key: "reason",
      header: "Audit Justification",
      render: (log) => <span>{log.reason}</span>,
    },
    {
      key: "ip_address",
      header: "IP Address",
      width: "130px",
      render: (log) => <span className="font-mono text-sm">{log.ip_address || "—"}</span>,
    },
    {
      key: "details",
      header: "Diff",
      width: "90px",
      align: "right",
      render: (log) => (
        <button
          className="btn btn-sm btn-secondary"
          onClick={() => setSelectedLog(log)}
          title="Inspect state changes"
        >
          View
        </button>
      ),
    },
  ];

  return (
    <div className="dashboard-content">
      <div className="page-header-row">
        <div>
          <h2>Administrator Audit Trail</h2>
          <p className="text-muted">
            Immutable historical record of all administrative operations, tier modifications, and security actions.
          </p>
        </div>
        <div className="page-header-actions">
          <a
            href={getExportUrl("action_logs")}
            download
            className="btn btn-secondary"
          >
            📥 Export CSV
          </a>
        </div>
      </div>

      {/* FILTER BAR */}
      <div className="filter-controls-card">
        <div className="search-input-box">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            className="input-search"
            placeholder="Search reason, admin email, or customer email..."
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
            value={actionFilter}
            onChange={(e) => {
              setActionFilter(e.target.value);
              setMeta((prev) => ({ ...prev, page: 1 }));
            }}
          >
            <option value="">Action: All</option>
            <option value="user_access_updated">user_access_updated</option>
            <option value="user_suspended">user_suspended</option>
            <option value="user_restored">user_restored</option>
            <option value="sessions_revoked">sessions_revoked</option>
            <option value="payment_recorded">payment_recorded</option>
            <option value="payment_voided">payment_voided</option>
            <option value="billing_plan_created">billing_plan_created</option>
            <option value="billing_plan_updated">billing_plan_updated</option>
            <option value="billing_plan_deleted">billing_plan_deleted</option>
            <option value="user_location_updated">user_location_updated</option>
            <option value="user_deleted">user_deleted</option>
          </select>

          {(searchQuery || actionFilter) && (
            <button
              className="btn btn-sm btn-link"
              onClick={() => {
                setSearchQuery("");
                setActionFilter("");
                setMeta((prev) => ({ ...prev, page: 1 }));
              }}
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* LOGS TABLE */}
      <div className="card-table-container">
        <DataTable
          columns={columns}
          data={logs}
          keyExtractor={(l) => l.id}
          loading={loading}
          emptyMessage="No audit logs match the current query."
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

      {/* STATE DIFF INSPECTION MODAL */}
      <Modal
        isOpen={Boolean(selectedLog)}
        onClose={() => setSelectedLog(null)}
        title={`Audit Entry: ${selectedLog?.action}`}
        description="Detailed record with immutable before/after state snapshots"
        maxWidth="720px"
      >
        {selectedLog && (
          <div className="diff-modal-content">
            <div className="c-info-list" style={{ marginBottom: "16px" }}>
              <div className="c-info-row">
                <span className="c-label">Actor Admin:</span>
                <span className="c-val">{selectedLog.actor_admin_email || "System"}</span>
              </div>
              <div className="c-info-row">
                <span className="c-label">Target Customer:</span>
                <span className="c-val">{selectedLog.target_user_email || "N/A"}</span>
              </div>
              <div className="c-info-row">
                <span className="c-label">Timestamp:</span>
                <span className="c-val">{formatDateTime(selectedLog.created_at)}</span>
              </div>
              <div className="c-info-row">
                <span className="c-label">Audit Reason:</span>
                <span className="c-val"><strong>{selectedLog.reason}</strong></span>
              </div>
              <div className="c-info-row">
                <span className="c-label">IP Address:</span>
                <span className="c-val font-mono">{selectedLog.ip_address || "—"}</span>
              </div>
            </div>

            <div className="diff-grid-2">
              <div className="diff-panel">
                <span className="diff-title">State Before Modification</span>
                <pre className="diff-code">
                  {selectedLog.before_state
                    ? JSON.stringify(selectedLog.before_state, null, 2)
                    : "No prior state (Creation event)"}
                </pre>
              </div>

              <div className="diff-panel">
                <span className="diff-title">State After Modification</span>
                <pre className="diff-code">
                  {selectedLog.after_state
                    ? JSON.stringify(selectedLog.after_state, null, 2)
                    : "No following state (Deletion event)"}
                </pre>
              </div>
            </div>

            <div className="modal-actions" style={{ marginTop: "18px" }}>
              <button
                className="btn btn-primary"
                onClick={() => setSelectedLog(null)}
              >
                Close Inspector
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
