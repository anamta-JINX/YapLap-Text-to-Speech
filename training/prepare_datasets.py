"""Build a compact training manifest from LJSpeech, RAVDESS and optional VCTK."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

AUDIO_SUFFIXES = {".wav", ".flac"}
ACCENTS = {"general", "american", "british", "australian", "indian"}


def add_ljspeech(root: Path) -> list[dict]:
    metadata_files = list(root.rglob("metadata.csv"))
    if not metadata_files:
        return []

    dataset_root = metadata_files[0].parent
    rows: list[dict] = []
    with metadata_files[0].open(encoding="utf-8", errors="ignore") as handle:
        for parts in csv.reader(handle, delimiter="|"):
            if len(parts) < 2:
                continue
            audio = dataset_root / "wavs" / f"{parts[0]}.wav"
            text = parts[2].strip() if len(parts) > 2 and parts[2].strip() else parts[1].strip()
            if audio.exists() and text:
                rows.append(
                    {
                        "audio": str(audio.resolve()),
                        "text": text,
                        "speaker": "ljspeech_lj",
                        "emotion": "neutral",
                        "accent": "american",
                        "source": "ljspeech",
                    }
                )
    return rows


def add_ravdess(root: Path) -> list[dict]:
    rows: list[dict] = []
    emotions = {"01": "neutral", "03": "happy", "04": "sad", "05": "angry"}
    statements = {
        "01": "Kids are talking by the door.",
        "02": "Dogs are sitting by the door.",
    }
    for audio in root.rglob("*.wav"):
        parts = audio.stem.split("-")
        if len(parts) != 7 or parts[0] != "03" or parts[1] != "01":
            continue
        emotion = emotions.get(parts[2])
        text = statements.get(parts[4])
        if emotion and text:
            rows.append(
                {
                    "audio": str(audio.resolve()),
                    "text": text,
                    "speaker": f"ravdess_{parts[6]}",
                    "emotion": emotion,
                    "accent": "american",
                    "source": "ravdess",
                }
            )
    return rows


def _accent_group(label: str) -> str:
    value = label.lower().replace("_", " ")
    if any(term in value for term in ["american", "canadian", "north america"]):
        return "american"
    if any(term in value for term in ["australian", "new zealand"]):
        return "australian"
    if any(term in value for term in ["indian", "india"]):
        return "indian"
    if any(term in value for term in ["english", "scottish", "irish", "welsh", "british", "england"]):
        return "british"
    return "general"


def _vctk_accents(root: Path) -> dict[str, str]:
    candidates = list(root.rglob("speaker-info.txt"))
    if not candidates:
        return {}

    result: dict[str, str] = {}
    for line in candidates[0].read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = line.split(maxsplit=4)
        if len(parts) >= 4 and parts[0].lower().startswith("p"):
            result[parts[0]] = _accent_group(" ".join(parts[3:]))
    return result


def add_vctk(root: Path) -> list[dict]:
    transcripts = {
        path.stem: path
        for path in root.rglob("*.txt")
        if path.name != "speaker-info.txt"
    }
    speaker_accents = _vctk_accents(root)
    rows: list[dict] = []

    for audio in root.rglob("*"):
        if not audio.is_file() or audio.suffix.lower() not in AUDIO_SUFFIXES:
            continue
        stem = audio.stem.replace("_mic1", "").replace("_mic2", "")
        speaker = stem.split("_")[0]
        text_path = transcripts.get(stem)
        if text_path:
            rows.append(
                {
                    "audio": str(audio.resolve()),
                    "text": text_path.read_text(encoding="utf-8", errors="ignore").strip(),
                    "speaker": f"vctk_{speaker}",
                    "emotion": "neutral",
                    "accent": speaker_accents.get(speaker, "general"),
                    "source": "vctk",
                }
            )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ljspeech", type=Path, required=True)
    parser.add_argument("--ravdess", type=Path, required=True)
    parser.add_argument("--vctk", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/processed/train.jsonl"))
    args = parser.parse_args()

    rows = add_ljspeech(args.ljspeech) + add_ravdess(args.ravdess)
    if args.vctk:
        rows.extend(add_vctk(args.vctk))

    rows = [
        row
        for row in rows
        if row["text"] and Path(row["audio"]).exists() and row["accent"] in ACCENTS
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    sources = {
        name: sum(row["source"] == name for row in rows)
        for name in sorted({row["source"] for row in rows})
    }
    print(f"Wrote {len(rows):,} examples to {args.output}: {sources}")


if __name__ == "__main__":
    main()
