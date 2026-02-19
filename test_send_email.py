# test_send_email.py
from email_utils import send_email_notification

# put the recipient you control (can be the same as EMAIL_USER)
recipient = "madhavberi222@gmail.com"

subject = "Test — Chaukas Drowsiness Monitoring System"
body = "This is a test email from Chaukas Drowsiness Monitoring System.\nIf you receive this, SMTP works."

ok = send_email_notification(recipient, subject, body)
print("send_email_notification returned:", ok)
