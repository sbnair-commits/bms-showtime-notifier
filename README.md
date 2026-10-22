# BookMyShow Ticket Tracker

A lightweight Python script that watches BookMyShow for a movie at one or more theatres and sends a Telegram alert the moment bookings open for your chosen date.

> **Disclaimer:** This project uses BookMyShow's unofficial, undocumented API. It can change or block you at any time. It is for personal use only. Keep the check interval polite (the default is 5 minutes) and don't use it to hammer the site.

## Features

- **Multi-theatre monitoring:** Checks every theatre listed in the `VENUES` dict, one after another.
- **Date-exact matching:** Only alerts when shows exist for your `TARGET_DATE`, so a movie already running on another day doesn't cause a false alarm.
- **Instant Telegram alerts:** Includes the theatre name and the show times.
- **No duplicate alerts:** Alerted theatres are saved to `alerted.json`, so a reboot doesn't repeat them.
- **Clean exit:** Stops by itself once every theatre has alerted.
- **No secrets in code:** Credentials are read from environment variables.

## Prerequisites

- Python 3.8+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Your numeric Telegram chat ID (for example from [@userinfobot](https://t.me/userinfobot))
- **Send your bot a `/start` message once.** Telegram refuses to deliver messages to someone who hasn't started a chat with the bot.

## Installation

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install requests
```

The script only needs `requests`; everything else is in the standard library.

> On Raspberry Pi OS (Debian 12+), plain `pip install` fails with `externally-managed-environment`. Use the virtual environment above.

## Configuration

### 1. Environment variables

| Variable | Required | Description |
|---|---|---|
| `TG_TOKEN` | Yes | Telegram bot token from @BotFather |
| `TG_CHAT_ID` | Yes | Your numeric Telegram chat ID |
| `BMS_ID` | Yes | The `bmsId` value from a BookMyShow request (see below) |
| `BMS_TOKEN` | Yes | The `token` value from the same request |

Linux / Raspberry Pi / macOS:
```bash
export TG_TOKEN=your_bot_token
export TG_CHAT_ID=your_chat_id
export BMS_ID=your_bms_id
export BMS_TOKEN=your_bms_token
```

Windows Command Prompt (**no quotes**, they become part of the value and cause errors):
```cmd
set TG_TOKEN=your_bot_token
set TG_CHAT_ID=your_chat_id
set BMS_ID=your_bms_id
set BMS_TOKEN=your_bms_token
```

Never commit these values. If a token ever lands in a commit, revoke it with @BotFather (`/revoke`); deleting it from the file is not enough because it stays in git history.

### 2. Movie, region, date and theatres

Edit the settings at the top of `bms_scraper.py`:

| Setting | Meaning |
|---|---|
| `MOVIE_CODE` | Event code, e.g. `ET00518674` |
| `MOVIE_NAME` | Name shown in the alert |
| `REGION_CODE` | City code, e.g. `TRIV` for Trivandrum |
| `TARGET_DATE` | `YYYYMMDD`. Must be today or later; a past date never alerts |
| `VENUES` | Dict of `venue_code: display name` for each theatre to watch |
| `CHECK_EVERY_SECONDS` | Delay between rounds (default 300) |

### 3. Finding the codes

- **Movie code and region code:** open the movie page on BookMyShow. The URL looks like `.../movies/<city>/<movie-name>/ET00518674`. The `ET...` part is the movie code.
- **Venue codes:** open a theatre's page or its showtimes view. The 4-letter code appears in the URL and in the network requests.
- **`bmsId` and `token`:** open your browser's developer tools (F12, Network tab) on a BookMyShow showtimes page, find the `showtimes/byvenue` request, and copy the `bmsId` and `token` query parameters. They are tied to your browser session and may expire. If you start getting `403` or empty results, grab fresh ones.

## Usage

```bash
python bms_scraper.py
```

Example output:
```
Querying ATYY for 20261022...
[ATYY] No showtimes for this movie yet.
Querying PMNK for 20261022...
[PMNK] No showtimes for this movie yet.
```

To test the pipeline end to end, temporarily set `TARGET_DATE` to a day when the movie is already showing at one of your venues. You should receive a Telegram message. Then delete `alerted.json` and set the real date back.

## Running in the background on a Raspberry Pi

### Quick option: tmux

```bash
sudo apt install tmux
tmux new -s tracker
source venv/bin/activate
python bms_scraper.py
```

Detach with `Ctrl + B`, then `D`. Reattach with `tmux attach -t tracker`. This does not survive a reboot.

### Recommended: systemd service (starts on boot)

1. Store the secrets in a private file:
   ```bash
   nano ~/bms.env
   ```
   ```
   TG_TOKEN=your_bot_token
   TG_CHAT_ID=your_chat_id
   BMS_ID=your_bms_id
   BMS_TOKEN=your_bms_token
   ```
   ```bash
   chmod 600 ~/bms.env
   ```

2. Create the service file:
   ```bash
   sudo nano /etc/systemd/system/bms-scraper.service
   ```
   Replace `<user>` and `<repo>` with your own values:
   ```ini
   [Unit]
   Description=BookMyShow Ticket Tracker
   After=network-online.target
   Wants=network-online.target

   [Service]
   Type=simple
   User=<user>
   WorkingDirectory=/home/<user>/<repo>
   EnvironmentFile=/home/<user>/bms.env
   ExecStart=/home/<user>/<repo>/venv/bin/python -u bms_scraper.py
   Restart=on-failure
   RestartSec=30

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start it:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now bms-scraper
   ```

Useful commands:

```bash
sudo systemctl status bms-scraper     # is it running?
journalctl -u bms-scraper -f          # live logs (Ctrl + C to stop watching)
sudo systemctl restart bms-scraper    # after editing the script or settings
sudo systemctl disable --now bms-scraper   # stop it and stop it starting on boot
```

The script exits cleanly after all theatres have alerted, and systemd won't restart a clean exit.

## Troubleshooting

| Problem | Likely cause and fix |
|---|---|
| `TG_TOKEN is not set` | The variable isn't exported in this shell or isn't in your `EnvironmentFile`. |
| Telegram error `404` | Wrong or revoked token, or stray quotes, spaces, or a `bot` prefix in the value. |
| Telegram error `400` / no message | You haven't sent `/start` to the bot, or the chat ID is wrong. |
| Status `403` from BookMyShow | `bmsId`/`token` expired or your IP is being blocked. Refresh them and keep the interval at 5 minutes or more. |
| Never alerts | `TARGET_DATE` is in the past or not open yet, or the venue/movie code is wrong. |
| Immediate alert for the wrong day | Make sure you are running the version that matches `Date` and `ShowTimes` for `TARGET_DATE` (this one does). |
| Script exits immediately with "All theatres alerted" | `alerted.json` remembers earlier alerts. Delete it, or change the movie or date. |
| `externally-managed-environment` on `pip install` | Use a virtual environment (see Installation). |

## How it works

For each theatre, the script calls the `showtimes/byvenue` endpoint, finds the entry for `TARGET_DATE` and that venue, then looks for your `MOVIE_CODE` with a non-empty `ShowTimes` list. If found, it sends a Telegram message and records the theatre in `alerted.json`.

## License

Distributed under the MIT License. See `LICENSE` for details.
