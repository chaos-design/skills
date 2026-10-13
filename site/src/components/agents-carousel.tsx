"use client";

import { AgentLogo } from "@/components/agent-logos";
import { useSkills } from "@/components/skills-provider";
import { useI18n } from "@/lib/i18n";

export function AgentsCarousel() {
  const { t } = useI18n();
  const { data } = useSkills();
  const agents = data.agents;
  // The list is duplicated once; the marquee translates by -50%, so the loop
  // is seamless as long as the two halves are identical. Each item carries a
  // stable key (the two halves share agent ids, so the array index can't be a
  // key) and the duplicate half is marked hidden so it is announced to no one.
  const marquee = [
    ...agents.map((agent) => ({ agent, key: `${agent.id}-1`, hidden: false })),
    ...agents.map((agent) => ({ agent, key: `${agent.id}-2`, hidden: true })),
  ];

  return (
    <section id="agents" className="scroll-mt-20 py-6">
      <h2 className="mb-3.5 text-sm font-medium uppercase tracking-normal text-foreground font-mono">
        {t("agents.title")}
      </h2>
      <div className="relative overflow-hidden">
        <div className="flex w-max animate-carousel gap-2 sm:gap-3">
          {marquee.map(({ agent, key, hidden }) => (
            <div
              key={key}
              aria-hidden={hidden ? "true" : undefined}
              className="inline-flex shrink-0 items-center gap-2 rounded-md border border-border bg-ds-gray-100/60 px-3 py-1.5 font-mono text-xs text-ds-gray-600"
            >
              <AgentLogo id={agent.id} className="h-4 w-4 shrink-0" />
              <span className="whitespace-nowrap">{agent.name}</span>
              <span className="text-ds-gray-700">· {agent.skills}</span>
            </div>
          ))}
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
