import os
import requests
import pandas as pd
from git import Repo
from datetime import datetime
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()
API_KEY = os.getenv("SERPAPI_KEY")
CSV_FILE = 'news/bitcoin_news.csv'
REPO_PATH = '.' 

# Construct URL using the key from .env
# Note: Adjust the base URL as per SerpApi's requirements
API_URL = f"https://serpapi.com/search.json?engine=google_news&q=bitcoin&api_key={API_KEY}"

def push_to_github(filename):
    try:
        # Check for .gitignore to protect your .env file
        if not os.path.exists('.gitignore'):
            with open('.gitignore', 'w') as f:
                f.write(".env\n__pycache__/\n")
            print("Created .gitignore to protect your .env file.")

        repo = Repo(REPO_PATH)
        repo.index.add([filename, ".gitignore"]) # Ensure .gitignore is also tracked
        
        commit_message = f"Auto-update: Bitcoin news {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        repo.index.commit(commit_message)
        
        origin = repo.remote(name='origin')
        origin.push(refspec='main:main')
        print("Successfully pushed to GitHub!")
    except Exception as e:
        print(f"Git Error: {e}")

def fetch_and_sync_news():
    if not API_KEY:
        print("Error: SERPAPI_KEY not found in .env file.")
        return

    try:
        print("Fetching latest news...")
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
        
        new_items = []
        for item in data.get("news_results", []):
            # Extract main info and sub-stories
            entries = item.get("stories", [item])
            for entry in entries:
                if entry.get("link"):
                    new_items.append({
                        "date": entry.get("date"),
                        "sources": entry.get("source", {}).get("name") if isinstance(entry.get("source"), dict) else entry.get("source"),
                        "title": entry.get("title"),
                        "link": entry.get("link")
                    })
        
        new_df = pd.DataFrame(new_items)

        # Prepend Logic
        if os.path.exists(CSV_FILE):
            existing_df = pd.read_csv(CSV_FILE)
            combined_df = pd.concat([new_df, existing_df], ignore_index=True)
        else:
            combined_df = new_df

        # Clean and Save
        combined_df.drop_duplicates(subset=['link'], keep='first', inplace=True)
        combined_df.to_csv(CSV_FILE, index=False, encoding='utf-8')
        
        push_to_github(CSV_FILE)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_and_sync_news()