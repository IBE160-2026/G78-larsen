// Next.js configuration (AD-17). Standalone output for the image; no trailing-slash redirect, so `/api/x/`
// reaches the backend's JSON 404 as it does through Caddy (AD-10). The `/api` rewrite exists in development only:
// the production build has no rewrites, and Caddy routes `/api` there.
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  skipTrailingSlashRedirect: true,
  poweredByHeader: false,
  async rewrites() {
    if (process.env.NODE_ENV !== 'development') return [];
    return [{ source: '/api/:path*', destination: 'http://127.0.0.1:8001/api/:path*' }];
  },
};

export default nextConfig;
