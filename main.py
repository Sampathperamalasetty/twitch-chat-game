"""Application entry point for Chat Canvas."""

import asyncio

import uvicorn

from bot import run_bot
from canvas import Canvas
from config import load_settings
from overlay import create_app
from theme import ThemeStore


async def run() -> None:
    settings = load_settings()
    canvas = Canvas()
    theme_store = ThemeStore()
    app = create_app(canvas, theme_store)
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8000))
    server_task = asyncio.create_task(server.serve())
    try:
        await run_bot(
            settings,
            canvas,
            theme_store,
            app.state.broadcast_pixel,
            app.state.broadcast_theme,
        )
    finally:
        server.should_exit = True
        await server_task


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
