"""Twitch chat connection and !pixel command handling."""

import asyncio
import json
import re
import time

from twitchAPI.chat import Chat, ChatMessage, EventData
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.twitch import Twitch

from canvas import Canvas
from config import Settings
from theme import ThemeStore


OAUTH_REDIRECT_URL = "http://localhost:17563"
PIXEL_COMMAND = re.compile(r"^!pixel\s+(\S+)\s+(\S+)\s+(\S+)\s*$", re.IGNORECASE)
CHAT_SCOPES = [AuthScope.CHAT_READ]


def parse_pixel_command(message: str) -> tuple[int, int, str] | None:
    match = PIXEL_COMMAND.fullmatch(message.strip())
    if not match:
        return None
    try:
        x, y = int(match.group(1)), int(match.group(2))
    except ValueError:
        return None
    color = match.group(3)
    if not (0 <= x <= 63 and 0 <= y <= 63):
        return None
    if Canvas.normalize_color(color) is None:
        return None
    return x, y, color


async def run_bot(
    settings: Settings,
    canvas: Canvas,
    theme_store: ThemeStore,
    on_pixel=None,
    on_theme=None,
) -> None:
    twitch = await Twitch(settings.client_id, settings.client_secret)
    chat = None
    try:
        authenticator = UserAuthenticator(
            twitch, CHAT_SCOPES, url=OAUTH_REDIRECT_URL
        )
        access_token, refresh_token = await authenticator.authenticate()
        await twitch.set_user_authentication(
            access_token, CHAT_SCOPES, refresh_token
        )
        chat = await Chat(twitch)
        last_pixel_at: dict[str, float] = {}

        async def on_ready(event: EventData) -> None:
            print(f"Connected to Twitch chat; joining #{settings.channel}.")
            await event.chat.join_room(settings.channel)

        async def on_message(message: ChatMessage) -> None:
            theme_match = re.match(r"^!theme(?:\s+(.*))?$", message.text.strip(), re.IGNORECASE)
            if theme_match is not None:
                if message.user.name.casefold() != settings.channel.casefold():
                    return
                theme = (theme_match.group(1) or "").strip()
                theme_store.set(theme)
                print(f"Theme updated: {theme or '(cleared)'}")
                if on_theme is not None:
                    await on_theme(theme)
                return

            parsed = parse_pixel_command(message.text)
            if parsed is None:
                return
            user_key = str(getattr(message.user, "id", "") or message.user.name).casefold()
            now = time.monotonic()
            previous = last_pixel_at.get(user_key)
            if previous is not None and now - previous < settings.pixel_cooldown_seconds:
                return
            x, y, color = parsed
            record = canvas.place_pixel(message.user.name, x, y, color)
            if record is not None:
                last_pixel_at[user_key] = now
                print(json_record(record))
                if on_pixel is not None:
                    await on_pixel(record)

        chat.register_event(ChatEvent.READY, on_ready)
        chat.register_event(ChatEvent.MESSAGE, on_message)
        chat.start()
        print("Press Ctrl+C to stop the bot.")
        await asyncio.Event().wait()
    finally:
        if chat is not None:
            chat.stop()
        await twitch.close()


def json_record(record: dict) -> str:
    """Format a placed pixel as a compact terminal-friendly JSON object."""
    return json.dumps(record, ensure_ascii=False)
