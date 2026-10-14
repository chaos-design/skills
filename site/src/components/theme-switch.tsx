"use client";

import { Check, type LucideIcon, Monitor, Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useI18n } from "@/lib/i18n";
import { useIsomorphicLayoutEffect } from "@/lib/use-isomorphic-layout-effect";
import { cn } from "@/lib/utils";

type Theme = "light" | "dark" | "system";
const STORAGE_KEY = "theme";

function isSystemDark() {
  return typeof window !== "undefined" && window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function apply(theme: Theme) {
  const dark = theme === "dark" || (theme === "system" && isSystemDark());
  document.documentElement.classList.toggle("dark", dark);
}

function readStored(): Theme | null {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    if (value === "light" || value === "dark" || value === "system") return value;
  } catch {
    // storage unavailable — fall back to the system preference.
  }
  return null;
}

const OPTIONS: {
  value: Theme;
  labelKey: "theme.light" | "theme.dark" | "theme.system";
  Icon: LucideIcon;
}[] = [
  { value: "light", labelKey: "theme.light", Icon: Sun },
  { value: "dark", labelKey: "theme.dark", Icon: Moon },
  { value: "system", labelKey: "theme.system", Icon: Monitor },
];

/**
 * Light / dark / system appearance switch. Persists the choice to localStorage
 * and keeps the `.dark` class on <html> in sync (the no-flash script does the
 * first paint; this owns subsequent changes).
 */
export function ThemeSwitch({ className }: { className?: string }) {
  const { t } = useI18n();
  const [theme, setTheme] = useState<Theme>("system");
  const [mounted, setMounted] = useState(false);

  // Layout effect, not a passive one: the stored choice has to be reflected in
  // this control before the first paint, not one frame later.
  useIsomorphicLayoutEffect(() => {
    setTheme(readStored() ?? "system");
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    apply(theme);
    if (theme !== "system") return;
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => apply("system");
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, [theme, mounted]);

  const choose = (next: Theme) => {
    setTheme(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // ignore — the choice still applies for this visit.
    }
  };

  const Current: LucideIcon = OPTIONS.find((o) => o.value === theme)?.Icon ?? Monitor;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => {}}
          aria-label={t("theme.label")}
          title={t("theme.label")}
          className={cn("text-muted-foreground transition-colors hover:text-foreground", className)}
        >
          <Current className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-44 font-mono">
        {OPTIONS.map((option) => (
          <DropdownMenuItem key={option.value} onSelect={() => choose(option.value)}>
            <option.Icon className="h-4 w-4" />
            {t(option.labelKey)}
            {theme === option.value ? <Check className="ml-auto h-4 w-4" /> : null}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
