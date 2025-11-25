import os
import requests
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ========================
#  CONFIGURATION
# ========================

# Your API-Sports NFL key (we'll set this in Render)
API_KEY = os.getenv("API_SPORTS_KEY")

# NFL league + season used by API-Sports
# You can later move these to env vars if you want
LEAGUE_ID = os.getenv("NFL_LEAGUE_ID", "1")  # 1 = NFL in API-Sports
SEASON = os.getenv("NFL_SEASON", "2024")

API_BASE = "https://v1.american-football.api-sports.io"

# Mapping between your front-end IDs and player names
ID_TO_NAME = {
    1:  "Jacksonville Jaguars D/ST",  # adjust to exact naming if needed
    2:  "Jalen Hurts",
    3:  "Puka Nacua",
    4:  "George Pickens",
    5:  "Bijan Robinson",
    6:  "Jaylen Warren",
    7:  "Jake Ferguson",
    8:  "Zach Charbonnet",
    9:  "Kenneth Gainwell",
    10: "Chris Boswell",
    11: "Bucky Irving",
    12: "Mark Andrews",
    13: "Michael Pittman Jr.",
    14: "J.K. Dobbins",
    15: "Jared Goff",
    16: "J.J. McCarthy",
    17: "T. Hunter",
}

NAME_TO_ID = {name: pid for pid, name in ID_TO_NAME.items()}


# ========================
#  HELPERS
# ========================

def status_to_bucket(raw_status: str) -> str:
    """
    Map raw injury status text from the API into:
      - 'healthy'
      - 'questionable'
      - 'out'
    """
    if not raw_status:
        return "healthy"

    s = raw_status.upper()

    # Very conservative mapping – tweak as you see real data
    if any(word in s for word in ["OUT", "IR", "INJURED RESERVE"]):
        return "out"
    if any(word in s for word in ["Q", "QUESTIONABLE", "DOUBTFUL", "PROBABLE", "DAY-TO-DAY"]):
        return "questionable"
    return "healthy"


# ========================
#  ROUTES
# ========================

@app.get("/api/injuries")
def injuries():
    """
    Returns JSON like:
      [
        {"id": 2, "status": "healthy"},
        {"id": 3, "status": "questionable"},
        ...
      ]
    where "id" is your front-end player id.
    """
    if not API_KEY:
        return jsonify({"error": "API_SPORTS_KEY not set in environment"}), 500

    headers = {"x-apisports-key": API_KEY}
    params = {
        "league": LEAGUE_ID,
        "season": SEASON,
        # You can add team filters later if needed
    }

    try:
        resp = requests.get(f"{API_BASE}/injuries", headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as e:
        app.logger.exception("Error calling API-Sports injuries endpoint")
        return jsonify({"error": "Failed to call API-Sports", "details": str(e)}), 500

    # NOTE: The exact shape of payload depends on API-Sports.
    # Common pattern: payload["response"] is a list of injury objects.
    name_to_status = {}

    for item in payload.get("response", []):
        # You may need to adjust these keys after you see a real response.
        player = item.get("player", {})       # e.g. {"name": "Jalen Hurts", ...}
        injury = item.get("injury", {})       # e.g. {"status": "Questionable", ...}

        name = player.get("name")
        raw_status = injury.get("status") or injury.get("type") or ""

        if not name:
            continue

        bucket = status_to_bucket(raw_status)
        # Last one wins if duplicates
        name_to_status[name] = bucket

    # Build the list of updates for YOUR roster
    updates = []
    for pid, name in ID_TO_NAME.items():
        # default to healthy if not mentioned in the injury list
        status = name_to_status.get(name, "healthy")
        updates.append({"id": pid, "status": status})

    return jsonify(updates)


if __name__ == "__main__":
    # Local testing: python backend.py
    app.run(debug=True, host="0.0.0.0", port=5000)
