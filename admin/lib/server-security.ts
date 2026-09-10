import { NextRequest, NextResponse } from "next/server";

export function backendBaseUrl(): string {
  const configured = process.env.FINPILOT_API_BASE_URL?.trim();
  if (configured) return configured.replace(/\/$/, "");

  if (process.env.NODE_ENV === "production") {
    throw new Error("FINPILOT_API_BASE_URL is required in production");
  }
  return "http://127.0.0.1:8000/api/v1";
}

export function rejectCrossSite(request: NextRequest): NextResponse | null {
  const origin = request.headers.get("origin");
  if (origin && origin !== request.nextUrl.origin) {
    return NextResponse.json(
      { detail: "Cross-origin admin request rejected." },
      { status: 403 },
    );
  }

  const fetchSite = request.headers.get("sec-fetch-site");
  if (fetchSite === "cross-site") {
    return NextResponse.json(
      { detail: "Cross-site admin request rejected." },
      { status: 403 },
    );
  }
  return null;
}

export async function readSmallBody(
  request: NextRequest,
  maxBytes = 16 * 1024,
): Promise<string> {
  const declared = Number(request.headers.get("content-length") ?? "0");
  if (Number.isFinite(declared) && declared > maxBytes) {
    throw new Error("REQUEST_TOO_LARGE");
  }

  const body = await request.text();
  if (new TextEncoder().encode(body).length > maxBytes) {
    throw new Error("REQUEST_TOO_LARGE");
  }
  return body;
}

export function tooLargeResponse(): NextResponse {
  return NextResponse.json(
    { detail: "Request body is too large." },
    { status: 413 },
  );
}
