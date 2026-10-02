"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  fetchAdminUsers,
  fetchBillingPlans,
  getExportUrl,
  restoreAdminUser,
  revokeAdminUserSessions,
  suspendAdminUser,
} from "../../../lib/api";
import { formatDate, truncate } from "../../../lib/format";
import type {
  AdminBillingPlanRow,
  AdminPaginationMeta,
  AdminUserRow,
} from "../../../lib/types/admin";
import { Customer360Modal } from "../../../components/admin/Customer360Modal";
import { type Column, DataTable } from "../../../components/admin/DataTable";
import { StatusBadge } from "../../../components/admin/StatusBadge";
import { useToast } from "../../../components/admin/Toast";

export default function UsersPage() {
  const { showToast } = useToast();
  const [users, setUsers] = useState<AdminUserRow[]>([]);
  const [plans, setPlans] = useState<AdminBillingPlanRow[]>([]);
  const [meta, setMeta] = useState<AdminPaginationMeta>({
    page: 1,
    page_size: 25,
    total: 0,
    total_pages: 1,
  });
  const [loading, setLoading] = useState(false);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [planFilter, setPlanFilter] = useState("");
  const [subStatusFilter, setSubStatusFilter] = useState("");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  // Selected User for Customer 360
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);

  const loadUsers = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchAdminUsers({
        page: meta.page,
        page_size: meta.page_size,
        q: searchQuery.trim() || undefined,
        status: statusFilter || undefined,
        plan: planFilter || undefined,
        subscription_status: subStatusFilter || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setUsers(res.items);
      setMeta(res.meta);
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to load customers", "error");
    } finally {
      setLoading(false);
    }
  }, [
    meta.page,
    meta.page_size,
    searchQuery,
    statusFilter,
    planFilter,
    subStatusFilter,
    sortBy,
    sortOrder,
    showToast,
  ]);

  useEffect(() => {
    fetchBillingPlans()
      .then(setPlans)
      .catch(() => {});
  }, []);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  // Debounced search reset to page 1
  function handleSearchChange(val: string) {
    setSearchQuery(val);
    setMeta((prev) => ({ ...prev, page: 1 }));
  }

  function handleSort(key: string) {
    if (sortBy === key) {
      setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(key);
      setSortOrder("desc");
    }
  }

  async function handleQuickToggleSuspend(user: AdminUserRow, e: React.MouseEvent) {
    e.stopPropagation();
    const isSuspended = user.user_status === "suspended";
    const reason = window.prompt(
      `Enter reason to ${isSuspended ? "restore" : "suspend"} ${user.email}:`,
    );
    if (!reason || !reason.trim()) return;

    try {
      if (isSuspended) {
        await restoreAdminUser(user.id, reason.trim());
        showToast(`User ${user.email} restored to Active`, "success");
      } else {
        await suspendAdminUser(user.id, reason.trim());
        showToast(`User ${user.email} suspended`, "warning");
      }
      await loadUsers();
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Action failed", "error");
    }
  }

  async function handleQuickRevokeSessions(user: AdminUserRow, e: React.MouseEvent) {
    e.stopPropagation();
    const reason = window.prompt(`Reason to revoke all sessions for ${user.email}:`);
    if (!reason || !reason.trim()) return;

    try {
      await revokeAdminUserSessions(user.id, reason.trim());
      showToast(`Sessions revoked for ${user.email}`, "success");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to revoke sessions", "error");
    }
  }

  const columns: Column<AdminUserRow>[] = [
    {
      key: "full_name",
      header: "Customer",
      sortable: true,
      render: (u) => (
        <div className="table-user-cell">
          <div className="table-avatar">
            {(u.full_name || u.email).charAt(0).toUpperCase()}
          </div>
          <div className="table-user-info">
            <span className="table-user-name">{u.full_name || "—"}</span>
            <span className="table-user-email">{u.email}</span>
          </div>
        </div>
      ),
    },
    {
      key: "user_status",
      header: "Status",
      sortable: true,
      width: "120px",
      render: (u) => <StatusBadge status={u.user_status} variant="user" />,
    },
    {
      key: "plan_code",
      header: "Plan Tier",
      width: "140px",
      render: (u) => (
        <div className="plan-cell-wrap">
          <StatusBadge status={u.plan_code} variant="plan" />
          {u.billing_plan_name && (
            <span className="plan-cell-sub">{truncate(u.billing_plan_name, 16)}</span>
          )}
        </div>
      ),
    },
    {
      key: "entitlement_status",
      header: "Entitlement",
      width: "130px",
      render: (u) => (
        <StatusBadge status={u.entitlement_status} variant="entitlement" />
      ),
    },
    {
      key: "email_verified",
      header: "Verified",
      width: "100px",
      render: (u) => (
        <span className={u.email_verified ? "text-good" : "text-muted"}>
          {u.email_verified ? "✓ Yes" : "No"}
        </span>
      ),
    },
    {
      key: "created_at",
      header: "Registered",
      sortable: true,
      width: "130px",
      render: (u) => formatDate(u.created_at),
    },
    {
      key: "actions",
      header: "Actions",
      width: "180px",
      align: "right",
      render: (u) => (
        <div className="table-actions-row" onClick={(e) => e.stopPropagation()}>
          <button
            className="btn btn-sm btn-secondary"
            onClick={() => setSelectedUserId(u.id)}
            title="Open Customer 360"
          >
            360° View
          </button>
          <button
            className={`btn btn-sm ${
              u.user_status === "suspended" ? "btn-primary" : "btn-warning"
            }`}
            onClick={(e) => handleQuickToggleSuspend(u, e)}
            title={u.user_status === "suspended" ? "Restore user" : "Suspend user"}
          >
            {u.user_status === "suspended" ? "Restore" : "Suspend"}
          </button>
          <button
            className="btn btn-sm btn-icon"
            onClick={(e) => handleQuickRevokeSessions(u, e)}
            title="Revoke active sessions"
          >
            🔒
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="dashboard-content">
      <div className="page-header-row">
        <div>
          <h2>Customers Directory</h2>
          <p className="text-muted">
            Search, filter, manage subscriptions, location, and security for all FinPilot users.
          </p>
        </div>
        <div className="page-header-actions">
          <a
            href={getExportUrl("users")}
            download
            className="btn btn-secondary"
          >
            📥 Export CSV
          </a>
        </div>
      </div>

      {/* FILTER CONTROLS BAR */}
      <div className="filter-controls-card">
        <div className="search-input-box">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            className="input-search"
            placeholder="Search by name, email address, or user ID..."
            value={searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
          />
          {searchQuery && (
            <button
              className="clear-search-btn"
              onClick={() => handleSearchChange("")}
            >
              ×
            </button>
          )}
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
            <option value="active">Active</option>
            <option value="suspended">Suspended</option>
          </select>

          <select
            className="filter-select"
            value={planFilter}
            onChange={(e) => {
              setPlanFilter(e.target.value);
              setMeta((prev) => ({ ...prev, page: 1 }));
            }}
          >
            <option value="">Plan: All</option>
            <option value="free">Free</option>
            <option value="pro">Pro</option>
          </select>

          <select
            className="filter-select"
            value={subStatusFilter}
            onChange={(e) => {
              setSubStatusFilter(e.target.value);
              setMeta((prev) => ({ ...prev, page: 1 }));
            }}
          >
            <option value="">Entitlement: All</option>
            <option value="trial">Trial</option>
            <option value="active">Active</option>
            <option value="expired">Expired</option>
            <option value="cancelled">Cancelled</option>
          </select>

          {(searchQuery || statusFilter || planFilter || subStatusFilter) && (
            <button
              className="btn btn-sm btn-link"
              onClick={() => {
                setSearchQuery("");
                setStatusFilter("");
                setPlanFilter("");
                setSubStatusFilter("");
                setMeta((prev) => ({ ...prev, page: 1 }));
              }}
            >
              Reset Filters
            </button>
          )}
        </div>
      </div>

      {/* USERS DATA TABLE */}
      <div className="card-table-container">
        <DataTable
          columns={columns}
          data={users}
          keyExtractor={(u) => u.id}
          loading={loading}
          emptyMessage="No customers match the current search filters."
          sortKey={sortBy}
          sortOrder={sortOrder}
          onSort={handleSort}
          onRowClick={(u) => setSelectedUserId(u.id)}
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

      {/* Customer 360 Modal */}
      <Customer360Modal
        userId={selectedUserId}
        plans={plans}
        onClose={() => setSelectedUserId(null)}
        onUserUpdated={loadUsers}
      />
    </div>
  );
}
