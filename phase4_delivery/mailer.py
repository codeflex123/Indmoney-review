import os
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re

# Add the project root to sys.path to allow importing config.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

class Mailer:
    def __init__(self, recipient=None):
        Config.validate()
        self.smtp_host = Config.SMTP_HOST
        self.smtp_port = Config.SMTP_PORT
        self.smtp_user = Config.SMTP_USER
        self.smtp_pass = Config.SMTP_PASS
        self.recipient = recipient or Config.RECIPIENT_EMAIL
        self.report_path = "weekly_pulse.md"

    def load_report(self):
        """Loads the content of the weekly pulse report."""
        if not os.path.exists(self.report_path):
            raise FileNotFoundError(f"Report file not found: {self.report_path}. Run Phase 3 first.")
        
        with open(self.report_path, 'r') as f:
            return f.read()

    def generate_html_body(self, md_content):
        """Converts Markdown report to a premium HTML template."""
        # Simple MD to HTML conversion for the weekly pulse format
        lines = md_content.split('\n')
        html_content = ""
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            if line.startswith('# '):
                html_content += f"<h1 style='color: #38bdf8; font-size: 24px; margin-bottom: 20px; border-bottom: 2px solid #1e293b; padding-bottom: 10px;'>{line[2:]}</h1>"
            elif line.startswith('## '):
                html_content += f"<h2 style='color: #818cf8; font-size: 18px; margin-top: 30px; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px;'>{line[3:]}</h2>"
            elif line.startswith('> '):
                # Handle stars and quotes
                if '⭐' in line:
                    html_content += f"<div style='color: #fbbf24; margin-top: 15px;'>{line[2:]}</div>"
                else:
                    html_content += f"<blockquote style='font-style: italic; color: #94a3b8; border-left: 4px solid #38bdf8; padding-left: 15px; margin: 10px 0;'>{line[2:]}</blockquote>"
            elif line.startswith('1. ') or line.startswith('- '):
                text = line[2:] if line.startswith('- ') else line[3:]
                # Bold themes or actions
                text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #f8fafc">\1</strong>', text)
                html_content += f"<li style='margin-bottom: 8px; color: #cbd5e1;'>{text}</li>"
            elif '**Generated on**' in line or '**Reviews Analyzed**' in line:
                html_content += f"<p style='font-size: 13px; color: #64748b; margin: 5px 0;'>{line}</p>"
            elif line == '---':
                html_content += "<hr style='border: none; border-top: 1px solid #1e293b; margin: 30px 0;'>"
            else:
                html_content += f"<p style='color: #cbd5e1; line-height: 1.6;'>{line}</p>"

        # Wrap in full email template
        full_html = f"""
        <html>
        <body style="background-color: #0f172a; font-family: 'Segoe UI', Arial, sans-serif; padding: 40px; color: #f8fafc;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #1e293b; border-radius: 20px; padding: 40px; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <span style="background: linear-gradient(135deg, #38bdf8, #818cf8); padding: 5px 15px; border-radius: 50px; font-size: 10px; font-weight: bold; color: white; letter-spacing: 2px; text-transform: uppercase;">Institutional Intelligence</span>
                </div>
                {html_content}
                <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #1e293b; text-align: center; font-size: 11px; color: #475569; letter-spacing: 1px; text-transform: uppercase;">
                    Strategic Feedback Engine v2.0 &bull; Powered by Gemini & Groq
                </div>
            </div>
        </body>
        </html>
        """
        return full_html

    def send_via_brevo(self, report_content, html_body):
        """Sends the email using Brevo (Sendinblue) API (HTTPS) to bypass SMTP blocks."""
        import requests
        from datetime import datetime
        print(f"Preparing to send HTML email via Brevo HTTP API to {self.recipient}...")
        
        headers = {
            "api-key": Config.BREVO_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "sender": {
                "name": "INDmoney Pulse Admin",
                "email": self.smtp_user  # Must be a verified sender in Brevo
            },
            "to": [
                {
                    "email": self.recipient
                }
            ],
            "subject": f"⚡ INDmoney Pulse: {datetime.now().strftime('%b %d')} Report",
            "htmlContent": html_body,
            "textContent": f"Hello,\n\nHere is your INDmoney Pulse report:\n\n{report_content}"
        }
        
        response = requests.post("https://api.brevo.com/v3/smtp/email", json=payload, headers=headers)
        
        if response.status_code in [200, 201]:
            print("Premium HTML Email sent successfully via Brevo API! ✅")
            return True
        else:
            print(f"Failed to send email via Brevo: {response.status_code} - {response.text} ❌")
            return False

    def send_email(self):
        """Sends the report via email, preferring Brevo API if configured."""
        if not self.recipient:
            print("Error: RECIPIENT_EMAIL is not set in .env")
            return False
            
        try:
            from datetime import datetime
            report_content = self.load_report()
            html_body = self.generate_html_body(report_content)
            
            # Prefer Brevo HTTP API if configured (Bypasses Railway SMTP Block, supports any recipient)
            if hasattr(Config, 'BREVO_API_KEY') and Config.BREVO_API_KEY:
                return self.send_via_brevo(report_content, html_body)
                
            # Fallback to Standard SMTP (Used by GitHub Actions)
            if not self.smtp_user or not self.smtp_pass:
                print("Error: Neither BREVO_API_KEY nor SMTP credentials are set in .env")
                return False

            print(f"Preparing to send HTML email via standard SMTP to {self.recipient}...")
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_user
            msg['To'] = self.recipient
            msg['Subject'] = f"⚡ INDmoney Pulse: {datetime.now().strftime('%b %d')} Report"
            
            # Text version for fallback
            text_body = f"Hello,\n\nHere is your INDmoney Pulse report:\n\n{report_content}"
            
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Connect and send
            print(f"Connecting to {self.smtp_host}:{self.smtp_port}...")
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_pass)
            
            server.sendmail(self.smtp_user, self.recipient, msg.as_string())
            server.quit()
            
            print("Premium HTML Email sent successfully via SMTP! ✅")
            return True
            
        except Exception as e:
            print(f"Failed to send email: {e} ❌")
            return False

if __name__ == "__main__":
    from datetime import datetime
    import sys
    custom_email = sys.argv[1] if len(sys.argv) > 1 else None
    mailer = Mailer(recipient=custom_email)
    mailer.send_email()
