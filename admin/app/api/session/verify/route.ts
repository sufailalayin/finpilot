import { NextRequest, NextResponse } from "next/server";

const BACKEND_BASE_URL =
  process.env.FINPILOT_API_BASE_URL ??
  process.env.NEXT_PUBLIC_FINPILOT_API_BASE_URL ??
  "https://finpilot-backend-production-1cb7.up.railway.app/api/v1";

export async function POST(request: NextRequest) {
  const pending = request.cookies.get("finpilot_admin_mfa_pending")?.value;
  if (!pending) {
    return NextResponse.json(
      { detail: "Administrator verification session expired." },
      { status: 401 },
    );
  }

  const body = await request.text();
  const response = await fetch(
    BACKEND_BASE_URL.replace(/\/$/, "") + "/auth/admin/mfa/verify",
    {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: "Bearer " + pending,
      },
      body,
      cache: "no-store",
    },
  );
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    return NextResponse.json(data, { status: response.status });
  }

  const result = NextResponse.json({ user: data.user });
  result.cookies.delete("finpilot_admin_mfa_pending");
  result.cookies.set("finpilot_admin_session", data.access_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/",
    maxAge: 60 * 30,
  });
  return result;
}
