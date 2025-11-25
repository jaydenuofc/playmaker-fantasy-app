from flask import Flask, jsonify
from flask_cors import CORS
from espn_api.football import League
import os

app = Flask(__name__)
CORS(app)  # allow requests from your GitHub Pages site

# 1. ESPN league configuration (fill these via env vars on Render later)
LEAGUE_ID = int(os.getenv("LEAGUE_ID", "123456"))  # temporary default
YEAR = int(os.getenv("YEAR", "2024"))

SWID = os.getenv("ESPN_SWID")   # for private leagues
ESPN_S2 = os.getenv("ESPN_S2")  # for private leagues

if SWID and ESPN_S2:
    league = League(league_id=LEAGUE_ID, year=YEAR, swid=SWID, espn_s2=ESPN_S2)
else:
    league = League(league_id=LEAGUE_ID, year=YEAR)

# 2. Mapping between your front-end IDs and ESPN names
ID_TO_NAME = {
    1:  "Jacksonville Jaguars D/ST",  # adjust to exact ESPN name if needed
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
    17: "T. Hunter",  # update once you know ESPN’s exact name
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


@app.get("/api/injuries")
def injuries():
    """
    JSON: [ { "id": 2, "status": "questionable" }, ... ]
    """
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
    # Local testing: python backend.py
    app.run(debug=True, host="0.0.0.0", port=5000)
