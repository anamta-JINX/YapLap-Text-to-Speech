from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from backend.services.tts_engine import YapTTSEngine


class FakeCommunicate:
    calls: list[tuple[str, str, dict[str, str]]] = []

    def __init__(self, text: str, voice: str, **tuning: str):
        self.calls.append((text, voice, tuning))

    async def stream(self):
        yield {"type": "audio", "data": b"ID3" + (b"a" * 256)}


class YapTTSEngineTests(unittest.IsolatedAsyncioTestCase):
    async def test_all_voice_accent_and_emotion_combinations_download(self):
        engine = YapTTSEngine(Path("models/not-present.pt"))
        fake_module = SimpleNamespace(Communicate=FakeCommunicate)
        FakeCommunicate.calls.clear()

        with patch.dict(sys.modules, {"edge_tts": fake_module}):
            for accent in engine.accents:
                for voice in (item["id"] for item in engine.voices):
                    for emotion in engine.emotions:
                        result = await engine.synthesize(
                            "A small voice test.", voice, emotion, accent, 1.0, 0
                        )
                        self.assertEqual(result.media_type, "audio/mpeg")
                        self.assertEqual(result.extension, "mp3")
                        self.assertGreater(len(result.content), 100)

        self.assertEqual(len(FakeCommunicate.calls), 80)
        tunings = {emotion: FakeCommunicate.calls[index][2] for index, emotion in enumerate(engine.emotions)}
        self.assertNotEqual(tunings["happy"], tunings["sad"])
        self.assertNotEqual(tunings["neutral"], tunings["angry"])


if __name__ == "__main__":
    unittest.main()
