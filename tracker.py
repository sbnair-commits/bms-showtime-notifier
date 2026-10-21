import json
import os
import sys
import time
import requests

# --- SETTINGS ---
MOVIE_CODE = "ET00518674"
MOVIE_NAME = "Jailer 2"
REGION_CODE = "TRIV"
TARGET_DATE = "20261022"     # YYYYMMDD -- update this; a past date never alerts
CHECK_EVERY_SECONDS = 300    # 5 minutes between rounds
PAUSE_BETWEEN_THEATRES = 2   # seconds between requests inside a round

# venue code -> name shown in the alert. Add or remove theatres here.
VENUES = {
    "ATYY": "ANAND theatre",
    "PMNK": "PVR Mymoon, Kochi",
}

TELEGRAM_BOT_TOKEN = os.environ.get("TG_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TG_CHAT_ID", "7437236512")

# Remembers which theatres have already alerted, so a reboot doesn't repeat them.
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alerted.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://in.bookmyshow.com/",
    "Accept": "application/json",
}


def state_key(venue_code):
    # Movie + date + venue, so changing the movie or date starts fresh automatically.
    return f"{MOVIE_CODE}:{TARGET_DATE}:{venue_code}"


def load_alerted():
    """Returns the set of venue codes already alerted for the current movie and date."""
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            saved = set(json.load(f))
    except FileNotFoundError:
        return set()
    except Exception as e:
        print(f"Could not read {STATE_FILE} ({e}); starting with no alerts recorded.", flush=True)
        return set()
    return {code for code in VENUES if state_key(code) in saved}


def save_alerted(alerted):
    """Writes the alerted set to disk. Keeps entries for other movies/dates untouched."""
    try:
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                saved = set(json.load(f))
        except Exception:
            saved = set()
        saved |= {state_key(code) for code in alerted}
        tmp_path = STATE_FILE + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(sorted(saved), f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, STATE_FILE)  # atomic, safe against a power cut mid-write
    except Exception as e:
        print(f"Warning: could not save alert state: {e}", flush=True)


def build_url(venue_code):
    return (
        "https://in.bookmyshow.com/api/v3/mobile/showtimes/byvenue"
        f"?dateCode={TARGET_DATE}&venueCode={venue_code}&regionCode={REGION_CODE}"
        "&memberId=&bmsId=1.267608125.1791543964158&appCode=WEBV2"
        "&token=26x3aab5x746514b3b7b&lsId="
    )


def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            print("Telegram notification sent!", flush=True)
            return True
        print(f"Telegram error code: {res.status_code} {res.text}", flush=True)
    except Exception as e:
        print(f"Failed to reach Telegram: {e}", flush=True)
    return False


def check_venue(venue_code):
    """Returns a list of show times if the movie is bookable at this venue, else None."""
    print(f"Querying {venue_code} for {TARGET_DATE}...", flush=True)
    try:
        response = requests.get(build_url(venue_code), headers=HEADERS, timeout=15)
    except Exception as e:
        print(f"[{venue_code}] Request failed: {e}", flush=True)
        return None

    if response.status_code != 200:
        print(f"[{venue_code}] Endpoint returned status code: {response.status_code}", flush=True)
        return None

    try:
        data = response.json()
    except Exception as e:
        print(f"[{venue_code}] Could not parse response: {e}", flush=True)
        return None

    for day in data.get("ShowDetails", []):
        if day.get("Date") != TARGET_DATE:
            continue
        if day.get("Venues", {}).get("VenueCode") != venue_code:
            continue
        for event in day.get("Event", []):
            for child in event.get("ChildEvents", []):
                if child.get("EventCode") == MOVIE_CODE and child.get("ShowTimes"):
                    return [s["ShowTime"] for s in child["ShowTimes"]]

    print(f"[{venue_code}] No showtimes for this movie yet.", flush=True)
    return None


def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TG_TOKEN is not set.", flush=True)
        sys.exit(1)

    alerted = load_alerted()
    if alerted:
        print(f"Already alerted earlier: {', '.join(sorted(alerted))}", flush=True)

    while True:
        if alerted == set(VENUES):
            print("All theatres alerted. Exiting.", flush=True)
            break  # clean exit; systemd won't restart it

        for code, name in VENUES.items():
            if code in alerted:
                continue
            shows = check_venue(code)
            if shows:
                msg = (
                    f"🚨 *ALERT!* Bookings are *OPEN* for *{MOVIE_NAME}* at *{name}* "
                    f"on {TARGET_DATE}!\nShows: {', '.join(shows)} 🎟️"
                )
                if send_telegram_alert(msg):
                    alerted.add(code)
                    save_alerted(alerted)  # saved immediately, before the next check
            time.sleep(PAUSE_BETWEEN_THEATRES)

        if alerted == set(VENUES):
            continue  # loop back to the exit check without waiting
        time.sleep(CHECK_EVERY_SECONDS)


if __name__ == "__main__":
    main()
