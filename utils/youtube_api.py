# utils/youtube_api.py
from __future__ import annotations
import time
from typing import Dict, List, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import API_KEY

# Build once; reuse
_service = build("youtube", "v3", developerKey=API_KEY)

def _sleep_backoff(try_no: int):
    time.sleep(min(2 ** try_no, 30))

def fetch_comments(
    video_id: str,
    max_total: int = 1000,
    include_replies: bool = True,
) -> List[Dict]:
    """
    Fetch top-level comments (and optional replies) with robust paging.
    Returns a list of dicts with rich metadata.
    """
    results: List[Dict] = []
    page_token: Optional[str] = None
    fetched = 0
    tries = 0

    while True:
        try:
            req = _service.commentThreads().list(
                part="snippet,replies",
                videoId=video_id,
                maxResults=100,  # API max
                pageToken=page_token,
                textFormat="plainText"
            )
            resp = req.execute()
            tries = 0  # reset on success
        except HttpError as e:
            tries += 1
            if e.resp.status in (403, 429, 500, 503) and tries <= 5:
                _sleep_backoff(tries)
                continue
            raise

        for item in resp.get("items", []):
            snip = item["snippet"]["topLevelComment"]["snippet"]
            top_id = item["snippet"]["topLevelComment"]["id"]
            results.append({
                "comment_id": top_id,
                "video_id": video_id,
                "parent_id": None,
                "is_reply": False,
                "author": snip.get("authorDisplayName"),
                "text": snip.get("textDisplay", ""),
                "likes": snip.get("likeCount", 0),
                "published_at": snip.get("publishedAt"),
                "updated_at": snip.get("updatedAt"),
                "reply_count": item["snippet"].get("totalReplyCount", 0),
            })
            fetched += 1
            if fetched >= max_total:
                return results

            # replies (if requested and present inline)
            if include_replies and "replies" in item:
                for r in item["replies"].get("comments", []):
                    rs = r["snippet"]
                    results.append({
                        "comment_id": r["id"],
                        "video_id": video_id,
                        "parent_id": top_id,
                        "is_reply": True,
                        "author": rs.get("authorDisplayName"),
                        "text": rs.get("textDisplay", ""),
                        "likes": rs.get("likeCount", 0),
                        "published_at": rs.get("publishedAt"),
                        "updated_at": rs.get("updatedAt"),
                        "reply_count": 0,
                    })
                    fetched += 1
                    if fetched >= max_total:
                        return results

        page_token = resp.get("nextPageToken")
        if not page_token or fetched >= max_total:
            break

    # If include_replies True, some threads may have replies not expanded.
    # Optionally: fetch deeper via comments.list(parentId) — only if needed.
    return results
