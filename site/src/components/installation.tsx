"use client";

import { Check, Copy, Sparkles } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { CommandLine } from "@/components/command-line";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useI18n } from "@/lib/i18n";
import { notifyCopied } from "@/lib/notify";
import { agentPrompt, installCommand } from "@/lib/skills";

const COPIED_MS = 2000;

/** Segment of the Command / Prompt switch. */
const SEGMENT_CLASS =
  "h-7 gap-1 rounded-[5px] border border-transparent px-2.5 font-mono text-xs text-ds-gray-600 shadow-none transition-colors hover:text-foreground data-[state=active]:border-border data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-none";

type Mode = "command" | "prompt";

/**
 * The installation block: a section label, a Command / Prompt switch, and a
 * copyable block whose text is always fully on screen — the command wraps at
 * whole tokens, so nothing is truncated and the height only changes with the
 * tab's own content.
 */
export function Installation({ skillName }: { skillName: string }) {
  const { t } = useI18n();
  const [mode, setMode] = useState<Mode>("command");
  const [copied, setCopied] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, []);

  const content = mode === "command" ? installCommand(skillName) : agentPrompt(skillName);

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
    </section>
  );
}
