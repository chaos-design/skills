import Link from "next/link";
import { Github, Menu } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { repoMeta } from "@/lib/skills";

const NAV_LINKS = [
  { label: "Leaderboard", href: "#leaderboard" },
  { label: "Try it", href: "#install" },
  { label: "Agents", href: "#agents" },
];

const NAV_LINK_CLASS =
  "font-mono text-sm text-ds-gray-600 transition-colors hover:text-foreground";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-3 px-4 lg:gap-6 lg:px-8">
        <Link href="/" className="flex min-w-0 items-center gap-2" aria-label={`${repoMeta.repo} home`}>
          <span
            aria-hidden="true"
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-foreground font-mono text-[13px] font-bold text-background"
          >
            S
          </span>
          <span className="font-mono text-sm font-medium tracking-tight text-foreground">skills</span>
          <span aria-hidden="true" className="hidden font-mono text-xs text-ds-gray-600 sm:inline">
            / chaos-design
          </span>
        </Link>

        <nav aria-label="Primary" className="hidden items-center gap-6 lg:flex">
          {NAV_LINKS.map((link) => (
            <a key={link.href} href={link.href} className={NAV_LINK_CLASS}>
              {link.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            asChild
            className="text-muted-foreground transition-colors hover:text-foreground"
          >
            <a href={repoMeta.repoUrl} target="_blank" rel="noreferrer" aria-label="GitHub repository">
              <Github className="h-4 w-4" />
            </a>
          </Button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="text-muted-foreground transition-colors hover:text-foreground lg:hidden"
                aria-label="Open menu"
              >
                <Menu className="h-5 w-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-44 font-mono">
              {NAV_LINKS.map((link) => (
                <DropdownMenuItem key={link.href} asChild>
                  <a href={link.href}>{link.label}</a>
                </DropdownMenuItem>
              ))}
              <DropdownMenuItem asChild>
                <a href={repoMeta.repoUrl} target="_blank" rel="noreferrer">
                  <Github className="h-4 w-4" />
                  GitHub
                </a>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}
