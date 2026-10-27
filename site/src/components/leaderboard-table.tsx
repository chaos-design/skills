"use client";

import { ArrowDown, ArrowUp, SearchX } from "lucide-react";
import { useMemo, useState } from "react";
import { SkillRow } from "@/components/skill-row";
import { useI18n } from "@/lib/i18n";
import type { Skill } from "@/lib/skills";

type Column = "commits" | "updated";

const dateValue = (iso: string | null): number => (iso ? Date.parse(`${iso}T00:00:00Z`) : 0);

/**
 * Sort rows by a single column with an explicit direction, used when a column
 * header is clicked. Ties fall back to the other column, then name, so the
 * order is stable.
 */
function sortByColumn(rows: Skill[], column: Column, dir: "asc" | "desc"): Skill[] {
  const sign = dir === "asc" ? 1 : -1;
  const sorted = [...rows].sort((a, b) => {
    const primary =
      column === "commits"
        ? a.stats.totalCommits - b.stats.totalCommits
        : dateValue(a.stats.lastCommit) - dateValue(b.stats.lastCommit);
    const secondary =
      column === "commits"
        ? dateValue(a.stats.lastCommit) - dateValue(b.stats.lastCommit)
        : a.stats.totalCommits - b.stats.totalCommits;
    return primary * sign || secondary * sign || a.name.localeCompare(b.name);
  });
  return sorted;
}

export function LeaderboardTable({ rows }: { rows: Skill[] }) {
  const { t } = useI18n();
  const [colSort, setColSort] = useState<{ column: Column; dir: "asc" | "desc" } | null>(null);

  const visible = useMemo(
    () => (colSort ? sortByColumn(rows, colSort.column, colSort.dir) : rows),
    [rows, colSort],
  );

  const toggleColumn = (column: Column) =>
    setColSort((prev) =>
      prev && prev.column === column
        ? { column, dir: prev.dir === "desc" ? "asc" : "desc" }
        : { column, dir: "desc" },
    );

  const header = (column: Column, label: string) => {
    const active = colSort?.column === column;
    const Indicator = active ? (colSort.dir === "desc" ? ArrowDown : ArrowUp) : null;
    return (
      <button
        type="button"
        onClick={() => toggleColumn(column)}
        aria-label={`${label} ${active ? (colSort.dir === "desc" ? "descending" : "ascending") : "sort"}`}
        className="grid w-full grid-cols-2 items-center gap-1 font-mono hover:text-foreground"
      >
        <span>{label}</span>
        <span className="flex justify-end">
          {Indicator ? (
            <Indicator className="h-3 w-3" />
          ) : (
            <span className="text-ds-gray-400">⇅</span>
          )}
        </span>
      </button>
    );
  };

  return (
    <div className="relative min-h-[400px]">
      <div className="hidden gap-4 border-b border-border py-3 text-sm font-medium uppercase text-ds-gray-600 lg:grid lg:grid-cols-16">
        <div className="col-span-1 font-mono">{t("table.rank")}</div>
        <div className="col-span-10 font-mono">{t("table.skill")}</div>
        <div className="col-span-2 text-right font-mono">{t("table.activity")}</div>
        <div className="col-span-1 text-right">{header("commits", t("table.commits"))}</div>
        <div className="col-span-2 text-right">{header("updated", t("table.updated"))}</div>
      </div>

      {visible.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-16 text-center">
          <SearchX className="h-6 w-6 text-ds-gray-600" />
          <p className="font-mono text-sm text-ds-gray-600">{t("leaderboard.empty")}</p>
        </div>
      ) : (
        visible.map((skill, index) => <SkillRow key={skill.name} skill={skill} rank={index + 1} />)
      )}
    </div>
  );
}
