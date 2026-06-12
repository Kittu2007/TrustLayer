import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    if (process.env.NODE_ENV === "development") {
      return [
        {
          source: "/api/:path*",
          destination: "http://127.0.0.1:8000/api/:path*",
        },
      ];
    }
    return [
      {
        source: "/api/:path*",
        destination: "https://trustlayerai.vercel.app/api/:path*",
      },
    ];
  },
};

export default nextConfig;
