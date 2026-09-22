#!/usr/bin/env python3
"""
==============================================================================
JNPHS (Jawahar Nagar Pinion High School) - Official Server & Email Relay
==============================================================================
Serves static website files and handles form submissions via SMTP to:
jnpschool@gmail.com

Usage:
  python server.py
  python server.py --port 5500

Configuration:
  Reads SMTP settings from '.env' file or system environment variables:
  - SMTP_HOST (e.g. smtp.gmail.com)
  - SMTP_PORT (e.g. 587)
  - SMTP_USER (e.g. jnpschool@gmail.com)
  - SMTP_PASS (e.g. your Gmail 16-character App Password)
  - RECIPIENT_EMAIL (default: jnpschool@gmail.com)
  - PORT (default: 5500)
==============================================================================
"""

import os
import sys
import json
import smtplib
import mimetypes
from datetime import datetime
from email.message import EmailMessage
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn

# Base project directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_env(env_path=os.path.join(BASE_DIR, '.env')):
    """Load environment variables from a .env file if present."""
    if not os.path.exists(env_path):
        return
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, val = line.split('=', 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    # Set only if not already in environment
                    if key and key not in os.environ:
                        os.environ[key] = val
    except Exception as e:
        print(f"[WARN] Error reading .env file: {e}")


# Load .env at startup
load_env()


def get_smtp_config():
    """Retrieve SMTP configuration settings."""
    return {
        'host': os.environ.get('SMTP_HOST', '').strip(),
        'port': int(os.environ.get('SMTP_PORT', '587').strip() or '587'),
        'user': os.environ.get('SMTP_USER', '').strip(),
        'pass': os.environ.get('SMTP_PASS', '').strip(),
        'recipient': os.environ.get('RECIPIENT_EMAIL', 'jnpschool@gmail.com').strip() or 'jnpschool@gmail.com',
    }


def is_smtp_configured(config):
    """Check if valid, non-placeholder SMTP credentials are provided."""
    if not config['host'] or not config['user'] or not config['pass']:
        return False
    if 'your_gmail_app_password' in config['pass'] or 'your_password' in config['pass']:
        return False
    return True


def send_email_smtp(subject, text_content, html_content=None, reply_to=None):
    """Send an email using configured SMTP settings."""
    config = get_smtp_config()
    if not is_smtp_configured(config):
        return False, "SMTP credentials are not configured on the server. Please set SMTP_HOST, SMTP_USER, and SMTP_PASS in .env or environment variables."

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = config['user']
    msg['To'] = config['recipient']
    if reply_to:
        msg['Reply-To'] = reply_to

    msg.set_content(text_content)
    if html_content:
        msg.add_alternative(html_content, subtype='html')

    try:
        # Use TLS on port 587 (or SSL on 465)
        if config['port'] == 465:
            with smtplib.SMTP_SSL(config['host'], config['port'], timeout=15) as server:
                server.login(config['user'], config['pass'])
                server.send_message(msg)
        else:
            with smtplib.SMTP(config['host'], config['port'], timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(config['user'], config['pass'])
                server.send_message(msg)
        return True, "Email sent successfully"
    except Exception as e:
        return False, f"SMTP error: {str(e)}"


class JNPHSRequestHandler(SimpleHTTPRequestHandler):
    """Custom request handler serving static files and API endpoints."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_POST(self):
        """Handle API POST requests."""
        if self.path == '/api/admissions':
            self.handle_admissions()
        elif self.path == '/api/contact':
            self.handle_contact()
        else:
            self.send_json_response(404, {'success': False, 'error': 'API endpoint not found'})

    def parse_json_body(self):
        """Safely parse JSON body from the POST request."""
        try:
            content_len = int(self.headers.get('Content-Length', 0))
            if content_len == 0:
                return None, "Empty request body"
            post_data = self.rfile.read(content_len).decode('utf-8')
            return json.loads(post_data), None
        except Exception as e:
            return None, f"Invalid JSON payload: {str(e)}"

    def send_json_response(self, status_code, data):
        """Send a JSON HTTP response."""
        response_bytes = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(response_bytes)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        """Handle CORS pre-flight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Accept')
        self.end_headers()

    def handle_admissions(self):
        """Process admissions form inquiry and send email via SMTP."""
        data, err = self.parse_json_body()
        if err:
            self.send_json_response(400, {'success': False, 'error': err})
            return

        student_name = (data.get('student_name') or '').strip()
        parent_name = (data.get('parent_name') or '').strip()
        phone_number = (data.get('phone_number') or '').strip()
        email_address = (data.get('email_address') or '').strip()
        class_applying = (data.get('class_applying') or '').strip()
        enquiry_message = (data.get('enquiry_message') or '').strip() or 'N/A'
        submission_time = (data.get('submission_time') or '').strip() or datetime.now().strftime('%d %B %Y, %I:%M %p')

        # Validation
        if not student_name or not parent_name or not phone_number or not email_address or not class_applying:
            self.send_json_response(400, {
                'success': False,
                'error': 'Missing required fields: student_name, parent_name, phone_number, email_address, class_applying'
            })
            return

        subject = f"New JNPHS Admission Enquiry — {student_name}"

        text_body = (
            f"Student Name: {student_name}\n"
            f"Parent/Guardian Name: {parent_name}\n"
            f"Phone Number: {phone_number}\n"
            f"Email Address: {email_address}\n"
            f"Class Applying For: {class_applying}\n"
            f"Message/Enquiry: {enquiry_message}\n"
            f"Submission Date & Time: {submission_time}\n"
        )

        html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; }}
  .container {{ max-width: 600px; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.08); border-top: 5px solid #D4AF37; }}
  .header {{ background: #0F2C59; color: #ffffff; padding: 24px; text-align: center; }}
  .header h2 {{ margin: 0 0 6px 0; font-size: 22px; }}
  .header p {{ margin: 0; color: #D4AF37; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }}
  .content {{ padding: 24px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
  th, td {{ padding: 12px 14px; text-align: left; border-bottom: 1px solid #e5e7eb; font-size: 14px; }}
  th {{ background: #f8fafc; color: #0F2C59; font-weight: 700; width: 40%; }}
  td {{ color: #1e293b; }}
  .footer {{ background: #f8fafc; padding: 16px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #e5e7eb; }}
</style></head>
<body>
  <div class="container">
    <div class="header">
      <h2>New Admission Enquiry</h2>
      <p>Jawahar Nagar Pinion High School (JNPHS)</p>
    </div>
    <div class="content">
      <table>
        <tr><th>Student Name</th><td><strong>{student_name}</strong></td></tr>
        <tr><th>Parent / Guardian Name</th><td>{parent_name}</td></tr>
        <tr><th>Phone Number</th><td><a href="tel:{phone_number}">{phone_number}</a></td></tr>
        <tr><th>Email Address</th><td><a href="mailto:{email_address}">{email_address}</a></td></tr>
        <tr><th>Class Applying For</th><td><strong>{class_applying}</strong></td></tr>
        <tr><th>Message / Enquiry</th><td>{enquiry_message}</td></tr>
        <tr><th>Submission Date & Time</th><td>{submission_time}</td></tr>
      </table>
    </div>
    <div class="footer">
      Jawahar Nagar Pinion High School • Marwadi Lane, Balaji Nagar, Secunderabad – 500087 • 040 2798 1051
    </div>
  </div>
</body>
</html>"""

        print(f"\n[ADMISSIONS ENQUIRY RECEIVED] Student: {student_name} | Class: {class_applying}")
        print(text_body)

        success, msg = send_email_smtp(subject, text_body, html_body, reply_to=email_address)
        if success:
            print(f"[SUCCESS] Email delivered to {get_smtp_config()['recipient']}")
            self.send_json_response(200, {
                'success': True,
                'message': 'Thank you. Your admission enquiry has been submitted successfully.'
            })
        else:
            print(f"[FAILED] Could not send email: {msg}")
            self.send_json_response(503 if "not configured" in msg else 500, {
                'success': False,
                'error': msg
            })

    def handle_contact(self):
        """Process general contact message and send email via SMTP."""
        data, err = self.parse_json_body()
        if err:
            self.send_json_response(400, {'success': False, 'error': err})
            return

        contact_name = (data.get('contact_name') or '').strip()
        contact_email = (data.get('contact_email') or '').strip()
        contact_subject = (data.get('contact_subject') or '').strip()
        contact_message = (data.get('contact_message') or '').strip()
        submission_time = (data.get('submission_time') or '').strip() or datetime.now().strftime('%d %B %Y, %I:%M %p')

        if not contact_name or not contact_email or not contact_subject or not contact_message:
            self.send_json_response(400, {
                'success': False,
                'error': 'Missing required fields: contact_name, contact_email, contact_subject, contact_message'
            })
            return

        subject = f"New JNPHS Contact Message — {contact_name}: {contact_subject}"

        text_body = (
            f"Full Name: {contact_name}\n"
            f"Email Address: {contact_email}\n"
            f"Subject: {contact_subject}\n"
            f"Message: {contact_message}\n"
            f"Submission Date & Time: {submission_time}\n"
        )

        html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; }}
  .container {{ max-width: 600px; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.08); border-top: 5px solid #D4AF37; }}
  .header {{ background: #0F2C59; color: #ffffff; padding: 24px; text-align: center; }}
  .header h2 {{ margin: 0 0 6px 0; font-size: 22px; }}
  .header p {{ margin: 0; color: #D4AF37; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }}
  .content {{ padding: 24px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
  th, td {{ padding: 12px 14px; text-align: left; border-bottom: 1px solid #e5e7eb; font-size: 14px; }}
  th {{ background: #f8fafc; color: #0F2C59; font-weight: 700; width: 35%; }}
  td {{ color: #1e293b; }}
  .footer {{ background: #f8fafc; padding: 16px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #e5e7eb; }}
</style></head>
<body>
  <div class="container">
    <div class="header">
      <h2>New Contact Message</h2>
      <p>Jawahar Nagar Pinion High School (JNPHS)</p>
    </div>
    <div class="content">
      <table>
        <tr><th>Sender Name</th><td><strong>{contact_name}</strong></td></tr>
        <tr><th>Sender Email</th><td><a href="mailto:{contact_email}">{contact_email}</a></td></tr>
        <tr><th>Subject</th><td>{contact_subject}</td></tr>
        <tr><th>Message</th><td>{contact_message}</td></tr>
        <tr><th>Submission Date & Time</th><td>{submission_time}</td></tr>
      </table>
    </div>
    <div class="footer">
      Jawahar Nagar Pinion High School • Marwadi Lane, Balaji Nagar, Secunderabad – 500087 • 040 2798 1051
    </div>
  </div>
</body>
</html>"""

        print(f"\n[CONTACT MESSAGE RECEIVED] Sender: {contact_name} | Subject: {contact_subject}")
        print(text_body)

        success, msg = send_email_smtp(subject, text_body, html_body, reply_to=contact_email)
        if success:
            print(f"[SUCCESS] Email delivered to {get_smtp_config()['recipient']}")
            self.send_json_response(200, {
                'success': True,
                'message': 'Thank you. Your message has been sent successfully.'
            })
        else:
            print(f"[FAILED] Could not send email: {msg}")
            self.send_json_response(503 if "not configured" in msg else 500, {
                'success': False,
                'error': msg
            })


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in separate threads for concurrency."""
    daemon_threads = True


def run(port=None):
    """Start the JNPHS HTTP server and API backend."""
    if port is None:
        port_env = os.environ.get('PORT', '5500').strip()
        port = int(port_env) if port_env.isdigit() else 5500

    # Parse port from command-line arguments if provided
    for i, arg in enumerate(sys.argv):
        if arg in ('--port', '-p') and i + 1 < len(sys.argv):
            try:
                port = int(sys.argv[i + 1])
            except ValueError:
                pass

    server_address = ('', port)
    httpd = ThreadedHTTPServer(server_address, JNPHSRequestHandler)

    config = get_smtp_config()
    smtp_status = "CONFIGURED" if is_smtp_configured(config) else "NOT CONFIGURED (Update .env to enable live email delivery)"

    print("=" * 70)
    print("  JAWAHAR NAGAR PINION HIGH SCHOOL (JNPHS) - WEB SERVER & API BACKEND")
    print("=" * 70)
    print(f"  Local Website URL : http://localhost:{port}/")
    print(f"  Admissions API    : http://localhost:{port}/api/admissions [POST]")
    print(f"  Contact API       : http://localhost:{port}/api/contact [POST]")
    print(f"  Target Recipient  : {config['recipient']}")
    print(f"  SMTP Status       : {smtp_status}")
    print("=" * 70)
    print(f"Server is running. Press Ctrl+C to stop.\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Server shutting down gracefully.")
        httpd.server_close()


if __name__ == '__main__':
    run()
