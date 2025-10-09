# email_utils.py
import os
import smtplib
from email.message import EmailMessage

# ----------------------------------------------
# 🔐 Load credentials from environment variables
# ----------------------------------------------
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

if not EMAIL_USER or not EMAIL_PASS:
    print("⚠️ [email_utils] EMAIL_USER or EMAIL_PASS not set. Emails will not be sent.")

# ----------------------------------------------
# 📬 Helper function to send one email
# ----------------------------------------------
def send_email_notification(to_email: str, subject: str, message: str):
    """
    Send a simple plain-text email using Gmail SMTP.
    Requires:
        - EMAIL_USER  (your Gmail address)
        - EMAIL_PASS  (app password)
    """
    if not EMAIL_USER or not EMAIL_PASS:
        print(f"⚠️ [email_utils] Missing credentials. Skipping email to {to_email}")
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

        print(f"✅ [email_utils] Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"❌ [email_utils] Failed to send email to {to_email}: {e}")
        return False


# ----------------------------------------------
# 🧠 Helper to build a nice alert message
# ----------------------------------------------
def compose_alert_message(driver_name: str, contact_name: str, alert_type: str) -> tuple[str, str]:
    """
    Builds subject + body for the alert email.
    """
    subject = f"⚠️ Drowsiness Alert for {driver_name} (Driver)"
    body = (
        f"Dear {contact_name},\n\n"
        f"The system has detected repeated {alert_type.upper()} alerts for driver \"{driver_name}\".\n"
        f"Immediate attention may be required.\n\n"
        f"Please ensure the driver takes a break or rests safely.\n\n"
        f"— Chaukas Drowsiness Monitoring System"
    )
    return subject, body
