import sqlite3
import uuid
import hashlib


from flask import Blueprint, request, jsonify
from database.db import get_db_connection

company_bp = Blueprint("company", __name__, url_prefix="/api/company")


@company_bp.route("/test", methods=["GET"])
def test_company():
    return jsonify({"message": "Company routes working"})


@company_bp.route("/user/register", methods=["POST"])
def register_company_user():
    data = request.get_json()

    required_fields = [
        "company_id",
        "full_name",
        "age",
        "email",
        "phone",
        "vehicle_number",
    ]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    company_user_id = str(uuid.uuid4())
    # 🔑 Set active user for detection alerts
    from app import latest_user_id  # if needed (see note below)

    latest_user_id = company_user_id

    print(f"🏢 Active company driver set for detection: {latest_user_id}")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 🔍 Verify company exists (VERY IMPORTANT)
        cursor.execute("SELECT id FROM companies WHERE id = ?", (data["company_id"],))
        company = cursor.fetchone()

        if not company:
            return jsonify({"error": "Invalid company_id"}), 400

        cursor.execute(
            """
            INSERT INTO company_users (
                id,
                company_id,
                full_name,
                age,
                email,
                phone,
                vehicle_number
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                company_user_id,
                data["company_id"],
                data["full_name"],
                data["age"],
                data["email"],
                data["phone"],
                data["vehicle_number"],
            ),
        )

        conn.commit()

        return (
            jsonify(
                {
                    "message": "Company user registered successfully",
                    "company_user_id": company_user_id,
                }
            ),
            201,
        )

    except sqlite3.IntegrityError as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()


@company_bp.route("/<string:company_id>/users", methods=["GET"])
def get_company_users(company_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, full_name, email, phone, vehicle_number
            FROM company_users
            WHERE company_id = ?
            """,
            (company_id,),
        )

        users = cursor.fetchall()
        conn.close()

        return jsonify([dict(u) for u in users]), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@company_bp.route("/register", methods=["POST"])
def register_company():
    data = request.get_json()

    # Basic validation
    if not data or not all(k in data for k in ("name", "email", "password")):
        return (
            jsonify({"success": False, "message": "Missing required fields"}),
            200,
        )  # ⚠️ always 200 for frontend compatibility

    # Hash the password securely
    password_hash = hashlib.sha256(data["password"].encode()).hexdigest()
    company_id = str(uuid.uuid4())

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if email already exists
        cursor.execute("SELECT id FROM companies WHERE email = ?", (data["email"],))
        existing_company = cursor.fetchone()

        if existing_company:
            conn.close()
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Email already exists. Please use a new one.",
                    }
                ),
                200,
            )  # ⚠️ frontend expects 200

        # Insert company
        cursor.execute(
            """
            INSERT INTO companies (id, name, email, password_hash)
            VALUES (?, ?, ?, ?)
            """,
            (
                company_id,
                data["name"],
                data["email"],
                password_hash,
            ),
        )

        conn.commit()
        conn.close()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Company registered successfully",
                    "company_id": company_id,
                }
            ),
            201,
        )  # ⚠️ not 201

    except Exception as e:
        return (
            jsonify(
                {"success": False, "message": "Internal server error", "error": str(e)}
            ),
            200,
        )  # ⚠️ still 200


@company_bp.route("/user/<string:company_user_id>/emergency-contact", methods=["POST"])
def add_emergency_contact(company_user_id):
    data = request.get_json()

    required_fields = ["name", "relation", "email", "phone"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    contact_id = str(uuid.uuid4())

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 🔍 Verify company_user exists
        cursor.execute("SELECT id FROM company_users WHERE id = ?", (company_user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "Invalid company_user_id"}), 400

        cursor.execute(
            """
            INSERT INTO company_contacts (
                id,
                company_user_id,
                name,
                relation,
                email,
                phone
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                contact_id,
                company_user_id,
                data["name"],
                data["relation"],
                data["email"],
                data["phone"],
            ),
        )

        conn.commit()

        return (
            jsonify(
                {
                    "message": "Emergency contact added successfully",
                    "contact_id": contact_id,
                }
            ),
            201,
        )

    except sqlite3.IntegrityError as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()
