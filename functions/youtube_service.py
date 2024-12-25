from dataclasses import dataclass
from typing import Optional, List, Tuple
from urllib.parse import urlencode
import requests
import json
from auth import access_youtube_secret

@dataclass
class Video:
    id: str
    title: str
    thumbnailURL: str
    channelTitle: str

@dataclass
class PageInfo:
    totalResults: int
    resultsPerPage: int

@dataclass
class Thumbnail:
    url: str
    width: int
    height: int

@dataclass
class Thumbnails:
    default: Thumbnail
    medium: Thumbnail
    high: Thumbnail

@dataclass
class VideoId:
    kind: str
    videoId: str

@dataclass
class Snippet:
    publishedAt: str
    channelId: str
    title: str
    description: str
    thumbnails: Thumbnails
    channelTitle: str
    liveBroadcastContent: str
    publishTime: str

@dataclass
class SearchResult:
    kind: str
    etag: str
    id: VideoId
    snippet: Snippet

@dataclass
class YouTubeResponse:
    kind: str
    etag: str
    nextPageToken: Optional[str]
    regionCode: str
    pageInfo: PageInfo
    items: List[SearchResult]

class YouTubeService:
    def __init__(self):
        self.base_url = "https://www.googleapis.com/youtube/v3/search"
        self.api_key = access_youtube_secret()
    
    def search_videos(self, query: str, page_token: Optional[str] = None) -> Tuple[List[Video], Optional[str]]:
        # Build query parameters
        params = {
            "part": "snippet",
            "q": f"{query} workout",
            "type": "video",
            "maxResults": "10",
            "key": self.api_key
        }
        
        if page_token:
            params["pageToken"] = page_token
            
        url = f"{self.base_url}?{urlencode(params)}"
        
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"API request failed with status {response.status_code}")
        
        data = response.json()

        return data

