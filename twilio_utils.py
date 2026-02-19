# twilio_utils.py
# ─────────────────────────────────────────────────────────────────
# 📞 Twilio Emergency Calling Utility
#
# This is a STANDALONE file. It is safe to delete without affecting
# the original app.py or any other existing files.
#
# Requires the following environment variables to be set:
#   TWILIO_ACCOUNT_SID   – from console.twilio.com
#   TWILIO_AUTH_TOKEN    – from console.twilio.com
#   TWILIO_FROM_NUMBER   – your Twilio-purchased phone number
#                          (e.g. "+12015551234")
#
# ⚠️  Trial accounts: destination numbers must be verified in Twilio.
# ─────────────────────────────────────────────────────────────────
import os

# ── Credentials (loaded from environment) ──────────────────────
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")

_client = None  # lazy-initialised to avoid crashing on import


def _get_client():
    """Return a cached Twilio REST client, or None if credentials are missing."""
    global _client

    if _client is not None:
        return _client

    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER]):
        print(
            "⚠️  [twilio_utils] One or more Twilio credentials are missing. "
            "Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER."
        )
        return None

    try:
        from twilio.rest import Client  # imported here so missing package is graceful

        _client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        print("✅ [twilio_utils] Twilio client initialised successfully.")
        return _client
    except ModuleNotFoundError:
        print(
            "❌ [twilio_utils] 'twilio' package not installed. "
            "Run: pip install twilio"
        )
        return None
    except Exception as e:
        print(f"❌ [twilio_utils] Failed to initialise Twilio client: {e}")
        return None


# ── TwiML voice message builder ────────────────────────────────
def _build_twiml(driver_name: str, alert_type: str) -> str:
    """
    Returns a TwiML string that Twilio reads aloud to the call recipient.
    The message is designed to be clear and urgent.
    """
    readable_type = alert_type.replace(
        "_", " "
    ).title()  # e.g. "head_tilt" → "Head Tilt"
    message = (
        f"Alert. Driver {driver_name} has triggered a {readable_type} drowsiness alert. "
        f"Immediate attention may be required. "
        f"Please ensure the driver takes a break or rests safely. "
        f"This message is from the Chaukas Drowsiness Monitoring System."
    )
    # Repeat the message once so the recipient doesn't miss it
    twiml = (
        f"<Response>"
        f"<Say voice='alice'>{message}</Say>"
        f"<Pause length='1'/>"
        f"<Say voice='alice'>{message}</Say>"
        f"</Response>"
    )
    return twiml


# ── Single call ────────────────────────────────────────────────
def make_emergency_call(to_phone: str, driver_name: str, alert_type: str) -> bool:
    """
    Place one emergency phone call to `to_phone`.

    Parameters
    ----------
    to_phone     : destination number in E.164 format, e.g. "+919876543210"
    driver_name  : name of the driver being monitored
    alert_type   : alert type string, e.g. "yawn", "sleep", "head_tilt"

    Returns True on success, False on any failure.
    """
    client = _get_client()
    if client is None:
        return False

    if not to_phone:
        print("⚠️  [twilio_utils] No phone number provided for this contact. Skipping.")
        return False

    try:
        twiml = _build_twiml(driver_name, alert_type)
        call = client.calls.create(
            twiml=twiml,
            to=to_phone,
            from_=TWILIO_FROM_NUMBER,
        )
        print(f"📞 [twilio_utils] Call placed to {to_phone} | SID: {call.sid}")
        return True
    except Exception as e:
        print(f"❌ [twilio_utils] Failed to call {to_phone}: {e}")
        return False


# ── Batch call all contacts ────────────────────────────────────
def call_all_contacts(contacts: list, driver_name: str, alert_type: str) -> int:
    """
    Calls every contact in the list that has a non-empty 'phone' field.

    Parameters
    ----------
    contacts    : list of dicts with at least {"name": ..., "phone": ...}
    driver_name : driver's full name
    alert_type  : alert type string

    Returns the number of successful calls placed.
    """
    successful = 0
    for contact in contacts:
        phone = contact.get("phone", "").strip()
        name = contact.get("name", "Emergency Contact")

        if not phone:
            print(f"⚠️  [twilio_utils] Contact '{name}' has no phone number. Skipping.")
            continue

        print(f"📲 [twilio_utils] Calling contact: {name} ({phone})")
        ok = make_emergency_call(phone, driver_name, alert_type)
        if ok:
            successful += 1

    print(f"📞 [twilio_utils] Total calls placed: {successful}/{len(contacts)}")
    return successful
