import type { Metadata, Viewport } from "next";
import { GeistMono } from "geist/font/mono";
import { GeistSans } from "geist/font/sans";
import { repoMeta } from "@/lib/skills";
import "./globals.css";

// Geist Sans / Geist Mono are bundled with the `geist` package and self-hosted
// at build time, so the export never fetches fonts from a CDN.

// Resolved once at build time: an explicit override wins, then the Vercel
// deployment URL, then the GitHub Pages project path.
const siteUrl =
  process.env.NEXT_PUBLIC_SITE_URL ??
  (process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : "https://chaos-design.github.io/skills");

export const metadata: Metadata = {
  title: {
    default: `The Agent Skills Directory · ${repoMeta.repo}`,
    template: `%s · ${repoMeta.repo}`,
  },
  description:
    "A curated collection of production-oriented agent skills for content extraction, bilingual reading, slide generation, HTML briefs, geo flow maps and more. Install any of them with a single command.",
  applicationName: repoMeta.repo,
  authors: [{ name: "Chaos Design", url: "https://github.com/chaos-design" }],
  creator: "Chaos Design",
  publisher: "Chaos Design",
  keywords: [
    "agent skills",
    "AI agents",
    "skills directory",
    "Claude Code",
    "Codex",
    "Cursor",
    "Gemini CLI",
    "OpenCode",
  ],
  metadataBase: new URL(siteUrl),
  alternates: {
    canonical: "/",
  },
  openGraph: {
    type: "website",
    siteName: `${repoMeta.repo} — The Agent Skills Directory`,
    title: `The Agent Skills Directory · ${repoMeta.repo}`,
    description:
      "Production-oriented agent skills for content extraction, bilingual reading, slides, HTML briefs and geo flow maps. Install any of them with a single command.",
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: `The Agent Skills Directory · ${repoMeta.repo}`,
    description:
      "Production-oriented agent skills for content extraction, bilingual reading, slides, HTML briefs and geo flow maps. Install any of them with a single command.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport: Viewport = {
  themeColor: "#000000",
  colorScheme: "dark",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`dark ${GeistSans.variable} ${GeistMono.variable}`}>
      <body className="antialiased">{children}</body>
    </html>
  );
}
