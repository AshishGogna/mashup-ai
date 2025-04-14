from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import time
import json
import ai_agent
import os
from pydantic import BaseModel
from typing import List, Optional
import mongoman
from typing import Dict
import llm_gemini
import httpx
from fastapi.responses import StreamingResponse
from fastapi import Request
from starlette.status import HTTP_206_PARTIAL_CONTENT

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Flutter web app origin
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/api/next-video")
def get_next_video(last_id: str = Query(default=None)):
    video = mongoman.find_next(last_id)

    code = 200
    response = {
        "message": "Video found",
        "video": video,
    }
    if (video is None):
        response = {
            "message": "No video found",
        }

    return JSONResponse(content=response, status_code=code)

class UpdateVideoRequest(BaseModel):
    id: str
    update_data: Dict
@app.put('/api/update-video')
def update_video(request: UpdateVideoRequest):
    video_id = request.id
    update_data = request.update_data

    result = mongoman.update_video(video_id, update_data)
    response = {
        "message": f"Video updated",
    }
    code = 200
    if (result == False):
        response = {
            "message": f"Video not updated",
        }
        code = 500
        
    return JSONResponse(content=response, status_code=code)

@app.get("/api/search")
def get_next_video(query: str = Query(default=None)):
    # print(all_videos)
    # print(len(all_videos))
    query = llm_gemini.search(query)
    print(query)
    results = mongoman.search_videos(query)
    print(results)

    code = 400
    response = {
        "message": "No videos found",
    }
    if (results is not None and len(results["results"]) > 0):
        code = 200
        response = {
            "message": "Videos found",
            "videos": results["results"],
            "pagination": results["pagination"],
        }

    return JSONResponse(content=response, status_code=code)

@app.get("/api/video")
async def proxy_video(id: str, request: Request):
    base_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://media.redgifs.com/",
    }

    try:
        video = mongoman.find_by_id(id)
        url = video["urls"]["sd"]
        print("Video URL:", url)

        # Extract Range header if present
        range_header = request.headers.get("range")
        headers = base_headers.copy()
        if range_header:
            headers["Range"] = range_header
            print(f"Forwarding Range header: {range_header}")

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, timeout=10.0, follow_redirects=True)

            if resp.status_code not in [200, 206]:
                raise HTTPException(status_code=resp.status_code, detail="Failed to fetch video")

        return StreamingResponse(
            resp.aiter_bytes(),
            status_code=resp.status_code,
            media_type=resp.headers.get("content-type", "video/mp4"),
            headers={
                "Content-Length": resp.headers.get("content-length"),
                "Content-Range": resp.headers.get("content-range", ""),
                "Accept-Ranges": "bytes",
                "Content-Disposition": 'inline; filename="video.mp4"',
                "Access-Control-Allow-Origin": "*"
            },
        )

    except httpx.RequestError as e:
        print(f"Request error: {e}")
        raise HTTPException(status_code=500, detail="Network error while fetching video")
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/home/tags")
def get_next_video(limit: int = Query(default=20)):
    tags = mongoman.get_unique_tags_with_posters(limit)

    for tag in tags:
        tag["poster_url"] = f"http://192.168.18.96:8000/api/image?id={tag["video_id"]}"

    code = 200
    response = {
        "message": "Tags found",
        "tags": tags,
    }
    if (tags is None):
        response = {
            "message": "No tags found",
        }

    return JSONResponse(content=response, status_code=code)

@app.get("/api/home/scenes")
def get_next_video():
    videos = mongoman.get_random_videos()

    for video in videos:
        # video["poster_url"] = f"http://192.168.18.96:8000/api/image?id={video["_id"]}"
        video["url"] = f"http://192.168.18.96:8000/api/video?id={video["_id"]}"

    code = 200
    response = {
        "message": "Videos found",
        "videos": videos,
    }
    if (videos is None):
        response = {
            "message": "No videos found",
        }

    return JSONResponse(content=response, status_code=code)

@app.get("/api/image")
async def proxy_image(id: str, request: Request):
    base_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://media.redgifs.com/",
    }

    try:
        video = mongoman.find_by_id(id)
        if not video or "urls" not in video or "poster" not in video["urls"]:
            raise HTTPException(status_code=404, detail="Image not found")
            
        url = video["urls"]["poster"]
        print("Image URL:", url)

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=base_headers, timeout=10.0, follow_redirects=True)

            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Failed to fetch image")

        return StreamingResponse(
            resp.aiter_bytes(),
            status_code=resp.status_code,
            media_type=resp.headers.get("content-type", "image/jpeg"),
            headers={
                "Content-Length": resp.headers.get("content-length"),
                "Content-Disposition": 'inline; filename="image.jpg"',
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "public, max-age=31536000"  # Cache for 1 year
            },
        )

    except httpx.RequestError as e:
        print(f"Request error: {e}")
        raise HTTPException(status_code=500, detail="Network error while fetching image")
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scenes")
def get_next_video(with_id: str = Query(default=None), last_id: str = Query(default=None), category: str = Query(default=None)):

    vs = []

    if (with_id is not None):
        video = mongoman.find_by_id(with_id)
        id = str(video["_id"])
        v = {
            "_id": id,
            "url": f"http://192.168.18.96:8000/api/video?id={id}",
            "tags": video["tags"],
            "scenes": video.get("scenes", []),  # Use get() with default empty list
        }
        vs.append(v)
        last_id = with_id

    videos = mongoman.find_next_10(last_id, category)
    for video in videos:
        id = str(video["_id"]["$oid"])
        v = {
            "_id": id,
            "url": f"http://192.168.18.96:8000/api/video?id={id}",
            "tags": video["tags"],
            "scenes": video.get("scenes", []),  # Use get() with default empty list
        }
        vs.append(v)

    code = 200
    response = {
        "message": "Videos found",
        "videos": vs,
    }
    if (videos is None):
        response = {
            "message": "No videos found",
        }

    return JSONResponse(content=response, status_code=code)