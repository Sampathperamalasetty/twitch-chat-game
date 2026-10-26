"""In-memory 64x64 canvas and pixel validation/persistence."""

from datetime import datetime, timezone
import json
import re
from pathlib import Path
from threading import Lock


WIDTH = 64
HEIGHT = 64
KNOWN_COLORS = {
    "red", "blue", "green", "yellow", "orange", "purple", "pink",
    "white", "black", "cyan",
}
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


class Canvas:
    def __init__(self, log_path: Path | str = "pixels.jsonl") -> None:
        self.pixels: list[list[str | None]] = [
            [None for _ in range(WIDTH)] for _ in range(HEIGHT)
        ]
        self.log_path = Path(log_path)
        self._lock = Lock()
        self.last_username: str | None = None
        self._load_history()

    def _load_history(self) -> None:
        """Replay valid pixel records so the canvas survives restarts."""
        if not self.log_path.exists():
            return
        try:
            with self.log_path.open("r", encoding="utf-8") as log_file:
                for line in log_file:
                    try:
                        record = json.loads(line)
                        username = record["username"]
                        x, y = int(record["x"]), int(record["y"])
                        raw_color = record["color"]
                        color = (
                            self.normalize_color(raw_color)
                            if isinstance(raw_color, str)
                            else None
                        )
                    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                        continue
                    if isinstance(username, str) and 0 <= x < WIDTH and 0 <= y < HEIGHT and color:
                        self.pixels[y][x] = color
                        self.last_username = username
        except OSError as error:
            print(f"Could not load pixel history from {self.log_path}: {error}")

    @staticmethod
    def normalize_color(color: str) -> str | None:
        value = color.lower()
        if value in KNOWN_COLORS:
            return value
        if HEX_COLOR.fullmatch(color):
            return color.lower()
        return None

    def place_pixel(self, username: str, x: int, y: int, color: str) -> dict | None:
        normalized_color = self.normalize_color(color)
        if not (0 <= x < WIDTH and 0 <= y < HEIGHT) or normalized_color is None:
            return None

        record = {
            "username": username,
            "x": x,
            "y": y,
            "color": normalized_color,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with self._lock:
            self.pixels[y][x] = normalized_color
            self.last_username = username
            with self.log_path.open("a", encoding="utf-8") as log_file:
                log_file.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def snapshot(self) -> dict:
        """Return a copy of the current state suitable for overlay clients."""
        with self._lock:
            return {
                "type": "snapshot",
                "pixels": [row.copy() for row in self.pixels],
                "last_username": self.last_username,
            }
