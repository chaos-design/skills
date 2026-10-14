import { SearchX } from "lucide-react";
import { SkillRow } from "@/components/skill-row";
import type { Skill } from "@/lib/skills";

export function LeaderboardTable({ rows }: { rows: Skill[] }) {
  return (
    <div className="relative min-h-[400px]">
      <div className="hidden gap-4 border-b border-border py-3 text-sm font-medium uppercase text-ds-gray-600 lg:grid lg:grid-cols-16">
        <div className="col-span-1 font-mono">#</div>
        <div className="col-span-10 font-mono">Skill</div>
        <div className="col-span-2 text-right font-mono">8W Activity</div>
        <div className="col-span-1 text-right font-mono">Commits</div>
        <div className="col-span-2 text-right font-mono">Updated</div>
      </div>

      {rows.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-16 text-center">
          <SearchX className="h-6 w-6 text-ds-gray-600" />
          <p className="font-mono text-sm text-ds-gray-600">No skills match your search.</p>
        </div>
      ) : (
        rows.map((skill, index) => <SkillRow key={skill.name} skill={skill} rank={index + 1} />)
      )}
    </div>
  );
}
