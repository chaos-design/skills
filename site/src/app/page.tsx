import { Hero } from "@/components/hero";
import { Leaderboard } from "@/components/leaderboard";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-4 sm:px-6 lg:px-8">
        <main className="flex-1">
          <Hero />
          <Leaderboard />
        </main>
        <SiteFooter />
      </div>
    </div>
  );
}
