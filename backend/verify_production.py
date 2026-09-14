"""Verify the public production URL after this commit finishes deploying."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

from backend.verify_deployment import verify


class SameOriginRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        if urlsplit(newurl).netloc != urlsplit(request.full_url).netloc:
            raise RuntimeError(
                "Production redirected to another host. If this is Vercel sign-in, "
                "authenticated production verification requires project access."
            )
        return super().redirect_request(request, fp, code, msg, headers, newurl)


def wait_for_deployment() -> None:
    repository = os.environ["GITHUB_REPOSITORY"]
    commit = os.environ["GITHUB_SHA"]
    token = os.environ.get("GH_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "YapLab-deployment-check",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    endpoint = f"https://api.github.com/repos/{repository}/commits/{commit}/status"
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        with urlopen(Request(endpoint, headers=headers), timeout=15) as response:
            data = json.load(response)
        status = next(
            (item for item in data["statuses"] if item["context"] == "Vercel"),
            None,
        )
        if status and status["state"] == "success":
            print(f"PASS: Vercel deployed commit {commit}.", flush=True)
            return
        if status and status["state"] in {"failure", "error"}:
            raise RuntimeError(f"Vercel deployment failed: {status.get('target_url', '')}")
        time.sleep(10)
    raise TimeoutError("Vercel did not finish deploying this commit within 180 seconds.")


def public_request(base_url: str, path: str, payload: dict | None = None):
    body = None if payload is None else json.dumps(payload).encode()
    request = Request(
        base_url.rstrip("/") + path,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "YapLab-deployment-check",
        },
    )
    opener = build_opener(SameOriginRedirect())
    try:
        response = opener.open(request, timeout=45)
    except HTTPError as error:
        response = error
    with response:
        status = response.status
        if status in {401, 403}:
            raise RuntimeError(
                f"Production access denied (HTTP {status}); the live checks could not run."
            )
        return status, {key.lower(): value for key, value in response.headers.items()}, response.read()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Production origin to verify.")
    parser.add_argument("--wait-deployment", action="store_true")
    arguments = parser.parse_args()
    if arguments.wait_deployment:
        wait_for_deployment()

    async def deployed_request(path: str, payload: dict | None = None):
        return await asyncio.to_thread(public_request, arguments.url, path, payload)

    asyncio.run(verify(speech=True, request_fn=deployed_request))
