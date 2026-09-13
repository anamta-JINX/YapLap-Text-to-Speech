from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from backend.api.routes import create_api_router
from backend.core.settings import Settings
from backend.services.tts_engine import YapTTSEngine


def create_application(project_root: Path) -> FastAPI:
    settings = Settings.from_project_root(project_root)
    engine = YapTTSEngine(settings.checkpoint)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        engine.load()
        yield

    app = FastAPI(
        title="YapLab API",
        version="2.3.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:8000",
        ],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    app.include_router(create_api_router(engine), prefix="/api")

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        web_root = settings.frontend_build.resolve()
        requested = (web_root / path).resolve()
        if path and requested.is_file() and requested.is_relative_to(web_root):
            return FileResponse(requested)

        index = web_root / "index.html"
        if index.exists():
            return FileResponse(index)

        return JSONResponse(
            {
                "message": "Frontend has not been built yet.",
                "fix": "Run python app.py from the project root.",
            },
            status_code=503,
        )

    return app
