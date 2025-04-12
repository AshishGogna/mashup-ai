from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import time
import json
import ai_agent
import os
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Flutter web app origin
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount the clips directory as static files
app.mount("/clips", StaticFiles(directory="clips"), name="clips")

class MashupRequest(BaseModel):
    id: str
    link: str
    start: float
    end: float

@app.get("/api/mashup")
async def mashup(query: str, page: int):
    video = ai_agent.find(query, page)
    # clips = ai_agent.generate_clips(video)

    code = 200#
    response = {
        "status": "success",
        "video": video,
    }

    if video is None or len(video) == 0:
        response = {
            "status": "nomore"
        }
        # code = 400
    return JSONResponse(content=response, status_code=code)

@app.post("/api/clip")
async def mashup(request: MashupRequest, background_tasks: BackgroundTasks):
    clip = ai_agent.generate_clip(request.id, request.link, request.start, request.end)

    if clip is None:
        return JSONResponse(content={"message": "Couldn't clip"}, status_code=404)
#
    response = FileResponse(
        path=clip,
        media_type="video/mp4",
        filename=clip
    )

    background_tasks.add_task(delete_file, clip)
    return response

def delete_file(file_path: str):
    try:
        os.remove(file_path)
        print(f"Deleted clip: {file_path}")
    except Exception as e:
        print(f"Error deleting clip file: {e}")

@app.get("/api/video/{video_path:path}")
async def get_video(video_path: str):
    # Remove 'clips/' from the path if it's included
    if video_path.startswith('clips/'):
        video_path = video_path[6:]  # Remove 'clips/' prefix
    
    # Construct the full path to the video file
    full_path = os.path.join("clips", video_path)
    
    # Check if the file exists
    if not os.path.exists(full_path):
        return JSONResponse(
            content={"message": f"Video file not found: {full_path}"},
            status_code=404
        )
    
    # Return the video file
    return FileResponse(
        path=full_path,
        media_type="video/mp4",
        filename=video_path
    )