import { NextRequest, NextResponse } from "next/server";
import { rejectCrossSite } from "../../../../lib/server-security";

export async function POST(request: NextRequest) {
  const rejected = rejectCrossSite(request);
  if (rejected) return rejected;
  const response = NextResponse.json({ ok: true });
  response.cookies.set("finpilot_admin_session", "", {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/",
    maxAge: 0,
  });
  response.cookies.set("finpilot_admin_mfa_pending", "", {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/api/session",
    maxAge: 0,
  });
  return response;
}
