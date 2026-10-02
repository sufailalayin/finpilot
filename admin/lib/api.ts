import type {
  AdminActionLogRow,
  AdminAnalyticsAI,
  AdminAnalyticsOverview,
  AdminAnalyticsRevenue,
  AdminAnalyticsSecurity,
  AdminAnalyticsSubscriptions,
  AdminAnalyticsUsers,
  AdminBillingPlanRow,
  AdminOverview,
  AdminPaginatedActionLogs,
  AdminPaginatedPayments,
  AdminPaginatedSecurityEvents,
  AdminPaginatedUsers,
  AdminPaymentRow,
  AdminUserDetail,
  AdminUserRow,
  AppRelease,
  Readiness,
} from "./types/admin";

export const API_BASE_URL = "/api/backend";

async function apiRequest<T = unknown>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(API_BASE_URL + path, {
    credentials: "same-origin",
    cache: "no-store",
    ...init,
    headers: {
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...(init.headers ?? {}),
    },
  });

  if (response.status === 401 || response.status === 403) {
    throw new Error("ADMIN_SESSION_EXPIRED");
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? body.message ?? `Admin request failed (${response.status})`);
  }

  return (response.status === 204 ? null : await response.json()) as T;
}

async function apiGet<T = unknown>(path: string): Promise<T> {
  return apiRequest<T>(path);
}

// -----------------------------------------------------------------------------
// ANALYTICS & OVERVIEW
// -----------------------------------------------------------------------------

export const fetchAdminOverview = (): Promise<AdminOverview> =>
  apiGet<AdminOverview>("/admin/overview");

export const fetchAdminAnalyticsOverview = (): Promise<AdminAnalyticsOverview> =>
  apiGet<AdminAnalyticsOverview>("/admin/analytics/overview");

export const fetchAdminAnalyticsUsers = (period = "30d"): Promise<AdminAnalyticsUsers> =>
  apiGet<AdminAnalyticsUsers>(`/admin/analytics/users?period=${encodeURIComponent(period)}`);

export const fetchAdminAnalyticsRevenue = (period = "30d"): Promise<AdminAnalyticsRevenue> =>
  apiGet<AdminAnalyticsRevenue>(`/admin/analytics/revenue?period=${encodeURIComponent(period)}`);

export const fetchAdminAnalyticsSubscriptions = (): Promise<AdminAnalyticsSubscriptions> =>
  apiGet<AdminAnalyticsSubscriptions>("/admin/analytics/subscriptions");

export const fetchAdminAnalyticsAI = (): Promise<AdminAnalyticsAI> =>
  apiGet<AdminAnalyticsAI>("/admin/analytics/ai");

export const fetchAdminAnalyticsSecurity = (period = "7d"): Promise<AdminAnalyticsSecurity> =>
  apiGet<AdminAnalyticsSecurity>(`/admin/analytics/security?period=${encodeURIComponent(period)}`);

// -----------------------------------------------------------------------------
// USER MANAGEMENT
// -----------------------------------------------------------------------------

export interface ListUsersParams {
  page?: number;
  page_size?: number;
  q?: string;
  status?: string;
  plan?: string;
  subscription_status?: string;
  sort_by?: string;
  sort_order?: string;
}

export const fetchAdminUsers = (params: ListUsersParams = {}): Promise<AdminPaginatedUsers> => {
  const query = new URLSearchParams();
  if (params.page) query.set("page", String(params.page));
  if (params.page_size) query.set("page_size", String(params.page_size));
  if (params.q) query.set("q", params.q);
  if (params.status) query.set("status", params.status);
  if (params.plan) query.set("plan", params.plan);
  if (params.subscription_status) query.set("subscription_status", params.subscription_status);
  if (params.sort_by) query.set("sort_by", params.sort_by);
  if (params.sort_order) query.set("sort_order", params.sort_order);
  const qStr = query.toString();
  return apiGet<AdminPaginatedUsers>("/admin/users" + (qStr ? `?${qStr}` : ""));
};

export const fetchAdminUserDetail = (userId: string): Promise<AdminUserDetail> =>
  apiGet<AdminUserDetail>(`/admin/users/${encodeURIComponent(userId)}/detail`);

export const updateAdminUser = (
  userId: string,
  payload: {
    full_name?: string | null;
    user_status?: string;
    plan_code?: string;
    billing_plan_id?: string | null;
    entitlement_status?: string;
    trial_ends_at?: string | null;
    paid_until?: string | null;
    reason: string;
  },
): Promise<AdminUserRow> =>
  apiRequest<AdminUserRow>(`/admin/users/${encodeURIComponent(userId)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

export const suspendAdminUser = (userId: string, reason: string): Promise<{ status: string }> =>
  apiRequest<{ status: string }>(
    `/admin/users/${encodeURIComponent(userId)}/suspend?reason=${encodeURIComponent(reason)}`,
    { method: "POST" },
  );

export const restoreAdminUser = (userId: string, reason: string): Promise<{ status: string }> =>
  apiRequest<{ status: string }>(
    `/admin/users/${encodeURIComponent(userId)}/restore?reason=${encodeURIComponent(reason)}`,
    { method: "POST" },
  );

export const revokeAdminUserSessions = (
  userId: string,
  reason: string,
): Promise<{ status: string }> =>
  apiRequest<{ status: string }>(
    `/admin/users/${encodeURIComponent(userId)}/revoke-sessions?reason=${encodeURIComponent(reason)}`,
    { method: "POST" },
  );

export const updateAdminUserLocation = (
  userId: string,
  payload: {
    country?: string | null;
    state?: string | null;
    city?: string | null;
    postal_code?: string | null;
    reason: string;
  },
): Promise<{ status: string }> =>
  apiRequest<{ status: string }>(`/admin/users/${encodeURIComponent(userId)}/location`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

export const deleteAdminUser = (
  userId: string,
  reason: string,
  confirmation = "DELETE",
): Promise<{ status: string }> =>
  apiRequest<{ status: string }>(`/admin/users/${encodeURIComponent(userId)}/delete`, {
    method: "POST",
    body: JSON.stringify({ reason, confirmation }),
  });

// -----------------------------------------------------------------------------
// BILLING PLANS
// -----------------------------------------------------------------------------

export const fetchBillingPlans = (): Promise<AdminBillingPlanRow[]> =>
  apiGet<AdminBillingPlanRow[]>("/admin/plans");

export const createBillingPlan = (payload: {
  code: string;
  name: string;
  access_level: string;
  billing_period: string;
  price: number | string;
  currency: string;
  google_play_product_id?: string | null;
  description?: string | null;
  features?: Record<string, unknown> | null;
  is_active?: boolean;
}): Promise<AdminBillingPlanRow> =>
  apiRequest<AdminBillingPlanRow>("/admin/plans", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const updateBillingPlan = (
  planId: string,
  payload: {
    name?: string;
    access_level?: string;
    billing_period?: string;
    price?: number | string;
    currency?: string;
    google_play_product_id?: string | null;
    description?: string | null;
    features?: Record<string, unknown> | null;
    is_active?: boolean;
    reason: string;
  },
): Promise<AdminBillingPlanRow> =>
  apiRequest<AdminBillingPlanRow>(`/admin/plans/${encodeURIComponent(planId)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

export const deleteBillingPlan = (planId: string, reason = "Deleted unused plan"): Promise<void> =>
  apiRequest<void>(
    `/admin/plans/${encodeURIComponent(planId)}?reason=${encodeURIComponent(reason)}`,
    { method: "DELETE" },
  );

// -----------------------------------------------------------------------------
// PAYMENTS MANAGEMENT
// -----------------------------------------------------------------------------

export interface ListPaymentsParams {
  page?: number;
  page_size?: number;
  q?: string;
  status?: string;
  user_id?: string;
  payment_method?: string;
}

export const fetchPayments = (params: ListPaymentsParams = {}): Promise<AdminPaginatedPayments> => {
  const query = new URLSearchParams();
  if (params.page) query.set("page", String(params.page));
  if (params.page_size) query.set("page_size", String(params.page_size));
  if (params.q) query.set("q", params.q);
  if (params.status) query.set("status", params.status);
  if (params.user_id) query.set("user_id", params.user_id);
  if (params.payment_method) query.set("payment_method", params.payment_method);
  const qStr = query.toString();
  return apiGet<AdminPaginatedPayments>("/admin/payments" + (qStr ? `?${qStr}` : ""));
};

export const recordPayment = (payload: {
  user_id: string;
  billing_plan_id?: string | null;
  amount: number | string;
  currency?: string;
  payment_method: string;
  provider?: string | null;
  reference?: string | null;
  status?: string;
  notes?: string | null;
  received_at?: string;
  reason: string;
}): Promise<AdminPaymentRow> =>
  apiRequest<AdminPaymentRow>("/admin/payments", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const updatePayment = (
  paymentId: string,
  payload: {
    payment_method?: string;
    provider?: string | null;
    reference?: string | null;
    notes?: string | null;
    reason: string;
  },
): Promise<AdminPaymentRow> =>
  apiRequest<AdminPaymentRow>(`/admin/payments/${encodeURIComponent(paymentId)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

export const voidPayment = (paymentId: string, reason: string): Promise<AdminPaymentRow> =>
  apiRequest<AdminPaymentRow>(`/admin/payments/${encodeURIComponent(paymentId)}/void`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });

// -----------------------------------------------------------------------------
// SUBSCRIPTIONS & AI
// -----------------------------------------------------------------------------

export const fetchAdminSubscriptions = (): Promise<AdminAnalyticsSubscriptions> =>
  apiGet<AdminAnalyticsSubscriptions>("/admin/subscriptions");

export const fetchAdminAIUsage = (): Promise<AdminAnalyticsAI> =>
  apiGet<AdminAnalyticsAI>("/admin/ai-usage");

// -----------------------------------------------------------------------------
// SECURITY & AUDIT LOGS
// -----------------------------------------------------------------------------

export interface ListSecurityEventsParams {
  page?: number;
  page_size?: number;
  q?: string;
  event_type?: string;
  user_id?: string;
}

export const fetchAdminSecurityEvents = (
  params: ListSecurityEventsParams = {},
): Promise<AdminPaginatedSecurityEvents> => {
  const query = new URLSearchParams();
  if (params.page) query.set("page", String(params.page));
  if (params.page_size) query.set("page_size", String(params.page_size));
  if (params.q) query.set("q", params.q);
  if (params.event_type) query.set("event_type", params.event_type);
  if (params.user_id) query.set("user_id", params.user_id);
  const qStr = query.toString();
  return apiGet<AdminPaginatedSecurityEvents>(
    "/admin/security-events" + (qStr ? `?${qStr}` : ""),
  );
};

export interface ListActionLogsParams {
  page?: number;
  page_size?: number;
  q?: string;
  action?: string;
  actor_id?: string;
  target_user_id?: string;
}

export const fetchAdminActionLogs = (
  params: ListActionLogsParams = {},
): Promise<AdminPaginatedActionLogs> => {
  const query = new URLSearchParams();
  if (params.page) query.set("page", String(params.page));
  if (params.page_size) query.set("page_size", String(params.page_size));
  if (params.q) query.set("q", params.q);
  if (params.action) query.set("action", params.action);
  if (params.actor_id) query.set("actor_id", params.actor_id);
  if (params.target_user_id) query.set("target_user_id", params.target_user_id);
  const qStr = query.toString();
  return apiGet<AdminPaginatedActionLogs>("/admin/action-logs" + (qStr ? `?${qStr}` : ""));
};

// -----------------------------------------------------------------------------
// SYSTEM READINESS & RELEASES
// -----------------------------------------------------------------------------

export const fetchSystemReadiness = (): Promise<Readiness> =>
  apiGet<Readiness>("/admin/readiness");

export const sendAdminTestEmail = (): Promise<{ status: string; recipient: string }> =>
  apiRequest<{ status: string; recipient: string }>("/admin/email/test", { method: "POST" });

export const fetchAppRelease = (): Promise<AppRelease> =>
  apiGet<AppRelease>("/admin/app-release");

export const updateAppRelease = (payload: Partial<AppRelease>): Promise<AppRelease> =>
  apiRequest<AppRelease>("/admin/app-release", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

// -----------------------------------------------------------------------------
// CSV EXPORT HELPER
// -----------------------------------------------------------------------------

export function getExportUrl(resource: "users" | "payments" | "action_logs"): string {
  return `${API_BASE_URL}/admin/export/${encodeURIComponent(resource)}`;
}
