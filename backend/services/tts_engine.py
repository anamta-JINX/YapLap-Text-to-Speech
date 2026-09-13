from __future__ import annotations

import asyncio
import io
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path

from backend.ml.tokenizer import text_to_sequence


@dataclass(frozen=True)
class AudioResult:
    content: bytes
    media_type: str
    extension: str
    engine: str


class YapTTSEngine:
    voices = [
        {"id": "zubeda", "name": "Zubeda", "gender": "female"},
        {"id": "khalda", "name": "Khalda", "gender": "female"},
        {"id": "samundar", "name": "Samundar Khan", "gender": "male"},
        {"id": "jameed", "name": "Jameed", "gender": "male"},
    ]
    emotions = ["neutral", "happy", "sad", "angry"]
    accents = ["general", "american", "british", "australian", "indian"]

    _neural_voices = {
        "general": {
            "zubeda": "en-US-AriaNeural",
            "khalda": "en-US-JennyNeural",
            "samundar": "en-US-GuyNeural",
            "jameed": "en-US-DavisNeural",
        },
        "american": {
            "zubeda": "en-US-AriaNeural",
            "khalda": "en-US-JennyNeural",
            "samundar": "en-US-GuyNeural",
            "jameed": "en-US-DavisNeural",
        },
        "british": {
            "zubeda": "en-GB-SoniaNeural",
            "khalda": "en-GB-LibbyNeural",
            "samundar": "en-GB-RyanNeural",
            "jameed": "en-GB-ThomasNeural",
        },
        "australian": {
            "zubeda": "en-AU-NatashaNeural",
            "khalda": "en-AU-AnnetteNeural",
            "samundar": "en-AU-WilliamNeural",
            "jameed": "en-AU-DarrenNeural",
        },
        "indian": {
            "zubeda": "en-IN-NeerjaNeural",
            "khalda": "en-IN-AashiNeural",
            "samundar": "en-IN-PrabhatNeural",
            "jameed": "en-IN-AaravNeural",
        },
    }
    _voice_index = {"zubeda": 0, "khalda": 1, "samundar": 2, "jameed": 3}

    def __init__(self, checkpoint_path: Path):
        self.checkpoint_path = checkpoint_path
        self.model = None
        self.device = "cpu"
        self.checkpoint_loaded = False
        self.name = "YapLab Neural"
        self.bundle: dict = {}

    def load(self) -> None:
        if not self.checkpoint_path.exists():
            return
        try:
            import torch
            from backend.ml.yapnet import YapNet, YapNetConfig

            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.bundle = torch.load(
                self.checkpoint_path, map_location=self.device, weights_only=False
            )
            config = YapNetConfig(**self.bundle["model_config"])
            model = YapNet(config).to(self.device)
            model.load_state_dict(self.bundle["model_state"])
            model.eval()
            self.model = model
            self.checkpoint_loaded = True
        except Exception as exc:
            print(f"YapLab checkpoint could not be loaded: {exc}")

    async def synthesize(
        self,
        text: str,
        voice: str,
        emotion: str,
        accent: str,
        speed: float,
        pitch: int,
    ) -> AudioResult:
        neural_error: Exception | None = None
        try:
            return await self._synthesize_neural(
                text, voice, emotion, accent, speed, pitch
            )
        except Exception as exc:
            neural_error = exc

        if self.checkpoint_loaded:
            try:
                content = await asyncio.to_thread(
                    self._synthesize_model, text, voice, emotion, accent, speed, pitch
                )
                return AudioResult(content, "audio/wav", "wav", "YapNet local")
            except Exception as exc:
                print(f"YapNet synthesis failed: {exc}")

        try:
            content = await asyncio.to_thread(
                self._synthesize_system, text, voice, emotion, accent, speed
            )
            return AudioResult(content, "audio/wav", "wav", "System voice fallback")
        except Exception as system_error:
            raise RuntimeError(
                "Neural speech is unavailable. Check your internet connection and install "
                f"the app requirements with this Python interpreter. ({neural_error}; {system_error})"
            ) from system_error

    async def _synthesize_neural(
        self,
        text: str,
        voice: str,
        emotion: str,
        accent: str,
        speed: float,
        pitch: int,
    ) -> AudioResult:
        import edge_tts

        tone_tuning = {
            "neutral": (0, 0, 0),
            "happy": (11, 15, 4),
            "sad": (-20, -13, -14),
            "angry": (16, -9, 9),
        }
        persona_pitch = {
            "zubeda": -2,
            "khalda": 6,
            "samundar": -10,
            "jameed": -3,
        }
        persona_rate = {"zubeda": -2, "khalda": 3, "samundar": -5, "jameed": 2}
        tone_rate, tone_pitch, tone_volume = tone_tuning[emotion]
        rate = round((speed - 1) * 100) + tone_rate + persona_rate[voice]
        pitch_hz = pitch * 4 + tone_pitch + persona_pitch[voice]
        communicate = edge_tts.Communicate(
            text,
            self._neural_voices[accent][voice],
            rate=self._signed(rate, "%"),
            pitch=self._signed(pitch_hz, "Hz"),
            volume=self._signed(tone_volume, "%"),
        )
        audio = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio.extend(chunk["data"])
        if len(audio) < 100:
            raise RuntimeError("The neural voice service returned no audio.")
        return AudioResult(bytes(audio), "audio/mpeg", "mp3", "YapLab Neural")

    @staticmethod
    def _signed(value: int, unit: str) -> str:
        return f"{value:+d}{unit}"

    def _synthesize_model(
        self,
        text: str,
        voice: str,
        emotion: str,
        accent: str,
        speed: float,
        pitch: int,
    ) -> bytes:
        import torch
        import torchaudio

        tokens = torch.tensor([text_to_sequence(text)], dtype=torch.long, device=self.device)
        aliases = self.bundle.get(
            "voice_aliases",
            {"zubeda": 0, "khalda": 1, "samundar": 2, "jameed": 3},
        )
        emotion_ids = self.bundle.get(
            "emotion_to_id", {"neutral": 0, "happy": 1, "sad": 2, "angry": 3}
        )
        accent_ids = self.bundle.get(
            "accent_to_id",
            {
                "general": 0,
                "american": 1,
                "british": 2,
                "australian": 3,
                "indian": 4,
            },
        )
        mel = self.model.infer(
            tokens,
            int(aliases.get(voice, self._voice_index[voice])),
            int(emotion_ids.get(emotion, 0)),
            int(accent_ids.get(accent, 0)),
            speed,
        )
        linear = torchaudio.transforms.InverseMelScale(
            n_stft=self.model.config.n_fft // 2 + 1,
            n_mels=self.model.config.mel_bins,
            sample_rate=self.model.config.sample_rate,
        )(mel.exp().clamp_min(1e-5).cpu())
        waveform = torchaudio.transforms.GriffinLim(
            n_fft=self.model.config.n_fft,
            hop_length=self.model.config.hop_length,
            n_iter=48,
        )(linear).clamp(-1, 1)
        if pitch:
            waveform = torchaudio.functional.pitch_shift(
                waveform, self.model.config.sample_rate, pitch
            )
        return self._wave_bytes(waveform.numpy(), self.model.config.sample_rate)

    def _synthesize_system(
        self, text: str, voice: str, emotion: str, accent: str, speed: float
    ) -> bytes:
        try:
            import pyttsx3
        except ImportError as exc:
            raise RuntimeError("pyttsx3 is not installed for offline speech.") from exc
        tuning = {
            "neutral": (1.0, 0.94),
            "happy": (1.14, 1.0),
            "sad": (0.76, 0.68),
            "angry": (1.22, 1.0),
        }
        rate_factor, volume = tuning[emotion]
        with tempfile.TemporaryDirectory(prefix="yaplab-") as folder:
            path = Path(folder) / "speech.wav"
            speaker = pyttsx3.init()
            installed = speaker.getProperty("voices")
            if installed:
                selected = self._pick_system_voice(
                    installed, accent, self._voice_index[voice]
                )
                speaker.setProperty("voice", selected.id)
            speaker.setProperty("rate", int(175 * speed * rate_factor))
            speaker.setProperty("volume", volume)
            speaker.save_to_file(text, str(path))
            speaker.runAndWait()
            speaker.stop()
            if not path.exists() or path.stat().st_size < 100:
                raise RuntimeError("The system voice did not produce audio.")
            return path.read_bytes()

    @staticmethod
    def _pick_system_voice(installed, accent: str, voice_index: int):
        hints = {
            "general": [],
            "american": ["en-us", "en_us", "american", "zira", "david"],
            "british": ["en-gb", "en_gb", "british", "hazel", "george"],
            "australian": ["en-au", "en_au", "australian", "natasha"],
            "indian": ["en-in", "en_in", "indian", "heera", "ravi"],
        }

        def searchable(item) -> str:
            languages = " ".join(
                value.decode(errors="ignore") if isinstance(value, bytes) else str(value)
                for value in getattr(item, "languages", [])
            )
            return f"{getattr(item, 'id', '')} {getattr(item, 'name', '')} {languages}".lower()

        candidates = [
            item
            for item in installed
            if any(hint in searchable(item) for hint in hints[accent])
        ]
        pool = candidates or list(installed)
        return pool[voice_index % len(pool)]

    @staticmethod
    def _wave_bytes(samples, sample_rate: int) -> bytes:
        import numpy as np

        pcm = (np.asarray(samples).reshape(-1) * 32767).astype("<i2")
        output = io.BytesIO()
        with wave.open(output, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(pcm.tobytes())
        return output.getvalue()
