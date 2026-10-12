#!/usr/bin/env node
/**
 * Regenerates src/data/skills.generated.json from the repository's source of
 * truth: skills/<name>/manifest.json (falling back to SKILL.md frontmatter)
 * plus the git history of each skill directory for activity metrics.
 *
 * Run from the site directory:  node scripts/sync-skills.mjs
 *
 * The generated file is committed, and CI fails when it drifts from the
 * repository, so the leaderboard never shows invented numbers.
 *
 * Exports the pure helpers so they can be unit tested without running git.
 */
import { execFileSync } from "node:child_process";
import { mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, "..", "..");
const skillsRoot = path.join(repoRoot, "skills");
const outFile = path.resolve(here, "..", "src", "data", "skills.generated.json");

export const REPO = "chaos-design/skills";
export const REPO_URL = "https://github.com/chaos-design/skills";
export const INSTALL_PREFIX = `npx skills add ${REPO_URL} --skill`;

export const WEEKS = 8;
const WEEK_MS = 7 * 24 * 60 * 60 * 1000;

/** Display names for the agent ids used in skill manifests. */
const AGENT_NAMES = {
  "claude-code": "Claude Code",
  "claude-ai": "Claude",
  cursor: "Cursor",
  "codex-cli": "Codex CLI",
  "gemini-cli": "Gemini CLI",
  opencode: "OpenCode",
};

/** UTC+8 timestamp formatted as YYYY-MM-DD HH:mm:ss (repository convention). */
export function formatTimestamp(date) {
  return new Date(date.getTime() + 8 * 60 * 60 * 1000).toISOString().slice(0, 19).replace("T", " ");
}

/** Date-only (YYYY-MM-DD) of an ISO-8601 string, in its own offset. */
export function isoDate(value) {
  return value.slice(0, 10);
}

/** Parse the small YAML frontmatter subset used by SKILL.md files. */
export function parseFrontmatter(text) {
  const match = /^---\r?\n([\s\S]*?)\r?\n---/.exec(text);
  if (!match) return {};
  const data = {};
  let folded = null;
  for (const line of match[1].split(/\r?\n/)) {
    const field = /^([A-Za-z][\w-]*):\s*(.*)$/.exec(line);
    if (field && !/^\s/.test(line)) {
      const key = field[1];
      const value = field[2].trim();
      if (value === ">" || value === ">-" || value === "|" || value === "|-") {
        folded = [];
        data[key] = folded;
      } else {
        folded = null;
        data[key] = unquote(value);
      }
      continue;
    }
    if (folded && /^\s+\S/.test(line)) {
      folded.push(line.trim());
    }
  }
  for (const [key, value] of Object.entries(data)) {
    if (Array.isArray(value)) data[key] = value.join(" ").trim();
  }
  return data;
}

function unquote(value) {
  if (value.length >= 2) {
    const first = value[0];
    const last = value[value.length - 1];
    if ((first === '"' && last === '"') || (first === "'" && last === "'")) {
      return value.slice(1, -1);
    }
  }
  return value;
}

/** Bucket commit timestamps into WEEKS rolling 7-day windows ending at `anchor`. */
export function weeklyBuckets(dates, anchor) {
  const buckets = new Array(WEEKS).fill(0);
  for (const date of dates) {
    const age = anchor.getTime() - date.getTime();
    // Clock skew (future commits) counts toward the current week.
    const index = age < 0 ? WEEKS - 1 : WEEKS - 1 - Math.floor(age / WEEK_MS);
    if (index >= 0) buckets[index] += 1;
  }
  return buckets;
}

function git(args) {
  return execFileSync("git", ["-C", repoRoot, ...args], {
    encoding: "utf8",
    maxBuffer: 64 * 1024 * 1024,
  });
}

function commitLog(relPath) {
  const out = git(["log", "--format=%ad", "--date=iso-strict", "--", relPath]);
  return out
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function contributorCount(relPath) {
  // HEAD is explicit: without a revision on the command line, shortlog
  // reads commits from stdin when stdin is not a TTY (the case when run
  // from Node), silently returning zero contributors.
  return git(["shortlog", "-sn", "HEAD", "--", relPath])
    .split("\n")
    .filter((line) => line.trim()).length;
}

/** Category group is the segment before the "·" separator in the manifest. */
export function categoryGroup(raw) {
  const group = String(raw ?? "").split("·")[0].trim();
  return group || "Skill";
}

function buildSkill(name, anchor, log) {
  const dir = path.join(skillsRoot, name);
  let manifest = {};
  try {
    manifest = JSON.parse(readFileSync(path.join(dir, "manifest.json"), "utf8"));
  } catch {
    manifest = {};
  }
  let frontmatter = {};
  try {
    frontmatter = parseFrontmatter(readFileSync(path.join(dir, "SKILL.md"), "utf8"));
  } catch {
    frontmatter = {};
  }

  const dates = log.map((entry) => new Date(entry));
  const weekly = weeklyBuckets(dates, anchor);
  const lastCommit = log.length > 0 ? isoDate(log[0]) : null;
  const firstCommit = log.length > 0 ? isoDate(log[log.length - 1]) : null;

  return {
    name,
    version: manifest.version ?? frontmatter.version ?? "0.0.0",
    category: categoryGroup(manifest.category ?? frontmatter.category),
    description: manifest.description ?? frontmatter.description ?? "",
    repo: REPO,
    homepage: manifest.homepage ?? `${REPO_URL}/tree/main/skills/${name}`,
    compat: Array.isArray(manifest.compat) ? manifest.compat : [],
    stats: {
      totalCommits: dates.length,
      commits8w: weekly.reduce((sum, n) => sum + n, 0),
      commits7d: weekly[WEEKS - 1],
      weekly,
      firstCommit,
      lastCommit,
      contributors: contributorCount(`skills/${name}`),
    },
  };
}

function buildAgents(skills) {
  const counts = new Map();
  for (const skill of skills) {
    for (const id of skill.compat) {
      counts.set(id, (counts.get(id) ?? 0) + 1);
    }
  }
  return [...counts.entries()]
    .map(([id, count]) => ({ id, name: AGENT_NAMES[id] ?? id, skills: count }))
    .sort((a, b) => b.skills - a.skills || a.name.localeCompare(b.name));
}

function main() {
  const now = new Date();
  const names = readdirSync(skillsRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort();
  const logs = names.map((name) => commitLog(`skills/${name}`));
  // Anchor the rolling activity windows to the newest commit in the
  // repository, not to wall-clock time, so the generated data is a pure
  // function of repository state and stays stable between syncs.
  const newest = logs.map((log) => Date.parse(log[0] ?? "")).filter(Number.isFinite);
  const anchor = new Date(newest.length > 0 ? Math.max(...newest) : 0);
  const skills = names.map((name, index) => buildSkill(name, anchor, logs[index]));
  const payload = {
    generatedAt: formatTimestamp(now),
    repo: REPO,
    repoUrl: REPO_URL,
    installPrefix: INSTALL_PREFIX,
    agents: buildAgents(skills),
    skills,
  };
  mkdirSync(path.dirname(outFile), { recursive: true });
  writeFileSync(outFile, `${JSON.stringify(payload, null, 2)}\n`);
  console.log(
    `synced ${skills.length} skills -> ${path.relative(repoRoot, outFile)} (${payload.generatedAt} UTC+8)`,
  );
}

const invokedDirectly =
  process.argv[1] !== undefined && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invokedDirectly) {
  main();
}
