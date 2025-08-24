# utils/realtime.py
from datetime import datetime, timezone
from typing import List, Dict
from googleapiclient.errors import HttpError
from utils.youtube_api import _service

def iso_now():
    return datetime.now(timezone.utc).isoformat()

def fetch_new_since(video_id: str, since_iso: str, max_total: int = 500) -> List[Dict]:
    """
    Fetch comments published after the given ISO timestamp.
    Uses search by paging then client-side filter.
    """
    new_items: List[Dict] = []
    page_token = None
    fetched = 0
    while True:
        try:
            req = _service.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=100,
                pageToken=page_token,
                order="time",            # newest first
                textFormat="plainText"
            )
            resp = req.execute()
        except HttpError as e:
            raise

        items = resp.get("items", [])
        for it in items:
            snip = it["snippet"]["topLevelComment"]["snippet"]
            if snip.get("publishedAt", "") > since_iso:
                new_items.append({
                    "comment_id": it["snippet"]["topLevelComment"]["id"],
                    "video_id": video_id,
                    "text": snip.get("textDisplay", ""),
                    "published_at": snip.get("publishedAt"),
                })
                fetched += 1
                if fetched >= max_total:
                    return new_items
            else:
                # since results are sorted by time desc, we can stop early
                return new_items

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return new_items
