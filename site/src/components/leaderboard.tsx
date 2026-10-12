"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Search, Sparkles } from "lucide-react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { LeaderboardTable } from "@/components/leaderboard-table";
import { filterSkills, skills, sortSkills, type SortKey } from "@/lib/skills";

const TAB_TRIGGER_CLASS =
  "rounded-none border-b-2 border-transparent bg-transparent px-0 pb-1 font-mono text-sm text-ds-gray-600 shadow-none transition-colors hover:text-foreground data-[state=active]:border-foreground data-[state=active]:bg-transparent data-[state=active]:text-foreground data-[state=active]:shadow-none";

export function Leaderboard() {
  const [query, setQuery] = useState("");
  const [tab, setTab] = useState<SortKey>("all");
  const [focused, setFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // "/" focuses the search field from anywhere, like the reference directory.
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      const target = event.target as HTMLElement | null;
      const typing =
        target instanceof HTMLInputElement ||
        target instanceof HTMLTextAreaElement ||
        target?.isContentEditable === true;
      if (event.key === "/" && !typing) {
        event.preventDefault();
        inputRef.current?.focus();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const rows = useMemo(() => sortSkills(filterSkills(skills, query), tab), [query, tab]);

  return (
    <section id="leaderboard" className="scroll-mt-20 py-6 sm:py-8">
      <h2 className="text-sm font-medium uppercase tracking-normal text-foreground font-mono">
        Skills Leaderboard
      </h2>

      <div className="w-full py-4">
        <div className="relative mb-6">
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
            <Search
              className={`h-4 w-4 text-muted-foreground transition-opacity ${focused ? "opacity-0" : "opacity-100"}`}
            />
            <Sparkles
              className={`absolute h-4 w-4 text-muted-foreground transition-opacity ${focused ? "opacity-100" : "opacity-0"}`}
            />
          </div>
          <Input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            placeholder="Search skills..."
            aria-label="Search skills"
            className="h-auto rounded-none border-0 border-b border-ds-gray-400 bg-transparent py-3 pl-9 pr-16 font-mono text-sm shadow-none placeholder:text-ds-gray-600 focus-visible:border-ds-gray-1000 focus-visible:ring-0 sm:border-ds-gray-1000"
          />
          <div className="pointer-events-none absolute inset-y-0 right-0 hidden items-center pr-3 sm:flex">
            <kbd className="rounded border border-border px-1.5 py-0.5 font-mono text-sm text-muted-foreground">
              /
            </kbd>
          </div>
        </div>

        <Tabs
          value={tab}
          onValueChange={(value) => setTab(value as SortKey)}
          className="mb-4"
        >
          <TabsList className="h-auto gap-4 bg-transparent p-0">
            <TabsTrigger value="all" className={TAB_TRIGGER_CLASS}>
              All Time ({skills.length})
            </TabsTrigger>
            <TabsTrigger value="trending" className={TAB_TRIGGER_CLASS}>
              Trending (7d)
            </TabsTrigger>
            <TabsTrigger value="hot" className={TAB_TRIGGER_CLASS}>
              Hot
            </TabsTrigger>
          </TabsList>
        </Tabs>

        <LeaderboardTable rows={rows} />
      </div>
    </section>
  );
}
