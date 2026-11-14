"use client";

import { Check, Copy, Sparkles } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CommandLine } from "@/components/command-line";
import { useSkills } from "@/components/skills-provider";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useI18n } from "@/lib/i18n";
import { notifyCopied } from "@/lib/notify";
import { agentPrompt, installCommand, installSet, type Skill } from "@/lib/skills";

const COPIED_MS = 2000;

/** Segment of the Command / Prompt switch. */
const SEGMENT_CLASS =
  "h-7 gap-1 rounded-[5px] border border-transparent px-2.5 font-mono text-xs text-ds-gray-600 shadow-none transition-colors hover:text-foreground data-[state=active]:border-border data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-none";

type Mode = "command" | "prompt";

/**
 * The commands to run to install a skill together with everything it needs:
 * required in-repo deps first, then the skill itself, then optional deps.
 * De-duplicated by name, in that top-to-bottom install order.
 */
function togetherCommands(guide: {
  required: Skill[];
  optional: Skill[];
  self: Skill | undefined;
}): string {
  const seen = new Set<string>();
  const lines: string[] = [];
  for (const skill of [...guide.required, guide.self, ...guide.optional]) {
    if (!skill || seen.has(skill.name)) continue;
    seen.add(skill.name);
    lines.push(installCommand(skill.name));
  }
  return lines.join("\n");
}

/**
 * The installation block: a Command / Prompt copy switch, plus a data-driven
 * installation guide — the in-repo skills that must be installed together with
 * this one, the ones that optionally extend it, and its runtime requirements.
 * Everything the guide shows is derived from the generated dataset, so it can
 * never drift from what the manifest actually declares.
 */
export function Installation({ skillName }: { skillName: string }) {
  const { t } = useI18n();
  const { data } = useSkills();
  const [mode, setMode] = useState<Mode>("command");
  const [copied, setCopied] = useState(false);
  const [guideCopied, setGuideCopied] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const guideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (timer.current) clearTimeout(timer.current);
      if (guideTimer.current) clearTimeout(guideTimer.current);
    };
  }, []);

  const guide = useMemo(() => installSet(data.skills, skillName), [data.skills, skillName]);
  const runtime = guide.self?.install?.runtime ?? [];
  const hasGuide = guide.required.length > 0 || guide.optional.length > 0 || runtime.length > 0;
  const content = mode === "command" ? installCommand(skillName) : agentPrompt(skillName);
  const together = useMemo(() => togetherCommands(guide), [guide]);

  const copy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(content);
    } catch {
      // Clipboard can be unavailable (insecure context, denied permission);
      // the text stays selectable on screen either way.
      return;
    }
    notifyCopied(content);
    setCopied(true);
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => setCopied(false), COPIED_MS);
  }, [content]);

  const copyTogether = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(together);
    } catch {
      // Same reason as above; the command block below stays selectable.
      return;
    }
    notifyCopied(together);
    setGuideCopied(true);
    if (guideTimer.current) clearTimeout(guideTimer.current);
    guideTimer.current = setTimeout(() => setGuideCopied(false), COPIED_MS);
  }, [together]);

  return (
    <section className="border-t border-border py-6">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-mono text-sm font-medium uppercase tracking-normal text-foreground">
          {t("detail.install")}
        </h2>
        <Tabs value={mode} onValueChange={(value) => setMode(value as Mode)}>
          <TabsList className="h-auto gap-0.5 rounded-md border border-border bg-ds-gray-100/60 p-0.5">
            <TabsTrigger value="command" className={SEGMENT_CLASS}>
              {t("install.command")}
            </TabsTrigger>
            <TabsTrigger value="prompt" className={SEGMENT_CLASS}>
              <Sparkles aria-hidden="true" className="h-3 w-3" />
              {t("install.prompt")}
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <button
        type="button"
        onClick={() => void copy()}
        aria-label={`${t("copy.command")}: ${content}`}
        title={copied ? t("copy.done") : t("copy.command")}
        className="flex w-full cursor-pointer items-start justify-between gap-3 rounded-md bg-ds-gray-100/80 px-4 py-3 text-left font-mono text-sm leading-6 text-foreground transition-colors hover:bg-ds-gray-200/80"
      >
        {/* Wraps whole tokens instead of scrolling: the full command is always
            on screen and readable, however narrow the column gets. */}
        <code className="block min-w-0 flex-1">
          <CommandLine command={content} dollar={mode === "command"} />
        </code>
        <span aria-hidden="true" className="mt-1 shrink-0 text-muted-foreground">
          {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
        </span>
      </button>

      {hasGuide && (
        <div className="mt-4 rounded-md border border-border bg-background/40">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-2.5">
            <h3 className="font-mono text-xs font-medium uppercase tracking-normal text-ds-gray-600">
              {t("install.guide")}
            </h3>
            {together.length > 0 && (
              <button
                type="button"
                onClick={() => void copyTogether()}
                className="flex items-center gap-1.5 font-mono text-xs text-ds-gray-600 transition-colors hover:text-foreground"
              >
                {guideCopied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                {guideCopied ? t("copy.done") : t("install.installTogether")}
              </button>
            )}
          </div>

          {guide.required.length > 0 && (
            <div className="px-4 py-3">
              <GuideList label={t("install.required")} deps={guide.required} />
            </div>
          )}

          {guide.optional.length > 0 && (
            <div className="border-t border-border px-4 py-3">
              <GuideList label={t("install.optional")} deps={guide.optional} muted />
            </div>
          )}

          {runtime.length > 0 && (
            <div className="border-t border-border px-4 py-3">
              <div className="mb-2 font-mono text-[11px] uppercase tracking-wider text-ds-gray-700">
                {t("install.runtime")}
              </div>
              <ul className="space-y-1.5">
                {runtime.map((line) => (
                  <li key={line} className="font-mono text-xs leading-5 text-ds-gray-600">
                    <span aria-hidden="true" className="mr-1.5 text-ds-gray-400">
                      ▸
                    </span>
                    {line}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

/** One labelled list of dependency skills, each a link to its detail page. */
function GuideList({
  label,
  deps,
  muted = false,
}: {
  label: string;
  deps: Skill[];
  muted?: boolean;
}) {
  if (deps.length === 0) return null;
  return (
    <div>
      <div
        className={`mb-2 font-mono text-[11px] uppercase tracking-wider ${
          muted ? "text-ds-gray-700" : "text-ds-gray-700"
        }`}
      >
        {label}
      </div>
      <ul className="divide-y divide-border">
        {deps.map((dep) => (
          <li key={dep.name}>
            <a
              href={`/${dep.name}/`}
              className="group flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 py-2"
            >
              <span className="flex min-w-0 items-center gap-2">
                <span className="font-mono text-sm text-foreground group-hover:underline group-hover:underline-offset-4">
                  {dep.name}
                </span>
                <span className="truncate font-mono text-xs text-ds-gray-700">{dep.category}</span>
              </span>
              <code className="shrink-0 break-all font-mono text-xs text-ds-gray-600">
                {installCommand(dep.name)}
              </code>
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
