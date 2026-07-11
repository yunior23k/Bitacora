import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# --- Database setup -----------------------------------------------------
# On Render, set DATABASE_URL to your Supabase (or any Postgres) connection
# string as an environment variable. Falls back to a local SQLite file for
# quick local testing (NOTE: SQLite on Render's free tier is NOT persistent
# across deploys/restarts -- use Postgres in production).
db_url = os.environ.get("DATABASE_URL", "sqlite:///local.db")
if db_url.startswith("postgres://"):
    # SQLAlchemy needs the postgresql:// scheme
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Config(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    initial = db.Column(db.Float, nullable=False, default=10000)
    unit_pct = db.Column(db.Float, nullable=False, default=2)


class Bet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)
    sport = db.Column(db.String(40), nullable=False)
    matchup = db.Column(db.String(200), nullable=False)
    pick = db.Column(db.String(200), nullable=False)
    odds = db.Column(db.Float, nullable=False)
    stake = db.Column(db.Float, nullable=False)
    units = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(10), nullable=False, default="pending")
    note = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date,
            "sport": self.sport,
            "matchup": self.matchup,
            "pick": self.pick,
            "odds": self.odds,
            "stake": self.stake,
            "units": self.units,
            "status": self.status,
            "note": self.note,
        }


with app.app_context():
    db.create_all()
    if Config.query.first() is None:
        db.session.add(Config(initial=10000, unit_pct=2))
        db.session.commit()


def american_to_profit(odds, stake):
    o = float(odds)
    if o > 0:
        return stake * (o / 100)
    return stake * (100 / abs(o))


# --- Pages ---------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# --- API: config -----------------------------------------------------------
@app.route("/api/config", methods=["GET"])
def get_config():
    c = Config.query.first()
    return jsonify({"initial": c.initial, "unit_pct": c.unit_pct})


@app.route("/api/config", methods=["POST"])
def update_config():
    data = request.get_json(force=True)
    try:
        initial = float(str(data.get("initial", "")).replace(",", "").replace("$", ""))
        unit_pct = float(data.get("unit_pct"))
    except (TypeError, ValueError):
        return jsonify({"error": "Datos inválidos"}), 400
    if initial <= 0 or unit_pct <= 0:
        return jsonify({"error": "Los valores deben ser mayores a 0"}), 400
    c = Config.query.first()
    c.initial = initial
    c.unit_pct = unit_pct
    db.session.commit()
    return jsonify({"initial": c.initial, "unit_pct": c.unit_pct})


# --- API: bets -------------------------------------------------------------
@app.route("/api/bets", methods=["GET"])
def list_bets():
    bets = Bet.query.order_by(Bet.date.desc(), Bet.id.desc()).all()
    return jsonify([b.to_dict() for b in bets])


@app.route("/api/bets", methods=["POST"])
def add_bet():
    data = request.get_json(force=True)
    required = ["date", "sport", "matchup", "pick", "odds", "stake"]
    if not all(data.get(k) not in (None, "") for k in required):
        return jsonify({"error": "Faltan campos requeridos"}), 400
    try:
        odds = float(data["odds"])
        stake = float(data["stake"])
    except (TypeError, ValueError):
        return jsonify({"error": "Momio y stake deben ser numéricos"}), 400

    bet = Bet(
        date=data["date"],
        sport=data["sport"],
        matchup=data["matchup"],
        pick=data["pick"],
        odds=odds,
        stake=stake,
        units=data.get("units"),
        status=data.get("status", "pending"),
        note=data.get("note", ""),
    )
    db.session.add(bet)
    db.session.commit()
    return jsonify(bet.to_dict()), 201


@app.route("/api/bets/<int:bet_id>", methods=["PATCH"])
def update_bet(bet_id):
    bet = Bet.query.get_or_404(bet_id)
    data = request.get_json(force=True)
    if "status" in data:
        bet.status = data["status"]
    db.session.commit()
    return jsonify(bet.to_dict())


@app.route("/api/bets/<int:bet_id>", methods=["DELETE"])
def delete_bet(bet_id):
    bet = Bet.query.get_or_404(bet_id)
    db.session.delete(bet)
    db.session.commit()
    return jsonify({"deleted": True})


@app.route("/api/stats", methods=["GET"])
def stats():
    c = Config.query.first()
    bets = Bet.query.all()
    profit = staked = pending = 0.0
    wins = losses = 0
    for b in bets:
        if b.status == "win":
            profit += american_to_profit(b.odds, b.stake)
            staked += b.stake
            wins += 1
        elif b.status == "loss":
            profit -= b.stake
            staked += b.stake
            losses += 1
        elif b.status == "push":
            staked += b.stake
        elif b.status == "pending":
            pending += b.stake
    settled = wins + losses
    current_bank = c.initial + profit
    return jsonify({
        "current_bank": current_bank,
        "initial": c.initial,
        "unit_pct": c.unit_pct,
        "unit_value": current_bank * (c.unit_pct / 100),
        "profit": profit,
        "staked": staked,
        "pending": pending,
        "roi": (profit / staked * 100) if staked > 0 else 0,
        "win_rate": (wins / settled * 100) if settled > 0 else 0,
        "wins": wins,
        "losses": losses,
    })


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
