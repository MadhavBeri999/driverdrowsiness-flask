# routes/call_routes.py
# ─────────────────────────────────────────────────────────────────────────────
# Flask Blueprint: emergency call endpoints
# ─────────────────────────────────────────────────────────────────────────────
# Endpoints:
#   GET  /get_call_contacts?user_id=<id>  → returns contacts with phone numbers
#   POST /trigger_calls                   → auto-dials via Vonage/Plivo (optional)
#   GET  /emergency_call_panel            → standalone HTML UI with Call buttons
#   GET  /plivo_answer                    → Plivo TTS XML (if using Plivo auto-call)
# ─────────────────────────────────────────────────────────────────────────────

from flask import Blueprint, jsonify, request, render_template, Response
from call_utils import (
    get_click_to_call_data,
    trigger_emergency_calls,
    get_latest_user_id,
    get_emergency_contacts_with_phones,
)
import os

call_bp = Blueprint("call_bp", __name__)


# ── 1. Get contacts with phone numbers (for frontend click-to-call) ────────────
@call_bp.route("/get_call_contacts", methods=["GET"])
def get_call_contacts():
    """
    Returns emergency contacts that have phone numbers for a given user.
    Query param: user_id (optional — falls back to most recent user)
    """
    user_id = request.args.get("user_id") or get_latest_user_id()
    if not user_id:
        return jsonify({"error": "No user found. Please register a driver first."}), 404

    data = get_click_to_call_data(user_id)
    return jsonify(data), 200


# ── 2. Trigger auto-calls via Vonage / Plivo ──────────────────────────────────
@call_bp.route("/trigger_calls", methods=["POST"])
def trigger_calls():
    """
    Triggers automated outbound calls to all emergency contacts.
    Body (JSON, all optional):
      { "user_id": "...", "driver_name": "...", "alert_type": "sleep" }
    Falls back to most recent user if user_id not provided.
    """
    body = request.get_json(silent=True) or {}

    user_id = body.get("user_id") or get_latest_user_id()
    driver_name = body.get("driver_name", "the driver")
    alert_type = body.get("alert_type", "drowsiness")

    if not user_id:
        return jsonify({"error": "No user found. Register a driver first."}), 404

    result = trigger_emergency_calls(user_id, driver_name, alert_type)
    return jsonify(result), 200


# ── 3. Standalone Emergency Call Panel (HTML) ─────────────────────────────────
@call_bp.route("/emergency_call_panel")
def emergency_call_panel():
    """
    A beautiful standalone HTML page with:
    - List of all emergency contacts with phone numbers
    - Clickable "📞 Call" buttons (tel: links — works on phones)
    - Auto-call trigger button (if backend API configured)
    Query param: user_id (optional)
    """
    user_id = request.args.get("user_id") or get_latest_user_id()
    contacts = []
    if user_id:
        contacts = get_emergency_contacts_with_phones(user_id)

    return render_template(
        "emergency_call_panel.html", contacts=contacts, user_id=user_id
    )


# ── 4. Plivo TTS Answer XML ───────────────────────────────────────────────────
@call_bp.route("/plivo_answer", methods=["GET"])
def plivo_answer():
    """
    Returns Plivo-compatible XML with a TTS message.
    Set PLIVO_ANSWER_URL to this endpoint's public URL if using Plivo auto-call.
    Example: https://your-ngrok-url.ngrok.io/plivo_answer
    """
    driver_name = request.args.get("driver_name", "the driver")
    alert_type = request.args.get("alert_type", "drowsiness")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Speak voice="WOMAN" language="en-US" loop="2">
        Alert! This is an automated emergency call from the Chaukas drowsiness detection system.
        Driver {driver_name} has been detected with a {alert_type} alert.
        Please check on the driver immediately.
    </Speak>
</Response>"""
    return Response(xml, mimetype="application/xml")
