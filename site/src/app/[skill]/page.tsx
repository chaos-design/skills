import { notFound } from "next/navigation";
import { SkillDetail } from "@/components/skill-detail";
import { getSkillByName, repoMeta } from "@/lib/skills";
import { loadSkillsData } from "@/lib/skills-data";

export function generateStaticParams() {
  return loadSkillsData().skills.map((skill) => ({ skill: skill.name }));
}

export async function generateMetadata({ params }: { params: Promise<{ skill: string }> }) {
  const skill = getSkillByName(loadSkillsData().skills, (await params).skill);
  if (!skill) return {};
  return {
    title: `${skill.name} · ${repoMeta.repo}`,
    description: skill.description,
    alternates: { canonical: `/${skill.name}/` },
  };
}

export default async function SkillPage({ params }: { params: Promise<{ skill: string }> }) {
  const { skill: name } = await params;
  // The route has to exist in the build-time dataset; the page body renders
  // from the live dataset so the numbers are always the current ones.
  if (!getSkillByName(loadSkillsData().skills, name)) notFound();
  return <SkillDetail skillName={name} />;
}
