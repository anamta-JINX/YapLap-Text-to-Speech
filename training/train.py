"""Train the compact YapNet experiment from random initialization."""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
import torch
from torch.nn import functional as F
from torch.utils.data import DataLoader
from tqdm import tqdm

from backend.ml.yapnet import YapNet, YapNetConfig
from training.dataset import SpeechDataset, collate_speech


def metadata(manifest: Path, max_speakers: int) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["speaker"]] = counts.get(row["speaker"], 0) + 1
    speakers = sorted(counts, key=counts.get, reverse=True)[:max_speakers]
    speaker_to_id = {name: index for index, name in enumerate(speakers)}
    emotion_to_id = {name: index for index, name in enumerate(["neutral", "happy", "sad", "angry"])}
    accent_to_id = {
        name: index
        for index, name in enumerate(["general", "american", "british", "australian", "indian"])
    }
    return speaker_to_id, emotion_to_id, accent_to_id


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("training/config.json"))
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    random.seed(config["seed"]); np.random.seed(config["seed"]); torch.manual_seed(config["seed"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    manifest = Path(config["manifest"])
    speaker_to_id, emotion_to_id, accent_to_id = metadata(manifest, config["num_speakers"])

    # Ignore examples outside the selected speaker vocabulary without mutating the source manifest.
    raw_rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    filtered = manifest.with_name("train.filtered.jsonl")
    filtered.write_text("\n".join(json.dumps(row) for row in raw_rows if row["speaker"] in speaker_to_id) + "\n", encoding="utf-8")
    dataset = SpeechDataset(
        filtered,
        speaker_to_id,
        emotion_to_id,
        accent_to_id,
        config["sample_rate"],
        config["mel_bins"],
        config["n_fft"],
        config["hop_length"],
        config["max_audio_seconds"],
    )
    loader = DataLoader(dataset, batch_size=config["batch_size"], shuffle=True, num_workers=config["num_workers"], pin_memory=device.type == "cuda", collate_fn=collate_speech, drop_last=True)

    model_config = YapNetConfig(
        hidden_size=config["hidden_size"],
        mel_bins=config["mel_bins"],
        num_speakers=len(speaker_to_id),
        num_emotions=len(emotion_to_id),
        num_accents=len(accent_to_id),
        sample_rate=config["sample_rate"],
        n_fft=config["n_fft"],
        hop_length=config["hop_length"],
    )
    model = YapNet(model_config).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config["learning_rate"], weight_decay=config["weight_decay"])
    checkpoint = Path(config["checkpoint"])
    start_epoch, best_loss = 0, float("inf")
    if args.resume and checkpoint.exists():
        saved = torch.load(checkpoint, map_location=device, weights_only=False)
        model.load_state_dict(saved["model_state"]); optimizer.load_state_dict(saved["optimizer_state"])
        start_epoch, best_loss = saved["epoch"] + 1, saved.get("loss", best_loss)

    scaler = torch.amp.GradScaler("cuda", enabled=device.type == "cuda")
    for epoch in range(start_epoch, config["epochs"]):
        model.train(); running = 0.0
        progress = tqdm(loader, desc=f"epoch {epoch + 1}/{config['epochs']}")
        for batch in progress:
            tokens, mels = batch["tokens"].to(device), batch["mels"].to(device)
            speakers, emotions = batch["speakers"].to(device), batch["emotions"].to(device)
            accents = batch["accents"].to(device)
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=device.type == "cuda"):
                predicted, ratio = model(tokens, speakers, emotions, accents, target_frames=mels.shape[-1])
                mask = batch["mask"].to(device).unsqueeze(1)
                acoustic_loss = (torch.abs(predicted - mels) * mask).sum() / (mask.sum() * mels.shape[1])
                token_lengths = (tokens != 0).sum(dim=1).clamp_min(1)
                target_ratio = batch["mel_lengths"].to(device) / token_lengths
                length_loss = F.smooth_l1_loss(ratio, target_ratio)
                loss = acoustic_loss + .1 * length_loss
            scaler.scale(loss).backward(); scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer); scaler.update()
            running += loss.item(); progress.set_postfix(loss=f"{loss.item():.4f}")
        epoch_loss = running / max(1, len(loader))
        if epoch_loss < best_loss:
            best_loss = epoch_loss; checkpoint.parent.mkdir(parents=True, exist_ok=True)
            aliases = {
                name: index % len(speaker_to_id)
                for index, name in enumerate(["zubeda", "khalda", "samundar", "jameed"])
            }
            torch.save({
                "model_state": model.state_dict(), "optimizer_state": optimizer.state_dict(),
                "model_config": model_config.to_dict(), "speaker_to_id": speaker_to_id,
                "emotion_to_id": emotion_to_id, "accent_to_id": accent_to_id,
                "voice_aliases": aliases,
                "epoch": epoch, "loss": best_loss, "trained_from_scratch": True,
                "datasets": sorted({row["source"] for row in raw_rows}),
            }, checkpoint)
            print(f"Saved best checkpoint to {checkpoint} (loss={best_loss:.4f})")


if __name__ == "__main__":
    main()
