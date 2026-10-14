"use client";

import { createContext, type ReactNode, useCallback, useContext, useEffect, useState } from "react";
import type { SkillsData } from "@/lib/skills";

/**
 * The live dataset.
 *
 * `initialData` is the generated file as it stood at build time; it renders on
 * the first paint so nothing pops in or shifts. Immediately after mount — and
 * again whenever the tab comes back into view — the same file is re-fetched
 * with `cache: "no-store"`, so every visit (and every return to a dormant tab)
 * shows the latest numbers the deployment has, not the ones baked into the
 * bundle.
 */
export type SkillsState = {
  data: SkillsData;
  /** True while the first revalidation is in flight. */
  refreshing: boolean;
};

const SkillsContext = createContext<SkillsState | null>(null);

// Set at build time from BASE_PATH (see next.config.ts): GitHub Pages serves
// the site under /<repo>, so the data URL has to carry the same prefix.
const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
const DATA_URL = `${basePath}/data/skills.json`;

export function SkillsProvider({
  initialData,
  children,
}: {
  initialData: SkillsData;
  children: ReactNode;
}) {
  const [data, setData] = useState<SkillsData>(initialData);
  const [refreshing, setRefreshing] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const response = await fetch(DATA_URL, { cache: "no-store" });
      if (!response.ok) return;
      const next = (await response.json()) as SkillsData;
      if (!Array.isArray(next.skills) || next.skills.length === 0) return;
      // Swap only on a real change, so an unchanged payload never re-renders.
      setData((current) => (JSON.stringify(current) === JSON.stringify(next) ? current : next));
    } catch {
      // Offline or blocked: keep whatever is already on screen.
    } finally {
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    function onVisible() {
      if (document.visibilityState === "visible") void refresh();
    }
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("focus", onVisible);
    return () => {
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("focus", onVisible);
    };
  }, [refresh]);

  return <SkillsContext.Provider value={{ data, refreshing }}>{children}</SkillsContext.Provider>;
}

export function useSkills(): SkillsState {
  const ctx = useContext(SkillsContext);
  if (!ctx) throw new Error("useSkills must be used within a SkillsProvider");
  return ctx;
}
