"use client";

import { Languages } from "lucide-react";
import { createContext, type ReactNode, useCallback, useContext, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { useIsomorphicLayoutEffect } from "@/lib/use-isomorphic-layout-effect";
import { cn } from "@/lib/utils";

export type Lang = "en" | "zh";

// `en` is the source of truth for the key set; `zh` is checked against it so a
// missing translation fails the type check. Only UI chrome is translated here —
// data-driven strings (skill names, categories, agent names, repo) stay as-is.
const en = {
  "nav.leaderboard": "Leaderboard",
  "nav.tryIt": "Try it",
  "nav.agents": "Agents",
  "nav.github": "GitHub",
  "nav.menu": "Open menu",
  "nav.ariaHome": "home",
  "hero.tagline": "The Open Agent Skills Ecosystem",
  "hero.subtitle":
    "Production-oriented agent skills for content extraction, bilingual reading, slides, HTML briefs and geo flow maps — install any of them with a single command.",
  "hero.tryNow": "Try it now",
  "agents.title": "Available for these agents",
  "leaderboard.title": "Skills Leaderboard",
  "leaderboard.search": "Search skills...",
  "leaderboard.tabAll": "All Time ({count})",
  "leaderboard.tabTrending": "Trending (7d)",
  "leaderboard.tabHot": "Hot",
  "leaderboard.tabCommits": "Commits",
  "leaderboard.tabUpdated": "Last Updated",
  "leaderboard.empty": "No skills match your filters.",
  "table.rank": "#",
  "table.skill": "Skill",
  "table.activity": "8W Activity",
  "table.activityRange": "8-week activity window: {from} – {to}.",
  "table.commits": "Commits",
  "table.updated": "Updated",
  "table.mobileSuffix": "/8w",
  "tooltip.commits8w": "{n} commits in the last 8 weeks",
  "row.copyHint": "Click anywhere in the row to copy its install command",
  "copy.command": "Copy install command",
  "copy.done": "Copied",
  "install.command": "Command",
  "install.prompt": "Prompt",
  "install.guide": "Installation guide",
  "install.required": "Required skills",
  "install.optional": "Optional skills",
  "install.runtime": "Runtime & setup",
  "install.installTogether": "Install together",
  "install.none": "None — this skill is self-contained.",
  "related.commits": "{n} commits",
  "detail.back": "Back to the skills leaderboard",
  "detail.install": "Installation",
  "detail.gone": "This skill is not in the current dataset.",
  "detail.statRepository": "Repository",
  "detail.statVersion": "Version",
  "detail.statFirstSeen": "First seen",
  "detail.statLastUpdated": "Last updated",
  "detail.statTotalCommits": "Total commits",
  "detail.statContributors": "Contributors",
  "detail.activityTitle": "Activity (8 weeks)",
  "detail.activityNote": "{a} commits in the last 8 weeks · {b} in the last 7 days",
  "detail.relatedSkills": "Related skills",
  "detail.viewSource": "View source on GitHub",
  "detail.docsTitle": "Documentation",
  "detail.docsLoading": "Loading documentation…",
  "detail.docsMissing": "No README is available for this skill in this language.",
  "detail.docsViewGitHub": "Read it on GitHub",
  "footer.apache": "Apache-2.0",
  "footer.github": "GitHub",
  "footer.readme": "README",
  "footer.synced": "Data synced {date} (UTC+8)",
  "theme.label": "Appearance",
  "theme.light": "Light",
  "theme.dark": "Dark",
  "theme.system": "System",
  "lang.label": "Switch language",
};

type MessageKey = keyof typeof en;

const zh: Record<MessageKey, string> = {
  "nav.leaderboard": "排行榜",
  "nav.tryIt": "试试",
  "nav.agents": "支持的 Agents",
  "nav.github": "GitHub",
  "nav.menu": "打开菜单",
  "nav.ariaHome": "主页",
  "hero.tagline": "开放的 Agent Skills 生态",
  "hero.subtitle":
    "面向生产环境的 Agent Skills，涵盖内容提取、双语阅读、幻灯片、HTML 简报与地理流向图等——一条命令即可安装其中任意一个。",
  "hero.tryNow": "立即体验",
  "agents.title": "支持这些 Agents",
  "leaderboard.title": "Skills 排行榜",
  "leaderboard.search": "搜索 skills...",
  "leaderboard.tabAll": "总榜（{count}）",
  "leaderboard.tabTrending": "趋势（7 天）",
  "leaderboard.tabHot": "热门",
  "leaderboard.tabCommits": "按提交数",
  "leaderboard.tabUpdated": "按最近更新",
  "leaderboard.empty": "没有匹配的 skills。",
  "table.rank": "#",
  "table.skill": "技能",
  "table.activity": "8 周活跃",
  "table.activityRange": "8 周活跃窗口：{from} – {to}。",
  "table.commits": "提交数",
  "table.updated": "更新时间",
  "table.mobileSuffix": "/8 周",
  "tooltip.commits8w": "近 8 周 {n} 次提交",
  "row.copyHint": "点击本行任意位置复制安装命令",
  "copy.command": "复制安装命令",
  "copy.done": "已复制",
  "install.command": "命令",
  "install.prompt": "提示词",
  "install.guide": "安装引导",
  "install.required": "所需技能",
  "install.optional": "可选技能",
  "install.runtime": "运行时与配置",
  "install.installTogether": "一并安装",
  "install.none": "无 —— 该技能可独立安装。",
  "related.commits": "{n} 次提交",
  "detail.back": "返回 skills 排行榜",
  "detail.install": "安装",
  "detail.gone": "当前数据集中没有这个 skill。",
  "detail.statRepository": "仓库",
  "detail.statVersion": "版本",
  "detail.statFirstSeen": "首次提交",
  "detail.statLastUpdated": "最近更新",
  "detail.statTotalCommits": "总提交数",
  "detail.statContributors": "贡献者",
  "detail.activityTitle": "活跃（8 周）",
  "detail.activityNote": "近 8 周 {a} 次提交 · 近 7 天 {b} 次",
  "detail.relatedSkills": "相关 skills",
  "detail.viewSource": "在 GitHub 上查看源码",
  "detail.docsTitle": "文档",
  "detail.docsLoading": "正在加载文档…",
  "detail.docsMissing": "该 skill 暂无当前语言的 README。",
  "detail.docsViewGitHub": "在 GitHub 上阅读",
  "footer.apache": "Apache-2.0",
  "footer.github": "GitHub",
  "footer.readme": "README",
  "footer.synced": "数据同步于 {date}（UTC+8）",
  "theme.label": "外观",
  "theme.light": "浅色",
  "theme.dark": "深色",
  "theme.system": "跟随系统",
  "lang.label": "切换语言",
};

const dict: Record<Lang, Record<MessageKey, string>> = { en, zh };

type Interpolations = Record<string, string | number>;

function interpolate(template: string, vars?: Interpolations): string {
  if (!vars) return template;
  return template.replace(/\{(\w+)\}/g, (match, key: string) =>
    vars[key] != null ? String(vars[key]) : match,
  );
}

export type I18nValue = {
  lang: Lang;
  /** Switch language (and persist it). */
  setLang: (next: Lang) => void;
  /** Translate a chrome string, optionally filling `{var}` placeholders. */
  t: (key: MessageKey, vars?: Interpolations) => string;
};

const I18nContext = createContext<I18nValue | null>(null);

const STORAGE_KEY = "lang";

function detectLang(): Lang {
  const nav = (navigator.language ?? "").toLowerCase();
  return nav.startsWith("zh") ? "zh" : "en";
}

/** The stored choice wins; only a first-time visitor falls back to the browser. */
export function readStoredLang(): Lang | null {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    if (value === "en" || value === "zh") return value;
  } catch {
    // storage unavailable (private mode) — fall back to the browser language.
  }
  return null;
}

export function I18nProvider({ children }: { children: ReactNode }) {
  // Server render defaults to English so the HTML matches on hydration; the
  // stored language is applied in a layout effect, i.e. before the first paint.
  const [lang, setLangState] = useState<Lang>("en");

  useIsomorphicLayoutEffect(() => {
    const next = readStoredLang() ?? detectLang();
    setLangState(next);
    document.documentElement.lang = next === "zh" ? "zh" : "en";
  }, []);

  const setLang = useCallback((next: Lang) => {
    setLangState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // ignore — the choice still applies for this visit.
    }
    document.documentElement.lang = next === "zh" ? "zh" : "en";
  }, []);

  const t = useCallback(
    (key: MessageKey, vars?: Interpolations) => interpolate(dict[lang][key] ?? key, vars),
    [lang],
  );

  const value = useMemo<I18nValue>(() => ({ lang, setLang, t }), [lang, setLang, t]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useI18n(): I18nValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within an I18nProvider");
  return ctx;
}

/** Compact toggle showing the language you would switch TO (中 / EN). */
export function LanguageToggle({ className }: { className?: string }) {
  const { lang, setLang, t } = useI18n();
  const target: Lang = lang === "zh" ? "en" : "zh";
  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={() => setLang(target)}
      aria-label={t("lang.label")}
      title={target === "zh" ? "切换到中文" : "Switch to English"}
      className={cn(
        "h-9 gap-1.5 px-2.5 font-mono text-xs text-ds-gray-600 hover:text-foreground",
        className,
      )}
    >
      <Languages className="h-4 w-4" />
      <span className="leading-none">{target === "zh" ? "中文" : "EN"}</span>
    </Button>
  );
}
