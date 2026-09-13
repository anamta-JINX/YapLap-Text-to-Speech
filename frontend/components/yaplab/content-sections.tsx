import { ArrowRight, AudioLines, Download, Languages, SlidersHorizontal } from "lucide-react";

import { voices } from "@/data/studio";

const features = [
  { icon: AudioLines, title: "Four human voices", copy: "Choose two expressive women or two distinct men." },
  { icon: Languages, title: "Accent control", copy: "Choose General, American, British, Australian or Indian English." },
  { icon: SlidersHorizontal, title: "Emotion and tuning", copy: "Set the mood, then fine-tune speed and pitch." },
  { icon: Download, title: "Ready to keep", copy: "Listen instantly and download generated audio as a WAV file." },
];

export function ContentSections() {
  return (
    <>
      <section id="features" className="content-section features-section">
        <div className="section-heading" data-reveal>
          <div><h2>YOUR WORDS.<br /><em>MORE RANGE.</em></h2></div>
        </div>
        <div className="feature-grid">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <article key={feature.title} data-reveal>
                <span><Icon aria-hidden="true" size={25} /></span>
                <h3>{feature.title}</h3>
                <p>{feature.copy}</p>
              </article>
            );
          })}
        </div>
      </section>

      <section id="voices" className="content-section voices-section">
        <div className="section-heading compact-heading" data-reveal>
          <div><h2>FOUR WAYS<br /><em>TO YAP.</em></h2></div>
          <a className="section-cta" href="#studio">TRY A VOICE <ArrowRight aria-hidden="true" size={18} /></a>
        </div>
        <div className="voice-showcase">
          {voices.map((item, index) => (
            <article key={item.id} data-reveal>
              <span className="voice-number">0{index + 1}</span>
              <div className="showcase-avatar">{item.initials}</div>
              <h3>{item.name}</h3>
              <p>{item.note}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="note-ribbon" aria-hidden="true" data-reveal>
        <div className="ribbon-note lime-note">ALL<br />VOICES<br />WELCOME.<span /></div>
        <p>Your words called.<br />They wanna yap.</p>
        <div className="ribbon-note coral-note">YAP<br />LAB<br />©<span /></div>
      </section>

      <section id="about" className="content-section how-section">
        <div className="section-heading" data-reveal>
          <div><h2>THREE STEPS.<br /><em>THAT&apos;S IT.</em></h2></div>
        </div>
        <div className="how-grid">
          <article data-reveal><span>01</span><h3>Write it</h3><p>Paste up to 5,000 characters or start from an example.</p></article>
          <article data-reveal><span>02</span><h3>Direct it</h3><p>Choose a voice, accent, emotion, speed and pitch.</p></article>
          <article data-reveal><span>03</span><h3>Hear it</h3><p>Generate, preview and download the result.</p></article>
        </div>
      </section>
    </>
  );
}
