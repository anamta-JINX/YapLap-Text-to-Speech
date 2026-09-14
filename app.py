"""Install/build the React frontend as needed, then run YapLab locally."""
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
FRONTEND_INDEX = FRONTEND_ROOT / "out" / "index.html"

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
    if not shutil.which("node") or not package_manager:
        raise SystemExit(
            "YapLab needs Node.js 22.13+ with npm or pnpm to rebuild the frontend.\n"
            "Install Node.js, reopen your terminal, and run python app.py again."
        )

    is_pnpm = Path(package_manager).stem.lower() == "pnpm"
    install_args = (
        ["install", "--prod=false", "--frozen-lockfile"]
        if is_pnpm
        else ["install", "--include=dev", "--include=optional", "--no-audit", "--no-fund"]
    )

    # A restored or incomplete node_modules directory can exist without the CLI.
    required_files = [
        "next/dist/bin/next",
        "react/package.json",
        "react-dom/package.json",
    ]

    def dependencies_ready() -> bool:
        return all(
            (FRONTEND_ROOT / "node_modules" / filename).is_file()
            for filename in required_files
        )

    def run_step(arguments: list[str], label: str) -> None:
        try:
            subprocess.run(
                [package_manager, *arguments],
                cwd=FRONTEND_ROOT,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            raise SystemExit(
                f"YapLab {label} failed (exit code {exc.returncode}).\n"
                "See the package manager error above. Fix that error, then run python app.py again."
            ) from None
        except OSError as exc:
            raise SystemExit(f"YapLab could not start {package_manager}: {exc}") from None

    if not dependencies_ready():
        print("Installing missing frontend dependencies (internet required)...", flush=True)
        run_step(install_args, "frontend dependency installation")
        if not dependencies_ready():
            raise SystemExit(
                "Frontend installation finished, but required build packages are still missing.\n"
                f'Open "{FRONTEND_ROOT}" and run: '
                f'{Path(package_manager).stem} {" ".join(install_args)}'
            )

    print("Building the YapLab frontend...", flush=True)
    run_step(["run", "build"], "frontend build")
    if not FRONTEND_INDEX.is_file():
        raise SystemExit(
            "The frontend build did not produce frontend/out/index.html.\n"
            "Check the build output above before restarting YapLab."
        )


if __name__ == "__main__":
    build_frontend_if_needed()
    uvicorn.run(app, host="127.0.0.1", port=8000)
