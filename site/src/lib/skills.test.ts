import { describe, expect, it } from "vitest";
import {
  agents,
  filterSkills,
  formatCompact,
  formatDate,
  skills,
  sortSkills,
} from "./skills";

describe("generated skill data", () => {
  it("describes every skill in the repository with real metadata", () => {
    // The repository currently ships 10 skills; the count can only grow.
    expect(skills.length).toBeGreaterThanOrEqual(10);
    expect(new Set(skills.map((skill) => skill.name)).size).toBe(skills.length);
    for (const skill of skills) {
      expect(skill.name).toMatch(/^[a-z0-9-]+$/);
      expect(skill.description.length).toBeGreaterThan(20);
      expect(skill.homepage).toMatch(/^https:\/\/github\.com\/chaos-design\/skills\/tree\/main\/skills\//);
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
