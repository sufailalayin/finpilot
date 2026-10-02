"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchAdminAIUsage } from "../../../lib/api";
import { formatNumber } from "../../../lib/format";
import type { AdminAnalyticsAI } from "../../../lib/types/admin";
import { BarChart, LineChart } from "../../../components/admin/Charts";
import { StatCard } from "../../../components/admin/StatCard";
import { useToast } from "../../../components/admin/Toast";

export default function AIUsagePage() {
  const { showToast } = useToast();
  const [data, setData] = useState<AdminAnalyticsAI | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchAdminAIUsage()
      .then(setData)
      .catch((err) => {
        showToast(err instanceof Error ? err.message : "Failed to load AI analytics", "error");
      })
      .finally(() => setLoading(false));
  }, [showToast]);

  const lineChartData =
    data?.points.map((p) => ({
      label: p.date,
      value: p.requests,
    })) || [];

  const charVolumeData =
    data?.points.slice(-14).map((p) => ({
      label: p.date.slice(5),
      value: Math.round((p.prompt_chars + p.response_chars) / 1000), // KB / thousands
    })) || [];

  return (
    <div className="dashboard-content">
      <div className="page-header-row">
        <div>
          <h2>AI Consumption Analytics</h2>
          <p className="text-muted">
            Monitor query volume, token and character throughput, and customer AI consumption.
          </p>
        </div>
      </div>

      {/* KPI GRID */}
      <div className="kpi-grid">
        <StatCard
          title="TOTAL AI REQUESTS"
          value={formatNumber(data?.total_requests)}
          subtext="Lifetime FinPilot AI interactions"
          trend={{ value: "All time", isPositive: true }}
          icon="⚡"
        />

        <StatCard
          title="LAST 24 HOURS"
          value={formatNumber(data?.requests_24h)}
          subtext="Queries processed in 24h"
          trend={{ value: `${data?.requests_24h ?? 0} reqs`, isNeutral: true }}
          icon="⏱️"
        />

        <StatCard
          title="LAST 7 DAYS"
          value={formatNumber(data?.requests_7d)}
          subtext="Weekly active requests"
          trend={{ value: "7 days", isPositive: true }}
          icon="📅"
        />

        <StatCard
          title="LAST 30 DAYS"
          value={formatNumber(data?.requests_30d)}
          subtext="Monthly consumption total"
          trend={{ value: "30 days", isPositive: true }}
          icon="📊"
        />

        <StatCard
          title="ACTIVE AI USERS (7D)"
          value={formatNumber(data?.unique_users_7d)}
          subtext="Distinct customers querying AI"
          trend={{ value: "Unique users", isPositive: true }}
          icon="👥"
        />
      </div>

      {/* CHARTS */}
      <div className="charts-grid-2" style={{ marginTop: "24px" }}>
        <div className="chart-card">
          <div className="chart-card-header">
            <div>
              <h4>Daily AI Queries (30 Days)</h4>
              <span className="text-muted text-sm">FinPilot AI assistance requests</span>
            </div>
            <span className="chart-badge">Volume</span>
          </div>
          <LineChart
            data={lineChartData}
            height={230}
            color="#818cf8"
            formatValue={(v) => `${v} reqs`}
          />
        </div>

        <div className="chart-card">
          <div className="chart-card-header">
            <div>
              <h4>Prompt & Response Volume (kChars)</h4>
              <span className="text-muted text-sm">Character throughput (last 14 days)</span>
            </div>
            <span className="chart-badge">Characters</span>
          </div>
          <BarChart
            data={charVolumeData}
            height={230}
            color="#38bdf8"
            formatValue={(v) => `${v}k chars`}
          />
        </div>
      </div>

      {/* TOP USERS TABLE */}
      <div className="card panel" style={{ marginTop: "24px" }}>
        <div className="section-header">
          <div>
            <h4>Top AI Consumers (Last 30 Days)</h4>
            <p className="text-muted text-sm">Customers with the highest AI prompt volume</p>
          </div>
        </div>
        <div className="c-table-wrap">
          <table className="datatable-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Customer</th>
                <th>Requests (30d)</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {(data?.top_users || []).map((u, i) => (
                <tr key={u.user_id}>
                  <td>
                    <span className="font-mono text-muted">#{i + 1}</span>
                  </td>
                  <td>
                    <strong>{u.user_email}</strong>
                  </td>
                  <td>
                    <span className="font-mono text-good">{formatNumber(u.requests)} requests</span>
                  </td>
                  <td>
                    <Link
                      href={`/users?q=${encodeURIComponent(u.user_email)}`}
                      className="btn-link"
                    >
                      View customer 360 →
                    </Link>
                  </td>
                </tr>
              ))}
              {(!data?.top_users || data.top_users.length === 0) && (
                <tr>
                  <td colSpan={4} className="datatable-empty">
                    No AI usage recorded yet
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
