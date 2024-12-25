# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn
from firebase_admin import initialize_app, auth, credentials
import os
from functools import wraps
import logging
import json
import sys
import platform
from exercise import *
from google.cloud import secretmanager
import requests
from auth import access_youtube_secret
from youtube_service import YouTubeService
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


initialize_app()

def authenticate_request(f):
    @wraps(f)
    def decorated_function(req: https_fn.Request):
        try:
            # Get Authorization header
            auth_header = req.headers.get('Authorization')
            if not auth_header:
                raise ValueError('Authorization header is not provided')

            token_id = auth_header.split('Bearer ')[1]
            if not token_id:
                raise ValueError('Auth token is empty')

            # Verify Firebase token
            decoded_token = auth.verify_id_token(token_id)
            logger.info(f'Chat Requested by {decoded_token.get("email")}')
            return f(req)

        except Exception as error:
            logger.error(f'Chat auth: {str(error)}')
            return https_fn.Response(
                response={'error': 'Authorization failed, please pass the correct Authentication token in the header'},
                status=403
            )
    
    return decorated_function

@https_fn.on_request()
@authenticate_request
def chat_completion(req: https_fn.Request) -> https_fn.Response:
    logger.info(f"Received request: {req.method}")
    if req.method != 'POST':
        return https_fn.Response('Method not allowed', status=405)

    try:
        # Get request data
        data = req.get_json()
        messages = TranscriptRequest(transcript = data.get('message',""))
        logger.info("Processing request")
        response = generate_exercises(messages)
        logger.info("Successfully processed request")
        return response.json()

        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return https_fn.Response(
            response=f'Error: {str(e)}',
            status=500
        )
    
@https_fn.on_request()
@authenticate_request
def chat_completion_general(req: https_fn.Request) -> https_fn.Response:
    logger.info(f"Received request: {req.method}")
    if req.method != 'POST':
        return https_fn.Response('Method not allowed', status=405)

    try:
        # Get request data
        data = req.get_json()
        prompt = data.get('prompt',"")
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


        return response.json()
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return https_fn.Response(
            response=f'Error: {str(e)}',
            status=500
        )
    
@https_fn.on_request()
@authenticate_request
def chat_completion_video(req: https_fn.Request) -> https_fn.Response:
    logger.info(f"Received request: {req.method}")
    if req.method != 'POST':
        return https_fn.Response('Method not allowed', status=405)

    try:
        # Get request data
        data = req.get_json()
        video = VideoRequest(video_id = data.get('video',""))
        logger.info("Processing request")
        response = get_transcript_and_generate_exercises(video)
        logger.info("Successfully processed request")

        return response.json()

        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return https_fn.Response(
            response=f'Error: {str(e)}',
            status=500
        )
    
@https_fn.on_request()
# @authenticate_request  # Comment this out for local testing
def youtube_api_proxy(req: https_fn.Request) -> https_fn.Response:
    logger.info(f"Received request: {req.method}")
    
    try:
        youtube_service = YouTubeService()
        query = req.args.get('q', '')
        page_token = req.args.get('pageToken')
        
        # Make sure this is a synchronous call
        print("querying youtube")
        result = youtube_service.search_videos(query, page_token)
        
        return result

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return https_fn.Response(
            response=f'Error: {str(e)}',
            status=500
        )

@https_fn.on_request()
def hello(req: https_fn.Request) -> https_fn.Response:
    return https_fn.Response(
        response=json.dumps({"message": "Hello! The function is working!"}),
        status=200,
        headers={'Content-Type': 'application/json'}
    )


"""
curl -X POST \
  http://localhost:5001/linen-patrol-239817/us-central1/chat_completion \
  -H "Content-Type: application/json" \
  -d '{
    "message": "10 pushups 3x"
  }'
"""

"""
curl -X POST \
  http://localhost:5001/linen-patrol-239817/us-central1/chat_completion_video \
  -H "Content-Type: application/json" \
  -d '{
    "video": "eMjyvIQbn9M"
  }'
"""

"""
curl http://localhost:5001/linen-patrol-239817/us-central1/hello
"""


"""
curl "http://localhost:5001/linen-patrol-239817/us-central1/youtube_api_proxy?q=yoga&maxResults=10&type=video&part=snippet"
"""


"""
curl -X POST \
  http://localhost:5001/linen-patrol-239817/us-central1/chat_completion_general \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is the capital of France?"
  }'
"""
