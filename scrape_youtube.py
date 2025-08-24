
"""
Scalable YouTube comments scraper
---------------------------------
- Searches videos by queries/keywords (or from a provided list of video IDs)
- Scrapes comments (and inline replies) with robust pagination & backoff
- Appends to CSV incrementally with de-duplication by comment_id
- Resumable via checkpointed processed video IDs
- Env-based API key loading (.env -> YOUTUBE_API_KEY)

Usage examples:
  # 1) Search by queries in queries.txt, scrape up to 200 videos per query, 2000 comments per video
  python scrape_youtube.py --queries queries.txt --videos-per-query 200 --max-comments-per-video 2000 --out data/youtube_comments.csv

  # 2) Provide your own list of video IDs
  python scrape_youtube.py --video-ids 3JZ_D3ELwOQ,dQw4w9WgXcQ --max-comments-per-video 5000 --out data/youtube_comments.csv

Notes:
  - Create a .env file in the same directory with: YOUTUBE_API_KEY=YOUR_KEY
  - You can run multiple times; it will skip already processed video IDs and deduplicate comment IDs.
"""

import os
import csv
import time
import argparse
from typing import List, Dict, Optional, Iterable, Set
from dataclasses import dataclass
from urllib.parse import urlencode

import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tqdm import tqdm


@dataclass
class ScrapeConfig:
    out_csv: str
    checkpoint_csv: str
    max_comments_per_video: int = 2000
    videos_per_query: int = 200
    order: str = "relevance"  # or "date", "viewCount", "rating"
    region_code: Optional[str] = None  # e.g., "US"
    published_after: Optional[str] = None  # ISO 8601, e.g., "2024-01-01T00:00:00Z"


def load_api_key() -> str:
    load_dotenv()
    key = os.getenv("YOUTUBE_API_KEY")
    if not key:
        raise RuntimeError("YOUTUBE_API_KEY not found. Create a .env file with YOUTUBE_API_KEY=YOUR_KEY")
    return key


def build_service(api_key: str):
    return build("youtube", "v3", developerKey=api_key)


def backoff_sleep(attempt: int):
    time.sleep(min(2 ** attempt, 30))


def search_video_ids(
    service,
    query: str,
    max_videos: int,
    order: str = "relevance",
    region_code: Optional[str] = None,
    published_after: Optional[str] = None,
) -> List[str]:
    """Search for video IDs for a given query."""
    ids: List[str] = []
    next_page = None
    attempts = 0
    pbar = tqdm(total=max_videos, desc=f"Searching '{query}'")

    while len(ids) < max_videos:
        try:
            req = service.search().list(
                part="id",
                q=query,
                type="video",
                maxResults=50,
                order=order,
                regionCode=region_code,
                publishedAfter=published_after,
                pageToken=next_page,
            )
            resp = req.execute()
            attempts = 0
        except HttpError as e:
            attempts += 1
            if e.resp.status in (403, 429, 500, 503) and attempts <= 5:
                backoff_sleep(attempts)
                continue
            raise

        for item in resp.get("items", []):
            if item["id"]["kind"] == "youtube#video":
                vid = item["id"]["videoId"]
                ids.append(vid)
                pbar.update(1)
                if len(ids) >= max_videos:
                    break

        next_page = resp.get("nextPageToken")
        if not next_page:
            break

    pbar.close()
    return ids


def fetch_comments_for_video(service, video_id: str, max_total: int, include_replies: bool = True) -> List[Dict]:
    """Fetch comments (and inline replies) for a single video with paging and backoff."""
    collected: List[Dict] = []
    page_token = None
    attempts = 0

    while len(collected) < max_total:
        try:
            req = service.commentThreads().list(
                part="snippet,replies",
                videoId=video_id,
                maxResults=100,
                pageToken=page_token,
                textFormat="plainText",
                order="relevance",  # or "time"
            )
            resp = req.execute()
            attempts = 0
        except HttpError as e:
            attempts += 1
            if e.resp.status in (403, 429, 500, 503) and attempts <= 5:
                backoff_sleep(attempts)
                continue
            raise

        items = resp.get("items", [])
        if not items:
            break

        for item in items:
            sn = item["snippet"]["topLevelComment"]["snippet"]
            top_id = item["snippet"]["topLevelComment"]["id"]
            collected.append({
                "comment_id": top_id,
                "video_id": video_id,
                "parent_id": None,
                "is_reply": False,
                "author": sn.get("authorDisplayName"),
                "text": sn.get("textDisplay", ""),
                "likes": sn.get("likeCount", 0),
                "published_at": sn.get("publishedAt"),
                "updated_at": sn.get("updatedAt"),
                "reply_count": item["snippet"].get("totalReplyCount", 0),
            })
            if len(collected) >= max_total:
                break

            if include_replies and "replies" in item:
                for r in item["replies"].get("comments", []):
                    rs = r["snippet"]
                    collected.append({
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
                    if len(collected) >= max_total:
                        break

            if len(collected) >= max_total:
                break

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return collected


def ensure_dirs(path: str):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def load_existing_comment_ids(csv_path: str) -> Set[str]:
    if not os.path.exists(csv_path):
        return set()
    try:
        existing = pd.read_csv(csv_path, usecols=["comment_id"])
        return set(existing["comment_id"].astype(str).tolist())
    except Exception:
        return set()


def append_rows(csv_path: str, rows: List[Dict]):
    ensure_dirs(csv_path)
    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "comment_id","video_id","parent_id","is_reply","author",
                "text","likes","published_at","updated_at","reply_count"
            ],
        )
        if not file_exists:
            writer.writeheader()
        for r in rows:
            writer.writerow(r)


def load_checkpoint(checkpoint_csv: str) -> Set[str]:
    if not os.path.exists(checkpoint_csv):
        return set()
    try:
        df = pd.read_csv(checkpoint_csv)
        return set(df["video_id"].astype(str).tolist())
    except Exception:
        return set()


def append_checkpoint(checkpoint_csv: str, video_id: str):
    ensure_dirs(checkpoint_csv)
    file_exists = os.path.exists(checkpoint_csv)
    with open(checkpoint_csv, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["video_id"])
        if not file_exists:
            writer.writeheader()
        writer.writerow({"video_id": video_id})


def dedupe_new(rows: List[Dict], seen_ids: Set[str]) -> List[Dict]:
    filtered = []
    for r in rows:
        cid = str(r.get("comment_id"))
        if cid and cid not in seen_ids:
            filtered.append(r)
            seen_ids.add(cid)
    return filtered


def parse_args():
    ap = argparse.ArgumentParser(description="Scale YouTube comments scraping to 100k+ rows")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--queries", type=str, help="Path to a file with one search query per line")
    g.add_argument("--video-ids", type=str, help="Comma-separated video IDs to scrape directly")
    ap.add_argument("--videos-per-query", type=int, default=200, help="Max videos to fetch per query")
    ap.add_argument("--max-comments-per-video", type=int, default=2000, help="Max comments per video")
    ap.add_argument("--out", type=str, default="data/youtube_comments.csv", help="Output CSV path")
    ap.add_argument("--checkpoint", type=str, default="data/checkpoints/processed_videos.csv", help="Checkpoint CSV of processed video IDs")
    ap.add_argument("--order", type=str, default="relevance", choices=["relevance","date","viewCount","rating"], help="Search ordering")
    ap.add_argument("--region", type=str, default=None, help="Region code (e.g., US, GB, PK)")
    ap.add_argument("--published-after", type=str, default=None, help="ISO-8601 date filter e.g. 2024-01-01T00:00:00Z")
    return ap.parse_args()


def main():
    args = parse_args()
    api_key = load_api_key()
    service = build_service(api_key)

    cfg = ScrapeConfig(
        out_csv=args.out,
        checkpoint_csv=args.checkpoint,
        max_comments_per_video=args.max_comments_per_video,
        videos_per_query=args.videos_per_query,
        order=args.order,
        region_code=args.region,
        published_after=args.published_after,
    )

    ensure_dirs(cfg.out_csv)
    ensure_dirs(cfg.checkpoint_csv)

    # load state
    seen_comments = load_existing_comment_ids(cfg.out_csv)
    processed_videos = load_checkpoint(cfg.checkpoint_csv)

    # Build list of videos to process
    video_ids: List[str] = []
    if args.video_ids:
        video_ids = [v.strip() for v in args.video_ids.split(",") if v.strip()]
    else:
        # read queries from file and search videos for each
        with open(args.queries, "r", encoding="utf-8") as f:
            queries = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
        for q in queries:
            found = search_video_ids(
                service,
                q,
                max_videos=cfg.videos_per_query,
                order=cfg.order,
                region_code=cfg.region_code,
                published_after=cfg.published_after,
            )
            video_ids.extend(found)

    # remove already processed videos
    video_ids = [v for v in video_ids if v not in processed_videos]

    total_written = 0
    for vid in tqdm(video_ids, desc="Scraping videos"):
        try:
            rows = fetch_comments_for_video(service, vid, max_total=cfg.max_comments_per_video, include_replies=True)
            rows = dedupe_new(rows, seen_comments)
            if rows:
                append_rows(cfg.out_csv, rows)
                total_written += len(rows)
            append_checkpoint(cfg.checkpoint_csv, vid)
        except HttpError as e:
            print(f"[WARN] HttpError on video {vid}: {e} — skipping.")
            append_checkpoint(cfg.checkpoint_csv, vid)
            continue
        except Exception as e:
            print(f"[WARN] Error on video {vid}: {e} — skipping.")
            append_checkpoint(cfg.checkpoint_csv, vid)
            continue

    print(f"Done. Newly written comments: {total_written}. Output: {cfg.out_csv}")
    print(f"Checkpointed processed video IDs in: {cfg.checkpoint_csv}")


if __name__ == "__main__":
    main()
