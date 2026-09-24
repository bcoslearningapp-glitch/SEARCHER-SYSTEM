import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  reactStrictMode: true,
  experimental: {
    // Uploads (source PDFs, Qur'an datasets) pass through server actions; match the API's 100 MB limit.
    serverActions: { bodySizeLimit: "100mb" },
  },
  async redirects() {
    return [{ source: "/", destination: "/en", permanent: false }];
  },
};

export default nextConfig;
