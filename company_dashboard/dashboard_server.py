from flask import Flask, render_template, request, jsonify
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Store last 20 alerts for display
company_alert_logs = []


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

    # Keep only latest 20 alerts
    company_alert_logs.insert(0, entry)
    company_alert_logs = company_alert_logs[:20]

    return jsonify({"status": "saved"}), 200


@app.route("/dashboard_data")
def dashboard_data():
    return jsonify(company_alert_logs)


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


if __name__ == "__main__":
    print("\n🏢 Company dashboard running on http://127.0.0.1:7000")
    app.run(port=7000, debug=True)
