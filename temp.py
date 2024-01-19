import subprocess
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import random
import cv2
from moviepy.video.io.VideoFileClip import VideoFileClip
from pydantic import BaseModel
import tempfile

app = FastAPI()

# Create a directory to store uploaded videos
upload_folder = "uploads"
os.makedirs(upload_folder, exist_ok=True)

# Create a temporary directory to store random frames
temp_folder = tempfile.mkdtemp()


# Serve the uploaded videos at /uploads path
app.mount("/uploads", StaticFiles(directory=upload_folder), name="uploads")
app.mount("/temp", StaticFiles(directory=temp_folder), name="temp")


class Message(BaseModel):
    text: str


@app.post("/message")
async def create_message(msg: Message):
    return {"message": msg.text}


@app.post("/extract-frames")
async def extract_frames(video: UploadFile = None):
    if not video:
        raise HTTPException(status_code=400, detail="Video file not provided")

    # Save the uploaded video
    video_path = os.path.join(upload_folder, video.filename)
    with open(video_path, "wb") as video_file:
        video_file.write(video.file.read())

    # Extract random frames from the video and save them in the temporary folder
    random_frame_paths = extract_random_frames(video_path)

    return JSONResponse(content={"frames": random_frame_paths})


def extract_random_frames(video_path, num_frames=5):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if num_frames > total_frames:
        raise HTTPException(status_code=400, detail="Number of frames requested exceeds total frames in the video")

    selected_frames = random.sample(range(1, total_frames + 1), num_frames)

    random_frame_paths = []
    for frame_number in selected_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number - 1)
        ret, frame = cap.read()
        if ret:
            # Save the frame in the temporary folder
            frame_filename = f"frame_{frame_number}.jpg"
            frame_path = os.path.join(temp_folder, frame_filename)
            cv2.imwrite(frame_path, frame)
            random_frame_paths.append(frame_path)

    cap.release()
    return random_frame_paths


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
