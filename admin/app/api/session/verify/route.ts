import { NextRequest, NextResponse } from "next/server";
import {
  backendBaseUrl,
  readSmallBody,
  rejectCrossSite,
  tooLargeResponse,
} from "../../../../lib/server-security";

export async function POST(request: NextRequest) {
  const rejected = rejectCrossSite(request);
  if (rejected) return rejected;

  const pending = request.cookies.get("finpilot_admin_mfa_pending")?.value;
  if (!pending) {
    return NextResponse.json(
      { detail: "Administrator verification session expired." },
      { status: 401 },
    );
  }

  let body: string;
  try {
    body = await readSmallBody(request);
  } catch {
    return tooLargeResponse();
  }

  let base: string;
  try {
    base = backendBaseUrl();
  } catch {
    return NextResponse.json(
      { detail: "Admin backend is not configured." },
      { status: 503 },
    );
  }

  const response = await fetch(
    base + "/auth/admin/mfa/verify",
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
