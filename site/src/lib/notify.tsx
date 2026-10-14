"use client";

import { toast } from "sonner";

/** How long a copy confirmation stays on screen. */
const COPIED_MS = 2600;

/**
 * Confirms a copy with the shadcn/ui (Sonner) toast.
 *
 * The card carries the exact text that went to the clipboard, in mono so it
 * reads as a command. Repeated copies do not queue up in a corner: Sonner keeps
 * the newest in front and lets the previous ones pile up behind it as
 * overlapping cards, so a burst of clicks never floods the page.
 */
export function notifyCopied(command: string) {
  toast.success(command, {
    duration: COPIED_MS,
    className: "font-mono text-xs",
  });
}
