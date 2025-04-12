import time
import json
import os
from youtubesearchpython import VideosSearch
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
# processed_video_ids = set()

def search_videos(query, max_results, page):
    search = VideosSearch(query, limit=max_results)
    
    for _ in range(page - 1):
        search.next()  # simulate page flipping

    results = search.result()
    return [
        {
            "title": video["title"],
            "video_id": video["id"],
            "link": video["link"]
        }
        for video in results["result"]
    ]

def get_transcript(video_id):
    try:
        return YouTubeTranscriptApi.get_transcript(video_id)
    except Exception as e:
        print(f"Transcript error for {video_id}: {e}")
        return None

def extract_clips_from_transcript(query, transcript, video_title):
    transcript_text = "\n".join([f"[{entry['start']:.2f}] {entry['text']}" for entry in transcript])
    prompt = f"""
You are a highly skilled video editing assistant.

The user wants to create a powerful, meaningful montage based on this request: "{query}". 
Your job is to find moments in the transcript that are emotionally or contextually significant. Each clip should represent a complete beat.

You do NOT need to make clips short. Prioritize RELEVANCE over brevity.
Only select a clip if it feels complete, emotionally or narratively.

Minimum duration: 10 seconds.

Use context before and after if needed to make the clip feel whole. Avoid cutting off in the middle of a sentence or moment. 

Respond in this exact format:
[
  {{
    "start_time": "00:00",
    "end_time": "00:00",
    "reason": "reason for the clip"
  }},
  ...
]

Transcript of "{video_title}":
{transcript_text[:3500]}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        content = response.choices[0].message.content.strip()
        print(f"GPT-4 response: {content}")  # Log the response
        return content
    except Exception as e:
        print(f"Error getting GPT-4 response: {e}")
        return "[]"  # Return empty array on error


def parse_and_filter_clips(clips_json_string, min_duration=3.0):
    if not clips_json_string or clips_json_string.strip() == "":
        print("Empty clips JSON string received")
        return []

    try:
        clips = json.loads(clips_json_string)
        if not isinstance(clips, list):
            print(f"Expected list but got {type(clips)}")
            return []

        filtered = []
        for clip in clips:
            try:
                if not all(key in clip for key in ["start_time", "end_time", "reason"]):
                    print(f"Missing required fields in clip: {clip}")
                    continue

                # Convert "MM:SS" or "HH:MM:SS" to seconds
                start_parts = [float(p) for p in clip["start_time"].split(":")]
                start = sum(p * 60 ** i for i, p in enumerate(reversed(start_parts)))

                end_parts = [float(p) for p in clip["end_time"].split(":")]
                end = sum(p * 60 ** i for i, p in enumerate(reversed(end_parts)))

                if end - start >= min_duration:
                    filtered.append(clip)
                else:
                    print(f"Clip too short: {clip['start_time']} - {clip['end_time']}")

            except Exception as e:
                print(f"Error processing clip {clip}: {e}")
                continue

        return filtered
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Invalid JSON string: {clips_json_string}")
        return []
    except Exception as e:
        print(f"Unexpected error in parse_and_filter_clips: {e}")
        return []

def get_next_result(user_query, page):
    videos = search_videos(user_query, 1, page)

    for video in videos:
        # if video["video_id"] in processed_video_ids:
        #     continue

        print("************************* processing video *************************")
        print(f"{video['video_id']}")
        print(f"{video['title']}")

        transcript = get_transcript(video["video_id"])
        if not transcript:
            print(f"No transcript available for {video['video_id']}")
            # processed_video_ids.add(video["video_id"])
            continue

        try:
            clips_json = extract_clips_from_transcript(user_query, transcript, video["title"])
            print(f"Raw clips JSON: {clips_json}")
            filtered_clips = parse_and_filter_clips(clips_json)
            print(f"Filtered clips: {filtered_clips}")
        except Exception as e:
            print(f"Failed to process clips for {video['video_id']}: {e}")
            # processed_video_ids.add(video["video_id"])
            continue

        for clip in filtered_clips:
            clip["video_id"] = video["video_id"]
            clip["title"] = video["title"]
            clip["link"] = video["link"]

        # processed_video_ids.add(video["video_id"])
        return {
            "clips": filtered_clips
        }

    return None
