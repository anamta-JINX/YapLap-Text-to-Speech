from typing import Literal

from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    voice: Literal["zubeda", "khalda", "samundar", "jameed"] = "zubeda"
    emotion: Literal["neutral", "happy", "sad", "angry"] = "neutral"
    accent: Literal["general", "american", "british", "australian", "indian"] = "general"
    speed: float = Field(default=1.0, ge=0.6, le=1.5)
    pitch: int = Field(default=0, ge=-4, le=4)
