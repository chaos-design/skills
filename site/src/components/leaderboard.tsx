"use client";

import { Search, Sparkles } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { LeaderboardTable } from "@/components/leaderboard-table";
import { useSkills } from "@/components/skills-provider";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useI18n } from "@/lib/i18n";
import { filterSkills, type SortKey, sortSkills } from "@/lib/skills";

// Only a 2px bottom underline marks the active tab — no side or top border.
const TAB_TRIGGER_CLASS =
  "rounded-none border-x-0 border-t-0 border-b-2 border-transparent bg-transparent px-0 pb-1.5 font-mono text-sm text-ds-gray-600 shadow-none transition-colors hover:text-foreground data-[state=active]:border-b-foreground data-[state=active]:bg-transparent data-[state=active]:text-foreground data-[state=active]:shadow-none";

export function Leaderboard() {
  const { t } = useI18n();
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

  const { data } = useSkills();
  const skills = data.skills;
  const rows = useMemo(() => sortSkills(filterSkills(skills, query), tab), [skills, query, tab]);

  return (
    <section id="leaderboard" className="scroll-mt-20 py-6 sm:py-8">
      <h2 className="text-sm font-medium uppercase tracking-normal text-foreground font-mono">
        {t("leaderboard.title")}
      </h2>

      <div className="w-full py-4">
        {/* Search + tabs stay pinned under the site header while the table
            scrolls. The bar spans the container edge-to-edge (negative margin
            mirrored by padding) so rows never peek out from behind it. */}
        <div className="sticky top-14 z-30 -mx-4 mb-4 bg-background/95 px-4 pb-4 pt-3 backdrop-blur supports-[backdrop-filter]:bg-background/80 sm:-mx-6 sm:px-6 lg:-mx-8 lg:px-8">
          <div className="relative mb-4">
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
              placeholder={t("leaderboard.search")}
              aria-label={t("leaderboard.search")}
              className="h-auto rounded-none border-0 border-b border-ds-gray-400 bg-transparent py-3 pl-9 pr-16 font-mono text-sm shadow-none placeholder:text-ds-gray-600 focus-visible:border-ds-gray-1000 focus-visible:ring-0 sm:border-ds-gray-1000"
            />
            <div className="pointer-events-none absolute inset-y-0 right-0 hidden items-center pr-3 sm:flex">
              <kbd className="rounded border border-border px-1.5 py-0.5 font-mono text-sm text-muted-foreground">
                /
              </kbd>
            </div>
          </div>

          <Tabs value={tab} onValueChange={(value) => setTab(value as SortKey)}>
            <TabsList className="h-auto gap-4 bg-transparent p-0">
              <TabsTrigger value="all" className={TAB_TRIGGER_CLASS}>
                {t("leaderboard.tabAll", { count: skills.length })}
              </TabsTrigger>
              <TabsTrigger value="trending" className={TAB_TRIGGER_CLASS}>
                {t("leaderboard.tabTrending")}
              </TabsTrigger>
              <TabsTrigger value="hot" className={TAB_TRIGGER_CLASS}>
                {t("leaderboard.tabHot")}
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        <LeaderboardTable rows={rows} />
      </div>
    </section>
  );
}
