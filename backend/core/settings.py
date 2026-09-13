from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    project_root: Path
    frontend_root: Path
    frontend_build: Path
    checkpoint: Path

    @classmethod
    def from_project_root(cls, project_root: Path) -> "Settings":
        root = project_root.resolve()
        frontend = root / "frontend"
        return cls(
            project_root=root,
            frontend_root=frontend,
            frontend_build=frontend / "dist" / "client",
            checkpoint=root / "models" / "yaplab_emotion_tts.pt",
        )
