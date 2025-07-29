import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import base64
import os

def send_analysis_email(recipient_email, subject, body_text, plots):
    sender_email = os.environ.get("DJANGO_EMAIL_SENDER")
    sender_app_password = os.environ.get("DJANGO_EMAIL_APP_PASSWORD")

    if not sender_email or not sender_app_password:
        raise ValueError("Email sender credentials (DJANGO_EMAIL_SENDER, DJANGO_EMAIL_APP_PASSWORD) not set in environment variables.")

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body_text, 'plain'))

    for i, plot_info in enumerate(plots):
        part = MIMEBase('application', 'octet-stream')
        # Decode the base64 string back to bytes
        image_bytes = base64.b64decode(plot_info['image'])
        part.set_payload(image_bytes)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {plot_info['title'].replace(' ', '_')}_{i+1}.png")
        msg.attach(part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_app_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False