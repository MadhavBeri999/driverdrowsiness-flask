from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from datetime import datetime
from flask_cors import CORS
import sqlite3
import hashlib


app = Flask(__name__)
CORS(app)

# REQUIRED for login session
app.secret_key = "company_dashboard_secret"

# Store last 20 alerts (UNCHANGED)
company_alert_logs = []


# ------------------ DATABASE HELPER ------------------
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Go one level up from company_dashboard → driver_drowsiness
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

DB_PATH = os.path.join(PROJECT_ROOT, "database", "driver_drowsiness.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    print("📂 Using DB:", DB_PATH)

    return conn


# ------------------ ALERT RECEIVER (UNCHANGED) ------------------
@app.route("/company_receive", methods=["POST"])
def company_receive():
    global company_alert_logs

    data = request.get_json()
    print("\n📩 Incoming alert from drowsiness system:", data)

    entry = {
        "driver_id": data.get("driver_id"),
        "driver_name": data.get("driver_name"),
        "alert_type": data.get("alert_type"),
        "alert_count": data.get("alert_count"),
        "tx_hash": data.get("tx_hash"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    company_alert_logs.insert(0, entry)
    company_alert_logs = company_alert_logs[:20]

    return jsonify({"status": "saved"}), 200


# ------------------ DASHBOARD DATA (UNCHANGED) ------------------
@app.route("/dashboard_data")
def dashboard_data():
    if "company_id" not in session:
        return jsonify([])

    return jsonify(company_alert_logs)


# ------------------ LOGIN PAGE ------------------
@app.route("/", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        company_name = request.form.get("company_name")
        password = request.form.get("password")

        hashed = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db_connection()
        company = conn.execute(
            "SELECT * FROM companies WHERE name=? AND password_hash=?",
            (company_name, hashed),
        ).fetchone()
        conn.close()

        if company:
            session["company_id"] = company["id"]
            session["company_name"] = company["name"]
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid company name or password"

    return render_template("login.html", error=error)


# ------------------ DASHBOARD PAGE ------------------
@app.route("/dashboard")
def dashboard():
    if "company_id" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html")


# ------------------ LOGOUT (OPTIONAL BUT GOOD) ------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ------------------ RUN ------------------
if __name__ == "__main__":
    print("\n🏢 Company dashboard running on http://127.0.0.1:7000")
    app.run(port=7000, debug=True)
