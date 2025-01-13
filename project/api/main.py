from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import json
from typing import List, Optional
from pydantic import BaseModel
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database path
DB_PATH = "../../emails.db"

# SMTP settings from environment variables
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "someone@gmail.com"
SMTP_PASSWORD = "password"

# Validate SMTP settings
if not all([SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD]):
    logger.error("Missing SMTP configuration!")

class Email(BaseModel):
    id: int
    from_addr: str
    subject: str
    date_str: str
    body: str
    category: Optional[str]
    priority: Optional[str]
    is_spam: Optional[bool]
    is_ads: Optional[bool]
    summary: Optional[str]
    recommended_reply: Optional[str]
    reply_sent: Optional[bool]

@app.get("/api/emails", response_model=List[Email])
async def get_emails():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id,
                from_addr,
                subject,
                date_str,
                body,
                category,
                priority,
                is_spam,
                is_ads,
                summary,
                recommended_reply,
                reply_sent
            FROM ingested_emails
            ORDER BY id DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        emails = []
        for row in rows:
            email = {
                "id": row[0],
                "from_addr": row[1],
                "subject": row[2],
                "date_str": row[3],
                "body": row[4],
                "category": row[5],
                "priority": row[6],
                "is_spam": bool(row[7]) if row[7] is not None else False,
                "is_ads": bool(row[8]) if row[8] is not None else False,
                "summary": row[9],
                "recommended_reply": row[10],
                "reply_sent": bool(row[11]) if row[11] is not None else False
            }
            emails.append(email)
            
        return emails
    except Exception as e:
        logger.error(f"Error fetching emails: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/emails/{email_id}/send-reply")
async def send_reply(email_id: int):
    conn = None
    try:
        # Log the attempt
        logger.info(f"Attempting to send reply for email ID: {email_id}")
        
        # 1. Get email details from database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT from_addr, subject, recommended_reply
            FROM ingested_emails
            WHERE id = ?
        """, (email_id,))
        
        row = cursor.fetchone()
        if not row:
            logger.error(f"Email ID {email_id} not found")
            raise HTTPException(status_code=404, detail="Email not found")
            
        to_addr, subject, reply_body = row
        
        # Log email details (excluding sensitive info)
        logger.info(f"Sending reply to: {to_addr}, Subject: {subject}")
        
        # 2. Send email via SMTP
        msg = EmailMessage()
        msg["From"] = SMTP_USERNAME
        msg["To"] = to_addr
        msg["Subject"] = f"Re: {subject}"
        msg.set_content(reply_body)
        
        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                logger.info("Connecting to SMTP server...")
                server.starttls()
                logger.info("TLS started, attempting login...")
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                logger.info("Login successful, sending message...")
                server.send_message(msg)
                logger.info("Message sent successfully")
        except smtplib.SMTPException as smtp_error:
            logger.error(f"SMTP Error: {str(smtp_error)}")
            raise HTTPException(status_code=500, detail=f"SMTP Error: {str(smtp_error)}")
            
        # 3. Mark as sent in database
        cursor.execute("""
            UPDATE ingested_emails
            SET reply_sent = 1
            WHERE id = ?
        """, (email_id,))
        
        conn.commit()
        logger.info(f"Email ID {email_id} marked as sent in database")
        
        return {"status": "success", "message": "Reply sent successfully"}
    except Exception as e:
        logger.error(f"Error sending reply: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()
