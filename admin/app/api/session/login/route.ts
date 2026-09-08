import { NextRequest, NextResponse } from "next/server";

const BACKEND_BASE_URL =
  process.env.FINPILOT_API_BASE_URL ??
  process.env.NEXT_PUBLIC_FINPILOT_API_BASE_URL ??
  "https://finpilot-backend-production-1cb7.up.railway.app/api/v1";

export async function POST(request: NextRequest) {
  const body = await request.text();
  const response = await fetch(BACKEND_BASE_URL.replace(/\/$/, "") + "/auth/login", {
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
    return NextResponse.json({ detail: "Administrator access required." }, { status: 403 });
  }

  const result = NextResponse.json({ user: data.user });
  result.cookies.set("finpilot_admin_session", data.access_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/",
    maxAge: 60 * 60 * 8,
  });
  return result;
}
