"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Check, Copy } from "lucide-react";
import { repoMeta, skills } from "@/lib/skills";

const TYPE_MS = 90;
const DELETE_MS = 45;
const HOLD_MS = 1800;
const COPIED_MS = 2000;

function prefersReducedMotion() {
  return (
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}

/**
 * The install command with a typewriter that cycles through every skill name,
 * mirroring the animated command on the reference directory. The copy button
 * always copies the complete command for the skill currently displayed.
 */
export function InstallCommand() {
  const [index, setIndex] = useState(0);
  const [typed, setTyped] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [copied, setCopied] = useState(false);
  const copiedTimer = useRef<ReturnType<typeof setTimeout>>(null);

  const target = skills[index].name;
  const command = `${repoMeta.installPrefix} ${target}`;

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
      setIndex((current) => (current + 1) % skills.length);
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
  }, [typed, deleting, index, target]);

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
    <div
      role="button"
      tabIndex={0}
      onClick={copy}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          void copy();
        }
      }}
      aria-label={`Copy install command: ${command}`}
      className="flex w-full cursor-pointer items-center justify-between gap-4 rounded-md bg-ds-gray-100/80 px-4 py-3 font-mono text-sm text-foreground transition-colors hover:bg-ds-gray-200/80"
    >
      <code className="flex min-w-0 items-center truncate">
        <span className="text-muted-foreground">$</span>
        <span className="ml-[1ch]">npx skills add</span>
        <span className="ml-[1ch] truncate text-muted-foreground">{repoMeta.repoUrl}</span>
        <span className="ml-[1ch]">--skill</span>
        <span className="ml-[1ch] text-foreground">{typed}</span>
        <span aria-hidden="true" className="animate-caret ml-[1px] inline-block w-[0.6em] bg-foreground">
          &nbsp;
        </span>
      </code>
      <span aria-hidden="true" className="shrink-0 text-muted-foreground">
        {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
      </span>
    </div>
  );
}
