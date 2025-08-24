from utils.youtube_api import fetch_comments
import pandas as pd

if __name__ == "__main__":
    video_id = "kn0IZelsCoM"  # Replace with your test video ID
    comments = fetch_comments(video_id)
    df = pd.DataFrame(comments, columns=["Comment"])
    print(df.head())
    df.to_csv("data/raw_comments.csv", index=False)
