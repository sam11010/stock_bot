import os
import smtplib
from email.message import EmailMessage
from robocorp.tasks import task

def send_email_with_attachment(sender, recipient, subject, body, attachment_path,
                               smtp_server, smtp_port, username, password):
    """Skickar ett e-postmeddelande med en bilaga via SMTP_SSL."""
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient
    msg.set_content(body)
    
    with open(attachment_path, 'rb') as f:
        file_data = f.read()
        file_name = os.path.basename(attachment_path)
    
    msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)
    
    with smtplib.SMTP_SSL(smtp_server, smtp_port) as smtp:
        smtp.login(username, password)
        smtp.send_message(msg)
    print(f"E-post skickat till {recipient} med bilagan {file_name}.")

@task
def send_email_task():
    # Ange dina e-postuppgifter
    sender = "s.gronlund8@gmail.com"
    recipient = "s.gronlund8@gmail.com"
    subject = "Dagens analysresultat"
    body = ("Hej,\n\nBifogat finner du den senaste CSV-filen med aktieanalysresultat.\n\nMed vänlig hälsning,\nDin Bot")
    smtp_server = "smtp.gmail.com"  # t.ex. smtp.gmail.com
    smtp_port = 465                   # vanligtvis 465 för SSL
    username = "s.gronlund8@gmail.com"
    # För bästa säkerhet, lagra lösenordet som en miljövariabel (t.ex. EMAIL_PASSWORD)
    password = os.environ.get("EMAIL_PASSWORD")
    if not password:
        raise ValueError("EMAIL_PASSWORD environment variable is not set")
    
    attachment_path = "analysis_results.csv"
    send_email_with_attachment(sender, recipient, subject, body, attachment_path,
                               smtp_server, smtp_port, username, password)