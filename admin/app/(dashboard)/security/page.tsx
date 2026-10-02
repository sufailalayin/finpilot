"use client";

import React, { useCallback, useEffect, useState } from "react";
import { fetchAdminAnalyticsSecurity, fetchAdminSecurityEvents } from "../../../lib/api";
import { formatDateTime, formatNumber, truncate } from "../../../lib/format";
import type {
  AdminAnalyticsSecurity,
  AdminPaginationMeta,
  AdminSecurityEventRow,
} from "../../../lib/types/admin";
import { LineChart } from "../../../components/admin/Charts";
import { type Column, DataTable } from "../../../components/admin/DataTable";
import { StatCard } from "../../../components/admin/StatCard";
import { useToast } from "../../../components/admin/Toast";

export default function SecurityPage() {
  const { showToast } = useToast();
  const [analytics, setAnalytics] = useState<AdminAnalyticsSecurity | null>(null);
  const [events, setEvents] = useState<AdminSecurityEventRow[]>([]);
  const [meta, setMeta] = useState<AdminPaginationMeta>({
    page: 1,
    page_size: 25,
    total: 0,
    total_pages: 1,
  });
  const [loading, setLoading] = useState(false);

  // Filters
  const [period, setPeriod] = useState<"24h" | "7d" | "30d">("7d");
  const [searchQuery, setSearchQuery] = useState("");
  const [eventTypeFilter, setEventTypeFilter] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [eventsRes, analyticsRes] = await Promise.all([
        fetchAdminSecurityEvents({
          page: meta.page,
          page_size: meta.page_size,
          q: searchQuery.trim() || undefined,
          event_type: eventTypeFilter || undefined,
        }),
        fetchAdminAnalyticsSecurity(period).catch(() => null),
      ]);
      setEvents(eventsRes.items);
      setMeta(eventsRes.meta);
      setAnalytics(analyticsRes);
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to load security logs", "error");
    } finally {
      setLoading(false);
    }
  }, [meta.page, meta.page_size, searchQuery, eventTypeFilter, period, showToast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const trendData =
    analytics?.points.map((p) => ({
      label: p.date,
      value: p.total,
    })) || [];

  const columns: Column<AdminSecurityEventRow>[] = [
    {
      key: "created_at",
      header: "Timestamp",
      width: "160px",
      render: (ev) => formatDateTime(ev.created_at),
    },
    {
      key: "event_type",
      header: "Event Type",
      width: "180px",
      render: (ev) => {
        const isFail = ev.event_type.toLowerCase().includes("fail");
        return (
          <span className={`font-mono text-sm ${isFail ? "text-danger" : "text-good"}`}>
            {ev.event_type}
          </span>
        );
      },
    },
    {
      key: "user_email",
      header: "Account",
      width: "220px",
      render: (ev) => (
        <span className="font-mono text-sm">{ev.user_email || "System / Anonymous"}</span>
      ),
    },
    {
      key: "ip_address",
      header: "IP Address",
      width: "140px",
      render: (ev) => <span className="font-mono text-sm">{ev.ip_address || "—"}</span>,
    },
    {
      key: "description",
      header: "Event Details",
      render: (ev) => <span>{ev.description || "—"}</span>,
    },
    {
      key: "user_agent",
      header: "Client Agent",
      width: "180px",
      render: (ev) => (
        <span className="text-muted text-sm" title={ev.user_agent || ""}>
          {truncate(ev.user_agent, 26) || "—"}
        </span>
      ),
    },
  ];

  return (
    <div className="dashboard-content">
      <div className="page-header-row">
        <div>
          <h2>Security Audit & Monitoring</h2>
          <p className="text-muted">
            Track user logins, token rotations, password resets, and suspicious authentication activity.
          </p>
        </div>
        <div className="page-header-actions">
          <div className="period-toggle-group">
            <button
              className={`btn btn-sm ${period === "24h" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setPeriod("24h")}
            >
              24h
            </button>
            <button
              className={`btn btn-sm ${period === "7d" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setPeriod("7d")}
            >
              7d
            </button>
            <button
              className={`btn btn-sm ${period === "30d" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setPeriod("30d")}
            >
              30d
            </button>
          </div>
        </div>
      </div>

      {/* KPI GRID */}
      <div className="kpi-grid">
        <StatCard
          title="TOTAL SECURITY EVENTS"
          value={formatNumber(analytics?.total_events)}
          subtext={`Captured over the last ${period}`}
          trend={{ value: `${period} window`, isNeutral: true }}
          icon="🛡️"
        />

        <StatCard
          title="FAILED AUTH ATTEMPTS"
          value={formatNumber(analytics?.failed_logins)}
          subtext="Failed logins and lockout events"
          trend={{
            value: (analytics?.failed_logins ?? 0) > 0 ? "Requires review" : "Clear",
            isPositive: (analytics?.failed_logins ?? 0) === 0,
          }}
          icon="⚠️"
        />

        <StatCard
          title="TOP EVENT PATTERN"
          value={analytics?.breakdown[0]?.event_type || "None"}
          subtext={`${analytics?.breakdown[0]?.count ?? 0} occurrences`}
          trend={{ value: "Most frequent", isNeutral: true }}
          icon="📋"
        />
      </div>

      {/* TREND CHART & BREAKDOWN */}
      <div className="charts-grid-2" style={{ marginTop: "24px" }}>
        <div className="chart-card">
          <div className="chart-card-header">
            <div>
              <h4>Security Activity Trend</h4>
              <span className="text-muted text-sm">Event frequency over time</span>
            </div>
            <span className="chart-badge">Timeline</span>
          </div>
          <LineChart
            data={trendData}
            height={230}
            color="#ef4444"
            formatValue={(v) => `${v} events`}
          />
        </div>

        <div className="card panel">
          <div className="section-header">
            <div>
              <h4>Event Type Breakdown</h4>
              <p className="text-muted text-sm">Classification of recorded security actions</p>
            </div>
          </div>
          <div className="c-table-wrap">
            <table className="datatable-table">
              <thead>
                <tr>
                  <th>Event Classification</th>
                  <th>Frequency</th>
                </tr>
              </thead>
              <tbody>
                {(analytics?.breakdown || []).map((b) => (
                  <tr key={b.event_type}>
                    <td>
                      <span className="font-mono text-sm">{b.event_type}</span>
                    </td>
                    <td>
                      <strong>{formatNumber(b.count)}</strong>
                    </td>
                  </tr>
                ))}
                {(!analytics?.breakdown || analytics.breakdown.length === 0) && (
                  <tr>
                    <td colSpan={2} className="datatable-empty">
                      No events in selected period
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* FILTER BAR */}
      <div className="filter-controls-card" style={{ marginTop: "24px" }}>
        <div className="search-input-box">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            className="input-search"
            placeholder="Search description, IP address, or customer email..."
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
            value={eventTypeFilter}
            onChange={(e) => {
              setEventTypeFilter(e.target.value);
              setMeta((prev) => ({ ...prev, page: 1 }));
            }}
          >
            <option value="">Event Type: All</option>
            <option value="login_success">login_success</option>
            <option value="login_failed">login_failed</option>
            <option value="password_reset">password_reset</option>
            <option value="mfa_verified">mfa_verified</option>
            <option value="admin_access_change">admin_access_change</option>
          </select>

          {(searchQuery || eventTypeFilter) && (
            <button
              className="btn btn-sm btn-link"
              onClick={() => {
                setSearchQuery("");
                setEventTypeFilter("");
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
          data={events}
          keyExtractor={(ev) => ev.id}
          loading={loading}
          emptyMessage="No security events match the current filter parameters."
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
    </div>
  );
}
