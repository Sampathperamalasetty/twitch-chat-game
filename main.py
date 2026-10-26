"""Application entry point for Chat Canvas."""

import asyncio

from bot import run_bot
from canvas import Canvas
from config import load_settings


def main() -> None:
    settings = load_settings()
    asyncio.run(run_bot(settings, Canvas()))


if __name__ == "__main__":
    main()
