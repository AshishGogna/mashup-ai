from pymongo import MongoClient
import json
from bson import ObjectId
from bson.json_util import dumps

# === 1. MongoDB Setup ===
client = MongoClient("mongodb://3.7.29.123:27017/")
db = client["scraper"]
videos_collection = db["videos"]

# === 2. Save video Function ===
def update_video(video_id, update_data):
    try:
        video_object_id = ObjectId(video_id)
        result = videos_collection.update_one(
            {"_id": video_object_id},
            {"$set": update_data}
        )

        # if result.modified_count > 0:
        #     return True
        # else:
        #     return False
        return True
    except Exception as e:
        print(f"update_video error: {e}")
        return False

def find_next(last_id):
    try:
        query = {}
        if last_id:
            query["_id"] = {"$gt": ObjectId(last_id)}
        result = videos_collection.find(query).sort("_id", 1).limit(1)
        video = list(result)
        if video:
            return json.loads(dumps(video[0]))
        else:
            return None
    except Exception as e:
        print(f"find_next error: {e}")
        return None
    
def find_one(source_id):
    return videos_collection.find_one({"source_id": source_id})

def find_by_id(video_id_str):
    try:
        video_id = ObjectId(video_id_str)
        return videos_collection.find_one({"_id": video_id})
    except Exception as e:
        print(f"find_by_id error: {e}")
        return None

def save_video(data):
    print(f"save_video: {data}")
    try:
        # Check if video already exists
        if videos_collection.find_one({"source_id": data["source_id"]}):
            return True  # video already exists
        else:
            videos_collection.insert_one(data)
            return False  # video was saved successfully
    except Exception as e:
        print(f"save_video error: {e}")
        return False

def find_all():
    try:
        result = videos_collection.find().sort("_id", 1)
        videos = list(result)
        return [json.loads(dumps(video)) for video in videos]
    except Exception as e:
        print(f"find_all error: {e}")
        return []

def get_unique_tags():
    try:
        # Use MongoDB's distinct to get unique tags
        unique_tags = videos_collection.distinct("tags")
        return sorted(unique_tags)  # Return sorted list of unique tags
    except Exception as e:
        print(f"get_unique_tags error: {e}")
        return []

def get_unique_scene_actions():
    try:
        pipeline = [
            {"$unwind": "$scenes"},
            {"$group": {"_id": "$scenes.action"}},
            {"$sort": {"_id": 1}}  # optional, sorts alphabetically
        ]
        unique_actions = [doc["_id"] for doc in videos_collection.aggregate(pipeline)]
        return unique_actions
    except Exception as e:
        print(f"get_unique_scene_actions error: {e}")
        return []

def search_videos(query, page=1, page_size=10):
    try:
        # Calculate skip value
        skip = (page - 1) * page_size
        
        # Get total count for pagination info
        total = videos_collection.count_documents(query)
        
        # Execute the query with pagination
        cursor = videos_collection.find(query).skip(skip).limit(page_size)
        results = list(cursor)
        
        # Convert results to JSON serializable format
        serializable_results = []
        for doc in results:
            # Convert ObjectId to string
            doc['_id'] = str(doc['_id'])
            serializable_results.append(doc)
        
        # Return results with pagination info
        return {
            "results": serializable_results,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size  # Ceiling division
            }
        }
    except Exception as e:
        print(f"search_videos error: {e}")
        return {
            "results": [],
            "pagination": {
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }
        }
