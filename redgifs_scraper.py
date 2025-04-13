import requests
import time
import mongoman
import uuid
import json
import os

# Read tags from JSON file
with open('redgifs_tags.json', 'r') as f:
    data = json.load(f)
    tags = [item["name"] for item in data["items"]]

def get_start_page(tag):
    with open('redgifs_tags.json', 'r') as f:
        data = json.load(f)
        for item in data["items"]:
            if item["name"] == tag:
                if "page" in item:
                    print(f"Tag {tag} already has page {item['page']}, skipping")
                    return None
                return 1
    return 1

def update_tag_progress(tag, page):
    print(f"updating tag progress: {tag}: {page}")
    with open('redgifs_tags.json', 'r') as f:
        data = json.load(f)
    
    # Find the tag in items and update its processed count
    for item in data["items"]:
        if item["name"] == tag:
            item["page"] = page
            break
    
    with open('redgifs_tags.json', 'w') as f:
        json.dump(data, f, indent=2)

base_url = "https://api.adultdatalink.com/redgifs/search"

def scrape_redgifs():
    headers = {
        "accept": "application/json"
    }

    for tag in tags:
        page = get_start_page(tag)
        update_tag_progress(tag, page)
        if page is None:
            continue
            
        print(f"Starting from page {page} for tag {tag}")
        
        while True:
            print("--------------------------------")
            print(f"request: {tag}: {page}")
            params = {
                "media_type": "gif",
                "search_text": tag,
                "count": 100,
                "page": page
            }

            response = requests.get(base_url, headers=headers, params=params)
            if response.status_code != 200:
                print(f"Error: Received status code {response.status_code}")
                print(f"Response: {response.text}")
                time.sleep(5)  # Wait longer on error
                break
            
            data = response.json()
            # print(f"response: {data}")

            gifs = data.get("media", {}).get("gifs", [])
            if not gifs:
                break  # No more data for this tag

            print(f"fetched {len(gifs)} gifs for tag: {tag}, page: {page}")
            _process_gifs(gifs)
            update_tag_progress(tag, page)

            page += 1

            time.sleep(0.5)  # Be nice to the server
            # break
        # break

def _process_gifs(gifs):
    for gif in gifs:
        existing = mongoman.find_one(gif["id"])
        print(f"existing: {gif['id']}: {existing is not None}")
        if existing:
            continue

        data = {
            "id": str(uuid.uuid4()),
            "source": "redgifs",
            "source_id": gif["id"],
            "tags": gif["tags"],
            "urls": gif["urls"],
        }
        mongoman.save_video(data)

scrape_redgifs()
