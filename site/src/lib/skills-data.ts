import { readFileSync } from "node:fs";
import path from "node:path";
import type { SkillsData } from "@/lib/skills";

/**
 * Build-time read of the generated dataset (public/data/skills.json).
 *
 * Server-only: it touches the filesystem, so it may never be imported from a
 * client component. The value it returns is only the first paint — the
 * SkillsProvider re-fetches the same file over HTTP on every visit, so a
 * redeployed dataset is picked up without rebuilding the HTML.
 */
export function loadSkillsData(): SkillsData {
  const file = path.join(process.cwd(), "public", "data", "skills.json");
  return JSON.parse(readFileSync(file, "utf8")) as SkillsData;
}
