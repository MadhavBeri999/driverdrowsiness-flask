# app.py
from flask import Flask, render_template, Response, jsonify, request
from detection.detect_drowsiness import gen_frames
from state import alert_counts, log_alert
from flask_cors import CORS
from email_utils import send_email_notification, compose_alert_message
import sqlite3
import uuid
import os
import time

app = Flask(__name__)
CORS(app)

# ------------------- Database Config -------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "driver_drowsiness.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def create_tables_if_not_exist():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        age INTEGER,
        email TEXT,
        phone TEXT
    );
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS contacts (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        name TEXT,
        relation TEXT,
        email TEXT,
        phone TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)
    conn.commit()
    conn.close()
    print("[DB] Ensured tables exist at:", DB_PATH)


def add_user_to_db(user_info, contacts):
    conn = get_db_connection()
    c = conn.cursor()
    user_id = str(uuid.uuid4())
    print("[add_user_to_db] Inserting user:", user_info)
    try:
        c.execute('''
            INSERT INTO users (id, full_name, age, email, phone)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, user_info['full_name'], int(user_info['age']), user_info['email'], user_info['phone']))
        
        for contact in contacts:
            contact_id = str(uuid.uuid4())
            print("[add_user_to_db] Inserting contact:", contact)
            c.execute('''
                INSERT INTO contacts (id, user_id, name, relation, email, phone)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                contact_id,
                user_id,
                contact.get('name'),
                contact.get('relation'),
                contact.get('email'),
                contact.get('phone')
            ))
        conn.commit()
        print("[add_user_to_db] Commit successful.")
    except Exception as db_err:
        conn.rollback()
        print("[add_user_to_db] ERROR while inserting into DB:", db_err)
        raise
    finally:
        conn.close()
    return user_id


# ------------------- Get User + Contacts -------------------
def get_contacts_for_user(user_id: str):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT full_name FROM users WHERE id = ?", (user_id,))
        user_row = c.fetchone()
        if not user_row:
            return None, []

        driver_name = user_row["full_name"]

        c.execute("SELECT name, email FROM contacts WHERE user_id = ?", (user_id,))
        contacts = [{"name": row["name"], "email": row["email"]} for row in c.fetchall()]
        return driver_name, contacts
    finally:
        conn.close()


# ------------------- Initialization -------------------
create_tables_if_not_exist()

latest_user_id = None  # ✅ Track most recent user
EMAILS_SENT_COUNT = 0  # ✅ Track total number of sent emails

COOL_DOWN_SECONDS = 10 * 60   # 10 minutes
_last_notification_time = {}  # cooldown dictionary


# ------------------- Routes -------------------
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/get_alert_counts')
def get_alert_counts():
    return jsonify(alert_counts)


@app.route('/health')
def health_check():
    return {"status": "OK"}, 200


@app.route('/add_user', methods=['POST'])
def add_user():
    global latest_user_id
    print("[/add_user] Request. DB_PATH:", DB_PATH)
    if not request.is_json:
        return jsonify({"status": "error", "message": "Expected JSON payload"}), 400

    data = request.get_json()
    print("[/add_user] Payload:", data)

    if not data or 'user_info' not in data or 'contacts' not in data:
        return jsonify({"status": "error", "message": "Invalid payload"}), 400

    user_info = data['user_info']
    contacts = data['contacts']

    required_fields = ('full_name', 'age', 'email', 'phone')
    if not all(user_info.get(k) for k in required_fields):
        return jsonify({"status": "error", "message": "User info fields missing"}), 400
    if not isinstance(contacts, list) or len(contacts) < 1:
        return jsonify({"status": "error", "message": "At least one emergency contact required"}), 400

    try:
        user_id = add_user_to_db(user_info, contacts)
        latest_user_id = user_id
        print(f"[app.py] ✅ Latest active user set to {latest_user_id}")
        return jsonify({"status": "success", "user_id": user_id}), 201
    except Exception as e:
        print("[/add_user] Exception while inserting:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/list_users', methods=['GET'])
def list_users():
    conn = get_db_connection()
    users = [dict(row) for row in conn.execute('SELECT * FROM users').fetchall()]
    contacts = [dict(row) for row in conn.execute('SELECT * FROM contacts').fetchall()]
    conn.close()
    return jsonify({"users": users, "contacts": contacts})


# ------------------- LOG ALERT -------------------
@app.route('/log_alert', methods=['POST'])
def log_alert_endpoint():
    global latest_user_id, EMAILS_SENT_COUNT

    data = request.get_json()
    print("[/log_alert] Incoming alert data:", data)

    user_id = data.get("user_id") or latest_user_id
    alert_type = data.get("alert_type")

    if not user_id or not alert_type:
        return jsonify({"error": "Missing user_id or alert_type"}), 400

    try:
        triggered = log_alert(user_id, alert_type)
        if triggered:
            print(f"🚨 [NOTIFICATION] Alert triggered for {alert_type} (user {user_id})")

            key = (user_id, alert_type)
            now_ts = time.time()
            last_sent = _last_notification_time.get(key, 0)
            if now_ts - last_sent < COOL_DOWN_SECONDS:
                print(f"⏱️ Cooldown active for {key}. Skipping email.")
                return jsonify({"threshold_exceeded": True, "emails_sent": 0, "cooldown": True}), 200

            driver_name, contacts = get_contacts_for_user(user_id)
            if not contacts:
                print(f"⚠️ No contacts found for user {user_id}")
                return jsonify({"threshold_exceeded": True, "emails_sent": 0}), 200

            sent_count = 0
            for contact in contacts:
                subject, body = compose_alert_message(driver_name, contact["name"], alert_type)
                success = send_email_notification(contact["email"], subject, body)
                if success:
                    sent_count += 1

            EMAILS_SENT_COUNT += sent_count  # ✅ Count all sent emails
            _last_notification_time[key] = time.time()
            print(f"📨 Emails sent successfully: {sent_count}")
            return jsonify({"threshold_exceeded": True, "emails_sent": sent_count}), 200

        return jsonify({"threshold_exceeded": triggered}), 200
    except Exception as e:
        print("[/log_alert] Exception:", e)
        return jsonify({"error": str(e)}), 500


# ------------------- NEW DASHBOARD ROUTES -------------------
@app.route('/get_total_notifications', methods=['GET'])
def get_total_notifications():
    """Return total number of emails sent since server start (in-memory)."""
    return jsonify({"emails_sent": EMAILS_SENT_COUNT}), 200


@app.route('/get_recent_alerts', methods=['GET'])
def get_recent_alerts():
    """Return the 10 most recent alerts with user name."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        # Join alerts → sessions → users
        c.execute("""
            SELECT a.alert_type, a.timestamp, u.full_name AS user_name
            FROM alerts a
            JOIN sessions s ON a.session_id = s.id
            JOIN users u ON s.user_id = u.id
            ORDER BY a.timestamp DESC
            LIMIT 10;
        """)
        rows = c.fetchall()
        conn.close()

        alerts = [
            {
                "type": r["alert_type"],
                "timestamp": r["timestamp"],
                "user": r["user_name"]
            }
            for r in rows
        ]
        return jsonify({"alerts": alerts}), 200
    except Exception as e:
        print("[/get_recent_alerts] Could not fetch alerts:", e)
        return jsonify({"alerts": []}), 200



@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')


# ------------------- Run Flask -------------------
if __name__ == '__main__':
    print("[app] Starting Flask app. DB file:", DB_PATH)
    app.run(host='0.0.0.0', port=5000, debug=True)
