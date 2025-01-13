#!/usr/bin/env python3
"""
classification_service.py

A service to classify & summarize emails stored by ingestion.py, using Ollama's /v1/completions endpoint.
We handle extra text like "json" prefix or triple backticks, and attempt to extract the valid JSON object.

Steps:
1. Periodically fetch unclassified emails from 'ingested_emails' (where category IS NULL).
2. For each email, call Ollama (/v1/completions, with "stream": false).
3. The prompt instructs the model to return valid JSON (category, priority, spam/ads, summary, recommended_reply).
4. We remove triple backticks if present, remove 'json' lines, and then use a regex to find the JSON block.
5. We store classification results in `ingested_emails`.

Requirements:
    pip install schedule requests

Usage:
    1) Run Ollama:   ./ollama serve
    2) python classification_service.py
"""

import time
import schedule
import sqlite3
import requests
import json
import re

DB_PATH = "emails.db"
OLLAMA_API_URL = "http://localhost:11434/v1/completions"
MODEL_NAME = "llama3.1"
POLL_INTERVAL_SECONDS = 10
GENERATE_REPLY = True


def init_classification_columns(db_path=DB_PATH):
    """
    Ensures 'ingested_emails' has the columns:
      category, priority, is_spam, is_ads, summary, recommended_reply.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    alters = [
        "ALTER TABLE ingested_emails ADD COLUMN category TEXT",
        "ALTER TABLE ingested_emails ADD COLUMN priority TEXT",
        "ALTER TABLE ingested_emails ADD COLUMN is_spam INTEGER",
        "ALTER TABLE ingested_emails ADD COLUMN is_ads INTEGER",
        "ALTER TABLE ingested_emails ADD COLUMN summary TEXT",
        "ALTER TABLE ingested_emails ADD COLUMN recommended_reply TEXT"
    ]
    for stmt in alters:
        try:
            c.execute(stmt)
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()


def fetch_unclassified_emails(db_path=DB_PATH):
    """
    Return rows where 'category' is NULL, meaning unclassified.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT id, from_addr, subject, date_str, body
        FROM ingested_emails
        WHERE category IS NULL
        ORDER BY id ASC
    """)
    rows = c.fetchall()
    conn.close()

    emails = []
    for row in rows:
        email_id, from_addr, subject, date_str, body = row
        emails.append({
            "id": email_id,
            "from_addr": from_addr or "",
            "subject": subject or "",
            "date_str": date_str or "",
            "body": body or ""
        })
    return emails


def call_ollama_classification_and_summary(from_addr, subject, body):
    """
    1) Build a single prompt that includes From, Subject, Body.
    2) Use a single POST to Ollama /v1/completions with "stream": false.
    3) We expect the final text in "completion".
    4) That text should be valid JSON, but if it has extra lines,
       we do additional processing to extract the JSON substring.
    """

    # Prompt strongly instructs the model to return valid JSON only.
    # Show an example to help ensure compliance.
    prompt = (
        f"You are an AI email classifier. Analyze the entire email context to determine:\n"
        f'  - "category": one of ["Work", "Personal", "Ads", "Spam", "Other"]\n'
        f'  - "priority": one of ["High", "Medium", "Low"]\n'
        f"  - \"is_spam\": true or false\n"
        f"  - \"is_ads\": true or false\n"
        f"  - \"summary\": a concise summary\n"
        + (f'  - "recommended_reply": a short recommended response\n' if GENERATE_REPLY else "")
        + "\nOutput only valid JSON (no extra text).\n\n"
        "Email Context:\n"
        f"From: {from_addr}\n"
        f"Subject: {subject}\n"
        f"Body:\n"
        f"{body}\n\n"
        "EXAMPLE JSON:\n"
        "{\n"
        '  "category": "Spam",\n'
        '  "priority": "Low",\n'
        '  "is_spam": true,\n'
        '  "is_ads": true,\n'
        '  "summary": "A short summary here"'
        + (',\n  "recommended_reply": "Possible short reply here"\n' if GENERATE_REPLY else "\n")
        + "}\n"
    )

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    try:
        resp = requests.post(OLLAMA_API_URL, json=payload, timeout=120)
        resp.raise_for_status()
    except requests.RequestException as e:
        print("[ERROR] Ollama request failed:", e)
        return default_classification()

    # Parse JSON from the /v1/completions response
    try:
        resp_data = resp.json()
    except json.JSONDecodeError:
        print("[ERROR] Could not parse JSON from the Ollama response.")
        return default_classification()

    # Usually, "completion" or "choices[0].text" will hold the final text
    final_text = ""
    if "completion" in resp_data:
        final_text = resp_data["completion"].strip()
    elif "choices" in resp_data and isinstance(resp_data["choices"], list) and len(resp_data["choices"]) > 0:
        final_text = resp_data["choices"][0].get("text", "").strip()
    else:
        print("[ERROR] No 'completion' or 'choices[0].text' found in response.")
        return default_classification()

    if not final_text:
        print("[ERROR] Received an empty 'completion' from Ollama.")
        return default_classification()

    # 1) Strip triple backticks if present
    final_text = re.sub(r'^```+', '', final_text.strip())
    final_text = re.sub(r'```+$', '', final_text).strip()

    # 2) Remove a leading "json" line if present (like "json\n{...}")
    final_text = re.sub(r'^json[\s\r\n]+', '', final_text, flags=re.IGNORECASE).strip()

    # 3) Extract the first { ... } block in case there's extra text:
    match = re.search(r'\{.*\}', final_text, flags=re.DOTALL)
    if not match:
        print("[ERROR] Could not find JSON braces in final text:\n", final_text)
        return default_classification()

    final_text_json = match.group(0).strip()

    # Now parse the substring as JSON
    try:
        result = json.loads(final_text_json)
        classification = {
            "category": result.get("category", "Other"),
            "priority": result.get("priority", "Low"),
            "is_spam": bool(result.get("is_spam", False)),
            "is_ads": bool(result.get("is_ads", False)),
            "summary": result.get("summary", ""),
            "recommended_reply": result.get("recommended_reply", "") if GENERATE_REPLY else ""
        }
        return classification
    except json.JSONDecodeError:
        print("[ERROR] The model did not return valid JSON.\nReturned text:", final_text_json)
        return default_classification()


def default_classification():
    """Fallback classification if something goes wrong."""
    return {
        "category": "Other",
        "priority": "Low",
        "is_spam": False,
        "is_ads": False,
        "summary": "",
        "recommended_reply": ""
    }


def store_classification_results(
    email_id,
    category,
    priority,
    is_spam,
    is_ads,
    summary,
    recommended_reply,
    db_path=DB_PATH
):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        UPDATE ingested_emails
        SET category = ?,
            priority = ?,
            is_spam = ?,
            is_ads = ?,
            summary = ?,
            recommended_reply = ?
        WHERE id = ?
    """, (category, priority, int(is_spam), int(is_ads), summary, recommended_reply, email_id))
    conn.commit()
    conn.close()


def job_classify_emails():
    print("\n[Classifier Job] Checking for unclassified emails...")
    emails = fetch_unclassified_emails(DB_PATH)
    if not emails:
        print("[Classifier Job] No unclassified emails found.")
        return

    print(f"[Classifier Job] Found {len(emails)} unclassified email(s). Processing...")

    for email_data in emails:
        email_id = email_data["id"]
        from_addr = email_data["from_addr"]
        subject = email_data["subject"]
        body = email_data["body"]

        classification = call_ollama_classification_and_summary(from_addr, subject, body)

        store_classification_results(
            email_id=email_id,
            category=classification["category"],
            priority=classification["priority"],
            is_spam=classification["is_spam"],
            is_ads=classification["is_ads"],
            summary=classification["summary"],
            recommended_reply=classification["recommended_reply"],
            db_path=DB_PATH
        )

        print(
            f"  - Email ID {email_id} => "
            f"Category={classification['category']}, "
            f"Priority={classification['priority']}, "
            f"Spam={classification['is_spam']}, "
            f"Ads={classification['is_ads']}"
        )
        if GENERATE_REPLY and classification["recommended_reply"]:
            print("    Recommended Reply:", classification["recommended_reply"])


if __name__ == "__main__":
    init_classification_columns(DB_PATH)

    schedule.every(POLL_INTERVAL_SECONDS).seconds.do(job_classify_emails)
    print(f"Classification service started. Checking every {POLL_INTERVAL_SECONDS}s. Press Ctrl+C to exit.")

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Classifier] Stopped by user.")