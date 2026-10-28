import { describe, expect, it } from "vitest";
import {
  authorKey,
  categoryGroup,
  commitDate,
  formatTimestamp,
  installGuide,
  isoDate,
  normalizeReadme,
  parseFrontmatter,
  READMES,
  resolveReadmePath,
  WEEKS,
  weeklyBuckets,
} from "./sync-skills.mjs";

describe("parseFrontmatter", () => {
  it("reads simple key/value pairs and strips quotes", () => {
    const data = parseFrontmatter('---\nname: "html-brief"\nversion: 0.1.0\n---\n# Body\n');
    expect(data).toEqual({ name: "html-brief", version: "0.1.0" });
  });

  it("joins folded block scalars with spaces", () => {
    const data = parseFrontmatter(
      "---\ndescription: >\n  Turns a complex question\n  into one HTML brief.\n---\n",
    );
    expect(data.description).toBe("Turns a complex question into one HTML brief.");
  });

  it("ignores body content that only looks like frontmatter", () => {
    const data = parseFrontmatter("# No frontmatter here\n\nname: not-frontmatter\n");
    expect(data).toEqual({});
  });
});

describe("categoryGroup", () => {
  it("takes the segment before the middle dot separator", () => {
    expect(categoryGroup("Workflow · Runtime feedback injection → checkpoint drain")).toBe(
      "Workflow",
    );
  });

  it("falls back to Skill for empty values", () => {
    expect(categoryGroup("")).toBe("Skill");
    expect(categoryGroup(undefined)).toBe("Skill");
  });
});

describe("weeklyBuckets", () => {
  const anchor = new Date("2026-10-12T09:00:00Z");
  const day = 24 * 60 * 60 * 1000;

  it("places commits into rolling 7-day windows ending at the anchor", () => {
    const dates = [
      new Date(anchor.getTime() - 2 * day), // current week
      new Date(anchor.getTime() - 9 * day), // previous week
      new Date(anchor.getTime() - 20 * day), // two weeks back
    ];
    const buckets = weeklyBuckets(dates, anchor);
    expect(buckets).toHaveLength(WEEKS);
    expect(buckets[WEEKS - 1]).toBe(1);
    expect(buckets[WEEKS - 2]).toBe(1);
    expect(buckets[WEEKS - 3]).toBe(1);
    expect(buckets.reduce((sum, n) => sum + n, 0)).toBe(3);
  });

  it("counts future timestamps toward the current week", () => {
    const buckets = weeklyBuckets([new Date(anchor.getTime() + 3 * 60 * 60 * 1000)], anchor);
    expect(buckets[WEEKS - 1]).toBe(1);
  });

  it("drops commits older than the whole window", () => {
    const buckets = weeklyBuckets([new Date(anchor.getTime() - 90 * day)], anchor);
    expect(buckets.every((count) => count === 0)).toBe(true);
  });
});

describe("formatTimestamp", () => {
  it("renders UTC+8 timestamps as YYYY-MM-DD HH:mm:ss", () => {
    expect(formatTimestamp(new Date("2026-10-12T09:30:00Z"))).toBe("2026-10-12 17:30:00");
  });
});

describe("isoDate", () => {
  it("keeps the calendar date of the ISO string itself", () => {
    expect(isoDate("2026-10-09T23:59:00+08:00")).toBe("2026-10-09");
    expect(isoDate("2026-10-09T00:30:00-05:00")).toBe("2026-10-09");
  });
});

describe("GitHub commit payloads", () => {
  it("reads the authored-at date, falling back to the committer date", () => {
    expect(commitDate({ commit: { author: { date: "2026-10-09T10:00:00Z" } } })).toBe(
      "2026-10-09T10:00:00Z",
    );
    expect(commitDate({ commit: { committer: { date: "2026-10-08T10:00:00Z" } } })).toBe(
      "2026-10-08T10:00:00Z",
    );
    expect(commitDate({})).toBeNull();
  });

  it("attributes a commit to its GitHub login when there is one", () => {
    expect(
      authorKey({ author: { login: "xcz" }, commit: { author: { email: "me@example.com" } } }),
    ).toBe("login:xcz");
  });

  it("falls back to email, then name, for commits without a linked account", () => {
    expect(authorKey({ commit: { author: { email: "me@example.com" } } })).toBe(
      "email:me@example.com",
    );
    expect(authorKey({ commit: { author: { name: "Someone" } } })).toBe("name:Someone");
  });

  it("counts the same person once across both shapes", () => {
    const commits = [
      { author: { login: "xcz" }, commit: { author: { email: "xcz@users.noreply.github.com" } } },
      { commit: { author: { email: "xcz@users.noreply.github.com" } } },
      { commit: { author: { email: "other@example.com" } } },
    ];
    expect(new Set(commits.map(authorKey)).size).toBe(2);
  });
});

describe("resolveReadmePath", () => {
  it("resolves relative links against the skill directory", () => {
    expect(resolveReadmePath("html-brief", "./LICENSE")).toBe("skills/html-brief/LICENSE");
    expect(resolveReadmePath("html-brief", "LICENSE")).toBe("skills/html-brief/LICENSE");
    expect(resolveReadmePath("html-brief", "../web-markdown/README.md")).toBe(
      "skills/web-markdown/README.md",
    );
  });

  it("clamps at the repository root instead of escaping it", () => {
    expect(resolveReadmePath("html-brief", "../../screenshots/x.webp")).toBe("screenshots/x.webp");
    expect(resolveReadmePath("html-brief", "../../../still/here.md")).toBe("still/here.md");
  });
});

describe("READMES", () => {
  it("publishes both languages from the repo's file convention", () => {
    expect(Object.keys(READMES)).toEqual(["en", "zh"]);
    expect(READMES.en.source).toBe("README.md");
    expect(READMES.zh.source).toBe("README.zh-CN.md");
    for (const [lang, entry] of Object.entries(READMES)) {
      expect(entry.target).toBe(`README.${lang}.md`);
    }
  });
});

describe("normalizeReadme", () => {
  it("converts raw img tags to markdown images on raw.githubusercontent", () => {
    const out = normalizeReadme(
      'See the gallery:\n\n<img src="../../screenshots/s/a.webp" width="420" alt="template screenshot">\n',
      "s",
    );
    expect(out).toContain(
      "![template screenshot](https://raw.githubusercontent.com/chaos-design/skills/main/screenshots/s/a.webp)",
    );
    // width is dropped: the site's CSS sizes images itself.
    expect(out).not.toContain("420");
    expect(out).not.toContain("<img");
  });

  it("leaves absolute image URLs alone while converting the tag", () => {
    const out = normalizeReadme('<img src="https://example.com/x.png" alt="x">', "s");
    expect(out).toBe("![x](https://example.com/x.png)");
  });

  it("keeps single-quoted attribute values verbatim", () => {
    const out = normalizeReadme("<img src='../../screenshots/s/b.webp' alt='single quoted'>", "s");
    expect(out).toBe(
      "![single quoted](https://raw.githubusercontent.com/chaos-design/skills/main/screenshots/s/b.webp)",
    );
  });

  it("drops the language-switch lines in both directions", () => {
    const en = normalizeReadme("# T\n\n[中文](./README.zh-CN.md)\n\n## Next", "s");
    expect(en).toBe("# T\n\n## Next");
    const zh = normalizeReadme("# 标题\n\n[English](./README.md)\n\n## 下一节", "s");
    expect(zh).toBe("# 标题\n\n## 下一节");
  });

  it("rewrites relative links to GitHub blob URLs", () => {
    const out = normalizeReadme(
      "See [LICENSE](./LICENSE), [web-markdown](../web-markdown/README.md) and [flow](./references/flow.md).",
      "bilingual-reader",
    );
    expect(out).toContain(
      "[LICENSE](https://github.com/chaos-design/skills/blob/main/skills/bilingual-reader/LICENSE)",
    );
    expect(out).toContain(
      "[web-markdown](https://github.com/chaos-design/skills/blob/main/skills/web-markdown/README.md)",
    );
    expect(out).toContain(
      "[flow](https://github.com/chaos-design/skills/blob/main/skills/bilingual-reader/references/flow.md)",
    );
  });

  it("rewrites relative markdown images to raw URLs", () => {
    const out = normalizeReadme("![diagram](../../screenshots/s/flow.svg)", "s");
    expect(out).toBe(
      "![diagram](https://raw.githubusercontent.com/chaos-design/skills/main/screenshots/s/flow.svg)",
    );
  });

  it("leaves relative paths inside code fences untouched", () => {
    const out = normalizeReadme(
      "# t\n\n```bash\ncat ./README.md\ncp ../other/x.md .\n```\n\n[ref](./references/a.md)",
      "s",
    );
    expect(out).toContain("cat ./README.md");
    expect(out).toContain("cp ../other/x.md .");
    expect(out).toContain(
      "[ref](https://github.com/chaos-design/skills/blob/main/skills/s/references/a.md)",
    );
  });

  it("keeps absolute URLs as they are", () => {
    const out = normalizeReadme("[site](https://github.com/chaos-design/skills)", "s");
    expect(out).toBe("[site](https://github.com/chaos-design/skills)");
  });
});

describe("installGuide", () => {
  const known = ["web-markdown", "x-tweet-fetcher", "html-brief"];

  it("keeps only in-repo dependency names and trims runtime lines", () => {
    const guide = installGuide(
      {
        dependsOn: ["web-markdown", "some-external-skill"],
        optionalDeps: ["x-tweet-fetcher"],
        runtime: ["Python 3.9+", "  pip install 'markitdown[all]'  "],
      },
      known,
    );
    expect(guide.dependsOn).toEqual(["web-markdown"]);
    expect(guide.optionalDeps).toEqual(["x-tweet-fetcher"]);
    expect(guide.runtime).toEqual(["Python 3.9+", "pip install 'markitdown[all]'"]);
  });

  it("returns an empty, well-formed guide when the manifest has none", () => {
    expect(installGuide({}, known)).toEqual({
      dependsOn: [],
      optionalDeps: [],
      runtime: [],
    });
    // Old manifests without an install block never crash the sync.
    expect(installGuide(undefined, known)).toEqual({
      dependsOn: [],
      optionalDeps: [],
      runtime: [],
    });
  });

  it("drops empty or non-string entries", () => {
    const guide = installGuide({ dependsOn: ["", "  ", null, "html-brief"] }, known);
    expect(guide.dependsOn).toEqual(["html-brief"]);
  });
});
