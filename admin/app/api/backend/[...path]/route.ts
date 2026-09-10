import { NextRequest, NextResponse } from "next/server";
import {
  backendBaseUrl,
  readSmallBody,
  rejectCrossSite,
  tooLargeResponse,
} from "../../../../lib/server-security";

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;

  if (path.some((segment) =>
    segment === "." ||
    segment === ".." ||
    segment.includes("/") ||
    segment.includes("\\")
  )) {
    return NextResponse.json(
      { detail: "Invalid admin proxy path." },
      { status: 400 },
    );
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

  const target =
    base + "/" + path.map((segment) => encodeURIComponent(segment)).join("/");

  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  const cookieToken = request.cookies.get("finpilot_admin_session")?.value;

  if (contentType) headers.set("content-type", contentType);
  if (cookieToken) {
    headers.set("authorization", "Bearer " + cookieToken);
  }

  if (!["GET", "HEAD", "OPTIONS"].includes(request.method)) {
    const rejected = rejectCrossSite(request);
    if (rejected) return rejected;
  }

  const init: RequestInit = {
    method: request.method,
    headers,
    cache: "no-store",
  };

  if (!["GET", "HEAD"].includes(request.method)) {
    try {
      init.body = await readSmallBody(request, 64 * 1024);
    } catch {
      return tooLargeResponse();
    }
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
