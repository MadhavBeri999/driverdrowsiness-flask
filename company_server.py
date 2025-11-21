from flask import Flask, request
from datetime import datetime

app = Flask(__name__)


@app.route("/receive-alert", methods=["POST"])
def receive_alert():
    data = request.json

    print("\n📡 Received alert from Driver Monitoring System")
    print(f"👤 Driver ID: {data.get('driver_id')}")
    print(f"👤 Driver Name: {data.get('driver_name')}")
    print(f"⚠️ Alert Type: {data.get('alert_type')}")
    print(f"⚠️ Alert Count: {data.get('alert_count')}")
    print(f"🧱 Blockchain Tx Hash: {data.get('tx_hash')}")
    print(f"⏱ Timestamp: {data.get('timestamp')}")
    print("Status: ✔ Saved for company audit\n")

    return {"status": "success", "message": "alert received"}, 200


if __name__ == "__main__":
    app.run(port=5001)
