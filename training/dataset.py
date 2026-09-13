from __future__ import annotations

import json
from pathlib import Path

import torch
import torchaudio
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import Dataset

from backend.ml.tokenizer import PAD_ID, text_to_sequence


class SpeechDataset(Dataset):
    def __init__(
        self,
        manifest: Path,
        speaker_to_id: dict[str, int],
        emotion_to_id: dict[str, int],
        accent_to_id: dict[str, int],
        sample_rate: int,
        mel_bins: int,
        n_fft: int,
        hop_length: int,
        max_seconds: float,
    ):
        self.rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.speaker_to_id = speaker_to_id
        self.emotion_to_id = emotion_to_id
        self.accent_to_id = accent_to_id
        self.sample_rate, self.max_samples = sample_rate, int(sample_rate * max_seconds)
        self.mel = torchaudio.transforms.MelSpectrogram(sample_rate=sample_rate, n_fft=n_fft, hop_length=hop_length, n_mels=mel_bins, f_min=40, f_max=sample_rate // 2)

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict:
        row = self.rows[index]
        audio, sr = torchaudio.load(row["audio"])
        audio = audio.mean(dim=0, keepdim=True)
        if sr != self.sample_rate:
            audio = torchaudio.functional.resample(audio, sr, self.sample_rate)
        audio = audio[:, :self.max_samples]
        peak = audio.abs().max().clamp_min(1e-5)
        audio = audio / peak * .95
        mel = self.mel(audio).squeeze(0).clamp_min(1e-5).log().transpose(0, 1)
        return {
            "tokens": torch.tensor(text_to_sequence(row["text"]), dtype=torch.long),
            "mel": mel,
            "speaker": torch.tensor(self.speaker_to_id[row["speaker"]], dtype=torch.long),
            "emotion": torch.tensor(self.emotion_to_id[row["emotion"]], dtype=torch.long),
            "accent": torch.tensor(self.accent_to_id[row.get("accent", "general")], dtype=torch.long),
        }


def collate_speech(items: list[dict]) -> dict:
    tokens = pad_sequence([item["tokens"] for item in items], batch_first=True, padding_value=PAD_ID)
    mel_lengths = torch.tensor([item["mel"].shape[0] for item in items], dtype=torch.long)
    max_frames = int(mel_lengths.max())
    mels = torch.zeros(len(items), max_frames, items[0]["mel"].shape[1])
    mask = torch.zeros(len(items), max_frames, dtype=torch.bool)
    for index, item in enumerate(items):
        frames = item["mel"].shape[0]
        mels[index, :frames] = item["mel"]
        mask[index, :frames] = True
    return {
        "tokens": tokens, "mels": mels.transpose(1, 2), "mel_lengths": mel_lengths, "mask": mask,
        "speakers": torch.stack([item["speaker"] for item in items]),
        "emotions": torch.stack([item["emotion"] for item in items]),
        "accents": torch.stack([item["accent"] for item in items]),
    }
