import os
from dotenv import load_dotenv
from google import genai
import json
import mongoman

load_dotenv()

MODEL_ID = "gemini-2.0-flash"

EXAMPLE_DOCUMENT = {
    "id": "4b21adbb-7f09-4fee-afe1-09de2f09bb81",
    "source": "redgifs",
    "source_id": "creepyinferioroxen",
    "tags": ["Amateur", "Big Dick", "Big Tits", "Brunette", "Latina", "Threesome", "Tits"],
    "urls": {
        "sd": "https://media.redgifs.com/CreepyInferiorOxen-mobile.mp4",
        "hd": "https://media.redgifs.com/CreepyInferiorOxen.mp4",
        "poster": "https://media.redgifs.com/CreepyInferiorOxen-poster.jpg",
        "thumbnail": "https://media.redgifs.com/CreepyInferiorOxen-mobile.jpg",
        "vthumbnail": "https://media.redgifs.com/CreepyInferiorOxen-mobile.mp4",
        "web_url": "https://redgifs.com/watch/creepyinferioroxen",
        "file_url": "https://api.redgifs.com/v2/gifs/creepyinferioroxen/files/CreepyInferiorOxen.mp4",
        "embed_url": "https://api.redgifs.com/v2/embed/discord?name=CreepyInferiorOxen.mp4"
    },
    "scenes": [
        {"action": "Blowjob", "start": 0},
        {"action": "Handjob", "start": 2},
        {"action": "Blowjob", "start": 4, "end": 8},
        {"action": "Handjob", "start": 8, "end": 18},
        {"action": "Blowjob", "start": 12, "end": 20},
        {"action": "Pussy Licking", "start": 24},
        {"action": "Handjob", "start": 26, "end": 32},
        {"action": "Blowjob", "start": 28, "end": 32},
        {"action": "Handjob", "start": 36}
    ]
}

def search(query):
    response_text = call(query)
    response_text = response_text.strip()
    if response_text.startswith('```json'):
        response_text = response_text[7:]
    if response_text.endswith('```'):
        response_text = response_text[:-3]
    response_text = response_text.strip()        
    query = json.loads(response_text)
    return query

def call(query):
    client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))
    
    # Get available tags and scene actions
    available_tags = mongoman.get_unique_tags()
    available_actions = mongoman.get_unique_scene_actions()
    
    # Define the context and user message
    contents = [
        {
            "role": "user",
            "parts": [{"text": f"""You are a MongoDB query expert. Convert the following natural language search query into a MongoDB query.

Search Query: "{query}"

Available Fields in Database:
1. tags: Array of strings. Available values: {json.dumps(available_tags)}
2. scenes: Array of objects with 'action' field. Available actions: {json.dumps(available_actions)}

Example Document Structure:
{json.dumps(EXAMPLE_DOCUMENT, indent=2)}

Instructions:
1. Analyze the search query to identify relevant scene actions
2. Analyze the search query to identify relevant tags
3. Search query should be very accurate, precise, and specific
4. Create a MongoDB query that matches the search intent
5. Use appropriate MongoDB operators based on the search context
6. Return only the MongoDB query object, no explanation needed

Convert the search query into a MongoDB query:"""}]
        }
    ]
    
    print(
        client.models.count_tokens(
            model=MODEL_ID,
            contents=contents,
        )
    )

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=contents
    )

    return response.text