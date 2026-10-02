"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchAdminAnalyticsSubscriptions } from "../../../lib/api";
import { formatMoney, formatNumber } from "../../../lib/format";
import type { AdminAnalyticsSubscriptions } from "../../../lib/types/admin";
import { DonutChart } from "../../../components/admin/Charts";
import { StatCard } from "../../../components/admin/StatCard";
import { useToast } from "../../../components/admin/Toast";

export default function SubscriptionsPage() {
  const { showToast } = useToast();
  const [data, setData] = useState<AdminAnalyticsSubscriptions | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchAdminAnalyticsSubscriptions()
      .then(setData)
      .catch((err) => {
        showToast(err instanceof Error ? err.message : "Failed to load subscriptions", "error");
      })
      .finally(() => setLoading(false));
  }, [showToast]);

  const donutItems = data
    ? [
        { label: "Active Paid", value: data.distribution.active_paid, color: "#10b981" },
        { label: "Trial", value: data.distribution.trial, color: "#f59e0b" },
        { label: "Free", value: data.distribution.free, color: "#38bdf8" },
        { label: "Expired", value: data.distribution.expired, color: "#ef4444" },
        { label: "Cancelled", value: data.distribution.cancelled, color: "#94a3b8" },
      ].filter((d) => d.value > 0)
    : [];

  return (
    <div className="dashboard-content">
      <div className="page-header-row">
        <div>
          <h2>Subscriptions & Conversion</h2>
          <p className="text-muted">
            Monitor customer entitlements, trial conversions, and tier distributions.
          </p>
        </div>
        <div className="page-header-actions">
          <Link href="/plans" className="btn btn-primary">
            Manage Billing Plans →
          </Link>
        </div>
      </div>

      {/* KPI METRICS ROW */}
      <div className="kpi-grid">
        <StatCard
          title="ACTIVE PAID PRO"
          value={formatNumber(data?.distribution.active_paid)}
          subtext="Full Pro entitlement active"
          trend={{ value: "Pro Tier", isPositive: true }}
          icon="⭐"
        />

        <StatCard
          title="ACTIVE TRIALS"
          value={formatNumber(data?.distribution.trial)}
          subtext="Prospects currently on trial"
          trend={{ value: "In Progress", isNeutral: true }}
          icon="⏳"
        />

        <StatCard
          title="TRIAL CONVERSION"
          value={`${data?.trial_conversion.conversion_rate_pct ?? 0}%`}
          subtext={`${data?.trial_conversion.trials_converted ?? 0} of ${
            data?.trial_conversion.trials_started ?? 0
          } converted`}
          trend={{
            value: `${data?.trial_conversion.trials_converted ?? 0} converted`,
            isPositive: (data?.trial_conversion.conversion_rate_pct ?? 0) > 0,
          }}
          icon="🎯"
        />

        <StatCard
          title="FREE TIER USERS"
          value={formatNumber(data?.distribution.free)}
          subtext="Standard free limits applied"
          trend={{ value: "Free Tier", isNeutral: true }}
          icon="👤"
        />

        <StatCard
          title="EXPIRED ACCESS"
          value={formatNumber(data?.distribution.expired)}
          subtext="Trials or subscriptions lapsed"
          trend={{ value: "Expired", isPositive: false }}
          icon="⚠️"
        />

        <StatCard
          title="CANCELLED ACCESS"
          value={formatNumber(data?.distribution.cancelled)}
          subtext="User voluntarily stopped"
          trend={{ value: "Cancelled", isPositive: false }}
          icon="🛑"
        />
      </div>

      {/* DETAILED GRIDS */}
      <div className="charts-grid-2" style={{ marginTop: "24px" }}>
        {/* DONUT BREAKDOWN */}
        <div className="chart-card">
          <div className="chart-card-header">
            <div>
              <h4>Entitlement Distribution</h4>
              <span className="text-muted text-sm">Status breakdown across user base</span>
            </div>
            <span className="chart-badge">Tiers</span>
          </div>
          <DonutChart
            data={donutItems}
            size={220}
            thickness={30}
            centerLabel="Total Tiers"
          />
        </div>

        {/* TRIAL CONVERSION CARD */}
        <div className="chart-card">
          <div className="chart-card-header">
            <div>
              <h4>Trial Conversion Funnel</h4>
              <span className="text-muted text-sm">Trial outcome indicators</span>
            </div>
            <span className="chart-badge">Conversion</span>
          </div>

          <div className="conversion-funnel-list">
            <div className="funnel-item">
              <span className="funnel-label">Trials Started</span>
              <strong className="funnel-val">
                {formatNumber(data?.trial_conversion.trials_started)}
              </strong>
            </div>
            <div className="funnel-item">
              <span className="funnel-label">Currently Active Trials</span>
              <strong className="funnel-val text-warn">
                {formatNumber(data?.trial_conversion.trials_active)}
              </strong>
            </div>
            <div className="funnel-item">
              <span className="funnel-label">Converted to Paid</span>
              <strong className="funnel-val text-good">
                {formatNumber(data?.trial_conversion.trials_converted)}
              </strong>
            </div>
            <div className="funnel-item">
              <span className="funnel-label">Expired Without Conversion</span>
              <strong className="funnel-val text-danger">
                {formatNumber(data?.trial_conversion.trials_expired)}
              </strong>
            </div>
            <div className="funnel-item highlight">
              <span className="funnel-label">Conversion Rate</span>
              <strong className="funnel-val font-mono">
                {data?.trial_conversion.conversion_rate_pct ?? 0}%
              </strong>
            </div>
          </div>
        </div>
      </div>

      {/* PLAN & METHOD TABLES */}
      <div className="charts-grid-2" style={{ marginTop: "24px" }}>
        {/* Plan Breakdown */}
        <div className="card panel">
          <div className="section-header">
            <div>
              <h4>Distribution by Plan Code</h4>
              <p className="text-muted text-sm">Subscribers split across plan codes</p>
            </div>
          </div>
          <div className="c-table-wrap">
            <table className="datatable-table">
              <thead>
                <tr>
                  <th>Plan Code</th>
                  <th>Subscribers</th>
                  <th>Share</th>
                  <th>Filter</th>
                </tr>
              </thead>
              <tbody>
                {(data?.by_plan || []).map((p) => (
                  <tr key={p.plan_code}>
                    <td>
                      <span className="font-mono">{p.plan_code.toUpperCase()}</span>
                    </td>
                    <td>
                      <strong>{formatNumber(p.count)}</strong>
                    </td>
                    <td>{p.percentage}%</td>
                    <td>
                      <Link
                        href={`/users?plan=${encodeURIComponent(p.plan_code)}`}
                        className="btn-link"
                      >
                        View users →
                      </Link>
                    </td>
                  </tr>
                ))}
                {(!data?.by_plan || data.by_plan.length === 0) && (
                  <tr>
                    <td colSpan={4} className="datatable-empty">
                      No plan distribution data available
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Payment Methods Breakdown */}
        <div className="card panel">
          <div className="section-header">
            <div>
              <h4>Payment Methods Distribution</h4>
              <p className="text-muted text-sm">Payment methods used by customers</p>
            </div>
          </div>
          <div className="c-table-wrap">
            <table className="datatable-table">
              <thead>
                <tr>
                  <th>Method</th>
                  <th>Transactions</th>
                  <th>Total Amount</th>
                  <th>Volume Share</th>
                </tr>
              </thead>
              <tbody>
                {(data?.payment_methods || []).map((m) => (
                  <tr key={m.method}>
                    <td>
                      <strong>{m.method.toUpperCase()}</strong>
                    </td>
                    <td>{formatNumber(m.count)} txns</td>
                    <td>{formatMoney(m.amount)}</td>
                    <td>{m.percentage}%</td>
                  </tr>
                ))}
                {(!data?.payment_methods || data.payment_methods.length === 0) && (
                  <tr>
                    <td colSpan={4} className="datatable-empty">
                      No payment methods recorded yet
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
