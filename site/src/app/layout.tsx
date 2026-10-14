import { GeistMono } from "geist/font/mono";
import { GeistSans } from "geist/font/sans";
import type { Metadata, Viewport } from "next";
import { SkillsProvider } from "@/components/skills-provider";
import { ThemeInit } from "@/components/theme-init";
import { Toaster } from "@/components/ui/sonner";
import { I18nProvider } from "@/lib/i18n";
import { repoMeta } from "@/lib/skills";
import { loadSkillsData } from "@/lib/skills-data";
import "./globals.css";

// Geist Sans / Geist Mono are bundled with the `geist` package and self-hosted
// at build time, so the export never fetches fonts from a CDN.

// Resolved once at build time: an explicit override wins, then the Vercel
// deployment URL, then the GitHub Pages project path.
const siteUrl =
  process.env.NEXT_PUBLIC_SITE_URL ??
  (process.env.VERCEL_URL
    ? `https://${process.env.VERCEL_URL}`
    : "https://chaos-design.github.io/skills");

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
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#000000" },
  ],
  colorScheme: "light dark",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const data = loadSkillsData();
  return (
    <html lang="en" className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body className="antialiased">
        <ThemeInit />
        <I18nProvider>
          <SkillsProvider initialData={data}>{children}</SkillsProvider>
        </I18nProvider>
        {/* Top-centre, under the sticky header (h-14), so a copy confirmation
            never covers the navigation or the row that was just clicked. */}
        <Toaster position="top-center" offset={{ top: 72 }} />
      </body>
    </html>
  );
}
