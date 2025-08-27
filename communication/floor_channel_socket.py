from __future__ import annotations

"""Socket.IO server managing floor and channel rooms."""

import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

socket_app = socketio.ASGIApp(sio)


@sio.event
async def connect(sid, environ):
    """Handle client connection."""
    # connection established; no-op
    return None


@sio.on("join")
async def on_join(sid, data):
    """Join a floor/channel room."""
    floor = data.get("floor")
    channel = data.get("channel")
    if not floor or not channel:
        return
    room = f"{floor}:{channel}"
    sio.enter_room(sid, room)
    await sio.emit("joined", {"floor": floor, "channel": channel}, room=sid)


@sio.on("message")
async def on_message(sid, data):
    """Broadcast ``message`` to all peers in the room."""
    floor = data.get("floor")
    channel = data.get("channel")
    message = data.get("message")
    if not (floor and channel and message):
        return
    room = f"{floor}:{channel}"
    await sio.emit(
        "message",
        {"floor": floor, "channel": channel, "message": message},
        room=room,
    )


__all__ = ["socket_app"]
