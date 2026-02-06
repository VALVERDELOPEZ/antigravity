"""
Lead Finder AI - Mailer Module
Handles sending emails via SMTP or logging them if not configured
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime

def send_smtp_email(to_email, subject, body, config=None):
    """
    Sends an email using SMTP if configured, otherwise logs it.
    config: Optional dict with 'server', 'port', 'username', 'password', 'sender_name'
    Returns: (bool, message)
    """
    if config:
        smtp_server = config.get('server')
        smtp_port = config.get('port', 587)
        smtp_user = config.get('username')
        smtp_password = config.get('password')
        from_name = config.get('sender_name') or 'Lead Finder AI'
        from_addr = smtp_user
    else:
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = os.getenv('SMTP_PORT', 587)
        smtp_user = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        from_name = os.getenv('EMAIL_FROM_NAME', 'Lead Finder AI')
        from_addr = os.getenv('EMAIL_FROM_ADDRESS')

    # Si falta configuración, simulamos el envío para no romper la app
    if not all([smtp_server, smtp_user, smtp_password]):
        log_msg = f"[SIMULATION] Email to {to_email} | Subject: {subject} | Body: {body[:50]}..."
        print(log_msg)
        # Guardar en un log local para que el usuario pueda verlo
        with open('mail_simulation.log', 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now()} - {log_msg}\n")
        return True, "Email simulated (SMTP not configured)"

    try:
        msg = MIMEMultipart()
        msg['From'] = f"{from_name} <{from_addr}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        
        print(f"✓ Email sent to {to_email}")
        return True, "Email sent successfully"
    except Exception as e:
        error_msg = f"Error sending email: {str(e)}"
        print(error_msg)
        return False, error_msg

if __name__ == "__main__":
    # Test simple
    from dotenv import load_dotenv
    load_dotenv('.env.local')
    success, msg = send_smtp_email("test@example.com", "Prueba Lead Finder", "Este es un correo de prueba.")
    print(f"Result: {success}, {msg}")
