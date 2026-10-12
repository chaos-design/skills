import { ExternalLink } from "lucide-react";
import { ActivitySparkline } from "@/components/activity-sparkline";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { formatCompact, formatDate, type Skill } from "@/lib/skills";

export function SkillRow({ skill, rank }: { skill: Skill; rank: number }) {
  const weekly = skill.stats.weekly;

  return (
    <a
      href={skill.homepage}
      target="_blank"
      rel="noreferrer"
      className="group grid grid-cols-[auto_1fr_auto] items-center gap-3 border-b border-border py-3 transition-colors hover:bg-ds-gray-100/30 lg:grid-cols-16 lg:gap-4"
    >
      <div className="min-w-7 lg:col-span-1">
        <span className="font-mono text-sm text-ds-gray-600 lg:text-base">{rank}</span>
      </div>

      <div className="flex min-w-0 flex-col gap-1 lg:col-span-10 lg:flex-row lg:items-center lg:gap-2">
        <h3 className="flex min-w-0 items-center gap-1.5 font-semibold text-foreground">
          <span className="truncate whitespace-nowrap">{skill.name}</span>
          <ExternalLink
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
      </div>

      {/* Mobile: the 8-week total stands in for the sparkline. */}
      <div className="font-mono text-xs text-ds-gray-600 lg:hidden">
        {skill.stats.commits8w}
        <span className="text-ds-gray-700">/8w</span>
      </div>

      <div className="hidden lg:col-span-2 lg:flex lg:items-center lg:justify-end">
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="group/sparkline relative flex h-8 w-28 items-center justify-center">
              <ActivitySparkline
                values={weekly}
                label={`Weekly commits, oldest first: ${weekly.join(", ")}`}
              />
            </div>
          </TooltipTrigger>
          <TooltipContent>
            {skill.stats.commits8w} commits in the last 8 weeks
          </TooltipContent>
        </Tooltip>
      </div>

      <div className="hidden font-mono text-sm text-ds-gray-600 lg:col-span-1 lg:block lg:text-right">
        {formatCompact(skill.stats.totalCommits)}
      </div>

      <div className="hidden font-mono text-xs text-ds-gray-600 lg:col-span-2 lg:block lg:text-right lg:text-sm">
        {formatDate(skill.stats.lastCommit)}
      </div>
    </a>
  );
}
