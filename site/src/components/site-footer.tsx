import { repoMeta } from "@/lib/skills";

export function SiteFooter() {
  return (
    <footer className="mt-10 border-t border-border py-8">
      <div className="flex flex-col gap-4 font-mono text-xs text-ds-gray-600 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <span className="font-medium text-foreground">{repoMeta.repo}</span>
          <span aria-hidden="true">·</span>
          <span>Apache-2.0</span>
        </div>
        <div className="flex flex-wrap items-center gap-4">
          <a
            href={repoMeta.repoUrl}
            target="_blank"
            rel="noreferrer"
            className="transition-colors hover:text-foreground"
          >
            GitHub
          </a>
          <a
            href={`${repoMeta.repoUrl}#readme`}
            target="_blank"
            rel="noreferrer"
            className="transition-colors hover:text-foreground"
          >
            README
          </a>
          <span className="text-ds-gray-700">Data synced {repoMeta.generatedAt} (UTC+8)</span>
        </div>
      </div>
      <p className="mt-4 font-mono text-xs text-ds-gray-700">
        Layout inspired by{" "}
        <a
          href="https://www.skills.sh/"
          target="_blank"
          rel="noreferrer"
          className="transition-colors hover:text-foreground"
        >
          skills.sh
        </a>{" "}
        · Built with Next.js, shadcn/ui and lucide
      </p>
    </footer>
  );
}
