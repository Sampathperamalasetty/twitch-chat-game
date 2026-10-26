"""Persistent overlay theme state."""

import json
from pathlib import Path


class ThemeStore:
    def __init__(self, path: Path | str = "theme.json") -> None:
        self.path = Path(path)
        self.theme = ""
        self._load()

    def _load(self) -> None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            value = data.get("theme", "") if isinstance(data, dict) else ""
            if isinstance(value, str):
                self.theme = value
        except FileNotFoundError:
            pass
        except (OSError, json.JSONDecodeError):
            print(f"Could not read theme from {self.path}; using an empty theme.")

    def set(self, value: str) -> None:
        self.theme = value
        self.path.write_text(
            json.dumps({"theme": value}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
