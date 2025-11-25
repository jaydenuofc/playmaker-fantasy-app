from flask import Flask, jsonify
from flask_cors import CORS
from espn_api.football import League
import os

app = Flask(__name__)
CORS(app)

# Mapping between your front-end IDs and ESPN names
ID_TO_NAME = {
    1:  "Jacksonville Jaguars D/ST",  # adjust if ESPN uses a slightly different name
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


def espn_status_to_frontend(es_status: str) -> str:
    """Convert ESPN injury status into 'healthy' / 'questionable' / 'out'."""
    if not es_status:
        return "healthy"
    s = es_status.upper()
    if s in ("OUT", "IR", "SUSPENSION", "PUP", "COVID-19"):
        return "out"
    if s in ("Q", "QUESTIONABLE", "D", "DOUBTFUL", "P", "PROBABLE"):
        return "questionable"
    return "healthy"


def get_league():
    """Create a League object from env vars. Raises if misconfigured."""
    league_id = int(os.getenv("LEAGUE_ID", "0"))
    year = int(os.getenv("YEAR", "2024"))
    swid = os.getenv("ESPN_SWID")
    espn_s2 = os.getenv("ESPN_S2")

    if league_id == 0:
        raise ValueError("LEAGUE_ID is not set in environment variables")

    # Private league (needs cookies)
    if swid and espn_s2:
        return League(league_id=league_id, year=year, swid=swid, espn_s2=espn_s2)

    # Public league
    return League(league_id=league_id, year=year)


@app.get("/api/injuries")
def injuries():
    try:
        league = get_league()
    except Exception as e:
        # App stays alive; you see this in logs and frontend gets a JSON error
        app.logger.exception("Error creating ESPN League")
        return jsonify({
            "error": "League configuration problem",
            "details": str(e)
        }), 500

    updates = []
    for team in league.teams:
        for p in team.roster:
            name = p.name
            if name not in NAME_TO_ID:
                continue

            front_id = NAME_TO_ID[name]
            injury_status = getattr(p, "injuryStatus", "")
            frontend_status = espn_status_to_frontend(injury_status)

            updates.append({"id": front_id, "status": frontend_status})

    return jsonify(updates)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
