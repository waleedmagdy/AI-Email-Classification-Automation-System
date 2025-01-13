#!/usr/bin/env python3
"""
gui.py

A Streamlit-based GUI dashboard for our AI Email System.

Features:
1. Displays a data table of ingested emails from 'emails.db'.
2. Visualizes category distribution (bar chart).
3. Shows spam vs non-spam stats (bar chart).
4. Displays a subset of "Ads" emails in a separate table.
5. Responsive and easy to extend.

Usage:
    pip install streamlit pandas altair
    streamlit run gui.py
"""

import streamlit as st
import sqlite3
import pandas as pd
import altair as alt

# Path to your local SQLite database
DB_PATH = "emails.db"


def load_data():
    """
    Load the entire ingested_emails table from the local SQLite database
    into a pandas DataFrame.
    """
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT
        id,
        from_addr,
        subject,
        date_str,
        category,
        is_spam,
        is_ads,
        summary,
        recommended_reply,
        reply_sent,
        inserted_at
    FROM ingested_emails
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def main():
    st.set_page_config(page_title="AI Email System Dashboard", layout="wide")
    st.title("AI Email System Dashboard")

    st.markdown(
        """
        This dashboard displays real-time information from our 
        **AI-driven email system**. It shows:
        - **Ingested emails** and their metadata
        - **Categorization** and **spam detection** results
        - A quick look at **ads** and recommended replies
        """
    )

    # Load data from DB
    df = load_data()

    # --- SECTION 1: Table of all Emails ---
    st.subheader("1. Ingested Emails (Table)")
    st.write("A direct view of your email records:")
    st.dataframe(df, use_container_width=True)

    # --- SECTION 2: Category Distribution ---
    st.subheader("2. Category Distribution")
    if "category" in df.columns and not df.empty:
        cat_counts = df["category"].value_counts().reset_index()
        cat_counts.columns = ["category", "count"]

        cat_chart = (
            alt.Chart(cat_counts)
            .mark_bar()
            .encode(
                x=alt.X("category:N", sort=None),
                y="count:Q",
                tooltip=["category", "count"]
            )
            .properties(width=600, height=400)
        )
        st.altair_chart(cat_chart, use_container_width=True)
    else:
        st.info("No category data available.")

    # --- SECTION 3: Spam vs. Non-Spam ---
    st.subheader("3. Spam vs. Non-Spam")
    if "is_spam" in df.columns and not df.empty:
        spam_counts = df["is_spam"].value_counts().reset_index()
        spam_counts.columns = ["is_spam", "count"]

        # Convert 0/1 to 'Not Spam'/ 'Spam' for clarity
        spam_counts["is_spam"] = spam_counts["is_spam"].apply(lambda x: "Spam" if x == 1 else "Not Spam")

        spam_chart = (
            alt.Chart(spam_counts)
            .mark_bar()
            .encode(
                x=alt.X("is_spam:N", sort=None),
                y="count:Q",
                tooltip=["is_spam", "count"]
            )
            .properties(width=400, height=300)
        )
        st.altair_chart(spam_chart, use_container_width=True)
    else:
        st.info("No spam data available.")

    # --- SECTION 4: Ads Emails ---
    st.subheader("4. Ads Emails")
    if "is_ads" in df.columns and not df.empty:
        ads_df = df[df["is_ads"] == 1]
        st.write("Below are emails flagged as 'Ads':")
        st.dataframe(
            ads_df[["id", "from_addr", "subject", "summary"]].reset_index(drop=True),
            use_container_width=True
        )
    else:
        st.info("No ads data available.")

    # --- SECTION 5: Next Steps / Footer ---
    st.markdown(
        """
        ---
        **Next Steps**:
        - Adjust your ingestion or classification scripts to feed more columns or refined data.
        - Add interactive filters (e.g., date range, search by sender).
        - Include advanced charts (time series of incoming emails, priority levels, etc.).
        - Integrate with the reply service for a fully interactive UI.
        """
    )


if __name__ == "__main__":
    main()
