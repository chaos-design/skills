"use client";

import { ChevronRight } from "lucide-react";
import Link from "next/link";
import { useCallback } from "react";
import { ActivitySparkline } from "@/components/activity-sparkline";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useI18n } from "@/lib/i18n";
import { notifyCopied } from "@/lib/notify";
import { formatCompact, formatDate, installCommand, type Skill } from "@/lib/skills";

/**
 * One leaderboard row.
 *
 * Clicking anywhere in the row copies that skill's install command and raises a
 * copy-confirmation toast — a separate hover button sat too far from the
 * pointer. The skill name stays a link to the detail page and sits above the
 * copy overlay.
 */
export function SkillRow({ skill, rank }: { skill: Skill; rank: number }) {
  const { t } = useI18n();
  const weekly = skill.stats.weekly;
  const command = installCommand(skill.name);

  const copy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(command);
    } catch {
      // Clipboard can be unavailable (insecure context, denied permission);
      // the row still opens the skill page via its name link.
      return;
    }
    notifyCopied(command);
  }, [command]);

  return (
    <div className="group relative grid grid-cols-[auto_1fr_auto] items-center gap-3 border-b border-border py-3 transition-colors hover:bg-ds-gray-100/30 lg:grid-cols-16 lg:gap-4">
      {/* A sibling overlay, not a wrapper: the row stays valid HTML with the
          skill name as a real link. It sits under the two things that own
          their own clicks (the name link and the sparkline tooltip). */}
      <button
        type="button"
        onClick={() => void copy()}
        aria-label={t("row.copyHint")}
        title={t("row.copyHint")}
        className="absolute inset-0 z-0 cursor-pointer focus-visible:outline-none focus-visible:border-b-2 focus-visible:border-ring"
      />

      <div className="min-w-7 lg:col-span-1">
        <span className="font-mono text-sm text-ds-gray-600 lg:text-base">{rank}</span>
      </div>

      <div className="flex min-w-0 flex-col gap-1 lg:col-span-10 lg:flex-row lg:items-center lg:gap-2">
        <h3 className="relative z-10 flex min-w-0 items-center gap-1.5 font-semibold text-foreground">
          {/* The one escape hatch from "click anywhere copies". */}
          <Link href={`/${skill.name}/`} className="underline-offset-4 hover:underline break-words">
            {skill.name}
          </Link>
          <ChevronRight
            aria-hidden="true"
            className="h-3.5 w-3.5 shrink-0 text-ds-gray-600 opacity-0 transition-opacity group-hover:opacity-100"
          />
        </h3>
        <p className="truncate font-mono text-xs text-ds-gray-600 lg:text-sm">{skill.repo}</p>
        <Badge
          variant="secondary"
          className="w-fit border-transparent font-mono text-[10px] uppercase tracking-wider text-ds-gray-600"
        >
          {skill.category}
        </Badge>
        {skill.tags.length > 0 && (
          <span className="flex flex-wrap items-center gap-1">
            {skill.tags.map((tag) => (
              <span
                key={tag}
                className="rounded-full border border-border bg-ds-gray-100/60 px-1.5 py-0.5 font-mono text-[10px] text-ds-gray-600"
              >
                {tag}
              </span>
            ))}
          </span>
        )}
      </div>

      {/* Mobile: the 8-week total stands in for the sparkline. */}
      <div className="font-mono text-xs text-ds-gray-600 lg:hidden">
        {skill.stats.commits8w}
        <span className="text-ds-gray-700">{t("table.mobileSuffix")}</span>
      </div>

      <div className="relative z-10 hidden lg:col-span-2 lg:flex lg:items-center lg:justify-end">
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="group/sparkline relative flex h-8 w-28 items-center justify-center">
              <ActivitySparkline
                values={weekly}
                label={t("tooltip.commits8w", { n: skill.stats.commits8w })}
              />
            </div>
          </TooltipTrigger>
          <TooltipContent>{t("tooltip.commits8w", { n: skill.stats.commits8w })}</TooltipContent>
        </Tooltip>
      </div>

      <div className="hidden font-mono text-sm text-ds-gray-600 lg:col-span-1 lg:block lg:text-right">
        {formatCompact(skill.stats.totalCommits)}
      </div>

      <div className="hidden font-mono text-xs text-ds-gray-600 lg:col-span-2 lg:block lg:text-right lg:text-sm">
        {formatDate(skill.stats.lastCommit)}
      </div>
    </div>
  );
}
