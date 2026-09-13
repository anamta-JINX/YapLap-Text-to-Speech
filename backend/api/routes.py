from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from backend.api.schemas import TTSRequest
from backend.services.tts_engine import YapTTSEngine


def create_api_router(engine: YapTTSEngine) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health() -> dict:
        return {
            "status": "ok",
            "engine": engine.name,
            "checkpoint_loaded": engine.checkpoint_loaded,
        }

    @router.get("/voices")
    def list_voices() -> dict:
        return {
            "voices": engine.voices,
            "emotions": engine.emotions,
            "accents": engine.accents,
        }

    @router.post("/tts")
    async def synthesize(payload: TTSRequest) -> Response:
        try:
            audio = await engine.synthesize(
                text=payload.text,
                voice=payload.voice,
                emotion=payload.emotion,
                accent=payload.accent,
                speed=payload.speed,
                pitch=payload.pitch,
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        return Response(
            content=audio.content,
            media_type=audio.media_type,
            headers={
                "Content-Disposition": (
                    f'attachment; filename="yaplab-{payload.voice}-'
                    f'{payload.emotion}-{payload.accent}.{audio.extension}"'
                ),
                "X-YapLab-Engine": audio.engine,
                "X-YapLab-Format": audio.extension,
            },
        )

    return router
