/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // The backend base URL; the console reads APIs only (read-only, proposal-only).
  env: {
    TC_API_BASE: process.env.TC_API_BASE ?? "http://localhost:8100",
  },
};

export default nextConfig;
