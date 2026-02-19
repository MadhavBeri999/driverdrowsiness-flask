from flask import Blueprint, request, jsonify
from database.db import get_db_connection
from email_utils import send_email_notification, compose_alert_message
import time

company_alert_bp = Blueprint("company_alerts", __name__)


@company_alert_bp.route("/company/log_alert", methods=["POST"])
def company_log_alert():
    data = request.get_json()

    company_user_id = data.get("company_user_id")
    alert_type = data.get("alert_type")

    if not company_user_id or not alert_type:
        return jsonify({"error": "Missing company_user_id or alert_type"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 🔹 Fetch driver
        cursor.execute(
            "SELECT full_name FROM company_users WHERE id = ?",
            (company_user_id,),
        )
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Invalid company_user_id"}), 400

        driver_name = row[0]

        # 🔹 Fetch emergency contacts
        cursor.execute(
            """
            SELECT name, email
            FROM company_contacts
            WHERE company_user_id = ?
            """,
            (company_user_id,),
        )
        contacts = cursor.fetchall()

        # 🔹 Store alert
        cursor.execute(
            """
            INSERT INTO alerts (session_id, alert_id, timestamp, count)
            VALUES (?, ?, CURRENT_TIMESTAMP, 1)
            """,
            (company_user_id, alert_type),
        )

        conn.commit()
        conn.close()

        # 🔹 Send emails
        sent = 0
        for name, email in contacts:
            subject, body = compose_alert_message(driver_name, name, alert_type)
            if send_email_notification(email, subject, body):
                sent += 1

        return (
            jsonify(
                {
                    "status": "ok",
                    "driver": driver_name,
                    "emails_sent": sent,
                }
            ),
            200,
        )

    except Exception as e:
        print("[company_log_alert] error:", e)
        return jsonify({"error": str(e)}), 500
