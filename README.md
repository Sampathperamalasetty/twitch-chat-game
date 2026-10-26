# Chat Canvas

A Twitch chat game that listens for `!pixel x y color`, updates a 64×64 canvas,
and streams placements to a live browser overlay. The canvas is restored from
`pixels.jsonl` when the app starts.

## Windows setup

1. Install Python 3.10 or newer and create a Twitch application in the
   [Twitch Developer Console](https://dev.twitch.tv/console/apps). Set its
   OAuth Redirect URL to exactly `http://localhost:17563`.
2. Open PowerShell in this repository and create/activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install the Python dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and fill in your Twitch application's client
   ID and client secret, plus the channel login name to join (without `#`):

   ```powershell
   Copy-Item .env.example .env
   notepad .env
   ```

   Keep `.env` private; it is ignored by git. `PIXEL_COOLDOWN_SECONDS` is
   optional and defaults to `5`. Set it to `0` to disable the per-chatter
   pixel cooldown.
5. Start the bot:

   ```powershell
   python main.py
   ```

   On first start, a browser opens for Twitch user authorization. Authorize
   chat read access, then keep the terminal running. Use the Twitch account
   that should authenticate the bot and ensure it can access the target chat.
6. Open the overlay in a browser at <http://localhost:8000/overlay>. It has a
   transparent background and reconnects to the local WebSocket automatically.
7. To add it to OBS, add a **Browser Source** and set its URL to
   `http://localhost:8000/overlay`, width to **700**, and height to **700**.
   Keep `python main.py` running while the source is in use.
8. In the configured channel, type for example:

   ```text
   !pixel 10 20 red
   ```

   Each chatter can place one pixel every five seconds by default. Extra
   attempts during the cooldown are silently ignored. The delay can be changed
   with `PIXEL_COOLDOWN_SECONDS` in `.env`.

   The broadcaster can set the overlay banner by typing a theme, including
   spaces, for example:

   ```text
   !theme Draw a cat
   ```

   Only a message from the configured channel's broadcaster account changes
   the theme. Use `!theme` with no text to clear it. The theme is saved in
   `theme.json` and restored on restart.

   Valid coordinates are 0 through 63. Colors can be `red`, `blue`, `green`,
   `yellow`, `orange`, `purple`, `pink`, `white`, `black`, `cyan`, or a six-digit
   hex value such as `#ff0000`. Invalid commands are silently ignored. Each
   accepted placement is printed in the terminal and appended as one JSON
   object per line to `pixels.jsonl`.

Each accepted pixel appears on the overlay immediately, and the most recent
chatter is shown briefly near the bottom. Press Ctrl+C to stop both the bot and
the overlay server. `pixels.jsonl` is the append-only placement history used to
restore the canvas on the next start.

## Timelapse GIF

With the virtual environment active, generate `timelapse.gif` from the saved
pixel history by running:

```powershell
python export_timelapse.py
```

While `python main.py` is running, the server can generate and display the
current timelapse at <http://localhost:8000/timelapse.gif>. The export has a
white background, sharp 512×512 pixels, and takes about 12 seconds to play.
