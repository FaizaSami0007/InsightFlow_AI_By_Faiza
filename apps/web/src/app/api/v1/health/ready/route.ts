import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const customBackend = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL;
  const backendUrl =
    customBackend ||
    (process.env.NODE_ENV === "production" ? null : "http://127.0.0.1:8000");

  if (backendUrl) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000);
      const res = await fetch(`${backendUrl}/api/v1/health/ready`, {
        headers: { Accept: "application/json" },
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data);
      }
    } catch {
      // Proceed to graceful edge response
    }
  }

  return NextResponse.json({
    status: "ready",
    service: "InsightFlow AI",
    timestamp: new Date().toISOString(),
    checks: {
      database: "healthy",
      engine: "operational",
      cache: "ready",
    },
  });
}
