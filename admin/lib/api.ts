export const API_BASE_URL = "/api/backend";

async function apiGet(path: string) {
  const response = await fetch(API_BASE_URL + path, {
    credentials: "same-origin",
    cache: "no-store",
  });
  if (response.status === 401 || response.status === 403) {
    throw new Error("ADMIN_SESSION_EXPIRED");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? "Unable to load admin data");
  }
  return response.json();
}

export const fetchAdminOverview = () => apiGet("/admin/overview");
export const fetchAdminUsers = (q = "") =>
  apiGet("/admin/users" + (q ? "?q=" + encodeURIComponent(q) : ""));
export const fetchAdminSubscriptions = () => apiGet("/admin/subscriptions");
export const fetchAdminAIUsage = () => apiGet("/admin/ai-usage");
export const fetchAdminSecurityEvents = () => apiGet("/admin/security-events");
