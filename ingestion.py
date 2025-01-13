#!/usr/bin/env python3
"""
ingestion.py

Component 1: Ingestion (with Base64 for attachments)
----------------------------------------------------
- Connects to Gmail (or any IMAP) using IMAP4_SSL.
- Fetches UNSEEN emails every X seconds (schedule).
- Parses each email (headers, body, attachments).
- Stores them in local SQLite DB (ingested_emails table).
- Attachments are base64-encoded to avoid JSON serialization errors.

Requirements:
    pip install schedule beautifulsoup4

Usage:
    python ingestion.py
"""

import time
import schedule
import imaplib
import email
from email import policy
from email.header import decode_header
import sqlite3
import json
import base64  # for attachments encoding

# Optional: for HTML-to-text cleaning
try:
    from bs4 import BeautifulSoup
    HAS_BEAUTIFULSOUP = True
except ImportError:
    HAS_BEAUTIFULSOUP = False


# -------------------------
# IMAP CONFIG (Update!)
# -------------------------
IMAP_SERVER = "imap.gmail.com"
IMAP_USER = "someone@gmail.com"
IMAP_PASS = "password"
MAILBOX_FOLDER = "INBOX"

# -------------------------
# Database Config
# -------------------------
DB_PATH = "emails.db"


def init_db(db_path: str = DB_PATH):
    """
    Creates the 'ingested_emails' table if it doesn't exist.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS ingested_emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_addr TEXT,
        subject TEXT,
        date_str TEXT,
        body TEXT,
        attachments TEXT,
        inserted_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()


def fetch_emails_from_imap(
    imap_server: str,
    imap_user: str,
    imap_password: str,
    mailbox_folder: str = "INBOX",
    search_criteria: str = "UNSEEN",
    mark_as_seen: bool = False
):
    """
    Connect to the IMAP server, fetch emails from the specified mailbox folder
    based on the given search criteria (e.g. "UNSEEN"), parse them,
    and return as a list of dicts.
    """
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(imap_user, imap_password)

        mail.select(mailbox_folder)
        status, message_ids = mail.search(None, search_criteria)
        if status != "OK":
            print(f"[ERROR] Could not search mailbox. Status: {status}")
            mail.logout()
            return []

        email_data_list = []
        for msg_id in message_ids[0].split():
            _, msg_data = mail.fetch(msg_id, "(RFC822)")
            if not msg_data or not msg_data[0]:
                continue

            raw_email = msg_data[0][1]
            if not raw_email:
                continue

            parsed_email = email.message_from_bytes(raw_email, policy=policy.default)
            email_dict = process_email(parsed_email)
            email_dict["imap_msg_id"] = msg_id.decode()

            if mark_as_seen:
                mail.store(msg_id, "+FLAGS", "\\Seen")

            email_data_list.append(email_dict)

        mail.logout()
        return email_data_list

    except Exception as e:
        print(f"[ERROR] Exception during IMAP fetch: {e}")
        return []


def process_email(parsed_email):
    """
    Convert a parsed email object into a dictionary 
    with keys: subject, from, date, body, attachments.
    """
    email_dict = {}

    subject, encoding = decode_header(parsed_email.get("Subject"))[0] if parsed_email.get("Subject") else (None, None)
    if isinstance(subject, bytes):
        try:
            subject = subject.decode(encoding if encoding else "utf-8", errors="ignore")
        except:
            subject = subject.decode(errors="ignore")
    email_dict["subject"] = subject if subject else ""

    email_dict["from"] = parsed_email.get("From", "")
    email_dict["to"] = parsed_email.get("To", "")
    email_dict["date"] = parsed_email.get("Date", "")

    email_body = get_email_body(parsed_email)
    if HAS_BEAUTIFULSOUP and is_html_content(parsed_email):
        email_body = clean_html(email_body)

    email_dict["body"] = email_body.strip() if isinstance(email_body, str) else ""

    email_dict["attachments"] = extract_attachments(parsed_email)

    return email_dict


def get_email_body(msg):
    """
    Prefer text/plain, else fallback to text/html if no text/plain found.
    """
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in disposition:
                continue
            if ctype == "text/plain":
                return part.get_content() or ""

        for part in msg.walk():
            ctype = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in disposition:
                continue
            if ctype == "text/html":
                return part.get_content() or ""
        return ""
    else:
        return msg.get_content() or ""


def is_html_content(msg):
    """
    Check if the message or any part is HTML.
    """
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                return True
        return False
    else:
        return msg.get_content_type() == "text/html"


def clean_html(html_text):
    """
    Convert HTML to plain text.
    """
    if not HAS_BEAUTIFULSOUP:
        return html_text
    soup = BeautifulSoup(html_text, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def extract_attachments(msg):
    """
    Extract attachments and base64-encode the payload so it can be JSON-serialized.
    Returns a list of { "filename": str, "data_b64": str }.
    """
    attachments = []
    if msg.is_multipart():
        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in content_disposition:
                filename = part.get_filename()
                payload = part.get_payload(decode=True)  # raw bytes
                if payload is not None:
                    data_b64 = base64.b64encode(payload).decode("ascii")
                    attachments.append({
                        "filename": filename,
                        "data_b64": data_b64
                    })
    return attachments


def store_parsed_email_in_db(
    from_addr: str,
    subject: str,
    date_str: str,
    body: str,
    attachments: list,
    db_path: str = DB_PATH
):
    """
    Inserts one parsed email record into the 'ingested_emails' table.
    Attachments are stored as a JSON string containing base64-encoded payloads.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    attachments_json = json.dumps(attachments)  # no error now, since data is base64 string
    c.execute("""
        INSERT INTO ingested_emails 
        (from_addr, subject, date_str, body, attachments)
        VALUES (?, ?, ?, ?, ?)
    """, (from_addr, subject, date_str, body, attachments_json))

    conn.commit()
    conn.close()


def job_fetch_and_store():
    """
    Scheduled job that checks for new UNSEEN emails, parses them,
    and stores them in 'ingested_emails' table.
    """
    print("\n[Job] Checking for new UNSEEN emails...")

    emails = fetch_emails_from_imap(
        imap_server=IMAP_SERVER,
        imap_user=IMAP_USER,
        imap_password=IMAP_PASS,
        mailbox_folder=MAILBOX_FOLDER,
        search_criteria="UNSEEN",
        mark_as_seen=False
    )

    if emails:
        print(f"[Job] Fetched {len(emails)} new email(s). Storing in DB...")
        for i, email_data in enumerate(emails, start=1):
            from_addr = email_data["from"]
            subject = email_data["subject"]
            date_str = email_data["date"]
            body = email_data["body"]
            attachments = email_data["attachments"]

            store_parsed_email_in_db(
                from_addr=from_addr,
                subject=subject,
                date_str=date_str,
                body=body,
                attachments=attachments,
                db_path=DB_PATH
            )
            print(f"  Stored Email #{i}")
    else:
        print("[Job] No new emails found.")


if __name__ == "__main__":
    init_db(DB_PATH)
    schedule.every(5).seconds.do(job_fetch_and_store)
    print("Starting scheduled email ingestion. Press Ctrl+C to exit.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Info] Ingestion stopped by user.")
