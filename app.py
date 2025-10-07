# app.py
from flask import Flask, render_template, Response, jsonify, request
from detection.detect_drowsiness import gen_frames  # keep your existing import
from state import alert_counts
from flask_cors import CORS
import sqlite3
import uuid
import os

app = Flask(__name__)
CORS(app)

# Database path resolved relative to this file (avoid cwd issues)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "driver_drowsiness.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def create_tables_if_not_exist():
    conn = get_db_connection()
    c = conn.cursor()
    # Users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        age INTEGER,
        email TEXT,
        phone TEXT
    );
    """)
    # Contacts table
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
        print("[add_user_to_db] user_info:", user_info)
        print("[add_user_to_db] contacts:", contacts)
        raise
    finally:
        conn.close()
    return user_id

# Ensure DB/tables exist at startup
create_tables_if_not_exist()

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
    print("[/add_user] Request. DB_PATH:", DB_PATH)  # <== ✅ DEBUGGING PATH
    print("[DEBUG] Using DB path:", DB_PATH)          # <== ✅ ADDED LINE
    
    if not request.is_json:
        print("[/add_user] Not JSON")
        return jsonify({"status": "error", "message": "Expected JSON payload"}), 400

    data = request.get_json()
    print("[/add_user] Payload:", data)

    if not data or 'user_info' not in data or 'contacts' not in data:
        return jsonify({"status": "error", "message": "Invalid payload"}), 400

    user_info = data['user_info']
    contacts = data['contacts']

    # Basic validation
    required_fields = ('full_name', 'age', 'email', 'phone')
    if not all(user_info.get(k) for k in required_fields):
        return jsonify({"status": "error", "message": "User info fields missing"}), 400
    if not isinstance(contacts, list) or len(contacts) < 1:
        return jsonify({"status": "error", "message": "At least one emergency contact required"}), 400

    try:
        user_id = add_user_to_db(user_info, contacts)
        return jsonify({"status": "success", "user_id": user_id}), 201
    except Exception as e:
        print("[/add_user] Exception while inserting:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/test_form')
def test_form():
    return render_template('test_form.html')

@app.route('/list_users', methods=['GET'])
def list_users():
    conn = get_db_connection()
    users = [dict(row) for row in conn.execute('SELECT * FROM users').fetchall()]
    contacts = [dict(row) for row in conn.execute('SELECT * FROM contacts').fetchall()]
    conn.close()
    return jsonify({"users": users, "contacts": contacts})

if __name__ == '__main__':
    print("[app] Starting Flask app. DB file:", DB_PATH)
    app.run(host='0.0.0.0', port=5000, debug=True)
