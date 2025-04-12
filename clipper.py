import yt_dlp
import ffmpeg
import os
import json

def download_video(id, video_url):
    try:
        output_path = f"downloads/{id}.mp4"
        # Check if file already exists
        if os.path.exists(output_path):
            print(f"Video already exists at {output_path}")
            return output_path
            
        ydl_opts = {
            'outtmpl': f"downloads/{id}.%(ext)s",
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoRemuxer',
                'preferedformat': 'mp4',
            }]
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
            
        # If the merged file exists, return it
        if os.path.exists(output_path):
            return output_path
            
        # If merging failed, try to find the best available format
        print("Merging failed, looking for best available format...")
        available_files = [f for f in os.listdir("downloads") if f.startswith(id)]
        if available_files:
            # Sort by file size to get the best quality
            best_file = max(available_files, key=lambda x: os.path.getsize(os.path.join("downloads", x)))
            print(f"Using best available format: {best_file}")
            return os.path.join("downloads", best_file)
            
        print("No suitable video files found")
        return None
    except Exception as e:
        print(f"yt-dlp failed: {e}")
        return None

def cut_clip_ffmpeg(video_path, start_time, end_time, output_path):
    duration = end_time - start_time
    (
        ffmpeg
        .input(video_path, ss=start_time, t=duration)
        .output(
            output_path,
            vcodec='libx264',
            acodec='aac',
            strict='experimental',
            movflags='faststart'  # helps playback start faster
        )
        .run(overwrite_output=True)
    )


def hms_to_seconds(hms):
    if ":" in hms:
        parts = list(map(float, hms.split(":")))
        while len(parts) < 3:
            parts.insert(0, 0)
        hours, minutes, seconds = parts
        return int(hours * 3600 + minutes * 60 + seconds)
    return float(hms)

def generate_clip(id, link, start, end):
    video_url = link
    video_title = f"{id}_{start}_{end}"
    print(f"Downloading video for clip {video_title}")
    video_path = download_video(id, video_url)

    if video_path is None:
        print(f"Failed to download video for clip {video_title}")
        raise Exception("Failed to download video")

    out_name = f"clips/{video_title}.mp4"
    os.makedirs("clips", exist_ok=True)
    
    try:
        print(f"Cutting clip from {start}s to {end}s")
        cut_clip_ffmpeg(video_path, start, end, out_name)
        print(f"Successfully created clip at {out_name}")
        return out_name
    except Exception as e:
        print(f"Error cutting clip: {e}")
        raise