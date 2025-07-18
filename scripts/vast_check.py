from __future__ import annotations

"""Check that the server is healthy and ready on Vast.ai."""

import argparse
import asyncio
import sys

import httpx
from aiortc import RTCPeerConnection, RTCSessionDescription


async def perform_check(base_url: str) -> None:
    async with httpx.AsyncClient(base_url=base_url, timeout=10) as client:
        resp = await client.get("/health")
        resp.raise_for_status()
        resp = await client.get("/ready")
        resp.raise_for_status()

        pc = RTCPeerConnection()
        pc.addTransceiver("video")
        pc.addTransceiver("audio")
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        resp = await client.post(
            "/offer",
            json={"sdp": pc.localDescription.sdp, "type": pc.localDescription.type},
        )
        resp.raise_for_status()
        answer = resp.json()
        await pc.setRemoteDescription(
            RTCSessionDescription(sdp=answer["sdp"], type=answer["type"])
        )
        await pc.close()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Check Spiral OS on Vast.ai")
    parser.add_argument(
        "base_url",
        nargs="?",
        default="http://localhost:8000",
        help="Base URL of the running server",
    )
    args = parser.parse_args()
    try:
        await perform_check(args.base_url.rstrip("/"))
    except Exception as exc:  # pragma: no cover - network failures vary
        print(f"Check failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
    else:
        print("Server is ready")


if __name__ == "__main__":
    asyncio.run(main())
