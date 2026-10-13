#!/usr/bin/env node
/**
 * Regenerates public/data/skills.json from the repository's source of
 * truth: skills/<name>/manifest.json (falling back to SKILL.md frontmatter)
 * plus the real commit history GitHub reports for each skill directory.
 *
 * Run from the site directory:  node scripts/sync-skills.mjs
 *
 * The file lives in public/ so the browser can re-fetch it on every visit
 * (cache: "no-store"), which is what keeps the leaderboard fresh between
 * deploys. It is generated, never hand-written.
 *
 * Activity comes from the GitHub REST API rather than a local clone, so the
 * numbers do not depend on how deep the checkout happens to be. Set
 * GITHUB_TOKEN to raise the rate limit (60 requests/hour unauthenticated).
 *
 * Exports the pure helpers so they can be unit tested without hitting the API.
 */
import { mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, "..", "..");
const skillsRoot = path.join(repoRoot, "skills");
const outFile = path.resolve(here, "..", "public", "data", "skills.json");

export const REPO = "chaos-design/skills";
export const REPO_URL = "https://github.com/chaos-design/skills";
export const INSTALL_PREFIX = `npx skills add ${REPO_URL} --skill`;

export const WEEKS = 8;
const WEEK_MS = 7 * 24 * 60 * 60 * 1000;

/** Display names for the agent ids used in skill manifests. */
const AGENT_NAMES = {
  "claude-ai": "Claude",
  cursor: "Cursor",
  "codex-cli": "Codex CLI",
  "gemini-cli": "Gemini CLI",
  opencode: "OpenCode",
};

/**
 * Ids that are the same product for display purposes: a manifest listing both
 * "claude-ai" and "claude-code" is one agent, Claude, not two.
 */
const AGENT_ALIASES = {
  "claude-code": "claude-ai",
};

/** Collapse alias ids onto the id the site renders, so Claude counts once. */
export function canonicalAgent(id) {
  return AGENT_ALIASES[String(id)] ?? String(id);
}

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

const API_ROOT = "https://api.github.com";
const PER_PAGE = 100;
/** 100 commits per page x 20 pages: far more than a skill directory has. */
const MAX_PAGES = 20;

/** "1234+octocat@users.noreply.github.com" -> "octocat"; null for other mail. */
export function noReplyLogin(email) {
  const match = /^(?:\d+\+)?([^@]+)@users\.noreply\.github\.com$/i.exec(String(email ?? "").trim());
  return match ? match[1] : null;
}

/** The identity a commit is attributed to, for counting contributors. */
export function authorKey(commit) {
  const login = commit?.author?.login;
  if (login) return `login:${login}`;
  const email = commit?.commit?.author?.email;
  // A commit without a linked account still carries the owner's noreply
  // address, which encodes the same login — count it as the same person.
  const alias = noReplyLogin(email);
  if (alias) return `login:${alias}`;
  if (email) return `email:${email}`;
  const name = commit?.commit?.author?.name;
  return name ? `name:${name}` : "unknown";
}

/** The authored-at date GitHub reports for a commit payload. */
export function commitDate(commit) {
  return commit?.commit?.author?.date ?? commit?.commit?.committer?.date ?? null;
}

async function apiGet(route, params) {
  const url = new URL(route, API_ROOT);
  for (const [key, value] of Object.entries(params ?? {})) {
    url.searchParams.set(key, String(value));
  }
  const headers = {
    Accept: "application/vnd.github+json",
    "User-Agent": "chaos-design-skills-site",
  };
  if (process.env.GITHUB_TOKEN) headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  const response = await fetch(url, { headers });
  if (!response.ok) {
    throw new Error(
      `GitHub API ${response.status} ${response.statusText} for ${url.pathname}${url.search} — set GITHUB_TOKEN to raise the rate limit`,
    );
  }
  return response.json();
}

/** Every commit that touched `relPath`, newest first. */
async function commitHistory(relPath) {
  const commits = [];
  for (let page = 1; page <= MAX_PAGES; page += 1) {
    const batch = await apiGet(`/repos/${REPO}/commits`, {
      path: relPath,
      per_page: PER_PAGE,
      page,
    });
    commits.push(...batch);
    if (batch.length < PER_PAGE) break;
  }
  return commits;
}

/** Category group is the segment before the "·" separator in the manifest. */
export function categoryGroup(raw) {
  const group = String(raw ?? "")
    .split("·")[0]
    .trim();
  return group || "Skill";
}

function buildSkill(name, anchor, history) {
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

  // GitHub returns the newest commit first, so index 0 is the latest change.
  const stamps = history.map(commitDate).filter(Boolean).sort().reverse();
  const dates = stamps.map((stamp) => new Date(stamp));
  const weekly = weeklyBuckets(dates, anchor);
  const lastCommit = stamps.length > 0 ? isoDate(stamps[0]) : null;
  const firstCommit = stamps.length > 0 ? isoDate(stamps[stamps.length - 1]) : null;

  return {
    name,
    version: manifest.version ?? frontmatter.version ?? "0.0.0",
    category: categoryGroup(manifest.category ?? frontmatter.category),
    description: manifest.description ?? frontmatter.description ?? "",
    repo: REPO,
    homepage: manifest.homepage ?? `${REPO_URL}/tree/main/skills/${name}`,
    // Canonicalised and de-duplicated: Claude and Claude Code are one entry.
    compat: [
      ...new Set((Array.isArray(manifest.compat) ? manifest.compat : []).map(canonicalAgent)),
    ],
    stats: {
      totalCommits: dates.length,
      commits8w: weekly.reduce((sum, n) => sum + n, 0),
      commits7d: weekly[WEEKS - 1],
      weekly,
      firstCommit,
      lastCommit,
      contributors: new Set(history.map(authorKey)).size,
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

async function main() {
  const now = new Date();
  const names = readdirSync(skillsRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort();
  // One request per skill directory (100 commits a page), fetched in parallel.
  const histories = await Promise.all(names.map((name) => commitHistory(`skills/${name}`)));
  // Anchor the rolling activity windows to the newest commit GitHub reports,
  // not to wall-clock time, so the generated data is a pure function of the
  // repository state and stays stable between syncs.
  const newest = histories
    .flat()
    .map((commit) => Date.parse(commitDate(commit) ?? ""))
    .filter(Number.isFinite);
  const anchor = new Date(newest.length > 0 ? Math.max(...newest) : 0);
  const skills = names.map((name, index) => buildSkill(name, anchor, histories[index]));
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
