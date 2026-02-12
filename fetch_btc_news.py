import os
import requests
import pandas as pd
from git import Repo
from datetime import datetime
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()
API_KEY = os.getenv("SERPAPI_KEY")
REPO_PATH = '.' 

def push_to_github(filenames):
    """
    Stages, commits, and pushes updated news files to GitHub.
    """
    try:
        # Check for .gitignore to protect your .env file
        if not os.path.exists('.gitignore'):
            with open('.gitignore', 'w') as f:
                f.write(".env\n__pycache__/\nvenv/\n*.pkl\n")
            print("✅ Created .gitignore to protect sensitive files.")

        repo = Repo(REPO_PATH)
        
        # Add all modified news files and .gitignore
        files_to_add = filenames + [".gitignore"]
        repo.index.add(files_to_add)
        
        commit_message = f"Auto-update: Crypto news {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        repo.index.commit(commit_message)
        
        origin = repo.remote(name='origin')
        origin.push(refspec='main:main')
        print(f"🚀 Successfully pushed updates for {len(filenames)} assets to GitHub!")
    except Exception as e:
        print(f"❌ Git Error: {e}")

def fetch_and_sync_news():
    """
    Iterates through multiple coins, fetches news via SerpApi, 
    updates local CSVs, and pushes to GitHub.
    """
    if not API_KEY:
        print("❌ Error: SERPAPI_KEY not found in .env file.")
        return

    # Define the assets and their storage paths
    COINS = {
        "bitcoin": "news/bitcoin_news.csv",
        "ethereum": "news/ethereum_news.csv",
        "solana": "news/solana_news.csv",
        "usdc": "news/usdc_news.csv",
        "tether": "news/tether_news.csv"
    }

    updated_files = []

    for symbol, csv_path in COINS.items():
        try:
            print(f"\n📡 Fetching latest news for {symbol.upper()}...")
            
            # Construct API Parameters
            params = {
                "engine": "google_news",
                "q": symbol,
                "api_key": API_KEY
            }
            
            response = requests.get("https://serpapi.com/search.json", params=params)
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
            
            if not new_items:
                print(f"⚠️ No new stories found for {symbol}.")
                continue
            
            new_df = pd.DataFrame(new_items)

            # Prepend Logic: New data goes to the top
            if os.path.exists(csv_path):
                existing_df = pd.read_csv(csv_path)
                combined_df = pd.concat([new_df, existing_df], ignore_index=True)
            else:
                combined_df = new_df

            # Clean: Remove duplicates based on link, keeping the newest occurrence
            combined_df.drop_duplicates(subset=['link'], keep='first', inplace=True)
            
            # Ensure the news/ directory exists
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            
            # Save the updated file
            combined_df.to_csv(csv_path, index=False, encoding='utf-8')
            updated_files.append(csv_path)
            print(f"✅ Updated {csv_path} ({len(new_items)} new items found).")

        except Exception as e:
            print(f"❌ Error syncing {symbol}: {e}")

    # 4. Final step: Push all updated files in one commit
    if updated_files:
        push_to_github(updated_files)
    else:
        print("ℹ️ No files were updated. Skipping Git push.")

if __name__ == "__main__":
    fetch_and_sync_news()