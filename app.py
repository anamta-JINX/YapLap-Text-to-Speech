"""Build the React frontend and run the YapLab FastAPI application."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

try:
    import uvicorn
    from backend.main import create_application
except ModuleNotFoundError as exc:
    missing = exc.name or "a required package"
    raise SystemExit(
        f"YapLab is missing '{missing}' for {sys.executable}.\n"
        f'Install this interpreter\'s dependencies with:\n  "{sys.executable}" '
        "-m pip install -r requirements.txt"
    ) from exc

PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
FRONTEND_INDEX = FRONTEND_ROOT / "dist" / "client" / "index.html"

app = create_application(PROJECT_ROOT)


def frontend_needs_build() -> bool:
    if not FRONTEND_INDEX.exists():
        return True

    built_at = FRONTEND_INDEX.stat().st_mtime
    source_roots = [
        FRONTEND_ROOT / "app",
        FRONTEND_ROOT / "components",
        FRONTEND_ROOT / "data",
        FRONTEND_ROOT / "public",
    ]
    return any(
        path.stat().st_mtime > built_at
        for source_root in source_roots
        if source_root.exists()
        for path in source_root.rglob("*")
        if path.is_file()
    )


def build_frontend_if_needed() -> None:
    if not frontend_needs_build():
        return

    package_manager = shutil.which("pnpm") or shutil.which("npm")
    if not package_manager:
        raise RuntimeError(
            "Node.js with pnpm or npm is required for the first frontend build."
        )

    subprocess.run(
        [package_manager, "run", "build"],
        cwd=FRONTEND_ROOT,
        check=True,
    )


if __name__ == "__main__":
    build_frontend_if_needed()
    uvicorn.run(app, host="127.0.0.1", port=8000)
