import praw
import time
import os
from dotenv import load_dotenv
import mongoman

# Load environment variables
load_dotenv()

# === 1. Reddit Auth ===
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent='NSFW scraper'
)

# === 2. Scraper Function ===
def scrape_subreddit(subreddit_name, limit=None):
    subreddit = reddit.subreddit(subreddit_name)
    print(f"Scraping r/{subreddit_name}...")

    for post in subreddit.new(limit=limit):  # Can use subreddit.top() too
        try:
            # Skip if already exists (checking by post ID)
            # if mongoman.save_post(post):  # Save post using mongo_utils
            #     continue

            # Prepare post data
            post_data = {
                "_id": post.id,
                "title": post.title,
                "url": post.url,
                "permalink": f"https://www.reddit.com{post.permalink}"
            }

            # Check if it's a RedGifs post and add media URL if so
            if "redgifs" in post.url:
                media_url = extract_media_url(post.url)
                post_data["media_url"] = media_url

            # Save post to MongoDB using mongo_utils
            # save_post(post_data)
            print(f"Saved: {post_data}")

            time.sleep(1)  # Be nice to Reddit's API
        except Exception as e:
            print(f"Error: {e}")
            continue

    print("✅ Done scraping.")

# === 3. Helper Function to Get RedGifs Media URL ===
def extract_media_url(post_url):
    """Extracts the media URL for RedGifs posts."""
    video_id = post_url.split('/')[-1]
    return f"https://media.redgifs.com/{video_id}.mp4"

# === 4. Run the Scraper ===
if __name__ == "__main__":
    scrape_subreddit("NSFW_GIF", limit=None)  # limit=None → all posts
