import { ContentSections } from "@/components/yaplab/content-sections";
import { Hero } from "@/components/yaplab/hero";
import { PlaneCursor } from "@/components/yaplab/plane-cursor";
import { ScrollReveal } from "@/components/yaplab/scroll-reveal";
import { SiteFooter } from "@/components/yaplab/site-footer";
import { SiteHeader } from "@/components/yaplab/site-header";
import { Studio } from "@/components/yaplab/studio";

export default function Home() {
  return (
    <main id="home" className="app-shell">
      <PlaneCursor />
      <ScrollReveal />
      <SiteHeader />
      <Hero />
      <Studio />
      <ContentSections />
      <SiteFooter />
    </main>
  );
}
