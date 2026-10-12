import { describe, expect, it } from "vitest";
import {
  categoryGroup,
  formatTimestamp,
  isoDate,
  parseFrontmatter,
  weeklyBuckets,
  WEEKS,
} from "./sync-skills.mjs";

describe("parseFrontmatter", () => {
  it("reads simple key/value pairs and strips quotes", () => {
    const data = parseFrontmatter('---\nname: "html-brief"\nversion: 0.1.0\n---\n# Body\n');
    expect(data).toEqual({ name: "html-brief", version: "0.1.0" });
  });

  it("joins folded block scalars with spaces", () => {
    const data = parseFrontmatter("---\ndescription: >\n  Turns a complex question\n  into one HTML brief.\n---\n");
    expect(data.description).toBe("Turns a complex question into one HTML brief.");
  });

  it("ignores body content that only looks like frontmatter", () => {
    const data = parseFrontmatter("# No frontmatter here\n\nname: not-frontmatter\n");
    expect(data).toEqual({});
  });
});

describe("categoryGroup", () => {
  it("takes the segment before the middle dot separator", () => {
    expect(categoryGroup("Workflow · Runtime feedback injection → checkpoint drain")).toBe("Workflow");
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
