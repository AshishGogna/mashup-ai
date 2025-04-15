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

def search_videos(query, last_id=None, page_size=10):
    try:
        # If last_id is provided, add it to the query to get results after that ID
        if last_id:
            query['_id'] = {'$gt': ObjectId(last_id)}
        
        # Get total count for pagination info
        # total = videos_collection.count_documents(query)
        
        # Execute the query with limit
        cursor = videos_collection.find(query).sort('_id', 1).limit(page_size)
        results = list(cursor)
        
        # Convert results to JSON serializable format
        serializable_results = []
        for doc in results:
            # Convert ObjectId to string
            doc['_id'] = str(doc['_id'])
            serializable_results.append(doc)
        
        # Get the last ID for next page
        last_result_id = str(results[-1]['_id']) if results else None
        
        # Return results with pagination info
        return {
            "results": serializable_results,
            "pagination": {
                # "total": total,
                "last_id": last_result_id,
                # "has_more": len(results) == page_size
            }
        }
    except Exception as e:
        print(f"search_videos error: {e}")
        return {
            "results": [],
            "pagination": {
                # "total": 0,
                "last_id": None,
                # "has_more": False
            }
        }

def get_unique_tags_with_posters(limit=-1):
    try:
        # Use MongoDB's aggregation to get unique tags with their video IDs
        pipeline = [
            # Unwind the tags array to get one document per tag
            {"$unwind": "$tags"},
            # Group by tag and get a random video's ID for each tag
            {
                "$group": {
                    "_id": "$tags",
                    "video_id": {"$first": "$_id"},
                    "count": {"$sum": 1},
                    "videos": {
                        "$push": {
                            "video_id": "$_id"
                        }
                    }
                }
            },
            # Add a random video ID from the videos array
            {
                "$addFields": {
                    "video_id": {
                        "$arrayElemAt": [
                            "$videos.video_id",
                            {"$mod": [{"$toInt": {"$multiply": ["$count", 0.5]}}, {"$size": "$videos"}]}
                        ]
                    }
                }
            },
            # Remove the videos array as it's no longer needed
            {"$project": {"videos": 0}}
        ]
        
        # Add sorting based on limit
        if limit != -1:
            # Sort by count in descending order when limit is specified
            pipeline.append({"$sort": {"count": -1, "_id": 1}})
            pipeline.append({"$limit": limit})
        else:
            # Sort alphabetically when getting all tags
            pipeline.append({"$sort": {"_id": 1}})
        
        # Execute the aggregation
        result = videos_collection.aggregate(pipeline)
        
        # Format the result
        tags_with_videos = [
            {
                "tag": doc["_id"],
                "poster_url": "",  # Use the actual poster URL
                "video_id": str(doc["video_id"]),  # Convert ObjectId to string
                "count": doc["count"]
            }
            for doc in result
        ]
        
        return tags_with_videos
    except Exception as e:
        print(f"get_unique_tags_with_posters error: {e}")
        return []

def get_random_videos(limit=10):
    try:
        # Use MongoDB's $sample operator to get random documents
        pipeline = [
            {"$sample": {"size": limit}},
            {"$project": {
                "_id": 1,
                "url": "$urls.sd", 
                "scenes": 1,
                # "poster_url": "$urls.poster"
            }}
        ]
        
        result = videos_collection.aggregate(pipeline)
        videos = list(result)
        
        # Convert ObjectId to string for JSON serialization
        for video in videos:
            video['_id'] = str(video['_id'])
            # Ensure we have a valid URL
            if not video.get('url'):
                video['url'] = f"http://192.168.18.96:8000/api/video?id={video['_id']}"
        
        return videos
    except Exception as e:
        print(f"get_random_videos error: {e}")
        return []

def find_next_10(last_id, category=None):
    try:
        query = {}
        if last_id:
            query["_id"] = {"$gt": ObjectId(last_id)}
        else:
            # Get a random video ID to start from
            random_video = videos_collection.aggregate([
                {"$sample": {"size": 1}},
                {"$project": {"_id": 1}}
            ])
            random_video = list(random_video)
            if random_video:
                query["_id"] = {"$gte": random_video[0]["_id"]}
        
        if category:
            query["tags"] = category  # MongoDB will match if the tag exists in the array
        
        result = videos_collection.find(query).sort("_id", 1).limit(5)
        videos = list(result)
        if videos:
            return [json.loads(dumps(video)) for video in videos]
        else:
            return []
    except Exception as e:
        print(f"find_next_10 error: {e}")
        return []
