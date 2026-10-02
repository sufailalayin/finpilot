"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  fetchAdminAnalyticsAI,
  fetchAdminAnalyticsOverview,
  fetchAdminAnalyticsRevenue,
  fetchAdminAnalyticsSubscriptions,
  fetchAdminAnalyticsUsers,
  fetchAdminSecurityEvents,
  fetchAdminUsers,
  fetchBillingPlans,
  fetchPayments,
} from "../../lib/api";
import { formatDate, formatDateTime, formatMoney, formatNumber } from "../../lib/format";
import type {
  AdminAnalyticsAI,
  AdminAnalyticsOverview,
  AdminAnalyticsRevenue,
  AdminAnalyticsSubscriptions,
  AdminAnalyticsUsers,
  AdminBillingPlanRow,
  AdminPaymentRow,
  AdminSecurityEventRow,
  AdminUserRow,
} from "../../lib/types/admin";
import { BarChart, DonutChart, LineChart } from "../../components/admin/Charts";
import { Customer360Modal } from "../../components/admin/Customer360Modal";
import { StatCard } from "../../components/admin/StatCard";
import { StatusBadge } from "../../components/admin/StatusBadge";
import { useToast } from "../../components/admin/Toast";

export default function OverviewDashboardPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);

  // Analytics data
  const [analytics, setAnalytics] = useState<AdminAnalyticsOverview | null>(null);
  const [userGrowth, setUserGrowth] = useState<AdminAnalyticsUsers | null>(null);
  const [revenueAnalytics, setRevenueAnalytics] = useState<AdminAnalyticsRevenue | null>(null);
  const [subAnalytics, setSubAnalytics] = useState<AdminAnalyticsSubscriptions | null>(null);
  const [aiAnalytics, setAIAnalytics] = useState<AdminAnalyticsAI | null>(null);

  // Recent tables
  const [recentUsers, setRecentUsers] = useState<AdminUserRow[]>([]);
  const [recentPayments, setRecentPayments] = useState<AdminPaymentRow[]>([]);
  const [recentSecurity, setRecentSecurity] = useState<AdminSecurityEventRow[]>([]);
  const [plans, setPlans] = useState<AdminBillingPlanRow[]>([]);

  // Selected customer for 360 modal
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [
        overviewRes,
        usersRes,
        revenueRes,
        subsRes,
        aiRes,
        recentUsersRes,
        recentPaymentsRes,
        recentSecRes,
        plansRes,
      ] = await Promise.all([
        fetchAdminAnalyticsOverview().catch(() => null),
        fetchAdminAnalyticsUsers("30d").catch(() => null),
        fetchAdminAnalyticsRevenue("30d").catch(() => null),
        fetchAdminAnalyticsSubscriptions().catch(() => null),
        fetchAdminAnalyticsAI().catch(() => null),
        fetchAdminUsers({ page: 1, page_size: 5 }).catch(() => ({ items: [] })),
        fetchPayments({ page: 1, page_size: 5 }).catch(() => ({ items: [] })),
        fetchAdminSecurityEvents({ page: 1, page_size: 5 }).catch(() => ({ items: [] })),
        fetchBillingPlans().catch(() => []),
      ]);

      setAnalytics(overviewRes);
      setUserGrowth(usersRes);
      setRevenueAnalytics(revenueRes);
      setSubAnalytics(subsRes);
      setAIAnalytics(aiRes);
      setRecentUsers(recentUsersRes.items);
      setRecentPayments(recentPaymentsRes.items);
      setRecentSecurity(recentSecRes.items);
      setPlans(plansRes);
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Unable to load dashboard data", "error");
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Prepare chart datasets from real data
  const userGrowthChartData =
    userGrowth?.points.map((p) => ({
      label: p.date,
      value: p.cumulative,
    })) || [];

  const revenueChartData =
    revenueAnalytics?.points.map((p) => ({
      label: p.date,
      value: typeof p.revenue === "string" ? parseFloat(p.revenue) : p.revenue,
    })) || [];

  const donutData = subAnalytics
    ? [
        { label: "Active Paid", value: subAnalytics.distribution.active_paid, color: "#10b981" },
        { label: "Trial", value: subAnalytics.distribution.trial, color: "#f59e0b" },
        { label: "Free", value: subAnalytics.distribution.free, color: "#38bdf8" },
        { label: "Expired", value: subAnalytics.distribution.expired, color: "#ef4444" },
        { label: "Cancelled", value: subAnalytics.distribution.cancelled, color: "#94a3b8" },
      ].filter((d) => d.value > 0)
    : [];

  const aiBarData =
    aiAnalytics?.points.slice(-14).map((p) => ({
      label: p.date.slice(5),
      value: p.requests,
    })) || [];

  return (
    <div className="dashboard-content">
      {/* KPI GRID */}
      <section className="section-block">
        <div className="section-title-row">
          <h3>Key Metrics Overview</h3>
          <span className="text-muted text-sm">Updated in real-time from production database</span>
        </div>

        <div className="kpi-grid">
          <StatCard
            title="TOTAL CUSTOMERS"
            value={formatNumber(analytics?.total_users)}
            subtext={`${analytics?.new_users_30d ?? 0} joined in last 30 days`}
            trend={{
              value: `+${analytics?.new_users_7d ?? 0} in 7d`,
              isPositive: true,
            }}
            icon="👥"
          />

          <StatCard
            title="ACTIVE SUBSCRIBERS"
            value={formatNumber(analytics?.paid_users)}
            subtext={`${analytics?.active_trials ?? 0} currently on trial`}
            trend={{
              value: `${analytics?.active_trials ?? 0} trials`,
              isNeutral: true,
            }}
            icon="⭐"
          />

          <StatCard
            title="REVENUE THIS MONTH"
            value={formatMoney(analytics?.revenue_this_month)}
            subtext={`Total: ${formatMoney(analytics?.total_recorded_revenue)}`}
            trend={{
              value: `${formatMoney(analytics?.revenue_today)} today`,
              isPositive: true,
            }}
            icon="💳"
          />

          <StatCard
            title="AI REQUESTS (7D)"
            value={formatNumber(analytics?.ai_requests_7d)}
            subtext={`${analytics?.ai_requests_today ?? 0} queries handled today`}
            trend={{
              value: `${analytics?.ai_requests_today ?? 0} today`,
              isPositive: true,
            }}
            icon="⚡"
          />

          <StatCard
            title="FINANCE ACCOUNTS"
            value={formatNumber(analytics?.finance_accounts)}
            subtext={`${formatNumber(analytics?.transactions)} total transactions`}
            trend={{
              value: `${formatNumber(analytics?.transactions)} txns`,
              isNeutral: true,
            }}
            icon="📊"
          />

          <StatCard
            title="SECURITY ALERTS (24H)"
            value={formatNumber(analytics?.security_events_24h)}
            subtext={`${analytics?.failed_login_attempts ?? 0} failed login attempts`}
            trend={{
              value: `${analytics?.failed_login_attempts ?? 0} failed`,
              isPositive: (analytics?.failed_login_attempts ?? 0) === 0,
            }}
            icon="🛡️"
          />
        </div>
      </section>

      {/* QUICK ACTIONS BANNER */}
      <section className="section-block">
        <div className="quick-actions-bar">
          <div className="qa-info">
            <h4>Operational Shortcuts</h4>
            <p>Direct entry points for common administrative workflows</p>
          </div>
          <div className="qa-buttons">
            <Link href="/payments" className="btn btn-primary">
              + Record Payment
            </Link>
            <Link href="/plans" className="btn btn-secondary">
              + Create Plan
            </Link>
            <Link href="/users" className="btn btn-secondary">
              👤 Manage Users
            </Link>
            <Link href="/release" className="btn btn-secondary">
              🚀 App Release
            </Link>
          </div>
        </div>
      </section>

      {/* CHARTS GRID */}
      <section className="section-block">
        <div className="charts-grid-2">
          {/* User Growth Line Chart */}
          <div className="chart-card">
            <div className="chart-card-header">
              <div>
                <h4>Customer Growth Trend</h4>
                <span className="text-muted text-sm">Cumulative registered accounts (last 30 days)</span>
              </div>
              <span className="chart-badge">Users</span>
            </div>
            <LineChart
              data={userGrowthChartData}
              color="#10b981"
              height={230}
              formatValue={(v) => `${v.toLocaleString()} users`}
            />
          </div>

          {/* Revenue Trend Line Chart */}
          <div className="chart-card">
            <div className="chart-card-header">
              <div>
                <h4>Daily Recorded Revenue</h4>
                <span className="text-muted text-sm">Received payments (last 30 days)</span>
              </div>
              <span className="chart-badge">Revenue</span>
            </div>
            <LineChart
              data={revenueChartData}
              color="#38bdf8"
              height={230}
              formatValue={(v) => formatMoney(v)}
            />
          </div>
        </div>

        <div className="charts-grid-2" style={{ marginTop: "18px" }}>
          {/* Subscription Breakdown Donut */}
          <div className="chart-card">
            <div className="chart-card-header">
              <div>
                <h4>Subscription Breakdown</h4>
                <span className="text-muted text-sm">Current entitlement tiers across all users</span>
              </div>
              <span className="chart-badge">Tiers</span>
            </div>
            <DonutChart
              data={donutData}
              size={210}
              thickness={28}
              centerLabel="Subscribers"
            />
          </div>

          {/* AI Usage Bar Chart */}
          <div className="chart-card">
            <div className="chart-card-header">
              <div>
                <h4>AI Consumption Activity</h4>
                <span className="text-muted text-sm">Daily AI requests handled (last 14 days)</span>
              </div>
              <span className="chart-badge">AI</span>
            </div>
            <BarChart
              data={aiBarData}
              color="#818cf8"
              height={230}
              formatValue={(v) => `${v} requests`}
            />
          </div>
        </div>
      </section>

      {/* RECENT ACTIVITY TABLES */}
      <section className="section-block">
        <div className="recent-activity-grid">
          {/* Recent Customers */}
          <div className="activity-panel">
            <div className="activity-panel-header">
              <h4>Recent Registrations</h4>
              <Link href="/users" className="panel-more-link">
                View all →
              </Link>
            </div>
            {recentUsers.length === 0 ? (
              <div className="chart-empty" style={{ height: "140px" }}>
                <span>No customer accounts yet</span>
              </div>
            ) : (
              <div className="activity-list">
                {recentUsers.map((u) => (
                  <div
                    key={u.id}
                    className="activity-item clickable-activity"
                    onClick={() => setSelectedUserId(u.id)}
                  >
                    <div className="activity-avatar">
                      {(u.full_name || u.email).charAt(0).toUpperCase()}
                    </div>
                    <div className="activity-content">
                      <div className="activity-primary">
                        <span className="activity-name">{u.full_name || u.email}</span>
                        <StatusBadge status={u.plan_code} variant="plan" />
                      </div>
                      <span className="activity-sub">{u.email}</span>
                    </div>
                    <div className="activity-time">{formatDate(u.created_at)}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recent Payments */}
          <div className="activity-panel">
            <div className="activity-panel-header">
              <h4>Recent Payments Received</h4>
              <Link href="/payments" className="panel-more-link">
                View all →
              </Link>
            </div>
            {recentPayments.length === 0 ? (
              <div className="chart-empty" style={{ height: "140px" }}>
                <span>No payment records recorded</span>
              </div>
            ) : (
              <div className="activity-list">
                {recentPayments.map((p) => (
                  <div key={p.id} className="activity-item">
                    <div className="payment-icon-mark">₹</div>
                    <div className="activity-content">
                      <div className="activity-primary">
                        <strong className="payment-amount">
                          {formatMoney(p.amount, p.currency)}
                        </strong>
                        <StatusBadge status={p.status} variant="payment" />
                      </div>
                      <span className="activity-sub">
                        {p.user_email} · {p.payment_method}
                      </span>
                    </div>
                    <div className="activity-time">{formatDate(p.received_at)}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Customer 360 Drilldown Modal */}
      <Customer360Modal
        userId={selectedUserId}
        plans={plans}
        onClose={() => setSelectedUserId(null)}
        onUserUpdated={loadData}
      />
    </div>
  );
}
