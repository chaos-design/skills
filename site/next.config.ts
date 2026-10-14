import type { NextConfig } from "next";

// BASE_PATH is set by the GitHub Pages deploy job (project pages live under
// /<repo>). Vercel deploys at the domain root and leaves it empty.
const basePath = (process.env.BASE_PATH ?? "").replace(/\/+$/, "");

const nextConfig: NextConfig = {
  // Fully static export: the same `out/` artifact is served by GitHub Pages
  // and by Vercel, so there is no server runtime to keep in sync.
  output: "export",
  basePath,
  // Exposed to the client: the runtime data fetch (/data/skills.json) has to
  // carry the same prefix as the router when deployed to GitHub Pages.
  env: {
    NEXT_PUBLIC_BASE_PATH: basePath,
  },
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  reactStrictMode: true,
};

export default nextConfig;
