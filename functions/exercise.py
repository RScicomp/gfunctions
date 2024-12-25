
from pydantic import BaseModel
import httpx
import os
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import logging
from typing import Annotated
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv
from auth import access_secret


# Load environment variables from .env file
load_dotenv()

# to get a string like this run:
# openssl rand -hex 32


# Pydantic models for request and response
class TranscriptRequest(BaseModel):
    transcript: str

class VideoRequest(BaseModel):
    video_id: str  # Define a Pydantic model for the request body


class Exercise(BaseModel):
    name: str
    description: str
    interval: float
    videoURL: str

class Group(BaseModel):
    name: str
    exercises: List[Exercise]


# Configuration
OPENAI_API_KEY = access_secret()
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set")

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


def generate_exercises(request: TranscriptRequest):
    prompt = f"""
    Analyze this transcript for specific exercise instructions: {request.transcript}

    Only identify and provide information for exercises that are clearly described. If the transcript does not contain clear exercise instructions, respond with "No clear exercise instructions found."

    For each clearly described exercise, provide the following information in a structured format:
    1. Name of the exercise
    2. Description of how to perform the exercise
    3. Interval (duration) in seconds. Ensure this is a number not a range.
    4. A placeholder URL for a video demonstration if no videoId is provided or the youtube video plus the timestamp of the exercise

    Please format your response as follows for each exercise:
    Exercise: [Name]
    Description: [Brief description]
    Interval: [Number of seconds]
    VideoURL: https://example.com/exercise-video or https://www.youtube.com/watch?v=<videoId>&t=<timestamp>s

    Separate each exercise with a blank line. If the user asks for a repeat of the same exercise, that is 3 sets, return the same exercise with the same name, description, interval, and videoURL the number of times specified (3)

    If the transcript contains non-exercise related talk or planning without clear exercise instructions, do not generate any exercise information for that part.
    """

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4o-mini-2024-07-18",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    with httpx.Client(timeout=50.0) as client:
        response = client.post(OPENAI_API_URL, json=payload, headers=headers)


    try:
        content = response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        raise 
    print(content)
    return parse_exercises(content)

def parse_exercises(text: str) -> Optional[Group]:
    exercises = []
    exercise_blocks = text.split("\n\n")

    for block in exercise_blocks:
        lines = block.split("\n")
        exercise_data = {}

        for line in lines:
            if line.startswith("Exercise:"):
                exercise_data["name"] = line.replace("Exercise:", "").strip()
            elif line.startswith("Description:"):
                exercise_data["description"] = line.replace("Description:", "").strip()
            elif line.startswith("Interval:"):
                interval_str = line.replace("Interval:", "").strip().split()[0]
                exercise_data["interval"] = float(interval_str)
            elif line.startswith("VideoURL:"):
                exercise_data["videoURL"] = line.replace("VideoURL:", "").strip()

        if "name" in exercise_data and "interval" in exercise_data:
            exercises.append(Exercise(**exercise_data))

    if exercises:
        return Group(name="Generated Group", exercises=exercises)
    return None


def get_transcript_and_generate_exercises(request: VideoRequest):
    
    try:
        video_id = request.video_id
        logging.info(f"Getting transcript for video ID: {video_id}")
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = '\n'.join([i['text'] for i in transcript_data])
        logging.info(f"Transcript retrieved successfully")
    except Exception as e:
        raise 
    # Step 2: Call the /generate_exercises endpoint
    exercises = generate_exercises(TranscriptRequest(transcript=transcript))

    return exercises

