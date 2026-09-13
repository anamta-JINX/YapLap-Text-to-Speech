"""A compact, fully trainable emotional acoustic model with no pretrained weights."""
from dataclasses import asdict, dataclass

import torch
from torch import nn
from torch.nn import functional as F

from backend.ml.tokenizer import SYMBOLS


@dataclass
class YapNetConfig:
    vocab_size: int = len(SYMBOLS)
    hidden_size: int = 256
    mel_bins: int = 80
    num_speakers: int = 128
    num_emotions: int = 4
    num_accents: int = 5
    sample_rate: int = 22050
    n_fft: int = 1024
    hop_length: int = 256

    def to_dict(self) -> dict:
        return asdict(self)


class YapNet(nn.Module):
    """Text + speaker + emotion to log-mel frames.

    During training, hidden states are resized to the target mel length. The length
    head learns frames-per-token for inference. This avoids pretrained aligners and
    keeps the complete training stack inside this repository.
    """

    def __init__(self, config: YapNetConfig):
        super().__init__()
        self.config = config
        h = config.hidden_size
        self.text_embedding = nn.Embedding(config.vocab_size, h, padding_idx=0)
        self.encoder = nn.GRU(h, h // 2, num_layers=2, batch_first=True, bidirectional=True, dropout=.1)
        self.speaker_embedding = nn.Embedding(config.num_speakers, h)
        self.emotion_embedding = nn.Embedding(config.num_emotions, h)
        self.accent_embedding = nn.Embedding(config.num_accents, h)
        self.condition = nn.Sequential(nn.Linear(h * 4, h), nn.GELU(), nn.LayerNorm(h))
        self.length_head = nn.Sequential(nn.Linear(h, h // 2), nn.GELU(), nn.Linear(h // 2, 1))
        self.decoder = nn.Sequential(
            nn.Conv1d(h, h, 5, padding=2), nn.GELU(), nn.BatchNorm1d(h),
            nn.Conv1d(h, h, 5, padding=2), nn.GELU(), nn.BatchNorm1d(h),
            nn.Conv1d(h, h // 2, 5, padding=2), nn.GELU(),
            nn.Conv1d(h // 2, config.mel_bins, 1),
        )

    def forward(self, tokens: torch.Tensor, speaker_ids: torch.Tensor, emotion_ids: torch.Tensor, accent_ids: torch.Tensor, target_frames: int | None = None):
        encoded, _ = self.encoder(self.text_embedding(tokens))
        pooled = encoded.mean(dim=1)
        speaker = self.speaker_embedding(speaker_ids)
        emotion = self.emotion_embedding(emotion_ids)
        accent = self.accent_embedding(accent_ids)
        conditioned = self.condition(torch.cat([pooled, speaker, emotion, accent], dim=-1))
        encoded = encoded + conditioned.unsqueeze(1)
        predicted_ratio = F.softplus(self.length_head(conditioned)).squeeze(-1) + 2.0
        if target_frames is None:
            target_frames = int(torch.clamp(predicted_ratio[0] * tokens.shape[1], 24, 2600).item())
        expanded = F.interpolate(encoded.transpose(1, 2), size=target_frames, mode="linear", align_corners=False)
        return self.decoder(expanded), predicted_ratio

    @torch.inference_mode()
    def infer(self, tokens: torch.Tensor, speaker_id: int, emotion_id: int, accent_id: int, speed: float = 1.0) -> torch.Tensor:
        speaker = torch.tensor([speaker_id], device=tokens.device)
        emotion = torch.tensor([emotion_id], device=tokens.device)
        accent = torch.tensor([accent_id], device=tokens.device)
        encoded, _ = self.encoder(self.text_embedding(tokens))
        pooled = encoded.mean(dim=1)
        conditioned = self.condition(torch.cat([pooled, self.speaker_embedding(speaker), self.emotion_embedding(emotion), self.accent_embedding(accent)], dim=-1))
        encoded = encoded + conditioned.unsqueeze(1)
        ratio = F.softplus(self.length_head(conditioned)).squeeze() + 2.0
        frames = int(torch.clamp(ratio * tokens.shape[1] / speed, 24, 2600).item())
        expanded = F.interpolate(encoded.transpose(1, 2), size=frames, mode="linear", align_corners=False)
        return self.decoder(expanded).squeeze(0)
