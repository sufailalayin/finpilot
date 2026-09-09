import { NextRequest, NextResponse } from "next/server";

const BACKEND_BASE_URL =
  process.env.FINPILOT_API_BASE_URL ??
  "http://127.0.0.1:8000/api/v1";

export async function POST(request: NextRequest) {
  const body = await request.text();
  const base = BACKEND_BASE_URL.replace(/\/$/, "");

  const response = await fetch(base + "/auth/login", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body,
    cache: "no-store",
  });
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    return NextResponse.json(data, { status: response.status });
  }
  if (!data.user?.is_admin) {
    return NextResponse.json(
      { detail: "Administrator access required." },
      { status: 403 },
    );
  }

  const mfa = await fetch(base + "/auth/admin/mfa/request", {
    method: "POST",
    headers: {
      authorization: "Bearer " + data.access_token,
    },
    cache: "no-store",
  });
  const mfaData = await mfa.json().catch(() => ({}));

  if (!mfa.ok) {
    return NextResponse.json(mfaData, { status: mfa.status });
  }

  const result = NextResponse.json({
    mfa_required: true,
    email: data.user.email,
    message: mfaData.message,
  });
  result.cookies.set("finpilot_admin_mfa_pending", data.access_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/api/session",
    maxAge: 60 * 10,
  });
  return result;
}
