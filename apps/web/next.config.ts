import type { NextConfig } from "next";

const API_BACKEND_URL =
  process.env.API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
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
