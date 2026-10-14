import generated from "@/data/skills.generated.json";

export type Agent = {
  id: string;
  name: string;
  skills: number;
};

export type Skill = {
  name: string;
  version: string;
  category: string;
  description: string;
  repo: string;
  homepage: string;
  compat: string[];
  stats: {
    totalCommits: number;
    commits8w: number;
    commits7d: number;
    /** Commit counts for the 8 rolling weekly buckets, oldest first. */
    weekly: number[];
    firstCommit: string | null;
    lastCommit: string | null;
    contributors: number;
  };
};

export type SortKey = "all" | "trending" | "hot";

export const repoMeta = {
  repo: generated.repo,
  repoUrl: generated.repoUrl,
  installPrefix: generated.installPrefix,
  generatedAt: generated.generatedAt,
} as const;

export const skills = generated.skills as Skill[];
export const agents = generated.agents as Agent[];

/** Case-insensitive match across the fields a visitor would search by. */
export function filterSkills(list: Skill[], query: string): Skill[] {
  const needle = query.trim().toLowerCase();
  if (!needle) return list;
  return list.filter((skill) =>
    [skill.name, skill.repo, skill.category, skill.description].some((field) =>
      field.toLowerCase().includes(needle),
    ),
  );
}

/** Sort by the metric each leaderboard tab stands for. */
export function sortSkills(list: Skill[], key: SortKey): Skill[] {
  const rows = [...list];
  switch (key) {
    case "trending":
      return rows.sort(
        (a, b) =>
          b.stats.commits7d - a.stats.commits7d ||
          dateValue(b.stats.lastCommit) - dateValue(a.stats.lastCommit) ||
          a.name.localeCompare(b.name),
      );
    case "hot":
      return rows.sort(
        (a, b) =>
          dateValue(b.stats.lastCommit) - dateValue(a.stats.lastCommit) ||
          b.stats.totalCommits - a.stats.totalCommits ||
          a.name.localeCompare(b.name),
      );
    default:
      return rows.sort(
        (a, b) =>
          b.stats.totalCommits - a.stats.totalCommits ||
          dateValue(b.stats.lastCommit) - dateValue(a.stats.lastCommit) ||
          a.name.localeCompare(b.name),
      );
  }
}

function dateValue(iso: string | null): number {
  return iso ? Date.parse(`${iso}T00:00:00Z`) : 0;
}

/** 1286544 -> "1.3M"; small numbers stay exact. */
export function formatCompact(value: number): string {
  if (value < 1000) return String(value);
  if (value < 1_000_000) return `${trimZero(value / 1000)}K`;
  return `${trimZero(value / 1_000_000)}M`;
}

function trimZero(value: number): string {
  const fixed = value >= 100 ? value.toFixed(0) : value.toFixed(1);
  return fixed.replace(/\.0$/, "");
}

/** "2026-10-09" -> "Oct 9, 2026" (UTC, so output never depends on the host TZ). */
export function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(`${iso}T00:00:00Z`).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
}
