"""Environment-backed application configuration."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    client_id: str
    client_secret: str
    channel: str
    pixel_cooldown_seconds: float = 5.0


def load_settings() -> Settings:
    load_dotenv()
    required = {
        "TWITCH_CLIENT_ID": os.getenv("TWITCH_CLIENT_ID"),
        "TWITCH_CLIENT_SECRET": os.getenv("TWITCH_CLIENT_SECRET"),
        "TWITCH_CHANNEL": os.getenv("TWITCH_CHANNEL"),
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(
            "Missing required .env setting(s): " + ", ".join(missing)
        )
    try:
        cooldown = float(os.getenv("PIXEL_COOLDOWN_SECONDS", "5"))
    except ValueError as error:
        raise RuntimeError("PIXEL_COOLDOWN_SECONDS must be a number") from error
    if cooldown < 0:
        raise RuntimeError("PIXEL_COOLDOWN_SECONDS must be zero or greater")
    return Settings(
        client_id=required["TWITCH_CLIENT_ID"],
        client_secret=required["TWITCH_CLIENT_SECRET"],
        channel=required["TWITCH_CHANNEL"].lstrip("#").strip(),
        pixel_cooldown_seconds=cooldown,
    )
