"use client";

import {
  CircleCheckIcon,
  InfoIcon,
  Loader2Icon,
  OctagonXIcon,
  TriangleAlertIcon,
} from "lucide-react";
import type { CSSProperties } from "react";
import { Toaster as Sonner, type ToasterProps } from "sonner";
import { useResolvedTheme } from "@/lib/use-resolved-theme";

/**
 * shadcn/ui's Sonner toaster (new-york style).
 *
 * Two adaptations to this codebase: the theme is read from the `.dark` class
 * instead of next-themes (the site has its own appearance switcher), and the
 * palette is mapped onto the site tokens so both canvases stay on brand.
 *
 * The width is ours as well: every toast here carries a full install command,
 * so a fixed card at most `26rem` wide — shrinking to `90vw` on phones — wraps
 * the command instead of stretching off screen.
 */
const Toaster = ({ ...props }: ToasterProps) => {
  const theme = useResolvedTheme();

  return (
    <Sonner
      theme={theme}
      className="toaster group"
      icons={{
        success: <CircleCheckIcon className="size-4" />,
        info: <InfoIcon className="size-4" />,
        warning: <TriangleAlertIcon className="size-4" />,
        error: <OctagonXIcon className="size-4" />,
        loading: <Loader2Icon className="size-4 animate-spin" />,
      }}
      style={
        {
          "--width": "min(90vw, 26rem)",
          "--normal-bg": "var(--popover)",
          "--normal-text": "var(--popover-foreground)",
          "--normal-border": "var(--border)",
          "--border-radius": "var(--radius)",
        } as CSSProperties
      }
      {...props}
    />
  );
};

export { Toaster };
