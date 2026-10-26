# Chat Canvas (step 1)

A small Twitch chat bot that listens for `!pixel x y color`, updates a 64×64
in-memory canvas, and appends valid placements to `pixels.jsonl`.

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

   Keep `.env` private; it is ignored by git.
5. Start the bot:

   ```powershell
   python main.py
   ```

   On first start, a browser opens for Twitch user authorization. Authorize
   chat read access, then keep the terminal running. Use the Twitch account
   that should authenticate the bot and ensure it can access the target chat.
6. In the configured channel, type for example:

   ```text
   !pixel 10 20 red
   ```

   Valid coordinates are 0 through 63. Colors can be `red`, `blue`, `green`,
   `yellow`, `orange`, `purple`, `pink`, `white`, `black`, `cyan`, or a six-digit
   hex value such as `#ff0000`. Invalid commands are silently ignored. Each
   accepted placement is printed in the terminal and appended as one JSON
   object per line to `pixels.jsonl`.

Press Ctrl+C to stop the bot. The canvas itself is currently held in memory;
the JSONL file is the append-only placement history.
