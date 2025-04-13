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
