"use client";

import { Check, Copy } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CommandLine } from "@/components/command-line";
import { useSkills } from "@/components/skills-provider";
import { repoMeta } from "@/lib/skills";

const TYPE_MS = 90;
const DELETE_MS = 45;
const HOLD_MS = 1800;
const COPIED_MS = 2000;

function prefersReducedMotion() {
  return (
    typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}

/**
 * The install command with a typewriter that cycles through every skill name,
 * mirroring the animated command on the reference directory. The copy button
 * always copies the complete command for the skill currently displayed.
 *
 * The box is sized by an invisible copy of the longest command the typewriter
 * can reach, so typing (and the wrap it triggers) never reflows the page.
 */
export function InstallCommand() {
  const { data } = useSkills();
  const names = data.skills;
  const [index, setIndex] = useState(0);
  const [typed, setTyped] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [copied, setCopied] = useState(false);
  const copiedTimer = useRef<ReturnType<typeof setTimeout>>(null);

  // Clamp the cursor: a refresh can ship a shorter skill list than the build.
  const target = names[Math.min(index, names.length - 1)].name;
  const command = `${repoMeta.installPrefix} ${target}`;

  // The widest command the typewriter will ever show — reserved up front.
  const longest = useMemo(
    () =>
      `${repoMeta.installPrefix} ${names.reduce((a, b) => (b.name.length > a.name.length ? b : a), names[0]).name}`,
    [names],
  );

  useEffect(() => {
    if (prefersReducedMotion()) {
      setTyped(target);
      return;
    }
    if (!deleting && typed === target) {
      const hold = setTimeout(() => setDeleting(true), HOLD_MS);
      return () => clearTimeout(hold);
    }
    if (deleting && typed === "") {
      setDeleting(false);
      setIndex((current) => (current + 1) % names.length);
      return;
    }
    const step = setTimeout(
      () =>
        setTyped((current) =>
          deleting ? target.slice(0, current.length - 1) : target.slice(0, current.length + 1),
        ),
      deleting ? DELETE_MS : TYPE_MS,
    );
    return () => clearTimeout(step);
  }, [typed, deleting, target, names.length]);

  useEffect(() => {
    return () => {
      if (copiedTimer.current) clearTimeout(copiedTimer.current);
    };
  }, []);

  const copy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(command);
    } catch {
      // Clipboard can be unavailable (insecure context, denied permission);
      // the command stays selectable on screen either way.
      return;
    }
    setCopied(true);
    if (copiedTimer.current) clearTimeout(copiedTimer.current);
    copiedTimer.current = setTimeout(() => setCopied(false), COPIED_MS);
  }, [command]);

  return (
    <button
      type="button"
      onClick={copy}
      aria-label={`Copy install command: ${command}`}
      className="flex w-full cursor-pointer items-start justify-between gap-3 rounded-md bg-ds-gray-100/80 px-4 py-3 text-left font-mono text-sm leading-6 text-foreground transition-colors hover:bg-ds-gray-200/80"
    >
      <span className="relative block min-w-0 flex-1">
        {/* Invisible sizer: reserves the tallest layout the typewriter can
            reach, so the hero never grows or shrinks while it types. */}
        <span aria-hidden="true" className="invisible block">
          <CommandLine command={longest} caret />
        </span>
        <code className="absolute inset-0 block">
          <CommandLine command={command} caret />
        </code>
      </span>
      <span aria-hidden="true" className="mt-1 shrink-0 self-start text-muted-foreground">
        {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
      </span>
    </button>
  );
}
