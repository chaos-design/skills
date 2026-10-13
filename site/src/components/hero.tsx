"use client";

import { AgentsCarousel } from "@/components/agents-carousel";
import { SKILLS_ASCII } from "@/components/brand-ascii";
import { InstallCommand } from "@/components/install-command";
import { useI18n } from "@/lib/i18n";

const ASCII_PRE_CLASS =
  "select-none whitespace-pre font-mono text-[12px] leading-[125%] tracking-[-1px] lg:text-[15px]";

const BLOCK_TITLE =
  "mb-3.5 text-sm font-medium uppercase tracking-normal text-foreground font-mono";

export function Hero() {
  const { t } = useI18n();
  return (
    <>
      <section className="mx-auto my-4 grid w-full max-w-6xl grid-cols-1 gap-10 py-6 sm:my-5 lg:my-7 lg:grid-cols-[auto_1fr] lg:gap-14 sm:py-8">
        <div className="flex items-start justify-center overflow-hidden lg:justify-start">
          <div className="relative max-w-[320px] overflow-hidden lg:max-w-[420px]">
            {/* Three stacked copies: one sizes the box, one is the offset shadow,
                one is the crisp foreground layer. */}
            <pre aria-hidden="true" className={`invisible ${ASCII_PRE_CLASS}`}>
              {SKILLS_ASCII}
            </pre>
            <pre
              aria-hidden="true"
              className={`absolute left-0 top-0 text-ds-gray-700 ${ASCII_PRE_CLASS}`}
            >
              {SKILLS_ASCII}
            </pre>
            <pre
              aria-hidden="true"
              className={`absolute left-0 top-0 text-foreground ${ASCII_PRE_CLASS}`}
            >
              {SKILLS_ASCII}
            </pre>
          </div>
        </div>

        <div className="flex flex-col gap-6 lg:gap-8">
          <p className="text-center font-mono text-[15px] font-medium uppercase tracking-tight text-primary lg:text-left lg:text-[19px]">
            {t("hero.tagline")}
          </p>
          <h1 className="text-balance text-center text-xl leading-tight tracking-tight text-ds-gray-600 sm:text-2xl lg:text-left lg:text-3xl">
            {t("hero.subtitle")}
          </h1>
        </div>
      </section>

      {/* Split row: install on the left, the agent strip on the right. */}
      <section className="grid w-full grid-cols-1 gap-8 py-6 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)] lg:gap-12">
        <div id="install" className="scroll-mt-20 min-w-0">
          <h2 className={`${BLOCK_TITLE} text-left sm:text-center lg:text-left`}>
            {t("hero.tryNow")}
          </h2>
          <div className="mx-auto w-full sm:max-w-[560px] lg:mx-0 lg:max-w-none">
            <InstallCommand />
          </div>
        </div>
        <div className="min-w-0">
          <AgentsCarousel />
        </div>
      </section>
    </>
  );
}
