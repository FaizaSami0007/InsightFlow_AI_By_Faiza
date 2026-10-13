import type { NextConfig } from "next";

const configuredBackend =
  process.env.API_URL ||
  process.env.NEXT_PUBLIC_API_URL;

// Only default to localhost in local development
const API_BACKEND_URL =
  configuredBackend ||
  (process.env.NODE_ENV === "production" ? null : "http://127.0.0.1:8000");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    if (!API_BACKEND_URL) {
      return [];
    }
    return [
      {
        source: "/api/:path*",
        destination: `${API_BACKEND_URL}/api/:path*`,
      },
      {
        source: "/docs",
        destination: `${API_BACKEND_URL}/docs`,
      },
      {
        source: "/openapi.json",
        destination: `${API_BACKEND_URL}/openapi.json`,
      },
    ];
  },
};

export default nextConfig;
