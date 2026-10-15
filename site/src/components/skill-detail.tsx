"use client";

import { ArrowLeft, Github } from "lucide-react";
import Link from "next/link";
import { ActivitySparkline } from "@/components/activity-sparkline";
import { Installation } from "@/components/installation";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { SkillReadme } from "@/components/skill-readme";
import { useSkills } from "@/components/skills-provider";
import { Badge } from "@/components/ui/badge";
import { useI18n } from "@/lib/i18n";
import {
  formatCompact,
  formatDate,
  getSkillByName,
  relatedSkills,
  repoMeta,
  type Skill,
} from "@/lib/skills";

const SECTION_TITLE = "text-sm font-medium uppercase tracking-normal text-foreground font-mono";

export function SkillDetail({ skillName }: { skillName: string }) {
  const { t } = useI18n();
  const { data } = useSkills();
  const skill = getSkillByName(data.skills, skillName) as Skill | undefined;

  // A skill that was in the build but not in the live dataset (removed, or
  // renamed between syncs) falls back to a minimal shell instead of crashing.
  if (!skill) {
    return (
      <div className="flex min-h-screen flex-col">
        <SiteHeader showNav={false} />
        <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-4 py-8 sm:px-6 lg:px-8">
          <main className="flex-1">
            <h1 className={`mb-3 ${SECTION_TITLE}`}>{skillName}</h1>
            <p className="font-mono text-sm text-ds-gray-600">{t("detail.gone")}</p>
            <Link
              href="/"
              className="mt-6 inline-flex items-center gap-2 font-mono text-sm text-ds-gray-600 transition-colors hover:text-foreground"
            >
              <ArrowLeft className="h-4 w-4" />
              {t("detail.back")}
            </Link>
          </main>
          <SiteFooter />
        </div>
      </div>
    );
  }

  const related = relatedSkills(data.skills, skill, 4);
  const stats: {
    key:
      | "detail.statRepository"
      | "detail.statVersion"
      | "detail.statFirstSeen"
      | "detail.statLastUpdated"
      | "detail.statTotalCommits"
      | "detail.statContributors";
    value: string;
    href?: string;
  }[] = [
    { key: "detail.statRepository", value: repoMeta.repo, href: skill.homepage },
    { key: "detail.statVersion", value: skill.version },
    { key: "detail.statFirstSeen", value: formatDate(skill.stats.firstCommit) },
    { key: "detail.statLastUpdated", value: formatDate(skill.stats.lastCommit) },
    { key: "detail.statTotalCommits", value: formatCompact(skill.stats.totalCommits) },
    { key: "detail.statContributors", value: String(skill.stats.contributors) },
  ];

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader showNav={false} />
      <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-4 py-8 sm:px-6 lg:px-8">
        <main className="grid grid-cols-1 gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,300px)] lg:gap-12">
          <div className="min-w-0">
            <nav aria-label="Breadcrumb" className="mb-6 font-mono text-xs text-ds-gray-700">
              <Link href="/" className="transition-colors hover:text-foreground">
                {repoMeta.repo}
              </Link>
              <span aria-hidden="true" className="mx-2">
                /
              </span>
              <span className="text-foreground">{skill.name}</span>
            </nav>

            <header className="pb-6">
              {/* Sticky title: the skill name stays on screen for the whole
                  scroll, so the stats and activity below never lose context. */}
              <div className="sticky top-14 z-30 border-b border-border bg-background/95 py-3 backdrop-blur supports-[backdrop-filter]:bg-background/80">
                <div className="flex flex-wrap items-center gap-3">
                  <Link
                    href="/"
                    aria-label={t("detail.back")}
                    className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-border bg-background text-ds-gray-600 transition-colors hover:text-foreground"
                  >
                    <ArrowLeft className="h-4 w-4" />
                  </Link>
                  <h1 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
                    {skill.name}
                  </h1>
                  <Badge
                    variant="secondary"
                    className="border-transparent bg-ds-gray-100 font-mono text-[11px] uppercase tracking-wider text-ds-gray-600"
                  >
                    {skill.category}
                  </Badge>
                </div>
              </div>

              <p className="mt-5 max-w-2xl text-[15px] leading-relaxed text-ds-gray-600">
                {skill.description}
              </p>
            </header>

            <Installation skillName={skill.name} />

            <SkillReadme skillName={skill.name} />

            <section className="grid grid-cols-2 gap-4 border-t border-border py-6 sm:grid-cols-3">
              {stats.map((item) => (
                <div key={item.key}>
                  <div className="font-mono text-xs uppercase tracking-wider text-ds-gray-700">
                    {t(item.key)}
                  </div>
                  {item.href ? (
                    <a
                      href={item.href}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-1 inline-block break-all font-mono text-sm text-foreground underline-offset-4 hover:underline"
                    >
                      {item.value}
                    </a>
                  ) : (
                    <div className="mt-1 break-all font-mono text-sm text-foreground">
                      {item.value}
                    </div>
                  )}
                </div>
              ))}
            </section>

            <section className="border-t border-border py-6">
              <h2 className={`mb-3 ${SECTION_TITLE}`}>{t("detail.activityTitle")}</h2>
              <div className="flex h-12 items-center text-ds-gray-600">
                <ActivitySparkline
                  values={skill.stats.weekly}
                  label={`Weekly commits, oldest first: ${skill.stats.weekly.join(", ")}`}
                />
              </div>
              <p className="mt-2 font-mono text-xs text-ds-gray-700">
                {t("detail.activityNote", {
                  a: skill.stats.commits8w,
                  b: skill.stats.commits7d,
                })}
              </p>
            </section>

            <section className="border-t border-border py-6">
              <a
                href={skill.homepage}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 font-mono text-sm text-ds-gray-600 transition-colors hover:text-foreground"
              >
                <Github className="h-4 w-4" />
                {t("detail.viewSource")}
              </a>
            </section>
          </div>

          {related.length > 0 && (
            // `self-start` + `sticky` pins the related list to the viewport for
            // the whole scroll, so it never drifts away from the main column.
            <aside className="min-w-0 lg:sticky lg:top-20 lg:self-start">
              <section className="border-t border-border py-6 lg:border-t-0 lg:py-0">
                <h2 className={`mb-3 ${SECTION_TITLE}`}>{t("detail.relatedSkills")}</h2>
                <ul className="divide-y divide-border">
                  {related.map((item) => (
                    <li key={item.name}>
                      <Link
                        href={`/${item.name}/`}
                        className="group flex flex-col gap-1 py-3 transition-colors hover:text-foreground"
                      >
                        <span className="truncate font-medium text-foreground group-hover:underline group-hover:underline-offset-4">
                          {item.name}
                        </span>
                        <span className="flex items-center justify-between gap-3">
                          <span className="truncate font-mono text-xs text-ds-gray-700">
                            {item.category}
                          </span>
                          <span className="shrink-0 font-mono text-xs text-ds-gray-700">
                            {t("related.commits", {
                              n: formatCompact(item.stats.totalCommits),
                            })}
                          </span>
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
              </section>
            </aside>
          )}
        </main>
        <SiteFooter />
      </div>
    </div>
  );
}
