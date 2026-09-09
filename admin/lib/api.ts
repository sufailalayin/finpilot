export const API_BASE_URL = "/api/backend";

async function apiRequest(path: string, init: RequestInit = {}) {
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
    throw new Error(body.detail ?? "Admin request failed");
  }
  return response.status === 204 ? null : response.json();
}

async function apiGet(path: string) {
  return apiRequest(path);
}

export const fetchAdminOverview = () => apiGet("/admin/overview");
export const fetchAdminUsers = (q = "") =>
  apiGet("/admin/users" + (q ? "?q=" + encodeURIComponent(q) : ""));
export const fetchAdminSubscriptions = () => apiGet("/admin/subscriptions");
export const fetchAdminAIUsage = () => apiGet("/admin/ai-usage");
export const fetchAdminSecurityEvents = () => apiGet("/admin/security-events");

export const fetchAdminActionLogs = () => apiGet("/admin/action-logs");

export const updateAdminUser = (
  userId: string,
  payload: {
    user_status?: string;
    plan_code?: string;
    entitlement_status?: string;
    trial_ends_at?: string | null;
    paid_until?: string | null;
    reason: string;
  },
) =>
  apiRequest("/admin/users/" + encodeURIComponent(userId), {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

export const revokeAdminUserSessions = (userId: string, reason: string) =>
  apiRequest(
    "/admin/users/" +
      encodeURIComponent(userId) +
      "/revoke-sessions?reason=" +
      encodeURIComponent(reason),
    { method: "POST" },
  );


export const sendAdminTestEmail = () =>
  apiRequest("/admin/email/test", { method: "POST" });
