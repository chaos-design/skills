#!/usr/bin/env node
/**
 * Regenerates public/data/skills.json from the repository's source of
 * truth: skills/<name>/manifest.json (falling back to SKILL.md frontmatter)
 * plus the real commit history GitHub reports for each skill directory.
 *
 * Also republishes every skill README under public/data/skills/<name>/ as
 * README.en.md / README.zh.md, normalized so they render as standalone
 * pages (relative links retargeted to the repository's main branch).
 *
 * Run from the site directory:  node scripts/sync-skills.mjs
 *
 * The files live in public/ so the browser can re-fetch them on every visit
 * (cache: "no-store" for the JSON), which is what keeps the leaderboard
 * fresh between deploys. They are generated, never hand-written.
 *
 * Activity comes from the GitHub REST API rather than a local clone, so the
 * numbers do not depend on how deep the checkout happens to be. Set
 * GITHUB_TOKEN to raise the rate limit (60 requests/hour unauthenticated).
 *
 * Exports the pure helpers so they can be unit tested without hitting the API.
 */
import { existsSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, "..", "..");
const skillsRoot = path.join(repoRoot, "skills");
const dataDir = path.resolve(here, "..", "public", "data");
const outFile = path.join(dataDir, "skills.json");

export const REPO = "chaos-design/skills";
export const REPO_URL = `https://github.com/${REPO}`;
export const INSTALL_PREFIX = `npx skills add ${REPO_URL} --skill`;
/** Where a published README's relative links are retargeted at. */
const RAW_BASE = `https://raw.githubusercontent.com/${REPO}/main`;
const BLOB_BASE = `${REPO_URL}/blob/main`;

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
    // Short, language-neutral labels the site filters and badges with. Kept
    // as an ordered, de-duplicated string list so the leaderboard's chip row
    // stays stable across syncs.
    tags: [
      ...new Set(
        (Array.isArray(manifest.tags) ? manifest.tags : []).filter(
          (t) => typeof t === "string" && t.trim() !== "",
        ),
      ),
    ],
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

/**
 * The skill READMEs the site publishes per language: source file inside
 * skills/<name>/ and the flat target name under public/data/skills/<name>/.
 */
export const READMES = {
  en: { source: "README.md", target: "README.en.md" },
  zh: { source: "README.zh-CN.md", target: "README.zh.md" },
};

/**
 * Resolve a README-relative path ("./LICENSE", "../web-markdown/README.md",
 * "../../screenshots/x.webp") against the skill's directory in the repo.
 * Pure string math, clamped at the repository root like path.resolve.
 */
export function resolveReadmePath(skillName, relative) {
  const segments = [];
  for (const part of `skills/${skillName}/${relative}`.split("/")) {
    if (part === "" || part === ".") continue;
    if (part === "..") {
      if (segments.length > 0) segments.pop();
      continue;
    }
    segments.push(part);
  }
  return segments.join("/");
}

const FENCE = /^\s*(```|~~~)/;

/**
 * The value of an HTML attribute, double-quoted, single-quoted or bare.
 * Quoted forms keep whitespace inside the value ("template screenshot").
 */
function attrValue(attrs, name) {
  const match = new RegExp(`${name}\\s*=\\s*("([^"]*)"|'([^']*)'|[^\\s"'>]+)`).exec(attrs);
  if (!match) return "";
  return match[2] ?? match[3] ?? match[1];
}

/**
 * Rewrite a relative markdown image into raw.githubusercontent form.
 */
function rewriteImage(label, target, skillName) {
  return `${label}(${RAW_BASE}/${resolveReadmePath(skillName, target)})`;
}

/**
 * Rewrite a relative markdown link into a GitHub blob URL so the doc renders
 * as a standalone page without the repository checkout around it.
 */
function rewriteLink(label, target, skillName) {
  return `${label}(${BLOB_BASE}/${resolveReadmePath(skillName, target)})`;
}

/**
 * Make a skill README renderable as a standalone document on the site:
 *
 * - raw <img> tags become markdown images (react-markdown renders markdown
 *   images without a raw-HTML pass) pointing at raw.githubusercontent.com;
 * - the "[中文](./README.zh-CN.md)" / "[English](./README.md)" switch lines
 *   are dropped — the site has its own language toggle, so a link that
 *   pushes the reader back to GitHub is noise;
 * - every remaining relative link (./LICENSE, ../other-skill/README.md,
 *   ../../screenshots/...) is retargeted to the repository's main branch,
 *   as a blob URL for documents and a raw URL for images.
 *
 * Code fences are left byte-for-byte: the rules only apply to prose lines,
 * so a ```bash block that mentions ./README.md survives untouched.
 */
export function normalizeReadme(text, skillName) {
  const lines = String(text).split(/\r?\n/);
  const out = [];
  let inFence = false;
  for (const line of lines) {
    if (FENCE.test(line)) {
      inFence = !inFence;
      out.push(line);
      continue;
    }
    if (inFence) {
      out.push(line);
      continue;
    }
    let next = line;
    // Drop a language-switch line: the whole line is the switch link itself.
    const switchLine = /^\s*\[(?:中文|English)\]\(\.\/README(?:\.zh-CN)?\.md\)\s*$/.exec(next);
    if (switchLine) {
      out.push("");
      continue;
    }
    next = next.replace(/<img\s+([^>]*)>/gi, (_match, attrs) => {
      const src = attrValue(attrs, "src");
      const alt = attrValue(attrs, "alt");
      // A repository-relative src is re-rooted; anything absolute stays.
      const target = /^\.{1,2}\//.test(src)
        ? `${RAW_BASE}/${resolveReadmePath(skillName, src)}`
        : src;
      // width/height are dropped on purpose: the site's own CSS sizes images.
      return `![${alt}](${target})`;
    });
    next = next.replace(/(!?\[[^\]]+\])\((\.{1,2}\/[^()\s]+)\)/g, (_match, label, target) =>
      label.startsWith("!")
        ? rewriteImage(label, target, skillName)
        : rewriteLink(label, target, skillName),
    );
    out.push(next);
  }
  // A dropped switch line can leave a double blank behind; fold it away.
  return out.join("\n").replace(/\n{3,}/g, "\n\n");
}

/**
 * Publish both READMEs of every skill into public/data/skills/<name>/.
 * The subtree is rebuilt from scratch each run, so a removed language file
 * never lingers in the export.
 */
function publishReadmes(names) {
  rmSync(path.join(dataDir, "skills"), { recursive: true, force: true });
  let count = 0;
  for (const name of names) {
    for (const { source, target } of Object.values(READMES)) {
      const file = path.join(skillsRoot, name, source);
      if (!existsSync(file)) continue;
      const outDir = path.join(dataDir, "skills", name);
      mkdirSync(outDir, { recursive: true });
      writeFileSync(
        path.join(outDir, target),
        `${normalizeReadme(readFileSync(file, "utf8"), name)}\n`,
      );
      count += 1;
    }
  }
  return count;
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
  mkdirSync(dataDir, { recursive: true });
  writeFileSync(outFile, `${JSON.stringify(payload, null, 2)}\n`);
  const readmes = publishReadmes(names);
  console.log(
    `synced ${skills.length} skills and ${readmes} readme copies -> ${path.relative(
      repoRoot,
      dataDir,
    )} (${payload.generatedAt} UTC+8)`,
  );
}

const invokedDirectly =
  process.argv[1] !== undefined && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invokedDirectly) {
  main();
}
