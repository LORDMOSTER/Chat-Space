import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

EMAIL_ADDRESS = "hsri59145@gmail.com"         # Your Gmail
EMAIL_PASSWORD = "rznfxkaebmtdgcwr"            # App password (remove spaces)

def send_verification_email(to_email: str, code: str):
    subject = "🔐 Your Verification Code"
    body = f"""
    <div style="font-family:sans-serif;">
        <h2>Verify your email</h2>
        <p>Your verification code is:</p>
        <h1 style="color:#2e6c80;">{code}</h1>
        <p>If you didn’t request this, just ignore this message.</p>
    </div>
    """

    message = MIMEMultipart()
    message["From"] = EMAIL_ADDRESS
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(message)
            print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Error sending email: {e}")
