"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useI18n } from "@/lib/i18n";
import { type DocLang, readmePath, readmeSourceUrl } from "@/lib/skills";

// Set at build time from BASE_PATH (see next.config.ts): GitHub Pages serves
// the site under /<repo>, so the doc URLs carry the same prefix.
const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

type Docs = Record<DocLang, string | null>;

/**
 * The documentation block: renders the skill's published README in the site
 * language and follows the header's 中/EN toggle.
 *
 * Both language files load on mount, so switching language re-renders
 * instantly instead of showing a second spinner. A language whose README was
 * never published falls back to a note with the GitHub source link.
 */
export function SkillReadme({ skillName }: { skillName: string }) {
  const { lang, t } = useI18n();
  const [docs, setDocs] = useState<Docs>({ en: null, zh: null });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const load = async (language: DocLang): Promise<string | null> => {
      try {
        const response = await fetch(`${basePath}/${readmePath(skillName, language)}`);
        return response.ok ? response.text() : null;
      } catch {
        // Offline or blocked: the missing-docs note still offers the GitHub link.
        return null;
      }
    };
    void Promise.all([load("en"), load("zh")]).then(([en, zh]) => {
      if (cancelled) return;
      setDocs({ en, zh });
      setLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [skillName]);

  const text = docs[lang];

  return (
    <section id="documentation" className="border-t border-border py-6">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-mono text-sm font-medium uppercase tracking-normal text-foreground">
          {t("detail.docsTitle")}
        </h2>
      </div>

      {loading ? (
        <p role="status" aria-live="polite" className="font-mono text-sm text-ds-gray-600">
          {t("detail.docsLoading")}
        </p>
      ) : text ? (
        <div className="doc-markdown">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              a: ({ node: _node, ...props }) => <a {...props} target="_blank" rel="noreferrer" />,
              // Plain <img>: the doc's images are remote (raw.githubusercontent)
              // and the export ships unoptimized, so next/image buys nothing.
              img: ({ node: _node, ...props }) => (
                // biome-ignore lint/performance/noImgElement: remote doc images, unoptimized static export
                <img {...props} alt={props.alt ?? ""} loading="lazy" />
              ),
            }}
          >
            {text}
          </ReactMarkdown>
        </div>
      ) : (
        <div className="space-y-2">
          <p className="font-mono text-sm text-ds-gray-600">{t("detail.docsMissing")}</p>
          <a
            href={readmeSourceUrl(skillName, lang)}
            target="_blank"
            rel="noreferrer"
            className="inline-block font-mono text-sm text-foreground underline-offset-4 hover:underline"
          >
            {t("detail.docsViewGitHub")}
          </a>
        </div>
      )}
    </section>
  );
}
