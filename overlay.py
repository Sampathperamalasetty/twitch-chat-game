"""FastAPI routes and WebSocket fan-out for the browser overlay."""

import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, Response
from starlette.concurrency import run_in_threadpool

from canvas import Canvas
from export_timelapse import build_timelapse
from theme import ThemeStore


OVERLAY_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Chat Canvas Overlay</title>
  <style>
    * { box-sizing: border-box; }
    html, body { margin: 0; width: 100%; height: 100%; background: transparent; }
    body { display: grid; place-items: center; overflow: hidden; font-family: sans-serif; }
    #canvas { width: min(640px, 92vw, 92vh); height: min(640px, 92vw, 92vh); image-rendering: pixelated; }
    #last-chatter { position: fixed; left: 50%; bottom: 18px; transform: translateX(-50%);
      color: white; background: #111c; border-radius: 5px; padding: 7px 12px;
      font-size: 16px; opacity: 0; transition: opacity 700ms ease; pointer-events: none; }
    #last-chatter.visible { opacity: 1; }
    #theme-banner { position: fixed; top: 18px; left: 50%; transform: translateX(-50%);
      max-width: 90vw; color: white; background: #111c; border-radius: 5px;
      padding: 9px 16px; font-size: 22px; font-weight: 700; text-align: center;
      opacity: 0; transition: opacity 250ms ease; pointer-events: none; }
    #theme-banner.visible { opacity: 1; }
  </style>
</head>
<body>
  <canvas id="canvas" width="640" height="640" aria-label="64 by 64 pixel canvas"></canvas>
  <div id="theme-banner"></div>
  <div id="last-chatter"></div>
  <script>
    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');
    const label = document.getElementById('last-chatter');
    const themeBanner = document.getElementById('theme-banner');
    const cell = 10;
    let fadeTimer;
    function updateTheme(theme) {
      themeBanner.textContent = theme || '';
      themeBanner.classList.toggle('visible', Boolean(theme));
    }
    function showChatter(username) {
      if (!username) return;
      label.textContent = `${username} placed a pixel`;
      label.classList.add('visible');
      clearTimeout(fadeTimer);
      fadeTimer = setTimeout(() => label.classList.remove('visible'), 2600);
    }
    function drawSnapshot(pixels, lastUsername, theme) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (let y = 0; y < 64; y++) {
        for (let x = 0; x < 64; x++) {
          if (pixels[y][x]) {
            ctx.fillStyle = pixels[y][x];
            ctx.fillRect(x * cell, y * cell, cell, cell);
          }
        }
      }
      showChatter(lastUsername);
      updateTheme(theme);
    }
    function connect() {
      const scheme = location.protocol === 'https:' ? 'wss' : 'ws';
      const socket = new WebSocket(`${scheme}://${location.host}/ws`);
      socket.onmessage = ({ data }) => {
        const message = JSON.parse(data);
        if (message.type === 'snapshot') drawSnapshot(message.pixels, message.last_username, message.theme);
        if (message.type === 'pixel') {
          ctx.fillStyle = message.color;
          ctx.fillRect(message.x * cell, message.y * cell, cell, cell);
          showChatter(message.username);
        }
        if (message.type === 'theme') updateTheme(message.theme);
      };
      socket.onclose = () => setTimeout(connect, 1000);
    }
    connect();
  </script>
</body>
</html>"""


def create_app(canvas: Canvas, theme_store: ThemeStore) -> FastAPI:
    app = FastAPI(title="Chat Canvas Overlay")
    clients: set[asyncio.Queue] = set()

    @app.get("/overlay", response_class=HTMLResponse)
    async def overlay_page() -> HTMLResponse:
        return HTMLResponse(OVERLAY_HTML)

    @app.get("/timelapse.gif")
    async def timelapse_gif() -> Response:
        gif_data = await run_in_threadpool(build_timelapse, canvas.log_path)
        return Response(
            content=gif_data,
            media_type="image/gif",
            headers={"Cache-Control": "no-store"},
        )

    @app.websocket("/ws")
    async def overlay_websocket(websocket: WebSocket) -> None:
        await websocket.accept()
        queue: asyncio.Queue = asyncio.Queue()
        clients.add(queue)
        try:
            snapshot = canvas.snapshot()
            snapshot["theme"] = theme_store.theme
            await websocket.send_json(snapshot)
            while True:
                await websocket.send_json(await queue.get())
        except WebSocketDisconnect:
            pass
        finally:
            clients.discard(queue)

    async def broadcast_pixel(record: dict) -> None:
        message = {"type": "pixel", **record}
        for queue in tuple(clients):
            queue.put_nowait(message)

    async def broadcast_theme(theme: str) -> None:
        message = {"type": "theme", "theme": theme}
        for queue in tuple(clients):
            queue.put_nowait(message)

    app.state.broadcast_pixel = broadcast_pixel
    app.state.broadcast_theme = broadcast_theme
    return app
