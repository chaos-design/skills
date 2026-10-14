"use client";

import { useState } from "react";
import { useIsomorphicLayoutEffect } from "@/lib/use-isomorphic-layout-effect";

export type ResolvedTheme = "light" | "dark";

/**
 * The theme <html> is actually painted with, read from the `.dark` class.
 *
 * The class is the single source of truth: the no-flash script sets it before
 * hydration and the appearance switcher keeps it in sync with the stored choice
 * *and* the OS, so observing it covers every path without a second copy of that
 * logic (or a theme provider) elsewhere.
 */
export function useResolvedTheme(): ResolvedTheme {
  const [theme, setTheme] = useState<ResolvedTheme>("light");

  useIsomorphicLayoutEffect(() => {
    const root = document.documentElement;
    const read = () => setTheme(root.classList.contains("dark") ? "dark" : "light");
    read();
    const observer = new MutationObserver(read);
    observer.observe(root, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
  }, []);

  return theme;
}
