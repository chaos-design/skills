import { InstallCommand } from "@/components/install-command";
import { SKILLS_ASCII } from "@/components/brand-ascii";

const ASCII_PRE_CLASS =
  "select-none whitespace-pre font-mono text-[12px] leading-[125%] tracking-[-1px] lg:text-[15px]";

export function Hero() {
  return (
    <section className="mx-auto my-4 grid w-full max-w-6xl grid-cols-1 gap-10 py-6 sm:my-5 lg:my-7 lg:grid-cols-[auto_1fr] lg:gap-14 sm:py-8">
      <div className="flex items-start justify-center overflow-hidden lg:justify-start">
        <div className="relative max-w-[320px] overflow-hidden lg:max-w-[420px]">
          {/* Three stacked copies: one sizes the box, one is the offset shadow,
              one is the crisp foreground layer. */}
          <pre aria-hidden="true" className={`invisible ${ASCII_PRE_CLASS}`}>
            {SKILLS_ASCII}
          </pre>
          <pre aria-hidden="true" className={`absolute left-0 top-0 text-ds-gray-700 ${ASCII_PRE_CLASS}`}>
            {SKILLS_ASCII}
          </pre>
          <pre aria-hidden="true" className={`absolute left-0 top-0 text-foreground ${ASCII_PRE_CLASS}`}>
            {SKILLS_ASCII}
          </pre>
        </div>
      </div>

      <div className="flex flex-col gap-6 lg:gap-8">
        <p className="text-center font-mono text-[15px] font-medium uppercase tracking-tight text-primary lg:text-left lg:text-[19px]">
          The Open Agent Skills Ecosystem
        </p>
        <h1 className="text-balance text-center text-xl leading-tight tracking-tight text-ds-gray-600 sm:text-2xl lg:text-left lg:text-3xl">
          Production-oriented agent skills for content extraction, bilingual reading, slides, HTML
          briefs and geo flow maps — install any of them with a single command.
        </h1>
        <div id="install" className="scroll-mt-20">
          <h2 className="mb-3.5 text-left text-sm font-medium uppercase tracking-normal text-foreground font-mono sm:text-center lg:text-left">
            Try it now
          </h2>
          <div className="mx-auto w-full sm:max-w-[348px] lg:mx-0">
            <InstallCommand />
          </div>
        </div>
      </div>
    </section>
  );
}
