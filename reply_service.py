#!/usr/bin/env python3
"""
reply_service.py

A service that:
1. Polls the DB for emails that have a recommended_reply and haven't been sent yet (reply_sent=0 or NULL).
2. Interactively asks the user if they want to send the recommended reply.
3. If approved, sends the email via SMTP.
4. Marks the row as sent in the DB (reply_sent=1).

Requirements:
    pip install schedule

Usage:
    python reply_service.py
"""

import time
import schedule
import sqlite3
import smtplib
from email.message import EmailMessage

# --------------------------
# CONFIG
# --------------------------
DB_PATH = "emails.db"

# The address and credentials from which you want to send replies.
# For a real system, use environment variables or a secure store.
SMTP_SERVER = "smtp.gmail.com"       # e.g. Gmail
SMTP_PORT = 587                     # 587 for TLS, 465 for SSL
SMTP_USERNAME = "someone@gmail.com"
SMTP_PASSWORD = "password"

# Poll for new recommended replies every N seconds
POLL_INTERVAL_SECONDS = 10


# --------------------------
# 1. Ensure reply_sent column
# --------------------------
def init_reply_sent_column(db_path=DB_PATH):
    """
    Ensure there's a 'reply_sent' column in ingested_emails.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE ingested_emails ADD COLUMN reply_sent INTEGER")
    except sqlite3.OperationalError:
        # Column already exists
        pass
    conn.commit()
    conn.close()


# --------------------------
# 2. Fetch emails needing replies
# --------------------------
def fetch_emails_needing_reply(db_path=DB_PATH):
    """
    Returns a list of emails where recommended_reply is not empty,
    and reply_sent is NULL or 0.
    We'll also fetch from_addr, subject, recommended_reply to compose a reply.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT 
            id, 
            from_addr,
            subject,
            recommended_reply
        FROM ingested_emails
        WHERE 
            recommended_reply IS NOT NULL 
            AND recommended_reply != ''
            AND (reply_sent IS NULL OR reply_sent = 0)
        ORDER BY id ASC
    """)
    rows = c.fetchall()
    conn.close()

    emails = []
    for row in rows:
        email_id, from_addr, subject, rec_reply = row
        emails.append({
            "id": email_id,
            "from_addr": from_addr or "",
            "subject": subject or "",
            "recommended_reply": rec_reply or ""
        })
    return emails


# --------------------------
# 3. Send the reply via SMTP
# --------------------------
def send_email_reply(
    from_addr: str,
    to_addr: str,
    subject: str,
    body: str
):
    """
    Sends an email using the SMTP credentials provided.
    For a real system, handle exceptions, SSL/TLS properly, etc.
    """
    # Here 'from_addr' is the user who originally wrote the email, 
    # but we actually send from SMTP_USERNAME in most typical flows.
    # The user might want to reply directly to from_addr, so the "To" is that address.
    msg = EmailMessage()
    msg["From"] = SMTP_USERNAME       # The mailbox we are sending from
    msg["To"] = to_addr              # Typically the original sender
    msg["Subject"] = f"Re: {subject}" # "Re:" or whichever you want
    msg.set_content(body)

    # Connect to SMTP server
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()  # TLS
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)


# --------------------------
# 4. Mark as sent in DB
# --------------------------
def mark_reply_sent(email_id, db_path=DB_PATH):
    """
    Marks the email row as reply_sent=1
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        UPDATE ingested_emails
        SET reply_sent = 1
        WHERE id = ?
    """, (email_id,))
    conn.commit()
    conn.close()


# --------------------------
# 5. The scheduled job
# --------------------------
def job_ask_and_send_replies():
    """
    1) Fetch emails with recommended replies that haven't been sent.
    2) For each, show user the recommended reply and ask if they want to send it.
    3) If user approves, send it and mark as sent.
    """
    print("\n[Reply Service] Checking for recommended replies to send...")
    emails = fetch_emails_needing_reply(DB_PATH)
    if not emails:
        print("[Reply Service] No pending replies found.")
        return

    print(f"[Reply Service] Found {len(emails)} email(s) with recommended replies.")
    for email_data in emails:
        email_id = email_data["id"]
        from_addr = email_data["from_addr"]
        subject = email_data["subject"]
        recommended_reply = email_data["recommended_reply"]

        print("\n--------------------------------------------------")
        print(f"Email ID: {email_id}")
        print(f"From:     {from_addr}")
        print(f"Subject:  {subject}")
        print("Recommended Reply:")
        print(recommended_reply)
        print("--------------------------------------------------")

        # Ask user
        choice = input("Send this recommended reply? (y/n) ").strip().lower()
        if choice == "y":
            # Send the reply
            # Typically we reply to the original 'from_addr' on the email
            # The recommended_reply is the body
            send_email_reply(
                from_addr=from_addr,       # Original sender
                to_addr=from_addr,         # Typically the same
                subject=subject,
                body=recommended_reply
            )
            mark_reply_sent(email_id, DB_PATH)
            print(f"[Reply Service] Reply sent and marked for email ID {email_id}")
        else:
            print("[Reply Service] Skipped sending.")


# --------------------------
# MAIN
# --------------------------
if __name__ == "__main__":
    # 1) Ensure reply_sent column
    init_reply_sent_column(DB_PATH)

    # 2) Schedule the job
    schedule.every(POLL_INTERVAL_SECONDS).seconds.do(job_ask_and_send_replies)
    print(f"Reply Service started. Checking every {POLL_INTERVAL_SECONDS}s. Press Ctrl+C to exit.")

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Reply Service] Stopped by user.")
