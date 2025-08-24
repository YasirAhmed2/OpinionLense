# utils/url.py
import re
from urllib.parse import urlparse, parse_qs

_YT_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")

def extract_video_id(url_or_id: str) -> str:
    """
    Accepts a YouTube URL (watch, youtu.be, embed, shorts) or a raw 11-char ID.
    Returns the 11-char video ID or raises ValueError.
    """
    s = url_or_id.strip()

    # already an ID?
    if _YT_ID_RE.match(s):
        return s

    parsed = urlparse(s)

    # watch?v=ID
    if parsed.query:
        vid = parse_qs(parsed.query).get("v", [None])[0]
        if vid and _YT_ID_RE.match(vid):
            return vid

    # youtu.be/ID or /embed/ID or /shorts/ID
    path_parts = [p for p in parsed.path.split("/") if p]
    if path_parts:
        cand = path_parts[-1]
        if _YT_ID_RE.match(cand):
            return cand

    raise ValueError(f"Could not extract video ID from: {url_or_id}")
