import { ArrowRight } from "lucide-react";

export function Hero() {
  return (
    <section className="hero" aria-labelledby="hero-title">
      <aside className="hero-side hero-side-left" aria-hidden="true">
        <div className="stacked-doodle">TEXT<span>→</span>VOICE<span>↓</span>VIBES<i /></div>
      </aside>

      <div className="hero-main">
        <div className="hero-type">
          <h1 id="hero-title">
            <span>MAKE IT</span>
            <em data-text="YAP.">YAP.</em>
          </h1>

          <div className="hero-marks" aria-hidden="true">
            <div className="sound-bursts"><i /><i /><i /></div>
            <div className="lime-sticker">SAY<br />MORE.<span /></div>
          </div>
        </div>

        <div className="hero-copy">
          <h2>Turn any text into a voice with personality.</h2>
          <p className="brand-slogan">Your words called. They wanna yap.</p>
          <div className="hero-actions">
            <a className="hero-button primary" href="#studio">
              Generate <ArrowRight aria-hidden="true" size={20} />
            </a>
            <a className="hero-button secondary" href="#voices">Explore Voices</a>
          </div>
        </div>
      </div>

      <aside className="hero-side hero-side-right" aria-hidden="true">
        <div className="circle-doodle">GOOD<br />IDEAS<br />SOUND<br />BETTER.<span /></div>
      </aside>

      <div className="mobile-doodle-strip" aria-hidden="true">
        <span>TEXT → VOICE → VIBES</span>
        <strong>SAY MORE.</strong>
        <span>GOOD IDEAS SOUND BETTER.</span>
      </div>
    </section>
  );
}
