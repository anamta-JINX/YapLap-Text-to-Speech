"""Check the deployable app before Vercel publishes a build.

Run with --speech to also exercise the real neural speech provider.
The default checks require no network access or extra test dependencies.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from html.parser import HTMLParser
from urllib.parse import urlsplit

import edge_tts

from app import FRONTEND_INDEX, app


class AssetLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.paths = {"/favicon.svg", "/paper-plane-pack.png"}

    def handle_starttag(self, tag: str, attrs) -> None:
        for key, value in attrs:
            if key in {"src", "href"} and value and value.startswith("/"):
                path = urlsplit(value).path
                if path != "/":
                    self.paths.add(path)


async def request(path: str, payload: dict | None = None):
    body = b"" if payload is None else json.dumps(payload).encode()
    messages = []
    delivered = False

    async def receive():
        nonlocal delivered
        if not delivered:
            delivered = True
            return {"type": "http.request", "body": body, "more_body": False}
        await asyncio.Event().wait()

    async def send(message):
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.4"},
        "http_version": "1.1",
        "scheme": "http",
        "method": "GET" if payload is None else "POST",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [(b"content-type", b"application/json")],
        "server": ("localhost", 8000),
        "client": ("127.0.0.1", 12345),
    }
    await asyncio.wait_for(app(scope, receive, send), timeout=45)
    start = next(item for item in messages if item["type"] == "http.response.start")
    headers = {key.decode().lower(): value.decode() for key, value in start["headers"]}
    content = b"".join(
        item.get("body", b"")
        for item in messages
        if item["type"] == "http.response.body"
    )
    return start["status"], headers, content


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


async def verify(speech: bool = False) -> None:
    require(callable(edge_tts.Communicate), "The neural speech dependency is missing.")
    require(FRONTEND_INDEX.is_file(), "frontend/out/index.html is missing.")

    async with app.router.lifespan_context(app):
        status, _, content = await request("/api/health")
        require(status == 200 and json.loads(content)["status"] == "ok", "Health check failed.")

        status, _, content = await request("/api/voices")
        voices = json.loads(content)
        require(status == 200, "Voice catalogue failed.")
        require(
            {voice["id"] for voice in voices["voices"]}
            == {"zubeda", "khalda", "samundar", "jameed"},
            "The voice catalogue changed.",
        )
        require(len(voices["emotions"]) == 4 and len(voices["accents"]) == 5,
                "Tone or accent options are missing.")

        status, headers, content = await request("/")
        require(status == 200 and "text/html" in headers.get("content-type", ""),
                "The homepage did not return HTML.")
        require(content == FRONTEND_INDEX.read_bytes(), "The homepage differs from the static export.")

        links = AssetLinks()
        links.feed(content.decode())
        root = FRONTEND_INDEX.parent.resolve()
        for path in sorted(links.paths):
            source = (root / path.lstrip("/")).resolve()
            require(source.is_relative_to(root) and source.is_file(), f"Missing frontend asset: {path}")
            status, _, content = await request(path)
            require(status == 200 and content == source.read_bytes(), f"Asset response failed: {path}")

        status, _, _ = await request("/api/tts", {"text": ""})
        require(status == 422, "Speech request validation failed.")
        print(f"PASS: app startup, health, voices, homepage, {len(links.paths)} assets, and API validation.")

        if speech:
            status, headers, content = await request(
                "/api/tts",
                {
                    "text": "Your words called. They wanna yap.",
                    "voice": "zubeda",
                    "emotion": "neutral",
                    "accent": "general",
                    "speed": 1.0,
                    "pitch": 0,
                },
            )
            require(status == 200, f"Speech generation failed: HTTP {status}: {content[:500]!r}")
            require(headers.get("content-type", "").startswith("audio/mpeg"),
                    "Speech did not return an MP3.")
            require(headers.get("x-yaplab-engine") == "YapLab Neural",
                    "Neural speech fell back to a different engine.")
            require(".mp3" in headers.get("content-disposition", "") and len(content) > 1000,
                    "The speech download is missing or empty.")
            print(f"PASS: real neural speech API returned a downloadable MP3 ({len(content)} bytes).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--speech", action="store_true", help="Also call the real speech provider.")
    arguments = parser.parse_args()
    asyncio.run(verify(speech=arguments.speech))
