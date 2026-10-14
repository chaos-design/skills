import { ImageResponse } from "next/og";
import { repoMeta } from "@/lib/skills";

// Required for `output: "export"`: the OG route must be prerendered to a
// static PNG at build time instead of served dynamically.
export const dynamic = "force-static";

export const alt = `The Agent Skills Directory · ${repoMeta.repo}`;
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

// Static OG card, prerendered at build time so the export stays self-contained.
export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          background: "#000",
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "72px 80px",
          fontFamily: "monospace",
        }}
      >
        <div style={{ color: "#8f8f8f", fontSize: 26, letterSpacing: 6 }}>
          THE AGENT SKILLS DIRECTORY
        </div>
        <div style={{ color: "#fff", fontSize: 84, fontWeight: 700, marginTop: 20, letterSpacing: -2 }}>
          {repoMeta.repo}
        </div>
        <div style={{ color: "#a1a1a1", fontSize: 30, marginTop: 28, lineHeight: 1.4, maxWidth: 880 }}>
          Production-oriented agent skills for content extraction, bilingual reading, slides,
          HTML briefs and geo flow maps.
        </div>
        <div
          style={{
            marginTop: 48,
            display: "flex",
            alignItems: "center",
            border: "1px solid #2e2e2e",
            borderRadius: 8,
            padding: "16px 24px",
            color: "#fff",
            fontSize: 26,
          }}
        >
          <span style={{ color: "#8f8f8f" }}>$ </span>
          npx skills add {repoMeta.repoUrl} --skill html-brief
        </div>
      </div>
    ),
    { ...size },
  );
}
