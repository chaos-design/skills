"use client";

import { useSkills } from "@/components/skills-provider";
import { useI18n } from "@/lib/i18n";
import { repoMeta } from "@/lib/skills";

export function SiteFooter() {
  const { t } = useI18n();
  // Comes from the live dataset, so it shows when the data was last synced —
  // not when the HTML was built.
  const { data } = useSkills();
  return (
    <footer className="mt-10 border-t border-border py-8">
      <div className="flex flex-col gap-4 font-mono text-xs text-ds-gray-600 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <span className="font-medium text-foreground">{repoMeta.repo}</span>
          <span aria-hidden="true">·</span>
          <span>{t("footer.apache")}</span>
        </div>
        <div className="flex flex-wrap items-center gap-4">
          <a
            href={repoMeta.repoUrl}
            target="_blank"
            rel="noreferrer"
            className="transition-colors hover:text-foreground"
          >
            {t("footer.github")}
          </a>
          <a
            href={`${repoMeta.repoUrl}#readme`}
            target="_blank"
            rel="noreferrer"
            className="transition-colors hover:text-foreground"
          >
            {t("footer.readme")}
          </a>
          <span className="text-ds-gray-700">{t("footer.synced", { date: data.generatedAt })}</span>
        </div>
      </div>
    </footer>
  );
}
