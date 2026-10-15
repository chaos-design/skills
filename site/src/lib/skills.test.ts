import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import {
  agentPrompt,
  filterSkills,
  formatCompact,
  formatDate,
  getSkillByName,
  installCommand,
  readmePath,
  readmeSourceUrl,
  relatedSkills,
  repoMeta,
  type SkillsData,
  sortSkills,
} from "./skills";

/**
 * The dataset is read from the file the sync script generates, not from a
 * bundle: what these tests assert is what the site actually ships.
 */
function readGeneratedDataset(): SkillsData {
  const file = path.join(process.cwd(), "public", "data", "skills.json");
  return JSON.parse(readFileSync(file, "utf8")) as SkillsData;
}

const dataset = readGeneratedDataset();
const skills = dataset.skills;
const agents = dataset.agents;

describe("generated skill data", () => {
  it("describes every skill in the repository with real metadata", () => {
    // The repository currently ships 10 skills; the count can only grow.
    expect(skills.length).toBeGreaterThanOrEqual(10);
    expect(new Set(skills.map((skill) => skill.name)).size).toBe(skills.length);
    for (const skill of skills) {
      expect(skill.name).toMatch(/^[a-z0-9-]+$/);
      expect(skill.description.length).toBeGreaterThan(20);
      expect(skill.homepage).toMatch(
        /^https:\/\/github\.com\/chaos-design\/skills\/tree\/main\/skills\//,
      );
      expect(skill.category.length).toBeGreaterThan(0);
      expect(skill.version).toMatch(/^\d+\.\d+\.\d+$/);
    }
  });

  it("keeps the activity metrics internally consistent", () => {
    for (const skill of skills) {
      expect(skill.stats.weekly).toHaveLength(8);
      expect(skill.stats.commits8w).toBe(skill.stats.weekly.reduce((sum, n) => sum + n, 0));
      expect(skill.stats.commits7d).toBe(skill.stats.weekly[7]);
      expect(skill.stats.commits7d).toBeLessThanOrEqual(skill.stats.commits8w);
      expect(skill.stats.commits8w).toBeLessThanOrEqual(skill.stats.totalCommits);
      expect(skill.stats.totalCommits).toBeGreaterThan(0);
      expect(skill.stats.lastCommit).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(skill.stats.contributors).toBeGreaterThan(0);
    }
  });

  it("derives the agent strip from manifest compatibility", () => {
    expect(agents.length).toBeGreaterThan(0);
    for (const agent of agents) {
      expect(agent.name.length).toBeGreaterThan(0);
      expect(agent.skills).toBeGreaterThan(0);
      expect(agent.skills).toBeLessThanOrEqual(skills.length);
    }
  });
});

describe("filterSkills", () => {
  it("returns the full list for an empty or whitespace query", () => {
    expect(filterSkills(skills, "")).toHaveLength(skills.length);
    expect(filterSkills(skills, "   ")).toHaveLength(skills.length);
  });

  it("matches by skill name, case-insensitively", () => {
    const hits = filterSkills(skills, "HTML-BRIEF");
    expect(hits.map((skill) => skill.name)).toEqual(["html-brief"]);
  });

  it("matches by category", () => {
    const hits = filterSkills(skills, "workflow");
    // Skills whose category group is "Workflow · ..." must be matched; the
    // filter may additionally hit skills via name or description.
    const names = hits.map((skill) => skill.name);
    expect(names).toContain("plan-flow");
    expect(names).toContain("task-inject");
  });

  it("matches by description words", () => {
    const hits = filterSkills(skills, "bilingual");
    expect(hits.map((skill) => skill.name)).toEqual(["bilingual-reader"]);
  });

  it("returns nothing for a query that matches no skill", () => {
    expect(filterSkills(skills, "kubernetes-helm-charts")).toEqual([]);
  });
});

describe("sortSkills", () => {
  it("sorts all-time by total commits, descending", () => {
    const rows = sortSkills(skills, "all");
    const totals = rows.map((skill) => skill.stats.totalCommits);
    expect(totals).toEqual([...totals].sort((a, b) => b - a));
  });

  it("sorts trending by commits in the last 7 days, descending", () => {
    const rows = sortSkills(skills, "trending");
    const weekly = rows.map((skill) => skill.stats.commits7d);
    expect(weekly).toEqual([...weekly].sort((a, b) => b - a));
  });

  it("sorts hot by most recently updated", () => {
    const rows = sortSkills(skills, "hot");
    const dates = rows.map((skill) => skill.stats.lastCommit ?? "");
    expect(dates).toEqual([...dates].sort().reverse());
  });

  it("does not mutate the input list", () => {
    const before = skills.map((skill) => skill.name);
    sortSkills(skills, "hot");
    expect(skills.map((skill) => skill.name)).toEqual(before);
  });
});

describe("formatCompact", () => {
  it("keeps numbers below one thousand exact", () => {
    expect(formatCompact(0)).toBe("0");
    expect(formatCompact(8)).toBe("8");
    expect(formatCompact(999)).toBe("999");
  });

  it("abbreviates thousands and millions", () => {
    expect(formatCompact(1000)).toBe("1K");
    expect(formatCompact(1286544)).toBe("1.3M");
    expect(formatCompact(3_800_000)).toBe("3.8M");
  });
});

describe("formatDate", () => {
  it("formats ISO dates without depending on the host timezone", () => {
    expect(formatDate("2026-10-09")).toBe("Oct 9, 2026");
    expect(formatDate("2026-01-01")).toBe("Jan 1, 2026");
  });

  it("renders an em dash for missing dates", () => {
    expect(formatDate(null)).toBe("—");
  });
});

describe("getSkillByName", () => {
  it("returns the skill when the name matches", () => {
    const hit = getSkillByName(skills, "bilingual-reader");
    expect(hit?.name).toBe("bilingual-reader");
    expect(hit).toBe(skills.find((skill) => skill.name === "bilingual-reader"));
  });

  it("returns undefined for a name that is not a skill", () => {
    expect(getSkillByName(skills, "kubernetes-helm-charts")).toBeUndefined();
  });
});

describe("install strings", () => {
  it("builds the install command from the site's own configuration", () => {
    expect(installCommand("bilingual-reader")).toBe(`${repoMeta.installPrefix} bilingual-reader`);
  });

  it("hands the agent a prompt that installs and follows the skill", () => {
    const prompt = agentPrompt("domain-modeling");
    expect(prompt).toContain(`npx skills use "${repoMeta.repoUrl}" --skill "domain-modeling"`);
    expect(prompt).toContain("follow the generated skill instructions");
    expect(prompt).toContain("supporting-files directory");
  });
});

describe("readme paths", () => {
  it("returns the public data path of the published README", () => {
    expect(readmePath("web-markdown", "en")).toBe("data/skills/web-markdown/README.en.md");
    expect(readmePath("web-markdown", "zh")).toBe("data/skills/web-markdown/README.zh.md");
  });

  it("links missing docs back to the source README on GitHub", () => {
    expect(readmeSourceUrl("web-markdown", "en")).toBe(
      `${repoMeta.repoUrl}/blob/main/skills/web-markdown/README.md`,
    );
    expect(readmeSourceUrl("web-markdown", "zh")).toBe(
      `${repoMeta.repoUrl}/blob/main/skills/web-markdown/README.zh-CN.md`,
    );
  });
});

/**
 * The published docs must render as standalone pages: no raw HTML images, no
 * relative link targets, no cross-language switch lines that would push the
 * reader back to GitHub.
 */
function readPublishedReadme(skillName: string, lang: "en" | "zh"): string {
  const file = path.join(process.cwd(), "public", "data", "skills", skillName, `README.${lang}.md`);
  return readFileSync(file, "utf8");
}

describe("published readme docs", () => {
  it("ships both language copies for every skill in the dataset", () => {
    for (const skill of skills) {
      for (const lang of ["en", "zh"] as const) {
        const text = readPublishedReadme(skill.name, lang);
        expect(text.length, `${skill.name} ${lang} readme too small`).toBeGreaterThan(200);
        expect(text).not.toContain("<img");
        expect(text).not.toMatch(/\]\(\.{1,2}\//);
        expect(text).not.toMatch(/^\s*\[(?:中文|English)\]\(\.\//m);
      }
    }
  });
});

describe("relatedSkills", () => {
  it("never includes the source skill", () => {
    for (const skill of skills) {
      expect(relatedSkills(skills, skill, skills.length).map((item) => item.name)).not.toContain(
        skill.name,
      );
    }
  });

  it("caps the result at the requested limit", () => {
    expect(relatedSkills(skills, skills[0], 3)).toHaveLength(3);
    expect(relatedSkills(skills, skills[0], 2)).toHaveLength(2);
  });

  it("lists same-category skills before others", () => {
    const byCategory = new Map<string, string[]>();
    for (const skill of skills) {
      byCategory.set(skill.category, [...(byCategory.get(skill.category) ?? []), skill.name]);
    }
    const members = [...byCategory.values()].find((names) => names.length > 1);
    if (!members) return;
    const skill = skills.find((item) => item.name === members[0]);
    if (!skill) return;
    const related = relatedSkills(skills, skill, skills.length);
    const otherCategories = related.filter((item) => item.category !== skill.category);
    const lastSameCategory = related.length - 1 - otherCategories.length;
    for (let index = 0; index <= lastSameCategory; index += 1) {
      expect(related[index].category).toBe(skill.category);
    }
  });
});
