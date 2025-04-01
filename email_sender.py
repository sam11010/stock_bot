import os
import smtplib
from email.message import EmailMessage
from robocorp.tasks import task
from RPA.Robocorp.Vault import Vault  

def send_email_with_attachments(sender, recipient, subject, body, attachment_paths,
                                smtp_server, smtp_port, username, password):
    """Skickar ett e-postmeddelande med bilagor via SMTP_SSL."""
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient
    msg.set_content(body)
    
    # Lägg till alla bilagor
    for attachment_path in attachment_paths:
        with open(attachment_path, 'rb') as f:
            file_data = f.read()
        file_name = os.path.basename(attachment_path)
        msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)
    
    with smtplib.SMTP_SSL(smtp_server, smtp_port) as smtp:
        smtp.login(username, password)
        smtp.send_message(msg)
    print(f"E-post skickat till {recipient} med bilagor: {', '.join(os.path.basename(p) for p in attachment_paths)}")

@task
def send_email_task():
    sender = "s.gronlund8@gmail.com"
    recipient = "s.gronlund8@gmail.com"
    subject = "Dagens analysresultat"
    body = (
        "Hej,\n\n"
        "Bifogat finner du de senaste CSV-filerna med aktieanalysresultat.\n\n"
        "Med vänlig hälsning,\nDin Bot"
    )
    smtp_server = "smtp.gmail.com"  # t.ex. smtp.gmail.com
    smtp_port = 465                # vanligtvis 465 för SSL
    username = "s.gronlund8@gmail.com"

    # Hämta lösenord från Vault
    vault = Vault()
    credentials = vault.get_secret("email_credentials")
    password = credentials.get("password")
    
    if not password:
        raise ValueError("Ingen 'password' hittades i secret 'email_credentials' i Vault.")
    
    # Lista med filvägar som ska bifogas
    attachment_paths = ["analysis_results_rsi_sma.csv", "analysis_results_macd.csv"]
    
    send_email_with_attachments(sender, recipient, subject, body, attachment_paths,
                                smtp_server, smtp_port, username, password)