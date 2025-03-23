import os
import time
import pandas as pd
import tweepy
import psycopg2
from sqlalchemy import create_engine, text

# Load environment variables from Kubernetes secrets or config map
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

DB_HOST = os.getenv("DB_HOST", "postgres-service")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "tweetsdb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

EXCEL_FILE_PATH = "/data/twitter_accounts.xlsx"

# Debug Log: Print Database Connection Details (Without Password)
print(f"[DEBUG] Connecting to DB: postgres@{DB_HOST}:{DB_PORT}/{DB_NAME}", flush=True)

# Set up Twitter API authentication (Using Twitter API v2)
try:
    client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN, wait_on_rate_limit=True)
    print("[DEBUG] Twitter API v2 Authentication Successful!", flush=True)
except Exception as e:
    print(f"[ERROR] Twitter API v2 Authentication Failed: {e}", flush=True)

# PostgreSQL connection
try:
    engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    print("[DEBUG] PostgreSQL Connection Established!", flush=True)
except Exception as e:
    print(f"[ERROR] PostgreSQL Connection Failed: {e}", flush=True)

# Create tweets table if it doesn't exist
def create_tweets_table():
    print("[DEBUG] Checking/Creating 'tweets' table in PostgreSQL...", flush=True)
    query = text("""
    CREATE TABLE IF NOT EXISTS tweets (
        id SERIAL PRIMARY KEY,
        tweet_id BIGINT UNIQUE,
        username VARCHAR(50),
        tweet_text TEXT,
        created_at TIMESTAMP,
        collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    try:
        with engine.connect() as conn:
            conn.execute(query)
            conn.commit()
        print("[DEBUG] Table 'tweets' verified/created successfully!", flush=True)
    except Exception as e:
        print(f"[ERROR] Failed to create table: {e}", flush=True)

# Function to scrape tweets using Twitter API v2
def scrape_tweets(username):
    print(f"[DEBUG] Fetching tweets for {username}...", flush=True)
    try:
        # Get user ID from username
        user = client.get_user(username=username, user_fields=["id"])
        if user.data is None:
            print(f"[WARNING] User {username} not found!", flush=True)
            return pd.DataFrame()

        user_id = user.data.id

        # Fetch latest tweets
        tweets_data = []
        tweets = client.get_users_tweets(id=user_id, max_results=10, tweet_fields=["created_at", "text"])
        
        if tweets.data:
            for tweet in tweets.data:
                tweets_data.append({
                    "tweet_id": tweet.id,
                    "username": username,
                    "tweet_text": tweet.text,
                    "created_at": tweet.created_at
                })
            print(f"[INFO] Retrieved {len(tweets_data)} tweets for {username}.", flush=True)
        else:
            print(f"[WARNING] No tweets found for {username}.", flush=True)

        return pd.DataFrame(tweets_data)
    except Exception as e:
        print(f"[ERROR] Error fetching tweets for {username}: {e}", flush=True)
        return pd.DataFrame()

# Function to read Twitter handles from Excel
def get_twitter_handles():
    print("[DEBUG] Reading Twitter handles from Excel...", flush=True)
    try:
        df = pd.read_excel(EXCEL_FILE_PATH)
        
        # Debug: Print detected column names
        print(f"[DEBUG] Columns found in Excel: {df.columns.tolist()}", flush=True)
        
        # Normalize column names (remove spaces)
        df.columns = df.columns.str.strip()

        if "Twitter Handle" in df.columns:
            handles = df["Twitter Handle"].dropna().unique().tolist()
            print(f"[INFO] Found {len(handles)} Twitter handles to scrape.", flush=True)
            return handles
        else:
            print("[ERROR] Column 'Twitter Handle' not found in Excel!", flush=True)
            return []
        
    except Exception as e:
        print(f"[ERROR] Error reading Excel file: {e}", flush=True)
        return []

# Store tweets in PostgreSQL
def store_tweets(df):
    if not df.empty:
        print(f"[DEBUG] Storing {len(df)} tweets in the database...", flush=True)
        try:
            df.to_sql("tweets", engine, if_exists="append", index=False)
            print(f"[INFO] Successfully stored {len(df)} tweets in the database.", flush=True)
        except Exception as e:
            print(f"[ERROR] Error inserting into DB: {e}", flush=True)
    else:
        print("[WARNING] No tweets to store. Skipping database insertion.", flush=True)

# Main job function
def job():
    print("[DEBUG] Starting the scraping job...", flush=True)
    create_tweets_table()
    twitter_handles = get_twitter_handles()
    if not twitter_handles:
        print("[WARNING] No Twitter handles found. Exiting job.", flush=True)
        return
    
    for username in twitter_handles:
        print(f"[INFO] Processing {username}...", flush=True)
        tweets_df = scrape_tweets(username)
        store_tweets(tweets_df)

    print("[DEBUG] Scraping job completed!", flush=True)

if __name__ == "__main__":
    while True:
        print("[DEBUG] Starting daily Twitter scraping job...", flush=True)
        job()
        print("[DEBUG] Job completed. Sleeping for 24 hours...", flush=True)
        time.sleep(86400)  # Sleep for 24 hours

