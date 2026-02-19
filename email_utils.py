import os
import smtplib
from email.message import EmailMessage

# Ensure these are set in your environment or .env file
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")


def send_email_notification(to_email: str, subject: str, message: str):
    if not EMAIL_USER or not EMAIL_PASS:
        print(
            f"❌ [EMAIL ERROR] EMAIL_USER or EMAIL_PASS not found in Environment Variables!"
        )
        return False

    try:
        msg = EmailMessage()
        msg["From"] = EMAIL_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(message)

        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_USER, EMAIL_PASS)
            smtp.send_message(msg)

        print(f"✅ [EMAIL SUCCESS] Sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ [EMAIL FAILURE] Could not send to {to_email}: {e}")
        return False


def compose_alert_message(
    driver_name: str, contact_name: str, alert_type: str, lat=None, lon=None
):
    subject = f"⚠️ EMERGENCY: Drowsiness Alert for {driver_name}"

    # ✅ FIXED: Correct Google Maps URL format
    if lat and lon:
        maps_link = f"https://www.google.com/maps?q={lat},{lon}"
        location_section = f"📍 Last Known Location: {maps_link}\n(Click the link to see the driver's exact position on the map)\n\n"
    else:
        location_section = "📍 Location: Not available.\n\n"

    body = (
        f"Dear {contact_name},\n\n"
        f"The Chaukas System has detected critical {alert_type.upper()} alerts for driver '{driver_name}'.\n"
        f"This indicates the driver is in a high-risk drowsiness state.\n\n"
        f"{location_section}"
        f"ACTION REQUIRED: Please contact the driver immediately.\n\n"
        f"— Chaukas AI Safety Systems"
    )
    return subject, body
