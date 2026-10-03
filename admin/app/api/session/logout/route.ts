import { NextRequest, NextResponse } from "next/server";
import {
  backendBaseUrl,
  rejectCrossSite,
} from "../../../../lib/server-security";

function clearAdminCookies(response: NextResponse) {
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
}

export async function POST(request: NextRequest) {
  const rejected = rejectCrossSite(request);
  if (rejected) return rejected;

  const sessionToken = request.cookies.get("finpilot_admin_session")?.value;

  if (sessionToken) {
    let base: string;
    try {
      base = backendBaseUrl();
    } catch {
      return NextResponse.json(
        { detail: "Admin backend is not configured." },
        { status: 503 },
      );
    }

    try {
      const backendResponse = await fetch(base + "/auth/admin/logout", {
        method: "POST",
        headers: {
          authorization: "Bearer " + sessionToken,
        },
        cache: "no-store",
      });

      if (
        !backendResponse.ok &&
        backendResponse.status !== 401 &&
        backendResponse.status !== 403
      ) {
        const data = await backendResponse.json().catch(() => ({}));
        return NextResponse.json(
          data,
          { status: backendResponse.status },
        );
      }
    } catch {
      return NextResponse.json(
        { detail: "FinPilot backend is temporarily unavailable." },
        { status: 502 },
      );
    }
  }

  const response = NextResponse.json({ ok: true });
  clearAdminCookies(response);
  return response;
}
