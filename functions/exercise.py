
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
    reps: Optional[int]
    restTime: Optional[int]


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

    Identify and provide information for exercises in the transcript. Never use the word seconds when doing time - assume it is the default to be in seconds. If the transcript does not contain any exercise instructions, respond with "No clear exercise instructions found."

    For each clearly described exercise, provide the following information in a structured format:
    1. Name of the exercise
    2. Description of how to perform the exercise
    3. Interval (duration) in seconds. Ensure this is a number not a range. Default to 60 if unsure. If there are reps assume there are 5 per rep. If there are exericses for each limb seperate the exercises by limb
    4. A placeholder URL for a video demonstration if no videoId is provided or the youtube video plus the timestamp of the exercise
    5. Reps. Default to 12 if not specified
    6. Rest time if specified. If not follow these rules of the objectives of the workout (if present in the transcript): 
        Muscle mass: Rest 90 between sets
        Strength and power: Rest 300 between sets
        Endurance: Rest less than 120  between sets
        Hypertrophy (muscle growth): Rest 60 between sets
        Interval workouts: Rest 90 between sets

    Please format your response as follows for each exercise:
    Exercise: [Name]
    Description: [Brief description]
    Interval: [Number of seconds]
    VideoURL: https://example.com/exercise-video or https://www.youtube.com/watch?v=<videoId>&t=<timestamp>s
    Reps: [Number of reps]
    RestTime: [Number of seconds]

    At the very first line of your response generate a suitable title for the entire workout ie. "Shoulder Strengthening". Do not add any special text to this title. Then generate the exercises below it.
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
    title = text.split("\n")[0]
    text = text.replace(title, "")
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
            elif line.startswith("Reps:"):
                exercise_data["reps"] = line.replace("Reps:", "").strip()
            elif line.startswith("RestTime:"):
                exercise_data["restTime"] = line.replace("RestTime:", "").strip()

        if "name" in exercise_data and "interval" in exercise_data:
            exercises.append(Exercise(**exercise_data))

    if exercises:
        return Group(name=title, exercises=exercises)
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

