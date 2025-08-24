# main.py
import pandas as pd
from utils.url import extract_video_id
from utils.youtube_api import fetch_comments

def run(video_url_or_id: str, out_path: str = "data/raw_comments.csv", limit: int = 1000):
    vid = extract_video_id(video_url_or_id)
    rows = fetch_comments(vid, max_total=limit, include_replies=True)
    if not rows:
        print("No comments fetched.")
        return
    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"Saved {len(df)} comments to {out_path}")

if __name__ == "__main__":
    # Example inputs:
    # run("https://www.youtube.com/watch?v=dQw4w9WgXcQ", limit=500)
    # or
    run("kn0IZelsCoM", limit=500)


