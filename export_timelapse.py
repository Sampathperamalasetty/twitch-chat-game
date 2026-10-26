"""Build a 512x512 animated GIF from the ordered pixel history."""

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw

from canvas import HEIGHT, WIDTH, Canvas


OUTPUT_SIZE = 512
TARGET_DURATION_MS = 12_000
MAX_DRAWING_FRAMES = 60


def read_pixel_history(log_path: Path | str = "pixels.jsonl") -> list[tuple[int, int, str]]:
    """Read valid placements in log order, skipping malformed lines."""
    path = Path(log_path)
    if not path.exists():
        return []

    records: list[tuple[int, int, str]] = []
    with path.open("r", encoding="utf-8") as log_file:
        for line in log_file:
            try:
                record = json.loads(line)
                x, y = int(record["x"]), int(record["y"])
                raw_color = record["color"]
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                continue
            color = Canvas.normalize_color(raw_color) if isinstance(raw_color, str) else None
            if 0 <= x < WIDTH and 0 <= y < HEIGHT and color is not None:
                records.append((x, y, color))
    return records


def build_timelapse(log_path: Path | str = "pixels.jsonl") -> bytes:
    """Return the GIF bytes, batching placements across roughly 12 seconds."""
    records = read_pixel_history(log_path)
    batch_size = max(1, math.ceil(len(records) / MAX_DRAWING_FRAMES))
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)
    frames = [image.resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.Resampling.NEAREST)]

    for start in range(0, len(records), batch_size):
        for x, y, color in records[start : start + batch_size]:
            draw.point((x, y), fill=color)
        frames.append(image.resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.Resampling.NEAREST))

    frame_duration = max(1, round(TARGET_DURATION_MS / len(frames)))
    from io import BytesIO

    output = BytesIO()
    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=frame_duration,
        loop=0,
        disposal=2,
        optimize=False,
    )
    return output.getvalue()


def export_timelapse(
    log_path: Path | str = "pixels.jsonl",
    output_path: Path | str = "timelapse.gif",
) -> Path:
    """Generate and save timelapse.gif, returning its path."""
    destination = Path(output_path)
    destination.write_bytes(build_timelapse(log_path))
    return destination


if __name__ == "__main__":
    result = export_timelapse()
    print(f"Saved timelapse to {result.resolve()}")
