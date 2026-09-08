export const API_BASE_URL =
  process.env.NEXT_PUBLIC_FINPILOT_API_BASE_URL ?? "http://localhost:8000/api/v1";

export async function fetchAdminOverview(token: string) {
  const response = await fetch(API_BASE_URL + "/admin/overview", {
    headers: { Authorization: "Bearer " + token },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Unable to load admin overview");
  }

  return response.json();
}

export async function fetchAdminUsers(token: string) {
  const response = await fetch(API_BASE_URL + "/admin/users", {
    headers: { Authorization: "Bearer " + token },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Unable to load admin users");
  }

  return response.json();
}
