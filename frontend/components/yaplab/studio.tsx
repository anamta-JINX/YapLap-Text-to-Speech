"use client";

import { useEffect, useRef, useState } from "react";
import {
  ArrowDownToLine,
  ArrowRight,
  Pause,
  Play,
  RotateCcw,
  Sparkles,
  WandSparkles,
} from "lucide-react";

import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import {
  accents,
  examples,
  MAX_CHARS,
  tones,
  voices,
  wave,
  type AccentId,
  type ToneId,
  type VoiceId,
} from "@/data/studio";

type StudioStatus = "idle" | "generating" | "ready" | "playing" | "error";
const ENGLISH_LOCALE = /^en[-_]/i;
const VOICE_INDEX: Record<VoiceId, number> = {
  zubeda: 0,
  khalda: 1,
  samundar: 2,
  jameed: 3,
};
const FEMALE_HINTS = ["female", "aria", "jenny", "zira", "sonia", "libby", "natasha", "neerja"];
const MALE_HINTS = ["male", "guy", "davis", "david", "ryan", "george", "william", "prabhat"];

function browserVoiceFor(voiceId: VoiceId, accentId: AccentId) {
  const available = window.speechSynthesis?.getVoices() ?? [];
  if (!available.length) return undefined;

  const accent = accents.find((item) => item.id === accentId) ?? accents[0];
  const exact = available.filter((item) => item.lang.toLowerCase() === accent.locale.toLowerCase());
  const english = available.filter((item) => ENGLISH_LOCALE.test(item.lang));
  const pool = exact.length ? exact : english.length ? english : available;
  const genderHints = voiceId === "zubeda" || voiceId === "khalda" ? FEMALE_HINTS : MALE_HINTS;
  const matchingGender = pool.filter((item) =>
    genderHints.some((hint) => item.name.toLowerCase().includes(hint)),
  );
  const preferredPool = matchingGender.length ? matchingGender : pool;
  return preferredPool[VOICE_INDEX[voiceId] % preferredPool.length];
}

export function Studio() {
  const [text, setText] = useState(examples[0].text);
  const [voice, setVoice] = useState<VoiceId>("zubeda");
  const [tone, setTone] = useState<ToneId>("happy");
  const [accent, setAccent] = useState<AccentId>("american");
  const [speed, setSpeed] = useState([1]);
  const [pitch, setPitch] = useState([0]);
  const [status, setStatus] = useState<StudioStatus>("idle");
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [audioFormat, setAudioFormat] = useState<"mp3" | "wav">("mp3");
  const [engine, setEngine] = useState("YapLab voice");
  const [message, setMessage] = useState("Ready when you are.");
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const activeVoice = voices.find((item) => item.id === voice) ?? voices[0];
  const activeAccent = accents.find((item) => item.id === accent) ?? accents[0];
  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  const seconds = Math.max(1, Math.round(wordCount / (2.5 * speed[0])));

  useEffect(() => {
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl);
      window.speechSynthesis?.cancel();
    };
  }, [audioUrl]);

  const clear = () => {
    setText("");
    setStatus("idle");
    setMessage("Blank canvas. Go yap.");
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioUrl(null);
  };

  const speakInBrowser = () => {
    if (!("speechSynthesis" in window)) {
      setStatus("error");
      setMessage("Speech playback is not supported in this browser.");
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    const tuning: Record<ToneId, { rate: number; pitch: number; volume: number }> = {
      neutral: { rate: 1, pitch: 1, volume: 0.94 },
      happy: { rate: 1.12, pitch: 1.28, volume: 1 },
      sad: { rate: 0.76, pitch: 0.7, volume: 0.68 },
      angry: { rate: 1.2, pitch: 0.8, volume: 1 },
    };
    utterance.rate = Math.min(2, Math.max(0.5, speed[0] * tuning[tone].rate));
    utterance.pitch = Math.min(2, Math.max(0, tuning[tone].pitch + pitch[0] / 12));
    utterance.volume = tuning[tone].volume;
    utterance.voice = browserVoiceFor(voice, accent) ?? null;
    utterance.onstart = () => setStatus("playing");
    utterance.onend = () => setStatus("ready");
    utterance.onerror = () => {
      setStatus("error");
      setMessage("Your browser blocked playback. Allow audio and try again.");
    };
    window.speechSynthesis.speak(utterance);
    setEngine("Browser voice");
    setMessage(`Playing with the ${activeAccent.label} accent.`);
    setStatus("playing");
  };

  const generate = async () => {
    if (!text.trim()) {
      setStatus("error");
      setMessage("Write something first, then try again.");
      return;
    }

    setStatus("generating");
    setMessage("Creating your voice…");
    try {
      const response = await fetch("/api/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: text.trim(),
          voice,
          emotion: tone,
          accent,
          speed: speed[0],
          pitch: pitch[0],
        }),
      });
      if (!response.ok) throw new Error("Local model unavailable");

      const blob = await response.blob();
      if (audioUrl) URL.revokeObjectURL(audioUrl);
      const nextUrl = URL.createObjectURL(blob);
      const responseFormat = response.headers.get("X-YapLab-Format");
      const nextFormat = responseFormat === "wav" || blob.type.includes("wav") ? "wav" : "mp3";
      setAudioUrl(nextUrl);
      setAudioFormat(nextFormat);
      setEngine(response.headers.get("X-YapLab-Engine") ?? "YapLab voice");
      setStatus("ready");
      setMessage(`Your yap is ready. Play it or download the ${nextFormat.toUpperCase()} file.`);
    } catch {
      if (audioUrl) URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
      speakInBrowser();
    }
  };

  const togglePlayback = () => {
    const player = audioRef.current;
    if (!player) {
      if (status === "playing") {
        window.speechSynthesis.cancel();
        setStatus("ready");
      } else {
        speakInBrowser();
      }
      return;
    }

    if (player.paused) {
      void player.play();
      setStatus("playing");
    } else {
      player.pause();
      setStatus("ready");
    }
  };

  const downloadAudio = () => {
    if (!audioUrl) return;
    const link = document.createElement("a");
    link.href = audioUrl;
    link.download = `yaplab-${voice}-${tone}-${accent}.${audioFormat}`;
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <>
      <section id="studio" className="workspace" aria-label="Text to speech studio">
        <section className="tool-card editor-card" aria-labelledby="script-label" data-reveal>
          <div className="card-heading">
            <div className="card-title-wrap">
              <span className="step-tag lime">01</span>
              <div><h2 id="script-label">WRITE SOMETHING</h2><p>Type or paste your text. Keep it real.</p></div>
            </div>
            <button className="clear-button" type="button" onClick={clear}>
              <RotateCcw aria-hidden="true" size={18} /> CLEAR
            </button>
          </div>

          <div className="textarea-wrap">
            <textarea
              value={text}
              maxLength={MAX_CHARS}
              onChange={(event) => setText(event.target.value)}
              aria-label="Text to convert to speech"
              placeholder="Type something worth hearing…"
            />
            <div className="editor-meta">
              <span>{text.length.toLocaleString()} / {MAX_CHARS.toLocaleString()}</span>
              <span>About {seconds} sec · {wordCount} words <Sparkles aria-hidden="true" size={14} /></span>
            </div>
          </div>

          <div className="examples-row">
            <strong>TRY AN EXAMPLE:</strong>
            <div className="example-buttons">
              {examples.map((example) => (
                <button key={example.label} type="button" onClick={() => setText(example.text)}>{example.label}</button>
              ))}
            </div>
          </div>
        </section>

        <aside className="tool-card controls-card" aria-labelledby="voice-label" data-reveal>
          <div className="card-heading">
            <div className="card-title-wrap">
              <span className="step-tag coral">02</span>
              <div><h2 id="voice-label">CHOOSE HOW IT SOUNDS</h2><p>Same words. A whole different vibe.</p></div>
            </div>
          </div>

          <div className="voice-accent-grid">
            <div className="control-block">
              <div className="control-label"><strong>VOICE</strong><span>{voices.length} voices</span></div>
              <Select value={voice} onValueChange={(value) => setVoice(value as VoiceId)}>
                <SelectTrigger className="voice-select" aria-label="Choose a voice">
                  <SelectValue>
                    <span className="voice-avatar">{activeVoice.initials}</span>
                    <span className="voice-selected-copy"><strong>{activeVoice.name}</strong><small>{activeVoice.note}</small></span>
                  </SelectValue>
                </SelectTrigger>
                <SelectContent className="select-menu" position="popper" align="start">
                  {voices.map((item) => <SelectItem key={item.id} value={item.id}>{item.name} · {item.note}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            <div className="control-block">
              <div className="control-label"><strong>ACCENT</strong><span>{accents.length} options</span></div>
              <Select value={accent} onValueChange={(value) => setAccent(value as AccentId)}>
                <SelectTrigger className="accent-select" aria-label="Choose an accent">
                  <SelectValue>{activeAccent.label}</SelectValue>
                </SelectTrigger>
                <SelectContent className="select-menu" position="popper" align="start">
                  {accents.map((item) => <SelectItem key={item.id} value={item.id}>{item.label}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="control-block tone-block">
            <div className="control-label"><strong>TONE</strong><span>Choose the mood.</span></div>
            <RadioGroup value={tone} onValueChange={(value) => setTone(value as ToneId)} className="tone-grid" aria-label="Choose a speaking tone">
              {tones.map((item) => {
                const ToneIcon = item.icon;
                return (
                  <label key={item.id} className={`tone-chip ${tone === item.id ? "active" : ""}`}>
                    <RadioGroupItem value={item.id} className="tone-radio" />
                    <ToneIcon aria-hidden="true" size={23} strokeWidth={1.8} />
                    <span className="tone-copy"><strong>{item.label}</strong><small>{item.note}</small></span>
                  </label>
                );
              })}
            </RadioGroup>
          </div>

          <div className="sliders">
            <label className="slider-row">
              <span><strong>SPEED</strong><b>{speed[0].toFixed(1)}×</b></span>
              <Slider value={speed} onValueChange={setSpeed} min={0.6} max={1.5} step={0.1} aria-label="Speech speed" />
              <small><span>Slower</span><span>Faster</span></small>
            </label>
            <label className="slider-row">
              <span><strong>PITCH</strong><b>{pitch[0] > 0 ? "+" : ""}{pitch[0]} st</b></span>
              <Slider value={pitch} onValueChange={setPitch} min={-4} max={4} step={1} aria-label="Voice pitch" />
              <small><span>Lower</span><span>Higher</span></small>
            </label>
          </div>
        </aside>
      </section>

      <section className={`result-panel ${status === "playing" ? "is-playing" : ""}`} aria-live="polite">
        <button className="generate-button" type="button" onClick={generate} disabled={status === "generating"}>
          {status === "generating" ? <><span className="spinner" />GENERATING…</> : <><WandSparkles aria-hidden="true" size={21} /> GENERATE MY YAP <ArrowRight aria-hidden="true" size={20} /></>}
        </button>
        <div className="result-details">
          <button className="play-button" type="button" onClick={togglePlayback} aria-label={status === "playing" ? "Pause audio" : "Play audio"}>
            {status === "playing" ? <Pause aria-hidden="true" size={23} fill="currentColor" /> : <Play aria-hidden="true" size={23} fill="currentColor" />}
          </button>
          <div>
            <strong>{status === "idle" ? "YOUR YAP WILL LAND HERE" : `${activeVoice.name} · ${tone} · ${activeAccent.label}`}</strong>
            <span>{message}</span>
          </div>
        </div>
        <div className="waveform" aria-label={status === "playing" ? "Audio playing" : "Audio waveform"}>
          {wave.map((height, index) => <i key={index} style={{ height: `${height}%`, animationDelay: `${index * -0.035}s` }} />)}
        </div>
        <div className="result-actions">
          <span>{engine}</span>
          <button className="download-button" type="button" onClick={downloadAudio} disabled={!audioUrl}>
            <ArrowDownToLine aria-hidden="true" size={18} /> DOWNLOAD {audioFormat.toUpperCase()}
          </button>
        </div>
        {audioUrl ? <audio ref={audioRef} src={audioUrl} onEnded={() => setStatus("ready")} /> : null}
      </section>
    </>
  );
}
