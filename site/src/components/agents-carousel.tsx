import { Braces, Code, Gem, MousePointer2, Sparkles, Terminal, type LucideIcon } from "lucide-react";
import { agents } from "@/lib/skills";

/** Icon per agent id, falling back to a neutral bot glyph. */
const AGENT_ICONS: Record<string, LucideIcon> = {
  "claude-code": Terminal,
  "claude-ai": Sparkles,
  cursor: MousePointer2,
  "codex-cli": Code,
  "gemini-cli": Gem,
  opencode: Braces,
};

export function AgentsCarousel() {
  // The list is duplicated once; the marquee translates by -50%, so the loop
  // is seamless as long as the two halves are identical.
  const marquee = [...agents, ...agents];

  return (
    <section id="agents" className="scroll-mt-20 py-6">
      <h2 className="mb-3.5 text-sm font-medium uppercase tracking-normal text-foreground font-mono">
        Available for these agents
      </h2>
      <div className="relative overflow-hidden">
        <div className="flex w-max animate-carousel gap-2 sm:gap-3">
          {marquee.map((agent, position) => {
            const Icon = AGENT_ICONS[agent.id] ?? Braces;
            return (
              <div
                key={`${agent.id}-${position}`}
                aria-hidden={position >= agents.length ? "true" : undefined}
                className="inline-flex shrink-0 items-center gap-2 rounded-md border border-border bg-ds-gray-100/60 px-3 py-1.5 font-mono text-xs text-ds-gray-600"
              >
                <Icon className="h-3.5 w-3.5 shrink-0" />
                <span className="whitespace-nowrap">{agent.name}</span>
                <span className="text-ds-gray-700">· {agent.skills}</span>
              </div>
            );
          })}
        </div>
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-y-0 left-0 w-24 bg-gradient-to-r from-background to-transparent sm:w-32 lg:w-48"
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-y-0 right-0 w-24 bg-gradient-to-l from-background to-transparent sm:w-32 lg:w-48"
        />
      </div>
    </section>
  );
}
