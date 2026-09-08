import { NextRequest, NextResponse } from "next/server";

const BACKEND_BASE_URL =
  process.env.FINPILOT_API_BASE_URL ??
  process.env.NEXT_PUBLIC_FINPILOT_API_BASE_URL ??
  "https://finpilot-backend-production-1cb7.up.railway.app/api/v1";

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const target = BACKEND_BASE_URL.replace(/\/$/, "") + "/" + path.join("/");

  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  const cookieToken = request.cookies.get("finpilot_admin_session")?.value;
  const incomingAuthorization = request.headers.get("authorization");

  if (contentType) headers.set("content-type", contentType);
  if (cookieToken) {
    headers.set("authorization", "Bearer " + cookieToken);
  } else if (incomingAuthorization) {
    headers.set("authorization", incomingAuthorization);
  }

  const init: RequestInit = {
    method: request.method,
    headers,
    cache: "no-store",
  };

  if (!["GET", "HEAD"].includes(request.method)) {
    init.body = await request.text();
  }

  try {
    const response = await fetch(target, init);
    const body = await response.text();

    return new NextResponse(body, {
      status: response.status,
      headers: {
        "content-type": response.headers.get("content-type") ?? "application/json",
        "cache-control": "no-store",
        "x-content-type-options": "nosniff",
      },
    });
  } catch {
    return NextResponse.json(
      { detail: "FinPilot backend is temporarily unavailable." },
      { status: 502 },
    );
  }
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
